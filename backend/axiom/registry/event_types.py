"""Registry loader for event types, schemas, and subscriptions."""

from typing import Any, Dict, List, Optional

from axiom.config import events_path
from axiom.models.events import (
    EventBusDef,
    EventBusChannel,
    EventDeliveryConfig,
    EventSchema,
    EventTypeDef,
    EventTypeRegistry,
    SubscriptionDef,
)
from axiom.registry.loader import YAMLLoader


class EventRegistryLoader:
    """Loads event system definitions from YAML files."""

    def __init__(self) -> None:
        self._base = events_path()

    def load_bus_def(self) -> EventBusDef:
        """Load the master events/event-bus.yaml definition."""
        data = YAMLLoader.load_yaml(self._base / "event-bus.yaml")
        return EventBusDef(**data)

    def load_event_types(self) -> EventTypeRegistry:
        """Load events/event-types.yaml."""
        data = YAMLLoader.load_yaml(self._base / "event-types.yaml")
        return EventTypeRegistry(**data)

    def list_event_types(self) -> Dict[str, EventTypeDef]:
        """Return all registered event types as {name: def}."""
        return self.load_event_types().event_types

    def get_event_type(self, event_type: str) -> Optional[EventTypeDef]:
        """Get a single event type definition by name."""
        return self.list_event_types().get(event_type)

    def load_schema(self, event_type: str) -> Optional[EventSchema]:
        """Load the event schema from events/schemas/<name>.yaml.

        The schema file path comes from the EventTypeDef.event_schema field.
        """
        et = self.get_event_type(event_type)
        if et is None or et.event_schema is None:
            return None
        schema_path = self._base / et.event_schema
        if not schema_path.exists():
            return None
        data = YAMLLoader.load_yaml(schema_path)
        return EventSchema(**data)

    def load_subscriptions(self) -> List[SubscriptionDef]:
        """Load all subscription files from events/subscriptions/*.yaml."""
        subscriptions: List[SubscriptionDef] = []
        sub_dir = self._base / "subscriptions"
        if not sub_dir.exists():
            return subscriptions
        for path in sorted(sub_dir.glob("*.yaml")):
            data = YAMLLoader.load_yaml(path)
            subscriptions.append(SubscriptionDef(**data))
        return subscriptions

    def get_subscribers(self, event_type: str) -> List[str]:
        """Return all agent IDs that subscribe to a given event type."""
        # First check event-types.yaml for explicit subscriber list
        et = self.get_event_type(event_type)
        if et is not None:
            return et.subscribed_by

        # Then check subscription files
        for sub in self.load_subscriptions():
            if event_type in sub.subscribes_to:
                return [sub.agent]
        return []

    def get_emitters(self, event_type: str) -> List[str]:
        """Return all agent IDs that can emit a given event type."""
        et = self.get_event_type(event_type)
        if et is None:
            return []
        return et.emitted_by

    def get_channel_for_event(self, event_type: str) -> str:
        """Return the channel name for a given event type."""
        et = self.get_event_type(event_type)
        if et is None:
            return "organization"
        return et.channel

    def validate_payload(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Validate a payload against the event's schema.

        Checks required fields exist and types match.
        This is a lightweight validation — future versions may use full JSON Schema.
        """
        schema = self.load_schema(event_type)
        if schema is None:
            return True  # No schema means no validation

        for field_name, field_def in schema.payload.items():
            if field_def.required and field_name not in payload:
                return False
            if field_def.type == "integer" and field_name in payload:
                val = payload[field_name]
                if not isinstance(val, int):
                    return False
                if field_def.min is not None and val < field_def.min:
                    return False
                if field_def.max is not None and val > field_def.max:
                    return False
            if field_def.type == "string" and field_name in payload:
                if not isinstance(payload[field_name], str):
                    return False
        return True

    def list_event_channels(self) -> List[EventBusChannel]:
        """Return all event bus channels."""
        bus = self.load_bus_def()
        return bus.channels

    def get_delivery_config(self) -> EventDeliveryConfig:
        """Return the event bus delivery configuration."""
        bus = self.load_bus_def()
        return bus.delivery