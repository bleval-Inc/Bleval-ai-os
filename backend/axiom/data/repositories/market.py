"""MARKET Repository — Data access for market data, trading, signals."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.data.models import (
    MarketBase,
    Symbol,
    MarketTick,
    MarketRate,
    AccountSnapshot,
    Position,
    Order,
    TradeSignal,
    SymbolType,
    Timeframe,
    PositionType,
    OrderStatus,
    SignalType,
    SignalSource,
)

if TYPE_CHECKING:
    from axiom.runtime.logging import RuntimeLogger


class MarketRepository:
    """Repository for MARKET domain operations."""

    def __init__(self, session: AsyncSession, logger: Optional["RuntimeLogger"] = None) -> None:
        self.session = session
        from axiom.runtime.logging import RuntimeLogger
        self.logger = logger or RuntimeLogger()

    # ──────────────────────────────────────────────────────────────────────────────
    # SYMBOLS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_symbol(self, **kwargs) -> Symbol:
        """Create a new symbol."""
        symbol = Symbol(**kwargs)
        self.session.add(symbol)
        await self.session.flush()
        return symbol

    async def get_symbol(self, symbol_id: int) -> Optional[Symbol]:
        """Get symbol by ID."""
        result = await self.session.execute(select(Symbol).where(Symbol.id == symbol_id))
        return result.scalar_one_or_none()

    async def get_symbol_by_name(self, name: str) -> Optional[Symbol]:
        """Get symbol by name."""
        result = await self.session.execute(select(Symbol).where(Symbol.name == name))
        return result.scalar_one_or_none()

    async def list_symbols(
        self,
        symbol_type: Optional[SymbolType] = None,
        is_active: Optional[bool] = True,
        currency_base: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Symbol]:
        """List symbols."""
        query = select(Symbol).order_by(Symbol.name)
        if symbol_type:
            query = query.where(Symbol.symbol_type == symbol_type)
        if is_active is not None:
            query = query.where(Symbol.is_active == is_active)
        if currency_base:
            query = query.where(Symbol.currency_base == currency_base)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # MARKET TICKS
    # ──────────────────────────────────────────────────────────────────────────────

    async def bulk_insert_ticks(self, ticks: List[MarketTick]) -> int:
        """Bulk insert market ticks."""
        if not ticks:
            return 0
        self.session.add_all(ticks)
        await self.session.flush()
        return len(ticks)

    async def get_latest_tick(self, symbol_id: int) -> Optional[MarketTick]:
        """Get latest tick for symbol."""
        query = (
            select(MarketTick)
            .where(MarketTick.symbol_id == symbol_id)
            .order_by(desc(MarketTick.timestamp))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ticks_range(
        self,
        symbol_id: int,
        start: datetime,
        end: datetime,
        limit: int = 10000,
    ) -> List[MarketTick]:
        """Get ticks in time range."""
        query = (
            select(MarketTick)
            .where(
                and_(
                    MarketTick.symbol_id == symbol_id,
                    MarketTick.timestamp >= start,
                    MarketTick.timestamp <= end,
                )
            )
            .order_by(desc(MarketTick.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_tick_stats(self, symbol_id: int, hours: int = 24) -> Dict[str, Any]:
        """Get tick statistics."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = select(
            func.count(MarketTick.id).label("count"),
            func.min(MarketTick.bid).label("min_bid"),
            func.max(MarketTick.bid).label("max_bid"),
            func.avg(MarketTick.bid).label("avg_bid"),
            func.min(MarketTick.ask).label("min_ask"),
            func.max(MarketTick.ask).label("max_ask"),
            func.avg(MarketTick.ask).label("avg_ask"),
        ).where(
            and_(
                MarketTick.symbol_id == symbol_id,
                MarketTick.timestamp >= cutoff,
            )
        )
        result = await self.session.execute(query)
        row = result.one()
        return {
            "count": row.count or 0,
            "min_bid": float(row.min_bid or 0),
            "max_bid": float(row.max_bid or 0),
            "avg_bid": float(row.avg_bid or 0),
            "min_ask": float(row.min_ask or 0),
            "max_ask": float(row.max_ask or 0),
            "avg_ask": float(row.avg_ask or 0),
            "avg_spread": float((row.avg_ask or 0) - (row.avg_bid or 0)),
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # MARKET RATES (OHLCV)
    # ──────────────────────────────────────────────────────────────────────────────

    async def bulk_insert_rates(self, rates: List[MarketRate]) -> int:
        """Bulk insert market rates (upsert)."""
        if not rates:
            return 0
        # For SQLite, use INSERT OR REPLACE
        # For PostgreSQL, would use ON CONFLICT
        self.session.add_all(rates)
        await self.session.flush()
        return len(rates)

    async def get_latest_rate(
        self, symbol_id: int, timeframe: Timeframe
    ) -> Optional[MarketRate]:
        """Get latest rate for symbol/timeframe."""
        query = (
            select(MarketRate)
            .where(
                and_(
                    MarketRate.symbol_id == symbol_id,
                    MarketRate.timeframe == timeframe,
                )
            )
            .order_by(desc(MarketRate.timestamp))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_rates_range(
        self,
        symbol_id: int,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> List[MarketRate]:
        """Get rates in time range."""
        query = (
            select(MarketRate)
            .where(
                and_(
                    MarketRate.symbol_id == symbol_id,
                    MarketRate.timeframe == timeframe,
                    MarketRate.timestamp >= start,
                    MarketRate.timestamp <= end,
                )
            )
            .order_by(MarketRate.timestamp)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_rates_for_indicators(
        self, symbol_id: int, timeframe: Timeframe, count: int = 500
    ) -> List[MarketRate]:
        """Get recent rates for indicator calculations."""
        query = (
            select(MarketRate)
            .where(
                and_(
                    MarketRate.symbol_id == symbol_id,
                    MarketRate.timeframe == timeframe,
                    MarketRate.is_complete == True,
                )
            )
            .order_by(desc(MarketRate.timestamp))
            .limit(count)
        )
        result = await self.session.execute(query)
        rates = list(result.scalars().all())
        return list(reversed(rates))  # Return chronological

    # ──────────────────────────────────────────────────────────────────────────────
    # ACCOUNT SNAPSHOTS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_account_snapshot(self, **kwargs) -> AccountSnapshot:
        """Create account snapshot."""
        snapshot = AccountSnapshot(**kwargs)
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_latest_account_snapshot(self, login: int) -> Optional[AccountSnapshot]:
        """Get latest account snapshot."""
        query = (
            select(AccountSnapshot)
            .where(AccountSnapshot.login == login)
            .order_by(desc(AccountSnapshot.timestamp))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_account_equity_curve(
        self, login: int, hours: int = 168
    ) -> List[AccountSnapshot]:
        """Get account equity curve."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(AccountSnapshot)
            .where(
                and_(
                    AccountSnapshot.login == login,
                    AccountSnapshot.timestamp >= cutoff,
                )
            )
            .order_by(AccountSnapshot.timestamp)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # POSITIONS
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_position(self, position: Position) -> Position:
        """Upsert position (by ticket)."""
        existing = await self.get_position_by_ticket(position.ticket)
        if existing:
            for key, value in position.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(position)
            await self.session.flush()
            return position

    async def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """Get position by ticket."""
        query = select(Position).where(Position.ticket == ticket)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_open_positions(
        self, symbol_id: Optional[int] = None, position_type: Optional[PositionType] = None
    ) -> List[Position]:
        """Get all open positions."""
        query = select(Position).order_by(desc(Position.time_open))
        if symbol_id:
            query = query.where(Position.symbol_id == symbol_id)
        if position_type:
            query = query.where(Position.type == position_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_positions_summary(self) -> Dict[str, Any]:
        """Get positions summary."""
        query = select(
            func.count(Position.id).label("count"),
            func.sum(Position.volume).label("total_volume"),
            func.sum(Position.profit).label("total_profit"),
            func.sum(Position.swap).label("total_swap"),
            func.sum(Position.commission).label("total_commission"),
        )
        result = await self.session.execute(query)
        row = result.one()
        return {
            "count": row.count or 0,
            "total_volume": float(row.total_volume or 0),
            "total_profit": float(row.total_profit or 0),
            "total_swap": float(row.total_swap or 0),
            "total_commission": float(row.total_commission or 0),
            "net_profit": float((row.total_profit or 0) + (row.total_swap or 0) + (row.total_commission or 0)),
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # ORDERS
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_order(self, order: Order) -> Order:
        """Upsert order (by ticket)."""
        existing = await self.get_order_by_ticket(order.ticket)
        if existing:
            for key, value in order.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(order)
            await self.session.flush()
            return order

    async def get_order_by_ticket(self, ticket: int) -> Optional[Order]:
        """Get order by ticket."""
        query = select(Order).where(Order.ticket == ticket)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_orders(
        self, symbol_id: Optional[int] = None
    ) -> List[Order]:
        """Get pending orders."""
        query = (
            select(Order)
            .where(Order.status == OrderStatus.PENDING)
            .order_by(desc(Order.time_setup))
        )
        if symbol_id:
            query = query.where(Order.symbol_id == symbol_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # TRADE SIGNALS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_trade_signal(self, **kwargs) -> TradeSignal:
        """Create a new trade signal."""
        signal = TradeSignal(**kwargs)
        self.session.add(signal)
        await self.session.flush()
        return signal

    async def get_trade_signal(self, signal_id: int) -> Optional[TradeSignal]:
        """Get trade signal by ID."""
        result = await self.session.execute(select(TradeSignal).where(TradeSignal.id == signal_id))
        return result.scalar_one_or_none()

    async def get_active_signals(
        self,
        symbol_id: Optional[int] = None,
        source: Optional[SignalSource] = None,
        signal_type: Optional[SignalType] = None,
    ) -> List[TradeSignal]:
        """Get active trade signals."""
        query = (
            select(TradeSignal)
            .where(
                and_(
                    TradeSignal.status == "active",
                    TradeSignal.expires_at.is_(None) | (TradeSignal.expires_at > datetime.utcnow()),
                )
            )
            .order_by(desc(TradeSignal.created_at))
        )
        if symbol_id:
            query = query.where(TradeSignal.symbol_id == symbol_id)
        if source:
            query = query.where(TradeSignal.source == source)
        if signal_type:
            query = query.where(TradeSignal.signal_type == signal_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_signal_status(
        self,
        signal_id: int,
        status: str,
        executed_at: Optional[datetime] = None,
        execution_price: Optional[Decimal] = None,
        execution_order_id: Optional[int] = None,
    ) -> Optional[TradeSignal]:
        """Update signal execution status."""
        signal = await self.get_trade_signal(signal_id)
        if signal:
            signal.status = status
            if executed_at:
                signal.executed_at = executed_at
            if execution_price:
                signal.execution_price = execution_price
            if execution_order_id:
                signal.execution_order_id = execution_order_id
            signal.updated_at = datetime.utcnow()
            await self.session.flush()
        return signal

    async def expire_old_signals(self) -> int:
        """Mark expired signals."""
        query = (
            select(TradeSignal)
            .where(
                and_(
                    TradeSignal.status == "active",
                    TradeSignal.expires_at.is_not(None),
                    TradeSignal.expires_at <= datetime.utcnow(),
                )
            )
        )
        result = await self.session.execute(query)
        signals = list(result.scalars().all())
        for signal in signals:
            signal.status = "expired"
            signal.updated_at = datetime.utcnow()
        await self.session.flush()
        return len(signals)