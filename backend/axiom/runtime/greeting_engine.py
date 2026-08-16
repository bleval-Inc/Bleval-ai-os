"""Greeting Engine — dynamic boot / invocation greeting system for AXIOM OS.

Generates context-aware greetings based on time of day, day of week, system
health, seasons, and returning-user state.  Designed for the JARVIS-like voice
interface — each greeting carries a mood tag so the TTS system can adjust tone.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from axiom.runtime.logging import RuntimeLogger


# ═══════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class GreetingResult:
    """A fully resolved greeting with metadata for the TTS engine."""

    text: str
    mood: str  # "professional" | "excited" | "calm" | "serious" | "warm"
    time_of_day: str  # "morning" | "afternoon" | "evening" | "night"
    health_label: str  # "healthy" | "degraded" | "critical"
    variant_id: str
    is_seasonal: bool
    is_returning: bool


# ═══════════════════════════════════════════════════════════════════════════
# Greeting Pools — at least 30 context-aware variants
# ═══════════════════════════════════════════════════════════════════════════

# Each variant is a dict with keys:
#   text  – the greeting template (may include {name} and {time})
#   mood  – the TTS tone tag
#   id    – unique variant identifier

_MORNING_POOL: List[dict] = [
    # Healthy (4)
    {"text": "Good morning! All systems are green and ready to go. How can I help you today?", "mood": "excited", "id": "morning_healthy_01"},
    {"text": "Rise and shine — everything looks great on my end. What's on the agenda?", "mood": "warm", "id": "morning_healthy_02"},
    {"text": "Morning. Systems nominal, coffee brewed — well, metaphorically. What do you need?", "mood": "professional", "id": "morning_healthy_03"},
    {"text": "Good morning! I've been monitoring overnight and all is well. Ready when you are.", "mood": "calm", "id": "morning_healthy_04"},
    # Degraded (3)
    {"text": "Good morning. Just a heads up — a couple of subsystems are running a bit warm, but we're still operational. What can I do for you?", "mood": "calm", "id": "morning_degraded_01"},
    {"text": "Morning. I've seen better mornings, but we're holding together. Let me know how I can assist.", "mood": "warm", "id": "morning_degraded_02"},
    {"text": "Good morning. A few metrics are slightly elevated — I'm keeping an eye on them. How can I help?", "mood": "professional", "id": "morning_degraded_03"},
    # Critical (3)
    {"text": "Good morning. We have some issues that need attention — I'd recommend a system check at your earliest convenience.", "mood": "serious", "id": "morning_critical_01"},
    {"text": "Morning. I'm detecting elevated stress on the system. I'll keep things running, but you should take a look when you can.", "mood": "calm", "id": "morning_critical_02"},
    {"text": "Good morning. System health is below ideal thresholds. I've logged the details for your review.", "mood": "professional", "id": "morning_critical_03"},
]

_AFTERNOON_POOL: List[dict] = [
    # Healthy (4)
    {"text": "Good afternoon! Systems are humming along beautifully. What's next?", "mood": "excited", "id": "afternoon_healthy_01"},
    {"text": "Afternoon — everything is running smoothly on my end. What can I do for you?", "mood": "warm", "id": "afternoon_healthy_02"},
    {"text": "Good afternoon. All telemetry nominal. Ready for your next command.", "mood": "professional", "id": "afternoon_healthy_03"},
    {"text": "Afternoon check-in — all systems nominal. You've got a clear board.", "mood": "calm", "id": "afternoon_healthy_04"},
    # Degraded (3)
    {"text": "Good afternoon. Things are a bit sluggish in a few areas, but nothing we can't handle. What do you need?", "mood": "calm", "id": "afternoon_degraded_01"},
    {"text": "Afternoon. Some subsystems are under a little extra load today. I'm managing it — just so you know.", "mood": "warm", "id": "afternoon_degraded_02"},
    {"text": "Good afternoon. A few resources are stretched thin, but I'm keeping everything operational. How can I help?", "mood": "professional", "id": "afternoon_degraded_03"},
    # Critical (2)
    {"text": "Good afternoon. We're in a degraded state — I recommend pausing non-essential tasks until we resolve it.", "mood": "serious", "id": "afternoon_critical_01"},
    {"text": "Afternoon. System health is concerning. I'd suggest investigating as soon as you're free.", "mood": "calm", "id": "afternoon_critical_02"},
]

_EVENING_POOL: List[dict] = [
    # Healthy (4)
    {"text": "Good evening! Everything's been running smoothly all day. What can I help with?", "mood": "warm", "id": "evening_healthy_01"},
    {"text": "Evening — systems are quiet and stable. How can I assist?", "mood": "calm", "id": "evening_healthy_02"},
    {"text": "Good evening. All systems nominal. Ready for the night shift whenever you are.", "mood": "professional", "id": "evening_healthy_03"},
    {"text": "Evening check — everything looks great. What's on your mind?", "mood": "excited", "id": "evening_healthy_04"},
    # Degraded (2)
    {"text": "Good evening. A few things need attention, but we're still in good shape overall. How can I help?", "mood": "warm", "id": "evening_degraded_01"},
    {"text": "Evening. I've logged a couple of anomalies from today — nothing critical, but worth noting. What do you need?", "mood": "calm", "id": "evening_degraded_02"},
    # Critical (2)
    {"text": "Good evening. We have unresolved issues from today. I recommend prioritizing them first thing.", "mood": "serious", "id": "evening_critical_01"},
    {"text": "Evening. Some systems aren't recovering as expected. I've queued diagnostics for you.", "mood": "professional", "id": "evening_critical_02"},
]

_NIGHT_POOL: List[dict] = [
    # Healthy (3)
    {"text": "Late night session — everything's quiet on my end. What are we working on?", "mood": "calm", "id": "night_healthy_01"},
    {"text": "Burning the midnight oil? Systems are steady and ready. How can I help?", "mood": "warm", "id": "night_healthy_02"},
    {"text": "Good evening — or should I say good morning? All systems nominal. What do you need?", "mood": "professional", "id": "night_healthy_03"},
    # Degraded (2)
    {"text": "Working late? A few systems are under load, but nothing alarming. What can I do?", "mood": "calm", "id": "night_degraded_01"},
    {"text": "Late hours — some services are showing fatigue, but I've got it handled. How can I assist?", "mood": "warm", "id": "night_degraded_02"},
    # Critical (2)
    {"text": "It's late and we have some system issues. I'd recommend holding off until we can investigate properly.", "mood": "serious", "id": "night_critical_01"},
    {"text": "I know it's late, but we should address a few critical readings. I've queued the diagnostics.", "mood": "professional", "id": "night_critical_02"},
]

# Wake-greeting pool — shorter, "ready when you are" style
_WAKE_POOL: List[dict] = [
    {"text": "I'm here. What do you need?", "mood": "professional", "id": "wake_01"},
    {"text": "Ready and waiting. What's next?", "mood": "warm", "id": "wake_02"},
    {"text": "Back online. How can I help?", "mood": "calm", "id": "wake_03"},
    {"text": "At your service. What's the task?", "mood": "excited", "id": "wake_04"},
    {"text": "I'm all ears. What are we working on?", "mood": "warm", "id": "wake_05"},
    {"text": "Awake and aware. Go ahead.", "mood": "professional", "id": "wake_06"},
    {"text": "Present. What can I do for you?", "mood": "calm", "id": "wake_07"},
]

# Day-of-week overlays — appended or prepended to base greetings
_DOW_OVERLAYS: dict = {
    0: {"prefix": "Happy Monday! ", "mood": "excited"},    # Monday
    1: {},                                                    # Tuesday
    2: {},                                                    # Wednesday
    3: {},                                                    # Thursday
    4: {"prefix": "TGIF! ", "mood": "excited"},              # Friday
    5: {"prefix": "Happy weekend! ", "mood": "warm"},        # Saturday
    6: {"prefix": "Happy weekend! ", "mood": "warm"},        # Sunday
}

# Seasonal overlays
_SEASONAL_OVERLAYS: List[dict] = [
    # Christmas (Dec 24-26)
    {"months": [12], "days": (24, 26), "prefix": "Merry Christmas! ", "mood": "excited", "id": "seasonal_christmas"},
    # New Year (Dec 31 - Jan 1)
    {"months": [12, 1], "days": (31, 1), "prefix": "Happy New Year! ", "mood": "excited", "id": "seasonal_newyear"},
    # Halloween (Oct 31)
    {"months": [10], "days": (31, 31), "prefix": "Happy Halloween! ", "mood": "excited", "id": "seasonal_halloween"},
    # Summer (Jun 21 - Sep 22)
    {"months": [6, 7, 8, 9], "days": (21, 22), "prefix": "Hope you're enjoying the summer. ", "mood": "warm", "id": "seasonal_summer", "is_range": True},
    # Spring (Mar 20 - Jun 20)
    {"months": [3, 4, 5, 6], "days": (20, 20), "prefix": "Spring is in the air. ", "mood": "warm", "id": "seasonal_spring", "is_range": True},
    # Autumn (Sep 23 - Dec 20)
    {"months": [9, 10, 11, 12], "days": (23, 20), "prefix": "Cozy autumn vibes. ", "mood": "warm", "id": "seasonal_autumn", "is_range": True},
    # Winter (Dec 21 - Mar 19)
    {"months": [12, 1, 2, 3], "days": (21, 19), "prefix": "Stay warm out there. ", "mood": "warm", "id": "seasonal_winter", "is_range": True},
]

# Returning-user variants
_RETURNING_PREFIXES: List[str] = [
    "Welcome back, {name}. ",
    "Good to see you again, {name}. ",
    "Hello again, {name}. ",
]

_FIRST_BOOT_MESSAGES: List[str] = [
    "System initialized. I'm ready to assist. What shall we do first?",
    "First boot complete. I'm at your command. What do you need?",
    "Everything is up and running for the first time. How can I help you get started?",
]

# Health mood overrides for critical states
_HEALTH_MOOD_OVERRIDES: dict = {
    "healthy": None,     # Keep original mood
    "degraded": None,    # Keep original mood
    "critical": "serious",
}

# ═══════════════════════════════════════════════════════════════════════════
# Greeting Engine
# ═══════════════════════════════════════════════════════════════════════════


class GreetingEngine:
    """Dynamic boot / invocation greeting system.

    Generates context-aware greetings based on time of day, day of week,
    system health, seasonal events, and returning-user state.  Never repeats
    the same greeting consecutively.

    Designed to integrate with SystemMonitor for telemetry-driven mood
    and with the TTS engine for spoken output.
    """

    def __init__(self, monitor=None, logger: Optional[RuntimeLogger] = None) -> None:
        self._monitor = monitor
        self._logger = logger or RuntimeLogger()
        self._last_greetings: List[str] = []  # Track last 5 variant IDs
        self._max_history = 5

        self._logger.info("greeting_engine", "GreetingEngine initialized")

    # ── Public API ─────────────────────────────────────────────────────────

    async def generate_greeting(
        self,
        telemetry=None,
        is_first_boot: bool = False,
        user_name: Optional[str] = None,
    ) -> GreetingResult:
        """Generate a full boot / invocation greeting.

        Args:
            telemetry: Optional TelemetrySnapshot for system health awareness.
            is_first_boot: Whether this is the system's first-ever boot.
            user_name: Optional user name for personalised greetings.

        Returns:
            A GreetingResult with rendered text, mood, and context metadata.
        """
        now = datetime.now()
        time_of_day = self._resolve_time_of_day(now)
        health_label = self._resolve_health_label(telemetry)
        dow_index = now.weekday()

        # Select base greeting pool for this time of day
        pool = self._get_pool(time_of_day)
        eligible = [v for v in pool if v["id"] not in self._last_greetings]
        if not eligible:
            eligible = pool  # Reset if everything has been used recently

        choice = random.choice(eligible)
        base_text = choice["text"]
        base_mood = choice["mood"]
        variant_id = choice["id"]

        # Check for seasonal overlay
        seasonal = self._detect_season(now)
        is_seasonal = seasonal is not None

        # Check returning user
        is_returning = not is_first_boot and user_name is not None

        # Build the final text
        text = base_text

        # Apply day-of-week prefix
        dow_overlay = _DOW_OVERLAYS.get(dow_index, {})
        dow_prefix = dow_overlay.get("prefix", "")
        if dow_prefix:
            text = dow_prefix + text

        # Apply seasonal prefix
        if is_seasonal and seasonal:
            text = seasonal["prefix"] + text

        # Apply returning-user prefix (after seasonal/DOW so the name is near
        # the front but seasonal greetings still take outermost position)
        if is_returning:
            prefix = random.choice(_RETURNING_PREFIXES).format(name=user_name or "User")
            text = prefix + text
        elif is_first_boot:
            text = random.choice(_FIRST_BOOT_MESSAGES)

        # Resolve final mood
        mood = self._resolve_mood(base_mood, health_label, seasonal, dow_overlay)

        # Track to avoid repetition
        self._last_greetings.append(variant_id)
        if len(self._last_greetings) > self._max_history:
            self._last_greetings.pop(0)

        self._logger.info(
            "greeting_engine",
            f"Generated greeting [{variant_id}] mood={mood} tod={time_of_day} health={health_label}",
        )

        return GreetingResult(
            text=text,
            mood=mood,
            time_of_day=time_of_day,
            health_label=health_label,
            variant_id=variant_id,
            is_seasonal=is_seasonal,
            is_returning=is_returning,
        )

    async def generate_wake_greeting(self, telemetry=None) -> GreetingResult:
        """Generate a short wake-from-idle greeting.

        Args:
            telemetry: Optional TelemetrySnapshot for health awareness.

        Returns:
            A GreetingResult with a concise wake phrase.
        """
        now = datetime.now()
        time_of_day = self._resolve_time_of_day(now)
        health_label = self._resolve_health_label(telemetry)

        eligible = [v for v in _WAKE_POOL if v["id"] not in self._last_greetings]
        if not eligible:
            eligible = _WAKE_POOL

        choice = random.choice(eligible)
        text = choice["text"]
        mood = choice["mood"]
        variant_id = choice["id"]

        # Apply health-based mood override for critical states
        if health_label == "critical":
            mood = "serious"

        self._last_greetings.append(variant_id)
        if len(self._last_greetings) > self._max_history:
            self._last_greetings.pop(0)

        self._logger.info(
            "greeting_engine",
            f"Generated wake greeting [{variant_id}] mood={mood} health={health_label}",
        )

        return GreetingResult(
            text=text,
            mood=mood,
            time_of_day=time_of_day,
            health_label=health_label,
            variant_id=variant_id,
            is_seasonal=False,
            is_returning=False,
        )

    async def generate_status_report(self, telemetry) -> str:
        """Generate a one-line system status summary suitable for voice TTS.

        Args:
            telemetry: A TelemetrySnapshot (or anything with .cpu.percent,
                       .memory.percent, .disk.percent, .health_label).

        Returns:
            A human-readable status string, e.g.
            "CPU at 23%, memory at 45%, disk at 60%. All systems nominal."
        """
        cpu = getattr(telemetry, "cpu", None)
        memory = getattr(telemetry, "memory", None)
        disk = getattr(telemetry, "disk", None)

        cpu_pct = getattr(cpu, "percent", 0) if cpu else 0
        mem_pct = getattr(memory, "percent", 0) if memory else 0
        disk_pct = getattr(disk, "percent", 0) if disk else 0

        # Determine health label safely (in case telemetry is not a full snapshot)
        health = telemetry.health_label if hasattr(telemetry, "health_label") else "unknown"

        status_line = (
            f"CPU at {cpu_pct:.0f} percent, "
            f"memory at {mem_pct:.0f} percent, "
            f"disk at {disk_pct:.0f} percent."
        )

        if health == "healthy":
            status_line += " All systems nominal."
        elif health == "degraded":
            status_line += " Some systems are under load but still operational."
        else:
            status_line += " I recommend checking the system logs."

        return status_line

    # ── Internal helpers ───────────────────────────────────────────────────

    def _resolve_time_of_day(self, dt: datetime) -> str:
        """Map an hour to a time-of-day label."""
        hour = dt.hour
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 17:
            return "afternoon"
        if 17 <= hour < 21:
            return "evening"
        return "night"

    def _resolve_health_label(self, telemetry) -> str:
        """Extract health label from telemetry or default to healthy."""
        if telemetry is not None and hasattr(telemetry, "health_label"):
            return telemetry.health_label
        return "healthy"

    def _get_pool(self, time_of_day: str) -> List[dict]:
        """Return the greeting pool for a given time of day."""
        mapping = {
            "morning": _MORNING_POOL,
            "afternoon": _AFTERNOON_POOL,
            "evening": _EVENING_POOL,
            "night": _NIGHT_POOL,
        }
        return mapping.get(time_of_day, _MORNING_POOL)

    def _detect_season(self, dt: datetime) -> Optional[dict]:
        """Detect whether today falls in a seasonal event window.

        Returns the matching seasonal overlay dict, or None.
        """
        for season in _SEASONAL_OVERLAYS:
            start_day, end_day = season["days"]
            is_range = season.get("is_range", False)

            if is_range:
                # Range-based season (e.g. Summer: Jun 21 - Sep 22)
                # Check if month and day fall within the range
                month = dt.month
                day = dt.day

                # Define season start and end boundaries
                # First month in months list is the start month
                # Last month in months list is the end month
                start_month = season["months"][0]
                end_month = season["months"][-1]

                if start_month == end_month:
                    # Same month range
                    if month == start_month and start_day <= day <= end_day:
                        return season
                elif month == start_month and day >= start_day:
                    return season
                elif month == end_month and day <= end_day:
                    return season
                elif start_month < month < end_month:
                    return season
                elif start_month > end_month:
                    # Wraps around year boundary (e.g. Winter: Dec 21 - Mar 19)
                    if month >= start_month or month <= end_month:
                        if month == start_month and day < start_day:
                            continue
                        if month == end_month and day > end_day:
                            continue
                        return season
            else:
                # Exact day or day range (e.g. Christmas: Dec 24-26)
                if dt.month in season["months"]:
                    # Handle month transitions (e.g. New Year Dec 31 - Jan 1)
                    if season["months"] == [12, 1]:
                        if dt.month == 12 and dt.day >= start_day:
                            return season
                        if dt.month == 1 and dt.day <= end_day:
                            return season
                    else:
                        if start_day <= dt.day <= end_day:
                            return season

        return None

    def _resolve_mood(
        self,
        base_mood: str,
        health_label: str,
        seasonal: Optional[dict],
        dow_overlay: dict,
    ) -> str:
        """Resolve the final mood tag, considering all contexts.

        Priority:
          1. Critical health overrides to "serious".
          2. Seasonal mood takes precedence over base.
          3. Day-of-week overlay mood takes next precedence.
          4. Base pool mood is the default.
        """
        # Critical health always takes precedence
        if health_label == "critical":
            return "serious"

        # Seasonal mood
        if seasonal is not None:
            return seasonal.get("mood", base_mood)

        # Day-of-week mood
        dow_mood = dow_overlay.get("mood")
        if dow_mood:
            return dow_mood

        return base_mood