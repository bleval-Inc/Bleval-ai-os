"""MARKET Domain Models — Market Data, Trading, MT5/TradingView Feeds."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom.data.database import DeclarativeBase


class MarketBase(DeclarativeBase):
    """Base for MARKET domain models."""
    metadata = MetaData(schema="market")


class SymbolType(str, enum.Enum):
    """Trading symbol types."""

    FOREX = "forex"
    CFD = "cfd"
    FUTURES = "futures"
    OPTIONS = "options"
    CRYPTO = "crypto"
    STOCK = "stock"
    INDEX = "index"
    COMMODITY = "commodity"


class Timeframe(str, enum.Enum):
    """Chart timeframes."""

    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"


class PositionType(str, enum.Enum):
    """Position types."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    """Order types."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, enum.Enum):
    """Order statuses."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SignalType(str, enum.Enum):
    """Trade signal types."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class SignalSource(str, enum.Enum):
    """Signal sources."""

    VALTA_PRIME = "valta_prime"
    TRADINGVIEW = "tradingview"
    MANUAL = "manual"
    ALGORITHM = "algorithm"
    TECHNICAL = "technical"


# ──────────────────────────────────────────────────────────────────────────────
# SYMBOLS & MARKET DATA
# ──────────────────────────────────────────────────────────────────────────────

