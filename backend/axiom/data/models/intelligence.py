"""INTELLIGENCE Domain Models — Market Intelligence for House of Valta.
Handles market news, macroeconomic data, geopolitical events, and institutional information.
"""

import enum
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

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
    JSON,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom.data.database import DeclarativeBase
from axiom.data.models.market import Symbol


class IntelligenceBase(DeclarativeBase):
    """Base for INTELLIGENCE domain models."""
    metadata = MetaData(schema="intelligence")


class NewsCategory(str, enum.Enum):
    """Categories of market news."""
    MARKET_NEWS = "market_news"
    MACROECONOMICS = "macroeconomics"
    GEOPOLITICS = "geopolitics"
    INSTITUTIONAL = "institutional"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"


class NewsSourceType(str, enum.Enum):
    """Types of news sources."""
    OFFICIAL = "official"  # Central banks, government institutions
    ESTABLISHED_MEDIA = "established_media"  # Reuters, Bloomberg, WSJ, etc.
    FINANCIAL_DATA = "financial_data"  # TradingView, Investing.com, etc.
    SOCIAL_MEDIA = "social_media"  # Twitter, Reddit, etc.
    BLOG = "blog"  # Individual analysts, trading blogs
    FORUM = "forum"  # Trading forums, communities


class RelevanceLevel(str, enum.Enum):
    """Relevance levels for filtering intelligence."""
    CRITICAL = "critical"  # Must-see, directly affects trading instruments
    HIGH = "high"  # Important, likely to affect trading
    MEDIUM = "medium"  # Moderate relevance
    LOW = "low"  # Low relevance, background information
    MINIMAL = "minimal"  # Minimal relevance, for completeness


class MarketNews(IntelligenceBase):
    """Market news and intelligence items."""

    __tablename__ = "market_news"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Core news content
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)  # Full article/content
    url: Mapped[Optional[String]] = mapped_column(String(1000), nullable=True)  # Source URL

    # Classification
    category: Mapped[NewsCategory] = mapped_column(SQLEnum(NewsCategory), nullable=False, index=True)
    source_type: Mapped[NewsSourceType] = mapped_column(SQLEnum(NewsSourceType), nullable=False, index=True)
    source_name: Mapped[String] = mapped_column(String(200), nullable=False, index=True)  # e.g., "Federal Reserve", "Reuters"

    # Relevance and filtering
    relevance_level: Mapped[RelevanceLevel] = mapped_column(SQLEnum(RelevanceLevel), nullable=False, index=True)
    relevance_score: Mapped[Integer] = mapped_column(Integer, nullable=True)  # 0-100 numerical score

    # Instruments affected (related to House of Valta trading model)
    affected_instruments: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)  # e.g., ["XAUUSD", "US30", "USD"]
    affected_currencies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    affected_commodities: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    affected_indices: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Timing
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)  # When the news was published
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)  # When we received it
    expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True, index=True)  # When it becomes stale

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # For source-specific fields

    # Dedup and tracking
    content_hash: Mapped[Optional[String]] = mapped_column(String(64), nullable=True, index=True)  # SHA-256 of content for dedup
    source_id: Mapped[Optional[String]] = mapped_column(String(100), nullable=True, index=True)  # Source-specific ID

    # Relationships (optional linking to symbols)
    related_symbol_ids: Mapped[List[int]] = mapped_column(JSON, default=list, nullable=False)  # IDs of related Symbol records

    __table_args__ = (
        Index("ix_market_news_published_at", "published_at"),
        Index("ix_market_news_category_relevance", "category", "relevance_level"),
        Index("ix_market_news_source_published", "source_name", "published_at"),
        Index("ix_market_news_received_at", "received_at"),
        Index("ix_market_news_expires_at", "expires_at"),
        UniqueConstraint("content_hash", "source_name", name="uq_market_news_content_source"),
    )

    def __repr__(self) -> str:
        return f"<MarketNews(id={self.id}, headline='{self.headline[:50]}...', category={self.category.value}, relevance={self.relevance_level.value})>"


class EconomicIndicator(IntelligenceBase):
    """Macroeconomic indicators and data releases."""

    __tablename__ = "economic_indicators"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Indicator details
    name: Mapped[String] = mapped_column(String(100), nullable=False, index=True)  # e.g., "CPI", "NFP", "GDP"
    description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    indicator_type: Mapped[String] = mapped_column(String(50), nullable=False, index=True)  # e.g., "inflation", "employment", "growth"

    # Release data
    release_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    actual_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    forecast_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    previous_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    unit: Mapped[Optional[String]] = mapped_column(String(20), nullable=True)  # e.g., "%", "points", "billions"

    # Market impact
    impact_level: Mapped[RelevanceLevel] = mapped_column(SQLEnum(RelevanceLevel), nullable=False, index=True)
    affected_instruments: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    affected_currencies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Source information
    source_name: Mapped[String] = mapped_column(String(200), nullable=False, index=True)  # e.g., "BLS", "ECB", "Eurostat"
    source_type: Mapped[NewsSourceType] = mapped_column(SQLEnum(NewsSourceType), nullable=False, index=True)
    release_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Specific time of release
    next_release: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)  # When next release is expected

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    survey_median: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)  # For survey-based indicators

    __table_args__ = (
        Index("ix_economic_indicators_release_date", "release_date"),
        Index("ix_economic_indicators_name_type", "name", "indicator_type"),
        Index("ix_economic_indicators_impact", "impact_level"),
        Index("ix_economic_indicators_next_release", "next_release"),
        UniqueConstraint("name", "release_date", "source_name", name="uq_economic_indicators_name_date_source"),
    )

    def __repr__(self) -> str:
        return f"<EconomicIndicator(id={self.id}, name='{self.name}', release='{self.release_date.date()}', actual={self.actual_value})>"


