"""Integration Lifecycle Manager — Orchestrates the complete integration lifecycle.

CONNECT → AUTHENTICATE → FETCH → VALIDATE → NORMALIZE → DEDUPLICATE →
CACHE → RATE_LIMIT → PERSIST → MONITOR → DISCONNECT → PUBLISH_EVENTS
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from axiom.engine.provider import Provider
from axiom.models.providers import (
    ToolInvocationRequest,
    ToolInvocationResult,
    ProviderStatus,
)
from axiom.runtime.logging import RuntimeLogger

from .models import (
    IntegrationConfig,
    IntegrationState,
    IntegrationStatus,
    IntegrationResult,
    ValidationMode,
    DeduplicationStrategy,
    CacheStrategy,
    PersistenceTarget,
)
from .validation import DataValidator
from .normalization import DataNormalizer
from .deduplication import Deduplicator
from .cache import IntegrationCache
from .monitor import IntegrationMonitor
from .events import IntegrationEventPublisher


class IntegrationLifecycle:
    """Orchestrates the complete integration lifecycle for a single integration."""

    def __init__(
        self,
        config: IntegrationConfig,
        logger: Optional[RuntimeLogger] = None,
        event_publisher: Optional[IntegrationEventPublisher] = None,
    ) -> None:
        self.config = config
        self.logger = logger or RuntimeLogger()
        self.event_publisher = event_publisher or IntegrationEventPublisher()

        # Status tracking
        self.status = IntegrationStatus(integration_id=config.integration_id)

        # Components (initialized lazily)
        self._provider: Optional[Provider] = None
        self._validator: Optional[DataValidator] = None
        self._normalizer: Optional[DataNormalizer] = None
        self._deduplicator: Optional[Deduplicator] = None
        self._cache: Optional[IntegrationCache] = None
        self._monitor: Optional[IntegrationMonitor] = None

        # State
        self._running = False
        self._fetch_task: Optional[asyncio.Task] = None

    # ── Lifecycle Entry Point ──────────────────────────────────────────────

    async def execute_full_cycle(self, correlation_id: Optional[str] = None) -> IntegrationResult:
        """Execute the complete integration lifecycle once.

        This is the main entry point for running an integration.
        It orchestrates all stages in order with full error handling.
        """
        corr_id = correlation_id or str(uuid.uuid4())
        result = IntegrationResult(
            integration_id=self.config.integration_id,
            success=False,
            state=IntegrationState.UNINITIALIZED,
            correlation_id=corr_id,
        )

        start_time = time.perf_counter()

        try:
            # Stage 1: CONNECT
            await self._transition(IntegrationState.CONNECTING)
            await self._publish_event("connecting", {"correlation_id": corr_id})
            await self._connect()
            await self._transition(IntegrationState.CONNECTED)
            await self._publish_event("connected", {"correlation_id": corr_id})

            # Stage 2: AUTHENTICATE
            await self._transition(IntegrationState.AUTHENTICATING)
            await self._publish_event("authenticating", {"correlation_id": corr_id})
            await self._authenticate()
            await self._transition(IntegrationState.AUTHENTICATED)
            await self._publish_event("authenticated", {"correlation_id": corr_id})

            # Stage 3: FETCH
            await self._transition(IntegrationState.FETCHING)
            await self._publish_event("fetching", {"correlation_id": corr_id})
            await self._fetch(result)
            await self._transition(IntegrationState.FETCHED)
            await self._publish_event("fetched", {
                "correlation_id": corr_id,
                "count": result.fetched_count,
            })

            # Stage 4: VALIDATE
            await self._transition(IntegrationState.VALIDATING)
            await self._publish_event("validating", {"correlation_id": corr_id})
            await self._validate(result)
            await self._transition(IntegrationState.VALIDATED)
            await self._publish_event("validated", {
                "correlation_id": corr_id,
                "passed": result.validated_count,
                "failed": result.fetched_count - result.validated_count,
            })

            # Stage 5: NORMALIZE
            await self._transition(IntegrationState.NORMALIZING)
            await self._publish_event("normalizing", {"correlation_id": corr_id})
            await self._normalize(result)
            await self._transition(IntegrationState.NORMALIZED)
            await self._publish_event("normalized", {
                "correlation_id": corr_id,
                "count": result.normalized_count,
            })

            # Stage 6: DEDUPLICATE
            await self._transition(IntegrationState.DEDUPLICATING)
            await self._publish_event("deduplicating", {"correlation_id": corr_id})
            await self._deduplicate(result)
            await self._transition(IntegrationState.DEDUPLICATED)
            await self._publish_event("deduplicated", {
                "correlation_id": corr_id,
                "count": result.deduplicated_count,
                "removed": result.fetched_count - result.deduplicated_count,
            })

            # Stage 7: CACHE
            await self._transition(IntegrationState.CACHING)
            await self._publish_event("caching", {"correlation_id": corr_id})
            await self._cache_data(result)
            await self._transition(IntegrationState.CACHED)
            await self._publish_event("cached", {
                "correlation_id": corr_id,
                "count": result.cached_count,
            })

            # Stage 8: RATE_LIMIT (checked during fetch, monitored here)
            await self._check_rate_limits(result)

            # Stage 9: PERSIST
            await self._transition(IntegrationState.PERSISTING)
            await self._publish_event("persisting", {"correlation_id": corr_id})
            await self._persist(result)
            await self._transition(IntegrationState.PERSISTED)
            await self._publish_event("persisted", {
                "correlation_id": corr_id,
                "count": result.persisted_count,
            })

            # Stage 10: MONITOR
            await self._transition(IntegrationState.MONITORING)
            await self._monitor_cycle(result)
            await self._publish_event("monitored", {
                "correlation_id": corr_id,
                "health_score": self.status.health_score,
            })

            # Stage 11: DISCONNECT (cleanup)
            await self._transition(IntegrationState.DISCONNECTING)
            await self._publish_event("disconnecting", {"correlation_id": corr_id})
            await self._disconnect()
            await self._transition(IntegrationState.DISCONNECTED)
            await self._publish_event("disconnected", {"correlation_id": corr_id})

            result.success = True
            result.state = IntegrationState.DISCONNECTED

        except Exception as e:
            self.logger.error("integration_lifecycle", f"Integration {self.config.integration_id} failed: {e}")
            self.status.last_error = str(e)
            self.status.last_error_at = datetime.utcnow()
            self.status.total_errors += 1
            self.status.consecutive_failures += 1
            self.status.consecutive_successes = 0
            await self._transition(IntegrationState.ERROR)
            await self._publish_event("error", {
                "correlation_id": corr_id,
                "error": str(e),
            })
            result.errors.append(str(e))
            result.state = IntegrationState.ERROR

        finally:
            result.total_duration_ms = (time.perf_counter() - start_time) * 1000
            result.completed_at = datetime.utcnow()
            self.status.consecutive_successes += 1 if result.success else 0
            self.status.consecutive_failures = 0 if result.success else self.status.consecutive_failures
            self._update_health_score()

        return result

    # ── Stage Implementations ──────────────────────────────────────────────

    async def _connect(self) -> None:
        """Establish connection to the external system."""
        # Get provider from registry (lazy import to avoid circular deps)
        from axiom.engine.provider_registry import get_provider_registry
        registry = get_provider_registry()
        self._provider = registry.get_provider(self.config.provider_id)

        if not self._provider:
            # Try to initialize provider for this org
            providers = await registry.initialize_providers(self.config.org_id)
            self._provider = registry.get_provider(self.config.provider_id)

        if not self._provider:
            raise RuntimeError(f"Provider {self.config.provider_id} not found or failed to initialize")

        # Initialize provider if needed
        if not self._provider.is_initialized:
            await self._provider.initialize()

        # Verify connection with health check
        health = await self._provider.health_check()
        if health.status != ProviderStatus.HEALTHY:
            raise RuntimeError(f"Provider health check failed: {health.error_message}")

        self.status.connected = True
        self.status.connection_latency_ms = health.latency_ms

    async def _authenticate(self) -> None:
        """Authenticate with the external system.

        For most providers, authentication is handled during provider initialization.
        This stage verifies authentication is valid and handles token refresh if needed.
        """
        if not self._provider:
            raise RuntimeError("Provider not connected")

        # Check if provider has valid auth
        health = await self._provider.health_check()
        if health.status == ProviderStatus.NO_AUTH:
            raise RuntimeError("Authentication failed - invalid or missing credentials")

        if health.status == ProviderStatus.UNHEALTHY:
            raise RuntimeError(f"Provider unhealthy: {health.error_message}")

        self.status.authenticated = True

        # If provider exposes token expiry, track it
        if hasattr(self._provider, "_token_expires_at"):
            self.status.token_expires_at = self._provider._token_expires_at

    async def _fetch(self, result: IntegrationResult) -> None:
        """Fetch data from the external system."""
        fetch_start = time.perf_counter()

        if not self._provider:
            raise RuntimeError("Provider not authenticated")

        # Determine what tool to use for fetching
        # This would be configured per integration
        tools = self._provider.get_tool_definitions()
        fetch_tool = None
        for tool in tools:
            if "fetch" in tool.tool_id.lower() or "get" in tool.tool_id.lower() or "list" in tool.tool_id.lower():
                fetch_tool = tool
                break

        if not fetch_tool:
            # Use first available read tool
            for tool in tools:
                if "read" in tool.capability:
                    fetch_tool = tool
                    break

        if not fetch_tool and tools:
            fetch_tool = tools[0]

        if not fetch_tool:
            raise RuntimeError("No fetch tool available on provider")

        # Execute fetch
        request = ToolInvocationRequest(
            provider_id=self.config.provider_id,
            tool_id=fetch_tool.tool_id,
            agent_id="integration_layer",
            org_id=self.config.org_id,
            parameters=self._build_fetch_params(),
            correlation_id=result.correlation_id,
        )

        response = await self._provider.execute_tool(request)

        result.fetch_duration_ms = (time.perf_counter() - fetch_start) * 1000

        if not response.success:
            raise RuntimeError(f"Fetch failed: {response.error}")

        # Extract data from response
        raw_data = response.output
        if isinstance(raw_data, dict):
            raw_data = [raw_data]
        elif not isinstance(raw_data, list):
            raw_data = [{"data": raw_data}]

        result.raw_data = raw_data
        result.fetched_count = len(raw_data)
        self.status.last_fetch_at = datetime.utcnow()
        self.status.last_fetch_duration_ms = result.fetch_duration_ms
        self.status.last_fetch_count = result.fetched_count
        self.status.last_fetch_error = None

    def _build_fetch_params(self) -> Dict[str, Any]:
        """Build fetch parameters from config."""
        params = {}

        # Add default filters
        params.update(self.config.fetch.default_filters)

        # Add incremental sync if configured
        if self.config.fetch.incremental_field and self.status.last_fetch_at:
            params[self.config.fetch.incremental_field] = self.status.last_fetch_at.isoformat()

        # Add pagination
        params["limit"] = self.config.fetch.page_size

        return params

    async def _validate(self, result: IntegrationResult) -> None:
        """Validate fetched data."""
        if not result.raw_data:
            result.validated_data = []
            return

        self._validator = self._validator or DataValidator(self.config.validation, self.logger)

        validated = []
        for item in result.raw_data:
            try:
                is_valid, error = self._validator.validate(item)
                if is_valid:
                    validated.append(item)
                    self.status.validation_passed += 1
                else:
                    self.status.validation_failed += 1
                    result.warnings.append(f"Validation failed: {error}")
                    if self.config.validation.mode == ValidationMode.STRICT:
                        raise ValueError(f"Validation failed: {error}")
            except Exception as e:
                self.status.validation_failed += 1
                result.warnings.append(f"Validation error: {e}")
                if self.config.validation.mode == ValidationMode.STRICT:
                    raise

        result.validated_data = validated
        result.validated_count = len(validated)
        self.status.last_validation_at = datetime.utcnow()

    async def _normalize(self, result: IntegrationResult) -> None:
        """Normalize validated data."""
        if not result.validated_data:
            result.normalized_data = []
            return

        norm_start = time.perf_counter()
        self._normalizer = self._normalizer or DataNormalizer(self.config.normalization, self.logger)

        normalized = []
        for item in result.validated_data:
            try:
                normalized_item = self._normalizer.normalize(item)
                normalized.append(normalized_item)
            except Exception as e:
                result.warnings.append(f"Normalization error: {e}")
                # In lenient mode, keep original
                if self.config.validation.mode != ValidationMode.STRICT:
                    normalized.append(item)

        result.normalization_duration_ms = (time.perf_counter() - norm_start) * 1000
        result.normalized_data = normalized
        result.normalized_count = len(normalized)
        self.status.last_normalization_at = datetime.utcnow()

    async def _deduplicate(self, result: IntegrationResult) -> None:
        """Deduplicate normalized data."""
        if not result.normalized_data:
            result.deduplicated_data = []
            return

        dedup_start = time.perf_counter()
        self._deduplicator = self._deduplicator or Deduplicator(self.config.deduplication, self.logger)

        original_count = len(result.normalized_data)
        result.deduplicated_data = self._deduplicator.deduplicate(result.normalized_data)
        result.deduplicated_count = len(result.deduplicated_data)

        duplicates_removed = original_count - result.deduplicated_count
        result.deduplication_duration_ms = (time.perf_counter() - dedup_start) * 1000
        self.status.duplicates_removed += duplicates_removed
        self.status.last_dedup_at = datetime.utcnow()

    async def _cache_data(self, result: IntegrationResult) -> None:
        """Cache deduplicated data."""
        if not result.deduplicated_data:
            result.cached_data = []
            return

        cache_start = time.perf_counter()
        self._cache = self._cache or IntegrationCache(self.config.cache, self.logger)

        cached = []
        for item in result.deduplicated_data:
            cache_key = self._build_cache_key(item)
            # Check if already cached
            existing = await self._cache.get(cache_key)
            if existing:
                self.status.cache_hits += 1
                cached.append(existing)
            else:
                self.status.cache_misses += 1
                await self._cache.set(cache_key, item)
                cached.append(item)

        result.cache_duration_ms = (time.perf_counter() - cache_start) * 1000
        result.cached_data = cached
        result.cached_count = len(cached)
        self.status.cache_size = await self._cache.size()

    def _build_cache_key(self, item: Dict[str, Any]) -> str:
        """Build cache key from item."""
        if self.config.cache.key_fields:
            key_parts = [str(item.get(f, "")) for f in self.config.cache.key_fields]
        else:
            # Use all fields
            key_parts = [f"{k}:{v}" for k, v in sorted(item.items())]

        return f"{self.config.cache.key_prefix}:{':'.join(key_parts)}"

    async def _check_rate_limits(self, result: IntegrationResult) -> None:
        """Check and record rate limit status."""
        if not self._provider:
            return

        health = await self._provider.health_check()
        # Rate limit info would be in health.details if available
        if health.details.get("rate_limited"):
            self.status.rate_limited = True
            self.status.rate_limit_reset_at = health.details.get("rate_limit_reset")
            result.warnings.append("Rate limited")
        else:
            self.status.rate_limited = False

    async def _persist(self, result: IntegrationResult) -> None:
        """Persist data to configured targets."""
        if not result.deduplicated_data:
            result.persisted_data = []
            return

        persist_start = time.perf_counter()

        for target in self.config.persistence.targets:
            try:
                if target == PersistenceTarget.DOMAIN_DATABASE:
                    await self._persist_to_domain_db(result)
                elif target == PersistenceTarget.EVENT_STORE:
                    await self._persist_to_event_store(result)
                elif target == PersistenceTarget.TIME_SERIES:
                    await self._persist_to_time_series(result)
                elif target == PersistenceTarget.SEARCH_INDEX:
                    await self._persist_to_search_index(result)
                elif target == PersistenceTarget.BLOB_STORAGE:
                    await self._persist_to_blob_storage(result)
            except Exception as e:
                result.errors.append(f"Persistence to {target.value} failed: {e}")
                self.status.persist_errors += 1
                if self.config.validation.mode == ValidationMode.STRICT:
                    raise

        result.persistence_duration_ms = (time.perf_counter() - persist_start) * 1000
        result.persisted_data = result.deduplicated_data  # Track what was persisted
        result.persisted_count = len(result.deduplicated_data)
        self.status.last_persist_at = datetime.utcnow()
        self.status.persisted_count += result.persisted_count

    async def _persist_to_domain_db(self, result: IntegrationResult) -> None:
        """Persist to domain database."""
        # This integrates with the domain databases (Phase 2)
        # For now, log that persistence would happen
        self.logger.info(
            "integration_lifecycle",
            f"Would persist {len(result.deduplicated_data)} records to domain database "
            f"for integration {self.config.integration_id}"
        )

    async def _persist_to_event_store(self, result: IntegrationResult) -> None:
        """Persist to event store."""
        self.logger.info(
            "integration_lifecycle",
            f"Would persist {len(result.deduplicated_data)} events to event store "
            f"for integration {self.config.integration_id}"
        )

    async def _persist_to_time_series(self, result: IntegrationResult) -> None:
        """Persist to time series database."""
        self.logger.info(
            "integration_lifecycle",
            f"Would persist {len(result.deduplicated_data)} time series points "
            f"for integration {self.config.integration_id}"
        )

    async def _persist_to_search_index(self, result: IntegrationResult) -> None:
        """Persist to search index."""
        self.logger.info(
            "integration_lifecycle",
            f"Would index {len(result.deduplicated_data)} documents "
            f"for integration {self.config.integration_id}"
        )

    async def _persist_to_blob_storage(self, result: IntegrationResult) -> None:
        """Persist to blob storage."""
        self.logger.info(
            "integration_lifecycle",
            f"Would store {len(result.deduplicated_data)} blobs "
            f"for integration {self.config.integration_id}"
        )

    async def _monitor_cycle(self, result: IntegrationResult) -> None:
        """Record monitoring metrics for this cycle."""
        self._monitor = self._monitor or IntegrationMonitor(self.config.monitoring, self.logger)

        metrics = {
            "fetch_duration_ms": result.fetch_duration_ms,
            "validation_duration_ms": result.validation_duration_ms,
            "normalization_duration_ms": result.normalization_duration_ms,
            "deduplication_duration_ms": result.deduplication_duration_ms,
            "cache_duration_ms": result.cache_duration_ms,
            "persistence_duration_ms": result.persistence_duration_ms,
            "total_duration_ms": result.total_duration_ms,
            "fetched_count": result.fetched_count,
            "validated_count": result.validated_count,
            "normalized_count": result.normalized_count,
            "deduplicated_count": result.deduplicated_count,
            "cached_count": result.cached_count,
            "persisted_count": result.persisted_count,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
        }

        await self._monitor.record_cycle(metrics)
        self._update_health_score()

    def _update_health_score(self) -> None:
        """Calculate health score based on recent performance."""
        total = self.status.consecutive_successes + self.status.consecutive_failures
        if total == 0:
            self.status.health_score = 1.0
        else:
            success_rate = self.status.consecutive_successes / total
            # Factor in error rate
            if self.status.total_errors > 0:
                error_rate = self.status.total_errors / max(total, 1)
                self.status.health_score = max(0.0, success_rate - error_rate)
            else:
                self.status.health_score = success_rate

    async def _disconnect(self) -> None:
        """Gracefully disconnect from the external system."""
        if self._provider:
            await self._provider.shutdown()
            self._provider = None

        self.status.connected = False
        self.status.authenticated = False

    async def _transition(self, new_state: IntegrationState) -> None:
        """Transition to a new state."""
        old_state = self.status.state
        self.status.state = new_state
        self.status.last_transition = datetime.utcnow()

        self.logger.debug("integration_lifecycle", f"Integration {self.config.integration_id}: {old_state.value} → {new_state.value}")

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish a lifecycle event."""
        await self.event_publisher.publish(
            integration_id=self.config.integration_id,
            event_type=event_type,
            payload=payload,
            state=self.status.state,
        )

    # ── Scheduled Execution ────────────────────────────────────────────────

    async def start_scheduled(self) -> None:
        """Start scheduled execution based on cron schedule."""
        if not self.config.schedule:
            return

        self._running = True

        # Parse cron and schedule
        # For now, simple interval - full cron in Phase 10
        import croniter
        cron = croniter.croniter(self.config.schedule, datetime.utcnow())

        while self._running:
            next_run = cron.get_next(datetime)
            wait_seconds = (next_run - datetime.utcnow()).total_seconds()

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            if not self._running:
                break

            try:
                await self.execute_full_cycle()
            except Exception as e:
                self.logger.error("integration_lifecycle", f"Scheduled integration cycle failed: {e}")

    async def stop_scheduled(self) -> None:
        """Stop scheduled execution."""
        self._running = False
        if self._fetch_task:
            self._fetch_task.cancel()
            try:
                await self._fetch_task
            except asyncio.CancelledError:
                pass

    def get_status(self) -> IntegrationStatus:
        """Get current integration status."""
        return self.status