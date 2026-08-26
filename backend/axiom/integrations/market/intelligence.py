"""Market Intelligence Engine — Combines data, indicators, signals for decisions."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from pydantic import BaseModel, Field

from axiom.data.models import (
    Symbol,
    SymbolType,
    Timeframe,
    TradeSignal,
    SignalType,
    SignalSource,
    # Position and PositionType used only for type hints
)
# Use TYPE_CHECKING for SQLAlchemy models to avoid Pydantic core schema issues
if TYPE_CHECKING:
    from axiom.data.models import Position, PositionType
from axiom.data.repositories import MarketRepository
from axiom.runtime.logging import RuntimeLogger

if TYPE_CHECKING:
    from axiom.integrations.market import (
        MultiProviderAggregator,
        MarketProviderConfig,
        CryptoProvider,
        ForexProvider,
        StockProvider,
        TechnicalIndicators,
        IndicatorConfig,
        SignalGenerator,
        SignalConfig,
        SignalDirection,
        DEFAULT_RULES,
        SignalResult,
    )
    from axiom.integrations.layer import IntegrationLayer


class IntelligenceConfig(BaseModel):
    """Market intelligence engine configuration."""

    # Data refresh
    tick_refresh_seconds: int = 5
    rate_refresh_minutes: Dict[Timeframe, int] = Field(default_factory=lambda: {
        Timeframe.M1: 1,
        Timeframe.M5: 5,
        Timeframe.M15: 15,
        Timeframe.H1: 60,
        Timeframe.H4: 240,
        Timeframe.D1: 1440,
    })

    # Symbols to track
    tracked_symbols: List[str] = Field(default_factory=list)
    symbol_types: List[SymbolType] = Field(default_factory=lambda: [
        SymbolType.CRYPTO, SymbolType.FOREX, SymbolType.STOCK
    ])

    # Timeframes for analysis
    analysis_timeframes: List[Timeframe] = Field(default_factory=lambda: [
        Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1
    ])

    # Signal generation
    signal_config: Optional[SignalConfig] = None
    indicator_config: Optional["IndicatorConfig"] = None

    # Risk management
    max_open_positions: int = 10
    max_position_per_symbol: float = 1.0
    max_daily_loss_pct: float = 5.0
    max_drawdown_pct: float = 15.0

    # Provider settings
    provider_configs: List["MarketProviderConfig"] = Field(default_factory=list)

    # Auto-trading
    auto_execute: bool = False
    require_approval_above_confidence: float = 0.85


class MarketSnapshot(BaseModel):
    """Complete market snapshot for a symbol."""

    symbol: str
    symbol_type: SymbolType
    timestamp: datetime
    tick: Optional[Any] = None  # TickData
    rates: Dict[Timeframe, List[Any]] = Field(default_factory=dict)  # RateData lists
    indicators: Dict[Timeframe, Any] = Field(default_factory=dict)  # IndicatorSet
    signals: List[Any] = Field(default_factory=list)  # SignalResult
    positions: List["Position"] = Field(default_factory=list)
    account: Optional[Any] = None  # AccountSnapshot

    class Config:
        arbitrary_types_allowed = True


class MarketIntelligenceEngine:
    """Main market intelligence engine."""

    def __init__(
        self,
        integration_layer: "IntegrationLayer",
        repository: Optional[MarketRepository] = None,
        market_repo: Optional[MarketRepository] = None,
        config: Optional[IntelligenceConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        # Support both parameter names for backward compatibility
        self.repository = repository or market_repo
        self.config = config or IntelligenceConfig()
        self.logger = logger or RuntimeLogger()

        # Initialize components
        self._setup_providers()
        # Lazy import to avoid circular dependency
        from axiom.integrations.market import TechnicalIndicators, IndicatorConfig
        self.indicators = TechnicalIndicators(self.config.indicator_config, self.logger)

        # Lazy import for signal generator
        from axiom.integrations.market import SignalGenerator, SignalConfig, DEFAULT_RULES
        signal_config = self.config.signal_config or SignalConfig(rules=DEFAULT_RULES)
        self.signal_generator = SignalGenerator(signal_config, self.indicators, self.logger)

        # State
        self._snapshots: Dict[str, MarketSnapshot] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []

    def _setup_providers(self):
        """Initialize data providers."""
        # Lazy import to avoid circular dependency
        from axiom.integrations.market import (
            MultiProviderAggregator,
            MarketProviderConfig,
            CryptoProvider,
            ForexProvider,
            StockProvider,
        )

        providers = []
        for pconfig in self.config.provider_configs:
            if not pconfig.enabled:
                continue
            if "binance" in pconfig.base_url.lower() or pconfig.custom_params.get("type") == "crypto":
                providers.append(CryptoProvider(pconfig, self.logger))
            elif "alphavantage" in pconfig.base_url.lower() or "oanda" in pconfig.base_url.lower():
                if pconfig.custom_params.get("type") == "forex":
                    providers.append(ForexProvider(pconfig, self.logger))
                else:
                    providers.append(StockProvider(pconfig, self.logger))
            else:
                self.logger.warning(f"Unknown provider type for {pconfig.name}")

        self.aggregator: "MultiProviderAggregator" = MultiProviderAggregator(
            self.integration_layer, providers, self.logger
        )

    async def start(self):
        """Start the intelligence engine."""
        if self._running:
            return

        self._running = True
        self.logger.info("Starting Market Intelligence Engine")

        # Initial data load
        await self._refresh_all_symbols()

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._tick_loop()),
            asyncio.create_task(self._rate_loop()),
            asyncio.create_task(self._signal_loop()),
            asyncio.create_task(self._position_monitor_loop()),
        ]

        # Connect WebSockets
        for provider in self.aggregator.providers:
            if provider.config.ws_url:
                await provider.connect_websocket()
                if self.config.tracked_symbols:
                    await provider.subscribe_ticker(self.config.tracked_symbols)
                    for tf in self.config.analysis_timeframes:
                        await provider.subscribe_klines(self.config.tracked_symbols, tf)

    async def stop(self):
        """Stop the intelligence engine."""
        self._running = False
        self.logger.info("Stopping Market Intelligence Engine")

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        await self.aggregator.close_all()

    async def _refresh_all_symbols(self):
        """Refresh data for all tracked symbols."""
        symbols = self.config.tracked_symbols
        if not symbols:
            # Fetch from providers
            all_symbols = await self.aggregator.fetch_all_symbols()
            for provider_name, syms in all_symbols.items():
                for sym in syms:
                    if sym.symbol_type in self.config.symbol_types:
                        symbols.append(sym.symbol)
            self.config.tracked_symbols = list(set(symbols))

        # Refresh each symbol
        for symbol in symbols:
            await self._refresh_symbol(symbol)

    async def _refresh_symbol(self, symbol: str):
        """Refresh data for a single symbol."""
        snapshot = self._snapshots.get(symbol, MarketSnapshot(
            symbol=symbol,
            symbol_type=SymbolType.CRYPTO,  # Would determine from provider
            timestamp=datetime.utcnow(),
        ))

        # Fetch tick
        tick = await self.aggregator.fetch_ticker(symbol, snapshot.symbol_type)
        if tick:
            snapshot.tick = tick

        # Fetch rates for each timeframe
        for tf in self.config.analysis_timeframes:
            rates = await self.aggregator.fetch_klines(symbol, snapshot.symbol_type, tf, 500)
            snapshot.rates[tf] = rates

            # Calculate indicators
            if rates:
                snapshot.indicators[tf] = self.indicators.calculate_all(rates)

        snapshot.timestamp = datetime.utcnow()
        self._snapshots[symbol] = snapshot

        # Store ticks and rates in repository
        if tick:
            await self.repository.bulk_insert_ticks([tick])  # Adapt to model

        for tf, rates in snapshot.rates.items():
            if rates:
                await self.repository.bulk_insert_rates(rates)  # Adapt to model

    async def _tick_loop(self):
        """Background tick refresh loop."""
        while self._running:
            try:
                for symbol in self.config.tracked_symbols:
                    await self._refresh_symbol(symbol)
                await asyncio.sleep(self.config.tick_refresh_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Tick loop error: {e}")
                await asyncio.sleep(10)

    async def _rate_loop(self):
        """Background rate refresh loop (less frequent)."""
        while self._running:
            try:
                for symbol in self.config.tracked_symbols:
                    for tf in self.config.analysis_timeframes:
                        rates = await self.aggregator.fetch_klines(
                            symbol, SymbolType.CRYPTO, tf, 100
                        )
                        if rates:
                            self._snapshots[symbol].rates[tf] = rates
                            self._snapshots[symbol].indicators[tf] = self.indicators.calculate_all(rates)
                            await self.repository.bulk_insert_rates(rates)
                await asyncio.sleep(60)  # Base interval
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Rate loop error: {e}")
                await asyncio.sleep(30)

    async def _signal_loop(self):
        """Background signal generation loop."""
        while self._running:
            try:
                await self._generate_signals_for_all()
                await asyncio.sleep(60)  # Check signals every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Signal loop error: {e}")
                await asyncio.sleep(30)

    async def _generate_signals_for_all(self):
        """Generate signals for all tracked symbols."""
        for symbol in self.config.tracked_symbols:
            snapshot = self._snapshots.get(symbol)
            if not snapshot:
                continue

            for tf in self.config.analysis_timeframes:
                rates = snapshot.rates.get(tf, [])
                if len(rates) < 50:
                    continue

                # Get account info
                account = await self.repository.get_latest_account_snapshot(0)  # Would use real login
                balance = float(account.equity) if account else 10000

                positions = await self.repository.get_open_positions()

                signals = await self.signal_generator.generate_signals(
                    symbol=symbol,
                    rates=rates,
                    timeframe=tf,
                    account_balance=balance,
                    open_positions=len(positions),
                    daily_pnl=0.0,  # Would calculate
                )

                if signals:
                    snapshot.signals.extend(signals)

                    # Store signals
                    for sig in signals:
                        trade_signal = self.signal_generator.to_trade_signal(sig, symbol)
                        # Would need symbol_id
                        await self.repository.create_trade_signal(
                            symbol_id=0,
                            signal_type=trade_signal.signal_type,
                            source=trade_signal.source,
                            direction=trade_signal.direction,
                            entry_price=trade_signal.entry_price,
                            stop_loss=trade_signal.stop_loss,
                            take_profit=trade_signal.take_profit,
                            confidence=trade_signal.confidence,
                            reasoning=trade_signal.reasoning,
                            metadata=trade_signal.metadata,
                            expires_at=trade_signal.expires_at,
                        )

    async def _position_monitor_loop(self):
        """Monitor open positions for stop loss/take profit."""
        while self._running:
            try:
                positions = await self.repository.get_open_positions()
                for pos in positions:
                    snapshot = self._snapshots.get(pos.symbol)
                    if not snapshot or not snapshot.tick:
                        continue

                    current_price = float(snapshot.tick.last or snapshot.tick.bid)
                    entry_price = float(pos.price_open)

                    # Check stop loss / take profit
                    if pos.type == PositionType.BUY:
                        if pos.sl and current_price <= float(pos.sl):
                            self.logger.warning(f"Stop loss hit for {pos.ticket}")
                            # Would trigger close
                        elif pos.tp and current_price >= float(pos.tp):
                            self.logger.info(f"Take profit hit for {pos.ticket}")
                    elif pos.type == PositionType.SELL:
                        if pos.sl and current_price >= float(pos.sl):
                            self.logger.warning(f"Stop loss hit for {pos.ticket}")
                        elif pos.tp and current_price <= float(pos.tp):
                            self.logger.info(f"Take profit hit for {pos.ticket}")

                await asyncio.sleep(self.config.tick_refresh_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Position monitor error: {e}")
                await asyncio.sleep(10)

    def get_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        """Get current market snapshot."""
        return self._snapshots.get(symbol)

    def get_all_snapshots(self) -> Dict[str, MarketSnapshot]:
        """Get all market snapshots."""
        return self._snapshots.copy()

    async def get_signals(
        self,
        symbol: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[Any]:
        """Get recent signals."""
        if symbol:
            snapshot = self._snapshots.get(symbol)
            if not snapshot:
                return []
            return [s for s in snapshot.signals if s.confidence >= min_confidence]

        all_signals = []
        for snapshot in self._snapshots.values():
            all_signals.extend([s for s in snapshot.signals if s.confidence >= min_confidence])
        return all_signals

    async def analyze_symbol(
        self,
        symbol: str,
        timeframes: Optional[List[Timeframe]] = None,
    ) -> Dict[str, Any]:
        """Comprehensive symbol analysis."""
        timeframes = timeframes or self.config.analysis_timeframes
        snapshot = self._snapshots.get(symbol)

        if not snapshot:
            await self._refresh_symbol(symbol)
            snapshot = self._snapshots.get(symbol)

        if not snapshot:
            return {"error": "Symbol not found"}

        analysis = {
            "symbol": symbol,
            "timestamp": snapshot.timestamp,
            "current_price": float(snapshot.tick.last) if snapshot.tick else None,
            "spread": float(snapshot.tick.ask - snapshot.tick.bid) if snapshot.tick else None,
            "timeframes": {},
        }

        for tf in timeframes:
            indicators = snapshot.indicators.get(tf)
            rates = snapshot.rates.get(tf, [])

            tf_analysis = {
                "rates_count": len(rates),
                "indicators": {},
                "signals": [],
            }

            if indicators:
                for name, ind in indicators.indicators.items():
                    tf_analysis["indicators"][name] = {
                        "value": ind.value,
                        "metadata": ind.metadata,
                    }

            tf_signals = [s for s in snapshot.signals if s.metadata.get("timeframe") == tf]
            tf_analysis["signals"] = [
                {
                    "rule": s.rule_name,
                    "direction": s.direction.value,
                    "strength": s.strength.value,
                    "confidence": s.confidence,
                    "entry": s.entry_price,
                    "sl": s.stop_loss,
                    "tp": s.take_profit,
                }
                for s in tf_signals
            ]

            analysis["timeframes"][tf.value] = tf_analysis

        return analysis

    async def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market overview."""
        overview = {
            "timestamp": datetime.utcnow(),
            "symbols_tracked": len(self.config.tracked_symbols),
            "active_signals": 0,
            "by_type": {},
            "top_opportunities": [],
            "risk_alerts": [],
        }

        for symbol, snapshot in self._snapshots.items():
            sym_type = snapshot.symbol_type.value
            if sym_type not in overview["by_type"]:
                overview["by_type"][sym_type] = 0
            overview["by_type"][sym_type] += 1

            for sig in snapshot.signals:
                if sig.confidence >= self.config.require_approval_above_confidence:
                    overview["active_signals"] += 1
                    overview["top_opportunities"].append({
                        "symbol": symbol,
                        "direction": sig.direction.value,
                        "confidence": sig.confidence,
                        "entry": sig.entry_price,
                        "risk_reward": (sig.take_profit - sig.entry_price) / (sig.entry_price - sig.stop_loss)
                        if sig.stop_loss and sig.take_profit and sig.entry_price else 0,
                    })

        # Sort opportunities
        overview["top_opportunities"].sort(key=lambda x: x["confidence"], reverse=True)
        overview["top_opportunities"] = overview["top_opportunities"][:10]

        return overview


# Rebuild models to resolve forward references (Pydantic V2)
try:
    IntelligenceConfig.model_rebuild()
    MarketSnapshot.model_rebuild()
except Exception:
    pass