class GeopoliticalEvent(IntelligenceBase):
    """Geopolitical events affecting markets."""

    __tablename__ = "geopolitical_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Event details
    title: Mapped[String] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    event_type: Mapped[String] = mapped_column(String(100), nullable=False, index=True)  # e.g., "election", "conflict", "summit", "policy_change"

    # Geographic scope
    region: Mapped[Optional[String]] = mapped_column(String(100), nullable=True, index=True)  # e.g., "Middle East", "Europe", "Asia-Pacific"
    countries_affected: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    event_scope: Mapped[String] = mapped_column(String(50), nullable=False)  # "local", "regional", "global"

    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_date: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True, index=True)
    is_ongoing: Mapped[Boolean] = mapped_column(Boolean, default=False, nullable=False)

    # Market impact
    impact_level: Mapped[RelevanceLevel] = mapped_column(SQLEnum(RelevanceLevel), nullable=False, index=True)
    impact_score: Mapped[Integer] = mapped_column(Integer, nullable=True)  # 0-100 numerical impact score
    affected_instruments: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    affected_currencies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    affected_commodities: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Source information
    source_name: Mapped[String] = mapped_column(String(200), nullable=False, index=True)
    source_type: Mapped[NewsSourceType] = mapped_column(SQLEnum(NewsSourceType), nullable=False, index=True)
    source_reliability: Mapped[Integer] = mapped_column(Integer, default=50, nullable=True)  # 0-100 reliability score

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_geopolitical_events_start_date", "start_date"),
        Index("ix_geopolitical_events_end_date", "end_date"),
        Index("ix_geopolitical_events_impact", "impact_level"),
        Index("ix_geopolitical_events_region", "region"),
        Index("ix_geopolitical_events_is_ongoing", "is_ongoing"),
    )

    def __repr__(self) -> str:
        return f"<GeopoliticalEvent(id={self.id}, title='{self.title[:50]}...', type='{self.event_type}', impact={self.impact_level.value})>"


class InstitutionalInfo(IntelligenceBase):
    """Institutional information and commentary."""

    __tablename__ = "institutional_info"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Content details
    title: Mapped[String] = mapped_column(String(300), nullable=False)
    summary: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[String]] = mapped_column(String(200), nullable=True)  # Analyst, spokesperson, etc.
    institution: Mapped[String] = mapped_column(String(200), nullable=False, index=True)  # e.g., "Goldman Sachs", "ECB", "IMF"

    # Information type
    info_type: Mapped[String] = mapped_column(String(100), nullable=False, index=True)  # e.g., "commentary", "positioning", "flow_analysis", "forecast"

    # Timing
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Market relevance
    relevance_level: Mapped[RelevanceLevel] = mapped_column(SQLEnum(RelevanceLevel), nullable=False, index=True)
    relevance_score: Mapped[Integer] = mapped_column(Integer, nullable=True)  # 0-100 numerical score
    affected_instruments: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    affected_currencies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Source information
    source_name: Mapped[String] = mapped_column(String(200), nullable=False, index=True)  # Where we got this from
    source_type: Mapped[NewsSourceType] = mapped_column(SQLEnum(NewsSourceType), nullable=False, index=True)
    source_url: Mapped[Optional[String]] = mapped_column(String(1000), nullable=True)  # Original source URL

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_institutional_info_published_at", "published_at"),
        Index("ix_institutional_info_institution_type", "institution", "info_type"),
        Index("ix_institutional_info_relevance", "relevance_level"),
        Index("ix_institutional_info_received_at", "received_at"),
    )

    def __repr__(self) -> str:
        return f"<InstitutionalInfo(id={self.id}, title='{self.title[:50]}...', institution='{self.institution}', type='{self.info_type}')>"


class IntelligenceCache(IntelligenceBase):
    """Cache layer for intelligence data to improve query performance."""

    __tablename__ = "intelligence_cache"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Cache key and data
    cache_key: Mapped[String] = mapped_column(String(200), nullable=False, unique=True, index=True)  # e.g., "news:gold:2024-01-15"
    cache_type: Mapped[String] = mapped_column(String(50), nullable=False, index=True)  # e.g., "news", "indicators", "events"
    cached_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # The actual cached data

    # Validity
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)  # When cache becomes invalid
    is_valid: Mapped[Boolean] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_intelligence_cache_cache_key", "cache_key"),
        Index("ix_intelligence_cache_expires_at", "expires_at"),
        Index("ix_intelligence_cache_cache_type", "cache_type"),
        Index("ix_intelligence_cache_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<IntelligenceCache(id={self.id}, key='{self.cache_key}', type='{self.cache_type}', valid={self.is_valid})>"