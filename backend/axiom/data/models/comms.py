"""COMMS Domain Models — Communications, Slack, Email, WhatsApp, Calendar."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom.data.database import DeclarativeBase


class CommsBase(DeclarativeBase):
    """Base for COMMS domain models."""
    metadata = MetaData(schema="comms")


class MessageDirection(str, enum.Enum):
    """Message direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, enum.Enum):
    """Message delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"


class ChannelType(str, enum.Enum):
    """Communication channel types."""

    SLACK = "slack"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    CALENDAR = "calendar"
    IN_APP = "in_app"


class EventType(str, enum.Enum):
    """Calendar event types."""

    MEETING = "meeting"
    CALL = "call"
    TASK = "task"
    REMINDER = "reminder"
    BLOCK = "block"
    HOLIDAY = "holiday"


class NotificationPriority(str, enum.Enum):
    """Notification priority."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


# ──────────────────────────────────────────────────────────────────────────────
# SLACK MESSAGES
# ──────────────────────────────────────────────────────────────────────────────

class SlackMessage(CommsBase):
    """Slack message - channels, DMs, threads."""

    __tablename__ = "slack_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    ts: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Slack timestamp
    thread_ts: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    channel_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    channel_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Author
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bot_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Content
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocks: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    files: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    # Reactions
    reactions: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    # Direction & status
    direction: Mapped[MessageDirection] = mapped_column(
        SQLEnum(MessageDirection), default=MessageDirection.INBOUND, nullable=False
    )
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus), default=MessageStatus.DELIVERED, nullable=False
    )

    # Metadata
    permalink: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    edited: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    parent_message_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("slack_messages.id"), nullable=True
    )

    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Self-referential for threads
    parent_message: Mapped[Optional["SlackMessage"]] = relationship(
        "SlackMessage", remote_side=[id], backref="replies"
    )

    __table_args__ = (
        UniqueConstraint("channel_id", "ts", name="uq_slack_channel_ts"),
        Index("ix_slack_messages_channel_posted", "channel_id", "posted_at"),
        Index("ix_slack_messages_thread", "thread_ts"),
        Index("ix_slack_messages_user_posted", "user_id", "posted_at"),
    )

    def __repr__(self) -> str:
        return f"<SlackMessage(channel={self.channel_name}, user={self.username}, ts={self.ts[:10]})>"


# ──────────────────────────────────────────────────────────────────────────────
# EMAIL MESSAGES
# ──────────────────────────────────────────────────────────────────────────────

class EmailMessage(CommsBase):
    """Email message - inbound/outbound."""

    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    in_reply_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    references: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Participants
    from_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    from_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_emails: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    cc_emails: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    bcc_emails: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Content
    subject: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Attachments
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    # Labels & categorization
    labels: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    is_unread: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Direction & status
    direction: Mapped[MessageDirection] = mapped_column(
        SQLEnum(MessageDirection), nullable=False, index=True
    )
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus), default=MessageStatus.DELIVERED, nullable=False
    )

    # Tracking
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bounced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bounce_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Sequence/campaign
    sequence_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sequence_step: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_email_messages_from_sent", "from_email", "sent_at"),
        Index("ix_email_messages_thread", "thread_id"),
        Index("ix_email_messages_unread_received", "is_unread", "received_at"),
        Index("ix_email_messages_sequence", "sequence_id", "sequence_step"),
    )

    def __repr__(self) -> str:
        return f"<EmailMessage(subject={self.subject[:50]}, from={self.from_email}, dir={self.direction.value})>"


# ──────────────────────────────────────────────────────────────────────────────
# WHATSAPP MESSAGES
# ──────────────────────────────────────────────────────────────────────────────

class WhatsAppMessage(CommsBase):
    """WhatsApp message via Twilio."""

    __tablename__ = "whatsapp_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    message_sid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    account_sid: Mapped[str] = mapped_column(String(100), nullable=False)

    # Participants
    from_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    to_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Content
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_urls: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    media_content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    num_media: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Type
    message_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)  # text, media, template, location, contacts

    # Template
    template_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    template_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Direction & status
    direction: Mapped[MessageDirection] = mapped_column(
        SQLEnum(MessageDirection), default=MessageDirection.OUTBOUND, nullable=False
    )
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus), default=MessageStatus.SENT, nullable=False, index=True
    )

    # Delivery tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Conversation
    conversation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_whatsapp_messages_conversation", "conversation_id"),
        Index("ix_whatsapp_messages_from_to_status", "from_number", "to_number", "status"),
        Index("ix_whatsapp_messages_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<WhatsAppMessage(sid={self.message_sid}, from={self.from_number}, to={self.to_number}, status={self.status.value})>"


# ──────────────────────────────────────────────────────────────────────────────
# CALENDAR EVENTS
# ──────────────────────────────────────────────────────────────────────────────

class CalendarEvent(CommsBase):
    """Calendar event - meetings, calls, tasks."""

    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)  # Google, Calendly, etc.
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # google, calendly, outlook, apple

    # Event details
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType), default=EventType.MEETING, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Time
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # RRULE
    recurrence_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Organizer
    organizer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organizer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Attendees
    attendees: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)  # [{email, name, status, role}]
    attendee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="confirmed", nullable=False)  # confirmed, tentative, cancelled

    # Metadata
    color_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    visibility: Mapped[str] = mapped_column(String(50), default="default", nullable=False)
    reminders: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_calendar_provider_extid"),
        Index("ix_calendar_events_organizer_start", "organizer_email", "start_time"),
        Index("ix_calendar_events_start_end", "start_time", "end_time"),
        Index("ix_calendar_events_provider", "provider"),
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent(title={self.title[:50]}, start={self.start_time}, organizer={self.organizer_email})>"


# ──────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ──────────────────────────────────────────────────────────────────────────────

class Notification(CommsBase):
    """System notification - alerts, reminders, updates."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Routing
    recipient_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Agent/user ID
    channels: Mapped[List[ChannelType]] = mapped_column(
        JSON, default=list, nullable=False
    )  # Where to deliver

    # Priority
    priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False
    )

    # Context
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # lead_created, deal_won, etc.
    event_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # lead, deal, etc.
    related_entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Action
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    action_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Delivery tracking
    delivery_status: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # Per-channel status
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Scheduling
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_notifications_recipient_read", "recipient_id", "is_read"),
        Index("ix_notifications_event_type", "event_type"),
        Index("ix_notifications_scheduled", "scheduled_for"),
        Index("ix_notifications_priority_created", "priority", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title={self.title[:50]}, recipient={self.recipient_id})>"