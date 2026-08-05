"""Provider Base Classes — Abstract base and execution framework for integrations."""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel

from axiom.config import get_secrets_manager
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationRequest,
    ToolInvocationResult,
    RateLimitConfig,
    RetryConfig,
    CircuitBreakerConfig,
    CapabilityMapping,
)
from axiom.runtime.logging import RuntimeLogger


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 3

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0

    def can_execute(self) -> bool:
        """Check if a call can proceed."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        # HALF_OPEN
        return self.half_open_calls < self.half_open_max_calls

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class TokenBucket:
    """Token bucket rate limiter."""

    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_available(self) -> int:
        """Get available tokens."""
        self._refill()
        return int(self.tokens)

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now


class Provider(ABC):
    """Abstract base class for all providers.

    Every provider must implement:
    - initialize(): Setup connections, validate auth
    - get_tools(): Return list of tool definitions
    - execute_tool(): Execute a specific tool
    - health_check(): Check provider health
    - shutdown(): Clean up resources

    The base class handles:
    - Authentication (via SecretsManager)
    - Rate limiting (token bucket)
    - Retry logic (exponential backoff)
    - Circuit breaker
    - Audit logging
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.config = config
        self.logger = logger or RuntimeLogger()
        self._initialized = False
        self._tools: Dict[str, ProviderToolDefinition] = {}
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker.failure_threshold,
            success_threshold=config.circuit_breaker.success_threshold,
            timeout_seconds=config.circuit_breaker.timeout_seconds,
            half_open_max_calls=config.circuit_breaker.half_open_max_calls,
        )
        self._rate_limiter = TokenBucket(
            capacity=config.rate_limit.requests_per_minute,
            refill_rate=config.rate_limit.token_bucket_refill_rate,
        )
        self._secrets = get_secrets_manager()
        self._health = ProviderHealth(provider_id=config.id)

    @property
    def provider_id(self) -> str:
        return self.config.id

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def health(self) -> ProviderHealth:
        return self._health

    # ── Abstract Methods ──────────────────────────────────────────────────

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (connections, auth validation)."""
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources."""
        raise NotImplementedError

    @abstractmethod
    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        """Return list of tools this provider offers."""
        raise NotImplementedError

    @abstractmethod
    async def _execute_tool_impl(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> ToolInvocationResult:
        """Execute a tool implementation."""
        raise NotImplementedError

    @abstractmethod
    async def _health_check_impl(self) -> ProviderHealth:
        """Provider-specific health check."""
        raise NotImplementedError

    # ── Public API ────────────────────────────────────────────────────────

    def refresh_tools(self) -> None:
        """Refresh tool definitions from implementation."""
        self._tools = {t.tool_id: t for t in self.get_tool_definitions()}

    def get_tool(self, tool_id: str) -> Optional[ProviderToolDefinition]:
        """Get a tool by ID."""
        return self._tools.get(tool_id)

    def get_schema(self) -> Dict[str, Any]:
        """Return provider schema for status/debugging."""
        return {
            "provider_id": self.provider_id,
            "type": self.config.type.value if self.config else "unknown",
            "enabled": self.config.enabled if self.config else True,
            "base_url": self.config.base_url if self.config else None,
            "tools": [
                {
                    "tool_id": t.tool_id,
                    "name": t.name,
                    "description": t.description,
                    "capability": t.capability,
                    "requires_approval": t.requires_approval,
                    "risk_level": t.risk_level,
                    "enabled": t.enabled,
                }
                for t in self._tools.values()
            ],
            "health": {
                "status": self._health.status.value,
                "latency_ms": self._health.latency_ms,
                "consecutive_successes": self._health.consecutive_successes,
                "consecutive_failures": self._health.consecutive_failures,
            },
            "circuit_breaker": {
                "state": self._circuit_breaker.state.value,
                "failure_count": self._circuit_breaker.failure_count,
            },
            "rate_limit": {
                "requests_per_minute": self.config.rate_limit.requests_per_minute if self.config else 0,
                "token_bucket_refill_rate": self.config.rate_limit.token_bucket_refill_rate if self.config else 0,
            },
        }

    async def execute_tool(self, request: ToolInvocationRequest) -> ToolInvocationResult:
        """Execute a tool with full contract enforcement.

        Flow:
        1. Check circuit breaker
        2. Check rate limit
        3. Check tool exists and is enabled
        4. Execute with retry logic
        5. Update circuit breaker and rate limiter
        6. Return result with audit data
        """
        start_time = time.perf_counter()
        correlation_id = request.correlation_id

        # 1. Check if provider is enabled
        if not self.config.enabled:
            return ToolInvocationResult(
                success=False,
                error=f"Provider {self.provider_id} is disabled",
                error_code="provider_disabled",
                provider_id=self.provider_id,
                tool_id=request.tool_id,
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 2. Check circuit breaker
        if not self._circuit_breaker.can_execute():
            return ToolInvocationResult(
                success=False,
                error=f"Circuit breaker OPEN for {self.provider_id}",
                error_code="circuit_breaker_open",
                provider_id=self.provider_id,
                tool_id=request.tool_id,
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 3. Check rate limit
        tool_def = self.get_tool(request.tool_id)
        if not tool_def:
            return ToolInvocationResult(
                success=False,
                error=f"Tool {request.tool_id} not found in provider {self.provider_id}",
                error_code="tool_not_found",
                provider_id=self.provider_id,
                tool_id=request.tool_id,
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        if not tool_def.enabled:
            return ToolInvocationResult(
                success=False,
                error=f"Tool {request.tool_id} is disabled",
                error_code="tool_disabled",
                provider_id=self.provider_id,
                tool_id=request.tool_id,
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Use tool-specific rate limit or provider default
        rate_limit = tool_def.rate_limit_override or self.config.rate_limit
        bucket = getattr(self, f"_rate_limiter_{request.tool_id}", None)
        if bucket is None:
            bucket = TokenBucket(
                capacity=rate_limit.requests_per_minute,
                refill_rate=rate_limit.token_bucket_refill_rate,
            )
            setattr(self, f"_rate_limiter_{request.tool_id}", bucket)

        if not bucket.consume(1):
            return ToolInvocationResult(
                success=False,
                error=f"Rate limit exceeded for {request.tool_id}",
                error_code="rate_limited",
                provider_id=self.provider_id,
                tool_id=request.tool_id,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                rate_limit_remaining=bucket.get_available(),
            )

        # 4. Execute with retry
        retry_config = self.config.retry
        last_error = None

        for attempt in range(retry_config.max_attempts):
            try:
                result = await self._execute_with_timeout(
                    tool_def, request.parameters, request.correlation_id
                )

                # Success
                duration = (time.perf_counter() - start_time) * 1000
                result.duration_ms = duration
                result.rate_limit_remaining = bucket.get_available()

                self._circuit_breaker.record_success()
                self._update_health(success=True, latency_ms=duration)

                # Audit log
                self._audit_log(request, result, success=True)

                return result

            except asyncio.TimeoutError:
                last_error = f"Tool execution timed out after {self.config.retry.base_delay_seconds}s"
            except Exception as e:
                last_error = str(e)

                # Check if we should retry
                if attempt < retry_config.max_attempts - 1:
                    delay = self._calculate_backoff(attempt, retry_config)
                    await asyncio.sleep(delay)
                    continue

        # All retries failed
        duration = (time.perf_counter() - start_time) * 1000
        self._circuit_breaker.record_failure()
        self._update_health(success=False, error=str(last_error))

        result = ToolInvocationResult(
            success=False,
            error=last_error or "Tool execution failed after retries",
            error_code="execution_failed",
            provider_id=self.provider_id,
            tool_id=request.tool_id,
            duration_ms=duration,
            rate_limit_remaining=bucket.get_available(),
        )

        self._audit_log(request, result, success=False)
        return result

    async def _execute_with_timeout(
        self, tool_def: ProviderToolDefinition, params: Dict[str, Any], correlation_id: str
    ) -> ToolInvocationResult:
        """Execute tool with timeout."""
        timeout = getattr(tool_def, "timeout_seconds", None) or 30.0
        return await asyncio.wait_for(
            self._execute_tool_impl(tool_def.tool_id, params),
            timeout=timeout,
        )

    def _calculate_backoff(self, attempt: int, config: RetryConfig) -> float:
        """Calculate exponential backoff with optional jitter."""
        delay = min(
            config.base_delay_seconds * (config.exponential_base ** attempt),
            config.max_delay_seconds,
        )
        if config.jitter:
            import random
            delay *= (0.5 + random.random())
        return delay

    async def health_check(self) -> ProviderHealth:
        """Run health check with circuit breaker awareness."""
        if not self._circuit_breaker.can_execute():
            self._health.status = ProviderStatus.UNHEALTHY
            self._health.error_message = "Circuit breaker OPEN"
            return self._health

        try:
            self._health = await self._health_check_impl()
            self._health.last_check = datetime.utcnow()
            if self._health.status == ProviderStatus.HEALTHY:
                self._health.last_success = datetime.utcnow()
                self._health.consecutive_successes += 1
                self._health.consecutive_failures = 0
            else:
                self._health.last_failure = datetime.utcnow()
                self._health.consecutive_failures += 1
                self._health.consecutive_successes = 0
        except Exception as e:
            self._health.status = ProviderStatus.UNHEALTHY
            self._health.error_message = str(e)
            self._health.last_check = datetime.utcnow()
            self._health.last_failure = datetime.utcnow()
            self._health.consecutive_failures += 1
            self._health.consecutive_successes = 0

        return self._health

    def _update_health(self, success: bool, latency_ms: float = 0, error: Optional[str] = None) -> None:
        """Update health status from tool execution."""
        self._health.last_check = datetime.utcnow()
        self._health.latency_ms = latency_ms
        if success:
            self._health.status = ProviderStatus.HEALTHY
            self._health.last_success = datetime.utcnow()
            self._health.consecutive_successes += 1
            self._health.consecutive_failures = 0
        else:
            self._health.last_failure = datetime.utcnow()
            self._health.consecutive_failures += 1
            self._health.consecutive_successes = 0
            if self._health.consecutive_failures >= self.config.circuit_breaker.failure_threshold:
                self._health.status = ProviderStatus.UNHEALTHY
            elif self._health.consecutive_failures > 0:
                self._health.status = ProviderStatus.DEGRADED

    def _audit_log(
        self,
        request: ToolInvocationRequest,
        result: ToolInvocationResult,
        success: bool,
    ) -> None:
        """Log tool invocation for audit trail."""
        sanitized_params = self._secrets.sanitize_for_logging(request.parameters)
        sanitized_output = self._secrets.sanitize_for_logging(
            result.output if isinstance(result.output, dict) else {"output": str(result.output)}
        )

        audit_entry = {
            "correlation_id": request.correlation_id,
            "provider_id": self.provider_id,
            "tool_id": request.tool_id,
            "agent_id": request.agent_id,
            "org_id": request.org_id,
            "success": success,
            "duration_ms": result.duration_ms,
            "parameters": sanitized_params,
            "output": sanitized_output,
            "error": result.error,
            "error_code": result.error_code,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Write to audit log
        self.logger.log_tool_audit(audit_entry)

        # Also record in memory if available
        # (Would integrate with MemoryEngine in runtime)


class ExternalAPIProvider(Provider):
    """Base class for HTTP-based external API providers.

    Provides:
    - HTTP client management (aiohttp)
    - Automatic auth header injection
    - Request/response logging
    - Standard error handling
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._session: Optional[Any] = None  # aiohttp.ClientSession
        self._auth_headers: Dict[str, str] = {}

    def _build_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers from config and secrets."""
        headers = {}
        auth = self.config.auth

        if auth.type == AuthType.BEARER_TOKEN:
            token = self._secrets.get_secret(auth.token_env_var) if auth.token_env_var else None
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth.type == AuthType.API_KEY:
            token = self._secrets.get_secret(auth.token_env_var) if auth.token_env_var else None
            if token:
                headers["X-API-Key"] = token
        elif auth.type == AuthType.BASIC_AUTH:
            username = self._secrets.get_secret(auth.username_env_var) if auth.username_env_var else None
            password = self._secrets.get_secret(auth.password_env_var) if auth.password_env_var else None
            if username and password:
                import base64
                creds = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {creds}"

        return headers

    async def initialize(self) -> None:
        """Initialize HTTP session and validate auth."""
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(timeout=timeout)
        self._auth_headers = self._build_auth_headers()

        # Validate auth with a simple request if health endpoint exists
        if self.config.health_check_endpoint:
            await self.health_check()

        self._initialized = True

    async def shutdown(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
        self._initialized = False

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an HTTP request with auth and error handling."""
        if not self._session:
            raise RuntimeError("Provider not initialized")

        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        request_headers = {**self._auth_headers, **(headers or {})}

        self.logger.debug(f"API Request: {method} {url}")

        async with self._session.request(
            method, url, params=params, json=json, headers=request_headers
        ) as response:
            self.logger.debug(f"API Response: {response.status}")

            if response.status >= 400:
                text = await response.text()
                raise ProviderAPIError(
                    f"API error {response.status}: {text}",
                    status_code=response.status,
                    response_text=text,
                )

            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return await response.json()
            return await response.text()

    async def _health_check_impl(self) -> ProviderHealth:
        """Default health check - GET health endpoint."""
        if not self.config.health_check_endpoint:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.HEALTHY,
                details={"note": "No health endpoint configured"},
            )

        start = time.perf_counter()
        try:
            await self._request("GET", self.config.health_check_endpoint)
            latency = (time.perf_counter() - start) * 1000
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.HEALTHY,
                latency_ms=latency,
            )
        except ProviderAPIError as e:
            if e.status_code == 401:
                return ProviderHealth(
                    provider_id=self.provider_id,
                    status=ProviderStatus.NO_AUTH,
                    error_message="Authentication failed",
                )
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.UNHEALTHY,
                error_message=str(e),
            )
        except Exception as e:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.UNHEALTHY,
                error_message=str(e),
            )


class ProviderAPIError(Exception):
    """API error from provider."""

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        response_text: str = "",
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


# Import AuthType for use in ExternalAPIProvider
from axiom.models.providers import AuthType