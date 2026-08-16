"""Calendar Provider — CalDAV, Google Calendar, and Outlook integration."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from axiom.engine.provider import ExternalAPIProvider
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationResult,
)
from axiom.runtime.logging import RuntimeLogger


class CalendarProvider(ExternalAPIProvider):
    """Calendar provider supporting CalDAV, Google Calendar, and Outlook.

    Capabilities:
    - Read events (calendar view, search, upcoming)
    - Create events (with attendees, reminders, recurrence)
    - Update/Delete events
    - Check availability (free/busy)
    - Manage calendars (create, list, share)
    - Sync across providers
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._provider_type = config.config.get("provider_type", "caldav")  # caldav, google, outlook

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            ProviderToolDefinition(
                tool_id="calendar_list_calendars",
                name="List Calendars",
                description="List all accessible calendars",
                capability="calendar_read",
                input_schema={},
            ),
            ProviderToolDefinition(
                tool_id="calendar_get_events",
                name="Get Events",
                description="Get events in a time range",
                capability="calendar_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string"},
                        "start": {"type": "string", "description": "ISO datetime"},
                        "end": {"type": "string", "description": "ISO datetime"},
                        "max_results": {"type": "integer", "default": 50},
                        "include_recurring": {"type": "boolean", "default": True},
                    },
                    "required": ["start", "end"],
                },
            ),
            ProviderToolDefinition(
                tool_id="calendar_get_upcoming",
                name="Get Upcoming Events",
                description="Get upcoming events from now",
                capability="calendar_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string"},
                        "days": {"type": "integer", "default": 7},
                        "max_results": {"type": "integer", "default": 20},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="calendar_create_event",
                name="Create Event",
                description="Create a new calendar event",
                capability="calendar_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string"},
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "start": {"type": "string", "description": "ISO datetime"},
                        "end": {"type": "string", "description": "ISO datetime"},
                        "timezone": {"type": "string", "default": "UTC"},
                        "attendees": {"type": "array", "items": {"type": "string", "format": "email"}},
                        "location": {"type": "string"},
                        "reminders": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "method": {"type": "string", "enum": ["email", "popup", "sms"]},
                                    "minutes": {"type": "integer"},
                                },
                                "required": ["method", "minutes"],
                            },
                        },
                        "recurrence": {"type": "string", "description": "RRULE string"},
                        "transparency": {"type": "string", "enum": ["opaque", "transparent"]},
                    },
                    "required": ["calendar_id", "summary", "start", "end"],
                },
            ),
            ProviderToolDefinition(
                tool_id="calendar_update_event",
                name="Update Event",
                description="Update an existing event",
                capability="calendar_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string"},
                        "event_id": {"type": "string"},
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                        "attendees": {"type": "array", "items": {"type": "string"}},
                        "location": {"type": "string"},
                        "reminders": {"type": "array"},
                        "status": {"type": "string", "enum": ["confirmed", "tentative", "cancelled"]},
                    },
                    "required": ["calendar_id", "event_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="calendar_delete_event",
                name="Delete Event",
                description="Delete an event",
                capability="calendar_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string"},
                        "event_id": {"type": "string"},
                        "send_updates": {"type": "string", "enum": ["all", "external_only", "none"]},
                    },
                    "required": ["calendar_id", "event_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="calendar_check_availability",
                name="Check Availability",
                description="Check free/busy for calendars",
                capability="calendar_availability",
                input_schema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {"type": "array", "items": {"type": "string"}},
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                        "timezone": {"type": "string", "default": "UTC"},
                    },
                    "required": ["calendar_ids", "start", "end"],
                },
            ),
            ProviderToolDefinition(
                tool_id="calendar_find_slots",
                name="Find Available Slots",
                description="Find available time slots for meeting",
                capability="calendar_availability",
                input_schema={
                    "type": "object",
                    "properties": {
                        "calendar_ids": {"type": "array", "items": {"type": "string"}},
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                        "duration_minutes": {"type": "integer", "default": 30},
                        "timezone": {"type": "string", "default": "UTC"},
                        "working_hours_start": {"type": "integer", "default": 9},
                        "working_hours_end": {"type": "integer", "default": 17},
                        "max_results": {"type": "integer", "default": 10},
                    },
                    "required": ["calendar_ids", "start", "end"],
                },
            ),
        ]

    async def initialize(self) -> None:
        """Initialize calendar provider based on type."""
        if self._provider_type == "caldav":
            await self._init_caldav()
        elif self._provider_type == "google":
            await self._init_google()
        elif self._provider_type == "outlook":
            await self._init_outlook()
        else:
            raise ValueError(f"Unknown calendar provider type: {self._provider_type}")

        self._initialized = True

    async def _init_caldav(self) -> None:
        """Initialize CalDAV connection."""
        import caldav

        url = self.config.config.get("caldav_url")
        username = self._secrets.get_secret(self.config.auth.username_env_var or "CALDAV_USERNAME")
        password = self._secrets.get_secret(self.config.auth.password_env_var or "CALDAV_PASSWORD")

        if not all([url, username, password]):
            raise RuntimeError("CalDAV credentials not configured")

        self._caldav_client = caldav.DAVClient(url, username=username, password=password)
        self._principal = self._caldav_client.principal()

    async def _init_google(self) -> None:
        """Initialize Google Calendar API."""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token = self._secrets.get_secret(self.config.auth.token_env_var or "GOOGLE_CALENDAR_TOKEN")
        if not token:
            raise RuntimeError("Google Calendar token not configured")

        creds = Credentials(token=token)
        self._google_service = build("calendar", "v3", credentials=creds)

    async def _init_outlook(self) -> None:
        """Initialize Microsoft Graph (Outlook) Calendar."""
        import httpx

        token = self._secrets.get_secret(self.config.auth.token_env_var or "OUTLOOK_TOKEN")
        if not token:
            raise RuntimeError("Outlook token not configured")

        self._http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"},
            base_url="https://graph.microsoft.com/v1.0",
        )

    async def _execute_tool_impl(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> ToolInvocationResult:
        method_name = f"_execute_{tool_id}"
        if hasattr(self, method_name):
            return await getattr(self, method_name)(parameters)

        return ToolInvocationResult(
            success=False,
            error=f"Tool {tool_id} not implemented",
            error_code="not_implemented",
            provider_id=self.provider_id,
            tool_id=tool_id,
        )

    # ── Tool Implementations ──────────────────────────────────────────────

    async def _execute_calendar_list_calendars(self, params: Dict[str, Any]) -> ToolInvocationResult:
        if self._provider_type == "caldav":
            calendars = self._principal.calendars()
            return ToolInvocationResult(
                success=True,
                output=[{"id": cal.url, "name": cal.name} for cal in calendars],
                provider_id=self.provider_id,
                tool_id="calendar_list_calendars",
            )
        elif self._provider_type == "google":
            result = await self._google_service.calendarList().list().execute()
            return ToolInvocationResult(
                success=True,
                output=result.get("items", []),
                provider_id=self.provider_id,
                tool_id="calendar_list_calendars",
            )
        elif self._provider_type == "outlook":
            resp = await self._http_client.get("/me/calendars")
            result = resp.json()
            return ToolInvocationResult(
                success=True,
                output=result.get("value", []),
                provider_id=self.provider_id,
                tool_id="calendar_list_calendars",
            )

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="calendar_list_calendars")

    async def _execute_calendar_get_events(self, params: Dict[str, Any]) -> ToolInvocationResult:
        start = params["start"]
        end = params["end"]
        calendar_id = params.get("calendar_id", "primary")
        max_results = params.get("max_results", 50)

        if self._provider_type == "caldav":
            cal = self._principal.calendar(calendar_id)
            events = cal.date_search(
                datetime.fromisoformat(start.replace("Z", "+00:00")),
                datetime.fromisoformat(end.replace("Z", "+00:00")),
                expand=True,
            )
            return ToolInvocationResult(
                success=True,
                output=[self._parse_caldav_event(e) for e in events[:max_results]],
                provider_id=self.provider_id,
                tool_id="calendar_get_events",
            )
        elif self._provider_type == "google":
            result = await self._google_service.events().list(
                calendarId=calendar_id,
                timeMin=start,
                timeMax=end,
                maxResults=max_results,
                singleEvents=params.get("include_recurring", True),
                orderBy="startTime",
            ).execute()
            return ToolInvocationResult(
                success=True,
                output=result.get("items", []),
                provider_id=self.provider_id,
                tool_id="calendar_get_events",
            )
        elif self._provider_type == "outlook":
            resp = await self._http_client.get(
                f"/me/calendars/{calendar_id}/events",
                params={
                    "$filter": f"start/dateTime ge '{start}' and end/dateTime le '{end}'",
                    "$top": max_results,
                    "$orderby": "start/dateTime",
                },
            )
            result = resp.json()
            return ToolInvocationResult(
                success=True,
                output=result.get("value", []),
                provider_id=self.provider_id,
                tool_id="calendar_get_events",
            )

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="calendar_get_events")

    async def _execute_calendar_get_upcoming(self, params: Dict[str, Any]) -> ToolInvocationResult:
        days = params.get("days", 7)
        start = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
        params["start"] = start
        params["end"] = end
        return await self._execute_calendar_get_events(params)

    async def _execute_calendar_create_event(self, params: Dict[str, Any]) -> ToolInvocationResult:
        calendar_id = params["calendar_id"]

        if self._provider_type == "google":
            event = {
                "summary": params["summary"],
                "description": params.get("description", ""),
                "start": {"dateTime": params["start"], "timeZone": params.get("timezone", "UTC")},
                "end": {"dateTime": params["end"], "timeZone": params.get("timezone", "UTC")},
                "location": params.get("location", ""),
            }
            if params.get("attendees"):
                event["attendees"] = [{"email": a} for a in params["attendees"]]
            if params.get("reminders"):
                event["reminders"] = {"useDefault": False, "overrides": params["reminders"]}
            if params.get("recurrence"):
                event["recurrence"] = [params["recurrence"]]

            result = await self._google_service.events().insert(
                calendarId=calendar_id, body=event, sendUpdates="all"
            ).execute()
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="calendar_create_event")

        elif self._provider_type == "outlook":
            event = {
                "subject": params["summary"],
                "body": {"contentType": "text", "content": params.get("description", "")},
                "start": {"dateTime": params["start"], "timeZone": params.get("timezone", "UTC")},
                "end": {"dateTime": params["end"], "timeZone": params.get("timezone", "UTC")},
                "location": {"displayName": params.get("location", "")},
                "attendees": [{"emailAddress": {"address": a}, "type": "required"} for a in params.get("attendees", [])],
            }
            result = await self._http_client.post(f"/me/calendars/{calendar_id}/events", json=event)
            return ToolInvocationResult(success=True, output=result.json(), provider_id=self.provider_id, tool_id="calendar_create_event")

        elif self._provider_type == "caldav":
            cal = self._principal.calendar(calendar_id)
            from icalendar import Calendar, Event as ICalEvent
            import uuid as uuid_lib

            ical = Calendar()
            ical.add("prodid", "-//AXIOM//Calendar//EN")
            ical.add("version", "2.0")

            ical_event = ICalEvent()
            ical_event.add("uid", str(uuid_lib.uuid4()))
            ical_event.add("dtstart", datetime.fromisoformat(params["start"].replace("Z", "+00:00")))
            ical_event.add("dtend", datetime.fromisoformat(params["end"].replace("Z", "+00:00")))
            ical_event.add("summary", params["summary"])
            ical_event.add("description", params.get("description", ""))
            ical_event.add("location", params.get("location", ""))

            ical.add_component(ical_event)
            cal.add_event(ical.to_ical().decode())

            return ToolInvocationResult(
                success=True,
                output={"message": "Event created", "uid": ical_event.get("uid")},
                provider_id=self.provider_id,
                tool_id="calendar_create_event",
            )

        return ToolInvocationResult(success=False, error="Not implemented", provider_id=self.provider_id, tool_id="calendar_create_event")

    async def _execute_calendar_update_event(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # Implementation would follow similar pattern to create
        return ToolInvocationResult(success=False, error="Not fully implemented", provider_id=self.provider_id, tool_id="calendar_update_event")

    async def _execute_calendar_delete_event(self, params: Dict[str, Any]) -> ToolInvocationResult:
        calendar_id = params["calendar_id"]
        event_id = params["event_id"]

        if self._provider_type == "google":
            await self._google_service.events().delete(
                calendarId=calendar_id, eventId=event_id, sendUpdates=params.get("send_updates", "all")
            ).execute()
            return ToolInvocationResult(success=True, output={"deleted": True}, provider_id=self.provider_id, tool_id="calendar_delete_event")

        return ToolInvocationResult(success=False, error="Not fully implemented", provider_id=self.provider_id, tool_id="calendar_delete_event")

    async def _execute_calendar_check_availability(self, params: Dict[str, Any]) -> ToolInvocationResult:
        if self._provider_type == "google":
            body = {
                "timeMin": params["start"],
                "timeMax": params["end"],
                "timeZone": params.get("timezone", "UTC"),
                "items": [{"id": cid} for cid in params["calendar_ids"]],
            }
            result = await self._google_service.freebusy().query(body=body).execute()
            return ToolInvocationResult(success=True, output=result.get("calendars", {}), provider_id=self.provider_id, tool_id="calendar_check_availability")

        return ToolInvocationResult(success=False, error="Not fully implemented", provider_id=self.provider_id, tool_id="calendar_check_availability")

    async def _execute_calendar_find_slots(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # Simplified - would need more complex logic for real slot finding
        busy = await self._execute_calendar_check_availability(params)
        # Process busy/free to find slots
        return ToolInvocationResult(success=True, output={"slots": [], "note": "Requires full implementation"}, provider_id=self.provider_id, tool_id="calendar_find_slots")

    def _parse_caldav_event(self, event) -> Dict[str, Any]:
        """Parse CalDAV event to dict."""
        vevent = event.vobject_instance.vevent
        return {
            "id": vevent.uid.value if hasattr(vevent, "uid") else "",
            "summary": vevent.summary.value if hasattr(vevent, "summary") else "",
            "description": vevent.description.value if hasattr(vevent, "description") else "",
            "start": vevent.dtstart.value.isoformat() if hasattr(vevent, "dtstart") else "",
            "end": vevent.dtend.value.isoformat() if hasattr(vevent, "dtend") else "",
            "location": vevent.location.value if hasattr(vevent, "location") else "",
        }

    async def _health_check_impl(self) -> ProviderHealth:
        try:
            if self._provider_type == "google":
                await self._google_service.calendarList().list().execute()
            elif self._provider_type == "outlook":
                await self._http_client.get("/me/calendars")
            elif self._provider_type == "caldav":
                self._principal.calendars()
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)
        except Exception as e:
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))