"""Schedule Coordinator — Yamako's engine for managing the Founder's complete day.

Yamako coordinates the Founder's schedule across:
  - Business (Jenson — client work, meetings, operations)
  - Trading (Valta Prime — market hours, POI monitoring windows)
  - Learning (structured study, reading, courses)
  - Training (physical exercise, routines)
  - Personal (meals, rest, family, errands)
  - Sleep (wind-down, lights-out, 8-hour target)

The coordinator automatically constructs the day around fixed anchors
(market opens, standing meetings, routine blocks) and fills remaining
windows with flexible work.

Schedule Priority (highest to lowest):
  1. Sleep & Recovery (non-negotiable)
  2. Training (body before mind)
  3. Trading / Market Windows
  4. Learning
  5. Client Meetings & Deliverables
  6. Business Operations
  7. Personal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Enums & Data Models
# ═══════════════════════════════════════════════════════════════════════════════


class BlockCategory(str, Enum):
    SLEEP = "sleep"
    TRAINING = "training"
    TRADING = "trading"
    LEARNING = "learning"
    CLIENT_WORK = "client_work"
    BUSINESS_OPS = "business_ops"
    MEETING = "meeting"
    PERSONAL = "personal"
    MEAL = "meal"
    TRAVEL = "travel"
    FLEXIBLE = "flexible"


class BlockPriority(int, Enum):
    CRITICAL = 0      # Cannot be moved
    HIGH = 1          # Move only if absolutely necessary
    MEDIUM = 2        # Can be rescheduled within same day
    LOW = 3           # Flexible — fills remaining time
    FILLER = 4        # Optional — dropped if day is full


@dataclass
class TimeBlock:
    """A scheduled block of time in the Founder's day."""
    name: str
    category: BlockCategory
    priority: BlockPriority
    start_time: str          # "HH:MM" in local time
    end_time: str            # "HH:MM" in local time
    description: str = ""
    day_of_week: str = "all"  # all, weekday, weekend, Mon, Tue, etc.
    is_fixed: bool = False    # Fixed time vs flexible placement
    owner: str = ""           # Which exec owns this block (jenson, valta_prime, yamako)
    completed: bool = False
    can_overlap: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# Default Schedule — Yamako's ideal Founder day
# ═══════════════════════════════════════════════════════════════════════════════

