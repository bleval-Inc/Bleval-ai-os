"""JOURNAL Domain Models — Trading Journal for House of Valta.
Captures voice-driven trade journal entries with structured data,
preserves raw transcriptions, and links to MT5 trade data.
"""

import enum
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

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
    JSON,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom.data.database import DeclarativeBase
from axiom.data.models.market import Symbol


class JournalBase(DeclarativeBase):
    """Base for JOURNAL domain models."""
    metadata = MetaData(schema="journal")


class TradingSession(str, enum.Enum):
    """Forex trading sessions."""
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    OVERLAP_LONDON_NEWYORK = "london_new_york_overlap"
    OVERLAP_ASIAN_LONDON = "asian_london_overlap"


class TradeResult(str, enum.Enum):
    """Trade result classifications."""
    WIN = "win"
    LOSS = "loss"
    BREAK_EVEN = "break_even"
    PARTIAL_CLOSE = "partial_close"


class JournalEntryType(str, enum.Enum):
    """Types of journal entries."""
    TRADE_JOURNAL = "trade_journal"
    DAILY_REFLECTION = "daily_reflection"
    WEEKLY_REVIEW = "weekly_review"
    MONTHLY_REVIEW = "monthly_review"
    STRATEGY_NOTE = "strategy_note"
    PSYCHOLOGY_NOTE = "psychology_note"


class APlusClassification(str, enum.Enum):
    """A+ setup classification tiers."""
    A_PLUS = "a_plus"
    A = "a"
    B_PLUS = "b_plus"
    B = "b"
    C_PLUS = "c_plus"
    C = "c"
    D = "d"
    F = "f"


class JournalEntry(JournalBase):
    """Trading journal entry - captures voice-driven trade analysis and decisions."""

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Entry metadata
    entry_type: Mapped[JournalEntryType] = mapped_column(SQLEnum(JournalEntryType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timing
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    session: Mapped[Optional[TradingSession]] = mapped_column(SQLEnum(TradingSession), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Trade identification (links to MT5 data where available)
    symbol_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("market.symbols.id"), nullable=True, index=True
    )
    mt5_deal_id: Mapped[Optional[BigInteger]] = mapped_column(BigInteger, nullable=True, index=True)  # Links to MT5 deal
    mt5_order_id: Mapped[Optional[BigInteger]] = mapped_column(BigInteger, nullable=True, index=True)  # Links to MT5 order

    # Instrument details
    instrument_name: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)  # e.g., "XAUUSD", "US30"
    instrument_type: Mapped[Optional[String]] = mapped_column(String(20), nullable=True)  # From SymbolType enum

    # Voice-driven content (preserved raw transcription)
    raw_transcription: Mapped[Text] = mapped_column(Text, nullable=False)  # Original voice dictation
    structured_notes: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)  # Processed/structured version

    # Market analysis fields (captured from voice)
    market_analysis: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    higher_timeframe_bias: Mapped[Optional[String]] = mapped_column(String(50), nullable=True)  # e.g., "Bullish on Daily/H4"
    market_breakdown: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)

    # Trade setup and execution
    setup_description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    entry_reasoning: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    entry_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    entry_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Risk management
    stop_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    stop_loss_reason: Mapped[Optional[String]] = mapped_column(String(255), nullable=True)
    target_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    target_reason: Mapped[Optional[String]] = mapped_column(String(255), nullable=True)

    # Trade management
    lot_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8), nullable=True)
    trade_direction: Mapped[Optional[String]] = mapped_column(String(10), nullable=True)  # "BUY" or "SELL"

    # Trade outcome
    exit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 5), nullable=True)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    result: Mapped[Optional[TradeResult]] = mapped_column(SQLEnum(TradeResult), nullable=True, index=True)
    pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)  # Profit/Loss in account currency
    pnl_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)  # Percentage return

    # Invalidation and trade management notes
    invalidation_criteria: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    trade_management_notes: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    actual_exit_reason: Mapped[Optional[String]] = mapped_column(String(255), nullable=True)

    # Psychology and behavioral tracking
    psychology_state: Mapped[Optional[String]] = mapped_column(String(255), nullable=True)  # Emotional state during trade
    mistakes_made: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    what_went_well: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)

    # Strategy classification and performance
    a_plus_classification: Mapped[Optional[APlusClassification]] = mapped_column(SQLEnum(APlusClassification), nullable=True, index=True)
    setup_score: Mapped[Optional[Integer]] = mapped_column(Integer, nullable=True)  # 1-100 setup quality score

    # Metadata and tagging
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    symbol: Mapped[Optional["Symbol"]] = relationship("Symbol")

    # Indexes for common query patterns
    __table_args__ = (
        Index("ix_journal_entries_date_session", "date", "session"),
        Index("ix_journal_entries_symbol_result", "symbol_id", "result"),
        Index("ix_journal_entries_a_plus_date", "a_plus_classification", "date"),
        Index("ix_journal_entries_mt5_deal", "mt5_deal_id"),
        Index("ix_journal_entries_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry(id={self.id}, uuid='{self.uuid}', date='{self.date}', type='{self.entry_type.value}')>"


class JournalTemplate(JournalBase):
    """Templates for common journal entry types to ensure consistency."""

    __tablename__ = "journal_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[String]] = mapped_column(String(255), nullable=True)
    entry_type: Mapped[JournalEntryType] = mapped_column(SQLEnum(JournalEntryType), nullable=False)

    # Template structure - defines what fields should be prompted for
    template_structure: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON schema for the template
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Voice command triggers - phrases that activate this template
    voice_triggers: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<JournalTemplate(id={self.id}, name='{self.name}', type='{self.entry_type.value}')>"


class JournalAnalytics(JournalBase):
    """Pre-computed analytics for journal performance tracking."""

    __tablename__ = "journal_analytics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Time period
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    period_type: Mapped[String] = mapped_column(String(20), nullable=False)  # "daily", "weekly", "monthly", "session"

    # Performance metrics
    total_trades: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    # Financial metrics
    total_pnl: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    average_win: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    average_loss: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    profit_factor: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0, nullable=False)  # Gross profit / gross loss
    expectancy: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)  # Average expected value per trade

    # Risk metrics
    max_drawdown: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)  # Peak to trough decline
    max_consecutive_wins: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    max_consecutive_losses: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)

    # Setup quality metrics
    a_plus_setups: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    average_setup_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    # Session breakdown
    asian_session_trades: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    london_session_trades: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)
    new_york_session_trades: Mapped[Integer] = mapped_column(Integer, default=0, nullable=False)

    # Instrument breakdown (JSON for flexibility)
    instrument_performance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Psychology insights
    common_mistakes: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    psychological_patterns: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Metadata
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    source_trade_count: Mapped[Integer] = mapped_column(Integer, nullable=False)  # Number of trades used in calculation

    __table_args__ = (
        UniqueConstraint("period_start", "period_end", "period_type", name="uq_journal_analytics_period"),
        Index("ix_journal_analytics_period_type", "period_type"),
        Index("ix_journal_analytics_generated_at", "generated_at"),
    )

    def __repr__(self) -> str:
        return f"<JournalAnalytics(id={self.id}, period='{self.period_type}', trades={self.total_trades}, wr={self.win_rate}%)>"