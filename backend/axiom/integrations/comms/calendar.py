"""Calendar Provider — Google, Outlook, Calendly, Cal.com."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel, Field, SecretStr

from axiom.data.models import (
    CalendarEvent,
    EventType,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class CalendarConfig(BaseModel):
    """Calendar configuration."""

    provider: str  # google, outlook, calendly, calcom
    enabled: bool = True

    # OAuth
    client_id: str
    client_secret: SecretStr
    redirect_uri: str
    scopes: List[str] = Field(default_factory=list)
    access_token: Optional[SecretStr] = None
    refresh_token: Optional[SecretStr] = None
    token_expires_at: Optional[datetime] = None

    # API
    base_url: str
    api_version: str = "v3"

    # Calendly/Cal.com specific
    organization_url: Optional[str] = None
    user_url: Optional[str] = None

    # Sync
    sync_interval_minutes: int = 15
    sync_past_days: int = 30
    sync_future_days: int = 90

    # Webhook
    webhook_url: Optional[str] = None
    webhook_secret: Optional[SecretStr] = None


class CalendarProvider:
    """Multi-provider calendar integration."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: CalendarConfig,
        repository,  # CommsRepository
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {}
            if self.config.access_token:
                headers["Authorization"] = f"Bearer {self.config.access_token.get_secret_value()}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def start(self):
        """Start calendar provider."""
        if self._running:
            return

        # Ensure valid token
        await self._ensure_token()

        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        self.logger.info(f"Calendar provider ({self.config.provider}) started")

    async def stop(self):
        """Stop calendar provider."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        if self._session and not self._session.closed:
            await self._session.close()
        self.logger.info("Calendar provider stopped")

    async def _ensure_token(self):
        """Ensure valid access token."""
        if not self.config.access_token:
            # Would initiate OAuth flow
            return

        if self.config.token_expires_at and self.config.token_expires_at < datetime.utcnow() + timedelta(minutes=5):
            await self._refresh_token()

    async def _refresh_token(self):
        """Refresh OAuth token."""
        if not self.config.refresh_token:
            return

        session = await self._get_session()
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret.get_secret_value(),
            "refresh_token": self.config.refresh_token.get_secret_value(),
            "grant_type": "refresh_token",
        }

        url = f"{self.config.base_url}/oauth2/token"
        async with session.post(url, data=data) as resp:
            if resp.status == 200:
                token_data = await resp.json()
                self.config.access_token = SecretStr(token_data["access_token"])
                if "refresh_token" in token_data:
                    self.config.refresh_token = SecretStr(token_data["refresh_token"])
                expires_in = token_data.get("expires_in", 3600)
                self.config.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                self.logger.info("Calendar token refreshed")

    # ──────────────────────────────────────────────────────────────────────────────
    # Google Calendar
    # ──────────────────────────────────────────────────────────────────────────────

    async def _google_list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
    ) -> List[Dict]:
        """List events from Google Calendar."""
        session = await self._get_session()
        params = {
            "singleEvents": "true",
            "orderBy": "startTime",
        }
        if time_min:
            params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            params["timeMax"] = time_max.isoformat() + "Z"

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("items", [])
            elif resp.status == 401:
                await self._refresh_token()
                return await self._google_list_events(calendar_id, time_min, time_max)
        return []

    async def _google_get_event(self, calendar_id: str, event_id: str) -> Optional[Dict]:
        """Get single event from Google Calendar."""
        session = await self._get_session()
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}"
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
        return None

    async def _google_create_event(
        self,
        calendar_id: str,
        event_data: Dict,
    ) -> Optional[Dict]:
        """Create event in Google Calendar."""
        session = await self._get_session()
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        async with session.post(url, json=event_data) as resp:
            if resp.status == 200:
                return await resp.json()
        return None

    # ──────────────────────────────────────────────────────────────────────────────
    # Outlook Calendar
    # ──────────────────────────────────────────────────────────────────────────────

    async def _outlook_list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
    ) -> List[Dict]:
        """List events from Outlook Calendar."""
        session = await self._get_session()
        params = {
            "$orderby": "start/dateTime",
            "$top": 100,
        }
        filter_parts = []
        if time_min:
            filter_parts.append(f"start/dateTime ge '{time_min.isoformat()}'")
        if time_max:
            filter_parts.append(f"end/dateTime le '{time_max.isoformat()}'")
        if filter_parts:
            params["$filter"] = " and ".join(filter_parts)

        url = f"https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events"
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("value", [])
        return []

    # ──────────────────────────────────────────────────────────────────────────────
    # Calendly
    # ──────────────────────────────────────────────────────────────────────────────

    async def _calendly_list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
    ) -> List[Dict]:
        """List events from Calendly."""
        session = await self._get_session()
        headers = {"Authorization": f"Bearer {self.config.access_token.get_secret_value()}"}
        params = {}
        if time_min:
            params["min_start_time"] = time_min.isoformat() + "Z"
        if time_max:
            params["max_start_time"] = time_max.isoformat() + "Z"

        url = f"https://api.calendly.com/scheduled_events"
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("collection", [])
        return []

    # ──────────────────────────────────────────────────────────────────────────────
    # Cal.com
    # ──────────────────────────────────────────────────────────────────────────────

    async def _calcom_list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
    ) -> List[Dict]:
        """List events from Cal.com."""
        session = await self._get_session()
        headers = {"Authorization": f"Bearer {self.config.access_token.get_secret_value()}"}
        params = {}
        if time_min:
            params["start_time"] = time_min.isoformat() + "Z"
        if time_max:
            params["end_time"] = time_max.isoformat() + "Z"

        url = f"https://api.cal.com/v1/bookings"
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("bookings", [])
        return []

    # ──────────────────────────────────────────────────────────────────────────────
    # Generic Event Parsing
    # ──────────────────────────────────────────────────────────────────────────────

    def _parse_google_event(self, raw: Dict) -> Optional[CalendarEvent]:
        """Parse Google Calendar event."""
        try:
            start = raw.get("start", {})
            end = raw.get("end", {})
            start_time = datetime.fromisoformat(start.get("dateTime", start.get("date")).replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(end.get("dateTime", end.get("date")).replace("Z", "+00:00"))

            organizer = raw.get("organizer", {})
            attendees = []
            for a in raw.get("attendees", []):
                attendees.append({
                    "email": a.get("email"),
                    "name": a.get("displayName"),
                    "status": a.get("responseStatus"),
                    "role": "attendee",
                })

            return CalendarEvent(
                uuid=self._generate_uuid(),
                external_id=raw.get("id"),
                provider="google",
                title=raw.get("summary", "Untitled"),
                description=raw.get("description"),
                event_type=EventType.MEETING,
                location=raw.get("location"),
                video_url=raw.get("hangoutLink"),
                start_time=start_time,
                end_time=end_time,
                timezone=raw.get("timeZone", "UTC"),
                all_day="date" in raw.get("start", {}),
                is_recurring=bool(raw.get("recurringEventId")),
                recurrence_rule=None,
                organizer_email=organizer.get("email", ""),
                organizer_name=organizer.get("displayName"),
                attendees=attendees,
                attendee_count=len(attendees),
                status=raw.get("status", "confirmed"),
            )
        except Exception as e:
            self.logger.error(f"Parse Google event error: {e}")
        return None

    def _parse_outlook_event(self, raw: Dict) -> Optional[CalendarEvent]:
        """Parse Outlook Calendar event."""
        try:
            start_time = datetime.fromisoformat(raw["start"]["dateTime"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(raw["end"]["dateTime"].replace("Z", "+00:00"))

            organizer = raw.get("organizer", {}).get("emailAddress", {})
            attendees = []
            for a in raw.get("attendees", []):
                addr = a.get("emailAddress", {})
                attendees.append({
                    "email": addr.get("address"),
                    "name": addr.get("name"),
                    "status": a.get("status", {}).get("response"),
                    "role": "attendee",
                })

            return CalendarEvent(
                uuid=self._generate_uuid(),
                external_id=raw.get("id"),
                provider="outlook",
                title=raw.get("subject", "Untitled"),
                description=raw.get("bodyPreview"),
                event_type=EventType.MEETING,
                location=raw.get("location", {}).get("displayName"),
                video_url=raw.get("onlineMeeting", {}).get("joinUrl"),
                start_time=start_time,
                end_time=end_time,
                timezone=raw.get("start", {}).get("timeZone", "UTC"),
                all_day=raw.get("isAllDay", False),
                is_recurring=bool(raw.get("seriesMasterId")),
                organizer_email=organizer.get("address", ""),
                organizer_name=organizer.get("name"),
                attendees=attendees,
                attendee_count=len(attendees),
                status="confirmed" if not raw.get("isCancelled") else "cancelled",
            )
        except Exception as e:
            self.logger.error(f"Parse Outlook event error: {e}")
        return None

    def _parse_calendly_event(self, raw: Dict) -> Optional[CalendarEvent]:
        """Parse Calendly event."""
        try:
            start_time = datetime.fromisoformat(raw["start_time"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(raw["end_time"].replace("Z", "+00:00"))

            return CalendarEvent(
                uuid=self._generate_uuid(),
                external_id=raw.get("uri", "").split("/")[-1],
                provider="calendly",
                title=raw.get("name", "Meeting"),
                description=raw.get("description"),
                event_type=EventType.MEETING,
                location=raw.get("location", {}).get("location"),
                video_url=raw.get("location", {}).get("join_url"),
                start_time=start_time,
                end_time=end_time,
                timezone=raw.get("timezone", "UTC"),
                organizer_email=raw.get("event_memberships", [{}])[0].get("user_email", ""),
                attendees=[{"email": raw.get("invitee_email"), "name": raw.get("invitee_name"), "status": "confirmed", "role": "attendee"}],
                attendee_count=1,
                status="confirmed",
            )
        except Exception as e:
            self.logger.error(f"Parse Calendly event error: {e}")
        return None

    def _parse_calcom_event(self, raw: Dict) -> Optional[CalendarEvent]:
        """Parse Cal.com event."""
        try:
            start_time = datetime.fromisoformat(raw["startTime"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(raw["endTime"].replace("Z", "+00:00"))

            return CalendarEvent(
                uuid=self._generate_uuid(),
                external_id=str(raw.get("id")),
                provider="calcom",
                title=raw.get("title", "Booking"),
                description=raw.get("description"),
                event_type=EventType.MEETING,
                location=raw.get("location"),
                video_url=raw.get("meetingUrl"),
                start_time=start_time,
                end_time=end_time,
                timezone=raw.get("timeZone", "UTC"),
                organizer_email=raw.get("organizer", {}).get("email", ""),
                attendees=[{"email": raw.get("attendee", {}).get("email"), "name": raw.get("attendee", {}).get("name"), "status": "confirmed", "role": "attendee"}],
                attendee_count=1,
                status=raw.get("status", "confirmed"),
            )
        except Exception as e:
            self.logger.error(f"Parse Cal.com event error: {e}")
        return None

    def _generate_uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())

    # ──────────────────────────────────────────────────────────────────────────────
    # Sync Operations
    # ──────────────────────────────────────────────────────────────────────────────

    async def _sync_loop(self):
        """Periodic calendar sync."""
        while self._running:
            try:
                await self.sync_events()
                await asyncio.sleep(self.config.sync_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Calendar sync error: {e}")
                await asyncio.sleep(300)

    async def sync_events(self) -> Dict[str, Any]:
        """Sync events from calendar provider."""
        stats = {"fetched": 0, "created": 0, "updated": 0, "errors": []}

        time_min = datetime.utcnow() - timedelta(days=self.config.sync_past_days)
        time_max = datetime.utcnow() + timedelta(days=self.config.sync_future_days)

        events = []
        if self.config.provider == "google":
            events = await self._google_list_events("primary", time_min, time_max)
            for raw in events:
                parsed = self._parse_google_event(raw)
                if parsed:
                    await self._upsert_event(parsed)
                    stats["fetched"] += 1
        elif self.config.provider == "outlook":
            events = await self._outlook_list_events("primary", time_min, time_max)
            for raw in events:
                parsed = self._parse_outlook_event(raw)
                if parsed:
                    await self._upsert_event(parsed)
                    stats["fetched"] += 1
        elif self.config.provider == "calendly":
            events = await self._calendly_list_events(time_min, time_max)
            for raw in events:
                parsed = self._parse_calendly_event(raw)
                if parsed:
                    await self._upsert_event(parsed)
                    stats["fetched"] += 1
        elif self.config.provider == "calcom":
            events = await self._calcom_list_events(time_min, time_max)
            for raw in events:
                parsed = self._parse_calcom_event(raw)
                if parsed:
                    await self._upsert_event(parsed)
                    stats["fetched"] += 1

        return stats

    async def _upsert_event(self, event: CalendarEvent):
        """Upsert event in repository."""
        await self.repository.upsert_calendar_event(event)

    async def get_upcoming_events(
        self,
        organizer_email: str,
        days: int = 7,
    ) -> List[CalendarEvent]:
        """Get upcoming events for organizer."""
        return await self.repository.get_upcoming_events(organizer_email, hours=days * 24)

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        video_url: Optional[str] = None,
    ) -> Optional[CalendarEvent]:
        """Create a new calendar event."""
        event_data = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": a} for a in (attendees or [])],
        }

        if self.config.provider == "google":
            raw = await self._google_create_event("primary", event_data)
            if raw:
                return self._parse_google_event(raw)

        return None

    # ──────────────────────────────────────────────────────────────────────────────
    # Webhook Handling
    # ──────────────────────────────────────────────────────────────────────────────

    async def handle_webhook(self, request: Any) -> Dict[str, Any]:
        """Handle calendar webhook."""
        # Verify signature if configured
        # Parse event
        # Sync changed event
        pass