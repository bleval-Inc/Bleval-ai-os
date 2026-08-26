"""Signal Generation — Rule-based and ML trading signals."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple, TYPE_CHECKING

from pydantic import BaseModel, Field

from axiom.data.models import SignalType, SignalSource, Timeframe, TradeSignal
from axiom.runtime.logging import RuntimeLogger

if TYPE_CHECKING:
    from axiom.integrations.market.indicators import TechnicalIndicators, IndicatorSet


class SignalDirection(str, Enum):
    """Signal direction."""

    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


class SignalStrength(str, Enum):
    """Signal strength."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class SignalRule(BaseModel):
    """Individual signal rule."""

    name: str
    condition: str  # Expression or function name
    direction: SignalDirection
    strength: SignalStrength = SignalStrength.MODERATE
    weight: float = 1.0
    timeframe: Timeframe = Timeframe.H1
    params: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class SignalConfig(BaseModel):
    """Signal generator configuration."""

    rules: List[SignalRule] = Field(default_factory=list)
    min_confidence: float = 0.6
    min_rules_triggered: int = 2
    max_signals_per_symbol_per_day: int = 10
    cooldown_minutes: int = 60
    risk_reward_ratio: float = 2.0
    max_position_size_pct: float = 5.0
    stop_loss_atr_mult: float = 2.0
    take_profit_atr_mult: float = 4.0


class SignalContext(BaseModel):
    """Context for signal evaluation."""

    symbol: str
    timeframe: Timeframe
    indicators: "IndicatorSet"
    current_price: float
    account_balance: float
    open_positions: int = 0
    daily_pnl: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SignalResult(BaseModel):
    """Result of signal evaluation."""

    rule_name: str
    triggered: bool
    direction: SignalDirection
    strength: SignalStrength
    confidence: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseSignalRule(ABC):
    """Base class for signal rules."""

    def __init__(self, rule: SignalRule, logger: Optional[RuntimeLogger] = None):
        self.rule = rule
        self.logger = logger or RuntimeLogger()

    @abstractmethod
    async def evaluate(self, context: SignalContext) -> SignalResult:
        """Evaluate the rule."""
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Built-in Signal Rules
# ──────────────────────────────────────────────────────────────────────────────

class MACrossoverRule(BaseSignalRule):
    """Moving Average Crossover."""

    async def evaluate(self, context: SignalContext) -> SignalResult:
        indicators = context.indicators
        fast_period = self.rule.params.get("fast_period", 9)
        slow_period = self.rule.params.get("slow_period", 21)

        fast_ma = indicators.get_value(f"EMA_{fast_period}")
        slow_ma = indicators.get_value(f"EMA_{slow_period}")
        prev_fast = indicators.get_value(f"EMA_{fast_period}_prev", fast_ma)
        prev_slow = indicators.get_value(f"EMA_{slow_period}_prev", slow_ma)

        if fast_ma is None or slow_ma is None:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=False,
                direction=SignalDirection.NEUTRAL,
                strength=SignalStrength.WEAK,
                confidence=0.0,
                reasoning="Insufficient MA data",
            )

        # Golden cross (bullish)
        if prev_fast <= prev_slow and fast_ma > slow_ma:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.LONG,
                strength=self.rule.strength,
                confidence=0.75,
                entry_price=context.current_price,
                reasoning=f"EMA{fast_period} crossed above EMA{slow_period}",
            )

        # Death cross (bearish)
        if prev_fast >= prev_slow and fast_ma < slow_ma:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.SHORT,
                strength=self.rule.strength,
                confidence=0.75,
                entry_price=context.current_price,
                reasoning=f"EMA{fast_period} crossed below EMA{slow_period}",
            )

        return SignalResult(
            rule_name=self.rule.name,
            triggered=False,
            direction=SignalDirection.NEUTRAL,
            strength=SignalStrength.WEAK,
            confidence=0.0,
            reasoning="No crossover",
        )


