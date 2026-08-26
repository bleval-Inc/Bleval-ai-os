"""Technical Indicators — Pure Python implementation for market analysis."""

import math
from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

from axiom.data.models import Timeframe, MarketRate
from axiom.runtime.logging import RuntimeLogger


class IndicatorConfig(BaseModel):
    """Configuration for indicator calculations."""

    # Moving averages
    sma_periods: List[int] = Field(default_factory=lambda: [20, 50, 200])
    ema_periods: List[int] = Field(default_factory=lambda: [9, 21, 50])

    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # RSI
    rsi_period: int = 14
    rsi_overbought: float = 70
    rsi_oversold: float = 30

    # Bollinger Bands
    bb_period: int = 20
    bb_std: float = 2.0

    # ATR
    atr_period: int = 14

    # Stochastic
    stoch_k: int = 14
    stoch_d: int = 3

    # ADX
    adx_period: int = 14

    # Ichimoku
    ichimoku_tenkan: int = 9
    ichimoku_kijun: int = 26
    ichimoku_senkou_b: int = 52

    # Volume
    volume_sma_period: int = 20


class IndicatorResult(BaseModel):
    """Single indicator result."""

    name: str
    value: Any
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndicatorSet(BaseModel):
    """Complete set of indicators for a symbol/timeframe."""

    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    indicators: Dict[str, IndicatorResult] = Field(default_factory=dict)

    def get(self, name: str) -> Optional[IndicatorResult]:
        return self.indicators.get(name)

    def get_value(self, name: str, default: Any = None) -> Any:
        result = self.indicators.get(name)
        return result.value if result else default


