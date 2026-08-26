"""Unified Integration Layer — Governed lifecycle for all external data connections.

The Integration Layer provides a complete, auditable lifecycle for every external
integration:

    CONNECT → AUTHENTICATE → FETCH → VALIDATE → NORMALIZE →
    DEDUPLICATE → CACHE → RATE_LIMIT → PERSIST → MONITOR →
    DISCONNECT → PUBLISH_EVENTS

This layer sits above the Provider Registry and adds:
- Unified connection/authentication flow with credential rotation
- Data validation and normalization pipelines
- Deduplication with configurable strategies
- Multi-tier caching (memory + persistent)
- Rate limiting with token bucket + respect for provider headers
- Persistence to domain databases
- Comprehensive monitoring and health metrics
- Event publishing for every lifecycle stage
- Graceful degradation and circuit breaking

No mock data in production paths. All integrations are REAL.
"""

from .integration_layer import IntegrationLayer
from .models import (
    IntegrationConfig,
    IntegrationState,
    ConnectionConfig,
    AuthConfig,
    FetchConfig,
    ValidationConfig,
    NormalizationConfig,
    DeduplicationConfig,
    CacheConfig,
    PersistenceConfig,
    MonitoringConfig,
)
from .lifecycle import IntegrationLifecycle
from .validation import DataValidator
from .normalization import DataNormalizer
from .deduplication import Deduplicator
from .cache import IntegrationCache
from .monitor import IntegrationMonitor
from .events import IntegrationEventPublisher

__all__ = [
    "IntegrationLayer",
    "IntegrationConfig",
    "IntegrationState",
    "ConnectionConfig",
    "AuthConfig",
    "FetchConfig",
    "ValidationConfig",
    "NormalizationConfig",
    "DeduplicationConfig",
    "CacheConfig",
    "PersistenceConfig",
    "MonitoringConfig",
    "IntegrationLifecycle",
    "DataValidator",
    "DataNormalizer",
    "Deduplicator",
    "IntegrationCache",
    "IntegrationMonitor",
    "IntegrationEventPublisher",
]