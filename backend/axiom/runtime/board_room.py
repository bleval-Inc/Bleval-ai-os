"""Board Room System — where executives meet, share KPIs, make decisions,
and track action items.

The Board Room is an asynchronous decision-making system using the event bus.
It is NOT real-time meetings — it is a structured coordination layer.

Meeting cadence:
  - Daily briefings (each morning)
  - Weekly executive meetings (every Monday)
  - Monthly reviews (first of month)
  - Quarterly strategic planning (quarter start)

Each executive automatically publishes KPI snapshots, agenda items, and
completed work before board meetings. The Board Room consolidates these
into structured minutes with decisions and action items.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from axiom.models.executive import (
    BoardRoomActionItem,
    BoardRoomAgenda,
    BoardRoomDecision,
    BoardRoomMeeting,
    MeetingType,
    ActionItemStatus,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Board Room
# ═══════════════════════════════════════════════════════════════════════════════


class BoardRoom:
    """Asynchronous board room for executive coordination.

    Manages:
      - Meeting scheduling and lifecycle
      - Agenda items from all executives
      - KPI snapshot collection
      - Decision recording
      - Action item tracking
      - Meeting minutes generation
      - Persistent board memory

    Architecture:
      Founder
        ↓
      BoardRoom ←→ Jenson, Valta Prime, Yamako
        ↓
      Memory (board decisions, minutes, action items)
    """

    def __init__(self, runtime: Any = None) -> None:
        self._runtime = runtime

        # Meeting state
        self._meetings: Dict[str, BoardRoomMeeting] = {}
        self._pending_agendas: Dict[str, BoardRoomAgenda] = {}
        self._action_items: Dict[str, BoardRoomActionItem] = {}

        # KPI tracking
        self._latest_kpis: Dict[str, Dict[str, float]] = {}
        self._kpi_history: List[Dict[str, Any]] = []

        # Background processing
        self._task: Optional[asyncio.Task] = None
        self._running = False

        # Scheduling
        self._last_daily: Optional[datetime] = None
        self._last_weekly: Optional[datetime] = None
        self._last_monthly: Optional[datetime] = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the board room background processor."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.info("board_room", "Board Room started")

    async def stop(self) -> None:
        """Stop the board room."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        """Background loop: check for scheduled meetings and process them."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                today_str = now.strftime("%Y-%m-%d")

                # Daily briefing: runs once per day when local hour >= 7
                local_hour = datetime.now().hour
                if local_hour >= 7 and local_hour <= 10:
                    if self._last_daily is None or self._last_daily.strftime("%Y-%m-%d") != today_str:
                        await self._run_daily_briefing()
                        self._last_daily = now

                # Weekly executive meeting: Monday morning
                if now.weekday() == 0 and local_hour >= 9 and local_hour <= 11:
                    if self._last_weekly is None or self._last_weekly.strftime("%Y-%m-%d") != today_str:
                        await self._run_weekly_meeting()
                        self._last_weekly = now

                # Monthly review: 1st of month, morning
                if now.day == 1 and local_hour >= 9 and local_hour <= 11:
                    month_str = now.strftime("%Y-%m")
                    if self._last_monthly is None or self._last_monthly.strftime("%Y-%m") != month_str:
                        await self._run_monthly_review()
                        self._last_monthly = now

                await asyncio.sleep(300)  # Check every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(300)

    # ── Meeting Lifecycle ────────────────────────────────────────────────────

    async def schedule_meeting(
        self,
        meeting_type: MeetingType,
        called_by: str = "system",
        title: str = "",
        attendees: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> str:
        """Schedule a new board meeting.

        Returns the meeting ID.
        """
        meeting_id = str(uuid.uuid4())

        meeting = BoardRoomMeeting(
            meeting_id=meeting_id,
            meeting_type=meeting_type,
            title=title or f"{meeting_type.value.replace('_', ' ').title()}",
            called_by=called_by,
            attendees=attendees or [],
            scheduled_at=scheduled_at or datetime.now(timezone.utc),
        )

        self._meetings[meeting_id] = meeting

        # Publish event if event engine is available
        await self._publish_event(
            "board-room-scheduled",
            {"meeting_id": meeting_id, "meeting_type": meeting_type.value},
        )

        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.info(
                "board_room",
                f"Meeting scheduled: {meeting_id} ({meeting_type.value})",
            )

        return meeting_id

    async def start_meeting(self, meeting_id: str) -> bool:
        """Start a scheduled meeting."""
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        meeting.started_at = datetime.now(timezone.utc)
        meeting.status = "in_progress"

        await self._publish_event(
            "board-room-started",
            {"meeting_id": meeting_id, "meeting_type": meeting.meeting_type.value},
        )

        return True

    async def complete_meeting(self, meeting_id: str) -> Optional[BoardRoomMeeting]:
        """Complete a meeting and generate minutes."""
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return None

        meeting.completed_at = datetime.now(timezone.utc)
        meeting.status = "completed"

        # Generate minutes
        meeting.minutes = self._generate_minutes(meeting)

        # Write to board memory
        await self._write_meeting_to_memory(meeting)

        await self._publish_event(
            "board-room-completed",
            {
                "meeting_id": meeting_id,
                "meeting_type": meeting.meeting_type.value,
                "decisions": len(meeting.decisions),
                "action_items": len(meeting.action_items),
            },
        )

        return meeting

    # ── Agenda Management ────────────────────────────────────────────────────

    def submit_agenda_item(
        self,
        submitted_by: str,
        title: str,
        description: str = "",
        supporting_data: Optional[Dict[str, Any]] = None,
        meeting_id: str = "",
        priority: int = 0,
    ) -> str:
        """Submit an agenda item for the next board meeting."""
        agenda_id = str(uuid.uuid4())

        item = BoardRoomAgenda(
            agenda_id=agenda_id,
            meeting_id=meeting_id,
            submitted_by=submitted_by,
            title=title,
            description=description,
            supporting_data=supporting_data or {},
            priority=priority,
        )

        if meeting_id:
            # Add to specific meeting
            meeting = self._meetings.get(meeting_id)
            if meeting:
                meeting.agenda.append(item)
        else:
            # Add to pending agenda
            self._pending_agendas[agenda_id] = item

        return agenda_id

    def get_pending_agenda(self) -> List[BoardRoomAgenda]:
        """Get all pending agenda items (not yet assigned to a meeting)."""
        return sorted(
            list(self._pending_agendas.values()),
            key=lambda a: (-a.priority, a.submitted_at),
        )

    def move_agenda_to_meeting(
        self, agenda_id: str, meeting_id: str
    ) -> bool:
        """Move a pending agenda item to a specific meeting."""
        item = self._pending_agendas.pop(agenda_id, None)
        if not item:
            return False
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            self._pending_agendas[agenda_id] = item
            return False
        item.meeting_id = meeting_id
        meeting.agenda.append(item)
        return True

    # ── KPI Publishing ───────────────────────────────────────────────────────

    def publish_kpi_snapshot(
        self, exec_id: str, kpis: Dict[str, float]
    ) -> None:
        """An executive publishes their KPI snapshot."""
        self._latest_kpis[exec_id] = kpis
        self._kpi_history.append({
            "exec_id": exec_id,
            "kpis": kpis,
            "timestamp": datetime.now(timezone.utc),
        })

        # Attach to active meeting if any
        active_meeting = self._get_active_meeting()
        if active_meeting:
            active_meeting.kpi_snapshots[exec_id] = kpis

    def get_latest_kpis(self) -> Dict[str, Dict[str, float]]:
        """Get the latest KPI snapshot from all executives."""
        return dict(self._latest_kpis)

    # ── Decision Making ──────────────────────────────────────────────────────

    async def make_decision(
        self,
        meeting_id: str,
        title: str,
        description: str,
        proposed_by: str,
        voted_by: Optional[List[str]] = None,
        approved: bool = False,
    ) -> BoardRoomDecision:
        """Record a board decision."""
        decision = BoardRoomDecision(
            decision_id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            title=title,
            description=description,
            proposed_by=proposed_by,
            voted_by=voted_by or [],
            votes_for=len(voted_by or []),
            approved=approved,
        )

        meeting = self._meetings.get(meeting_id)
        if meeting:
            meeting.decisions.append(decision)

        await self._publish_event(
            "board-room-decision",
            {
                "decision_id": decision.decision_id,
                "meeting_id": meeting_id,
                "title": title,
                "approved": approved,
                "proposed_by": proposed_by,
            },
        )

        return decision

    # ── Action Items ─────────────────────────────────────────────────────────

    def create_action_item(
        self,
        meeting_id: str,
        title: str,
        assigned_to: str,
        description: str = "",
        priority: str = "normal",
        deadline: Optional[datetime] = None,
        depends_on: Optional[List[str]] = None,
    ) -> str:
        """Create an action item from a board meeting.

        Returns the action item ID.
        """
        item_id = str(uuid.uuid4())

        item = BoardRoomActionItem(
            item_id=item_id,
            meeting_id=meeting_id,
            title=title,
            description=description,
            assigned_to=assigned_to,
            priority=priority,
            deadline=deadline,
            status=ActionItemStatus.OPEN,
            depends_on=depends_on or [],
        )

        self._action_items[item_id] = item

        # Link to meeting
        meeting = self._meetings.get(meeting_id)
        if meeting:
            meeting.action_items.append(item)

        return item_id

    def complete_action_item(
        self, item_id: str, notes: str = ""
    ) -> bool:
        """Mark an action item as completed."""
        item = self._action_items.get(item_id)
        if not item:
            return False
        item.status = ActionItemStatus.COMPLETED
        item.completed_at = datetime.now(timezone.utc)
        item.notes = notes
        return True

    def get_open_action_items(
        self, exec_id: Optional[str] = None
    ) -> List[BoardRoomActionItem]:
        """Get all open action items, optionally filtered by assignee."""
        items = [
            item for item in self._action_items.values()
            if item.status in (ActionItemStatus.OPEN, ActionItemStatus.IN_PROGRESS, ActionItemStatus.BLOCKED)
        ]
        if exec_id:
            items = [i for i in items if i.assigned_to == exec_id]
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    def get_overdue_action_items(self) -> List[BoardRoomActionItem]:
        """Get action items past their deadline."""
        now = datetime.now(timezone.utc)
        return [
            item for item in self._action_items.values()
            if item.deadline and item.deadline < now
            and item.status in (ActionItemStatus.OPEN, ActionItemStatus.IN_PROGRESS, ActionItemStatus.BLOCKED)
        ]

    # ── Board Room Meetings ──────────────────────────────────────────────────

    async def _run_daily_briefing(self) -> str:
        """Run the daily briefing — collect KPI snapshots, top priorities."""
        meeting_id = await self.schedule_meeting(
            meeting_type=MeetingType.DAILY_BRIEFING,
            called_by="system",
            title="Daily Executive Briefing",
            attendees=["jenson", "valta_prime", "yamako"],
        )
        await self.start_meeting(meeting_id)

        # Add top-of-mind agenda items from each executive
        for exec_id in ("jenson", "valta_prime", "yamako"):
            exec_kpis = self._latest_kpis.get(exec_id, {})
            self.submit_agenda_item(
                submitted_by=exec_id,
                title=f"{exec_id.capitalize()} Daily Briefing",
                description=f"KPI snapshot: {exec_kpis}",
                meeting_id=meeting_id,
            )

        await self.complete_meeting(meeting_id)
        return meeting_id

    async def _run_weekly_meeting(self) -> str:
        """Run the weekly executive meeting."""
        meeting_id = await self.schedule_meeting(
            meeting_type=MeetingType.WEEKLY_EXECUTIVE,
            called_by="system",
            title="Weekly Executive Meeting",
            attendees=["jenson", "valta_prime", "yamako"],
        )
        await self.start_meeting(meeting_id)

        # Collect pending agenda items
        for item in list(self._pending_agendas.values()):
            self.move_agenda_to_meeting(item.agenda_id, meeting_id)

        # Add standard weekly agenda items
        for exec_id in ("jenson", "valta_prime", "yamako"):
            kpis = self._latest_kpis.get(exec_id, {})
            open_items = len(self.get_open_action_items(exec_id))
            self.submit_agenda_item(
                submitted_by=exec_id,
                title=f"{exec_id.capitalize()} — Weekly Review",
                description=f"KPIs: {len(kpis)} tracked\nOpen items: {open_items}",
                meeting_id=meeting_id,
                priority=1,
            )

        await self.complete_meeting(meeting_id)
        return meeting_id

    async def _run_monthly_review(self) -> str:
        """Run the monthly review."""
        meeting_id = await self.schedule_meeting(
            meeting_type=MeetingType.MONTHLY_REVIEW,
            called_by="system",
            title="Monthly Executive Review",
            attendees=["jenson", "valta_prime", "yamako"],
        )
        await self.start_meeting(meeting_id)

        for exec_id in ("jenson", "valta_prime", "yamako"):
            kpis = self._latest_kpis.get(exec_id, {})
            self.submit_agenda_item(
                submitted_by=exec_id,
                title=f"{exec_id.capitalize()} — Monthly Performance",
                description=f"Full KPI review: {kpis}",
                meeting_id=meeting_id,
                priority=2,
            )

        await self.complete_meeting(meeting_id)
        return meeting_id

    # ── Minutes & Memory ─────────────────────────────────────────────────────

    def _generate_minutes(self, meeting: BoardRoomMeeting) -> str:
        """Generate structured meeting minutes."""
        lines = [
            f"# Board Meeting Minutes",
            f"",
            f"**Meeting:** {meeting.title}",
            f"**Type:** {meeting.meeting_type.value}",
            f"**Date:** {(meeting.started_at or meeting.scheduled_at).isoformat() if (meeting.started_at or meeting.scheduled_at) else 'N/A'}",
            f"**Status:** {meeting.status}",
            f"**Called by:** {meeting.called_by}",
            f"**Attendees:** {', '.join(meeting.attendees) if meeting.attendees else 'None'}",
            f"",
            f"---",
            f"",
            f"## Agenda",
        ]

        for i, item in enumerate(meeting.agenda, 1):
            lines.extend([
                f"",
                f"### {i}. {item.title}",
                f"**Submitted by:** {item.submitted_by}",
                f"**Status:** {item.status}",
                f"",
                f"{item.description}",
            ])

        if meeting.kpi_snapshots:
            lines.extend([
                f"",
                f"---",
                f"## KPI Snapshots",
            ])
            for exec_id, kpis in meeting.kpi_snapshots.items():
                lines.extend([
                    f"",
                    f"### {exec_id.capitalize()}",
                ])
                for kpi_name, kpi_value in kpis.items():
                    lines.append(f"- {kpi_name}: {kpi_value}")

        if meeting.decisions:
            lines.extend([
                f"",
                f"---",
                f"## Decisions",
            ])
            for decision in meeting.decisions:
                lines.extend([
                    f"",
                    f"### {decision.title}",
                    f"**Proposed by:** {decision.proposed_by}",
                    f"**Approved:** {'Yes' if decision.approved else 'No'}",
                    f"**Votes:** {decision.votes_for} for, {decision.votes_against} against",
                    f"",
                    f"{decision.description}",
                ])

        if meeting.action_items:
            lines.extend([
                f"",
                f"---",
                f"## Action Items",
            ])
            for item in meeting.action_items:
                lines.extend([
                    f"",
                    f"- **{item.title}** — assigned to {item.assigned_to}",
                    f"  Priority: {item.priority}",
                    f"  Deadline: {item.deadline.isoformat() if item.deadline else 'N/A'}",
                    f"  Status: {item.status.value}",
                ])

        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by AXIOM Board Room at {datetime.now(timezone.utc).isoformat()}*")

        return "\n".join(lines)

    async def _write_meeting_to_memory(
        self, meeting: BoardRoomMeeting
    ) -> None:
        """Persist meeting minutes to board memory."""
        if not self._runtime or not hasattr(self._runtime, "memory"):
            return
        try:
            memory_engine = self._runtime.memory
            # Use write_agent_memory on a special "board" agent
            memory_engine.write_agent_memory(
                agent_id="system",
                key=f"board_meeting_{meeting.meeting_id[:8]}",
                content=meeting.minutes,
            )
        except Exception:
            pass

    # ── Queries ──────────────────────────────────────────────────────────────

    def _get_active_meeting(self) -> Optional[BoardRoomMeeting]:
        """Get the currently active meeting, if any."""
        for meeting in self._meetings.values():
            if meeting.status == "in_progress":
                return meeting
        return None

    def get_meeting(self, meeting_id: str) -> Optional[BoardRoomMeeting]:
        """Get a specific meeting record."""
        return self._meetings.get(meeting_id)

    def list_meetings(
        self, limit: int = 10, meeting_type: Optional[MeetingType] = None
    ) -> List[BoardRoomMeeting]:
        """List recent meetings, optionally filtered by type."""
        meetings = sorted(
            self._meetings.values(),
            key=lambda m: m.scheduled_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        if meeting_type:
            meetings = [m for m in meetings if m.meeting_type == meeting_type]
        return meetings[:limit]

    def get_kpi_history(
        self, exec_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get historical KPI data, optionally filtered by executive."""
        history = self._kpi_history
        if exec_id:
            history = [h for h in history if h["exec_id"] == exec_id]
        return history[-50:]  # Last 50 entries

    def get_dashboard(self) -> Dict[str, Any]:
        """Return a complete board room dashboard snapshot."""
        return {
            "total_meetings": len(self._meetings),
            "active_meeting": self._get_active_meeting().meeting_id if self._get_active_meeting() else None,
            "pending_agenda_items": len(self._pending_agendas),
            "open_action_items": len(self.get_open_action_items()),
            "overdue_action_items": len(self.get_overdue_action_items()),
            "latest_kpis": self._latest_kpis,
            "last_daily": self._last_daily.isoformat() if self._last_daily else None,
            "last_weekly": self._last_weekly.isoformat() if self._last_weekly else None,
            "last_monthly": self._last_monthly.isoformat() if self._last_monthly else None,
        }

    async def _publish_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> None:
        """Publish a board room event."""
        if not self._runtime or not hasattr(self._runtime, "event"):
            return
        try:
            await self._runtime.event.publish(
                event_type=event_type,
                source="board_room",
                payload=payload,
            )
        except Exception:
            pass