class TechnicalIndicators:
    """Technical indicator calculator."""

    def __init__(
        self,
        config: Optional[IndicatorConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.config = config or IndicatorConfig()
        self.logger = logger or RuntimeLogger()

    def _to_floats(self, rates: List[MarketRate]) -> Tuple[
        List[float], List[float], List[float], List[float], List[float]
    ]:
        """Convert rates to float arrays."""
        opens = [float(r.open) for r in rates]
        highs = [float(r.high) for r in rates]
        lows = [float(r.low) for r in rates]
        closes = [float(r.close) for r in rates]
        volumes = [float(r.volume) for r in rates]
        return opens, highs, lows, closes, volumes

    def _to_numpy(self, rates: List[MarketRate]) -> Dict[str, np.ndarray]:
        """Convert rates to numpy arrays."""
        opens, highs, lows, closes, volumes = self._to_floats(rates)
        return {
            "open": np.array(opens),
            "high": np.array(highs),
            "low": np.array(lows),
            "close": np.array(closes),
            "volume": np.array(volumes),
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # Moving Averages
    # ──────────────────────────────────────────────────────────────────────────────

    @staticmethod
    def sma(data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average (static version for backward compatibility)."""
        if len(data) < period:
            return np.full_like(data, np.nan)
        return np.convolve(data, np.ones(period) / period, mode="valid")

    @staticmethod
    def ema(data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average (static version for backward compatibility)."""
        if len(data) < period:
            return np.full_like(data, np.nan)
        alpha = 2.0 / (period + 1)
        ema_values = np.full_like(data, np.nan)
        ema_values[period - 1] = np.mean(data[:period])
        for i in range(period, len(data)):
            ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i - 1]
        return ema_values

    # Instance method wrappers for object-oriented usage
    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Instance wrapper for SMA."""
        return self.sma(data, period)

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Instance wrapper for EMA."""
        return self.ema(data, period)

    def vwap(self, rates: List[MarketRate]) -> np.ndarray:
        """Volume Weighted Average Price."""
        data = self._to_numpy(rates)
        typical = (data["high"] + data["low"] + data["close"]) / 3
        vwap = np.cumsum(typical * data["volume"]) / np.cumsum(data["volume"])
        return vwap

    # ──────────────────────────────────────────────────────────────────────────────
    # MACD
    # ──────────────────────────────────────────────────────────────────────────────

    def macd(
        self,
        closes: np.ndarray,
        fast: Optional[int] = None,
        slow: Optional[int] = None,
        signal: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD: returns (macd_line, signal_line, histogram)."""
        fast = fast or self.config.macd_fast
        slow = slow or self.config.macd_slow
        signal = signal or self.config.macd_signal

        ema_fast = self.ema(closes, fast)
        ema_slow = self.ema(closes, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    # ──────────────────────────────────────────────────────────────────────────────
    # RSI
    # ──────────────────────────────────────────────────────────────────────────────

    @staticmethod
    def rsi(closes: np.ndarray, period: Optional[int] = 14) -> np.ndarray:
        """Relative Strength Index (static version for backward compatibility)."""
        if len(closes) < period + 1:
            return np.full_like(closes, np.nan)

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.full_like(closes, np.nan)
        avg_loss = np.full_like(closes, np.nan)

        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])

        for i in range(period + 1, len(closes)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period

        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _rsi(self, closes: np.ndarray, period: Optional[int] = None) -> np.ndarray:
        """Instance wrapper for RSI."""
        period = period or self.config.rsi_period
        return self.rsi(closes, period)

    # ──────────────────────────────────────────────────────────────────────────────
    # Bollinger Bands
    # ──────────────────────────────────────────────────────────────────────────────

    def bollinger_bands(
        self,
        closes: np.ndarray,
        period: Optional[int] = None,
        std_dev: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands: returns (upper, middle, lower)."""
        period = period or self.config.bb_period
        std_dev = std_dev or self.config.bb_std

        if len(closes) < period:
            nan = np.full_like(closes, np.nan)
            return nan, nan, nan

        sma_vals = self.sma(closes, period)
        std_vals = np.full_like(closes, np.nan)

        for i in range(period - 1, len(closes)):
            std_vals[i] = np.std(closes[i - period + 1 : i + 1])

        upper = sma_vals + std_dev * std_vals
        lower = sma_vals - std_dev * std_vals

        return upper, sma_vals, lower

    # ──────────────────────────────────────────────────────────────────────────────
    # ATR (Average True Range)
    # ──────────────────────────────────────────────────────────────────────────────

    def atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: Optional[int] = None,
    ) -> np.ndarray:
        """Average True Range."""
        period = period or self.config.atr_period
        if len(highs) < period + 1:
            return np.full_like(highs, np.nan)

        tr = np.zeros_like(highs)
        tr[0] = highs[0] - lows[0]

        for i in range(1, len(highs)):
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )

        atr_vals = np.full_like(highs, np.nan)
        atr_vals[period] = np.mean(tr[:period + 1])

        for i in range(period + 1, len(highs)):
            atr_vals[i] = (atr_vals[i - 1] * (period - 1) + tr[i]) / period

        return atr_vals

    # ──────────────────────────────────────────────────────────────────────────────
    # Stochastic
    # ──────────────────────────────────────────────────────────────────────────────

    def stochastic(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        k_period: Optional[int] = None,
        d_period: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Stochastic Oscillator: returns (%K, %D)."""
        k_period = k_period or self.config.stoch_k
        d_period = d_period or self.config.stoch_d

        if len(closes) < k_period:
            nan = np.full_like(closes, np.nan)
            return nan, nan

        k_vals = np.full_like(closes, np.nan)

        for i in range(k_period - 1, len(closes)):
            highest = np.max(highs[i - k_period + 1 : i + 1])
            lowest = np.min(lows[i - k_period + 1 : i + 1])
            if highest != lowest:
                k_vals[i] = 100 * (closes[i] - lowest) / (highest - lowest)

        d_vals = np.full_like(closes, np.nan)
        for i in range(k_period - 1 + d_period - 1, len(closes)):
            d_vals[i] = np.mean(k_vals[i - d_period + 1 : i + 1])

        return k_vals, d_vals

    # ──────────────────────────────────────────────────────────────────────────────
    # ADX (Average Directional Index)
    # ──────────────────────────────────────────────────────────────────────────────

    def adx(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: Optional[int] = None,
    ) -> np.ndarray:
        """Average Directional Index."""
        period = period or self.config.adx_period
        if len(highs) < period + 1:
            return np.full_like(highs, np.nan)

        plus_dm = np.zeros_like(highs)
        minus_dm = np.zeros_like(highs)

        for i in range(1, len(highs)):
            up = highs[i] - highs[i - 1]
            down = lows[i - 1] - lows[i]
            if up > down and up > 0:
                plus_dm[i] = up
            elif down > up and down > 0:
                minus_dm[i] = down

        tr = np.zeros_like(highs)
        tr[0] = highs[0] - lows[0]
        for i in range(1, len(highs)):
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )

        atr_vals = self.atr(highs, lows, closes, period)

        plus_di = 100 * plus_dm / np.where(atr_vals == 0, 1e-10, atr_vals)
        minus_di = 100 * minus_dm / np.where(atr_vals == 0, 1e-10, atr_vals)

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        dx = np.where((plus_di + minus_di) == 0, 0, dx)

        adx_vals = np.full_like(highs, np.nan)
        adx_vals[period] = np.mean(dx[:period + 1])
        for i in range(period + 1, len(highs)):
            adx_vals[i] = (adx_vals[i - 1] * (period - 1) + dx[i]) / period

        return adx_vals

    # ──────────────────────────────────────────────────────────────────────────────
    # Ichimoku Cloud
    # ──────────────────────────────────────────────────────────────────────────────

    def ichimoku(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        tenkan: Optional[int] = None,
        kijun: Optional[int] = None,
        senkou_b: Optional[int] = None,
    ) -> Dict[str, np.ndarray]:
        """Ichimoku Cloud components."""
        tenkan = tenkan or self.config.ichimoku_tenkan
        kijun = kijun or self.config.ichimoku_kijun
        senkou_b = senkou_b or self.config.ichimoku_senkou_b

        # Tenkan-sen (Conversion Line)
        tenkan_sen = np.full_like(highs, np.nan)
        for i in range(tenkan - 1, len(highs)):
            tenkan_sen[i] = (np.max(highs[i - tenkan + 1 : i + 1]) + np.min(lows[i - tenkan + 1 : i + 1])) / 2

        # Kijun-sen (Base Line)
        kijun_sen = np.full_like(highs, np.nan)
        for i in range(kijun - 1, len(highs)):
            kijun_sen[i] = (np.max(highs[i - kijun + 1 : i + 1]) + np.min(lows[i - kijun + 1 : i + 1])) / 2

        # Senkou Span A (Leading Span A)
        senkou_a = np.full_like(highs, np.nan)
        for i in range(kijun - 1, len(highs)):
            if not np.isnan(tenkan_sen[i]) and not np.isnan(kijun_sen[i]):
                senkou_a[i] = (tenkan_sen[i] + kijun_sen[i]) / 2

        # Senkou Span B (Leading Span B)
        senkou_b_vals = np.full_like(highs, np.nan)
        for i in range(senkou_b - 1, len(highs)):
            senkou_b_vals[i] = (np.max(highs[i - senkou_b + 1 : i + 1]) + np.min(lows[i - senkou_b + 1 : i + 1])) / 2

        # Chikou Span (Lagging Span)
        chikou = np.full_like(closes, np.nan)
        chikou[:-kijun] = closes[kijun:]

        return {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_a": senkou_a,
            "senkou_b": senkou_b_vals,
            "chikou": chikou,
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # Volume Indicators
    # ──────────────────────────────────────────────────────────────────────────────

    def obv(self, closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """On-Balance Volume."""
        obv = np.zeros_like(closes)
        obv[0] = volumes[0]
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv[i] = obv[i - 1] + volumes[i]
            elif closes[i] < closes[i - 1]:
                obv[i] = obv[i - 1] - volumes[i]
            else:
                obv[i] = obv[i - 1]
        return obv

    def vwap_intraday(self, rates: List[MarketRate]) -> np.ndarray:
        """Session VWAP."""
        return self.vwap(rates)

    # ──────────────────────────────────────────────────────────────────────────────
    # Support/Resistance
    # ──────────────────────────────────────────────────────────────────────────────

    def pivot_points(
        self, high: float, low: float, close: float
    ) -> Dict[str, float]:
        """Classic pivot points."""
        pp = (high + low + close) / 3
        return {
            "pp": pp,
            "r1": 2 * pp - low,
            "s1": 2 * pp - high,
            "r2": pp + (high - low),
            "s2": pp - (high - low),
            "r3": high + 2 * (pp - low),
            "s3": low - 2 * (high - pp),
        }

    def fibonacci_levels(self, high: float, low: float) -> Dict[str, float]:
        """Fibonacci retracement levels."""
        diff = high - low
        return {
            "0.0": high,
            "0.236": high - 0.236 * diff,
            "0.382": high - 0.382 * diff,
            "0.5": high - 0.5 * diff,
            "0.618": high - 0.618 * diff,
            "0.786": high - 0.786 * diff,
            "1.0": low,
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # Full Calculation
    # ──────────────────────────────────────────────────────────────────────────────

    def calculate_all(self, rates: List[MarketRate]) -> IndicatorSet:
        """Calculate all indicators for a series of rates."""
        if not rates:
            return IndicatorSet(symbol="", timeframe=Timeframe.M1, timestamp=datetime.utcnow())

        data = self._to_numpy(rates)
        closes = data["close"]
        highs = data["high"]
        lows = data["low"]
        opens = data["open"]
        volumes = data["volume"]

        symbol = rates[0].symbol if hasattr(rates[0], "symbol") else "UNKNOWN"
        timeframe = rates[0].timeframe if hasattr(rates[0], "timeframe") else Timeframe.M1
        timestamp = rates[-1].timestamp

        indicators = {}

        # SMAs
        for period in self.config.sma_periods:
            sma_vals = self.sma(closes, period)
            if not np.isnan(sma_vals[-1]):
                indicators[f"SMA_{period}"] = IndicatorResult(
                    name=f"SMA_{period}",
                    value=float(sma_vals[-1]),
                    timestamp=timestamp,
                    metadata={"period": period, "series": sma_vals.tolist()[-10:]},
                )

        # EMAs
        for period in self.config.ema_periods:
            ema_vals = self.ema(closes, period)
            if not np.isnan(ema_vals[-1]):
                indicators[f"EMA_{period}"] = IndicatorResult(
                    name=f"EMA_{period}",
                    value=float(ema_vals[-1]),
                    timestamp=timestamp,
                    metadata={"period": period, "series": ema_vals.tolist()[-10:]},
                )

        # MACD
        macd_line, signal_line, histogram = self.macd(closes)
        if not np.isnan(macd_line[-1]):
            indicators["MACD"] = IndicatorResult(
                name="MACD",
                value={"macd": float(macd_line[-1]), "signal": float(signal_line[-1]),
                       "histogram": float(histogram[-1])},
                timestamp=timestamp,
            )

        # RSI
        rsi_vals = self.rsi(closes)
        if not np.isnan(rsi_vals[-1]):
            indicators["RSI"] = IndicatorResult(
                name="RSI",
                value=float(rsi_vals[-1]),
                timestamp=timestamp,
                metadata={
                    "period": self.config.rsi_period,
                    "overbought": self.config.rsi_overbought,
                    "oversold": self.config.rsi_oversold,
                    "series": rsi_vals.tolist()[-10:],
                },
            )

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.bollinger_bands(closes)
        if not np.isnan(bb_middle[-1]):
            indicators["BOLLINGER"] = IndicatorResult(
                name="BOLLINGER",
                value={
                    "upper": float(bb_upper[-1]),
                    "middle": float(bb_middle[-1]),
                    "lower": float(bb_lower[-1]),
                },
                timestamp=timestamp,
                metadata={"period": self.config.bb_period, "std": self.config.bb_std},
            )

        # ATR
        atr_vals = self.atr(highs, lows, closes)
        if not np.isnan(atr_vals[-1]):
            indicators["ATR"] = IndicatorResult(
                name="ATR",
                value=float(atr_vals[-1]),
                timestamp=timestamp,
                metadata={"period": self.config.atr_period},
            )

        # Stochastic
        stoch_k, stoch_d = self.stochastic(highs, lows, closes)
        if not np.isnan(stoch_k[-1]):
            indicators["STOCHASTIC"] = IndicatorResult(
                name="STOCHASTIC",
                value={"k": float(stoch_k[-1]), "d": float(stoch_d[-1])},
                timestamp=timestamp,
            )

        # ADX
        adx_vals = self.adx(highs, lows, closes)
        if not np.isnan(adx_vals[-1]):
            indicators["ADX"] = IndicatorResult(
                name="ADX",
                value=float(adx_vals[-1]),
                timestamp=timestamp,
                metadata={"period": self.config.adx_period},
            )

        # Ichimoku
        ichimoku = self.ichimoku(highs, lows, closes)
        if not np.isnan(ichimoku["tenkan_sen"][-1]):
            indicators["ICHIMOKU"] = IndicatorResult(
                name="ICHIMOKU",
                value={k: float(v[-1]) if not np.isnan(v[-1]) else None
                       for k, v in ichimoku.items()},
                timestamp=timestamp,
            )

        # Volume
        obv_vals = self.obv(closes, volumes)
        indicators["OBV"] = IndicatorResult(
            name="OBV",
            value=float(obv_vals[-1]),
            timestamp=timestamp,
        )

        # VWAP
        vwap_vals = self.vwap(rates)
        if not np.isnan(vwap_vals[-1]):
            indicators["VWAP"] = IndicatorResult(
                name="VWAP",
                value=float(vwap_vals[-1]),
                timestamp=timestamp,
            )

        # Pivot Points (using last completed candle)
        if len(rates) >= 2:
            prev = rates[-2]
            pivots = self.pivot_points(float(prev.high), float(prev.low), float(prev.close))
            indicators["PIVOTS"] = IndicatorResult(
                name="PIVOTS",
                value=pivots,
                timestamp=timestamp,
            )

        return IndicatorSet(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            indicators=indicators,
        )