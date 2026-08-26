"""Communication Gateway — Unified messaging and notification hub."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from axiom.integrations.layer import IntegrationLayer
from axiom.integrations.comms import (
    SlackProvider, SlackConfig,
    EmailProvider, EmailConfig,
    WhatsAppProvider, WhatsAppConfig,
    CalendarProvider, CalendarConfig,
    NotificationRouter, NotificationConfig,
)
from axiom.runtime.logging import RuntimeLogger


class GatewayConfig(BaseModel):
    """Communication gateway configuration."""

    slack: Optional[SlackConfig] = None
    email: Optional[EmailConfig] = None
    whatsapp: Optional[WhatsAppConfig] = None
    calendar: Optional[CalendarConfig] = None
    notifications: Optional[NotificationConfig] = None

    # Defaults
    default_slack_channel: str = "#general"
    default_email_sender: str = "noreply@axiom.ai"


class CommunicationGateway:
    """Unified communication gateway."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        repositories,  # Dict with comms, bleval, market, research repositories
        config: Optional[GatewayConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repositories = repositories
        self.config = config or GatewayConfig()
        self.logger = logger or RuntimeLogger()

        # Providers
        self.slack: Optional[SlackProvider] = None
        self.email: Optional[EmailProvider] = None
        self.whatsapp: Optional[WhatsAppProvider] = None
        self.calendar: Optional[CalendarProvider] = None
        self.notifications: Optional[NotificationRouter] = None

        self._running = False
        self._initialized = False

    async def initialize(self):
        """Initialize all providers."""
        if self._initialized:
            return

        # Initialize Slack
        if self.config.slack and self.config.slack.enabled:
            self.slack = SlackProvider(
                self.integration_layer,
                self.config.slack,
                self.repositories.get("comms"),
                self.logger
            )
            await self.slack.start()

        # Initialize Email
        if self.config.email and self.config.email.enabled:
            self.email = EmailProvider(
                self.integration_layer,
                self.config.email,
                self.repositories.get("comms"),
                self.logger
            )
            await self.email.start()

        # Initialize WhatsApp
        if self.config.whatsapp and self.config.whatsapp.enabled:
            self.whatsapp = WhatsAppProvider(
                self.integration_layer,
                self.config.whatsapp,
                self.repositories.get("comms"),
                self.logger
            )
            await self.whatsapp.start()

        # Initialize Calendar
        if self.config.calendar and self.config.calendar.enabled:
            self.calendar = CalendarProvider(
                self.integration_layer,
                self.config.calendar,
                self.repositories.get("comms"),
                self.logger
            )
            await self.calendar.start()

        # Initialize Notification Router
        if self.config.notifications:
            self.notifications = NotificationRouter(
                self.integration_layer,
                self.repositories.get("comms"),
                self.slack,
                self.email,
                self.whatsapp,
                self.config.notifications,
                self.logger
            )
            await self.notifications.start()

        self._initialized = True
        self.logger.info("Communication gateway initialized")

    async def start(self):
        """Start gateway."""
        await self.initialize()
        self._running = True
        self.logger.info("Communication gateway started")

    async def stop(self):
        """Stop gateway."""
        self._running = False

        if self.notifications:
            await self.notifications.stop()
        if self.calendar:
            await self.calendar.stop()
        if self.whatsapp:
            await self.whatsapp.stop()
        if self.email:
            await self.email.stop()
        if self.slack:
            await self.slack.stop()

        self.logger.info("Communication gateway stopped")

    # ──────────────────────────────────────────────────────────────────────────────
    # Slack Shortcuts
    # ──────────────────────────────────────────────────────────────────────────────

    async def slack_send(
        self,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
    ) -> Optional[Dict]:
        if not self.slack:
            return None
        return await self.slack.send_message(channel, text, blocks, thread_ts)

    async def slack_dm(self, user_id: str, text: str, blocks: Optional[List[Dict]] = None) -> Optional[Dict]:
        if not self.slack:
            return None
        return await self.slack.send_dm(user_id, text, blocks)

    # ──────────────────────────────────────────────────────────────────────────────
    # Email Shortcuts
    # ──────────────────────────────────────────────────────────────────────────────

    async def email_send(
        self,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.email:
            return {"status": "not_configured"}
        return await self.email.send_email(to, subject, body_text, body_html, **kwargs)

    async def email_send_templated(
        self,
        to: List[str],
        template_name: str,
        data: Dict[str, Any],
        subject_template: str,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.email:
            return {"status": "not_configured"}
        return await self.email.send_templated_email(to, template_name, data, subject_template, **kwargs)

    # ──────────────────────────────────────────────────────────────────────────────
    # WhatsApp Shortcuts
    # ──────────────────────────────────────────────────────────────────────────────

    async def whatsapp_send(self, to: str, body: str, media: Optional[List[str]] = None) -> Dict[str, Any]:
        if not self.whatsapp:
            return {"status": "not_configured"}
        return await self.whatsapp.send_message(to, body, media)

    async def whatsapp_template(self, to: str, template: str, lang: str = "en", vars: Optional[List[str]] = None) -> Dict[str, Any]:
        if not self.whatsapp:
            return {"status": "not_configured"}
        return await self.whatsapp.send_template(to, template, lang, vars)

    # ──────────────────────────────────────────────────────────────────────────────
    # Calendar Shortcuts
    # ──────────────────────────────────────────────────────────────────────────────

    async def calendar_sync(self) -> Dict[str, Any]:
        if not self.calendar:
            return {"status": "not_configured"}
        return await self.calendar.sync_events()

    async def calendar_upcoming(self, organizer: str, days: int = 7) -> List[Any]:
        if not self.calendar:
            return []
        return await self.calendar.get_upcoming_events(organizer, days)

    async def calendar_create(self, **kwargs) -> Optional[Any]:
        if not self.calendar:
            return None
        return await self.calendar.create_event(**kwargs)

    # ──────────────────────────────────────────────────────────────────────────────
    # Notification Shortcuts
    # ──────────────────────────────────────────────────────────────────────────────

    async def notify(
        self,
        recipient: str,
        title: str,
        body: str,
        event_type: str,
        priority: str = "normal",
        **kwargs
    ):
        if not self.notifications:
            return
        from axiom.data.models import NotificationPriority
        priority_enum = NotificationPriority(priority.lower())
        return await self.notifications.send_notification(
            recipient_id=recipient,
            title=title,
            body=body,
            event_type=event_type,
            priority=priority_enum,
            **kwargs
        )

    async def notify_lead(self, lead_id: int, owner_id: str, data: Dict):
        if not self.notifications:
            return
        return await self.notifications.notify_lead_created(lead_id, owner_id, data)

    async def notify_deal(self, deal_id: int, owner_id: str, data: Dict):
        if not self.notifications:
            return
        return await self.notifications.notify_deal_won(deal_id, owner_id, data)

    async def notify_meeting(self, event_id: int, attendees: List[str], data: Dict):
        if not self.notifications:
            return
        return await self.notifications.notify_meeting_scheduled(event_id, attendees, data)

    async def notify_signal(self, signal_id: int, recipient: str, data: Dict):
        if not self.notifications:
            return
        return await self.notifications.notify_trade_signal(signal_id, recipient, data)

    # ──────────────────────────────────────────────────────────────────────────────
    # Health & Status
    # ──────────────────────────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all communication channels."""
        health = {
            "gateway_running": self._running,
            "initialized": self._initialized,
            "channels": {},
        }

        if self.slack:
            health["channels"]["slack"] = {"configured": True, "running": self.slack._running}
        if self.email:
            health["channels"]["email"] = {"configured": True, "running": self.email._running}
        if self.whatsapp:
            health["channels"]["whatsapp"] = {"configured": True, "running": self.whatsapp._running}
        if self.calendar:
            health["channels"]["calendar"] = {"configured": True, "running": self.calendar._running}
        if self.notifications:
            health["channels"]["notifications"] = {"configured": True, "running": self.notifications._running}

        return health