"""Integration Event Publisher — Publishes lifecycle events to the EventEngine."""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from axiom.engine.event import EventEngine
from axiom.runtime.logging import RuntimeLogger


class IntegrationEventPublisher:
    """Publishes integration lifecycle events to the event bus."""

    def __init__(
        self,
        event_engine: Optional[EventEngine] = None,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.event_engine = event_engine
        self.logger = logger or RuntimeLogger()
        self._initialized = False

    async def initialize(self, event_engine: EventEngine) -> None:
        """Initialize with event engine reference."""
        self.event_engine = event_engine
        self._initialized = True

    async def publish(
        self,
        integration_id: str,
        event_type: str,
        payload: Dict[str, Any],
        state: str = "",
    ) -> None:
        """Publish an integration lifecycle event."""
        if not self._initialized or not self.event_engine:
            # Event engine not ready - queue or log
            self.logger.debug("integration_layer", f"Integration event (no engine): {integration_id}.{event_type}")
            return

        full_event_type = f"integration.{event_type}"

        try:
            # Publish to event engine
            await self.event_engine.publish(
                event_type=full_event_type,
                source="integration_layer",
                payload={
                    "integration_id": integration_id,
                    "stage": event_type,
                    "state": state,
                    **payload,
                },
            )
        except Exception as e:
            self.logger.warning("integration_layer", f"Failed to publish integration event: {e}")

    async def publish_batch(
        self,
        integration_id: str,
        events: List[Dict[str, Any]],
    ) -> None:
        """Publish multiple events at once."""
        for event_data in events:
            await self.publish(
                integration_id=integration_id,
                event_type=event_data.get("event_type", "unknown"),
                payload=event_data.get("payload", {}),
                state=event_data.get("state", ""),
            )


class IntegrationEventSubscriber:
    """Subscribes to integration events for downstream processing."""

    def __init__(
        self,
        event_engine: EventEngine,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.event_engine = event_engine
        self.logger = logger or RuntimeLogger()
        self._handlers: Dict[str, List[callable]] = {}

    def register_handler(self, event_type: str, handler: callable) -> None:
        """Register a handler for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def start(self) -> None:
        """Start listening for events."""
        for event_type in self._handlers:
            try:
                await self.event_engine.subscribe(event_type, self._handle_event)
            except Exception as e:
                self.logger.warning(f"Failed to subscribe to {event_type}: {e}")

    async def _handle_event(self, event: Any) -> None:
        """Route event to registered handlers."""
        event_type = getattr(event, "event_type", "") or event.get("event_type", "")
        payload = getattr(event, "payload", {}) or event.get("payload", {})

        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
            except Exception as e:
                self.logger.error(f"Handler for {event_type} failed: {e}")