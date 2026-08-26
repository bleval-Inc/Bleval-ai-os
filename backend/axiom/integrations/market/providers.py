"""Market Data Providers — Crypto, Forex, Stocks with unified interface."""

import asyncio
import hashlib
import hmac
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, TYPE_CHECKING
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel, Field, SecretStr

from axiom.data.models import Symbol, SymbolType, Timeframe, MarketTick, MarketRate
from axiom.runtime.logging import RuntimeLogger

if TYPE_CHECKING:
    from axiom.integrations.layer import IntegrationLayer


class MarketProviderConfig(BaseModel):
    """Configuration for a market data provider."""

    name: str
    enabled: bool = True
    api_key: Optional[SecretStr] = None
    api_secret: Optional[SecretStr] = None
    api_passphrase: Optional[SecretStr] = None
    base_url: str
    ws_url: Optional[str] = None
    rate_limit_rpm: int = 120
    timeout_seconds: int = 10
    symbols: List[str] = Field(default_factory=list)
    default_timeframe: Timeframe = Timeframe.M1
    custom_params: Dict[str, Any] = Field(default_factory=dict)
    testnet: bool = False


class SymbolInfo(BaseModel):
    """Normalized symbol information."""

    symbol: str
    base: str
    quote: str
    symbol_type: SymbolType
    exchange: str
    min_qty: Optional[Decimal] = None
    max_qty: Optional[Decimal] = None
    step_size: Optional[Decimal] = None
    price_precision: int = 8
    qty_precision: int = 8
    is_active: bool = True
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class TickData(BaseModel):
    """Normalized tick data."""

    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    last: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    exchange: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class RateData(BaseModel):
    """Normalized OHLCV rate data."""

    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_complete: bool = False
    exchange: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class MarketProvider(ABC):
    """Abstract base for market data providers."""

    def __init__(self, config: MarketProviderConfig, logger: Optional[RuntimeLogger] = None):
        self.config = config
        self.logger = logger or RuntimeLogger()
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws_connection: Optional[aiohttp.ClientWebSocketResponse] = None
        self._symbol_cache: Dict[str, SymbolInfo] = {}
        self._last_request = 0.0
        self._rate_limit_delay = 60.0 / config.rate_limit_rpm

    @property
    @abstractmethod
    def exchange_name(self) -> str:
        """Exchange identifier."""
        pass

    @property
    @abstractmethod
    def supported_types(self) -> List[SymbolType]:
        """Supported symbol types."""
        pass

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
        if self._ws_connection and not self._ws_connection.closed:
            await self._ws_connection.close()

    async def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self._last_request
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request = time.time()

    def _normalize_symbol(self, symbol: str) -> Tuple[str, str, SymbolType]:
        """Normalize symbol to (symbol, base, quote, type)."""
        # Override in subclasses
        return symbol, symbol, SymbolType.CRYPTO

    async def fetch_symbols(self) -> List[SymbolInfo]:
        """Fetch all available symbols."""
        await self._rate_limit()
        session = await self._get_session()

        try:
            url = f"{self.config.base_url}/v3/exchangeInfo"  # Binance-style default
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

            symbols = []
            for item in data.get("symbols", data):
                sym_info = self._parse_symbol(item)
                if sym_info:
                    symbols.append(sym_info)
                    self._symbol_cache[sym_info.symbol] = sym_info

            return symbols
        except Exception as e:
            self.logger.error(f"Fetch symbols error: {e}")
            return []

    @abstractmethod
    def _parse_symbol(self, raw: Dict[str, Any]) -> Optional[SymbolInfo]:
        """Parse raw symbol data."""
        pass

    async def fetch_ticker(self, symbol: str) -> Optional[TickData]:
        """Fetch latest ticker for symbol."""
        await self._rate_limit()
        session = await self._get_session()

        try:
            url = f"{self.config.base_url}/v3/ticker/24hr"
            params = {"symbol": symbol}
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

            return self._parse_ticker(symbol, data)
        except Exception as e:
            self.logger.error(f"Fetch ticker error for {symbol}: {e}")
            return None

    @abstractmethod
    def _parse_ticker(self, symbol: str, raw: Dict[str, Any]) -> Optional[TickData]:
        """Parse raw ticker data."""
        pass

    async def fetch_klines(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 500,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[RateData]:
        """Fetch OHLCV klines/candles."""
        await self._rate_limit()
        session = await self._get_session()

        try:
            url = f"{self.config.base_url}/v3/klines"
            params = {
                "symbol": symbol,
                "interval": self._timeframe_to_interval(timeframe),
                "limit": min(limit, 1000),
            }
            if start_time:
                params["startTime"] = int(start_time.timestamp() * 1000)
            if end_time:
                params["endTime"] = int(end_time.timestamp() * 1000)

            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

            return [self._parse_kline(symbol, timeframe, item) for item in data]
        except Exception as e:
            self.logger.error(f"Fetch klines error for {symbol}: {e}")
            return []

    @abstractmethod
    def _timeframe_to_interval(self, timeframe: Timeframe) -> str:
        """Convert Timeframe to provider interval string."""
        pass

    @abstractmethod
    def _parse_kline(
        self, symbol: str, timeframe: Timeframe, raw: List[Any]
    ) -> RateData:
        """Parse raw kline data."""
        pass

    # WebSocket methods for real-time data
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket for real-time data."""
        if not self.config.ws_url:
            return False

        try:
            session = await self._get_session()
            self._ws_connection = await session.ws_connect(self.config.ws_url)
            return True
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            return False

    @abstractmethod
    async def subscribe_ticker(self, symbols: List[str]) -> bool:
        """Subscribe to ticker updates."""
        pass

    @abstractmethod
    async def subscribe_klines(self, symbols: List[str], timeframe: Timeframe) -> bool:
        """Subscribe to kline updates."""
        pass

    async def listen(self) -> AsyncIterator[TickData]:
        """Listen for real-time updates."""
        if not self._ws_connection:
            return

        async for msg in self._ws_connection:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                parsed = self._parse_ws_message(data)
                if parsed:
                    yield parsed
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.logger.error(f"WebSocket error: {self._ws_connection.exception()}")
                break

    @abstractmethod
    def _parse_ws_message(self, raw: Dict[str, Any]) -> Optional[TickData]:
        """Parse WebSocket message."""
        pass


class CryptoProvider(MarketProvider):
    """Cryptocurrency provider (Binance-compatible)."""

    @property
    def exchange_name(self) -> str:
        return "binance" if not self.config.testnet else "binance_testnet"

    @property
    def supported_types(self) -> List[SymbolType]:
        return [SymbolType.CRYPTO, SymbolType.FUTURES]

    def _parse_symbol(self, raw: Dict[str, Any]) -> Optional[SymbolInfo]:
        if raw.get("status") != "TRADING":
            return None

        base = raw.get("baseAsset", "")
        quote = raw.get("quoteAsset", "")
        symbol = f"{base}{quote}"

        return SymbolInfo(
            symbol=symbol,
            base=base,
            quote=quote,
            symbol_type=SymbolType.CRYPTO,
            exchange=self.exchange_name,
            min_qty=Decimal(raw.get("filters", [{}])[0].get("minQty", "0")),
            max_qty=Decimal(raw.get("filters", [{}])[0].get("maxQty", "0")),
            step_size=Decimal(raw.get("filters", [{}])[1].get("stepSize", "0")),
            price_precision=int(raw.get("pricePrecision", 8)),
            qty_precision=int(raw.get("quantityPrecision", 8)),
            raw_data=raw,
        )

    def _parse_ticker(self, symbol: str, raw: Dict[str, Any]) -> Optional[TickData]:
        try:
            return TickData(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bid=Decimal(raw.get("bidPrice", "0")),
                ask=Decimal(raw.get("askPrice", "0")),
                last=Decimal(raw.get("lastPrice", "0")),
                volume=Decimal(raw.get("volume", "0")),
                exchange=self.exchange_name,
                raw_data=raw,
            )
        except Exception:
            return None

    def _timeframe_to_interval(self, timeframe: Timeframe) -> str:
        mapping = {
            Timeframe.M1: "1m",
            Timeframe.M5: "5m",
            Timeframe.M15: "15m",
            Timeframe.M30: "30m",
            Timeframe.H1: "1h",
            Timeframe.H4: "4h",
            Timeframe.D1: "1d",
            Timeframe.W1: "1w",
        }
        return mapping.get(timeframe, "1m")

    def _parse_kline(
        self, symbol: str, timeframe: Timeframe, raw: List[Any]
    ) -> RateData:
        return RateData(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.fromtimestamp(raw[0] / 1000),
            open=Decimal(str(raw[1])),
            high=Decimal(str(raw[2])),
            low=Decimal(str(raw[3])),
            close=Decimal(str(raw[4])),
            volume=Decimal(str(raw[5])),
            is_complete=bool(raw[6]),
            exchange=self.exchange_name,
            raw_data={"raw": raw},
        )

    async def subscribe_ticker(self, symbols: List[str]) -> bool:
        if not self._ws_connection:
            return False
        streams = [f"{s.lower()}@ticker" for s in symbols]
        msg = {"method": "SUBSCRIBE", "params": streams, "id": 1}
        await self._ws_connection.send_json(msg)
        return True

    async def subscribe_klines(self, symbols: List[str], timeframe: Timeframe) -> bool:
        if not self._ws_connection:
            return False
        interval = self._timeframe_to_interval(timeframe)
        streams = [f"{s.lower()}@kline_{interval}" for s in symbols]
        msg = {"method": "SUBSCRIBE", "params": streams, "id": 2}
        await self._ws_connection.send_json(msg)
        return True

    def _parse_ws_message(self, raw: Dict[str, Any]) -> Optional[TickData]:
        if "e" not in raw:
            return None

        if raw["e"] == "24hrTicker":
            return TickData(
                symbol=raw["s"],
                timestamp=datetime.fromtimestamp(raw["E"] / 1000),
                bid=Decimal(raw["b"]),
                ask=Decimal(raw["a"]),
                last=Decimal(raw["c"]),
                volume=Decimal(raw["v"]),
                exchange=self.exchange_name,
                raw_data=raw,
            )
        return None


class ForexProvider(MarketProvider):
    """Forex provider (Alpha Vantage / OANDA compatible)."""

    @property
    def exchange_name(self) -> str:
        return "alphavantage"  # or oanda

    @property
    def supported_types(self) -> List[SymbolType]:
        return [SymbolType.FOREX]

    def _parse_symbol(self, raw: Dict[str, Any]) -> Optional[SymbolInfo]:
        # Alpha Vantage doesn't have symbol list endpoint
        # Parse from custom config
        return None

    def _parse_ticker(self, symbol: str, raw: Dict[str, Any]) -> Optional[TickData]:
        # Alpha Vantage format
        try:
            quote = raw.get("Realtime Currency Exchange Rate", {})
            return TickData(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bid=Decimal(quote.get("8. Bid Price", "0")),
                ask=Decimal(quote.get("9. Ask Price", "0")),
                last=Decimal(quote.get("5. Exchange Rate", "0")),
                exchange=self.exchange_name,
                raw_data=raw,
            )
        except Exception:
            return None

    def _timeframe_to_interval(self, timeframe: Timeframe) -> str:
        mapping = {
            Timeframe.M1: "1min",
            Timeframe.M5: "5min",
            Timeframe.M15: "15min",
            Timeframe.M30: "30min",
            Timeframe.H1: "60min",
            Timeframe.D1: "daily",
            Timeframe.W1: "weekly",
        }
        return mapping.get(timeframe, "60min")

    def _parse_kline(
        self, symbol: str, timeframe: Timeframe, raw: List[Any]
    ) -> RateData:
        # Alpha Vantage returns dict with timestamp keys
        pass

    async def subscribe_ticker(self, symbols: List[str]) -> bool:
        # Forex typically uses REST polling
        return False

    async def subscribe_klines(self, symbols: List[str], timeframe: Timeframe) -> bool:
        return False

    def _parse_ws_message(self, raw: Dict[str, Any]) -> Optional[TickData]:
        return None


class StockProvider(MarketProvider):
    """Stock provider (Alpha Vantage / IEX / Polygon)."""

    @property
    def exchange_name(self) -> str:
        return "alphavantage"

    @property
    def supported_types(self) -> List[SymbolType]:
        return [SymbolType.STOCK, SymbolType.ETF]

    def _parse_symbol(self, raw: Dict[str, Any]) -> Optional[SymbolInfo]:
        return SymbolInfo(
            symbol=raw.get("symbol", ""),
            base=raw.get("symbol", ""),
            quote="USD",
            symbol_type=SymbolType.STOCK,
            exchange=self.exchange_name,
            raw_data=raw,
        )

    def _parse_ticker(self, symbol: str, raw: Dict[str, Any]) -> Optional[TickData]:
        try:
            quote = raw.get("Global Quote", {})
            return TickData(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                last=Decimal(quote.get("05. price", "0")),
                volume=Decimal(quote.get("06. volume", "0")),
                exchange=self.exchange_name,
                raw_data=raw,
            )
        except Exception:
            return None

    def _timeframe_to_interval(self, timeframe: Timeframe) -> str:
        mapping = {
            Timeframe.M1: "1min",
            Timeframe.M5: "5min",
            Timeframe.M15: "15min",
            Timeframe.M30: "30min",
            Timeframe.H1: "60min",
            Timeframe.D1: "daily",
            Timeframe.W1: "weekly",
        }
        return mapping.get(timeframe, "60min")

    def _parse_kline(
        self, symbol: str, timeframe: Timeframe, raw: List[Any]
    ) -> RateData:
        pass

    async def subscribe_ticker(self, symbols: List[str]) -> bool:
        return False

    async def subscribe_klines(self, symbols: List[str], timeframe: Timeframe) -> bool:
        return False

    def _parse_ws_message(self, raw: Dict[str, Any]) -> Optional[TickData]:
        return None


class MultiProviderAggregator:
    """Aggregates data from multiple providers with fallback."""

    def __init__(
        self,
        integration_layer: "IntegrationLayer",
        providers: List[MarketProvider],
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.providers = providers
        self.logger = logger or RuntimeLogger()
        self._primary = providers[0] if providers else None

    def get_provider_for_symbol(self, symbol: str, symbol_type: SymbolType) -> Optional[MarketProvider]:
        """Get best provider for symbol."""
        for provider in self.providers:
            if symbol_type in provider.supported_types:
                if not provider.config.symbols or symbol in provider.config.symbols:
                    return provider
        return self._primary

    async def fetch_ticker(self, symbol: str, symbol_type: SymbolType) -> Optional[TickData]:
        """Fetch ticker with fallback."""
        provider = self.get_provider_for_symbol(symbol, symbol_type)
        if not provider:
            return None

        result = await provider.fetch_ticker(symbol)
        if result:
            return result

        # Try fallback providers
        for p in self.providers:
            if p != provider and symbol_type in p.supported_types:
                result = await p.fetch_ticker(symbol)
                if result:
                    self.logger.info(f"Fallback to {p.exchange_name} for {symbol}")
                    return result

        return None

    async def fetch_klines(
        self,
        symbol: str,
        symbol_type: SymbolType,
        timeframe: Timeframe,
        limit: int = 500,
    ) -> List[RateData]:
        """Fetch klines with fallback."""
        provider = self.get_provider_for_symbol(symbol, symbol_type)
        if not provider:
            return []

        result = await provider.fetch_klines(symbol, timeframe, limit)
        if result:
            return result

        # Fallback
        for p in self.providers:
            if p != provider and symbol_type in p.supported_types:
                result = await p.fetch_klines(symbol, timeframe, limit)
                if result:
                    return result

        return []

    async def fetch_all_symbols(self) -> Dict[str, List[SymbolInfo]]:
        """Fetch symbols from all providers."""
        results = {}
        for provider in self.providers:
            try:
                symbols = await provider.fetch_symbols()
                if symbols:
                    results[provider.exchange_name] = symbols
            except Exception as e:
                self.logger.error(f"Fetch symbols failed for {provider.exchange_name}: {e}")
        return results

    async def close_all(self):
        """Close all provider connections."""
        for provider in self.providers:
            await provider.close()