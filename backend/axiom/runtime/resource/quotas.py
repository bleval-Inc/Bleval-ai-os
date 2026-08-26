"""Quota Manager — Resource quotas and limits for agents, users, organizations."""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from axiom.runtime.logging import RuntimeLogger


class QuotaConfig(BaseModel):
    """Quota configuration."""

    # CPU quotas (percentage of total)
    max_cpu_per_agent: float = 20.0  # Max CPU % per agent
    max_cpu_per_user: float = 50.0   # Max CPU % per user
    max_cpu_per_org: float = 80.0    # Max CPU % per organization

    # Memory quotas (percentage of total)
    max_memory_per_agent: float = 25.0
    max_memory_per_user: float = 60.0
    max_memory_per_org: float = 90.0

    # Concurrent tasks
    max_concurrent_per_agent: int = 5
    max_concurrent_per_user: int = 20
    max_concurrent_per_org: int = 50

    # API calls per minute
    api_calls_per_minute_per_agent: int = 100
    api_calls_per_minute_per_user: int = 500
    api_calls_per_minute_per_org: int = 2000

    # Storage quotas (MB)
    storage_per_agent: int = 500
    storage_per_user: int = 2000
    storage_per_org: int = 10000

    # Token quotas (for LLM)
    tokens_per_minute_per_agent: int = 50000
    tokens_per_minute_per_user: int = 200000
    tokens_per_minute_per_org: int = 1000000

    # Daily limits
    tokens_per_day_per_agent: int = 500000
    tokens_per_day_per_user: int = 2000000
    tokens_per_day_per_org: int = 10000000

    # Custom quotas
    custom_quotas: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class QuotaScope(str, Enum):
    """Quota scope."""

    AGENT = "agent"
    USER = "user"
    ORGANIZATION = "organization"
    GLOBAL = "global"


class QuotaType(str, Enum):
    """Quota resource type."""

    CPU = "cpu"
    MEMORY = "memory"
    CONCURRENT_TASKS = "concurrent_tasks"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    TOKENS = "tokens"
    TOKENS_DAILY = "tokens_daily"
    CUSTOM = "custom"


class QuotaViolation(BaseModel):
    """Quota violation record."""

    scope: QuotaScope
    scope_id: str
    quota_type: QuotaType
    limit: float
    current: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str = "rejected"  # rejected, warned, throttled


