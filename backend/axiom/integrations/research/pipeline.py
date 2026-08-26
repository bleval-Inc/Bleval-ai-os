"""Research Ingestion Pipeline — Orchestrates the full ingestion flow."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from axiom.data.models import (
    ResearchReport,
    ContentPiece,
    KnowledgeEntry,
    ContentType,
)
from axiom.data.repositories import ResearchRepository
from axiom.runtime.logging import RuntimeLogger

if TYPE_CHECKING:
    from axiom.integrations.research.news_ingestion import NewsArticleRaw
    from axiom.integrations.research import (
        NewsIngestionProvider,
        NewsProviderConfig,
        WebIngestionProvider,
        WebProviderConfig,
        ContentProcessor,
        ProcessingConfig,
        ResearchSynthesizer,
        SynthesisConfig,
    )
    from axiom.integrations.layer import IntegrationLayer


class ResearchPipeline:
    """Complete research ingestion and synthesis pipeline."""

    def __init__(
        self,
        integration_layer: "IntegrationLayer",
        repository: ResearchRepository,
        news_configs: List["NewsProviderConfig"],
        web_config: Optional["WebProviderConfig"] = None,
        processing_config: Optional["ProcessingConfig"] = None,
        synthesis_config: Optional["SynthesisConfig"] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        # Lazy import to avoid circular dependency
        from axiom.integrations.research import (
            NewsIngestionProvider,
            WebIngestionProvider,
            ContentProcessor,
            ResearchSynthesizer,
        )

        # Initialize components
        self.news_provider = NewsIngestionProvider(
            integration_layer, news_configs, self.logger
        )
        self.web_provider = None
        if web_config:
            self.web_provider = WebIngestionProvider(integration_layer, web_config, self.logger)

        self.processor = ContentProcessor(integration_layer, processing_config, self.logger)
        self.synthesizer = ResearchSynthesizer(integration_layer, synthesis_config, self.logger)

    async def run_news_ingestion(
        self,
        since: Optional[datetime] = None,
        limit_per_provider: int = 50,
    ) -> Dict[str, Any]:
        """Run news ingestion cycle."""
        stats = {
            "fetched": 0,
            "processed": 0,
            "stored": 0,
            "knowledge_created": 0,
            "errors": [],
        }

        try:
            # Fetch raw news
            raw_articles = await self.news_provider.fetch_all_news(since, limit_per_provider)
            stats["fetched"] = len(raw_articles)

            # Process each article
            processed_pieces = []
            for raw in raw_articles:
                try:
                    # Convert to NewsArticle model (would use repository.upsert_news_article)
                    # For now, create ProcessedContent directly
                    # This is a simplified flow - real impl would store raw first
                    pass
                except Exception as e:
                    stats["errors"].append(f"Processing {raw.external_id}: {e}")

            stats["processed"] = len(processed_pieces)

            # Store processed pieces
            for piece in processed_pieces:
                try:
                    await self.repository.create_content_piece(
                        content_id=piece.content_id,
                        content_type=piece.content_type,
                        title=piece.title,
                        content=piece.content,
                        summary=piece.summary,
                        source_url=piece.metadata.get("url"),
                        source_type=piece.metadata.get("source", "unknown"),
                        author=piece.metadata.get("author"),
                        published_at=datetime.fromisoformat(piece.metadata["published_at"]) if piece.metadata.get("published_at") else None,
                        language=piece.language,
                        sentiment=piece.sentiment,
                        sentiment_score=piece.sentiment_score,
                        entities=piece.entities,
                        keywords=piece.keywords,
                        categories=piece.categories,
                        topics=piece.topics,
                        symbols=piece.symbols,
                        word_count=piece.word_count,
                        reading_time_minutes=piece.reading_time_minutes,
                        quality_score=piece.quality_score,
                    )
                    stats["stored"] += 1
                except Exception as e:
                    stats["errors"].append(f"Storing {piece.content_id}: {e}")

            # Generate knowledge entries
            if processed_pieces:
                knowledge = await self.synthesizer.update_knowledge_base(
                    [await self._to_content_piece(p) for p in processed_pieces]
                )
                for entry in knowledge:
                    try:
                        await self.repository.upsert_knowledge_entry(entry)
                        stats["knowledge_created"] += 1
                    except Exception as e:
                        stats["errors"].append(f"Knowledge {entry.key}: {e}")

        except Exception as e:
            stats["errors"].append(f"Pipeline error: {e}")
            self.logger.error(f"News ingestion pipeline failed: {e}")

        return stats

    async def run_web_ingestion(
        self,
        start_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run web crawling and ingestion cycle."""
        if not self.web_provider:
            return {"error": "Web provider not configured"}

        stats = {
            "crawled": 0,
            "processed": 0,
            "stored": 0,
            "errors": [],
        }

        try:
            # Crawl
            results = await self.web_provider.crawl(start_urls)
            stats["crawled"] = len(results)

            # Process each page
            for result in results:
                if result.status_code != 200 or not result.content:
                    continue

                try:
                    processed = await self.processor.process_web_page(
                        self.web_provider.to_web_page(result)
                    )
                    stats["processed"] += 1

                    # Store
                    await self.repository.create_content_piece(
                        content_id=processed.content_id,
                        content_type=processed.content_type,
                        title=processed.title,
                        content=processed.content,
                        summary=processed.summary,
                        source_url=processed.metadata.get("url"),
                        source_type="web",
                        language=processed.language,
                        sentiment=processed.sentiment,
                        sentiment_score=processed.sentiment_score,
                        entities=processed.entities,
                        keywords=processed.keywords,
                        categories=processed.categories,
                        symbols=processed.symbols,
                        word_count=processed.word_count,
                        reading_time_minutes=processed.reading_time_minutes,
                        quality_score=processed.quality_score,
                    )
                    stats["stored"] += 1

                except Exception as e:
                    stats["errors"].append(f"Processing {result.url}: {e}")

        except Exception as e:
            stats["errors"].append(f"Web pipeline error: {e}")
            self.logger.error(f"Web ingestion pipeline failed: {e}")

        return stats

    async def synthesize_topic_report(
        self,
        topic: str,
        timeframe_hours: int = 24,
        author: str = "Axiom Research",
    ) -> Optional[ResearchReport]:
        """Synthesize a research report for a topic."""
        try:
            # Get relevant content pieces
            pieces = await self.repository.list_content_pieces(
                topic=topic,
                limit=100,
            )

            # Filter by timeframe
            cutoff = datetime.utcnow() - timedelta(hours=timeframe_hours)
            pieces = [p for p in pieces if p.published_at and p.published_at >= cutoff]

            if not pieces:
                self.logger.warning(f"No content for topic {topic} in timeframe")
                return None

            # Synthesize report
            report = await self.synthesizer.synthesize_report(
                pieces, topic, author, timeframe_hours
            )

            # Store report
            stored = await self.repository.create_research_report(
                topic=report.topic,
                author=report.author,
                status=report.status,
                executive_summary=report.executive_summary,
                conclusion=report.conclusion,
                sections=report.sections,
                sources_count=report.sources_count,
                overall_sentiment=report.overall_sentiment,
                confidence_score=report.confidence_score,
                timeframe_start=report.timeframe_start,
                timeframe_end=report.timeframe_end,
                symbols_covered=report.symbols_covered,
                categories_covered=report.categories_covered,
            )

            return stored

        except Exception as e:
            self.logger.error(f"Report synthesis failed for {topic}: {e}")
            return None

    async def run_full_cycle(
        self,
        topics: List[str],
        news_since: Optional[datetime] = None,
        web_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run complete research cycle: ingest -> process -> synthesize."""
        results = {
            "news": {},
            "web": {},
            "reports": {},
            "started_at": datetime.utcnow(),
            "completed_at": None,
        }

        # News ingestion
        self.logger.info("Starting news ingestion...")
        results["news"] = await self.run_news_ingestion(news_since)

        # Web ingestion
        if self.web_provider:
            self.logger.info("Starting web ingestion...")
            results["web"] = await self.run_web_ingestion(web_urls)

        # Synthesize reports for each topic
        for topic in topics:
            self.logger.info(f"Synthesizing report for {topic}...")
            report = await self.synthesize_topic_report(topic)
            if report:
                results["reports"][topic] = {
                    "id": report.id,
                    "status": report.status.value,
                    "confidence": report.confidence_score,
                    "sources": report.sources_count,
                }

        results["completed_at"] = datetime.utcnow()
        return results

    async def _to_content_piece(self, processed) -> ContentPiece:
        """Helper to convert ProcessedContent to ContentPiece for repository."""
        return ContentPiece(
            content_id=processed.content_id,
            content_type=processed.content_type,
            title=processed.title,
            content=processed.content,
            summary=processed.summary,
            source_url=processed.metadata.get("url"),
            source_type=processed.metadata.get("source", "unknown"),
            author=processed.metadata.get("author"),
            published_at=datetime.fromisoformat(processed.metadata["published_at"]) if processed.metadata.get("published_at") else None,
            language=processed.language,
            sentiment=processed.sentiment,
            sentiment_score=processed.sentiment_score,
            entities=processed.entities,
            keywords=processed.keywords,
            categories=processed.categories,
            topics=processed.topics,
            symbols=processed.symbols,
            word_count=processed.word_count,
            reading_time_minutes=processed.reading_time_minutes,
            quality_score=processed.quality_score,
        )

    async def close(self):
        """Cleanup resources."""
        await self.news_provider.close()
        if self.web_provider:
            await self.web_provider.close()