IDEAL_DAILY_SCHEDULE: List[TimeBlock] = [
    # ── Morning Routine (fixed) ─────────────────────────────────────────────
    TimeBlock("Wake Up", BlockCategory.PERSONAL, BlockPriority.CRITICAL,
              "05:00", "05:05", "Wake up, sit up, turn off alarm. No snooze.", is_fixed=True),
    TimeBlock("Hydration", BlockCategory.PERSONAL, BlockPriority.CRITICAL,
              "05:05", "05:10", "Drink a glass of water.", is_fixed=True),
    TimeBlock("Grounding / Meditation", BlockCategory.PERSONAL, BlockPriority.HIGH,
              "05:10", "05:20", "Sit quietly. Breathe. Set intention.", is_fixed=True),
    TimeBlock("Training", BlockCategory.TRAINING, BlockPriority.HIGH,
              "05:20", "06:00", "Physical training. Body before mind.", is_fixed=True),
    TimeBlock("Shower & Prepare", BlockCategory.PERSONAL, BlockPriority.HIGH,
              "06:00", "06:20", "Cold shower. Prepare for the day.", is_fixed=True),
    TimeBlock("Morning Study", BlockCategory.LEARNING, BlockPriority.HIGH,
              "06:20", "07:00", "Read, study, or consume educational content.", is_fixed=True),
    TimeBlock("Breakfast", BlockCategory.MEAL, BlockPriority.MEDIUM,
              "07:00", "07:20", "Fuel the body. No screens.", is_fixed=True),
    TimeBlock("Plan the Day", BlockCategory.BUSINESS_OPS, BlockPriority.HIGH,
              "07:20", "07:40", "Review schedule, priorities, set daily goals.", is_fixed=True),
    TimeBlock("Market Review", BlockCategory.TRADING, BlockPriority.HIGH,
              "07:40", "08:10", "Review markets with Valta Prime. Check GOLD/US30.", is_fixed=True),

    # ── Morning Work Block ──────────────────────────────────────────────────
    TimeBlock("Deep Work I", BlockCategory.CLIENT_WORK, BlockPriority.MEDIUM,
              "08:10", "10:00", "First focused work block. High-priority deliverables.", is_fixed=False),

    # ── Late Morning ────────────────────────────────────────────────────────
    TimeBlock("Trading Session I", BlockCategory.TRADING, BlockPriority.MEDIUM,
              "10:00", "11:30", "London/NY overlap. Active trading window.", is_fixed=False,
              owner="valta_prime"),
    TimeBlock("Meetings & Calls", BlockCategory.MEETING, BlockPriority.MEDIUM,
              "11:30", "12:30", "Client meetings, calls, syncs.", owner="jenson"),

    # ── Midday ──────────────────────────────────────────────────────────────
    TimeBlock("Lunch", BlockCategory.MEAL, BlockPriority.MEDIUM,
              "12:30", "13:15", "Proper lunch break. Step away from screens.", is_fixed=True),
    TimeBlock("Deep Work II", BlockCategory.CLIENT_WORK, BlockPriority.MEDIUM,
              "13:15", "15:00", "Second focused work block.", is_fixed=False),

    # ── Afternoon ────────────────────────────────────────────────────────────
    TimeBlock("Trading Session II", BlockCategory.TRADING, BlockPriority.MEDIUM,
              "15:00", "16:30", "US afternoon session. Monitor positions.", is_fixed=False,
              owner="valta_prime"),
    TimeBlock("Admin & Review", BlockCategory.BUSINESS_OPS, BlockPriority.LOW,
              "16:30", "17:30", "Email, admin, day review.", owner="jenson"),

    # ── Evening Routine ────────────────────────────────────────────────────
    TimeBlock("Learning Block", BlockCategory.LEARNING, BlockPriority.MEDIUM,
              "17:30", "18:30", "Structured learning / course work.", is_fixed=True),
    TimeBlock("Dinner", BlockCategory.MEAL, BlockPriority.MEDIUM,
              "18:30", "19:15", "Dinner. Family time if applicable.", is_fixed=True),
    TimeBlock("Flexible / Personal", BlockCategory.PERSONAL, BlockPriority.LOW,
              "19:15", "20:00", "Personal projects, reading, hobbies."),

    # ── Wind-Down ────────────────────────────────────────────────────────────
    TimeBlock("Wind-Down", BlockCategory.SLEEP, BlockPriority.CRITICAL,
              "20:00", "21:00", "No screens. Read, journal, prepare for sleep.", is_fixed=True),
    TimeBlock("Sleep", BlockCategory.SLEEP, BlockPriority.CRITICAL,
              "21:00", "05:00", "8 hours of sleep. Non-negotiable.", is_fixed=True),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Schedule Coordinator
# ═══════════════════════════════════════════════════════════════════════════════


class ScheduleCoordinator:
    """Yamako's schedule coordination engine.

    Manages the Founder's complete day by:
      1. Building the daily schedule from fixed blocks + flexible work
      2. Coordinating with Jenson for client work windows
      3. Coordinating with Valta Prime for trading windows
      4. Handling schedule conflicts and priority resolution
      5. Providing reminders for upcoming transitions
      6. Tracking schedule compliance
    """

    def __init__(self, runtime: Any = None) -> None:
        self._runtime = runtime
        self._base_schedule: List[TimeBlock] = list(IDEAL_DAILY_SCHEDULE)
        self._today_schedule: List[TimeBlock] = []
        self._current_day: str = ""
        self._reminders: List[Dict[str, Any]] = []

    # ── Daily Schedule Building ──────────────────────────────────────────────

    def build_today(self) -> List[TimeBlock]:
        """Build today's schedule from the base schedule.

        Applies day-of-week filtering and marks flexible blocks
        that can be rearranged.
        """
        today = datetime.now()
        day_name = today.strftime("%A")
        today_str = today.strftime("%Y-%m-%d")

        self._current_day = today_str
        today_blocks: List[TimeBlock] = []

        for block in self._base_schedule:
            # Apply day-of-week filter
            dow = block.day_of_week
            if dow in ("all", day_name):
                today_blocks.append(block)
            elif dow == "weekday" and day_name not in ("Saturday", "Sunday"):
                today_blocks.append(block)
            elif dow == "weekend" and day_name in ("Saturday", "Sunday"):
                today_blocks.append(block)

        self._today_schedule = today_blocks
        return list(self._today_schedule)

    def get_today(self) -> List[TimeBlock]:
        """Get today's schedule, building it if not yet built."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if self._current_day != today_str or not self._today_schedule:
            return self.build_today()
        return list(self._today_schedule)

    # ─── Context from Other Executives ───────────────────────────────────────

    def add_jenson_block(
        self,
        name: str,
        start_time: str,
        end_time: str,
        description: str = "",
        priority: BlockPriority = BlockPriority.MEDIUM,
    ) -> bool:
        """Add a Jenson-requested block to today's schedule.

        Returns True if added, False if conflict couldn't be resolved.
        """
        block = TimeBlock(
            name=name,
            category=BlockCategory.CLIENT_WORK,
            priority=priority,
            start_time=start_time,
            end_time=end_time,
            description=description,
            owner="jenson",
        )

        # Try to insert without conflict
        if self._can_insert(block, self._today_schedule):
            self._today_schedule.append(block)
            self._sort_schedule()
            return True

        # Try to resolve by moving lower-priority blocks
        return self._resolve_conflict(block)

    def add_valta_prime_block(
        self,
        name: str,
        start_time: str,
        end_time: str,
        description: str = "",
        priority: BlockPriority = BlockPriority.MEDIUM,
    ) -> bool:
        """Add a Valta Prime-requested block to today's schedule."""
        block = TimeBlock(
            name=name,
            category=BlockCategory.TRADING,
            priority=priority,
            start_time=start_time,
            end_time=end_time,
            description=description,
            owner="valta_prime",
        )

        if self._can_insert(block, self._today_schedule):
            self._today_schedule.append(block)
            self._sort_schedule()
            return True

        return self._resolve_conflict(block)

    # ── Conflict Resolution ──────────────────────────────────────────────────

    def _can_insert(self, new_block: TimeBlock, schedule: List[TimeBlock]) -> bool:
        """Check if a block can be inserted without conflict."""
        new_start = self._to_minutes(new_block.start_time)
        new_end = self._to_minutes(new_block.end_time)

        for existing in schedule:
            if existing.can_overlap:
                continue
            ex_start = self._to_minutes(existing.start_time)
            ex_end = self._to_minutes(existing.end_time)

            # Check overlap
            if new_start < ex_end and new_end > ex_start:
                return False

        return True

    def _resolve_conflict(self, new_block: TimeBlock) -> bool:
        """Try to resolve a scheduling conflict.

        Strategy: find a conflicting lower-priority block and move it
        to a flexible window later in the day.
        """
        new_start = self._to_minutes(new_block.start_time)
        new_end = self._to_minutes(new_block.end_time)

        for existing in list(self._today_schedule):
            ex_start = self._to_minutes(existing.start_time)
            ex_end = self._to_minutes(existing.end_time)

            # Check overlap
            if new_start < ex_end and new_end > ex_start:
                # If new block is higher priority, move existing
                if new_block.priority.value < existing.priority.value:
                    # Try to find a replacement window
                    replacement = self._find_replacement_window(existing)
                    if replacement:
                        existing.start_time = replacement[0]
                        existing.end_time = replacement[1]
                        self._today_schedule.append(new_block)
                        self._sort_schedule()
                        return True
                else:
                    # New block is lower priority — reject
                    return False

        # No conflict after resolution
        self._today_schedule.append(new_block)
        self._sort_schedule()
        return True

    def _find_replacement_window(self, block: TimeBlock) -> Optional[tuple]:
        """Find a replacement time window for a displaced block."""
        block_duration = self._to_minutes(block.end_time) - self._to_minutes(block.start_time)
        day_end = self._to_minutes("21:00")

        # Look for gaps in the afternoon/evening
        sorted_blocks = sorted(self._today_schedule, key=lambda b: self._to_minutes(b.start_time))
        cursor = self._to_minutes("13:00")

        for existing in sorted_blocks:
            ex_start = self._to_minutes(existing.start_time)
            if existing.can_overlap:
                continue
            if ex_start > cursor:
                gap = ex_start - cursor
                if gap >= block_duration:
                    start_h = cursor // 60
                    start_m = cursor % 60
                    end_h = (cursor + block_duration) // 60
                    end_m = (cursor + block_duration) % 60
                    return (f"{start_h:02d}:{start_m:02d}", f"{end_h:02d}:{end_m:02d}")
            cursor = max(cursor, self._to_minutes(existing.end_time))

        return None

    # ── Reminders ─────────────────────────────────────────────────────────────

    def get_current_block(self) -> Optional[TimeBlock]:
        """Get the currently active schedule block."""
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute

        for block in self.get_today():
            start = self._to_minutes(block.start_time)
            end = self._to_minutes(block.end_time)
            if start <= now_minutes < end:
                return block

        return None

    def get_next_block(self) -> Optional[TimeBlock]:
        """Get the next upcoming schedule block."""
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute

        for block in self.get_today():
            start = self._to_minutes(block.start_time)
            if start > now_minutes:
                return block

        return None

    def get_reminders(self) -> List[Dict[str, Any]]:
        """Get reminders for upcoming transitions.

        Returns reminders for:
          - Blocks starting in 15 minutes
          - Blocks starting now
          - Overdue blocks
        """
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute
        reminders: List[Dict[str, Any]] = []

        for block in self.get_today():
            start = self._to_minutes(block.start_time)
            minutes_until = start - now_minutes

            if 14 <= minutes_until <= 16:
                reminders.append({
                    "type": "upcoming",
                    "block": block.name,
                    "start_time": block.start_time,
                    "minutes_until": minutes_until,
                    "message": f"{block.name} starts in {minutes_until} minutes. {block.description}",
                    "owner": block.owner,
                })
            elif 0 <= minutes_until <= 1:
                reminders.append({
                    "type": "starting_now",
                    "block": block.name,
                    "message": f"Time for: {block.name} — {block.description}",
                    "owner": block.owner,
                })

        return reminders[:5]  # Max 5 reminders

    # ── Compliance Tracking ──────────────────────────────────────────────────

    def get_compliance(self) -> Dict[str, Any]:
        """Calculate schedule compliance for today.

        Returns:
          - total_blocks: Total blocks scheduled
          - completed: Blocks marked completed
          - in_progress: Currently active block
          - upcoming: Blocks yet to start
          - compliance_pct: Overall completion percentage
        """
        today = self.get_today()
        total = len(today)
        completed = sum(1 for b in today if b.completed)
        current = self.get_current_block()
        upcoming = sum(1 for b in today if self._to_minutes(b.start_time) > (datetime.now().hour * 60 + datetime.now().minute))

        return {
            "date": self._current_day,
            "total_blocks": total,
            "completed": completed,
            "current_block": current.name if current else None,
            "upcoming": upcoming,
            "compliance_pct": round((completed / total) * 100, 1) if total > 0 else 0,
        }

    def mark_completed(self, block_name: str) -> bool:
        """Mark a schedule block as completed."""
        for block in self._today_schedule:
            if block.name.lower() == block_name.lower():
                block.completed = True
                return True
        return False

    # ── Sleep Enforcement ────────────────────────────────────────────────────

    def get_sleep_reminder(self) -> Optional[str]:
        """Check if it's time for wind-down and return a reminder."""
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute

        # Wind-down starts at 20:00 (1200 minutes)
        if 1195 <= now_minutes <= 1200:
            return "🛌 Wind-down time in 5 minutes. Start preparing for sleep. No screens."

        if 1200 <= now_minutes <= 1205:
            return "🛌 Wind-down starts now. Step away from screens. Read. Journal. Prepare for rest."

        # Lights-out at 21:00 (1260 minutes)
        if 1255 <= now_minutes <= 1260:
            return "🌙 Lights-out in 5 minutes. Complete your wind-down routine."

        if 1260 <= now_minutes <= 1265:
            return "🌙 Lights-out. Time to sleep. 8 hours until 05:00."

        return None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _to_minutes(self, time_str: str) -> int:
        """Convert 'HH:MM' to minutes since midnight."""
        parts = time_str.strip().split(":")
        return int(parts[0]) * 60 + int(parts[1])

    def _sort_schedule(self) -> None:
        """Sort today's schedule by start time."""
        self._today_schedule.sort(key=lambda b: self._to_minutes(b.start_time))

    # ── Status ───────────────────────────────────────────────────────────────

    def get_dashboard(self) -> Dict[str, Any]:
        """Get a full schedule dashboard."""
        today = self.get_today()
        current = self.get_current_block()
        next_block = self.get_next_block()
        compliance = self.get_compliance()

        return {
            "date": self._current_day,
            "current_block": current.name if current else None,
            "next_block": next_block.name if next_block else f"{next_block.start_time} - {next_block.name}" if next_block else None,
            "compliance": compliance,
            "today_blocks": [
                {
                    "name": b.name,
                    "time": f"{b.start_time}-{b.end_time}",
                    "category": b.category.value,
                    "priority": b.priority.name,
                    "owner": b.owner,
                    "completed": b.completed,
                }
                for b in today
            ],
        }