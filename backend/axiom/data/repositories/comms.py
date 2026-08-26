"""COMMS Repository — Data access for Slack, Email, WhatsApp, Calendar, Notifications."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.data.models import (
    CommsBase,
    SlackMessage,
    EmailMessage,
    WhatsAppMessage,
    CalendarEvent,
    Notification,
    MessageDirection,
    MessageStatus,
    ChannelType,
    EventType,
    NotificationPriority,
)

if TYPE_CHECKING:
    from axiom.runtime.logging import RuntimeLogger


class CommsRepository:
    """Repository for COMMS domain operations."""

    def __init__(self, session: AsyncSession, logger: Optional["RuntimeLogger"] = None) -> None:
        self.session = session
        from axiom.runtime.logging import RuntimeLogger
        self.logger = logger or RuntimeLogger()

    # ──────────────────────────────────────────────────────────────────────────────
    # SLACK MESSAGES
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_slack_message(self, message: SlackMessage) -> SlackMessage:
        """Upsert Slack message by uuid."""
        existing = await self.get_slack_by_uuid(message.uuid)
        if existing:
            for key, value in message.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(message)
            await self.session.flush()
            return message

    async def get_slack_by_uuid(self, uuid: str) -> Optional[SlackMessage]:
        """Get Slack message by UUID."""
        query = select(SlackMessage).where(SlackMessage.uuid == uuid)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_slack_by_channel_ts(
        self, channel_id: str, ts: str
    ) -> Optional[SlackMessage]:
        """Get Slack message by channel and timestamp."""
        query = select(SlackMessage).where(
            and_(SlackMessage.channel_id == channel_id, SlackMessage.ts == ts)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_slack_messages(
        self,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_processed: Optional[bool] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SlackMessage]:
        """Get Slack messages with filters."""
        query = select(SlackMessage).order_by(desc(SlackMessage.posted_at))
        if channel_id:
            query = query.where(SlackMessage.channel_id == channel_id)
        if user_id:
            query = query.where(SlackMessage.user_id == user_id)
        if is_processed is not None:
            query = query.where(SlackMessage.is_processed == is_processed)
        if since:
            query = query.where(SlackMessage.posted_at >= since)
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_thread_messages(
        self, thread_ts: str, limit: int = 100
    ) -> List[SlackMessage]:
        """Get all messages in a thread."""
        query = (
            select(SlackMessage)
            .where(
                or_(
                    SlackMessage.ts == thread_ts,
                    SlackMessage.thread_ts == thread_ts,
                )
            )
            .order_by(SlackMessage.posted_at)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_slack_processed(
        self, uuid: str, error: Optional[str] = None
    ) -> Optional[SlackMessage]:
        """Mark Slack message as processed."""
        msg = await self.get_slack_by_uuid(uuid)
        if msg:
            msg.is_processed = True
            if error:
                msg.processing_error = error
            msg.updated_at = datetime.utcnow()
            await self.session.flush()
        return msg

    # ──────────────────────────────────────────────────────────────────────────────
    # EMAIL MESSAGES
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_email_message(self, message: EmailMessage) -> EmailMessage:
        """Upsert email by message_id."""
        existing = await self.get_email_by_message_id(message.message_id)
        if existing:
            for key, value in message.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(message)
            await self.session.flush()
            return message

    async def get_email_by_message_id(self, message_id: str) -> Optional[EmailMessage]:
        """Get email by message ID."""
        query = select(EmailMessage).where(EmailMessage.message_id == message_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_email_by_thread_id(self, thread_id: str) -> List[EmailMessage]:
        """Get all emails in a thread."""
        query = (
            select(EmailMessage)
            .where(EmailMessage.thread_id == thread_id)
            .order_by(EmailMessage.received_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_emails(
        self,
        direction: Optional[MessageDirection] = None,
        is_unread: Optional[bool] = None,
        is_processed: Optional[bool] = None,
        from_email: Optional[str] = None,
        sequence_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[EmailMessage]:
        """Get emails with filters."""
        query = select(EmailMessage).order_by(desc(EmailMessage.received_at))
        if direction:
            query = query.where(EmailMessage.direction == direction)
        if is_unread is not None:
            query = query.where(EmailMessage.is_unread == is_unread)
        if is_processed is not None:
            query = query.where(EmailMessage.is_processed == is_processed)
        if from_email:
            query = query.where(EmailMessage.from_email == from_email)
        if sequence_id:
            query = query.where(EmailMessage.sequence_id == sequence_id)
        if since:
            query = query.where(EmailMessage.received_at >= since)
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unread_emails_count(self) -> int:
        """Get count of unread inbound emails."""
        query = select(func.count(EmailMessage.id)).where(
            and_(
                EmailMessage.direction == MessageDirection.INBOUND,
                EmailMessage.is_unread == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_email_read(
        self, message_id: str, read_at: Optional[datetime] = None
    ) -> Optional[EmailMessage]:
        """Mark email as read."""
        email = await self.get_email_by_message_id(message_id)
        if email:
            email.is_unread = False
            email.opened_at = read_at or datetime.utcnow()
            email.updated_at = datetime.utcnow()
            await self.session.flush()
        return email

    async def mark_email_processed(
        self, message_id: str, error: Optional[str] = None
    ) -> Optional[EmailMessage]:
        """Mark email as processed."""
        email = await self.get_email_by_message_id(message_id)
        if email:
            email.is_processed = True
            if error:
                email.processing_error = error
            email.updated_at = datetime.utcnow()
            await self.session.flush()
        return email

    # ──────────────────────────────────────────────────────────────────────────────
    # WHATSAPP MESSAGES
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_whatsapp_message(self, message: WhatsAppMessage) -> WhatsAppMessage:
        """Upsert WhatsApp message by message_sid."""
        existing = await self.get_whatsapp_by_sid(message.message_sid)
        if existing:
            for key, value in message.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(message)
            await self.session.flush()
            return message

    async def get_whatsapp_by_sid(self, message_sid: str) -> Optional[WhatsAppMessage]:
        """Get WhatsApp message by SID."""
        query = select(WhatsAppMessage).where(WhatsAppMessage.message_sid == message_sid)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_whatsapp_messages(
        self,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        conversation_id: Optional[str] = None,
        status: Optional[MessageStatus] = None,
        is_processed: Optional[bool] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[WhatsAppMessage]:
        """Get WhatsApp messages with filters."""
        query = select(WhatsAppMessage).order_by(desc(WhatsAppMessage.created_at))
        if from_number:
            query = query.where(WhatsAppMessage.from_number == from_number)
        if to_number:
            query = query.where(WhatsAppMessage.to_number == to_number)
        if conversation_id:
            query = query.where(WhatsAppMessage.conversation_id == conversation_id)
        if status:
            query = query.where(WhatsAppMessage.status == status)
        if is_processed is not None:
            query = query.where(WhatsAppMessage.is_processed == is_processed)
        if since:
            query = query.where(WhatsAppMessage.created_at >= since)
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_whatsapp_conversation(
        self, conversation_id: str, limit: int = 100
    ) -> List[WhatsAppMessage]:
        """Get WhatsApp conversation."""
        query = (
            select(WhatsAppMessage)
            .where(WhatsAppMessage.conversation_id == conversation_id)
            .order_by(WhatsAppMessage.created_at)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_whatsapp_status(
        self,
        message_sid: str,
        status: MessageStatus,
        delivered_at: Optional[datetime] = None,
        read_at: Optional[datetime] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[WhatsAppMessage]:
        """Update WhatsApp delivery status."""
        msg = await self.get_whatsapp_by_sid(message_sid)
        if msg:
            msg.status = status
            if delivered_at:
                msg.delivered_at = delivered_at
            if read_at:
                msg.read_at = read_at
            if error_code:
                msg.error_code = error_code
            if error_message:
                msg.error_message = error_message
            msg.updated_at = datetime.utcnow()
            await self.session.flush()
        return msg

    async def mark_whatsapp_processed(
        self, message_sid: str, error: Optional[str] = None
    ) -> Optional[WhatsAppMessage]:
        """Mark WhatsApp message as processed."""
        msg = await self.get_whatsapp_by_sid(message_sid)
        if msg:
            msg.is_processed = True
            if error:
                msg.processing_error = error
            msg.updated_at = datetime.utcnow()
            await self.session.flush()
        return msg

    # ──────────────────────────────────────────────────────────────────────────────
    # CALENDAR EVENTS
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_calendar_event(self, event: CalendarEvent) -> CalendarEvent:
        """Upsert calendar event by provider + external_id."""
        existing = await self.get_calendar_by_provider_id(event.provider, event.external_id)
        if existing:
            for key, value in event.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(event)
            await self.session.flush()
            return event

    async def get_calendar_by_provider_id(
        self, provider: str, external_id: str
    ) -> Optional[CalendarEvent]:
        """Get calendar event by provider and external ID."""
        query = select(CalendarEvent).where(
            and_(CalendarEvent.provider == provider, CalendarEvent.external_id == external_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_calendar_events(
        self,
        organizer_email: Optional[str] = None,
        provider: Optional[str] = None,
        event_type: Optional[EventType] = None,
        start_after: Optional[datetime] = None,
        end_before: Optional[datetime] = None,
        is_processed: Optional[bool] = None,
        limit: int = 100,
    ) -> List[CalendarEvent]:
        """Get calendar events with filters."""
        query = select(CalendarEvent).order_by(CalendarEvent.start_time)
        if organizer_email:
            query = query.where(CalendarEvent.organizer_email == organizer_email)
        if provider:
            query = query.where(CalendarEvent.provider == provider)
        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)
        if start_after:
            query = query.where(CalendarEvent.end_time >= start_after)
        if end_before:
            query = query.where(CalendarEvent.start_time <= end_before)
        if is_processed is not None:
            query = query.where(CalendarEvent.is_processed == is_processed)
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_events(
        self, organizer_email: str, hours: int = 168
    ) -> List[CalendarEvent]:
        """Get upcoming calendar events for organizer."""
        now = datetime.utcnow()
        end = now + timedelta(hours=hours)
        query = (
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.organizer_email == organizer_email,
                    CalendarEvent.end_time >= now,
                    CalendarEvent.start_time <= end,
                    CalendarEvent.status != "cancelled",
                )
            )
            .order_by(CalendarEvent.start_time)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_calendar_processed(
        self, event_id: int, error: Optional[str] = None
    ) -> Optional[CalendarEvent]:
        """Mark calendar event as processed."""
        query = select(CalendarEvent).where(CalendarEvent.id == event_id)
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        if event:
            event.is_processed = True
            if error:
                event.processing_error = error
            event.updated_at = datetime.utcnow()
            await self.session.flush()
        return event

    # ──────────────────────────────────────────────────────────────────────────────
    # NOTIFICATIONS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_notification(self, **kwargs) -> Notification:
        """Create a new notification."""
        notification = Notification(**kwargs)
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def get_notification(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID."""
        query = select(Notification).where(Notification.id == notification_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_notifications(
        self,
        recipient_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        is_dismissed: Optional[bool] = None,
        priority: Optional[NotificationPriority] = None,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Notification]:
        """Get notifications with filters."""
        query = select(Notification).order_by(desc(Notification.created_at))
        if recipient_id:
            query = query.where(Notification.recipient_id == recipient_id)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        if is_dismissed is not None:
            query = query.where(Notification.is_dismissed == is_dismissed)
        if priority:
            query = query.where(Notification.priority == priority)
        if event_type:
            query = query.where(Notification.event_type == event_type)
        if since:
            query = query.where(Notification.created_at >= since)
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_notifications(
        self, now: Optional[datetime] = None
    ) -> List[Notification]:
        """Get notifications ready to send (scheduled_for <= now, not sent)."""
        now = now or datetime.utcnow()
        query = (
            select(Notification)
            .where(
                and_(
                    Notification.scheduled_for.is_not(None),
                    Notification.scheduled_for <= now,
                    Notification.sent_at.is_(None),
                    Notification.expires_at.is_(None) | (Notification.expires_at > now),
                )
            )
            .order_by(Notification.priority.desc(), Notification.scheduled_for)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_notification_sent(
        self, notification_id: int, delivery_status: dict
    ) -> Optional[Notification]:
        """Mark notification as sent."""
        notif = await self.get_notification(notification_id)
        if notif:
            notif.sent_at = datetime.utcnow()
            notif.delivery_status = delivery_status
            notif.updated_at = datetime.utcnow()
            await self.session.flush()
        return notif

    async def mark_notification_read(
        self, notification_id: int, read_at: Optional[datetime] = None
    ) -> Optional[Notification]:
        """Mark notification as read."""
        notif = await self.get_notification(notification_id)
        if notif:
            notif.is_read = True
            notif.read_at = read_at or datetime.utcnow()
            notif.updated_at = datetime.utcnow()
            await self.session.flush()
        return notif

    async def mark_notification_dismissed(
        self, notification_id: int, dismissed_at: Optional[datetime] = None
    ) -> Optional[Notification]:
        """Mark notification as dismissed."""
        notif = await self.get_notification(notification_id)
        if notif:
            notif.is_dismissed = True
            notif.dismissed_at = dismissed_at or datetime.utcnow()
            notif.updated_at = datetime.utcnow()
            await self.session.flush()
        return notif

    async def get_notification_stats(
        self, recipient_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get notification statistics for recipient."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = select(
            func.count(Notification.id).label("total"),
            func.sum(func.case((Notification.is_read == True, 1), else_=0)).label("read"),
            func.sum(func.case((Notification.is_dismissed == True, 1), else_=0)).label("dismissed"),
            func.sum(func.case((Notification.priority == NotificationPriority.URGENT, 1), else_=0)).label("urgent"),
            func.sum(func.case((Notification.priority == NotificationPriority.CRITICAL, 1), else_=0)).label("critical"),
        ).where(
            and_(
                Notification.recipient_id == recipient_id,
                Notification.created_at >= cutoff,
            )
        )
        result = await self.session.execute(query)
        row = result.one()
        return {
            "total": row.total or 0,
            "read": row.read or 0,
            "dismissed": row.dismissed or 0,
            "urgent": row.urgent or 0,
            "critical": row.critical or 0,
            "unread": (row.total or 0) - (row.read or 0),
        }