class RSIReversalRule(BaseSignalRule):
    """RSI Overbought/Oversold Reversal."""

    async def evaluate(self, context: SignalContext) -> SignalResult:
        rsi = context.indicators.get_value("RSI")
        if rsi is None:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=False,
                direction=SignalDirection.NEUTRAL,
                strength=SignalStrength.WEAK,
                confidence=0.0,
                reasoning="No RSI data",
            )

        overbought = self.rule.params.get("overbought", 70)
        oversold = self.rule.params.get("oversold", 30)

        # Oversold bounce
        if rsi <= oversold:
            strength = SignalStrength.STRONG if rsi <= oversold - 10 else SignalStrength.MODERATE
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.LONG,
                strength=strength,
                confidence=0.65 + (oversold - rsi) / 100,
                entry_price=context.current_price,
                reasoning=f"RSI oversold at {rsi:.1f}",
            )

        # Overbought reversal
        if rsi >= overbought:
            strength = SignalStrength.STRONG if rsi >= overbought + 10 else SignalStrength.MODERATE
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.SHORT,
                strength=strength,
                confidence=0.65 + (rsi - overbought) / 100,
                entry_price=context.current_price,
                reasoning=f"RSI overbought at {rsi:.1f}",
            )

        return SignalResult(
            rule_name=self.rule.name,
            triggered=False,
            direction=SignalDirection.NEUTRAL,
            strength=SignalStrength.WEAK,
            confidence=0.0,
            reasoning=f"RSI neutral at {rsi:.1f}",
        )


class MACDSignalRule(BaseSignalRule):
    """MACD Signal Line Crossover."""

    async def evaluate(self, context: SignalContext) -> SignalResult:
        macd = context.indicators.get_value("MACD")
        if not macd:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=False,
                direction=SignalDirection.NEUTRAL,
                strength=SignalStrength.WEAK,
                confidence=0.0,
                reasoning="No MACD data",
            )

        macd_val = macd.get("macd", 0)
        signal_val = macd.get("signal", 0)
        histogram = macd.get("histogram", 0)

        # Bullish crossover
        if macd_val > signal_val and histogram > 0:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.LONG,
                strength=SignalStrength.MODERATE,
                confidence=0.7,
                entry_price=context.current_price,
                reasoning=f"MACD bullish crossover (hist: {histogram:.4f})",
            )

        # Bearish crossover
        if macd_val < signal_val and histogram < 0:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.SHORT,
                strength=SignalStrength.MODERATE,
                confidence=0.7,
                entry_price=context.current_price,
                reasoning=f"MACD bearish crossover (hist: {histogram:.4f})",
            )

        return SignalResult(
            rule_name=self.rule.name,
            triggered=False,
            direction=SignalDirection.NEUTRAL,
            strength=SignalStrength.WEAK,
            confidence=0.0,
            reasoning="No MACD signal",
        )


class BollingerBreakoutRule(BaseSignalRule):
    """Bollinger Band Breakout/Squeeze."""

    async def evaluate(self, context: SignalContext) -> SignalResult:
        bb = context.indicators.get_value("BOLLINGER")
        if not bb:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=False,
                direction=SignalDirection.NEUTRAL,
                strength=SignalStrength.WEAK,
                confidence=0.0,
                reasoning="No Bollinger data",
            )

        upper = bb.get("upper", 0)
        lower = bb.get("lower", 0)
        middle = bb.get("middle", 0)
        price = context.current_price

        band_width = (upper - lower) / middle if middle != 0 else 0

        # Squeeze (low volatility -> potential breakout)
        if band_width < 0.05:  # 5% width
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.NEUTRAL,  # Direction unknown
                strength=SignalStrength.WEAK,
                confidence=0.5,
                entry_price=price,
                reasoning=f"Bollinger squeeze (width: {band_width:.2%})",
                metadata={"squeeze": True, "band_width": band_width},
            )

        # Upper breakout
        if price > upper:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.LONG,
                strength=SignalStrength.STRONG,
                confidence=0.75,
                entry_price=price,
                reasoning=f"Price broke above upper band ({price:.2f} > {upper:.2f})",
            )

        # Lower breakout
        if price < lower:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.SHORT,
                strength=SignalStrength.STRONG,
                confidence=0.75,
                entry_price=price,
                reasoning=f"Price broke below lower band ({price:.2f} < {lower:.2f})",
            )

        # Mean reversion signals
        if price > middle and context.indicators.get_value("RSI", 50) > 60:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.SHORT,
                strength=SignalStrength.MODERATE,
                confidence=0.6,
                entry_price=price,
                reasoning="Price at upper band with high RSI - mean reversion",
            )

        if price < middle and context.indicators.get_value("RSI", 50) < 40:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.LONG,
                strength=SignalStrength.MODERATE,
                confidence=0.6,
                entry_price=price,
                reasoning="Price at lower band with low RSI - mean reversion",
            )

        return SignalResult(
            rule_name=self.rule.name,
            triggered=False,
            direction=SignalDirection.NEUTRAL,
            strength=SignalStrength.WEAK,
            confidence=0.0,
            reasoning="Price within bands",
        )


