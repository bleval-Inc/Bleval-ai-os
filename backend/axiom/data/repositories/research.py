"""RESEARCH Repository — Data access for research, news, web content, knowledge."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.data.models import (
    ResearchBase,
    ResearchReport,
    NewsArticle,
    WebPage,
    ContentPiece,
    KnowledgeEntry,
    ResearchStatus,
    ContentType,
    ContentStatus,
    NewsSource,
    Sentiment,
)

if TYPE_CHECKING:
    from axiom.runtime.logging import RuntimeLogger


class ResearchRepository:
    """Repository for RESEARCH domain operations."""

    def __init__(self, session: AsyncSession, logger: Optional["RuntimeLogger"] = None) -> None:
        self.session = session
        from axiom.runtime.logging import RuntimeLogger
        self.logger = logger or RuntimeLogger()

    # ──────────────────────────────────────────────────────────────────────────────
    # RESEARCH REPORTS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_research_report(self, **kwargs) -> ResearchReport:
        """Create a new research report."""
        report = ResearchReport(**kwargs)
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_research_report(self, report_id: int) -> Optional[ResearchReport]:
        """Get research report by ID."""
        result = await self.session.execute(select(ResearchReport).where(ResearchReport.id == report_id))
        return result.scalar_one_or_none()

    async def list_research_reports(
        self,
        status: Optional[ResearchStatus] = None,
        author: Optional[str] = None,
        topic: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ResearchReport]:
        """List research reports."""
        query = select(ResearchReport).order_by(desc(ResearchReport.created_at))
        if status:
            query = query.where(ResearchReport.status == status)
        if author:
            query = query.where(ResearchReport.author == author)
        if topic:
            query = query.where(ResearchReport.topic.ilike(f"%{topic}%"))
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_report_status(
        self, report_id: int, status: ResearchStatus
    ) -> Optional[ResearchReport]:
        """Update report status."""
        report = await self.get_research_report(report_id)
        if report:
            report.status = status
            report.updated_at = datetime.utcnow()
            await self.session.flush()
        return report

    # ──────────────────────────────────────────────────────────────────────────────
    # NEWS ARTICLES
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_news_article(self, article: NewsArticle) -> NewsArticle:
        """Upsert news article by external_id."""
        existing = await self.get_news_by_external_id(article.external_id, article.source)
        if existing:
            for key, value in article.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(article)
            await self.session.flush()
            return article

    async def get_news_by_external_id(
        self, external_id: str, source: NewsSource
    ) -> Optional[NewsArticle]:
        """Get news article by external ID and source."""
        query = select(NewsArticle).where(
            and_(NewsArticle.external_id == external_id, NewsArticle.source == source)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_news(
        self,
        symbols: Optional[List[str]] = None,
        sources: Optional[List[NewsSource]] = None,
        sentiment: Optional[Sentiment] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[NewsArticle]:
        """Get latest news articles."""
        query = (
            select(NewsArticle)
            .where(NewsArticle.status == ContentStatus.PUBLISHED)
            .order_by(desc(NewsArticle.published_at))
        )
        if symbols:
            query = query.where(NewsArticle.symbols.overlap(symbols))
        if sources:
            query = query.where(NewsArticle.source.in_(sources))
        if sentiment:
            query = query.where(NewsArticle.sentiment == sentiment)
        if since:
            query = query.where(NewsArticle.published_at >= since)
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_news_by_symbol(
        self, symbol: str, hours: int = 24, limit: int = 50
    ) -> List[NewsArticle]:
        """Get news for a specific symbol."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(NewsArticle)
            .where(
                and_(
                    NewsArticle.symbols.contains([symbol]),
                    NewsArticle.published_at >= cutoff,
                    NewsArticle.status == ContentStatus.PUBLISHED,
                )
            )
            .order_by(desc(NewsArticle.published_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_news_sentiment_summary(
        self, symbol: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Get sentiment summary for symbol."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = select(
            NewsArticle.sentiment,
            func.count(NewsArticle.id).label("count"),
        ).where(
            and_(
                NewsArticle.symbols.contains([symbol]),
                NewsArticle.published_at >= cutoff,
            )
        ).group_by(NewsArticle.sentiment)
        result = await self.session.execute(query)
        return {row.sentiment.value: row.count for row in result.all()}

    # ──────────────────────────────────────────────────────────────────────────────
    # WEB PAGES
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_web_page(self, page: WebPage) -> WebPage:
        """Upsert web page by URL."""
        existing = await self.get_web_page_by_url(page.url)
        if existing:
            for key, value in page.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(page)
            await self.session.flush()
            return page

    async def get_web_page_by_url(self, url: str) -> Optional[WebPage]:
        """Get web page by URL."""
        query = select(WebPage).where(WebPage.url == url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_web_pages_by_domain(
        self, domain: str, limit: int = 100
    ) -> List[WebPage]:
        """Get web pages by domain."""
        query = (
            select(WebPage)
            .where(WebPage.url.ilike(f"%://{domain}%"))
            .order_by(desc(WebPage.crawled_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # CONTENT PIECES
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_content_piece(self, **kwargs) -> ContentPiece:
        """Create a content piece."""
        piece = ContentPiece(**kwargs)
        self.session.add(piece)
        await self.session.flush()
        return piece

    async def get_content_piece(self, piece_id: int) -> Optional[ContentPiece]:
        """Get content piece by ID."""
        result = await self.session.execute(select(ContentPiece).where(ContentPiece.id == piece_id))
        return result.scalar_one_or_none()

    async def list_content_pieces(
        self,
        content_type: Optional[ContentType] = None,
        status: Optional[ContentStatus] = None,
        topic: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContentPiece]:
        """List content pieces."""
        query = select(ContentPiece).order_by(desc(ContentPiece.created_at))
        if content_type:
            query = query.where(ContentPiece.content_type == content_type)
        if status:
            query = query.where(ContentPiece.status == status)
        if topic:
            query = query.where(ContentPiece.topic.ilike(f"%{topic}%"))
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_content_pieces_for_report(
        self, report_id: int
    ) -> List[ContentPiece]:
        """Get content pieces associated with a report."""
        query = (
            select(ContentPiece)
            .where(ContentPiece.research_report_id == report_id)
            .order_by(ContentPiece.sequence_order)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # KNOWLEDGE ENTRIES
    # ──────────────────────────────────────────────────────────────────────────────

    async def upsert_knowledge_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Upsert knowledge entry by key."""
        existing = await self.get_knowledge_by_key(entry.key)
        if existing:
            for key, value in entry.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            self.session.add(entry)
            await self.session.flush()
            return entry

    async def get_knowledge_by_key(self, key: str) -> Optional[KnowledgeEntry]:
        """Get knowledge entry by key."""
        query = select(KnowledgeEntry).where(KnowledgeEntry.key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search_knowledge(
        self,
        query_text: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[KnowledgeEntry]:
        """Full-text search knowledge base."""
        query = (
            select(KnowledgeEntry)
            .where(
                or_(
                    KnowledgeEntry.key.ilike(f"%{query_text}%"),
                    KnowledgeEntry.title.ilike(f"%{query_text}%"),
                    KnowledgeEntry.summary.ilike(f"%{query_text}%"),
                    KnowledgeEntry.content.ilike(f"%{query_text}%"),
                )
            )
            .order_by(desc(KnowledgeEntry.confidence))
        )
        if category:
            query = query.where(KnowledgeEntry.category == category)
        if tags:
            query = query.where(KnowledgeEntry.tags.overlap(tags))
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_knowledge_by_category(
        self, category: str, limit: int = 50
    ) -> List[KnowledgeEntry]:
        """Get knowledge entries by category."""
        query = (
            select(KnowledgeEntry)
            .where(KnowledgeEntry.category == category)
            .order_by(desc(KnowledgeEntry.confidence))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())