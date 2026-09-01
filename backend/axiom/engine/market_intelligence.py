"""Market Intelligence Ingestion Engine — House of Valta Market Data Collection.
Handles ingestion, normalization, deduplication, and storage of market intelligence data
from various sources including news APIs, economic calendars, and institutional sources.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging

import aiohttp
import feedparser
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from axiom.data.database import Domain

from axiom.data.database import DatabaseManager
from axiom.data.models.intelligence import (
    MarketNews,
    EconomicIndicator,
    GeopoliticalEvent,
    InstitutionalInfo,
    IntelligenceCache,
    NewsCategory,
    NewsSourceType,
    RelevanceLevel,
)
from axiom.data.models.market import Symbol

if TYPE_CHECKING:
    from axiom.runtime.lifecycle import AxiomRuntime

logger = logging.getLogger(__name__)


class MarketIntelligenceEngine:
    """Engine for ingesting and managing market intelligence data."""

    def __init__(self, data_manager: DatabaseManager, runtime: "AxiomRuntime"):
        self.data_manager = data_manager
        self.runtime = runtime
        self._session: Optional[aiohttp.ClientSession] = None
        self._is_running = False

        # Source configurations
        self.news_sources = {
            "reuters": {
                "url": "https://www.reuters.com/tools/rss",
                "type": NewsSourceType.ESTABLISHED_MEDIA,
                "categories": [NewsCategory.MARKET_NEWS, NewsCategory.MACROECONOMICS],
            },
            "bloomberg": {
                "url": "https://feeds.bloomberg.com/markets/news.rss",
                "type": NewsSourceType.ESTABLISHED_MEDIA,
                "categories": [NewsCategory.MARKET_NEWS, NewsCategory.MACROECONOMICS],
            },
            "fred": {
                "url": "https://fred.stlouisfed.org/feed/",
                "type": NewsSourceType.OFFICIAL,
                "categories": [NewsCategory.MACROECONOMICS],
            },
            "tradingview": {
                "url": "https://www.tradingview.com/news/",
                "type": NewsSourceType.FINANCIAL_DATA,
                "categories": [NewsCategory.MARKET_NEWS, NewsCategory.TECHNICAL],
            },
            "fxstreet": {
                "url": "https://www.fxstreet.com/rss/news",
                "type": NewsSourceType.FINANCIAL_DATA,
                "categories": [NewsCategory.MARKET_NEWS, NewsCategory.MACROECONOMICS],
            },
            "financial_juice": {
                "url": "https://www.financialjuice.com/rss/",
                "type": NewsSourceType.FINANCIAL_DATA,
                "categories": [NewsCategory.MARKET_NEWS, NewsCategory.MACROECONOMICS],
            },
        }

        self.economic_calendar_sources = {
            "investing_com": {
                "url": "https://www.investing.com/economic-calendar/",
                "type": NewsSourceType.FINANCIAL_DATA,
                "indicators": ["CPI", "NFP", "GDP", "PMI", "Interest Rate Decision"],
            },
            "forex_factory": {
                "url": "https://www.forexfactory.com/calendar.php",
                "type": NewsSourceType.FINANCIAL_DATA,
                "indicators": ["CPI", "NFP", "GDP", "PMI", "Interest Rate Decision"],
            },
            "fred": {
                "url": "https://fred.stlouisfed.org/releases/",
                "type": NewsSourceType.OFFICIAL,
                "indicators": ["CPI", "GDP", "UNRATE", "PAYEMS", "FEDFUNDS"],
            },
        }

        self.institutional_sources = {
            "federal_reserve": {
                "url": "https://www.federalreserve.gov/feeds/press_all.xml",
                "type": NewsSourceType.OFFICIAL,
                "priority": "high",
            },
            "ecb": {
                "url": "https://www.ecb.europa.eu/rss/press.html",
                "type": NewsSourceType.OFFICIAL,
                "priority": "high",
            },
            "imf": {
                "url": "https://www.imf.org/en/News/rss",
                "type": NewsSourceType.OFFICIAL,
                "priority": "medium",
            },
            "world_bank": {
                "url": "https://www.worldbank.org/en/news/all/rss",
                "type": NewsSourceType.OFFICIAL,
                "priority": "medium",
            },
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "AxiomOS-MarketIntelligence/1.0"},
            )
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _assess_relevance(
        self,
        title: str,
        content: str,
        category: NewsCategory,
        source_type: NewsSourceType,
    ) -> tuple[RelevanceLevel, int]:
        """Assess relevance of intelligence item to House of Valta trading model."""
        # Combine title and content for analysis
        text = f"{title} {content}".lower()

        # Keywords that indicate high relevance to Valta's trading model
        high_relevance_keywords = [
            "gold",
            "xauusd",
            "us30",
            "dow jones",
            "s&p 500",
            "spx",
            "nasdaq",
            "usd",
            "dollar",
            "eur/usd",
            "gbp/usd",
            "usd/jpy",
            "oil",
            "crude",
            "brent",
            "wti",
            "silver",
            "copper",
            "platinum",
            "palladium",
            "interest rate",
            "fed",
            "federal reserve",
            "ecb",
            "boe",
            "boj",
            "inflation",
            "cpi",
            "pce",
            "gdp",
            "employment",
            "unemployment",
            "nfp",
            "nonfarm payroll",
            "pmi",
            "manufacturing",
            "services",
            "retail sales",
            "consumer confidence",
            "manufacturing",
            "ism",
            "fomc",
            "monetary policy",
            "quantitative easing",
            "tapering",
            "yield curve",
            "treasury",
            "bonds",
            "vix",
            "volatility",
            "risk sentiment",
            "risk on",
            "risk off",
            "safe haven",
        ]

        medium_relevance_keywords = [
            "europe",
            "asia",
            "china",
            "japan",
            "uk",
            "canada",
            "australia",
            "emerging markets",
            "forex",
            "currency",
            "commodities",
            "indices",
            "equities",
            "stocks",
            "bonds",
            "yields",
            "central bank",
            "policy",
            "fiscal",
            "monetary",
            "trade",
            "tariff",
            "sanctions",
            "geopolitical",
            "conflict",
            "war",
            "election",
            "political",
        ]

        # Count keyword matches
        high_matches = sum(1 for kw in high_relevance_keywords if kw in text)
        medium_matches = sum(1 for kw in medium_relevance_keywords if kw in text)

        # Base relevance by source type
        source_relevance = {
            NewsSourceType.OFFICIAL: 30,
            NewsSourceType.ESTABLISHED_MEDIA: 25,
            NewsSourceType.FINANCIAL_DATA: 20,
            NewsSourceType.SOCIAL_MEDIA: 10,
            NewsSourceType.BLOG: 5,
            NewsSourceType.FORUM: 5,
        }

        base_score = source_relevance.get(source_type, 10)

        # Add keyword-based scores
        keyword_score = min(high_matches * 10 + medium_matches * 5, 40)

        # Category-based adjustment
        category_adjustment = {
            NewsCategory.MARKET_NEWS: 10,
            NewsCategory.MACROECONOMICS: 15,
            NewsCategory.GEOPOLITICS: 10,
            NewsCategory.INSTITUTIONAL: 10,
            NewsCategory.TECHNICAL: 5,
            NewsCategory.SENTIMENT: 5,
        }.get(category, 0)

        total_score = min(base_score + keyword_score + category_adjustment, 100)

        # Determine relevance level
        if total_score >= 80:
            relevance_level = RelevanceLevel.CRITICAL
        elif total_score >= 60:
            relevance_level = RelevanceLevel.HIGH
        elif total_score >= 40:
            relevance_level = RelevanceLevel.MEDIUM
        elif total_score >= 20:
            relevance_level = RelevanceLevel.LOW
        else:
            relevance_level = RelevanceLevel.MINIMAL

        return relevance_level, total_score

    def _determine_affected_instruments(self, text: str) -> Dict[str, List[str]]:
        """Determine which instruments are affected by the intelligence item."""
        text_lower = text.lower()

        # Instrument mappings
        instrument_mapping = {
            "gold": ["XAUUSD", "XAU", "GOLD"],
            "silver": ["XAGUSD", "XAG", "SILVER"],
            "oil": ["USOIL", "UKOIL", "WTI", "BRENT"],
            "natural gas": ["XNGUSD"],
            "copper": ["HGUSD"],
            "platinum": ["XPTUSD"],
            "palladium": ["XPDUSD"],
            "usd": ["USD", "USDX", "DXY"],
            "eur": ["EURUSD", "EUR"],
            "gbp": ["GBPUSD", "GBP"],
            "jpy": ["USDJPY", "JPY"],
            "aud": ["AUDUSD", "AUD"],
            "cad": ["USDCAD", "CAD"],
            "chf": ["USDCHF", "CHF"],
            "nzd": ["NZDUSD", "NZD"],
            "us30": ["US30", "DJI", "DOW"],
            "spx": ["US500", "SPX", "S&P 500"],
            "nasdaq": ["USTEC", "NDX", "NASDAQ"],
            "russell": ["US2000", "RUT", "RUSSELL 2000"],
            "ftse": ["UK100", "FTSE"],
            "dax": ["DE30", "DAX"],
            "cac": ["FR40", "CAC"],
            "nikkei": ["JP225", "NIKKEI"],
            "hang_seng": ["HK33", "HSI"],
            "shanghai": ["CN50", "SSE"],
        }

        affected_instruments = []
        affected_currencies = []
        affected_commodities = []
        affected_indices = []

        for keyword, instruments in instrument_mapping.items():
            if keyword in text_lower:
                affected_instruments.extend(instruments)
                # Categorize instruments
                for instr in instruments:
                    if instr in ["XAUUSD", "XAGUSD", "USOIL", "UKOIL", "WTI", "BRENT", "XNGUSD", "HGUSD", "XPTUSD", "XPDUSD"]:
                        affected_commodities.append(instr)
                    elif instr in ["USD", "USDX", "DXY", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]:
                        affected_currencies.append(instr)
                    elif instr in [
                        "US30",
                        "DJI",
                        "DOW",
                        "US500",
                        "SPX",
                        "S&P 500",
                        "USTEC",
                        "NDX",
                        "NASDAQ",
                        "US2000",
                        "RUT",
                        "RUSSELL 2000",
                        "UK100",
                        "FTSE",
                        "DE30",
                        "DAX",
                        "FR40",
                        "CAC",
                        "JP225",
                        "NIKKEI",
                        "HK33",
                        "HSI",
                        "CN50",
                        "SSE",
                    ]:
                        affected_indices.append(instr)

        # Remove duplicates
        return {
            "instruments": list(set(affected_instruments)),
            "currencies": list(set(affected_currencies)),
            "commodities": list(set(affected_commodities)),
            "indices": list(set(affected_indices)),
        }

    async def _store_news_item(
        self,
        title: str,
        summary: Optional[str],
        content: Optional[str],
        url: Optional[str],
        category: NewsCategory,
        source_type: NewsSourceType,
        source_name: str,
        published_at: datetime,
    ) -> Optional[MarketNews]:
        """Store a news item in the database with deduplication."""
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            # Create content for hashing
            content_for_hash = f"{title}{summary or ''}{content or ''}{url or ''}"
            content_hash = self._calculate_content_hash(content_for_hash)

            # Check for duplicates
            existing = (
                db.query(MarketNews)
                .filter(
                    and_(
                        MarketNews.content_hash == content_hash,
                        MarketNews.source_name == source_name,
                    )
                )
                .first()
            )
            if existing:
                logger.debug(f"Duplicate news item skipped: {title[:50]}...")
                return None

            # Assess relevance
            relevance_level, relevance_score = self._assess_relevance(
                title, content or summary or "", category, source_type
            )

            # Determine affected instruments
            affected = self._determine_affected_instruments(content_for_hash)

            # Set expiration (24 hours for news by default)
            expires_at = published_at + timedelta(hours=24)

            # Create news item
            news_item = MarketNews(
                headline=title[:500],  # Limit headline length
                summary=summary,
                content=content,
                url=url,
                category=category,
                source_type=source_type,
                source_name=source_name,
                relevance_level=relevance_level,
                relevance_score=relevance_score,
                affected_instruments=affected["instruments"],
                affected_currencies=affected["currencies"],
                affected_commodities=affected["commodities"],
                affected_indices=affected["indices"],
                published_at=published_at,
                expires_at=expires_at,
                content_hash=content_hash,
                source_id=None,  # Could be populated from source-specific ID
            )

            db.add(news_item)
            db.commit()
            db.refresh(news_item)

            logger.info(f"Stored news item: {title[:50]}... (relevance: {relevance_level.value})")
            return news_item

        except Exception as e:
            logger.error(f"Error storing news item: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    async def ingest_rss_feed(
        self,
        feed_url: str,
        source_name: str,
        source_type: NewsSourceType,
        category: NewsCategory,
    ) -> int:
        """Ingest news from an RSS feed."""
        try:
            session = await self._get_session()
            async with session.get(feed_url) as response:
                if response.status != 200:
                    logger.warning(
                        f"Failed to fetch RSS feed {feed_url}: HTTP {response.status}"
                    )
                    return 0

                content = await response.text()
                feed = feedparser.parse(content)

                stored_count = 0
                db = self.data_manager.get_session(Domain.MARKET)

                try:
                    for entry in feed.entries[:50]:  # Limit to 50 most recent entries
                        title = getattr(entry, "title", "").strip()
                        if not title:
                            continue

                        summary = getattr(entry, "summary", None)
                        content = getattr(entry, "content", [{}])[0].get(
                            "value", None
                        ) if hasattr(entry, "content") else None
                        url = getattr(entry, "link", None)

                        # Parse publication date
                        published_at = datetime.utcnow()  # Default
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6])
                        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                            published_at = datetime(*entry.updated_parsed[:6])

                        news_item = await self._store_news_item(
                            title,
                            summary,
                            content,
                            url,
                            category,
                            source_type,
                            source_name,
                            published_at,
                        )
                        if news_item:
                            stored_count += 1

                finally:
                    pass  # Session is closed in _store_news_item

                logger.info(
                    f"Ingested {stored_count} news items from {source_name} ({feed_url})"
                )
                return stored_count

        except Exception as e:
            logger.error(f"Error ingesting RSS feed {feed_url}: {e}")
            return 0

    async def ingest_economic_indicator(
        self,
        name: str,
        release_date: datetime,
        actual_value: Optional[float] = None,
        forecast_value: Optional[float] = None,
        previous_value: Optional[float] = None,
        unit: Optional[str] = None,
        source_name: str = "Unknown",
        source_type: NewsSourceType = NewsSourceType.OFFICIAL,
        indicator_type: str = "economic",
        description: Optional[str] = None,
        release_time: Optional[datetime] = None,
        next_release: Optional[datetime] = None,
        survey_median: Optional[float] = None,
    ) -> Optional[EconomicIndicator]:
        """Store an economic indicator release."""
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            # Check for duplicates
            existing = (
                db.query(EconomicIndicator)
                .filter(
                    and_(
                        EconomicIndicator.name == name,
                        EconomicIndicator.release_date == release_date,
                        EconomicIndicator.source_name == source_name,
                    )
                )
                .first()
            )
            if existing:
                logger.debug(
                    f"Duplicate economic indicator skipped: {name} {release_date.date()}"
                )
                return None

            # Assess relevance
            relevance_level, relevance_score = self._assess_relevance(
                name, description or "", NewsCategory.MACROECONOMICS, source_type
            )
            impact_level = relevance_level  # For economic indicators, relevance = impact

            # Determine affected instruments
            text_for_analysis = f"{name} {description or ''}".lower()
            affected = self._determine_affected_instruments(text_for_analysis)

            # Create indicator
            indicator = EconomicIndicator(
                name=name[:100],
                description=description,
                indicator_type=indicator_type[:50],
                release_date=release_date,
                actual_value=actual_value,
                forecast_value=forecast_value,
                previous_value=previous_value,
                unit=unit,
                impact_level=impact_level,
                affected_instruments=affected["instruments"],
                affected_currencies=affected["currencies"],
                source_name=source_name[:200],
                source_type=source_type,
                release_time=release_time,
                next_release=next_release,
                tags=[],
                extra_data={},
                survey_median=survey_median,
            )

            db.add(indicator)
            db.commit()
            db.refresh(indicator)

            logger.info(
                f"Stored economic indicator: {name} = {actual_value} {unit or ''} "
                f"(impact: {impact_level.value})"
            )
            return indicator

        except Exception as e:
            logger.error(f"Error storing economic indicator: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    async def ingest_geopolitical_event(
        self,
        title: str,
        description: Optional[str],
        event_type: str,
        region: Optional[str],
        countries_affected: List[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        is_ongoing: bool = False,
        source_name: str = "Unknown",
        source_type: NewsSourceType = NewsSourceType.OFFICIAL,
        source_reliability: int = 50,
    ) -> Optional[GeopoliticalEvent]:
        """Store a geopolitical event."""
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            # Assess relevance
            relevance_level, relevance_score = self._assess_relevance(
                title, description or "", NewsCategory.GEOPOLITICS, source_type
            )
            impact_level = relevance_level  # For geopolitical events, relevance = impact

            # Determine affected instruments
            text_for_analysis = f"{title} {description or ''}".lower()
            affected = self._determine_affected_instruments(text_for_analysis)

            # Determine event scope
            event_scope = "global"
            if region:
                if len(countries_affected) == 1:
                    event_scope = "local"
                elif len(countries_affected) <= 5:
                    event_scope = "regional"
                else:
                    event_scope = "global"

            # Create event
            event = GeopoliticalEvent(
                title=title[:300],
                description=description,
                event_type=event_type[:100],
                region=region,
                countries_affected=countries_affected,
                event_scope=event_scope,
                start_date=start_date,
                end_date=end_date,
                is_ongoing=is_ongoing,
                impact_level=impact_level,
                impact_score=relevance_score,
                affected_instruments=affected["instruments"],
                affected_currencies=affected["currencies"],
                affected_commodities=[],  # Could be enhanced
                source_name=source_name[:200],
                source_type=source_type,
                source_reliability=source_reliability,
                tags=[],
                extra_data={},
            )

            db.add(event)
            db.commit()
            db.refresh(event)

            logger.info(
                f"Stored geopolitical event: {title[:50]}... "
                f"(impact: {impact_level.value}, scope: {event_scope})"
            )
            return event

        except Exception as e:
            logger.error(f"Error storing geopolitical event: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    async def ingest_institutional_info(
        self,
        title: str,
        summary: Optional[str],
        content: Optional[str],
        author: Optional[str],
        institution: str,
        info_type: str,
        published_at: datetime,
        source_name: str = "Unknown",
        source_type: NewsSourceType = NewsSourceType.OFFICIAL,
        source_url: Optional[str] = None,
    ) -> Optional[InstitutionalInfo]:
        """Store institutional information/commentary."""
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            # Assess relevance
            relevance_level, relevance_score = self._assess_relevance(
                title, content or summary or "", NewsCategory.INSTITUTIONAL, source_type
            )

            # Determine affected instruments
            text_for_analysis = f"{title} {content or summary or ''}".lower()
            affected = self._determine_affected_instruments(text_for_analysis)

            # Create institutional info
            info = InstitutionalInfo(
                title=title[:300],
                summary=summary,
                content=content,
                author=author,
                institution=institution[:200],
                info_type=info_type[:100],
                published_at=published_at,
                relevance_level=relevance_level,
                relevance_score=relevance_score,
                affected_instruments=affected["instruments"],
                affected_currencies=affected["currencies"],
                source_name=source_name[:200],
                source_type=source_type,
                source_url=source_url,
                tags=[],
                extra_data={},
            )

            db.add(info)
            db.commit()
            db.refresh(info)

            logger.info(
                f"Stored institutional info: {title[:50]}... from {institution} "
                f"(relevance: {relevance_level.value})"
            )
            return info

        except Exception as e:
            logger.error(f"Error storing institutional info: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    async def run_news_ingestion_cycle(self) -> Dict[str, int]:
        """Run a complete news ingestion cycle from all configured sources."""
        results = {
            "news_items": 0,
            "economic_indicators": 0,
            "geopolitical_events": 0,
            "institutional_info": 0,
            "errors": 0,
        }

        logger.info("Starting market intelligence ingestion cycle...")

        try:
            # Ingest news from RSS feeds
            for source_key, source_config in self.news_sources.items():
                try:
                    count = await self.ingest_rss_feed(
                        source_config["url"],
                        source_key.title(),
                        source_config["type"],
                        NewsCategory.MARKET_NEWS,  # Default category
                    )
                    results["news_items"] += count
                except Exception as e:
                    logger.error(f"Error ingesting from {source_key}: {e}")
                    results["errors"] += 1

            # Ingest from institutional sources
            for source_key, source_config in self.institutional_sources.items():
                try:
                    count = await self.ingest_rss_feed(
                        source_config["url"],
                        source_key.upper().replace("_", " "),
                        source_config["type"],
                        NewsCategory.INSTITUTIONAL,
                    )
                    results["institutional_info"] += count
                except Exception as e:
                    logger.error(f"Error ingesting institutional from {source_key}: {e}")
                    results["errors"] += 1

            logger.info(
                f"Ingestion cycle complete: {results['news_items']} news, "
                f"{results['economic_indicators']} indicators, "
                f"{results['geopolitical_events']} events, "
                f"{results['institutional_info']} institutional items"
            )

        except Exception as e:
            logger.error(f"Error in news ingestion cycle: {e}")
            results["errors"] += 1

        return results

    async def start_background_ingestion(self, interval_minutes: int = 15):
        """Start background ingestion of market intelligence data."""
        if self._is_running:
            logger.warning("Market intelligence ingestion already running")
            return

        self._is_running = True
        logger.info(
            f"Starting background market intelligence ingestion "
            f"(interval: {interval_minutes} minutes)"
        )

        while self._is_running:
            try:
                await self.run_news_ingestion_cycle()
                # Wait for the specified interval
                await asyncio.sleep(interval_minutes * 60)
            except asyncio.CancelledError:
                logger.info("Market intelligence ingestion cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background ingestion loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying on error

        logger.info("Market intelligence ingestion stopped")

    def stop_background_ingestion(self):
        """Stop background ingestion."""
        self._is_running = False
        logger.info("Stopping market intelligence ingestion...")

    async def get_recent_intelligence(
        self,
        hours: int = 24,
        category: Optional[NewsCategory] = None,
        min_relevance: RelevanceLevel = RelevanceLevel.LOW,
        limit: int = 100,
    ) -> Dict[str, List[Any]]:
        """Get recent intelligence items from the database."""
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            # Build base query conditions
            time_condition = and_(
                MarketNews.received_at >= since,
                EconomicIndicator.received_at >= since,
                GeopoliticalEvent.received_at >= since,
                InstitutionalInfo.received_at >= since,
            )

            # Relevance condition
            relevance_condition = or_(
                MarketNews.relevance_level >= min_relevance,
                EconomicIndicator.impact_level >= min_relevance,
                GeopoliticalEvent.impact_level >= min_relevance,
                InstitutionalInfo.relevance_level >= min_relevance,
            )

            # Get news
            news_query = db.query(MarketNews).filter(
                and_(
                    MarketNews.received_at >= since,
                    MarketNews.relevance_level >= min_relevance,
                    MarketNews.expires_at.is_(None)
                    | (MarketNews.expires_at > datetime.utcnow()),
                )
            )
            if category:
                news_query = news_query.filter(MarketNews.category == category)
            news_items = news_query.order_by(desc(MarketNews.published_at)).limit(limit).all()

            # Get economic indicators
            indicators_query = db.query(EconomicIndicator).filter(
                and_(
                    EconomicIndicator.received_at >= since,
                    EconomicIndicator.impact_level >= min_relevance,
                )
            )
            indicators = (
                indicators_query.order_by(desc(EconomicIndicator.release_date))
                .limit(limit)
                .all()
            )

            # Get geopolitical events
            events_query = db.query(GeopoliticalEvent).filter(
                and_(
                    GeopoliticalEvent.received_at >= since,
                    GeopoliticalEvent.impact_level >= min_relevance,
                )
            )
            events = (
                events_query.order_by(desc(GeopoliticalEvent.start_date))
                .limit(limit)
                .all()
            )

            # Get institutional info
            info_query = db.query(InstitutionalInfo).filter(
                and_(
                    InstitutionalInfo.received_at >= since,
                    InstitutionalInfo.relevance_level >= min_relevance,
                )
            )
            info_items = (
                info_query.order_by(desc(InstitutionalInfo.published_at))
                .limit(limit)
                .all()
            )

            return {
                "news": news_items,
                "indicators": indicators,
                "events": events,
                "institutional": info_items,
            }

        finally:
            db.close()

    async def get_intelligence_for_instruments(
        self,
        instruments: List[str],
        hours: int = 24,
        limit: int = 50,
    ) -> Dict[str, List[Any]]:
        """Get intelligence items that affect specific instruments."""
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            # Build conditions for each instrument type
            instrument_conditions = []
            for instrument in instruments:
                instrument_conditions.append(
                    MarketNews.affected_instruments.contains([instrument])
                )

            # Get news affecting these instruments
            news_query = db.query(MarketNews).filter(
                and_(
                    MarketNews.received_at >= since,
                    or_(*instrument_conditions) if instrument_conditions else False,
                    MarketNews.expires_at.is_(None)
                    | (MarketNews.expires_at > datetime.utcnow()),
                )
            )
            news_items = (
                news_query.order_by(desc(MarketNews.published_at))
                .limit(limit)
                .all()
            )

            # Similar for other types...
            indicators_query = db.query(EconomicIndicator).filter(
                and_(
                    EconomicIndicator.received_at >= since,
                    or_(*[
                        EconomicIndicator.affected_instruments.contains([instrument])
                        for instrument in instruments
                    ]) if instruments else False,
                )
            )
            indicators = (
                indicators_query.order_by(desc(EconomicIndicator.release_date))
                .limit(limit)
                .all()
            )

            events_query = db.query(GeopoliticalEvent).filter(
                and_(
                    GeopoliticalEvent.received_at >= since,
                    or_(*[
                        GeopoliticalEvent.affected_instruments.contains([instrument])
                        for instrument in instruments
                    ]) if instruments else False,
                )
            )
            events = (
                events_query.order_by(desc(GeopoliticalEvent.start_date))
                .limit(limit)
                .all()
            )

            info_query = db.query(InstitutionalInfo).filter(
                and_(
                    InstitutionalInfo.received_at >= since,
                    or_(*[
                        InstitutionalInfo.affected_instruments.contains([instrument])
                        for instrument in instruments
                    ]) if instruments else False,
                )
            )
            info_items = (
                info_query.order_by(desc(InstitutionalInfo.published_at))
                .limit(limit)
                .all()
            )

            return {
                "news": news_items,
                "indicators": indicators,
                "events": events,
                "institutional": info_items,
            }

        finally:
            db.close()