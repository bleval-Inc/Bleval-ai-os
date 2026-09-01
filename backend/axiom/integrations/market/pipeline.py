"""Market Data Pipeline — Orchestrates ingestion, processing, and signal generation."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from axiom.data.models import (
    Symbol,
    SymbolType,
    Timeframe,
    MarketTick,
    MarketRate,
    TradeSignal,
    SignalType,
    SignalSource,
)
from axiom.data.repositories import MarketRepository
from axiom.runtime.logging import RuntimeLogger

if TYPE_CHECKING:
    from axiom.integrations.market import (
        MarketIntelligenceEngine,
        IntelligenceConfig,
        MarketProviderConfig,
        MultiProviderAggregator,
    )
    from axiom.integrations.layer import IntegrationLayer


class MarketPipeline:
    """Complete market data pipeline."""

    def __init__(
        self,
        integration_layer: "IntegrationLayer",
        repository: MarketRepository,
        provider_configs: List["MarketProviderConfig"],
        tracked_symbols: List[str],
        config: Optional["IntelligenceConfig"] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        # Lazy import to avoid circular dependency
        from axiom.integrations.market import MarketIntelligenceEngine, IntelligenceConfig

        # Build intelligence config
        intel_config = config or IntelligenceConfig()
        intel_config.provider_configs = provider_configs
        intel_config.tracked_symbols = tracked_symbols

        self.engine = MarketIntelligenceEngine(
            integration_layer=integration_layer,
            repository=repository,
            config=intel_config,
            logger=self.logger
        )

    async def start(self):
        """Start the pipeline."""
        self.logger.info("Starting Market Pipeline")
        await self.engine.start()

    async def stop(self):
        """Stop the pipeline."""
        self.logger.info("Stopping Market Pipeline")
        await self.engine.stop()

    async def ingest_historical(
        self,
        symbol: str,
        symbol_type: SymbolType,
        timeframe: Timeframe,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Ingest historical data for backtesting."""
        stats = {"symbol": symbol, "timeframe": timeframe.value, "inserted": 0, "errors": []}

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            # Fetch in chunks (max 1000 per request)
            chunk_days = 30 if timeframe >= Timeframe.H1 else 7
            current_start = start_time

            while current_start < end_time:
                current_end = min(current_start + timedelta(days=chunk_days), end_time)

                rates = await self.engine.aggregator.fetch_klines(
                    symbol, symbol_type, timeframe, 1000, current_start, current_end
                )

                if rates:
                    # Convert to MarketRate models
                    for rate in rates:
                        market_rate = MarketRate(
                            symbol_id=0,  # Would resolve
                            timeframe=timeframe,
                            timestamp=rate.timestamp,
                            open=rate.open,
                            high=rate.high,
                            low=rate.low,
                            close=rate.close,
                            volume=rate.volume,
                            is_complete=rate.is_complete,
                            source=rate.exchange,
                        )
                        self.repository.session.add(market_rate)
                    await self.repository.session.flush()
                    stats["inserted"] += len(rates)

                current_start = current_end
                await asyncio.sleep(0.1)  # Rate limit

        except Exception as e:
            stats["errors"].append(str(e))
            self.logger.error(f"Historical ingest error: {e}")

        return stats

    async def ingest_realtime_tick(
        self, symbol: str, symbol_type: SymbolType
    ) -> Optional[MarketTick]:
        """Ingest a single real-time tick."""
        try:
            tick = await self.engine.aggregator.fetch_ticker(symbol, symbol_type)
            if tick:
                market_tick = MarketTick(
                    symbol_id=0,  # Would resolve
                    timestamp=tick.timestamp,
                    bid=tick.bid,
                    ask=tick.ask,
                    last=tick.last,
                    volume=tick.volume,
                    source=tick.exchange,
                )
                self.repository.session.add(market_tick)
                await self.repository.session.flush()
                return market_tick
        except Exception as e:
            self.logger.error(f"Realtime tick ingest error: {e}")
        return None

    async def generate_and_store_signal(
        self,
        symbol: str,
        timeframe: Timeframe,
        source: SignalSource = SignalSource.TECHNICAL,
    ) -> Optional[TradeSignal]:
        """Generate and store a signal."""
        snapshot = self.engine.get_snapshot(symbol)
        if not snapshot:
            return None

        rates = snapshot.rates.get(timeframe, [])
        if len(rates) < 50:
            return None

        account = await self.repository.get_latest_account_snapshot(0)
        balance = float(account.equity) if account else 10000

        positions = await self.repository.get_open_positions()

        signals = await self.engine.signal_generator.generate_signals(
            symbol=symbol,
            rates=rates,
            timeframe=timeframe,
            account_balance=balance,
            open_positions=len(positions),
        )

        if signals:
            best_signal = max(signals, key=lambda s: s.confidence)
            trade_signal = self.engine.signal_generator.to_trade_signal(
                best_signal, symbol, source
            )

            # Resolve symbol_id
            # symbol_obj = await self.repository.get_symbol_by_name(symbol)

            stored = await self.repository.create_trade_signal(
                symbol_id=0,  # symbol_obj.id if symbol_obj else 0
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

            return stored

        return None

    async def run_analysis_cycle(self) -> Dict[str, Any]:
        """Run a complete analysis cycle for all symbols."""
        results = {
            "timestamp": datetime.utcnow(),
            "symbols_analyzed": 0,
            "signals_generated": 0,
            "errors": [],
        }

        for symbol in self.engine.config.tracked_symbols:
            try:
                analysis = await self.engine.analyze_symbol(symbol)
                if "error" not in analysis:
                    results["symbols_analyzed"] += 1
                    tf_signals = sum(len(tf.get("signals", [])) for tf in analysis.get("timeframes", {}).values())
                    results["signals_generated"] += tf_signals
            except Exception as e:
                results["errors"].append(f"{symbol}: {e}")

        return results

    async def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get portfolio-level metrics."""
        positions = await self.repository.get_open_positions()
        summary = await self.repository.get_positions_summary()

        account = await self.repository.get_latest_account_snapshot(0)
        equity = float(account.equity) if account else 0
        balance = float(account.balance) if account else 0

        return {
            "equity": equity,
            "balance": balance,
            "unrealized_pnl": equity - balance,
            "positions": summary,
            "margin_level": (equity / float(account.margin)) * 100 if account and account.margin else 0,
            "free_margin": float(account.free_margin) if account else 0,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check pipeline health."""
        health = {
            "status": "healthy",
            "engine_running": self.engine._running,
            "symbols_tracked": len(self.engine.config.tracked_symbols),
            "snapshots_active": len(self.engine._snapshots),
            "providers": {},
            "last_update": None,
        }

        # Check providers
        for provider in self.engine.aggregator.providers:
            health["providers"][provider.exchange_name] = {
                "connected": provider._ws_connection is not None and not provider._ws_connection.closed,
                "symbols_cached": len(provider._symbol_cache),
            }

        # Check data freshness
        latest = None
        for snapshot in self.engine._snapshots.values():
            if latest is None or snapshot.timestamp > latest:
                latest = snapshot.timestamp
        health["last_update"] = latest

        # Determine status
        if not self.engine._running:
            health["status"] = "stopped"
        elif latest and (datetime.utcnow() - latest).total_seconds() > 120:
            health["status"] = "stale"
        elif any(not p["connected"] for p in health["providers"].values()):
            health["status"] = "degraded"

        return health