class QuotaUsage(BaseModel):
    """Current quota usage."""

    scope: QuotaScope
    scope_id: str
    quotas: Dict[QuotaType, Dict[str, float]] = Field(default_factory=dict)
    # Format: {quota_type: {"used": x, "limit": y, "percent": z}}

    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuotaManager:
    """Manages resource quotas."""

    def __init__(
        self,
        config: Optional[QuotaConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.config = config or QuotaConfig()
        self.logger = logger or RuntimeLogger()

        self._usage: Dict[str, QuotaUsage] = {}
        self._violations: List[QuotaViolation] = []
        self._max_violations = 1000

        # Sliding windows for rate limits
        self._api_windows: Dict[str, List[datetime]] = {}
        self._token_windows: Dict[str, List[datetime]] = {}
        self._daily_token_windows: Dict[str, Dict[datetime, int]] = {}

    def _get_scope_key(self, scope: QuotaScope, scope_id: str) -> str:
        return f"{scope.value}:{scope_id}"

    def _get_limits(self, scope: QuotaScope) -> Dict[str, float]:
        """Get limits for scope."""
        if scope == QuotaScope.AGENT:
            return {
                "cpu": self.config.max_cpu_per_agent,
                "memory": self.config.max_memory_per_agent,
                "concurrent": self.config.max_concurrent_per_agent,
                "api_calls": self.config.api_calls_per_minute_per_agent,
                "storage": self.config.storage_per_agent,
                "tokens": self.config.tokens_per_minute_per_agent,
                "tokens_daily": self.config.tokens_per_day_per_agent,
            }
        elif scope == QuotaScope.USER:
            return {
                "cpu": self.config.max_cpu_per_user,
                "memory": self.config.max_memory_per_user,
                "concurrent": self.config.max_concurrent_per_user,
                "api_calls": self.config.api_calls_per_minute_per_user,
                "storage": self.config.storage_per_user,
                "tokens": self.config.tokens_per_minute_per_user,
                "tokens_daily": self.config.tokens_per_day_per_user,
            }
        elif scope == QuotaScope.ORGANIZATION:
            return {
                "cpu": self.config.max_cpu_per_org,
                "memory": self.config.max_memory_per_org,
                "concurrent": self.config.max_concurrent_per_org,
                "api_calls": self.config.api_calls_per_minute_per_org,
                "storage": self.config.storage_per_org,
                "tokens": self.config.tokens_per_minute_per_org,
                "tokens_daily": self.config.tokens_per_day_per_org,
            }
        return {}

    async def check_quota(
        self,
        scope: QuotaScope,
        scope_id: str,
        quota_type: QuotaType,
        requested: float = 1.0,
    ) -> Tuple[bool, Optional[QuotaViolation]]:
        """Check if quota allows request."""
        key = self._get_scope_key(scope, scope_id)
        limits = self._get_limits(scope)

        limit = limits.get(quota_type.value, float('inf'))
        if limit == float('inf'):
            return True, None

        # Get current usage
        usage = await self._get_current_usage(scope, scope_id, quota_type)

        if usage + requested > limit:
            violation = QuotaViolation(
                scope=scope,
                scope_id=scope_id,
                quota_type=quota_type,
                limit=limit,
                current=usage + requested,
            )
            self._violations.append(violation)
            if len(self._violations) > self._max_violations:
                self._violations.pop(0)
            return False, violation

        return True, None

    async def consume_quota(
        self,
        scope: QuotaScope,
        scope_id: str,
        quota_type: QuotaType,
        amount: float = 1.0,
    ) -> bool:
        """Consume quota."""
        allowed, violation = await self.check_quota(scope, scope_id, quota_type, amount)
        if not allowed:
            return False

        # Update usage
        key = self._get_scope_key(scope, scope_id)
        if key not in self._usage:
            self._usage[key] = QuotaUsage(scope=scope, scope_id=scope_id)

        if quota_type == QuotaType.API_CALLS:
            return await self._record_api_call(scope, scope_id, amount)
        elif quota_type == QuotaType.TOKENS:
            return await self._record_tokens(scope, scope_id, amount)
        elif quota_type == QuotaType.CONCURRENT_TASKS:
            # Handled by scheduler
            return True

        return True

    async def release_quota(
        self,
        scope: QuotaScope,
        scope_id: str,
        quota_type: QuotaType,
        amount: float = 1.0,
    ):
        """Release quota (for concurrent tasks)."""
        if quota_type == QuotaType.CONCURRENT_TASKS:
            # Would track and decrement
            pass

    async def _get_current_usage(
        self, scope: QuotaScope, scope_id: str, quota_type: QuotaType
    ) -> float:
        """Get current usage for quota type."""
        key = self._get_scope_key(scope, scope_id)

        if quota_type == QuotaType.API_CALLS:
            return await self._count_api_calls(scope, scope_id)
        elif quota_type == QuotaType.TOKENS:
            return await self._count_tokens(scope, scope_id)
        elif quota_type == QuotaType.TOKENS_DAILY:
            return await self._count_daily_tokens(scope, scope_id)
        elif quota_type == QuotaType.CONCURRENT_TASKS:
            # Would query scheduler
            return 0

        # For static quotas (CPU, memory, storage)
        # Would query actual system metrics
        return 0

    async def _record_api_call(self, scope: QuotaScope, scope_id: str, amount: float) -> bool:
        """Record API call in sliding window."""
        key = self._get_scope_key(scope, scope_id)
        now = datetime.utcnow()
        minute_key = now.replace(second=0, microsecond=0)

        if key not in self._api_windows:
            self._api_windows[key] = []

        window = self._api_windows[key]
        window.append(now)

        # Remove old entries (> 1 minute)
        cutoff = now - timedelta(minutes=1)
        self._api_windows[key] = [t for t in window if t > cutoff]

        return True

    async def _count_api_calls(self, scope: QuotaScope, scope_id: str) -> int:
        """Count API calls in current window."""
        key = self._get_scope_key(scope, scope_id)
        if key not in self._api_windows:
            return 0

        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        return len([t for t in self._api_windows[key] if t > cutoff])

    async def _record_tokens(self, scope: QuotaScope, scope_id: str, amount: float) -> bool:
        """Record token usage."""
        key = self._get_scope_key(scope, scope_id)
        now = datetime.utcnow()
        minute_key = now.replace(second=0, microsecond=0)

        if key not in self._token_windows:
            self._token_windows[key] = []

        self._token_windows[key].append(now)

        # Minute window
        cutoff = now - timedelta(minutes=1)
        self._token_windows[key] = [t for t in self._token_windows[key] if t > cutoff]

        # Daily window
        day_key = now.date()
        if key not in self._daily_token_windows:
            self._daily_token_windows[key] = {}

        self._daily_token_windows[key][day_key] = self._daily_token_windows[key].get(day_key, 0) + amount

        # Cleanup old days
        cutoff_day = now.date() - timedelta(days=7)
        self._daily_token_windows[key] = {
            d: v for d, v in self._daily_token_windows[key].items() if d > cutoff_day
        }

        return True

    async def _count_tokens(self, scope: QuotaScope, scope_id: str) -> float:
        """Count tokens in current minute."""
        key = self._get_scope_key(scope, scope_id)
        if key not in self._token_windows:
            return 0

        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        # Simplified - would track actual token counts
        return len([t for t in self._token_windows[key] if t > cutoff]) * 1000

    async def _count_daily_tokens(self, scope: QuotaScope, scope_id: str) -> float:
        """Count tokens today."""
        key = self._get_scope_key(scope, scope_id)
        if key not in self._daily_token_windows:
            return 0

        today = datetime.utcnow().date()
        return self._daily_token_windows[key].get(today, 0)

    def get_usage(self, scope: QuotaScope, scope_id: str) -> Optional[QuotaUsage]:
        """Get current usage for scope."""
        key = self._get_scope_key(scope, scope_id)
        return self._usage.get(key)

    def get_all_usage(self, scope: Optional[QuotaScope] = None) -> List[QuotaUsage]:
        """Get all usage records."""
        result = []
        for usage in self._usage.values():
            if scope is None or usage.scope == scope:
                result.append(usage)
        return result

    def get_violations(
        self,
        scope: Optional[QuotaScope] = None,
        scope_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[QuotaViolation]:
        """Get quota violations."""
        violations = self._violations
        if scope:
            violations = [v for v in violations if v.scope == scope]
        if scope_id:
            violations = [v for v in violations if v.scope_id == scope_id]
        if since:
            violations = [v for v in violations if v.timestamp >= since]
        return violations

    async def get_quota_status(
        self, scope: QuotaScope, scope_id: str
    ) -> Dict[str, Any]:
        """Get full quota status for scope."""
        limits = self._get_limits(scope)
        status = {}

        for quota_type, limit in limits.items():
            if isinstance(limit, float) and limit == float('inf'):
                continue

            qt = QuotaType(quota_type)
            used = await self._get_current_usage(scope, scope_id, qt)
            status[quota_type] = {
                "used": used,
                "limit": limit,
                "percent": (used / limit * 100) if limit > 0 else 0,
                "available": max(0, limit - used),
            }

        return status

    def reset_usage(self, scope: QuotaScope, scope_id: str):
        """Reset usage for scope (for testing)."""
        key = self._get_scope_key(scope, scope_id)
        if key in self._usage:
            del self._usage[key]
        if key in self._api_windows:
            del self._api_windows[key]
        if key in self._token_windows:
            del self._token_windows[key]
        if key in self._daily_token_windows:
            del self._daily_token_windows[key]