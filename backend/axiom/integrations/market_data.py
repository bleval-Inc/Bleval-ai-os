"""Market Data Provider — Polygon.io, Alpha Vantage, Twelve Data for quotes and OHLCV."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from axiom.engine.provider import ExternalAPIProvider
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationResult,
)
from axiom.runtime.logging import RuntimeLogger


class MarketDataProvider(ExternalAPIProvider):
    """Market data provider supporting multiple backends.

    DATA ONLY — No trade execution.

    Supported backends:
    - Polygon.io (stocks, forex, crypto, options)
    - Alpha Vantage (stocks, forex, crypto, technical indicators)
    - Twelve Data (stocks, forex, crypto, indices)
    - Yahoo Finance (free, limited)

    Capabilities:
    - Real-time quotes
    - Historical OHLCV (multiple timeframes)
    - Options chains
    - Dividends/splits
    - Company fundamentals
    - Economic calendar
    - News sentiment
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._backend = config.config.get("backend", "polygon")  # polygon, alphavantage, twelvedata, yahoo
        self._api_key = None
        self._base_urls = {
            "polygon": "https://api.polygon.io",
            "alphavantage": "https://www.alphavantage.co/query",
            "twelvedata": "https://api.twelvedata.com",
        }

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            ProviderToolDefinition(
                tool_id="marketdata_get_quote",
                name="Get Real-time Quote",
                description="Get real-time quote for a symbol",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Symbol (e.g., 'AAPL', 'EURUSD', 'BTC-USD')"},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="marketdata_get_ohlcv",
                name="Get OHLCV Data",
                description="Get historical price candles",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "timeframe": {"type": "string", "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"], "default": "1h"},
                        "from_date": {"type": "string", "description": "ISO datetime"},
                        "to_date": {"type": "string", "description": "ISO datetime"},
                        "limit": {"type": "integer", "default": 100},
                        "adjusted": {"type": "boolean", "default": True},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="marketdata_get_options_chain",
                name="Get Options Chain",
                description="Get options chain for a symbol",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "expiration": {"type": "string", "description": "ISO date"},
                        "include_greeks": {"type": "boolean", "default": True},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="marketdata_get_fundamentals",
                name="Get Company Fundamentals",
                description="Get fundamental data for a stock",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "include_financials": {"type": "boolean", "default": True},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="marketdata_get_dividends_splits",
                name="Get Dividends and Splits",
                description="Get dividend and split history",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "from_date": {"type": "string"},
                        "to_date": {"type": "string"},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="marketdata_search_symbols",
                name="Search Symbols",
                description="Search for symbols by name or ticker",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "asset_type": {"type": "string", "enum": ["stocks", "forex", "crypto", "options", "indices", "all"], "default": "all"},
                        "limit": {"type": "integer", "default": 20},
                    },
                    "required": ["query"],
                },
            ),
            ProviderToolDefinition(
                tool_id="marketdata_get_news",
                name="Get Market News",
                description="Get news for symbol or general market",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                        "from_date": {"type": "string"},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="marketdata_get_economic_calendar",
                name="Get Economic Calendar",
                description="Get upcoming economic events",
                capability="economic_calendar",
                input_schema={
                    "type": "object",
                    "properties": {
                        "from_date": {"type": "string"},
                        "to_date": {"type": "string"},
                        "countries": {"type": "array", "items": {"type": "string"}},
                        "impact": {"type": "array", "items": {"type": "string", "enum": ["high", "medium", "low"]}},
                    },
                },
            ),
        ]

    async def initialize(self) -> None:
        """Initialize API key and session."""
        await super().initialize()

        key_env = {
            "polygon": "POLYGON_API_KEY",
            "alphavantage": "ALPHAVANTAGE_API_KEY",
            "twelvedata": "TWELVEDATA_API_KEY",
            "yahoo": None,
        }

        env_var = key_env.get(self._backend)
        if env_var:
            self._api_key = self._secrets.get_secret(env_var)
            if not self._api_key:
                raise RuntimeError(f"{self._backend.upper()} API key not configured (env: {env_var})")

        # Set base URL and headers per backend
        if self._backend == "polygon":
            self.base_url = "https://api.polygon.io"
            self._default_params = {"apikey": self._api_key}
        elif self._backend == "alphavantage":
            self.base_url = "https://www.alphavantage.co/query"
            self._default_params = {"apikey": self._api_key}
        elif self._backend == "twelvedata":
            self.base_url = "https://api.twelvedata.com"
            self._default_params = {"apikey": self._api_key}
        elif self._backend == "yahoo":
            self.base_url = "https://query1.finance.yahoo.com"
            self._default_params = {}
        else:
            raise ValueError(f"Unknown backend: {self._backend}")

        self._initialized = True

    async def _execute_tool_impl(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> ToolInvocationResult:
        method_name = f"_execute_{tool_id}"
        if hasattr(self, method_name):
            return await getattr(self, method_name)(parameters)

        return ToolInvocationResult(
            success=False,
            error=f"Tool {tool_id} not implemented",
            error_code="not_implemented",
            provider_id=self.provider_id,
            tool_id=tool_id,
        )

    # ── Tool Implementations ──────────────────────────────────────────────

    async def _execute_marketdata_get_quote(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]

        if self._backend == "polygon":
            # Polygon uses ticker format like "AAPL" or "C:EURUSD"
            result = await self._request(
                "GET",
                f"/v2/last/trade/{symbol}",
                params={"apikey": self._api_key},
            )
            if result.get("status") == "OK":
                return ToolInvocationResult(
                    success=True,
                    output={
                        "symbol": symbol,
                        "price": result.get("results", {}).get("p"),
                        "size": result.get("results", {}).get("s"),
                        "timestamp": result.get("results", {}).get("t"),
                    },
                    provider_id=self.provider_id,
                    tool_id="marketdata_get_quote",
                )

        elif self._backend == "alphavantage":
            result = await self._request(
                "GET",
                "",
                params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self._api_key},
            )
            if "Global Quote" in result:
                q = result["Global Quote"]
                return ToolInvocationResult(
                    success=True,
                    output={
                        "symbol": symbol,
                        "price": float(q.get("05. price", 0)),
                        "change": float(q.get("09. change", 0)),
                        "change_pct": q.get("10. change percent", "0%"),
                        "volume": int(q.get("06. volume", 0)),
                    },
                    provider_id=self.provider_id,
                    tool_id="marketdata_get_quote",
                )

        elif self._backend == "twelvedata":
            result = await self._request(
                "GET",
                "/price",
                params={"symbol": symbol, "apikey": self._api_key},
            )
            if "price" in result:
                return ToolInvocationResult(
                    success=True,
                    output={
                        "symbol": symbol,
                        "price": float(result["price"]),
                    },
                    provider_id=self.provider_id,
                    tool_id="marketdata_get_quote",
                )

        elif self._backend == "yahoo":
            result = await self._request(
                "GET",
                "/v7/finance/quote",
                params={"symbols": symbol},
            )
            if result.get("quoteResponse", {}).get("result"):
                q = result["quoteResponse"]["result"][0]
                return ToolInvocationResult(
                    success=True,
                    output={
                        "symbol": symbol,
                        "price": q.get("regularMarketPrice"),
                        "change": q.get("regularMarketChange"),
                        "change_pct": q.get("regularMarketChangePercent"),
                        "volume": q.get("regularMarketVolume"),
                    },
                    provider_id=self.provider_id,
                    tool_id="marketdata_get_quote",
                )

        return ToolInvocationResult(success=False, error="Failed to get quote", provider_id=self.provider_id, tool_id="marketdata_get_quote")

    async def _execute_marketdata_get_ohlcv(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]
        timeframe = params.get("timeframe", "1h")
        from_date = params.get("from_date")
        to_date = params.get("to_date")
        limit = params.get("limit", 100)
        adjusted = params.get("adjusted", True)

        if self._backend == "polygon":
            # Map timeframe to Polygon format
            tf_map = {
                "1m": "minute", "5m": "5 minute", "15m": "15 minute", "30m": "30 minute",
                "1h": "hour", "4h": "4 hour", "1d": "day", "1w": "week", "1M": "month",
            }
            multiplier, timespan = self._parse_polygon_timeframe(timeframe)

            query_params = {
                "apikey": self._api_key,
                "limit": min(limit, 50000),
                "adjusted": "true" if adjusted else "false",
                "sort": "asc",
            }
            if from_date:
                query_params["from"] = from_date[:10]
            if to_date:
                query_params["to"] = to_date[:10]

            result = await self._request(
                "GET",
                f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}",
                params=query_params,
            )

            if result.get("status") == "OK" and result.get("results"):
                output = []
                for bar in result["results"]:
                    output.append({
                        "timestamp": datetime.fromtimestamp(bar["t"] / 1000).isoformat(),
                        "open": bar["o"],
                        "high": bar["h"],
                        "low": bar["l"],
                        "close": bar["c"],
                        "volume": bar["v"],
                        "vwap": bar.get("vw"),
                        "transactions": bar.get("n"),
                    })
                return ToolInvocationResult(success=True, output=output, provider_id=self.provider_id, tool_id="marketdata_get_ohlcv")

        elif self._backend == "alphavantage":
            tf_map = {
                "1m": ("TIME_SERIES_INTRADAY", "1min"),
                "5m": ("TIME_SERIES_INTRADAY", "5min"),
                "15m": ("TIME_SERIES_INTRADAY", "15min"),
                "30m": ("TIME_SERIES_INTRADAY", "30min"),
                "1h": ("TIME_SERIES_INTRADAY", "60min"),
                "1d": ("TIME_SERIES_DAILY", None),
                "1w": ("TIME_SERIES_WEEKLY", None),
                "1M": ("TIME_SERIES_MONTHLY", None),
            }
            function, interval = tf_map.get(timeframe, ("TIME_SERIES_DAILY", None))

            query = {"function": function, "symbol": symbol, "apikey": self._api_key, "outputsize": "full"}
            if interval:
                query["interval"] = interval
            if adjusted:
                query["adjusted"] = "true"

            result = await self._request("GET", "", params=query)

            # Parse response based on function
            data_key = None
            for key in result.keys():
                if "Time Series" in key:
                    data_key = key
                    break

            if data_key:
                output = []
                for ts, values in list(result[data_key].items())[:limit]:
                    output.append({
                        "timestamp": ts,
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": int(values["5. volume"]),
                    })
                return ToolInvocationResult(success=True, output=output, provider_id=self.provider_id, tool_id="marketdata_get_ohlcv")

        elif self._backend == "twelvedata":
            tf_map = {
                "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
                "1h": "1h", "4h": "4h", "1d": "1day", "1w": "1week", "1M": "1month",
            }
            interval = tf_map.get(timeframe, "1h")

            query = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": min(limit, 5000),
                "apikey": self._api_key,
            }
            if from_date:
                query["start_date"] = from_date[:10]
            if to_date:
                query["end_date"] = to_date[:10]

            result = await self._request("GET", "/time_series", params=query)

            if "values" in result:
                output = []
                for bar in result["values"]:
                    output.append({
                        "timestamp": bar["datetime"],
                        "open": float(bar["open"]),
                        "high": float(bar["high"]),
                        "low": float(bar["low"]),
                        "close": float(bar["close"]),
                        "volume": int(bar["volume"]),
                    })
                return ToolInvocationResult(success=True, output=output, provider_id=self.provider_id, tool_id="marketdata_get_ohlcv")

        elif self._backend == "yahoo":
            # Yahoo uses different timeframe codes
            tf_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "1d": "1d", "1w": "1wk", "1M": "1mo"}
            interval = tf_map.get(timeframe, "1h")

            # Convert dates to timestamps
            period1 = int(datetime.fromisoformat(from_date.replace("Z", "+00:00")).timestamp()) if from_date else int((datetime.utcnow() - timedelta(days=365)).timestamp())
            period2 = int(datetime.fromisoformat(to_date.replace("Z", "+00:00")).timestamp()) if to_date else int(datetime.utcnow().timestamp())

            result = await self._request(
                "GET",
                f"/v8/finance/chart/{symbol}",
                params={"period1": period1, "period2": period2, "interval": interval},
            )

            if result.get("chart", {}).get("result"):
                chart = result["chart"]["result"][0]
                timestamps = chart.get("timestamp", [])
                quotes = chart.get("indicators", {}).get("quote", [{}])[0]
                output = []
                for i, ts in enumerate(timestamps[:limit]):
                    output.append({
                        "timestamp": datetime.fromtimestamp(ts).isoformat(),
                        "open": quotes.get("open", [])[i],
                        "high": quotes.get("high", [])[i],
                        "low": quotes.get("low", [])[i],
                        "close": quotes.get("close", [])[i],
                        "volume": quotes.get("volume", [])[i],
                    })
                return ToolInvocationResult(success=True, output=output, provider_id=self.provider_id, tool_id="marketdata_get_ohlcv")

        return ToolInvocationResult(success=False, error="Failed to get OHLCV", provider_id=self.provider_id, tool_id="marketdata_get_ohlcv")

    def _parse_polygon_timeframe(self, tf: str) -> tuple:
        """Parse timeframe to Polygon multiplier/timespan."""
        mapping = {
            "1m": (1, "minute"), "5m": (5, "minute"), "15m": (15, "minute"), "30m": (30, "minute"),
            "1h": (1, "hour"), "4h": (4, "hour"),
            "1d": (1, "day"), "1w": (1, "week"), "1M": (1, "month"),
        }
        return mapping.get(tf, (1, "hour"))

    async def _execute_marketdata_get_options_chain(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]
        expiration = params.get("expiration")
        include_greeks = params.get("include_greeks", True)

        if self._backend == "polygon":
            query = {"apikey": self._api_key, "limit": 1000}
            if expiration:
                query["expiration_date"] = expiration[:10] if "T" not in expiration else expiration.split("T")[0]

            result = await self._request("GET", f"/v3/reference/options/contracts", params={**query, "underlying_ticker": symbol})

            if result.get("status") == "OK" and result.get("results"):
                return ToolInvocationResult(success=True, output=result["results"], provider_id=self.provider_id, tool_id="marketdata_get_options_chain")

        # Not implemented for other backends yet
        return ToolInvocationResult(success=False, error=f"Options chain not implemented for {self._backend}", provider_id=self.provider_id, tool_id="marketdata_get_options_chain")

    async def _execute_marketdata_get_fundamentals(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]
        include_financials = params.get("include_financials", True)

        if self._backend == "polygon":
            result = await self._request("GET", f"/vX/reference/tickers/{symbol}", params={"apikey": self._api_key})
            if result.get("status") == "OK":
                return ToolInvocationResult(success=True, output=result.get("results", {}), provider_id=self.provider_id, tool_id="marketdata_get_fundamentals")

        elif self._backend == "alphavantage":
            result = await self._request("GET", "", params={"function": "OVERVIEW", "symbol": symbol, "apikey": self._api_key})
            if "Symbol" in result:
                return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="marketdata_get_fundamentals")

        elif self._backend == "twelvedata":
            result = await self._request("GET", "/profile", params={"symbol": symbol, "apikey": self._api_key})
            if "name" in result:
                return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="marketdata_get_fundamentals")

        return ToolInvocationResult(success=False, error="Fundamentals not available", provider_id=self.provider_id, tool_id="marketdata_get_fundamentals")

    async def _execute_marketdata_get_dividends_splits(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]
        from_date = params.get("from_date")
        to_date = params.get("to_date")

        if self._backend == "polygon":
            query = {"apikey": self._api_key, "limit": 1000}
            if from_date:
                query["ex_dividend_date.gte"] = from_date[:10]
            if to_date:
                query["ex_dividend_date.lte"] = to_date[:10]

            result = await self._request("GET", f"/v3/reference/dividends/{symbol}", params=query)
            if result.get("status") == "OK":
                return ToolInvocationResult(success=True, output=result.get("results", []), provider_id=self.provider_id, tool_id="marketdata_get_dividends_splits")

        return ToolInvocationResult(success=False, error="Not implemented for this backend", provider_id=self.provider_id, tool_id="marketdata_get_dividends_splits")

    async def _execute_marketdata_search_symbols(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query = params["query"]
        asset_type = params.get("asset_type", "all")
        limit = params.get("limit", 20)

        if self._backend == "polygon":
            market_map = {"stocks": "stocks", "forex": "fx", "crypto": "crypto", "options": "options", "indices": "indices"}
            market = market_map.get(asset_type, "stocks") if asset_type != "all" else None

            q = {"apikey": self._api_key, "search": query, "limit": limit, "active": "true"}
            if market:
                q["market"] = market

            result = await self._request("GET", "/v3/reference/tickers", params=q)
            if result.get("status") == "OK":
                return ToolInvocationResult(success=True, output=result.get("results", []), provider_id=self.provider_id, tool_id="marketdata_search_symbols")

        elif self._backend == "alphavantage":
            result = await self._request("GET", "", params={"function": "SYMBOL_SEARCH", "keywords": query, "apikey": self._api_key})
            if "bestMatches" in result:
                return ToolInvocationResult(success=True, output=result["bestMatches"][:limit], provider_id=self.provider_id, tool_id="marketdata_search_symbols")

        elif self._backend == "twelvedata":
            result = await self._request("GET", "/symbol_search", params={"symbol": query, "apikey": self._api_key})
            if "data" in result:
                return ToolInvocationResult(success=True, output=result["data"][:limit], provider_id=self.provider_id, tool_id="marketdata_search_symbols")

        elif self._backend == "yahoo":
            result = await self._request("GET", "/v1/finance/search", params={"q": query, "quotesCount": limit})
            if "quotes" in result:
                return ToolInvocationResult(success=True, output=result["quotes"], provider_id=self.provider_id, tool_id="marketdata_search_symbols")

        return ToolInvocationResult(success=False, error="Search not implemented", provider_id=self.provider_id, tool_id="marketdata_search_symbols")

    async def _execute_marketdata_get_news(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params.get("symbol")
        limit = params.get("limit", 10)
        from_date = params.get("from_date")

        if self._backend == "polygon":
            query = {"apikey": self._api_key, "limit": limit, "order": "desc", "sort": "published_utc"}
            if symbol:
                query["ticker"] = symbol
            if from_date:
                query["published_utc.gte"] = from_date[:10]

            result = await self._request("GET", "/v2/reference/news", params=query)
            if result.get("status") == "OK":
                return ToolInvocationResult(success=True, output=result.get("results", []), provider_id=self.provider_id, tool_id="marketdata_get_news")

        elif self._backend == "alphavantage":
            query = {"function": "NEWS_SENTIMENT", "apikey": self._api_key, "limit": limit}
            if symbol:
                query["tickers"] = symbol
            result = await self._request("GET", "", params=query)
            if "feed" in result:
                return ToolInvocationResult(success=True, output=result["feed"], provider_id=self.provider_id, tool_id="marketdata_get_news")

        return ToolInvocationResult(success=False, error="News not available", provider_id=self.provider_id, tool_id="marketdata_get_news")

    async def _execute_marketdata_get_economic_calendar(self, params: Dict[str, Any]) -> ToolInvocationResult:
        from_date = params.get("from_date", datetime.utcnow().date().isoformat())
        to_date = params.get("to_date", (datetime.utcnow() + timedelta(days=30)).date().isoformat())
        countries = params.get("countries", ["US"])
        impact = params.get("impact")

        if self._backend == "alphavantage":
            result = await self._request("GET", "", params={"function": "ECONOMIC_CALENDAR", "apikey": self._api_key})
            # Filter by date/country/impact
            events = []
            if "data" in result:
                for event in result["data"]:
                    event_date = event.get("date", "")[:10]
                    if from_date <= event_date <= to_date:
                        if not countries or event.get("country") in countries:
                            if not impact or event.get("impact", "").lower() in impact:
                                events.append(event)
            return ToolInvocationResult(success=True, output=events, provider_id=self.provider_id, tool_id="marketdata_get_economic_calendar")

        # Twelve Data also has economic calendar
        elif self._backend == "twelvedata":
            query = {"country": ",".join(countries), "apikey": self._api_key}
            result = await self._request("GET", "/economic_calendar", params=query)
            if "data" in result:
                return ToolInvocationResult(success=True, output=result["data"], provider_id=self.provider_id, tool_id="marketdata_get_economic_calendar")

        return ToolInvocationResult(success=False, error="Economic calendar not available", provider_id=self.provider_id, tool_id="marketdata_get_economic_calendar")

    async def _health_check_impl(self) -> ProviderHealth:
        try:
            # Test with a simple request
            if self._backend == "polygon":
                result = await self._request("GET", "/v2/last/trade/AAPL", params={"apikey": self._api_key})
                if result.get("status") == "OK":
                    return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)

            elif self._backend == "alphavantage":
                result = await self._request("GET", "", params={"function": "GLOBAL_QUOTE", "symbol": "AAPL", "apikey": self._api_key})
                if "Global Quote" in result:
                    return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)

            elif self._backend == "twelvedata":
                result = await self._request("GET", "/price", params={"symbol": "AAPL", "apikey": self._api_key})
                if "price" in result:
                    return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)

            elif self._backend == "yahoo":
                result = await self._request("GET", "/v7/finance/quote", params={"symbols": "AAPL"})
                if result.get("quoteResponse", {}).get("result"):
                    return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)

            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message="Health check failed")
        except Exception as e:
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))