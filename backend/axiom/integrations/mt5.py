"""MT5 Provider — MetaTrader 5 integration for account data and market data (READ ONLY)."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from axiom.engine.provider import Provider
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationResult,
)
from axiom.runtime.logging import RuntimeLogger


class MT5Provider(Provider):
    """MetaTrader 5 provider for trading account data and market data.

    IMPORTANT: READ-ONLY / DATA AND ANALYSIS ONLY.
    No trade execution capabilities.

    Capabilities:
    - Account info (balance, equity, margin, leverage)
    - Positions (open positions, history)
    - Orders (pending orders, history)
    - Market data (symbols, ticks, rates)
    - Deals history
    - Account summary and statistics
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._mt5 = None
        self._connected = False

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            ProviderToolDefinition(
                tool_id="mt5_account_info",
                name="Get Account Info",
                description="Get account information (balance, equity, margin, etc.)",
                capability="account_read",
                input_schema={},
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_positions",
                name="Get Open Positions",
                description="Get all open positions",
                capability="positions_read",
                input_schema={},
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_orders",
                name="Get Pending Orders",
                description="Get all pending orders",
                capability="orders_read",
                input_schema={},
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_history_deals",
                name="Get Deal History",
                description="Get historical deals",
                capability="history_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "from_date": {"type": "string", "description": "ISO datetime"},
                        "to_date": {"type": "string", "description": "ISO datetime"},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_history_orders",
                name="Get Order History",
                description="Get historical orders",
                capability="history_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "from_date": {"type": "string", "description": "ISO datetime"},
                        "to_date": {"type": "string", "description": "ISO datetime"},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_symbols",
                name="Get Available Symbols",
                description="Get list of available trading symbols",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "group": {"type": "string", "description": "Symbol group filter (e.g., 'FOREX*', 'GOLD*')"},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_symbol_info",
                name="Get Symbol Info",
                description="Get detailed symbol specification",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_rates",
                name="Get Historical Rates",
                description="Get historical price data (OHLCV)",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "timeframe": {"type": "string", "enum": ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"], "default": "H1"},
                        "count": {"type": "integer", "default": 100},
                        "from_date": {"type": "string", "description": "ISO datetime"},
                        "to_date": {"type": "string", "description": "ISO datetime"},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="mt5_get_ticks",
                name="Get Tick Data",
                description="Get recent tick data",
                capability="market_data_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "count": {"type": "integer", "default": 1000},
                        "from_date": {"type": "string", "description": "ISO datetime"},
                    },
                    "required": ["symbol"],
                },
            ),
            ProviderToolDefinition(
                tool_id="mt5_account_summary",
                name="Get Account Summary",
                description="Get comprehensive account summary for reporting",
                capability="account_read",
                input_schema={},
            ),
        ]

    async def initialize(self) -> None:
        """Initialize MT5 connection."""
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
        except ImportError:
            raise RuntimeError("MetaTrader5 package not installed. Install with: pip install MetaTrader5")

        # Get connection parameters from config
        login = self.config.config.get("login")
        password = self._secrets.get_secret(self.config.auth.password_env_var or "MT5_PASSWORD")
        server = self.config.config.get("server")
        path = self.config.config.get("path")

        if not all([login, password, server]):
            raise RuntimeError("MT5 credentials not fully configured")

        # Initialize MT5
        if not self._mt5.initialize(
            login=int(login),
            password=password,
            server=server,
            path=path,
        ):
            error = self._mt5.last_error()
            raise RuntimeError(f"MT5 initialization failed: {error}")

        self._connected = True
        self._initialized = True

        # Verify connection
        account_info = self._mt5.account_info()
        if account_info is None:
            raise RuntimeError("Failed to get account info after connection")

        self.logger.info(f"MT5 connected: Account {account_info.login}, Server: {account_info.server}")

    async def shutdown(self) -> None:
        """Shutdown MT5 connection."""
        if self._mt5 and self._connected:
            self._mt5.shutdown()
            self._connected = False

    async def _execute_tool_impl(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> ToolInvocationResult:
        if not self._connected:
            return ToolInvocationResult(
                success=False,
                error="MT5 not connected",
                error_code="not_connected",
                provider_id=self.provider_id,
                tool_id=tool_id,
            )

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

    async def _execute_mt5_account_info(self, params: Dict[str, Any]) -> ToolInvocationResult:
        info = self._mt5.account_info()
        if info is None:
            return ToolInvocationResult(success=False, error="Failed to get account info", provider_id=self.provider_id, tool_id="mt5_account_info")

        return ToolInvocationResult(
            success=True,
            output={
                "login": info.login,
                "server": info.server,
                "balance": info.balance,
                "equity": info.equity,
                "margin": info.margin,
                "margin_free": info.margin_free,
                "margin_level": info.margin_level,
                "leverage": info.leverage,
                "currency": info.currency,
                "profit": info.profit,
                "credit": info.credit,
                "trade_mode": info.trade_mode,
                "trade_allowed": info.trade_allowed,
                "expert_allowed": info.trade_expert,
            },
            provider_id=self.provider_id,
            tool_id="mt5_account_info",
        )

    async def _execute_mt5_get_positions(self, params: Dict[str, Any]) -> ToolInvocationResult:
        positions = self._mt5.positions_get()
        if positions is None:
            return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="mt5_get_positions")

        result = []
        for pos in positions:
            result.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "buy" if pos.type == 0 else "sell",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "swap": pos.swap,
                "comment": pos.comment,
                "magic": pos.magic,
                "time": datetime.fromtimestamp(pos.time).isoformat(),
                "time_update": datetime.fromtimestamp(pos.time_update).isoformat() if pos.time_update else None,
            })

        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="mt5_get_positions")

    async def _execute_mt5_get_orders(self, params: Dict[str, Any]) -> ToolInvocationResult:
        orders = self._mt5.orders_get()
        if orders is None:
            return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="mt5_get_orders")

        result = []
        for order in orders:
            result.append({
                "ticket": order.ticket,
                "symbol": order.symbol,
                "type": self._order_type_to_str(order.type),
                "volume": order.volume_initial,
                "price_open": order.price_open,
                "sl": order.sl,
                "tp": order.tp,
                "comment": order.comment,
                "magic": order.magic,
                "time_setup": datetime.fromtimestamp(order.time_setup).isoformat(),
                "time_expiration": datetime.fromtimestamp(order.time_expiration).isoformat() if order.time_expiration else None,
            })

        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="mt5_get_orders")

    def _order_type_to_str(self, type_val: int) -> str:
        types = {
            0: "buy_limit", 1: "sell_limit", 2: "buy_stop", 3: "sell_stop",
            4: "buy_stop_limit", 5: "sell_stop_limit",
        }
        return types.get(type_val, f"unknown_{type_val}")

    async def _execute_mt5_get_history_deals(self, params: Dict[str, Any]) -> ToolInvocationResult:
        from_date = params.get("from_date")
        to_date = params.get("to_date", datetime.utcnow().isoformat())

        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        else:
            from_dt = datetime.utcnow() - timedelta(days=30)

        to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

        deals = self._mt5.history_deals_get(from_dt, to_dt)
        if deals is None:
            return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="mt5_get_history_deals")

        result = []
        for deal in deals:
            result.append({
                "ticket": deal.ticket,
                "order": deal.order,
                "symbol": deal.symbol,
                "type": "buy" if deal.type == 0 else "sell",
                "volume": deal.volume,
                "price": deal.price,
                "profit": deal.profit,
                "commission": deal.commission,
                "swap": deal.swap,
                "fee": deal.fee,
                "comment": deal.comment,
                "time": datetime.fromtimestamp(deal.time).isoformat(),
            })

        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="mt5_get_history_deals")

    async def _execute_mt5_get_history_orders(self, params: Dict[str, Any]) -> ToolInvocationResult:
        from_date = params.get("from_date")
        to_date = params.get("to_date", datetime.utcnow().isoformat())

        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        else:
            from_dt = datetime.utcnow() - timedelta(days=30)

        to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

        orders = self._mt5.history_orders_get(from_dt, to_dt)
        if orders is None:
            return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="mt5_get_history_orders")

        result = []
        for order in orders:
            result.append({
                "ticket": order.ticket,
                "symbol": order.symbol,
                "type": self._order_type_to_str(order.type),
                "volume": order.volume_initial,
                "price_open": order.price_open,
                "sl": order.sl,
                "tp": order.tp,
                "state": self._order_state_to_str(order.state),
                "time_setup": datetime.fromtimestamp(order.time_setup).isoformat(),
                "time_done": datetime.fromtimestamp(order.time_done).isoformat() if order.time_done else None,
            })

        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="mt5_get_history_orders")

    def _order_state_to_str(self, state: int) -> str:
        states = {
            0: "started", 1: "placed", 2: "canceled", 3: "partial", 4: "filled", 5: "rejected", 6: "expired",
        }
        return states.get(state, f"unknown_{state}")

    async def _execute_mt5_get_symbols(self, params: Dict[str, Any]) -> ToolInvocationResult:
        group = params.get("group", "*")
        symbols = self._mt5.symbols_get(group)
        if symbols is None:
            return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="mt5_get_symbols")

        result = []
        for sym in symbols:
            result.append({
                "name": sym.name,
                "description": sym.description,
                "currency_base": sym.currency_base,
                "currency_profit": sym.currency_profit,
                "currency_margin": sym.currency_margin,
                "digits": sym.digits,
                "trade_mode": sym.trade_mode,
                "min_lot": sym.volume_min,
                "max_lot": sym.volume_max,
                "step_lot": sym.volume_step,
                "spread": sym.spread,
            })

        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="mt5_get_symbols")

    async def _execute_mt5_get_symbol_info(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]
        info = self._mt5.symbol_info(symbol)
        if info is None:
            return ToolInvocationResult(success=False, error=f"Symbol {symbol} not found", provider_id=self.provider_id, tool_id="mt5_get_symbol_info")

        return ToolInvocationResult(
            success=True,
            output={
                "name": info.name,
                "description": info.description,
                "currency_base": info.currency_base,
                "currency_profit": info.currency_profit,
                "currency_margin": info.currency_margin,
                "digits": info.digits,
                "trade_mode": info.trade_mode,
                "min_lot": info.volume_min,
                "max_lot": info.volume_max,
                "step_lot": info.volume_step,
                "spread": info.spread,
                "spread_float": info.spread_float,
                "ticks_bookdepth": info.ticks_bookdepth,
                "points": info.point,
                "trade_contract_size": info.trade_contract_size,
                "trade_tick_value": info.trade_tick_value,
                "trade_tick_value_profit": info.trade_tick_value_profit,
                "trade_tick_value_loss": info.trade_tick_value_loss,
                "swap_long": info.swap_long,
                "swap_short": info.swap_short,
                "margin_hedged": info.margin_hedged,
                "margin_initial": info.margin_initial,
                "margin_maintenance": info.margin_maintenance,
            },
            provider_id=self.provider_id,
            tool_id="mt5_get_symbol_info",
        )

    async def _execute_mt5_get_rates(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]
        timeframe = params.get("timeframe", "H1")
        count = params.get("count", 100)
        from_date = params.get("from_date")
        to_date = params.get("to_date")

        # Map timeframe string to MT5 constant
        tf_map = {
            "M1": self._mt5.TIMEFRAME_M1, "M5": self._mt5.TIMEFRAME_M5,
            "M15": self._mt5.TIMEFRAME_M15, "M30": self._mt5.TIMEFRAME_M30,
            "H1": self._mt5.TIMEFRAME_H1, "H4": self._mt5.TIMEFRAME_H4,
            "D1": self._mt5.TIMEFRAME_D1, "W1": self._mt5.TIMEFRAME_W1,
            "MN1": self._mt5.TIMEFRAME_MN1,
        }
        tf = tf_map.get(timeframe, self._mt5.TIMEFRAME_H1)

        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            rates = self._mt5.copy_rates_range(symbol, tf, from_dt, datetime.fromisoformat(to_date.replace("Z", "+00:00")) if to_date else datetime.utcnow())
        else:
            rates = self._mt5.copy_rates_from_pos(symbol, tf, 0, count)

        if rates is None:
            return ToolInvocationResult(success=False, error="Failed to get rates", provider_id=self.provider_id, tool_id="mt5_get_rates")

        result = []
        for rate in rates:
            result.append({
                "time": datetime.fromtimestamp(rate[0]).isoformat(),
                "open": rate[1],
                "high": rate[2],
                "low": rate[3],
                "close": rate[4],
                "tick_volume": rate[5],
                "spread": rate[6],
                "real_volume": rate[7],
            })

        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="mt5_get_rates")

    async def _execute_mt5_get_ticks(self, params: Dict[str, Any]) -> ToolInvocationResult:
        symbol = params["symbol"]
        count = params.get("count", 1000)
        from_date = params.get("from_date")

        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            ticks = self._mt5.copy_ticks_range(symbol, from_dt, datetime.utcnow(), self._mt5.COPY_TICKS_ALL)
        else:
            ticks = self._mt5.copy_ticks_from(symbol, datetime.utcnow(), count, self._mt5.COPY_TICKS_ALL)

        if ticks is None:
            return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="mt5_get_ticks")

        result = []
        for tick in ticks:
            result.append({
                "time": datetime.fromtimestamp(tick[0]).isoformat(),
                "bid": tick[1],
                "ask": tick[2],
                "last": tick[3],
                "volume": tick[4],
                "flags": tick[5],
            })

        return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="mt5_get_ticks")

    async def _execute_mt5_account_summary(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # Combine account info, positions, and basic stats
        account = await self._execute_mt5_account_info({})
        positions = await self._execute_mt5_get_positions({})
        orders = await self._execute_mt5_get_orders({})

        # Calculate stats from positions
        total_profit = sum(p.get("profit", 0) for p in positions.output) if positions.success else 0
        total_swap = sum(p.get("swap", 0) for p in positions.output) if positions.success else 0

        return ToolInvocationResult(
            success=True,
            output={
                "account": account.output,
                "open_positions": len(positions.output) if positions.success else 0,
                "pending_orders": len(orders.output) if orders.success else 0,
                "total_unrealized_profit": total_profit,
                "total_swap": total_swap,
                "margin_used_pct": (account.output.get("margin", 0) / account.output.get("equity", 1) * 100) if account.success else 0,
            },
            provider_id=self.provider_id,
            tool_id="mt5_account_summary",
        )

    async def _health_check_impl(self) -> ProviderHealth:
        try:
            if not self._connected or not self._mt5:
                return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message="Not connected")

            info = self._mt5.account_info()
            if info is None:
                return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message="No account info")

            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)
        except Exception as e:
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))