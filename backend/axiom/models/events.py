"""Pydantic models for the event system.

Includes both the configuration models (event bus, event types, schemas,
subscriptions) and the runtime Event type that flows through the engine.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Configuration models (from YAML files) ───────────────────────────────

class EventSchemaField(BaseModel):
    """Field definition inside an event schema."""
    type: str = "string"
    required: bool = False
    description: str = ""
    min: Optional[int] = None
    max: Optional[int] = None
    items: Optional[str] = None


class EventSchema(BaseModel):
    """Schema definition from events/schemas/<name>.yaml."""
    name: str
    version: str = "1.0"
    payload: Dict[str, EventSchemaField] = {}


class EventBusChannel(BaseModel):
    """Channel definition from event-bus.yaml."""
    name: str
    description: str = ""
    scope: str = "org"


class EventDeliveryConfig(BaseModel):
    """Delivery configuration from event-bus.yaml."""
    type: str = "publish-subscribe"
    guarantees: str = "at-least-once"
    ordering: str = "per-channel"
    persistence: str = ""


class EventBusDef(BaseModel):
    """Top-level event bus definition from events/event-bus.yaml."""
    version: str = "3.0"
    name: str = ""
    description: str = ""
    channels: List[EventBusChannel] = []
    delivery: EventDeliveryConfig = EventDeliveryConfig()
    rules: List[str] = []


class EventTypeDef(BaseModel):
    """Event type definition from events/event-types.yaml."""
    description: str = ""
    channel: str = "organization"
    emitted_by: List[str] = []
    subscribed_by: List[str] = []
    event_schema: Optional[str] = Field(None, alias="schema")
    example_payload: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)


class EventTypeRegistry(BaseModel):
    event_types: Dict[str, EventTypeDef] = {}


class SubscriptionDef(BaseModel):
    """Subscription definition from events/subscriptions/<agent>.yaml."""
    agent: str
    subscribes_to: List[str] = []


# ── Runtime Event model ──────────────────────────────────────────────────

class Event(BaseModel):
    """An event flowing through the system at runtime.

    Every action generates at least one event.  Events carry lightweight
    payloads with context references, not large data blobs.
    """
    event_id: str
    event_type: str
    source: str
    channel: str
    payload: Dict[str, Any] = {}
    timestamp: datetime
    schema_path: Optional[str] = Field(None, alias="schema_ref")
    correlation_id: Optional[str] = None
    retry_count: int = 0