class Symbol(MarketBase):
    """Trading symbol / instrument."""

    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    symbol_type: Mapped[SymbolType] = mapped_column(SQLEnum(SymbolType), nullable=False, index=True)

    # Contract specs
    currency_base: Mapped[str] = mapped_column(String(10), nullable=False)
    currency_profit: Mapped[str] = mapped_column(String(10), nullable=False)
    currency_margin: Mapped[str] = mapped_column(String(10), nullable=False)
    digits: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Trading params
    trade_mode: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_lot: Mapped[Decimal] = mapped_column(Numeric(10, 8), default=0.01, nullable=False)
    max_lot: Mapped[Decimal] = mapped_column(Numeric(10, 8), default=100.0, nullable=False)
    step_lot: Mapped[Decimal] = mapped_column(Numeric(10, 8), default=0.01, nullable=False)
    spread: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spread_float: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Swap & margin
    swap_long: Mapped[Decimal] = mapped_column(Numeric(10, 5), default=0, nullable=False)
    swap_short: Mapped[Decimal] = mapped_column(Numeric(10, 5), default=0, nullable=False)
    margin_hedged: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    margin_initial: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    margin_maintenance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    # Contract
    trade_contract_size: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=100000, nullable=False)
    trade_tick_value: Mapped[Decimal] = mapped_column(Numeric(10, 5), default=0, nullable=False)
    trade_tick_value_profit: Mapped[Decimal] = mapped_column(Numeric(10, 5), default=0, nullable=False)
    trade_tick_value_loss: Mapped[Decimal] = mapped_column(Numeric(10, 5), default=0, nullable=False)
    point: Mapped[Decimal] = mapped_column(Numeric(10, 5), default=0.00001, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    ticks: Mapped[List["MarketTick"]] = relationship("MarketTick", back_populates="symbol", lazy="dynamic")
    rates: Mapped[List["MarketRate"]] = relationship("MarketRate", back_populates="symbol", lazy="dynamic")
    positions: Mapped[List["Position"]] = relationship("Position", back_populates="symbol", lazy="selectin")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="symbol", lazy="selectin")

    __table_args__ = (
        Index("ix_symbols_type_active", "symbol_type", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Symbol(id={self.id}, name={self.name}, type={self.symbol_type.value})>"


class MarketTick(MarketBase):
    """Tick-level market data (highest resolution)."""

    __tablename__ = "market_ticks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Symbol reference
    symbol_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("symbols.id"), nullable=False, index=True
    )

    # Tick data
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    bid: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    ask: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    last: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    flags: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="mt5", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    symbol: Mapped["Symbol"] = relationship("Symbol", back_populates="ticks")

    __table_args__ = (
        Index("ix_market_ticks_symbol_timestamp", "symbol_id", "timestamp"),
        Index("ix_market_ticks_timestamp_received", "timestamp", "received_at"),
    )

    def __repr__(self) -> str:
        return f"<MarketTick(symbol_id={self.symbol_id}, bid={self.bid}, ask={self.ask})>"


class MarketRate(MarketBase):
    """OHLCV rate/candle data (timeframe-based)."""

    __tablename__ = "market_rates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Symbol & timeframe
    symbol_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("symbols.id"), nullable=False, index=True
    )
    timeframe: Mapped[Timeframe] = mapped_column(SQLEnum(Timeframe), nullable=False, index=True)

    # OHLCV
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    open: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    tick_volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    spread: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    real_volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="mt5", nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    symbol: Mapped["Symbol"] = relationship("Symbol", back_populates="rates")

    __table_args__ = (
        UniqueConstraint("symbol_id", "timeframe", "timestamp", name="uq_rate_symbol_tf_time"),
        Index("ix_market_rates_symbol_tf_timestamp", "symbol_id", "timeframe", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<MarketRate(symbol_id={self.symbol_id}, tf={self.timeframe.value}, close={self.close})>"


# ──────────────────────────────────────────────────────────────────────────────
# ACCOUNT & TRADING
# ──────────────────────────────────────────────────────────────────────────────

class AccountSnapshot(MarketBase):
    """Account snapshot at a point in time."""

    __tablename__ = "account_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Account info
    login: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    server: Mapped[str] = mapped_column(String(100), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    leverage: Mapped[int] = mapped_column(Integer, nullable=False)

    # Balance & equity
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    profit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    # Margin
    margin: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    margin_free: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    margin_level: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    margin_so_call: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    margin_so_so: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    # Credit
    credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    # Trade permissions
    trade_mode: Mapped[int] = mapped_column(Integer, nullable=False)
    trade_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    trade_expert: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Snapshot metadata
    source: Mapped[str] = mapped_column(String(50), default="mt5", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_account_snapshots_login_timestamp", "login", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AccountSnapshot(login={self.login}, equity={self.equity}, margin_level={self.margin_level})>"


class Position(MarketBase):
    """Open trading position."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identifiers
    ticket: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    symbol_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("symbols.id"), nullable=False, index=True
    )

    # Position details
    type: Mapped[PositionType] = mapped_column(SQLEnum(PositionType), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)

    # Prices
    price_open: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    price_current: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)

    # Risk management
    sl: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    tp: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)

    # P&L
    profit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    swap: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    # Metadata
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    magic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    time_open: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    time_update: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Source
    source: Mapped[str] = mapped_column(String(50), default="mt5", nullable=False)

    # Relationships
    symbol: Mapped["Symbol"] = relationship("Symbol", back_populates="positions")

    __table_args__ = (
        Index("ix_positions_symbol_type", "symbol_id", "type"),
        Index("ix_positions_ticket", "ticket"),
    )

    def __repr__(self) -> str:
        return f"<Position(ticket={self.ticket}, symbol_id={self.symbol_id}, type={self.type.value}, vol={self.volume})>"


class Order(MarketBase):
    """Pending order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identifiers
    ticket: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    symbol_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("symbols.id"), nullable=False, index=True
    )

    # Order details
    type: Mapped[OrderType] = mapped_column(SQLEnum(OrderType), nullable=False)
    volume_initial: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    volume_current: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)

    # Prices
    price_open: Mapped[Decimal] = mapped_column(Numeric(15, 5), nullable=False)
    sl: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    tp: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    price_stop_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)

    # Status
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), default="started", nullable=False)

    # Metadata
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    magic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    time_setup: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    time_expiration: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    time_done: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Source
    source: Mapped[str] = mapped_column(String(50), default="mt5", nullable=False)

    # Relationships
    symbol: Mapped["Symbol"] = relationship("Symbol", back_populates="orders")

    __table_args__ = (
        Index("ix_orders_symbol_status", "symbol_id", "status"),
        Index("ix_orders_ticket", "ticket"),
        Index("ix_orders_expiration", "time_expiration"),
    )

    def __repr__(self) -> str:
        return f"<Order(ticket={self.ticket}, symbol_id={self.symbol_id}, type={self.type.value}, status={self.status.value})>"