class TrendFollowRule(BaseSignalRule):
    """Multi-timeframe Trend Following."""

    async def evaluate(self, context: SignalContext) -> SignalResult:
        # Check ADX for trend strength
        adx = context.indicators.get_value("ADX")
        if adx is None or adx < 25:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=False,
                direction=SignalDirection.NEUTRAL,
                strength=SignalStrength.WEAK,
                confidence=0.0,
                reasoning=f"Weak trend (ADX: {adx})",
            )

        # Check price vs MAs
        price = context.current_price
        ema_50 = context.indicators.get_value("EMA_50")
        ema_200 = context.indicators.get_value("EMA_200")

        if ema_50 and ema_200:
            if price > ema_50 > ema_200:
                return SignalResult(
                    rule_name=self.rule.name,
                    triggered=True,
                    direction=SignalDirection.LONG,
                    strength=SignalStrength.STRONG,
                    confidence=0.8,
                    entry_price=price,
                    reasoning=f"Strong uptrend: price > EMA50 > EMA200, ADX={adx:.1f}",
                )
            elif price < ema_50 < ema_200:
                return SignalResult(
                    rule_name=self.rule.name,
                    triggered=True,
                    direction=SignalDirection.SHORT,
                    strength=SignalStrength.STRONG,
                    confidence=0.8,
                    entry_price=price,
                    reasoning=f"Strong downtrend: price < EMA50 < EMA200, ADX={adx:.1f}",
                )

        return SignalResult(
            rule_name=self.rule.name,
            triggered=False,
            direction=SignalDirection.NEUTRAL,
            strength=SignalStrength.WEAK,
            confidence=0.0,
            reasoning="No clear trend",
        )


