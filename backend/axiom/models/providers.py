"""Provider Models — Pydantic models for provider configuration and state."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, SecretStr


class ProviderType(str, Enum):
    """Categories of providers."""

    DEVELOPMENT = "development"
    BUSINESS = "business"
    TRADING = "trading"
    PERSONAL = "personal"
    SYSTEM = "system"
    COMMUNICATION = "communication"


class AuthType(str, Enum):
    """Authentication methods supported."""

    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    SESSION = "session"
    NONE = "none"


class RateLimitConfig(BaseModel):
    """Rate limiting configuration for a provider."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_allowance: int = 10
    token_bucket_refill_rate: float = 1.0  # tokens per second


class RetryConfig(BaseModel):
    """Retry configuration with exponential backoff."""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_status: List[int] = [429, 500, 502, 503, 504]


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 3


class ProviderAuthConfig(BaseModel):
    """Authentication configuration for a provider."""

    type: AuthType = AuthType.NONE
    # For bearer_token / api_key
    token_env_var: Optional[str] = None
    token: Optional[SecretStr] = None
    # For basic_auth
    username_env_var: Optional[str] = None
    password_env_var: Optional[str] = None
    # For oauth2
    client_id_env_var: Optional[str] = None
    client_secret_env_var: Optional[str] = None
    token_url: Optional[str] = None
    scopes: List[str] = []
    # For session
    cookie_env_var: Optional[str] = None


class ProviderModel(BaseModel):
    """Provider definition model (loaded from YAML)."""

    id: str
    name: str
    type: ProviderType
    description: str
    version: str = "1.0.0"
    base_url: Optional[str] = None
    auth: ProviderAuthConfig = Field(default_factory=ProviderAuthConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    capabilities: List[str] = []
    # Tool-specific configuration
    config: Dict[str, Any] = {}
    # Health check
    health_check_endpoint: Optional[str] = None
    health_check_interval_seconds: int = 60
    # Metadata
    enabled: bool = True
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProviderToolDefinition(BaseModel):
    """Tool definition provided by a provider."""

    tool_id: str
    name: str
    description: str
    capability: str
    # JSON Schema for parameters
    input_schema: Dict[str, Any]
    # Permission requirements
    requires_approval: bool = False
    risk_level: str = "low"  # low, medium, high, critical
    # Rate limiting override
    rate_limit_override: Optional[RateLimitConfig] = None
    # Metadata
    tags: List[str] = []
    enabled: bool = True


class ProviderStatus(str, Enum):
    """Provider runtime status."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"
    NO_AUTH = "no_auth"


class ProviderHealth(BaseModel):
    """Provider health check result."""

    provider_id: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    latency_ms: float = 0.0
    last_check: datetime = Field(default_factory=datetime.utcnow)
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    error_message: Optional[str] = None
    details: Dict[str, Any] = {}


class ToolInvocationRequest(BaseModel):
    """Request to invoke a provider tool."""

    provider_id: str
    tool_id: str
    agent_id: str
    org_id: str
    parameters: Dict[str, Any]
    correlation_id: str
    idempotency_key: Optional[str] = None


class ToolInvocationResult(BaseModel):
    """Result of a tool invocation."""

    success: bool
    output: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: float = 0.0
    provider_id: str
    tool_id: str
    # For memory recording
    audit_data: Dict[str, Any] = {}
    # Rate limit info
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


class CapabilityMapping(BaseModel):
    """Maps a capability to provider tools."""

    capability: str
    provider_id: str
    tool_id: str
    priority: int = 0  # Higher = preferred
    org_ids: List[str] = []  # Empty = all orgs