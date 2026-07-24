"""Event Engine — async publish-subscribe event bus.

Provides:
- Channel-based pub/sub with asyncio queues
- Event validation against schemas
- At-least-once delivery with retry logic
- Dead-letter queue for failed events (bounded)
- File-based event persistence for replay
- Replay capability

Architecture:
  publish() -> channel queue -> background processor -> subscriber callbacks
                              -> persistent JSON log
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from axiom.config import settings
from axiom.models.events import Event, EventBusDef
from axiom.registry.event_types import EventRegistryLoader

# Type alias for event subscriber callbacks
EventCallback = Callable[[Event], Awaitable[None]]


class EventEngine:
    """Asynchronous event bus with persistence, retry, and replay."""

    MAX_DLQ_SIZE = 10_000

    def __init__(self) -> None:
        self._registry = EventRegistryLoader()
        self._bus_def: Optional[EventBusDef] = None

        # Per-channel asyncio queues
        self._queues: Dict[str, "asyncio.Queue[Event]"] = {}
        self._subscribers: Dict[str, List[EventCallback]] = {}

        # Retry state
        self._retry_queue: "asyncio.Queue[Event]" = None  # type: ignore[assignment]
        self._dead_letter_queue: List[Event] = []
        self._max_retries: int = 3

        # Background task references
        self._processor_task: Optional[Any] = None
        self._retry_task: Optional[Any] = None
        self._running: bool = False

    @property
    def bus_def(self) -> EventBusDef:
        if self._bus_def is None:
            self._bus_def = self._registry.load_bus_def()
        return self._bus_def

    @property
    def queues(self) -> Dict[str, "asyncio.Queue[Event]"]:
        return self._queues

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Initialise queues for all channels and start background processors."""
        import asyncio

        self._running = True
        for channel in self.bus_def.channels:
            if channel.name not in self._queues:
                self._queues[channel.name] = asyncio.Queue()
                self._subscribers[channel.name] = []

        self._retry_queue = asyncio.Queue()
        self._processor_task = asyncio.create_task(self._process_events())
        self._retry_task = asyncio.create_task(self._process_retries())

    async def stop(self) -> None:
        """Gracefully shut down the event engine."""
        self._running = False
        if self._processor_task is not None:
            self._processor_task.cancel()
            self._processor_task = None
        if self._retry_task is not None:
            self._retry_task.cancel()
            self._retry_task = None

    # ── Publishing ───────────────────────────────────────────────────────

    async def publish(
        self,
        event_type: str,
        source: str,
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish an event to the appropriate channel.

        Raises RuntimeError if called before start().
        Raises ValueError for unknown event types or channels.
        Returns True if the event was enqueued.
        """
        if not self._running:
            raise RuntimeError(
                "EventEngine.publish() called before start(). "
                "Ensure the event engine is started via engine.start() "
                "before publishing events."
            )

        et_def = self._registry.get_event_type(event_type)
        if et_def is None:
            raise ValueError(f"Unknown event type: {event_type}")

        raw_channel = et_def.channel
        channel = self._resolve_channel(raw_channel)

        # Validate payload against schema
        if payload is not None:
            if not self._registry.validate_payload(event_type, payload):
                raise ValueError(f"Payload validation failed for event: {event_type}")

        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            channel=channel,
            payload=payload or {},
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
        )

        # Persist to file
        self._persist_event(event)

        # Enqueue for processing
        if channel in self._queues:
            await self._queues[channel].put(event)
            return True
        else:
            raise ValueError(f"Unknown channel: {channel}. Available channels: {list(self._queues.keys())}")

    # ── Subscription ─────────────────────────────────────────────────────

    def subscribe(self, channel: str, callback: EventCallback) -> None:
        """Register a callback on a channel.

        The callback will be invoked for every event published to that channel.
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)

    def subscribe_to_event(self, event_type: str, callback: EventCallback) -> None:
        """Register a callback for a specific event type.

        The engine resolves the event type's channel and subscribes there.
        The callback should check the event_type before processing.
        """
        et_def = self._registry.get_event_type(event_type)
        if et_def is None:
            raise ValueError(f"Unknown event type: {event_type}")
        channel = self._resolve_channel(et_def.channel)
        self.subscribe(channel, callback)

    def subscribe_agent(self, agent_id: str, callback: EventCallback) -> None:
        """Register all subscriptions for a given agent based on their
        subscription definitions."""
        subs = self._registry.load_subscriptions()
        for sub in subs:
            if sub.agent == agent_id:
                for event_type in sub.subscribes_to:
                    self.subscribe_to_event(event_type, callback)

    # ── Public API wrappers ──────────────────────────────────────────────

    def list_event_types(self) -> Dict[str, Any]:
        """Return all registered event types (public API)."""
        return self._registry.list_event_types()

    def get_event_type(self, event_type: str) -> Optional[Any]:
        """Get a specific event type definition (public API)."""
        return self._registry.get_event_type(event_type)

    def list_event_channels(self) -> List[str]:
        """Return all event bus channels (public API)."""
        return [ch.name for ch in self.bus_def.channels]

    def get_delivery_config(self, event_type: str) -> Optional[Any]:
        """Get delivery config for an event type (public API)."""
        return self._registry.get_delivery_config(event_type)

    # ── Event Log / Replay / DLQ ─────────────────────────────────────────

    def get_event_log(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Read persisted events from disk, optionally filtered by type."""
        events: List[Event] = []
        log_dir = settings.event_log_dir
        if not log_dir.exists():
            return events

        for month_dir in sorted(log_dir.iterdir(), reverse=True):
            if not month_dir.is_dir():
                continue
            for f in sorted(month_dir.glob("*.json"), reverse=True):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        ev = Event(**data)
                        if event_type is None or ev.event_type == event_type:
                            events.append(ev)
                            if len(events) >= limit:
                                return events
                except (json.JSONDecodeError, Exception):
                    continue
        return events

    def replay_events(self, event_type: str, since: Optional[datetime] = None) -> List[Event]:
        """Re-read events from disk for replay processing.

        Returns events that match the given type, optionally since a timestamp.
        """
        events = self.get_event_log(event_type, limit=1000)
        if since is not None:
            events = [e for e in events if e.timestamp >= since]
        return events

    def get_dead_letter_queue(self) -> List[Event]:
        """Return events that exceeded max retries."""
        return list(self._dead_letter_queue)

    # ── Internal processing ──────────────────────────────────────────────

    async def _process_events(self) -> None:
        """Background task: read from all channel queues and dispatch to subscribers."""
        import asyncio

        while self._running:
            for channel_name, queue in self._queues.items():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.5)
                    await self._dispatch(event, channel_name)
                except asyncio.TimeoutError:
                    continue
                except Exception as exc:
                    # Enqueue for retry with per-event backoff
                    event.retry_count += 1
                    if event.retry_count <= self._max_retries:
                        await self._retry_queue.put(event)
                    else:
                        self._add_to_dlq(event)

    async def _dispatch(self, event: Event, channel: str) -> None:
        """Dispatch an event to all subscribers on the channel."""
        callbacks = self._subscribers.get(channel, [])
        for callback in callbacks:
            try:
                await callback(event)
            except Exception:
                raise  # Let the caller handle retry

    async def _process_retries(self) -> None:
        """Background task: retry failed events with exponential backoff.

        Each event tracks its own retry count so backoff is per-event, not
        shared across all events.

        Backoff formula: 2^retry_count seconds, capped at 30s.
        """
        import asyncio

        while self._running:
            try:
                event = await asyncio.wait_for(self._retry_queue.get(), timeout=5.0)
                et_def = self._registry.get_event_type(event.event_type)
                if et_def is None:
                    self._add_to_dlq(event)
                    continue
                channel = self._resolve_channel(et_def.channel)

                # Exponential backoff: wait 2^retry_count seconds before retry
                backoff = min(2.0 ** event.retry_count, 30.0)
                if backoff > 0:
                    await asyncio.sleep(backoff)

                try:
                    await self._dispatch(event, channel)
                except Exception:
                    if event.retry_count < self._max_retries:
                        event.retry_count += 1
                        await self._retry_queue.put(event)
                    else:
                        self._add_to_dlq(event)
            except asyncio.TimeoutError:
                continue

    def _add_to_dlq(self, event: Event) -> None:
        """Add an event to the dead-letter queue, enforcing the capacity limit."""
        if len(self._dead_letter_queue) >= self.MAX_DLQ_SIZE:
            # Evict oldest (FIFO eviction)
            self._dead_letter_queue.pop(0)
        self._dead_letter_queue.append(event)

    def _persist_event(self, event: Event) -> None:
        """Write an event to the file-based event log."""
        month_str = event.timestamp.strftime("%Y-%m")
        log_dir = settings.event_log_dir / month_str
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"{event.event_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            f.write(event.model_dump_json())

    def _resolve_channel(self, event_channel: str) -> str:
        """Resolve channel names like 'department.sales' -> 'department'."""
        return event_channel.split(".")[0]