# ──────────────────────────────────────────────────────────────────────────────
# TRADE SIGNALS
# ──────────────────────────────────────────────────────────────────────────────

class TradeSignal(MarketBase):
    """Trade signal from Valta Prime, TradingView, or algorithms."""

    __tablename__ = "trade_signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Signal details
    symbol_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("symbols.id"), nullable=False, index=True
    )
    signal_type: Mapped[SignalType] = mapped_column(SQLEnum(SignalType), nullable=False, index=True)
    source: Mapped[SignalSource] = mapped_column(SQLEnum(SignalSource), nullable=False, index=True)

    # Entry
    entry_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    entry_timeframe: Mapped[Optional[Timeframe]] = mapped_column(SQLEnum(Timeframe), nullable=True)

    # Risk management
    stop_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    take_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    risk_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    position_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8), nullable=True)

    # Analysis
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technical_factors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)  # active, executed, cancelled, expired
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    execution_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    execution_order_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    symbol: Mapped["Symbol"] = relationship("Symbol")

    __table_args__ = (
        Index("ix_trade_signals_symbol_status", "symbol_id", "status"),
        Index("ix_trade_signals_source_status", "source", "status"),
        Index("ix_trade_signals_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TradeSignal(symbol_id={self.symbol_id}, type={self.signal_type.value}, source={self.source.value})>"


# ──────────────────────────────────────────────────────────────────────────────
# SIMPLIFIED TABLES FOR DASHBOARD & ANALYTICS (MetaApi Optimized)
# ──────────────────────────────────────────────────────────────────────────────


class AccountSnapshotSimple(MarketBase):
    """Simplified account snapshot for equity curve and dashboard metrics."""

    __tablename__ = "account_snapshots_simple"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Core metrics for dashboard
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    margin: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    free_margin: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    open_pnl: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Source tracking
    source: Mapped[str] = mapped_column(String(50), default="metaapi", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_account_snapshots_simple_timestamp", "timestamp"),
    )


class TradesHistory(MarketBase):
    """Comprehensive trade history for analytics and reporting."""

    __tablename__ = "trades_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Trade identifiers
    deal_id: Mapped[BigInteger] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    order_id: Mapped[Optional[BigInteger]] = mapped_column(BigInteger, nullable=True, index=True)

    # Trade details
    symbol: Mapped[String(20)] = mapped_column(String(20), nullable=False, index=True)
    type: Mapped[String(10)] = mapped_column(String(10), nullable=False)  # buy/sell
    volume: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 5), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(12, 5), nullable=False)

    # Financials
    profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    swap: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Timing
    close_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False, index=True)

    # Source tracking
    source: Mapped[String(50)] = mapped_column(String(50), default="metaapi", nullable=False)
    received_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_trades_history_symbol", "symbol"),
        Index("ix_trades_history_close_time", "close_time"),
        Index("ix_trades_history_source", "source"),
    )


class DailySummaries(MarketBase):
    """Pre-aggregated daily summaries for fast trading calendar rendering."""

    __tablename__ = "daily_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Date key
    trade_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False, index=True)

    # Daily aggregates
    total_trades: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    net_pnl: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    win_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    # Source tracking
    source: Mapped[String(50)] = mapped_column(String(50), default="metaapi", nullable=False)
    received_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("trade_date", "source", name="uq_daily_summaries_date_source"),
        Index("ix_daily_summaries_trade_date", "trade_date"),
        Index("ix_daily_summaries_source", "source"),
    )