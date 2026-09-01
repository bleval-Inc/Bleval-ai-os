"""Fundamental Reporting Engine — Valta Prime Session Intelligence.
Generates automated fundamental-analysis briefing sessions for Asian, London, and New York sessions.
Focuses on GOLD and US30 analysis using live data from market intelligence, economic data, etc.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

from axiom.engine.executive_intelligence import ExecutiveIntelligence
from axiom.engine.market_intelligence import MarketIntelligenceEngine
from axiom.data.database import DatabaseManager, Domain
from axiom.data.models.intelligence import (
    MarketNews,
    EconomicIndicator,
    GeopoliticalEvent,
    InstitutionalInfo,
    NewsCategory,
    NewsSourceType,
    RelevanceLevel,
)
from axiom.data.models.market import Symbol
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TradingSession(str, Enum):
    """Forex trading sessions."""
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"


class ReportType(str, Enum):
    """Types of fundamental reports."""
    SESSION_BRIEFING = "session_briefing"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_OUTLOOK = "weekly_outlook"


class FundamentalReportingEngine:
    """Engine for generating Valta Prime's fundamental analysis reports."""

    def __init__(
        self,
        data_manager: DatabaseManager,
        market_intelligence: MarketIntelligenceEngine,
        executive_intelligence: ExecutiveIntelligence,
    ):
        self.data_manager = data_manager
        self.market_intelligence = market_intelligence
        self.executive_intelligence = executive_intelligence
        self._reports_cache: Dict[str, Any] = {}
        self._last_report_times: Dict[TradingSession, datetime] = {}

    async def generate_session_briefing(
        self,
        session: TradingSession,
        target_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate a fundamental analysis briefing for a specific trading session.

        Args:
            session: The trading session (Asian, London, New York)
            target_time: The time for which to generate the report (defaults to now)

        Returns:
            Dictionary containing the structured fundamental report
        """
        if target_time is None:
            target_time = datetime.utcnow()

        # Check if we have a recent cached report for this session
        cache_key = f"{session.value}_{target_time.date()}"
        if cache_key in self._reports_cache:
            cached_report = self._reports_cache[cache_key]
            # Return cached report if it's less than 4 hours old
            if (target_time - cached_report["generated_at"]).total_seconds() < 14400:  # 4 hours
                logger.info(f"Returning cached {session.value} session briefing from {cached_report['generated_at']}")
                return cached_report

        logger.info(f"Generating new {session.value} session fundamental briefing for {target_time}")

        # Define session time windows (UTC)
        session_windows = {
            TradingSession.ASIAN: {
                "start_hour": 0,   # 00:00 UTC
                "end_hour": 8,     # 08:00 UTC
                "name": "Asian Session",
                "major_centers": ["Tokyo", "Sydney", "Singapore", "Hong Kong"]
            },
            TradingSession.LONDON: {
                "start_hour": 7,   # 07:00 UTC
                "end_hour": 16,    # 16:00 UTC
                "name": "London Session",
                "major_centers": ["London", "Frankfurt", "Zurich"]
            },
            TradingSession.NEW_YORK: {
                "start_hour": 12,  # 12:00 UTC (NY 8:00 AM)
                "end_hour": 21,    # 21:00 UTC (NY 5:00 PM)
                "name": "New York Session",
                "major_centers": ["New York", "Chicago", "Toronto"]
            }
        }

        window_info = session_windows[session]

        # Determine the relevant time period for analysis
        # For session briefings, we look at:
        # 1. Overnight developments (since previous session close)
        # 2. Today's developments so far
        # 3. Upcoming events during this session

        analysis_start = target_time.replace(hour=0, minute=0, second=0, microsecond=0)  # Start of today
        analysis_end = target_time

        # Get market intelligence data
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            # Get recent news (last 24 hours)
            recent_news = await self._get_recent_news(db, hours=24)

            # Get recent economic indicators (last 48 hours)
            recent_indicators = await self._get_recent_indicators(db, hours=48)

            # Get recent geopolitical events (last 72 hours)
            recent_events = await self._get_recent_events(db, hours=72)

            # Get recent institutional info (last 24 hours)
            recent_institutional = await self._get_recent_institutional(db, hours=24)

            # Get symbols for GOLD and US30
            gold_symbol = await self._get_symbol(db, "XAUUSD")
            us30_symbol = await self._get_symbol(db, "US30")

            # Generate analysis for each instrument
            gold_analysis = await self._analyze_instrument(
                db, "XAUUSD", "GOLD", gold_symbol,
                recent_news, recent_indicators, recent_events, recent_institutional,
                session, target_time
            )

            us30_analysis = await self._analyze_instrument(
                db, "US30", "US30", us30_symbol,
                recent_news, recent_indicators, recent_events, recent_institutional,
                session, target_time
            )

            # Get market events to watch during this session
            events_to_watch = await self._get_session_events_to_watch(
                db, session, target_time, window_info
            )

            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                gold_analysis, us30_analysis, recent_news, recent_indicators, session, target_time
            )

            # Generate Valta Prime's assessment
            valta_assessment = await self._generate_valta_assessment(
                gold_analysis, us30_analysis, session, target_time
            )

            # Construct the final report
            report = {
                "session": session.value,
                "session_name": window_info["name"],
                "date": target_time.date().isoformat(),
                "generated_at": target_time.isoformat(),
                "report_type": ReportType.SESSION_BRIEFING.value,
                "executive_summary": executive_summary,
                "gold": gold_analysis,
                "us30": us30_analysis,
                "market_events_to_watch": events_to_watch,
                "valta_prime_assessment": valta_assessment,
                "data_sources": {
                    "news_items": len(recent_news),
                    "economic_indicators": len(recent_indicators),
                    "geopolitical_events": len(recent_events),
                    "institutional_info": len(recent_institutional),
                }
            }

            # Cache the report
            self._reports_cache[cache_key] = report
            self._last_report_times[session] = target_time

            logger.info(f"Generated {session.value} session briefing with {len(recent_news)} news items, {len(recent_indicators)} indicators")
            return report

        except Exception as e:
            logger.error(f"Error generating {session.value} session briefing: {e}")
            raise
        finally:
            db.close()

    async def _get_recent_news(self, db: Session, hours: int = 24) -> List[MarketNews]:
        """Get recent market news items."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(MarketNews)
            .filter(
                and_(
                    MarketNews.received_at >= since,
                    MarketNews.expires_at.is_(None)
                    | (MarketNews.expires_at > datetime.utcnow()),
                )
            )
            .order_by(desc(MarketNews.published_at))
            .limit(50)
            .all()
        )

    async def _get_recent_indicators(self, db: Session, hours: int = 48) -> List[EconomicIndicator]:
        """Get recent economic indicators."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(EconomicIndicator)
            .filter(EconomicIndicator.received_at >= since)
            .order_by(desc(EconomicIndicator.release_date))
            .limit(30)
            .all()
        )

    async def _get_recent_events(self, db: Session, hours: int = 72) -> List[GeopoliticalEvent]:
        """Get recent geopolitical events."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(GeopoliticalEvent)
            .filter(GeopoliticalEvent.received_at >= since)
            .order_by(desc(GeopoliticalEvent.start_date))
            .limit(20)
            .all()
        )

    async def _get_recent_institutional(self, db: Session, hours: int = 24) -> List[InstitutionalInfo]:
        """Get recent institutional information."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(InstitutionalInfo)
            .filter(InstitutionalInfo.received_at >= since)
            .order_by(desc(InstitutionalInfo.published_at))
            .limit(20)
            .all()
        )

    async def _get_symbol(self, db: Session, symbol_name: str) -> Optional[Symbol]:
        """Get a symbol by name."""
        return db.query(Symbol).filter(Symbol.name == symbol_name).first()

    def _assess_instrument_relevance(
        self,
        news_items: List[MarketNews],
        indicators: List[EconomicIndicator],
        events: List[GeopoliticalEvent],
        institutional: List[InstitutionalInfo],
        instrument_symbol: str,
    ) -> Dict[str, Any]:
        """Assess which data items are relevant to a specific instrument."""
        relevant_news = []
        relevant_indicators = []
        relevant_events = []
        relevant_institutional = []

        # Instrument-specific keywords
        instrument_keywords = {
            "XAUUSD": ["gold", "xauusd", "precious metals", "safe haven", "inflation hedge"],
            "US30": ["us30", "dow jones", "equities", "stocks", "market", "earnings", "corporate"]
        }

        keywords = instrument_keywords.get(instrument_symbol, [instrument_symbol.lower()])

        # Filter news by relevance to instrument
        for news in news_items:
            text = f"{news.headline} {news.summary or ''} {news.content or ''}".lower()
            if any(keyword in text for keyword in keywords):
                relevant_news.append(news)
            # Also include high relevance items regardless of keyword match
            elif news.relevance_level in [RelevanceLevel.CRITICAL, RelevanceLevel.HIGH]:
                relevant_news.append(news)

        # Filter indicators by relevance
        for indicator in indicators:
            text = f"{indicator.name} {indicator.description or ''}".lower()
            # Most economic indicators affect both gold and us30, but weight differently
            if any(keyword in text for keyword in ["interest rate", "inflation", "employment", "gdp", "cpi", "fed", "central bank"]):
                relevant_indicators.append(indicator)

        # Filter events by relevance
        for event in events:
            text = f"{event.title} {event.description or ''}".lower()
            if any(keyword in text for keyword in ["war", "conflict", "election", "policy", "central bank", "recession"]):
                relevant_events.append(event)

        # Filter institutional by relevance
        for info in institutional:
            text = f"{info.title} {info.summary or ''} {info.content or ''}".lower()
            if any(keyword in text for keyword in ["gold", "equities", "market", "fed", "central bank", "inflation"]):
                relevant_institutional.append(info)

        return {
            "news": relevant_news,
            "indicators": relevant_indicators,
            "events": relevant_events,
            "institutional": relevant_institutional
        }

    async def _analyze_instrument(
        self,
        db: Session,
        symbol_name: str,
        display_name: str,
        symbol_obj: Optional[Symbol],
        news_items: List[MarketNews],
        indicators: List[EconomicIndicator],
        events: List[GeopoliticalEvent],
        institutional: List[InstitutionalInfo],
        session: TradingSession,
        target_time: datetime,
    ) -> Dict[str, Any]:
        """Analyze a specific instrument (GOLD or US30) for the session briefing."""

        # Get relevance-filtered data
        relevant_data = self._assess_instrument_relevance(
            news_items, indicators, events, institutional, symbol_name
        )

        # Determine bias/context based on recent data
        bias_context = await self._determine_bias_context(
            relevant_data["news"],
            relevant_data["indicators"],
            relevant_data["events"],
            relevant_data["institutional"],
            symbol_name,
            session
        )

        # Identify bullish factors
        bullish_factors = await self._identify_bullish_factors(
            relevant_data["news"],
            relevant_data["indicators"],
            relevant_data["events"],
            relevant_data["institutional"],
            symbol_name,
            session
        )

        # Identify bearish factors
        bearish_factors = await self._identify_bearish_factors(
            relevant_data["news"],
            relevant_data["indicators"],
            relevant_data["events"],
            relevant_data["institutional"],
            symbol_name,
            session
        )

        # Identify key catalysts
        key_catalysts = await self._identify_key_catalysts(
            relevant_data["news"],
            relevant_data["indicators"],
            relevant_data["events"],
            relevant_data["institutional"],
            session,
            target_time,
            look_ahead_hours=8  # Look ahead 8 hours for session-relevant catalysts
        )

        # Identify risks
        risks = await self._identify_risks(
            relevant_data["news"],
            relevant_data["indicators"],
            relevant_data["events"],
            relevant_data["institutional"],
            symbol_name,
            session
        )

        # Get current price if symbol exists
        current_price = None
        price_change_24h = None
        if symbol_obj:
            # In a real implementation, we'd get current price from market data feed
            # For now, we'll note that live pricing would come from the market data provider
            pass

        return {
            "symbol": symbol_name,
            "display_name": display_name,
            "bias_context": bias_context,
            "bullish_factors": bullish_factors,
            "bearish_factors": bearish_factors,
            "key_catalysts": key_catalysts,
            "risks": risks,
            "current_price": current_price,
            "price_change_24h": price_change_24h,
            "analysis_timestamp": target_time.isoformat(),
            "data_summary": {
                "news_items": len(relevant_data["news"]),
                "economic_indicators": len(relevant_data["indicators"]),
                "geopolitical_events": len(relevant_data["events"]),
                "institutional_info": len(relevant_data["institutional"]),
            }
        }

    async def _determine_bias_context(
        self,
        news: List[MarketNews],
        indicators: List[EconomicIndicator],
        events: List[GeopoliticalEvent],
        institutional: List[InstitutionalInfo],
        instrument_symbol: str,
        session: TradingSession,
    ) -> str:
        """Determine the overall bias/context for an instrument."""
        # Simple sentiment analysis based on news relevance and tone
        bullish_score = 0
        bearish_score = 0

        # Analyze news sentiment
        for news_item in news:
            text = f"{news_item.headline} {news_item.summary or ''}".lower()
            # Simple keyword-based sentiment (would use NLP in production)
            bullish_indicators = ["rise", "gain", "up", "bullish", "positive", "strong", "beat", "exceed"]
            bearish_indicators = ["fall", "drop", "down", "bearish", "negative", "weak", "miss", "below"]

            for indicator in bullish_indicators:
                if indicator in text:
                    bullish_score += 1
            for indicator in bearish_indicators:
                if indicator in text:
                    bearish_score += 1

        # Analyze economic indicators
        for indicator in indicators:
            if indicator.actual_value and indicator.forecast_value:
                if indicator.actual_value > indicator.forecast_value:
                    # Better than expected = bullish for risk assets, bearish for safe havens
                    if instrument_symbol == "US30":
                        bullish_score += 2
                    else:  # GOLD
                        bearish_score += 1  # Generally bearish for gold
                else:
                    # Worse than expected = bearish for risk assets, bullish for safe havens
                    if instrument_symbol == "US30":
                        bearish_score += 2
                    else:  # GOLD
                        bullish_score += 1  # Generally bullish for gold

        # Determine final bias
        if bullish_score > bearish_score + 2:
            return "Bullish"
        elif bearish_score > bullish_score + 2:
            return "Bearish"
        else:
            return "Neutral/Mixed"

    async def _identify_bullish_factors(
        self,
        news: List[MarketNews],
        indicators: List[EconomicIndicator],
        events: List[GeopoliticalEvent],
        institutional: List[InstitutionalInfo],
        instrument_symbol: str,
        session: TradingSession,
    ) -> List[str]:
        """Identify bullish factors for the instrument."""
        factors = []

        # Extract from news
        for news_item in news[:10]:  # Top 10 most recent
            text = f"{news_item.headline} {news_item.summary or ''}".lower()
            if any(word in text for word in ["rise", "gain", "up", "bullish", "positive", "strong", "beat", "exceed", "upgrade", "outperform"]):
                # Extract a meaningful phrase
                if news_item.headline:
                    factors.append(news_item.headline[:100] + ("..." if len(news_item.headline) > 100 else ""))

        # Extract from indicators
        for indicator in indicators[:5]:
            if indicator.actual_value and indicator.forecast_value:
                if indicator.actual_value > indicator.forecast_value:
                    if instrument_symbol == "US30" or indicator.name in ["GDP", "PMI", "Employment", "Retail Sales"]:
                        factors.append(f"{indicator.name}: {indicator.actual_value} vs forecast {indicator.forecast_value} {indicator.unit or ''} - Better than expected")
                    elif instrument_symbol == "XAUUSD" and indicator.name in ["USD Index", "DXY", "Real Yields"]:
                        factors.append(f"{indicator.name}: {indicator.actual_value} vs forecast {indicator.forecast_value} - Weak USD/yields supportive")

        # Extract from institutional
        for info in institutional[:3]:
            if info.summary and ("bullish" in info.summary.lower() or "positive" in info.summary.lower()):
                factors.append(f"{info.institution}: {info.summary[:80] + ('...' if len(info.summary) > 80 else '')}")

        # Add session-specific factors
        session_factors = {
            TradingSession.ASIAN: [
                "Asian market liquidity and overnight flows",
                "China economic data influence",
                "Yen carry trade dynamics"
            ],
            TradingSession.LONDON: [
                "European market opening",
                "London gold fix influence",
                "European economic data releases"
            ],
            TradingSession.NEW_YORK: [
                "US market open and economic data",
                "Fed speakers and policy expectations",
                "Corporate earnings and US-specific news"
            ]
        }

        factors.extend(session_factors.get(session, []))

        # Deduplicate and limit
        unique_factors = list(dict.fromkeys(factors))  # Preserves order and removes duplicates
        return unique_factors[:8]  # Top 8 factors

    async def _identify_bearish_factors(
        self,
        news: List[MarketNews],
        indicators: List[EconomicIndicator],
        events: List[GeopoliticalEvent],
        institutional: List[InstitutionalInfo],
        instrument_symbol: str,
        session: TradingSession,
    ) -> List[str]:
        """Identify bearish factors for the instrument."""
        factors = []

        # Extract from news
        for news_item in news[:10]:  # Top 10 most recent
            text = f"{news_item.headline} {news_item.summary or ''}".lower()
            if any(word in text for word in ["fall", "drop", "down", "bearish", "negative", "weak", "miss", "below", "downgrade", "underperform"]):
                # Extract a meaningful phrase
                if news_item.headline:
                    factors.append(news_item.headline[:100] + ("..." if len(news_item.headline) > 100 else ""))

        # Extract from indicators
        for indicator in indicators[:5]:
            if indicator.actual_value and indicator.forecast_value:
                if indicator.actual_value < indicator.forecast_value:
                    if instrument_symbol == "US30" or indicator.name in ["GDP", "PMI", "Employment", "Retail Sales"]:
                        factors.append(f"{indicator.name}: {indicator.actual_value} vs forecast {indicator.forecast_value} {indicator.unit or ''} - Worse than expected")
                    elif instrument_symbol == "XAUUSD" and indicator.name in ["USD Index", "DXY", "Real Yields"]:
                        factors.append(f"{indicator.name}: {indicator.actual_value} vs forecast {indicator.forecast_value} - Strong USD/yields negative")

        # Extract from institutional
        for info in institutional[:3]:
            if info.summary and ("bearish" in info.summary.lower() or "negative" in info.summary.lower()):
                factors.append(f"{info.institution}: {info.summary[:80] + ('...' if len(info.summary) > 80 else '')}")

        # Add session-specific factors
        session_factors = {
            TradingSession.ASIAN: [
                "Asian market volatility and geopolitical tensions",
                "Currency fluctuations in emerging markets",
                "Commodity demand concerns from China"
            ],
            TradingSession.LONDON: [
                "European Central Bank policy uncertainty",
                "Brexit-related market impacts",
                "European economic growth concerns"
            ],
            TradingSession.NEW_YORK: [
                "US fiscal policy and debt ceiling concerns",
                "Inflation persistence worries",
                "Geopolitical risk-off sentiment"
            ]
        }

        factors.extend(session_factors.get(session, []))

        # Deduplicate and limit
        unique_factors = list(dict.fromkeys(factors))
        return unique_factors[:8]  # Top 8 factors

    async def _identify_key_catalysts(
        self,
        news: List[MarketNews],
        indicators: List[EconomicIndicator],
        events: List[GeopoliticalEvent],
        institutional: List[InstitutionalInfo],
        session: TradingSession,
        target_time: datetime,
        look_ahead_hours: int = 8,
    ) -> List[str]:
        """Identify key catalysts to watch during the session."""
        catalysts = []

        # Look for upcoming economic indicators
        cutoff_time = target_time + timedelta(hours=look_ahead_hours)
        upcoming_indicators = [
            ind for ind in indicators
            if ind.release_time and target_time <= ind.release_time <= cutoff_time
        ]

        for indicator in upcoming_indicators[:5]:  # Top 5 upcoming
            time_str = indicator.release_time.strftime("%H:%M UTC") if indicator.release_time else "TBD"
            catalysts.append(
                f"{indicator.name} release ({time_str}): "
                f"Forecast {indicator.forecast_value or 'TBD'} {indicator.unit or ''}, "
                f"Previous {indicator.previous_value or 'TBD'} {indicator.unit or ''}"
            )

        # Look for scheduled events (central bank speeches, etc.)
        # In production, this would come from economic calendars
        session_events = {
            TradingSession.ASIAN: [
                "Tokyo session open (00:00 UTC)",
                "Sydney session open (21:00 UTC previous day)",
                "Chinese economic data releases",
                "BOJ policy updates"
            ],
            TradingSession.LONDON: [
                "London session open (07:00 UTC)",
                "European market open (08:00 UTC)",
                "ECB speeches and policy updates",
                "UK economic data releases"
            ],
            TradingSession.NEW_YORK: [
                "NY session open (12:00 UTC)",
                "US market open (13:30 UTC)",
                "Fed speakers and FOMC minutes releases",
                "US economic data releases (CPI, jobs, GDP, etc.)"
            ]
        }

        catalysts.extend(session_events.get(session, []))

        # Add breaking news catalysts
        breaking_news = [n for n in news if n.relevance_level == RelevanceLevel.CRITICAL][:3]
        for news in breaking_news:
            catalysts.append(f"Breaking: {news.headline[:80] + ('...' if len(news.headline) > 80 else '')}")

        return catalysts[:6]  # Top 6 catalysts

    async def _identify_risks(
        self,
        news: List[MarketNews],
        indicators: List[EconomicIndicator],
        events: List[GeopoliticalEvent],
        institutional: List[InstitutionalInfo],
        instrument_symbol: str,
        session: TradingSession,
    ) -> List[str]:
        """Identify key risks for the instrument."""
        risks = []

        # Extract from news - risk-related language
        for news_item in news[:10]:
            text = f"{news_item.headline} {news_item.summary or ''}".lower()
            if any(word in text for word in ["risk", "uncertainty", "volatility", "concern", "worry", "fear", "threat", "danger", "crisis"]):
                if news_item.headline:
                    risks.append(news_item.headline[:100] + ("..." if len(news_item.headline) > 100 else ""))

        # Extract from indicators - unexpected volatility or misses
        for indicator in indicators[:5]:
            if indicator.actual_value and indicator.forecast_value:
                miss_size = abs(indicator.actual_value - indicator.forecast_value)
                # Significant miss (>0.5% for rates, >1% for others)
                if miss_size > 0.5:  # Simplified threshold
                    risks.append(
                        f"{indicator.name}: Actual {indicator.actual_value} vs forecast {indicator.forecast_value} "
                        f"{indicator.unit or ''} - Significant miss creates uncertainty"
                    )

        # Extract from geopolitical events
        high_risk_events = [e for e in events if e.impact_level in [RelevanceLevel.CRITICAL, RelevanceLevel.HIGH]][:3]
        for event in high_risk_events:
            risks.append(f"Geopolitical: {event.title[:80] + ('...' if len(event.title) > 80 else '')} - {event.impact_level.value} impact")

        # Extract from institutional - warnings or cautions
        for info in institutional[:3]:
            if info.summary and any(word in info.summary.lower() for word in ["caution", "warn", "risk", "concern", "uncertain"]):
                risks.append(f"{info.institution}: {info.summary[:80] + ('...' if len(info.summary) > 80 else '')}")

        # Add session-specific risks
        session_risks = {
            TradingSession.ASIAN: [
                "Overnight gap risk from US markets",
                "Asian currency volatility",
                "Commodity price sensitivity to USD fluctuations"
            ],
            TradingSession.LONDON: [
                "European market overlap volatility (London/New York)",
                "Energy price volatility impact",
                "Bank of England policy uncertainty"
            ],
            TradingSession.NEW_YORK: [
                "End-of-day positioning and profit-taking",
                "Weekend gap risk preparation",
                "Month-end/quarter-end rebalancing flows"
            ]
        }

        risks.extend(session_risks.get(session, []))

        # Deduplicate and limit
        unique_risks = list(dict.fromkeys(risks))
        return unique_risks[:6]  # Top 6 risks

    async def _get_session_events_to_watch(
        self,
        db: Session,
        session: TradingSession,
        target_time: datetime,
        window_info: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Get specific market events to watch during this session."""
        events_to_watch = []

        # Define the session time window
        session_start = target_time.replace(
            hour=window_info["start_hour"],
            minute=0,
            second=0,
            microsecond=0
        )
        session_end = target_time.replace(
            hour=window_info["end_hour"],
            minute=0,
            second=0,
            microsecond=0
        )

        # If we're past the session end, look at next occurrence
        if target_time.hour >= window_info["end_hour"]:
            session_start = session_start + timedelta(days=1)
            session_end = session_end + timedelta(days=1)

        # Get economic indicators scheduled during this session
        db = self.data_manager.get_session(Domain.MARKET)
        try:
            session_indicators = (
                db.query(EconomicIndicator)
                .filter(
                    and_(
                        EconomicIndicator.release_time >= session_start,
                        EconomicIndicator.release_time <= session_end,
                    )
                )
                .order_by(EconomicIndicator.release_time)
                .limit(10)
                .all()
            )

            for indicator in session_indicators:
                events_to_watch.append({
                    "type": "economic_indicator",
                    "title": f"{indicator.name} Release",
                    "time": indicator.release_time.strftime("%H:%M UTC") if indicator.release_time else "TBD",
                    "importance": "high" if indicator.name in ["NFP", "CPI", "FOMC", "GDP"] else "medium",
                    "forecast": f"{indicator.forecast_value or 'TBD'} {indicator.unit or ''}",
                    "previous": f"{indicator.previous_value or 'TBD'} {indicator.unit or ''}",
                    "description": indicator.description or f"{indicator.name} economic indicator release"
                })

        finally:
            db.close()

        # Add standard session markers
        events_to_watch.extend([
            {
                "type": "session_open",
                "title": f"{window_info['name']} Open",
                "time": f"{window_info['start_hour']:02d}:00 UTC",
                "importance": "medium",
                "description": f"Start of the {window_info['name']} trading session"
            },
            {
                "type": "session_close",
                "title": f"{window_info['name']} Close",
                "time": f"{window_info['end_hour']:02d}:00 UTC",
                "importance": "medium",
                "description": f"End of the {window_info['name']} trading session"
            }
        ])

        # Sort by time
        events_to_watch.sort(key=lambda x: x["time"] if x["time"] != "TBD" else "23:59")
        return events_to_watch[:10]  # Top 10 events to watch

    async def _generate_executive_summary(
        self,
        gold_analysis: Dict[str, Any],
        us30_analysis: Dict[str, Any],
        news: List[MarketNews],
        indicators: List[EconomicIndicator],
        session: TradingSession,
        target_time: datetime,
    ) -> str:
        """Generate an executive summary of the session briefing."""
        session_names = {
            TradingSession.ASIAN: "Asian",
            TradingSession.LONDON: "London",
            TradingSession.NEW_YORK: "New York"
        }

        session_name = session_names[session]
        gold_bias = gold_analysis["bias_context"]
        us30_bias = us30_analysis["bias_context"]

        # Count high-impact items
        critical_news = [n for n in news if n.relevance_level == RelevanceLevel.CRITICAL]
        high_impact_indicators = [i for i in indicators if i.impact_level in [RelevanceLevel.CRITICAL, RelevanceLevel.HIGH]]

        summary_parts = [
            f"{session_name} session overview as of {target_time.strftime('%H:%M UTC')}. ",
            f"Market sentiment shows {gold_bias.lower()} bias for GOLD and {us30_bias.lower()} bias for US30. "
        ]

        if critical_news:
            summary_parts.append(
                f"{len(critical_news)} breaking news items requiring immediate attention. "
            )

        if high_impact_indicators:
            summary_parts.append(
                f"{len(high_impact_indicators)} high-impact economic releases are either recent or upcoming. "
            )

        summary_parts.append(
            "Focus remains on USD dynamics, yield environment, and central bank policy expectations "
            f"as key drivers for both precious metals and equities markets."
        )

        return "".join(summary_parts)

    async def _generate_valta_assessment(
        self,
        gold_analysis: Dict[str, Any],
        us30_analysis: Dict[str, Any],
        session: TradingSession,
        target_time: datetime,
    ) -> str:
        """Generate Valta Prime's assessment of the session."""
        session_names = {
            TradingSession.ASIAN: "Asian",
            TradingSession.LONDON: "London",
            TradingSession.NEW_YORK: "New York"
        }

        session_name = session_names[session]
        gold_bias = gold_analysis["bias_context"]
        us30_bias = us30_analysis["bias_context"]

        # Count conviction factors
        gold_bullish = len(gold_analysis["bullish_factors"])
        gold_bearish = len(gold_analysis["bearish_factors"])
        us30_bullish = len(us30_analysis["bullish_factors"])
        us30_bearish = len(us30_analysis["bearish_factors"])

        assessment_parts = [
            f"Valta Prime Assessment - {session_name} Session: ",
            f"Based on analysis of market data, economic indicators, and institutional positioning, "
        ]

        # Overall market tone
        if gold_bias == us30_bias:
            if gold_bias == "Bullish":
                assessment_parts.append(
                    f"concurrent bullish bias in both GOLD and US30 suggests risk-on sentiment "
                    f"with confidence in economic growth prospects. "
                )
            elif gold_bias == "Bearish":
                assessment_parts.append(
                    f"concurrent bearish bias in both GOLD and US30 suggests risk-off sentiment "
                    f"with flight to safety concerns outweighing growth optimism. "
                )
            else:
                assessment_parts.append(
                    f"mixed/neutral bias in both instruments suggests market indecision "
                    f"awaiting clearer directional cues from economic data or policy developments. "
                )
        else:
            assessment_parts.append(
                f"divergent bias between GOLD ({gold_bias}) and US30 ({us30_bias}) suggests "
                f"sector-specific drivers are dominating over broad market themes. "
            )

        # Conviction level
        total_bullish = gold_bullish + us30_bullish
        total_bearish = gold_bearish + us30_bearish

        if abs(total_bullish - total_bearish) >= 4:
            assessment_parts.append(
                "High conviction view supported by clear fundamental drivers. "
            )
        elif abs(total_bullish - total_bearish) >= 2:
            assessment_parts.append(
                "Moderate conviction with some conflicting signals requiring careful position sizing. "
            )
        else:
            assessment_parts.append(
                "Low conviction environment with balanced risks/opportunities favors selective, high-conviction setups only. "
            )

        assessment_parts.append(
            "As always, this analysis represents probabilistic assessment rather than certainty. "
            f"Position sizing and risk management remain paramount regardless of directional bias."
        )

        return "".join(assessment_parts)

    async def get_latest_report(
        self,
        session: Optional[TradingSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the latest generated report for a session or the most recent overall."""
        if session:
            # Look for today's report for this session
            today = datetime.utcnow().date()
            cache_key = f"{session.value}_{today}"
            if cache_key in self._reports_cache:
                return self._reports_cache[cache_key]

            # Look for any recent report from this session
            session_reports = [
                (k, v) for k, v in self._reports_cache.items()
                if k.startswith(f"{session.value}_")
            ]
            if session_reports:
                # Return the most recent
                session_reports.sort(key=lambda x: x[1]["generated_at"], reverse=True)
                return session_reports[0][1]
            return None
        else:
            # Return the most recent report overall
            if not self._reports_cache:
                return None

            latest = max(self._reports_cache.values(), key=lambda x: x["generated_at"])
            return latest

    def clear_cache(self, older_than_hours: int = 24):
        """Clear old reports from cache."""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        keys_to_remove = [
            k for k, v in self._reports_cache.items()
            if datetime.fromisoformat(v["generated_at"]) < cutoff_time
        ]
        for key in keys_to_remove:
            del self._reports_cache[key]
        logger.info(f"Cleared {len(keys_to_remove)} old reports from cache")