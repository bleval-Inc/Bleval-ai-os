"""Data Layer — Four Isolated Domain Databases.

Architecture:
- BLEVAL Database: Sales, leads, deals, campaigns, CRM operations
- MARKET Database: Market data, trading signals, MT5/TradingView feeds
- RESEARCH Database: Web research, news, content, knowledge base
- COMMS Database: Slack, email, WhatsApp, calendar, communications

Each domain has:
- Dedicated async engine + session factory
- Domain-specific models/schemas
- Independent migrations (Alembic)
- Connection pooling with read replicas
- Repository pattern for data access
"""

from .database import (
    DatabaseManager,
    get_database_manager,
    DomainDatabase,
)
from .models import (
    # BLEVAL models
    Lead,
    Contact,
    Opportunity,
    Campaign,
    Deal,
    Activity,
    # MARKET models
    MarketTick,
    MarketRate,
    Symbol,
    AccountSnapshot,
    Position,
    Order,
    TradeSignal,
    # RESEARCH models
    ResearchReport,
    NewsArticle,
    WebPage,
    ContentPiece,
    KnowledgeEntry,
    # COMMS models
    SlackMessage,
    EmailMessage,
    WhatsAppMessage,
    CalendarEvent,
    Notification,
)
from .repositories import (
    BlevalRepository,
    MarketRepository,
    ResearchRepository,
    CommsRepository,
)

__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "DomainDatabase",
    # Models
    "Lead",
    "Contact",
    "Opportunity",
    "Campaign",
    "Deal",
    "Activity",
    "MarketTick",
    "MarketRate",
    "Symbol",
    "AccountSnapshot",
    "Position",
    "Order",
    "TradeSignal",
    "ResearchReport",
    "NewsArticle",
    "WebPage",
    "ContentPiece",
    "KnowledgeEntry",
    "SlackMessage",
    "EmailMessage",
    "WhatsAppMessage",
    "CalendarEvent",
    "Notification",
    # Repositories
    "BlevalRepository",
    "MarketRepository",
    "ResearchRepository",
    "CommsRepository",
]