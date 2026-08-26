"""Communication Gateway — Slack, Email, WhatsApp, Calendar, Notifications."""

from .slack import SlackProvider, SlackConfig, SlackEvent
from .email import EmailProvider, EmailConfig
from .whatsapp import WhatsAppProvider, WhatsAppConfig
from .calendar import CalendarProvider, CalendarConfig
from .notifications import (
    NotificationRouter,
    NotificationConfig,
    NotificationChannel,
    DeliveryResult,
)
from .gateway import CommunicationGateway, GatewayConfig

__all__ = [
    "SlackProvider",
    "SlackConfig",
    "SlackEvent",
    "EmailProvider",
    "EmailConfig",
    "WhatsAppProvider",
    "WhatsAppConfig",
    "CalendarProvider",
    "CalendarConfig",
    "NotificationRouter",
    "NotificationConfig",
    "NotificationChannel",
    "DeliveryResult",
    "CommunicationGateway",
    "GatewayConfig",
]