class IchimokuRule(BaseSignalRule):
    """Ichimoku Cloud Signals."""

    async def evaluate(self, context: SignalContext) -> SignalResult:
        ichimoku = context.indicators.get_value("ICHIMOKU")
        if not ichimoku:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=False,
                direction=SignalDirection.NEUTRAL,
                strength=SignalStrength.WEAK,
                confidence=0.0,
                reasoning="No Ichimoku data",
            )

        price = context.current_price
        tenkan = ichimoku.get("tenkan_sen")
        kijun = ichimoku.get("kijun_sen")
        senkou_a = ichimoku.get("senkou_a")
        senkou_b = ichimoku.get("senkou_b")

        if None in [tenkan, kijun, senkou_a, senkou_b]:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=False,
                direction=SignalDirection.NEUTRAL,
                strength=SignalStrength.WEAK,
                confidence=0.0,
                reasoning="Incomplete Ichimoku data",
            )

        cloud_top = max(senkou_a, senkou_b)
        cloud_bottom = min(senkou_a, senkou_b)

        # TK Cross
        tk_cross_bullish = tenkan > kijun
        tk_cross_bearish = tenkan < kijun

        # Price vs Cloud
        price_above_cloud = price > cloud_top
        price_in_cloud = cloud_bottom <= price <= cloud_top
        price_below_cloud = price < cloud_bottom

        # Kumo breakout
        if price_above_cloud and tk_cross_bullish:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.LONG,
                strength=SignalStrength.VERY_STRONG,
                confidence=0.85,
                entry_price=price,
                reasoning="Price above cloud with TK bullish cross",
            )

        if price_below_cloud and tk_cross_bearish:
            return SignalResult(
                rule_name=self.rule.name,
                triggered=True,
                direction=SignalDirection.SHORT,
                strength=SignalStrength.VERY_STRONG,
                confidence=0.85,
                entry_price=price,
                reasoning="Price below cloud with TK bearish cross",
            )

        # Cloud as support/resistance
        if price_in_cloud:
            if tk_cross_bullish:
                return SignalResult(
                    rule_name=self.rule.name,
                    triggered=True,
                    direction=SignalDirection.LONG,
                    strength=SignalStrength.MODERATE,
                    confidence=0.6,
                    entry_price=price,
                    reasoning="TK bullish cross within cloud",
                )
            elif tk_cross_bearish:
                return SignalResult(
                    rule_name=self.rule.name,
                    triggered=True,
                    direction=SignalDirection.SHORT,
                    strength=SignalStrength.MODERATE,
                    confidence=0.6,
                    entry_price=price,
                    reasoning="TK bearish cross within cloud",
                )

        return SignalResult(
            rule_name=self.rule.name,
            triggered=False,
            direction=SignalDirection.NEUTRAL,
            strength=SignalStrength.WEAK,
            confidence=0.0,
            reasoning="No Ichimoku signal",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Signal Generator
# ──────────────────────────────────────────────────────────────────────────────

class SignalGenerator:
    """Signal generator with rule engine."""

    def __init__(
        self,
        config: "SignalConfig",
        indicators: "TechnicalIndicators",
        logger: Optional[RuntimeLogger] = None,
    ):
        self.config = config
        self.indicators = indicators
        self.logger = logger or RuntimeLogger()
        self._rules: List[BaseSignalRule] = []
        self._last_signal: Dict[str, datetime] = {}
        self._daily_count: Dict[str, int] = {}
        self._last_day: Optional[datetime] = None
        self._build_rules()

    def _build_rules(self):
        """Build rule instances from config."""
        rule_map = {
            "ma_crossover": MACrossoverRule,
            "rsi_reversal": RSIReversalRule,
            "macd_signal": MACDSignalRule,
            "bollinger_breakout": BollingerBreakoutRule,
            "trend_follow": TrendFollowRule,
            "ichimoku": IchimokuRule,
        }

        for rule_config in self.config.rules:
            if not rule_config.enabled:
                continue
            rule_class = rule_map.get(rule_config.condition)
            if rule_class:
                self._rules.append(rule_class(rule_config, self.logger))

    def _check_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in cooldown."""
        last = self._last_signal.get(symbol)
        if last:
            elapsed = (datetime.utcnow() - last).total_seconds() / 60
            if elapsed < self.config.cooldown_minutes:
                return False
        return True

    def _check_daily_limit(self, symbol: str) -> bool:
        """Check daily signal limit."""
        today = datetime.utcnow().date()
        if self._last_day != today:
            self._daily_count.clear()
            self._last_day = today

        return self._daily_count.get(symbol, 0) < self.config.max_signals_per_symbol_per_day

    def _calculate_levels(
        self,
        direction: SignalDirection,
        entry: float,
        atr: float,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate stop loss and take profit."""
        if direction in (SignalDirection.LONG, SignalDirection.CLOSE_SHORT):
            sl = entry - (atr * self.config.stop_loss_atr_mult)
            tp = entry + (atr * self.config.take_profit_atr_mult)
        elif direction in (SignalDirection.SHORT, SignalDirection.CLOSE_LONG):
            sl = entry + (atr * self.config.stop_loss_atr_mult)
            tp = entry - (atr * self.config.take_profit_atr_mult)
        else:
            return None, None
        return sl, tp

    async def generate_signals(
        self,
        symbol: str,
        rates: List[Any],  # MarketRate objects
        timeframe: Timeframe = Timeframe.H1,
        account_balance: float = 10000,
        open_positions: int = 0,
        daily_pnl: float = 0.0,
    ) -> List[SignalResult]:
        """Generate signals for a symbol."""
        if not self._check_cooldown(symbol) or not self._check_daily_limit(symbol):
            return []

        # Calculate indicators
        indicator_set = self.indicators.calculate_all(rates)
        current_price = float(rates[-1].close) if rates else 0
        atr = indicator_set.get_value("ATR", 0)

        context = SignalContext(
            symbol=symbol,
            timeframe=timeframe,
            indicators=indicator_set,
            current_price=current_price,
            account_balance=account_balance,
            open_positions=open_positions,
            daily_pnl=daily_pnl,
        )

        # Evaluate all rules
        results = []
        for rule in self._rules:
            if rule.rule.timeframe != timeframe:
                continue
            result = await rule.evaluate(context)
            if result.triggered:
                # Add risk management levels
                if result.entry_price and atr > 0:
                    sl, tp = self._calculate_levels(result.direction, result.entry_price, atr)
                    result.stop_loss = sl
                    result.take_profit = tp
                results.append(result)

        # Filter by minimum rules triggered
        if len(results) < self.config.min_rules_triggered:
            return []

        # Aggregate signals
        final_signals = self._aggregate_signals(results, symbol, timeframe, current_price, atr)

        # Update tracking
        for sig in final_signals:
            self._last_signal[symbol] = datetime.utcnow()
            self._daily_count[symbol] = self._daily_count.get(symbol, 0) + 1

        return final_signals

    def _aggregate_signals(
        self,
        results: List[SignalResult],
        symbol: str,
        timeframe: Timeframe,
        price: float,
        atr: float,
    ) -> List[SignalResult]:
        """Aggregate multiple rule results into final signals."""
        if not results:
            return []

        # Group by direction
        long_signals = [r for r in results if r.direction == SignalDirection.LONG]
        short_signals = [r for r in results if r.direction == SignalDirection.SHORT]
        neutral_signals = [r for r in results if r.direction == SignalDirection.NEUTRAL]

        # Weighted confidence
        long_weight = sum(r.confidence * r.rule.weight if hasattr(r, 'rule') else r.confidence for r in long_signals)
        short_weight = sum(r.confidence * r.rule.weight if hasattr(r, 'rule') else r.confidence for r in short_signals)

        final = []

        if long_weight > short_weight and long_weight > 0:
            avg_confidence = sum(r.confidence for r in long_signals) / len(long_signals)
            if avg_confidence >= self.config.min_confidence:
                sl, tp = self._calculate_levels(SignalDirection.LONG, price, atr)
                final.append(SignalResult(
                    rule_name="AGGREGATED_LONG",
                    triggered=True,
                    direction=SignalDirection.LONG,
                    strength=SignalStrength.STRONG if avg_confidence > 0.8 else SignalStrength.MODERATE,
                    confidence=avg_confidence,
                    entry_price=price,
                    stop_loss=sl,
                    take_profit=tp,
                    reasoning=f"{len(long_signals)} rules triggered: " + ", ".join(r.rule_name for r in long_signals),
                    metadata={"rules": [r.rule_name for r in long_signals]},
                ))

        elif short_weight > long_weight and short_weight > 0:
            avg_confidence = sum(r.confidence for r in short_signals) / len(short_signals)
            if avg_confidence >= self.config.min_confidence:
                sl, tp = self._calculate_levels(SignalDirection.SHORT, price, atr)
                final.append(SignalResult(
                    rule_name="AGGREGATED_SHORT",
                    triggered=True,
                    direction=SignalDirection.SHORT,
                    strength=SignalStrength.STRONG if avg_confidence > 0.8 else SignalStrength.MODERATE,
                    confidence=avg_confidence,
                    entry_price=price,
                    stop_loss=sl,
                    take_profit=tp,
                    reasoning=f"{len(short_signals)} rules triggered: " + ", ".join(r.rule_name for r in short_signals),
                    metadata={"rules": [r.rule_name for r in short_signals]},
                ))

        # Include squeeze/neutral signals as info
        for sig in neutral_signals:
            if sig.confidence > 0.5:
                final.append(sig)

        return final

    def to_trade_signal(
        self, result: SignalResult, symbol: str, source: SignalSource = SignalSource.TECHNICAL
    ) -> TradeSignal:
        """Convert signal result to TradeSignal model."""
        signal_type_map = {
            SignalDirection.LONG: SignalType.ENTRY_LONG,
            SignalDirection.SHORT: SignalType.ENTRY_SHORT,
            SignalDirection.CLOSE_LONG: SignalType.EXIT_LONG,
            SignalDirection.CLOSE_SHORT: SignalType.EXIT_SHORT,
        }

        return TradeSignal(
            symbol_id=0,  # Would be resolved by caller
            signal_type=signal_type_map.get(result.direction, SignalType.ENTRY_LONG),
            source=source,
            direction=result.direction.value,
            entry_price=Decimal(str(result.entry_price)) if result.entry_price else None,
            stop_loss=Decimal(str(result.stop_loss)) if result.stop_loss else None,
            take_profit=Decimal(str(result.take_profit)) if result.take_profit else None,
            confidence=result.confidence,
            reasoning=result.reasoning,
            metadata=result.metadata,
            expires_at=datetime.utcnow() + timedelta(hours=4),
        )


# Default rule configuration
DEFAULT_RULES = [
    SignalRule(name="ma_cross", condition="ma_crossover", direction=SignalDirection.LONG, weight=1.0),
    SignalRule(name="rsi_rev", condition="rsi_reversal", direction=SignalDirection.LONG, weight=0.8),
    SignalRule(name="macd_cross", condition="macd_signal", direction=SignalDirection.LONG, weight=1.0),
    SignalRule(name="bb_break", condition="bollinger_breakout", direction=SignalDirection.LONG, weight=1.2),
    SignalRule(name="trend", condition="trend_follow", direction=SignalDirection.LONG, weight=1.5),
    SignalRule(name="ichimoku", condition="ichimoku", direction=SignalDirection.LONG, weight=1.5),
]

# Rebuild models to resolve forward references (Pydantic V2)
try:
    SignalConfig.model_rebuild()
    SignalResult.model_rebuild()
except Exception:
    pass