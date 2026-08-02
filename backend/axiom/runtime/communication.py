"""Executive Communication Coordinator — manages who speaks, who waits,
urgency, Founder availability, and interruption priority.

Three executives communicate through this coordinator:
  - Jenson (Bleval Inc)
  - Valta Prime (House of Valta)
  - Yamako (Personal Operations)

The Coordinator ensures:
  1. Never allow all executives to speak simultaneously
  2. One speaker at a time (unless emergency override)
  3. Emergency situations override normal priority
  4. Founder availability determines delivery method
  5. Conversation context is maintained
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Enums & Data Models
# ═══════════════════════════════════════════════════════════════════════════════


class UrgencyLevel(str, Enum):
    """How urgently an executive needs Founder attention."""

    SILENT = "silent"            # Background only, no Founder interruption
    LOW = "low"                  # Briefing mode, queued for next Founder check-in
    NORMAL = "normal"            # Conversational, queued in order
    HIGH = "high"                # Important — interrupt if Founder is available
    CRITICAL = "critical"        # Emergency — override all, immediate interrupt
    ESCALATION = "escalation"    # Founder-defined POI / emergency escalation rules


class SpeakerState(str, Enum):
    """Current state of an executive in the communication system."""

    IDLE = "idle"
    SPEAKING = "speaking"
    WAITING = "waiting"
    BRIEFING = "briefing"
    EMERGENCY = "emergency"


class FounderAvailability(str, Enum):
    """What the Founder is currently doing — determines delivery mechanism."""

    AVAILABLE = "available"          # Can receive messages directly
    IN_MEETING = "in_meeting"        # Queue non-critical, interrupt for emergency
    IN_TRADE = "in_trade"            # Only emergency interruptions
    SLEEPING = "sleeping"            # Queue everything for morning (unless emergency)
    TRAINING = "training"            # Brief only critical
    STUDYING = "studying"            # Brief only critical
    DO_NOT_DISTURB = "do_not_disturb"
    UNKNOWN = "unknown"


@dataclass
class ExecutiveMessage:
    """A structured message from one executive to the Founder or another executive."""

    message_id: str
    sender: str                     # Executive ID
    recipient: str                  # "founder" or another executive ID
    urgency: UrgencyLevel
    subject: str
    body: str
    context: Dict[str, Any] = field(default_factory=dict)
    requires_response: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delivered: bool = False
    read: bool = False
    response: Optional[str] = None


@dataclass
class SpeakerQueueEntry:
    """An executive waiting to speak."""

    executive_id: str
    urgency: UrgencyLevel
    message: ExecutiveMessage
    queued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════════════════
# Communication Coordinator
# ═══════════════════════════════════════════════════════════════════════════════


class CommunicationCoordinator:
    """Central coordinator for all executive communication.

    Manages:
      - Who is speaking at any given time
      - Who is waiting to speak
      - Urgency levels and priority
      - Founder availability and routing
      - Emergency overrides
      - Message queue and delivery tracking

    Architecture:
      Founder
        ↑↓
      CommunicationCoordinator
        ↑↓       ↑↓          ↑↓
      Jenson   ValtaPrime   Yamako
    """

    def __init__(self, runtime: Any = None) -> None:
        self._runtime = runtime

        # Speaker state
        self._active_speaker: Optional[str] = None
        self._speaker_states: Dict[str, SpeakerState] = {
            "jenson": SpeakerState.IDLE,
            "valta_prime": SpeakerState.IDLE,
            "yamako": SpeakerState.IDLE,
        }

        # Queues
        self._speaker_queue: List[SpeakerQueueEntry] = []
        self._message_history: List[ExecutiveMessage] = []
        self._pending_responses: Dict[str, ExecutiveMessage] = {}

        # Founder state
        self._founder_availability: FounderAvailability = FounderAvailability.UNKNOWN
        self._founder_currently_addressed: Optional[str] = None  # Which exec Founder is talking to

        # Emergency lock
        self._emergency_active: bool = False
        self._emergency_executive: Optional[str] = None
        self._emergency_timestamp: Optional[datetime] = None

        # Config
        self._max_queue_size = 50
        self._max_history = 200

    # ── Founder Availability ──────────────────────────────────────────────────

    def set_founder_availability(
        self, availability: FounderAvailability
    ) -> None:
        """Update the Founder's current availability state.

        This determines how messages are delivered:
          AVAILABLE → direct delivery
          IN_MEETING → queue non-critical, interrupt for emergency
          IN_TRADE → only emergency interruptions
          SLEEPING → queue everything
          etc.
        """
        old = self._founder_availability
        self._founder_availability = availability

        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.info(
                "communication",
                f"Founder availability changed: {old.value} → {availability.value}",
            )

    def get_founder_availability(self) -> FounderAvailability:
        return self._founder_availability

    def founder_is_addressing(self, executive_id: str) -> None:
        """Record that the Founder is currently addressing a specific executive."""
        self._founder_currently_addressed = executive_id

    def founder_stopped_addressing(self) -> None:
        """Record that the Founder stopped addressing the current executive."""
        self._founder_currently_addressed = None
        self._process_queue()

    # ── Speaking State ────────────────────────────────────────────────────────

    def get_active_speaker(self) -> Optional[str]:
        """Return the executive currently speaking, if any."""
        return self._active_speaker

    def is_executive_speaking(self, executive_id: str) -> bool:
        """Check if a specific executive is currently speaking."""
        return self._active_speaker == executive_id

    def get_speaker_state(self, executive_id: str) -> SpeakerState:
        """Get the current state of an executive in the communication system."""
        return self._speaker_states.get(executive_id, SpeakerState.IDLE)

    def all_speakers_idle(self) -> bool:
        """Check if no executive is currently speaking."""
        return self._active_speaker is None

    # ── Message Sending ───────────────────────────────────────────────────────

    async def send(
        self,
        sender: str,
        recipient: str,
        urgency: UrgencyLevel,
        subject: str,
        body: str,
        context: Optional[Dict[str, Any]] = None,
        requires_response: bool = False,
    ) -> ExecutiveMessage:
        """Send a message from an executive to the Founder or another executive.

        The coordinator will:
          1. Check if the sender can speak now
          2. Check Founder availability
          3. Queue or deliver based on urgency and availability
          4. Return the message with delivery status
        """
        import uuid

        message = ExecutiveMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            recipient=recipient,
            urgency=urgency,
            subject=subject,
            body=body,
            context=context or {},
            requires_response=requires_response,
        )

        # Record the message
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]

        # Handle based on urgency
        if urgency in (UrgencyLevel.CRITICAL, UrgencyLevel.ESCALATION):
            await self._handle_emergency(message)
        elif urgency == UrgencyLevel.HIGH:
            await self._handle_high_urgency(message)
        else:
            await self._handle_normal(message)

        return message

    async def _handle_emergency(self, message: ExecutiveMessage) -> None:
        """Handle an emergency/critical message — immediate interrupt."""
        self._emergency_active = True
        self._emergency_executive = message.sender
        self._emergency_timestamp = datetime.now(timezone.utc)

        # Override current speaker
        if self._active_speaker and self._active_speaker != message.sender:
            # Record the interrupted speaker
            interrupted = self._active_speaker
            self._speaker_states[interrupted] = SpeakerState.WAITING

        self._active_speaker = message.sender
        self._speaker_states[message.sender] = SpeakerState.EMERGENCY

        message.delivered = True

        # Log the emergency
        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.workflow_event(
                instance_id=f"emergency-{message.message_id}",
                event="executive_emergency",
                details={
                    "sender": message.sender,
                    "urgency": message.urgency.value,
                    "subject": message.subject,
                    "recipient": message.recipient,
                },
            )

        # If the message requires a response, track it
        if message.requires_response:
            self._pending_responses[message.message_id] = message

    async def _handle_high_urgency(self, message: ExecutiveMessage) -> None:
        """Handle a high urgency message — interrupt if Founder is available."""
        if self._founder_availability in (
            FounderAvailability.AVAILABLE,
            FounderAvailability.UNKNOWN,
        ):
            # Can deliver directly
            if self._active_speaker is None:
                self._active_speaker = message.sender
                self._speaker_states[message.sender] = SpeakerState.SPEAKING
                message.delivered = True
            else:
                # Queue if someone else is speaking (unless emergency overrides)
                self._queue_message(message)
        elif self._founder_availability == FounderAvailability.IN_MEETING:
            # Queue for next break
            self._queue_message(message)
        else:
            # Queue for later
            self._queue_message(message)

    async def _handle_normal(self, message: ExecutiveMessage) -> None:
        """Handle a normal/low urgency message — queue or brief."""
        if message.urgency == UrgencyLevel.SILENT:
            # Silent messages go directly to background memory
            message.delivered = True
            message.read = True
            self._archive_silent_message(message)
            return

        self._queue_message(message)

    def _queue_message(self, message: ExecutiveMessage) -> None:
        """Queue a message for delivery when the Founder is available."""
        self._speaker_queue.append(SpeakerQueueEntry(
            executive_id=message.sender,
            urgency=message.urgency,
            message=message,
        ))

        # Sort queue by urgency (emergency first, then high, etc.)
        urgency_order = {
            UrgencyLevel.ESCALATION: 0,
            UrgencyLevel.CRITICAL: 1,
            UrgencyLevel.HIGH: 2,
            UrgencyLevel.NORMAL: 3,
            UrgencyLevel.LOW: 4,
            UrgencyLevel.SILENT: 5,
        }
        self._speaker_queue.sort(
            key=lambda e: (urgency_order.get(e.urgency, 99), e.queued_at)
        )

        self._speaker_states[message.sender] = SpeakerState.WAITING

        # Enforce max queue size
        if len(self._speaker_queue) > self._max_queue_size:
            # Drop lowest priority oldest messages
            self._speaker_queue = self._speaker_queue[:self._max_queue_size]

    def _archive_silent_message(self, message: ExecutiveMessage) -> None:
        """Archive a silent message to executive memory."""
        if not self._runtime or not hasattr(self._runtime, "memory"):
            return
        try:
            self._runtime.memory.write_agent_memory(
                agent_id=message.sender,
                key=f"silent-msg-{message.message_id[:8]}",
                content=(
                    f"# Silent Communication\n\n"
                    f"**Subject:** {message.subject}\n\n"
                    f"{message.body}\n\n"
                    f"**Timestamp:** {message.timestamp.isoformat()}"
                ),
            )
        except Exception:
            pass

    # ── Queue Processing ──────────────────────────────────────────────────────

    def _process_queue(self) -> None:
        """Process the speaker queue — deliver the next waiting message.

        Called when:
          - The current speaker finishes
          - The Founder becomes available
          - An emergency clears
        """
        if not self._speaker_queue:
            return

        # Check if emergency is still active
        if self._emergency_active:
            return

        # Don't interrupt if someone is already speaking
        if self._active_speaker is not None:
            return

        # Don't interrupt if Founder is busy with someone
        if self._founder_currently_addressed is not None:
            return

        # Check Founder availability
        if self._founder_availability in (
            FounderAvailability.SLEEPING,
            FounderAvailability.IN_TRADE,
            FounderAvailability.TRAINING,
            FounderAvailability.STUDYING,
            FounderAvailability.DO_NOT_DISTURB,
        ):
            # Only deliver high+ urgency
            if all(
                e.urgency not in (UrgencyLevel.HIGH, UrgencyLevel.CRITICAL, UrgencyLevel.ESCALATION)
                for e in self._speaker_queue
            ):
                return

        # Deliver the next message
        entry = self._speaker_queue.pop(0)
        entry.message.delivered = True
        self._active_speaker = entry.executive_id
        self._speaker_states[entry.executive_id] = SpeakerState.SPEAKING

    # ── Speaker Release ──────────────────────────────────────────────────────

    async def release_speaker(self, executive_id: str) -> None:
        """Release a speaker — called when an executive finishes speaking."""
        if self._active_speaker == executive_id:
            self._active_speaker = None
            self._speaker_states[executive_id] = SpeakerState.IDLE

            # Check if this was an emergency
            if (
                self._emergency_active
                and self._emergency_executive == executive_id
            ):
                self._emergency_active = False
                self._emergency_executive = None
                self._emergency_timestamp = None

            # Process the queue for the next speaker
            self._process_queue()

    async def acknowledge_response(
        self, message_id: str, response: str
    ) -> bool:
        """Record a Founder's response to a message."""
        if message_id in self._pending_responses:
            msg = self._pending_responses[message_id]
            msg.response = response
            msg.read = True

            # Release the speaker if they were waiting for this
            await self.release_speaker(msg.sender)
            return True
        return False

    # ── Emergency Clear ────────────────────────────────────────────────────────

    async def clear_emergency(self) -> None:
        """Clear the emergency state and resume normal operations."""
        if self._emergency_active:
            emergency_exec = self._emergency_executive
            self._emergency_active = False
            self._emergency_executive = None
            self._emergency_timestamp = None

            if emergency_exec:
                self._speaker_states[emergency_exec] = SpeakerState.IDLE

            self._process_queue()

            if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
                self._runtime.logger.info(
                    "communication",
                    f"Emergency cleared for {emergency_exec}, resuming normal operations",
                )

    # ── Query Methods ─────────────────────────────────────────────────────────

    def get_speaker_queue(
        self, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return the current speaker queue."""
        return [
            {
                "executive": entry.executive_id,
                "urgency": entry.urgency.value,
                "subject": entry.message.subject,
                "queued_at": entry.queued_at.isoformat(),
            }
            for entry in self._speaker_queue[:limit]
        ]

    def get_message_history(
        self, limit: int = 20, sender: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return recent message history, optionally filtered by sender."""
        messages = self._message_history
        if sender:
            messages = [m for m in messages if m.sender == sender]
        return [
            {
                "message_id": m.message_id,
                "sender": m.sender,
                "recipient": m.recipient,
                "urgency": m.urgency.value,
                "subject": m.subject,
                "delivered": m.delivered,
                "read": m.read,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in messages[-limit:]
        ]

    def get_pending_messages(
        self, executive_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages awaiting Founder response."""
        pending = []
        for mid, msg in self._pending_responses.items():
            if executive_id is None or msg.sender == executive_id:
                pending.append({
                    "message_id": mid,
                    "sender": msg.sender,
                    "subject": msg.subject,
                    "urgency": msg.urgency.value,
                    "timestamp": msg.timestamp.isoformat(),
                })
        return pending

    def get_dashboard(self) -> Dict[str, Any]:
        """Return a complete communication dashboard snapshot."""
        return {
            "active_speaker": self._active_speaker,
            "speaker_states": {
                k: v.value for k, v in self._speaker_states.items()
            },
            "founder_availability": self._founder_availability.value,
            "founder_addressing": self._founder_currently_addressed,
            "emergency_active": self._emergency_active,
            "emergency_executive": self._emergency_executive,
            "queue_length": len(self._speaker_queue),
            "pending_responses": len(self._pending_responses),
            "total_messages_sent": len(self._message_history),
        }

    # ── Founder Request ────────────────────────────────────────────────────────

    def request_founder_attention(
        self, executive_id: str, reason: str
    ) -> str:
        """An executive requests the Founder's attention.

        Returns a formatted string the executive can display.
        """
        return (
            f"⚠️  Founder Request — {executive_id.capitalize()} requires your attention.\n"
            f"Reason: {reason}\n\n"
            f"Say /talk to {executive_id} to enter their workstation."
        )

    # ── Conflict Resolution ────────────────────────────────────────────────────

    def resolve_speaker_conflict(self) -> Optional[str]:
        """If multiple executives are trying to speak simultaneously,
        resolve the conflict based on urgency and priority.

        Priority order: Valta Prime (trading critical) > Jenson (business critical)
        > Yamako (personal critical)

        Returns the executive_id that should speak next.
        """
        if self._emergency_active:
            return self._emergency_executive

        # Get all waiting executives with their highest urgency message
        waiting: Dict[str, UrgencyLevel] = {}
        for entry in self._speaker_queue:
            exec_id = entry.executive_id
            if exec_id not in waiting or entry.urgency.value < waiting[exec_id].value:
                waiting[exec_id] = entry.urgency

        if not waiting:
            return None

        # Priority matrix: urgency first, then domain priority for ties
        urgency_order = {
            UrgencyLevel.ESCALATION: 0,
            UrgencyLevel.CRITICAL: 1,
            UrgencyLevel.HIGH: 2,
            UrgencyLevel.NORMAL: 3,
            UrgencyLevel.LOW: 4,
            UrgencyLevel.SILENT: 5,
        }

        # Domain priority for equal urgency
        domain_priority = {
            "valta_prime": 0,   # Trading = highest priority
            "jenson": 1,         # Business = second
            "yamako": 2,         # Personal = third
        }

        def sort_key(item: Tuple[str, UrgencyLevel]) -> Tuple[int, int, str]:
            exec_id, urgency = item
            return (
                urgency_order.get(urgency, 99),
                domain_priority.get(exec_id, 99),
                exec_id,
            )

        sorted_waiting = sorted(waiting.items(), key=sort_key)
        return sorted_waiting[0][0] if sorted_waiting else None