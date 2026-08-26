"""Notification Router — Multi-channel notification delivery."""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from pydantic import BaseModel, Field

from axiom.data.models import (
    Notification,
    ChannelType,
    NotificationPriority,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.integrations.comms import SlackProvider, EmailProvider, WhatsAppProvider
from axiom.runtime.logging import RuntimeLogger


class NotificationChannel(Enum):
    """Notification delivery channel."""

    SLACK = "slack"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationConfig(BaseModel):
    """Notification routing configuration."""

    # Default channels per priority
    priority_channels: Dict[NotificationPriority, List[NotificationChannel]] = Field(
        default_factory=lambda: {
            NotificationPriority.LOW: [NotificationChannel.IN_APP],
            NotificationPriority.NORMAL: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationPriority.HIGH: [NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.SLACK],
            NotificationPriority.URGENT: [NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WHATSAPP],
            NotificationPriority.CRITICAL: [NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WHATSAPP, NotificationChannel.SMS],
        }
    )

    # Channel-specific config
    slack_channels: Dict[str, str] = Field(default_factory=dict)  # event_type -> channel_id
    email_templates: Dict[str, str] = Field(default_factory=dict)  # event_type -> template
    whatsapp_templates: Dict[str, str] = Field(default_factory=dict)

    # Delivery
    max_retries: int = 3
    retry_delay_seconds: int = 60
    batch_size: int = 50

    # Quiet hours
    quiet_hours_enabled: bool = True
    quiet_start: str = "22:00"
    quiet_end: str = "08:00"
    quiet_timezone: str = "UTC"

    # Deduplication
    dedup_window_minutes: int = 60


class DeliveryResult(BaseModel):
    """Result of notification delivery."""

    channel: NotificationChannel
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    delivered_at: Optional[datetime] = None


class NotificationRouter:
    """Routes notifications to appropriate channels."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        repository,  # CommsRepository
        slack_provider: Optional[SlackProvider] = None,
        email_provider: Optional[EmailProvider] = None,
        whatsapp_provider: Optional[WhatsAppProvider] = None,
        config: Optional[NotificationConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repository = repository
        self.slack = slack_provider
        self.email = email_provider
        self.whatsapp = whatsapp_provider
        self.config = config or NotificationConfig()
        self.logger = logger or RuntimeLogger()

        self._delivery_handlers: Dict[NotificationChannel, Callable] = {}
        self._pending_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._dedup_cache: Dict[str, datetime] = {}

    async def start(self):
        """Start notification router."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        self.logger.info("Notification router started")

    async def stop(self):
        """Stop notification router."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Notification router stopped")

    async def send_notification(
        self,
        recipient_id: str,
        title: str,
        body: str,
        event_type: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        event_id: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create and queue a notification."""
        # Determine channels
        if channels is None:
            channels = self.config.priority_channels.get(priority, [NotificationChannel.IN_APP])

        # Check quiet hours
        if self._is_quiet_hours() and priority not in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
            # Delay until quiet hours end
            scheduled_for = self._get_next_active_time()

        # Check deduplication
        dedup_key = f"{recipient_id}:{event_type}:{event_id or ''}"
        if dedup_key in self._dedup_cache:
            last_sent = self._dedup_cache[dedup_key]
            if (datetime.utcnow() - last_sent).total_seconds() < self.config.dedup_window_minutes * 60:
                self.logger.debug(f"Notification deduplicated: {dedup_key}")
                # Return existing or skip
                pass

        # Create notification record
        notification = await self.repository.create_notification(
            title=title,
            body=body,
            recipient_id=recipient_id,
            channels=[c.value for c in channels],
            priority=priority,
            event_type=event_type,
            event_id=event_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            action_url=action_url,
            action_text=action_text,
            scheduled_for=scheduled_for,
            expires_at=expires_at,
            tags=tags or [],
            extra_data=extra_data or {},
        )

        # Queue for delivery
        await self._pending_queue.put(notification.id)

        # Update dedup cache
        self._dedup_cache[dedup_key] = datetime.utcnow()

        return notification

    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours."""
        if not self.config.quiet_hours_enabled:
            return False

        now = datetime.utcnow().time()
        start = datetime.strptime(self.config.quiet_start, "%H:%M").time()
        end = datetime.strptime(self.config.quiet_end, "%H:%M").time()

        if start < end:
            return start <= now < end
        else:  # Crosses midnight
            return now >= start or now < end

    def _get_next_active_time(self) -> datetime:
        """Get next time after quiet hours."""
        now = datetime.utcnow()
        end = datetime.strptime(self.config.quiet_end, "%H:%M").time()
        next_active = datetime.combine(now.date(), end)
        if next_active <= now:
            next_active += timedelta(days=1)
        return next_active

    async def _worker_loop(self):
        """Process notification queue."""
        while self._running:
            try:
                notification_id = await asyncio.wait_for(
                    self._pending_queue.get(), timeout=5.0
                )
                await self._deliver_notification(notification_id)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Notification worker error: {e}")
                await asyncio.sleep(1)

    async def _deliver_notification(self, notification_id: int):
        """Deliver notification to all channels."""
        notification = await self.repository.get_notification(notification_id)
        if not notification:
            return

        if notification.expires_at and notification.expires_at < datetime.utcnow():
            self.logger.debug(f"Notification {notification_id} expired")
            return

        results = []
        for channel_str in notification.channels:
            channel = NotificationChannel(channel_str)
            result = await self._deliver_to_channel(notification, channel)
            results.append(result)

        # Update delivery status
        delivery_status = {r.channel.value: {"success": r.success, "message_id": r.message_id, "error": r.error} for r in results}
        await self.repository.mark_notification_sent(notification_id, delivery_status)

        # Check if all failed
        if all(not r.success for r in results):
            self.logger.error(f"All channels failed for notification {notification_id}")

    async def _deliver_to_channel(
        self, notification: Notification, channel: NotificationChannel
    ) -> DeliveryResult:
        """Deliver to specific channel."""
        try:
            if channel == NotificationChannel.SLACK and self.slack:
                return await self._deliver_slack(notification)
            elif channel == NotificationChannel.EMAIL and self.email:
                return await self._deliver_email(notification)
            elif channel == NotificationChannel.WHATSAPP and self.whatsapp:
                return await self._deliver_whatsapp(notification)
            elif channel == NotificationChannel.IN_APP:
                return await self._deliver_in_app(notification)
            elif channel == NotificationChannel.WEBHOOK:
                return await self._deliver_webhook(notification)
            else:
                return DeliveryResult(channel=channel, success=False, error="Channel not configured")
        except Exception as e:
            return DeliveryResult(channel=channel, success=False, error=str(e))

    async def _deliver_slack(self, notification: Notification) -> DeliveryResult:
        """Deliver via Slack."""
        channel_id = self.config.slack_channels.get(notification.event_type, "#general")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": notification.title, "emoji": True}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": notification.body}
            }
        ]

        if notification.action_url and notification.action_text:
            blocks.append({
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": notification.action_text},
                    "url": notification.action_url,
                    "style": "primary" if notification.priority in [NotificationPriority.URGENT, NotificationPriority.CRITICAL] else "default"
                }]
            })

        result = await self.slack.send_message(channel_id, blocks=blocks)
        if result:
            return DeliveryResult(channel=NotificationChannel.SLACK, success=True, message_id=result.get("ts"))
        return DeliveryResult(channel=NotificationChannel.SLACK, success=False, error="Send failed")

    async def _deliver_email(self, notification: Notification) -> DeliveryResult:
        """Deliver via Email."""
        # Would get recipient email from user profile
        to_email = f"{notification.recipient_id}@example.com"  # Placeholder

        template = self.config.email_templates.get(notification.event_type, "")
        if template:
            body_html = template.replace("{{title}}", notification.title).replace("{{body}}", notification.body)
            if notification.action_url and notification.action_text:
                body_html += f'<p><a href="{notification.action_url}">{notification.action_text}</a></p>'
        else:
            body_html = f"<h2>{notification.title}</h2><p>{notification.body}</p>"

        result = await self.email.send_email(
            to_emails=[to_email],
            subject=notification.title,
            body_html=body_html,
        )
        if result.get("status") == "sent":
            return DeliveryResult(channel=NotificationChannel.EMAIL, success=True, message_id=result.get("message_id"))
        return DeliveryResult(channel=NotificationChannel.EMAIL, success=False, error=result.get("error"))

    async def _deliver_whatsapp(self, notification: Notification) -> DeliveryResult:
        """Deliver via WhatsApp."""
        # Would get recipient WhatsApp from profile
        to_number = "+15551234567"  # Placeholder

        template = self.config.whatsapp_templates.get(notification.event_type, "")
        body = template.replace("{{title}}", notification.title).replace("{{body}}", notification.body) if template else f"*{notification.title}*\n{notification.body}"

        result = await self.whatsapp.send_message(to_number, body)
        if result.get("status") == "sent":
            return DeliveryResult(channel=NotificationChannel.WHATSAPP, success=True, message_id=result.get("message_sid"))
        return DeliveryResult(channel=NotificationChannel.WHATSAPP, success=False, error=result.get("error"))

    async def _deliver_in_app(self, notification: Notification) -> DeliveryResult:
        """Deliver in-app (already stored in DB)."""
        return DeliveryResult(channel=NotificationChannel.IN_APP, success=True, delivered_at=datetime.utcnow())

    async def _deliver_webhook(self, notification: Notification) -> DeliveryResult:
        """Deliver via webhook."""
        # Would POST to configured webhook URL
        pass

    async def get_pending_notifications(self) -> List[Notification]:
        """Get notifications ready to send."""
        return await self.repository.get_pending_notifications()

    async def process_due_notifications(self):
        """Process all due notifications."""
        pending = await self.get_pending_notifications()
        for notif in pending:
            await self._pending_queue.put(notif.id)

    # Convenience methods for common events
    async def notify_lead_created(self, lead_id: int, owner_id: str, lead_data: Dict):
        await self.send_notification(
            recipient_id=owner_id,
            title="New Lead",
            body=f"Lead {lead_data.get('email')} from {lead_data.get('source', 'unknown')}",
            event_type="lead_created",
            priority=NotificationPriority.NORMAL,
            event_id=str(lead_id),
            related_entity_type="lead",
            related_entity_id=str(lead_id),
            action_url=f"/leads/{lead_id}",
            action_text="View Lead",
        )

    async def notify_deal_won(self, deal_id: int, owner_id: str, deal_data: Dict):
        amount = deal_data.get("amount", 0)
        await self.send_notification(
            recipient_id=owner_id,
            title="Deal Won! 🎉",
            body=f"Deal '{deal_data.get('name')}' worth ${amount:,.2f} closed.",
            event_type="deal_won",
            priority=NotificationPriority.HIGH,
            event_id=str(deal_id),
            related_entity_type="deal",
            related_entity_id=str(deal_id),
            action_url=f"/deals/{deal_id}",
            action_text="View Deal",
        )

    async def notify_meeting_scheduled(self, event_id: int, attendee_ids: List[str], event_data: Dict):
        for attendee in attendee_ids:
            await self.send_notification(
                recipient_id=attendee,
                title="Meeting Scheduled",
                body=f"Meeting '{event_data.get('title')}' on {event_data.get('start_time')}",
                event_type="meeting_scheduled",
                priority=NotificationPriority.NORMAL,
                event_id=str(event_id),
                related_entity_type="calendar_event",
                related_entity_id=str(event_id),
                action_url=f"/calendar/{event_id}",
                action_text="View Meeting",
            )

    async def notify_trade_signal(self, signal_id: int, recipient_id: str, signal_data: Dict):
        direction = signal_data.get("direction", "")
        symbol = signal_data.get("symbol", "")
        confidence = signal_data.get("confidence", 0)
        priority = NotificationPriority.URGENT if confidence > 0.85 else NotificationPriority.HIGH

        await self.send_notification(
            recipient_id=recipient_id,
            title=f"Trade Signal: {direction.upper()} {symbol}",
            body=f"Confidence: {confidence:.0%}. Entry: {signal_data.get('entry_price')}, SL: {signal_data.get('stop_loss')}, TP: {signal_data.get('take_profit')}",
            event_type="trade_signal",
            priority=priority,
            event_id=str(signal_id),
            related_entity_type="trade_signal",
            related_entity_id=str(signal_id),
            action_url=f"/trading/signals/{signal_id}",
            action_text="View Signal",
        )