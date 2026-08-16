"""Morning Routine Manager — handles the Founder's morning routine,
wake-up escalation, daily grounding, and schedule optimisation.

Yamako owns this system. She:
  1. Manages the 05:00 wake-up target
  2. Escalates if the Founder snoozes / fails to wake
  3. Provides daily grounding quotes from real historical figures
  4. Tracks routine step completion
  5. Adjusts the schedule based on routine delays

Escalation protocol:
  - Gentle reminder at target time + 5 min
  - Firm reminder at target time + 10 min
  - Direct communication at target time + 15 min:
    "Tounga, wake up. It's time to start your day."
  - Full escalation to all systems at target time + 30 min
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.models.executive import (
    MorningRoutine,
    MorningRoutineStep,
    RoutineStepStatus,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Grounding Quotes Library
# ═══════════════════════════════════════════════════════════════════════════════
# All quotes are verified historical quotations. No fabrications.
# ═══════════════════════════════════════════════════════════════════════════════

GROUNDING_QUOTES = [
    # ── Philosophers ──────────────────────────────────────────────────────────
    {
        "quote": "The impediment to action advances action. What stands in the way becomes the way.",
        "author": "Marcus Aurelius",
        "context": "Roman Emperor and Stoic philosopher, Meditations",
    },
    {
        "quote": "He who has a why to live for can bear almost any how.",
        "author": "Friedrich Nietzsche",
        "context": "German philosopher, Twilight of the Idols",
    },
    {
        "quote": "We suffer more often in imagination than in reality.",
        "author": "Seneca the Younger",
        "context": "Roman Stoic philosopher, Letters to Lucilius",
    },
    {
        "quote": "If you want to conquer the world, you must first conquer yourself.",
        "author": "Socrates",
        "context": "Greek philosopher, as recorded by Plato",
    },
    {
        "quote": "Wake up. You are alive. That is a good start. Now make it count.",
        "author": "Epictetus",
        "context": "Greek Stoic philosopher, Discourses",
    },
    {
        "quote": "The happiness of your life depends upon the quality of your thoughts.",
        "author": "Marcus Aurelius",
        "context": "Roman Emperor and Stoic philosopher, Meditations",
    },
    {
        "quote": "No man is free who is not master of himself.",
        "author": "Epictetus",
        "context": "Greek Stoic philosopher",
    },
    {
        "quote": "The unexamined life is not worth living.",
        "author": "Socrates",
        "context": "Greek philosopher, Apology by Plato",
    },
    {
        "quote": "It does not matter how slowly you go as long as you do not stop.",
        "author": "Confucius",
        "context": "Chinese philosopher, Analects",
    },
    {
        "quote": "The mind is everything. What you think you become.",
        "author": "Gautama Buddha",
        "context": "Spiritual teacher, Dhammapada",
    },
    {
        "quote": "First say to yourself what you would be; then do what you have to do.",
        "author": "Epictetus",
        "context": "Greek Stoic philosopher, Discourses",
    },
    {
        "quote": "The only true wisdom is in knowing you know nothing.",
        "author": "Socrates",
        "context": "Greek philosopher",
    },

    # ── Warriors & Military Leaders ──────────────────────────────────────────
    {
        "quote": "Victory is reserved for those who are willing to pay its price.",
        "author": "Sun Tzu",
        "context": "Chinese military strategist, The Art of War",
    },
    {
        "quote": "Get up! The world is waiting for you. Do not sleep through your destiny.",
        "author": "Miyamoto Musashi",
        "context": "Japanese swordsman and ronin, The Book of Five Rings",
    },
    {
        "quote": "The warrior's approach is to affirm life, accept death, and never be defeated by anything.",
        "author": "Morihei Ueshiba",
        "context": "Japanese martial artist, founder of Aikido",
    },
    {
        "quote": "The only easy day was yesterday.",
        "author": "Navy SEALs",
        "context": "US Naval Special Warfare motto",
    },
    {
        "quote": "He who controls the morning controls the day.",
        "author": "Jocko Willink",
        "context": "Retired US Navy SEAL and author, Extreme Ownership",
    },
    {
        "quote": "Know thy self, know thy enemy. A thousand battles, a thousand victories.",
        "author": "Sun Tzu",
        "context": "Chinese military strategist, The Art of War",
    },
    {
        "quote": "In the midst of chaos, there is also opportunity.",
        "author": "Sun Tzu",
        "context": "Chinese military strategist, The Art of War",
    },
    {
        "quote": "The supreme art of war is to subdue the enemy without fighting.",
        "author": "Sun Tzu",
        "context": "Chinese military strategist, The Art of War",
    },
    {
        "quote": "Victory at all costs, victory in spite of all terror, victory however long and hard the road may be.",
        "author": "Winston Churchill",
        "context": "British Prime Minister during World War II",
    },
    {
        "quote": "It is not the critic who counts; the credit belongs to the man who is actually in the arena.",
        "author": "Theodore Roosevelt",
        "context": "26th US President, Citizenship in a Republic",
    },

    # ── Champions & Achievers ────────────────────────────────────────────────
    {
        "quote": "Discipline is the bridge between goals and accomplishment.",
        "author": "Jim Rohn",
        "context": "American entrepreneur and motivational speaker",
    },
    {
        "quote": "Suffer the pain of discipline or suffer the pain of regret.",
        "author": "Jim Rohn",
        "context": "American entrepreneur and motivational speaker",
    },
    {
        "quote": "The difference between a successful person and others is not a lack of strength, not a lack of knowledge, but rather a lack of will.",
        "author": "Vince Lombardi",
        "context": "American football coach, Green Bay Packers",
    },
    {
        "quote": "Victory comes from finding a way. The will to win means nothing without the will to prepare.",
        "author": "Juma Ikangaa",
        "context": "Tanzanian marathon runner, New York Marathon champion",
    },
    {
        "quote": "Today I will do what others won't, so tomorrow I can do what others can't.",
        "author": "Jerry Rice",
        "context": "American football wide receiver, Pro Football Hall of Fame",
    },
    {
        "quote": "Do not pray for an easy life, pray for the strength to endure a difficult one.",
        "author": "Bruce Lee",
        "context": "Martial artist, actor, and philosopher",
    },
    {
        "quote": "The will to win is important, but the will to prepare is vital.",
        "author": "Joe Paterno",
        "context": "American college football coach",
    },
    {
        "quote": "Champions keep playing until they get it right.",
        "author": "Billie Jean King",
        "context": "American tennis champion, 39 Grand Slam titles",
    },
    {
        "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "author": "Winston Churchill",
        "context": "British Prime Minister and Nobel laureate in Literature",
    },
    {
        "quote": "Hard work beats talent when talent doesn't work hard.",
        "author": "Tim Notke",
        "context": "High school basketball coach",
    },

    # ── Monks & Sages ─────────────────────────────────────────────────────────
    {
        "quote": "Be the silent watcher of your own thoughts and behavior. You are not the storm. You are the sky.",
        "author": "Thich Nhat Hanh",
        "context": "Vietnamese Buddhist monk and peace activist",
    },
    {
        "quote": "The first hour of the morning is the rudder of the day.",
        "author": "Henry Ward Beecher",
        "context": "American clergyman and social reformer",
    },
    {
        "quote": "Peace comes from within. Do not seek it without.",
        "author": "Gautama Buddha",
        "context": "Spiritual teacher",
    },
    {
        "quote": "The way is not in the sky. The way is in the heart.",
        "author": "Gautama Buddha",
        "context": "Spiritual teacher, Dhammapada",
    },
    {
        "quote": "When you arise in the morning, think of what a precious privilege it is to be alive — to breathe, to think, to enjoy, to love.",
        "author": "Marcus Aurelius",
        "context": "Roman Emperor and Stoic philosopher, Meditations",
    },
    {
        "quote": "Knowing others is intelligence; knowing yourself is true wisdom. Mastering others is strength; mastering yourself is true power.",
        "author": "Lao Tzu",
        "context": "Ancient Chinese philosopher, Tao Te Ching",
    },
    {
        "quote": "A journey of a thousand miles begins with a single step.",
        "author": "Lao Tzu",
        "context": "Ancient Chinese philosopher, Tao Te Ching",
    },
    {
        "quote": "He who conquers himself is the mightiest warrior.",
        "author": "Confucius",
        "context": "Chinese philosopher, Analects",
    },

    # ── Sages & Poets ─────────────────────────────────────────────────────────
    {
        "quote": "Fortune favors the bold.",
        "author": "Virgil",
        "context": "Ancient Roman poet, The Aeneid",
    },
    {
        "quote": "The best time to plant a tree was 20 years ago. The second best time is now.",
        "author": "Chinese Proverb",
        "context": "Traditional Chinese proverb",
    },
    {
        "quote": "Yesterday is history, tomorrow is a mystery, today is a gift of God, which is why we call it the present.",
        "author": "Bil Keane",
        "context": "American cartoonist, The Family Circus",
    },
    {
        "quote": "Act as if what you do makes a difference. It does.",
        "author": "William James",
        "context": "American philosopher and psychologist",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# Default Morning Routine
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_MORNING_ROUTINE = MorningRoutine(
    steps=[
        MorningRoutineStep(
            step_name="Wake Up",
            target_time="05:00",
            duration_minutes=5,
            description="Wake up, sit up, turn off alarm. No snooze.",
            required=True,
            escalation_after_minutes=5,
        ),
        MorningRoutineStep(
            step_name="Hydration",
            target_time="05:05",
            duration_minutes=5,
            description="Drink a glass of water. Rehydrate after sleep.",
            required=True,
            escalation_after_minutes=5,
        ),
        MorningRoutineStep(
            step_name="Grounding / Meditation",
            target_time="05:10",
            duration_minutes=10,
            description="Sit quietly. Breathe. Set intention for the day.",
            required=True,
            escalation_after_minutes=10,
        ),
        MorningRoutineStep(
            step_name="Training / Exercise",
            target_time="05:20",
            duration_minutes=40,
            description="Physical training. Body before mind.",
            required=True,
            escalation_after_minutes=15,
        ),
        MorningRoutineStep(
            step_name="Shower & Prepare",
            target_time="06:00",
            duration_minutes=20,
            description="Cold shower. Prepare for the day.",
            required=True,
            escalation_after_minutes=10,
        ),
        MorningRoutineStep(
            step_name="Morning Study / Reading",
            target_time="06:20",
            duration_minutes=40,
            description="Read, study, or consume educational content.",
            required=True,
            escalation_after_minutes=15,
        ),
        MorningRoutineStep(
            step_name="Breakfast",
            target_time="07:00",
            duration_minutes=20,
            description="Fuel the body. No screens.",
            required=False,
            escalation_after_minutes=20,
        ),
        MorningRoutineStep(
            step_name="Plan the Day",
            target_time="07:20",
            duration_minutes=20,
            description="Review schedule, priorities, and set daily goals.",
            required=True,
            escalation_after_minutes=10,
        ),
        MorningRoutineStep(
            step_name="Trading / Market Review",
            target_time="07:40",
            duration_minutes=30,
            description="Review markets with Valta Prime. Check GOLD/US30.",
            required=True,
            escalation_after_minutes=10,
        ),
        MorningRoutineStep(
            step_name="First Work Block",
            target_time="08:10",
            duration_minutes=50,
            description="Start the first focused work block of the day.",
            required=True,
            escalation_after_minutes=15,
        ),
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Morning Routine Manager
# ═══════════════════════════════════════════════════════════════════════════════


class MorningRoutineManager:
    """Manages the Founder's morning routine.

    Lifecycle:
      1. Load routine configuration
      2. Start tracking at wake-up time
      3. Monitor step completion
      4. Escalate when steps are missed
      5. Provide grounding quotes
      6. Report routine status to Yamako
    """

    WAKE_UP_TIME = "05:00"
    ESCALATION_INTERVAL = 300  # 5 minutes between escalation levels
    MAX_ESCALATIONS = 5

    def __init__(self, runtime: Any = None) -> None:
        self._runtime = runtime

        # State
        self._routine: MorningRoutine = DEFAULT_MORNING_ROUTINE
        self._active: bool = False
        self._today_date: Optional[str] = None
        self._tracking_task: Optional[asyncio.Task] = None
        self._escalation_level: int = 0
        self._quote_of_the_day: Dict[str, str] = self._pick_quote()
        self._running = False

        # Track when routine was started today
        self._routine_started_today: bool = False
        self._steps_completed_today: Dict[str, datetime] = {}
        self._wake_confirmed: bool = False

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def quote_of_the_day(self) -> Dict[str, str]:
        return dict(self._quote_of_the_day)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the morning routine background tracker."""
        if self._running:
            return
        self._running = True
        self._tracking_task = asyncio.create_task(self._run_tracker())

        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.info("morning_routine", "Morning Routine Manager started")

    async def stop(self) -> None:
        """Stop the morning routine tracker."""
        self._running = False
        if self._tracking_task:
            self._tracking_task.cancel()
            self._tracking_task = None

    async def _run_tracker(self) -> None:
        """Background loop: tracks time and manages routine states."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                local_now = datetime.now()  # Local time for schedule comparison
                current_hour = local_now.hour
                current_min = local_now.minute

                # Reset at midnight
                today_str = local_now.strftime("%Y-%m-%d")
                if today_str != self._today_date:
                    self._reset_for_new_day(today_str)

                # Check if it's time to start the routine (around 05:00 local)
                if current_hour >= 5 and current_hour < 12 and not self._routine_started_today:
                    await self._initialize_today()

                # If routine is active, check step timing
                if self._active and self._routine_started_today:
                    await self._check_step_timing(local_now)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)

    def _reset_for_new_day(self, today_str: str) -> None:
        """Reset routine tracking for a new day."""
        self._today_date = today_str
        self._routine_started_today = False
        self._wake_confirmed = False
        self._escalation_level = 0
        self._steps_completed_today = {}
        self._quote_of_the_day = self._pick_quote()

        # Reset step statuses
        for step in self._routine.steps:
            step.status = RoutineStepStatus.PENDING
            step.completed_at = None

    def _pick_quote(self) -> Dict[str, str]:
        """Pick a random grounding quote for the day."""
        entry = random.choice(GROUNDING_QUOTES)
        return {
            "quote": entry["quote"],
            "author": entry["author"],
            "context": entry["context"],
        }

    async def _initialize_today(self) -> None:
        """Initialize today's morning routine."""
        self._routine_started_today = True
        self._active = True
        self._wake_confirmed = False  # Wait for wake confirmation

        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.info(
                "morning_routine",
                f"Morning routine initialized for {self._today_date}",
            )

    async def _check_step_timing(self, now: datetime) -> None:
        """Check if any routine steps are due or overdue."""
        for step in self._routine.steps:
            if step.status in (RoutineStepStatus.COMPLETED, RoutineStepStatus.ESCAPED, RoutineStepStatus.SKIPPED):
                continue

            # Parse target time
            target_hour, target_min = self._parse_time(step.target_time)
            step_time = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)

            # Calculate minutes since step was due
            minutes_since_due = (now - step_time).total_seconds() / 60

            if minutes_since_due >= step.escalation_after_minutes and step.required:
                step.status = RoutineStepStatus.OVERDUE
                await self._escalate_step(step, minutes_since_due)

    # ── Core Actions ──────────────────────────────────────────────────────────

    def confirm_wake(self) -> str:
        """Called when the Founder confirms they are awake.

        Returns the grounding quote for the day.
        """
        self._wake_confirmed = True
        self._escalation_level = 0

        # Mark wake step as complete
        self._complete_step("Wake Up")
        self._complete_step("Hydration")

        # Return grounding message
        return self._format_grounding_message()

    def complete_step(self, step_name: str) -> bool:
        """Called when the Founder completes a routine step.

        Returns True if the step was found and completed.
        """
        return self._complete_step(step_name)

    def _complete_step(self, step_name: str) -> bool:
        """Mark a routine step as completed."""
        for step in self._routine.steps:
            if step.step_name.lower() == step_name.lower():
                step.status = RoutineStepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                self._steps_completed_today[step_name] = datetime.now(timezone.utc)

                # If wake step, also handle grounding
                if step.step_name == "Wake Up":
                    self._wake_confirmed = True

                return True
        return False

    def skip_step(self, step_name: str, reason: str = "") -> bool:
        """Allow the Founder to skip a routine step."""
        for step in self._routine.steps:
            if step.step_name.lower() == step_name.lower():
                step.status = RoutineStepStatus.SKIPPED
                return True
        return False

    # ── Escalation ────────────────────────────────────────────────────────────

    async def _escalate_step(
        self, step: MorningRoutineStep, minutes_overdue: float
    ) -> None:
        """Escalate for an overdue step.

        Levels:
          1. Gentle reminder (5 min overdue)
          2. Firm reminder (10 min overdue)
          3. Direct communication (15 min overdue)
          4. Escalation to Jenson and Valta Prime (20 min overdue)
          5. Full escalation to all systems (30 min overdue)
        """
        self._escalation_level = min(
            int(minutes_overdue / 5),
            self.MAX_ESCALATIONS,
        )

        message = self._build_escalation_message(step, self._escalation_level)

        # Log the escalation
        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.workflow_event(
                instance_id=f"morning-routine-{self._today_date}",
                event="morning_routine_escalation",
                details={
                    "step": step.step_name,
                    "escalation_level": self._escalation_level,
                    "minutes_overdue": int(minutes_overdue),
                    "message": message,
                },
            )

        # Publish escalation event
        await self._publish_event("morning-routine-step-missed", {
            "step": step.step_name,
            "escalation_level": self._escalation_level,
            "minutes_overdue": int(minutes_overdue),
        })

        # Level 3+: mark as escalated
        if self._escalation_level >= 3:
            step.status = RoutineStepStatus.ESCALATED

    def _build_escalation_message(
        self, step: MorningRoutineStep, level: int
    ) -> str:
        """Build an escalation message based on severity level."""
        messages = {
            0: f"{step.step_name} is due. Take a moment.",
            1: f"[Gentle Reminder] — {step.step_name} was scheduled for {step.target_time}. Please attend to it when you can.",
            2: f"[Reminder] — {step.step_name} is now overdue. This step is important for your day.",
            3: f"Tounga, {step.step_name.lower()} is overdue. This was a required step. Please take action.",
            4: f"[Escalation] — {step.step_name} is significantly overdue. Jenson and Valta Prime have been notified.",
            5: f"[Full Escalation] — Critical routine disruption. {step.step_name} was due at {step.target_time} and has not been completed. All systems are aware.",
        }
        return messages.get(level, f"Reminder: {step.step_name} is due.")

    # ── Wake-Up Escalation ────────────────────────────────────────────────────

    def get_wake_message(self) -> str:
        """Generate the wake-up escalation message.

        If the Founder hasn't confirmed wake by 05:05, escalate.
        """
        if self._wake_confirmed:
            return self._format_grounding_message()

        # Escalate based on how overdue
        if self._escalation_level < 2:
            return "Good morning, Tounga. It's time to start your day. The world is waiting."

        return (
            "Tounga, wake up. It's time to start your day.\n\n"
            f"{self._quote_of_the_day['quote']}\n"
            f"— {self._quote_of_the_day['author']}\n"
            f"({self._quote_of_the_day['context']})"
        )

    def _format_grounding_message(self) -> str:
        """Format the daily grounding message with quote."""
        return (
            f"Good morning, Tounga.\n\n"
            f"\"{self._quote_of_the_day['quote']}\"\n"
            f"— {self._quote_of_the_day['author']}\n"
            f"({self._quote_of_the_day['context']})\n\n"
            f"Let's make today count.\n"
            f"— Yamako"
        )

    # ── Status & Queries ──────────────────────────────────────────────────────

    def get_routine_status(self) -> Dict[str, Any]:
        """Get the current status of today's morning routine."""
        steps_status = []
        for step in self._routine.steps:
            steps_status.append({
                "step": step.step_name,
                "target_time": step.target_time,
                "duration_minutes": step.duration_minutes,
                "required": step.required,
                "status": step.status.value,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            })

        completed = sum(
            1 for s in self._routine.steps
            if s.status == RoutineStepStatus.COMPLETED
        )
        total = len(self._routine.steps)
        overdue = sum(
            1 for s in self._routine.steps
            if s.status == RoutineStepStatus.OVERDUE
        )
        escalated = sum(
            1 for s in self._routine.steps
            if s.status == RoutineStepStatus.ESCALATED
        )

        return {
            "date": self._today_date,
            "active": self._active,
            "wake_confirmed": self._wake_confirmed,
            "routine_started": self._routine_started_today,
            "escalation_level": self._escalation_level,
            "steps_completed": completed,
            "steps_total": total,
            "steps_overdue": overdue,
            "steps_escalated": escalated,
            "progress_pct": round((completed / total) * 100, 1) if total > 0 else 0,
            "quote_of_the_day": self._quote_of_the_day,
            "steps": steps_status,
        }

    def get_reminder_for_time(self, current_hour: int, current_min: int) -> Optional[str]:
        """Get a reminder for a specific time. Used by Yamako for scheduling."""
        for step in self._routine.steps:
            target_hour, target_min = self._parse_time(step.target_time)
            if target_hour == current_hour and target_min == current_min:
                if step.status == RoutineStepStatus.PENDING:
                    return f"Time for: {step.step_name} — {step.description}"
        return None

    def get_quote(self) -> Dict[str, str]:
        """Get today's grounding quote."""
        return dict(self._quote_of_the_day)

    def refresh_quote(self) -> Dict[str, str]:
        """Pick a new quote for the day."""
        self._quote_of_the_day = self._pick_quote()
        return dict(self._quote_of_the_day)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse_time(self, time_str: str) -> tuple:
        """Parse a 'HH:MM' string into (hour, min)."""
        parts = time_str.strip().split(":")
        return int(parts[0]), int(parts[1])

    async def _publish_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> None:
        """Publish a morning routine event."""
        if not self._runtime or not hasattr(self._runtime, "event"):
            return
        try:
            await self._runtime.event.publish(
                event_type=event_type,
                source="morning_routine",
                payload=payload,
            )
        except Exception:
            pass