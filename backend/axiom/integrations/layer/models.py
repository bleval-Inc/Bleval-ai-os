"""Models for the Unified Integration Layer.

Defines configuration and state models for the complete integration lifecycle:
CONNECT → AUTHENTICATE → FETCH → VALIDATE → NORMALIZE → DEDUPLICATE →
CACHE → RATE_LIMIT → PERSIST → MONITOR → DISCONNECT → PUBLISH_EVENTS
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from pydantic import BaseModel, Field


class IntegrationState(str, Enum):
    """Lifecycle states for an integration."""

    UNINITIALIZED = "uninitialized"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    FETCHING = "fetching"
    FETCHED = "fetched"
    VALIDATING = "validating"
    VALIDATED = "validated"
    NORMALIZING = "normalizing"
    NORMALIZED = "normalized"
    DEDUPLICATING = "deduplicating"
    DEDUPLICATED = "deduplicated"
    CACHING = "caching"
    CACHED = "cached"
    PERSISTING = "persisting"
    PERSISTED = "persisted"
    MONITORING = "monitoring"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    DISABLED = "disabled"


class ConnectionProtocol(str, Enum):
    """Supported connection protocols."""

    HTTPS = "https"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    TCP = "tcp"
    LOCAL_PIPE = "local_pipe"
    MT4_MT5 = "mt4_mt5"  # MetaTrader terminal connection


class AuthStrategy(str, Enum):
    """Authentication strategies."""

    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    SESSION_COOKIE = "session_cookie"
    MUTUAL_TLS = "mutual_tls"
    API_KEY_QUERY = "api_key_query"
    SIGNATURE_V4 = "signature_v4"
    CUSTOM = "custom"


class ValidationMode(str, Enum):
    """Data validation modes."""

    STRICT = "strict"  # Fail on any validation error
    LENIENT = "lenient"  # Log warnings, continue
    SCHEMA_ONLY = "schema_only"  # Only validate schema, not business rules
    NONE = "none"  # Skip validation (not recommended for production)


class DeduplicationStrategy(str, Enum):
    """Deduplication strategies."""

    EXACT_MATCH = "exact_match"  # Exact field match
    FUZZY_MATCH = "fuzzy_match"  # Fuzzy matching on key fields
    SEMANTIC_HASH = "semantic_hash"  # Hash of normalized content
    COMPOSITE_KEY = "composite_key"  # Multi-field composite key
    TIME_WINDOW = "time_window"  # Within time window + key match
    CUSTOM = "custom"  # Custom function


class CacheStrategy(str, Enum):
    """Cache strategies."""

    MEMORY_ONLY = "memory_only"
    PERSISTENT_ONLY = "persistent_only"
    TIERED = "tiered"  # Memory (L1) + Persistent (L2)
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    READ_THROUGH = "read_through"


class PersistenceTarget(str, Enum):
    """Persistence targets."""

    DOMAIN_DATABASE = "domain_database"  # BLEVAL/Market/Research/Comms DB
    EVENT_STORE = "event_store"  # Immutable event log
    BLOB_STORAGE = "blob_storage"  # Large objects (files, media)
    TIME_SERIES = "time_series"  # Metrics, ticks, rates
    SEARCH_INDEX = "search_index"  # Full-text search


class RateLimitScope(str, Enum):
    """Rate limit scope."""

    PROVIDER = "provider"  # Per provider
    TOOL = "tool"  # Per tool
    ORG = "org"  # Per organization
    GLOBAL = "global"  # Global across all


@dataclass
class ConnectionConfig:
    """Connection configuration."""

    protocol: ConnectionProtocol = ConnectionProtocol.HTTPS
    base_url: Optional[str] = None
    timeout_seconds: float = 30.0
    max_connections: int = 10
    keepalive_seconds: float = 60.0
    retry_on_connect: bool = True
    connect_retry_attempts: int = 3
    connect_retry_delay: float = 1.0
    # WebSocket specific
    ws_ping_interval: float = 30.0
    ws_ping_timeout: float = 10.0
    # Custom connection parameters
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthConfig:
    """Authentication configuration."""

    strategy: AuthStrategy = AuthStrategy.BEARER_TOKEN
    # Credential references (env vars or secret manager keys)
    credentials: Dict[str, str] = field(default_factory=dict)
    # OAuth2 specific
    token_url: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    client_id: Optional[str] = None
    # Token management
    token_refresh_threshold_seconds: int = 300  # Refresh 5 min before expiry
    auto_refresh: bool = True
    # Custom auth
    custom_auth_handler: "Optional[Callable]" = None


@dataclass
class FetchConfig:
    """Fetch configuration."""

    # Pagination
    page_size: int = 100
    max_pages: int = 1000
    pagination_strategy: str = "cursor"  # cursor, offset, page
    # Filtering
    default_filters: Dict[str, Any] = field(default_factory=dict)
    incremental_field: Optional[str] = None  # For incremental sync
    # Rate limiting awareness
    respect_retry_after: bool = True
    respect_rate_limit_headers: bool = True
    # Concurrency
    concurrent_requests: int = 1
    # Request customization
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationConfig:
    """Validation configuration."""

    mode: ValidationMode = ValidationMode.STRICT
    schema: Optional[Dict[str, Any]] = None  # JSON Schema
    required_fields: List[str] = field(default_factory=list)
    # Business rule validators
    business_rules: "List[Callable[[Dict], bool]]" = field(default_factory=list)
    business_rule_names: List[str] = field(default_factory=list)
    # Type coercion
    coerce_types: bool = True
    # Null handling
    allow_null_required: bool = False
    # Custom validators
    custom_validators: "List[Callable[[Dict], tuple[bool, str]]]" = field(default_factory=list)


@dataclass
class NormalizationConfig:
    """Normalization configuration."""

    # Field mapping: source_field -> target_field
    field_mapping: Dict[str, str] = field(default_factory=dict)
    # Type transformations
    type_transformations: Dict[str, str] = field(default_factory=dict)  # field -> target_type
    # Value transformations
    value_transformations: Dict[str, "Callable[[Any], Any]"] = field(default_factory=dict)
    # Standardization
    standardize_timestamps: bool = True
    timestamp_format: str = "iso8601"  # iso8601, unix, unix_ms, rfc3339
    standardize_currency: bool = True
    base_currency: str = "USD"
    standardize_identifiers: bool = True  # UUIDs, emails, phones
    # Custom normalizers
    custom_normalizers: "List[Callable[[Dict], Dict]]" = field(default_factory=list)


@dataclass
class DeduplicationConfig:
    """Deduplication configuration."""

    strategy: DeduplicationStrategy = DeduplicationStrategy.EXACT_MATCH
    key_fields: List[str] = field(default_factory=list)
    # For fuzzy matching
    fuzzy_threshold: float = 0.85
    fuzzy_fields: List[str] = field(default_factory=list)
    # For time window
    time_window_seconds: int = 3600
    time_field: str = "timestamp"
    # For composite key
    composite_fields: List[str] = field(default_factory=list)
    # Custom deduplication function
    custom_dedup_fn: "Optional[Callable[[List[Dict]], List[Dict]]]" = None
    # Keep strategy
    keep_strategy: str = "first"  # first, last, max_field, min_field
    keep_field: Optional[str] = None  # For max/min


@dataclass
class CacheConfig:
    """Cache configuration."""

    strategy: CacheStrategy = CacheStrategy.TIERED
    # Memory cache (L1)
    memory_max_size: int = 10000
    memory_ttl_seconds: int = 300
    # Persistent cache (L2)
    persistent_path: Optional[str] = None
    persistent_max_size_mb: int = 1024
    persistent_ttl_seconds: int = 86400
    # Cache keys
    key_fields: List[str] = field(default_factory=list)
    key_prefix: str = "integration"
    # Invalidation
    invalidate_on_write: bool = True
    invalidate_on_error: bool = False


@dataclass
class PersistenceConfig:
    """Persistence configuration."""

    targets: List[PersistenceTarget] = field(default_factory=lambda: [PersistenceTarget.DOMAIN_DATABASE])
    # Domain database
    domain_db_path: Optional[str] = None
    table_name: Optional[str] = None
    # Batch settings
    batch_size: int = 100
    flush_interval_seconds: int = 60
    # Conflict resolution
    conflict_strategy: str = "upsert"  # upsert, ignore, replace, error
    primary_key: Optional[str] = None
    # Event store
    event_store_path: Optional[str] = None
    # Time series
    time_series_path: Optional[str] = None
    time_series_retention_days: int = 365


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""

    enabled: bool = True
    # Metrics collection
    collect_latency: bool = True
    collect_throughput: bool = True
    collect_error_rates: bool = True
    collect_data_quality: bool = True
    # Health checks
    health_check_interval_seconds: int = 60
    health_check_timeout_seconds: int = 10
    # Alerting
    alert_on_failure: bool = True
    alert_on_degraded: bool = True
    alert_on_rate_limited: bool = True
    alert_threshold_error_rate: float = 0.05
    alert_threshold_latency_p99_ms: float = 5000
    # Custom metrics
    custom_metrics: "List[Callable[[Any], Dict[str, float]]]" = field(default_factory=list)


class IntegrationConfig(BaseModel):
    """Complete integration configuration."""

    integration_id: str
    name: str
    description: str = ""
    provider_id: str  # References ProviderRegistry
    org_id: str
    # Lifecycle configs
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    fetch: FetchConfig = Field(default_factory=FetchConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    # Runtime
    enabled: bool = True
    schedule: Optional[str] = None  # Cron expression for scheduled fetches
    # Metadata
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class IntegrationStatus(BaseModel):
    """Current integration status."""

    integration_id: str
    state: IntegrationState = IntegrationState.UNINITIALIZED
    last_transition: datetime = Field(default_factory=datetime.utcnow)
    # Connection
    connected: bool = False
    connection_latency_ms: float = 0.0
    # Authentication
    authenticated: bool = False
    token_expires_at: Optional[datetime] = None
    # Fetch
    last_fetch_at: Optional[datetime] = None
    last_fetch_duration_ms: float = 0.0
    last_fetch_count: int = 0
    last_fetch_error: Optional[str] = None
    # Validation
    last_validation_at: Optional[datetime] = None
    validation_passed: int = 0
    validation_failed: int = 0
    # Normalization
    last_normalization_at: Optional[datetime] = None
    # Deduplication
    last_dedup_at: Optional[datetime] = None
    duplicates_removed: int = 0
    # Cache
    cache_hits: int = 0
    cache_misses: int = 0
    cache_size: int = 0
    # Persistence
    last_persist_at: Optional[datetime] = None
    persisted_count: int = 0
    persist_errors: int = 0
    # Rate limiting
    rate_limited: bool = False
    rate_limit_reset_at: Optional[datetime] = None
    # Monitoring
    health_score: float = 1.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    # Error tracking
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    total_errors: int = 0


class IntegrationResult(BaseModel):
    """Result of an integration execution."""

    integration_id: str
    success: bool
    state: IntegrationState
    # Data
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)
    validated_data: List[Dict[str, Any]] = Field(default_factory=list)
    normalized_data: List[Dict[str, Any]] = Field(default_factory=list)
    deduplicated_data: List[Dict[str, Any]] = Field(default_factory=list)
    cached_data: List[Dict[str, Any]] = Field(default_factory=list)
    persisted_data: List[Dict[str, Any]] = Field(default_factory=list)
    # Metrics
    fetch_duration_ms: float = 0.0
    validation_duration_ms: float = 0.0
    normalization_duration_ms: float = 0.0
    deduplication_duration_ms: float = 0.0
    cache_duration_ms: float = 0.0
    persistence_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    # Counts
    fetched_count: int = 0
    validated_count: int = 0
    normalized_count: int = 0
    deduplicated_count: int = 0
    cached_count: int = 0
    persisted_count: int = 0
    # Errors
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    # Metadata
    correlation_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None