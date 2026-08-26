"""Market Intelligence Layer — Real-time data providers, indicators, signals."""

# Import signals FIRST so SignalConfig is defined before IntelligenceConfig references it
from .signals import (
    SignalGenerator,
    SignalConfig,
    SignalRule,
    SignalDirection,
    SignalStrength,
    SignalResult,
    SignalContext,
    MACrossoverRule,
    RSIReversalRule,
    MACDSignalRule,
    BollingerBreakoutRule,
    TrendFollowRule,
    IchimokuRule,
    DEFAULT_RULES,
)

# Then indicators (no forward refs to signals)
from .indicators import TechnicalIndicators, IndicatorConfig, IndicatorSet, IndicatorResult

# Then providers
from .providers import (
    MarketProvider,
    MarketProviderConfig,
    CryptoProvider,
    ForexProvider,
    StockProvider,
    MultiProviderAggregator,
    SymbolInfo,
    TickData,
    RateData,
)

# Then intelligence (references SignalConfig via forward ref)
from .intelligence import MarketIntelligenceEngine, IntelligenceConfig, MarketSnapshot

# Then pipeline
from .pipeline import MarketPipeline

# Rebuild Pydantic models to resolve forward references (Pydantic V2)
try:
    from .signals import SignalConfig as _SignalConfig, SignalResult as _SignalResult
    from .intelligence import IntelligenceConfig as _IntelligenceConfig, MarketSnapshot as _MarketSnapshot
    _SignalConfig.model_rebuild()
    _SignalResult.model_rebuild()
    _IntelligenceConfig.model_rebuild()
    _MarketSnapshot.model_rebuild()
except Exception:
    pass

__all__ = [
    # Providers
    "MarketProvider",
    "MarketProviderConfig",
    "CryptoProvider",
    "ForexProvider",
    "StockProvider",
    "MultiProviderAggregator",
    "SymbolInfo",
    "TickData",
    "RateData",
    # Indicators
    "TechnicalIndicators",
    "IndicatorConfig",
    "IndicatorSet",
    "IndicatorResult",
    # Signals
    "SignalGenerator",
    "SignalConfig",
    "SignalRule",
    "SignalDirection",
    "SignalStrength",
    "SignalResult",
    "SignalContext",
    "MACrossoverRule",
    "RSIReversalRule",
    "MACDSignalRule",
    "BollingerBreakoutRule",
    "TrendFollowRule",
    "IchimokuRule",
    "DEFAULT_RULES",
    # Intelligence
    "MarketIntelligenceEngine",
    "IntelligenceConfig",
    "MarketSnapshot",
    # Pipeline
    "MarketPipeline",
]