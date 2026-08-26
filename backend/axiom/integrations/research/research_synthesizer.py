"""Research Synthesizer — Generates research reports from processed content."""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from collections import defaultdict

from pydantic import BaseModel, Field

# Import enums (these are fine for Pydantic)
from axiom.data.models import (
    ResearchStatus,
    ContentType,
    Sentiment,
    ContentPiece,
    KnowledgeEntry,
)
# Forward references for type hints
ResearchReport = "ResearchReport"

from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class SynthesisConfig(BaseModel):
    """Research synthesis configuration."""

    min_sources_per_topic: int = 3
    max_report_sections: int = 10
    min_section_content_pieces: int = 2
    similarity_threshold: float = 0.7
    enable_deduplication: bool = True
    enable_cross_referencing: bool = True
    auto_publish_threshold: float = 0.75
    max_report_length: int = 10000
    default_timeframe_hours: int = 24


class TopicCluster(BaseModel):
    """Cluster of related content pieces."""

    topic: str
    symbols: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    pieces: List["ContentPiece"] = Field(default_factory=list)
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    key_entities: Dict[str, List[str]] = Field(default_factory=dict)
    time_range: Tuple[datetime, datetime]
    relevance_score: float = 0.0

    class Config:
        arbitrary_types_allowed = True


class SectionDraft(BaseModel):
    """Draft report section."""

    title: str
    topic: str
    content: str
    sources: List["ContentPiece"] = Field(default_factory=list)
    symbols: List[str] = Field(default_factory=list)
    sentiment: Optional[Sentiment] = None
    confidence: float = 0.0

    class Config:
        arbitrary_types_allowed = True


class ResearchSynthesizer:
    """Synthesizes research reports from ingested content."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: Optional[SynthesisConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config or SynthesisConfig()
        self.logger = logger or RuntimeLogger()

    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """Simple Jaccard similarity on word sets."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def _cluster_by_topic(
        self, pieces: List[ContentPiece]
    ) -> List[TopicCluster]:
        """Cluster content pieces by topic."""
        if not pieces:
            return []

        clusters: List[TopicCluster] = []
        used = set()

        for piece in pieces:
            if piece.id in used:
                continue

            # Start new cluster
            cluster = TopicCluster(
                topic=piece.topic or piece.categories[0] if piece.categories else "general",
                symbols=piece.symbols or [],
                categories=piece.categories or [],
                pieces=[piece],
                time_range=(piece.published_at or datetime.utcnow(), piece.published_at or datetime.utcnow()),
            )
            used.add(piece.id)

            # Find similar pieces
            for other in pieces:
                if other.id in used:
                    continue

                # Check topic overlap
                topic_match = False
                if cluster.topic and other.topic:
                    sim = self._compute_text_similarity(cluster.topic, other.topic)
                    if sim >= self.config.similarity_threshold:
                        topic_match = True

                # Check symbol overlap
                symbol_overlap = set(cluster.symbols) & set(other.symbols or [])
                if symbol_overlap:
                    topic_match = True

                # Check category overlap
                category_overlap = set(cluster.categories) & set(other.categories or [])
                if category_overlap:
                    topic_match = True

                if topic_match:
                    cluster.pieces.append(other)
                    used.add(other.id)
                    cluster.symbols = list(set(cluster.symbols + (other.symbols or [])))
                    cluster.categories = list(set(cluster.categories + (other.categories or [])))
                    if other.published_at:
                        cluster.time_range = (
                            min(cluster.time_range[0], other.published_at),
                            max(cluster.time_range[1], other.published_at),
                        )

            # Only keep clusters with minimum pieces
            if len(cluster.pieces) >= self.config.min_sources_per_topic:
                # Calculate relevance score
                cluster.relevance_score = self._calculate_cluster_relevance(cluster)

                # Aggregate sentiment
                for p in cluster.pieces:
                    if p.sentiment:
                        cluster.sentiment_distribution[p.sentiment.value] = (
                            cluster.sentiment_distribution.get(p.sentiment.value, 0) + 1
                        )

                # Aggregate entities
                for p in cluster.pieces:
                    for ent_type, entities in (p.entities or {}).items():
                        if ent_type not in cluster.key_entities:
                            cluster.key_entities[ent_type] = []
                        for ent in entities:
                            if ent not in cluster.key_entities[ent_type]:
                                cluster.key_entities[ent_type].append(ent)

                clusters.append(cluster)

        # Sort by relevance
        clusters.sort(key=lambda c: c.relevance_score, reverse=True)
        return clusters[:self.config.max_report_sections]

    def _calculate_cluster_relevance(self, cluster: TopicCluster) -> float:
        """Calculate relevance score for a cluster."""
        score = 0.0

        # Number of pieces
        score += min(len(cluster.pieces) * 0.1, 0.5)

        # Quality average
        avg_quality = sum(p.quality_score or 0 for p in cluster.pieces) / len(cluster.pieces)
        score += avg_quality * 0.3

        # Recency (newer = higher)
        now = datetime.utcnow()
        avg_age_hours = sum(
            (now - (p.published_at or now)).total_seconds() / 3600
            for p in cluster.pieces
        ) / len(cluster.pieces)
        if avg_age_hours <= 1:
            score += 0.2
        elif avg_age_hours <= 6:
            score += 0.15
        elif avg_age_hours <= 24:
            score += 0.1

        # Symbol diversity
        if len(cluster.symbols) >= 5:
            score += 0.1
        elif len(cluster.symbols) >= 2:
            score += 0.05

        return min(score, 1.0)

    async def _generate_section(self, cluster: TopicCluster) -> SectionDraft:
        """Generate a report section from a cluster."""
        pieces = cluster.pieces

        # Determine section title
        if cluster.symbols:
            title = f"{', '.join(cluster.symbols[:3])}: {cluster.topic.title()}"
        else:
            title = cluster.topic.title()

        # Aggregate content
        content_parts = []
        for piece in pieces:
            if piece.summary:
                content_parts.append(f"**{piece.title}** ({piece.source_type.value}): {piece.summary}")
            elif piece.content:
                content_parts.append(f"**{piece.title}**: {piece.content[:300]}...")

        # Determine overall sentiment
        sentiment_counts = cluster.sentiment_distribution
        total = sum(sentiment_counts.values())
        if total > 0:
            dominant = max(sentiment_counts.items(), key=lambda x: x[1])
            sentiment = Sentiment(dominant[0]) if dominant[0] in [s.value for s in Sentiment] else None
        else:
            sentiment = None

        # Calculate confidence
        confidence = cluster.relevance_score

        # Build section content
        intro = f"This section covers {len(pieces)} sources"
        if cluster.symbols:
            intro += f" related to {', '.join(cluster.symbols[:5])}"
        intro += f" over the period {cluster.time_range[0].strftime('%Y-%m-%d')} to {cluster.time_range[1].strftime('%Y-%m-%d')}.\n\n"

        body = "\n\n".join(content_parts)

        # Add entity summary
        entity_summary = ""
        if cluster.key_entities:
            entity_parts = []
            for ent_type, entities in cluster.key_entities.items():
                if entities:
                    entity_parts.append(f"**{ent_type}**: {', '.join(entities[:5])}")
            if entity_parts:
                entity_summary = "\n\n**Key Entities**:\n" + "\n".join(entity_parts)

        full_content = intro + body + entity_summary

        return SectionDraft(
            title=title,
            topic=cluster.topic,
            content=full_content,
            sources=pieces,
            symbols=cluster.symbols,
            sentiment=sentiment,
            confidence=confidence,
        )

    def _generate_executive_summary(
        self, sections: List[SectionDraft], report_topic: str
    ) -> str:
        """Generate executive summary from sections."""
        if not sections:
            return f"No significant findings for {report_topic} in the analyzed period."

        summary_parts = [
            f"**Executive Summary: {report_topic}**\n",
            f"Analysis of {sum(len(s.sources) for s in sections)} sources across {len(sections)} key topics.\n",
        ]

        # Top findings
        for i, section in enumerate(sections[:5], 1):
            symbol_str = f" ({', '.join(section.symbols[:3])})" if section.symbols else ""
            summary_parts.append(
                f"{i}. **{section.title}**: "
                f"Based on {len(section.sources)} sources"
                f"{' with ' + section.sentiment.value + ' sentiment' if section.sentiment else ''}"
                f"{symbol_str}. Confidence: {section.confidence:.0%}\n"
            )

        return "\n".join(summary_parts)

    def _generate_conclusion(
        self, sections: List[SectionDraft], overall_sentiment: Optional[Sentiment]
    ) -> str:
        """Generate conclusion from sections."""
        if not sections:
            return "Insufficient data for conclusions."

        conclusions = ["**Conclusion**\n"]

        # Overall sentiment
        if overall_sentiment:
            conclusions.append(f"Overall market sentiment: **{overall_sentiment.value.upper()}**.\n")

        # Key themes
        all_symbols = set()
        all_categories = set()
        for section in sections:
            all_symbols.update(section.symbols)

        if all_symbols:
            conclusions.append(f"Key symbols covered: {', '.join(sorted(all_symbols)[:10])}.\n")

        # Source diversity
        source_types = set()
        for section in sections:
            for source in section.sources:
                source_types.add(source.source_type)
        conclusions.append(f"Source diversity: {len(source_types)} types ({', '.join(s.value for s in source_types)}).\n")

        # Confidence
        avg_confidence = sum(s.confidence for s in sections) / len(sections)
        conclusions.append(f"Average confidence across sections: {avg_confidence:.0%}.\n")

        return "\n".join(conclusions)

    async def synthesize_report(
        self,
        pieces: List[ContentPiece],
        topic: str,
        author: str = "Axiom Research",
        timeframe_hours: Optional[int] = None,
    ) -> ResearchReport:
        """Synthesize a research report from content pieces."""
        if not pieces:
            return ResearchReport(
                topic=topic,
                author=author,
                status=ResearchStatus.COMPLETED,
                executive_summary="No content available for synthesis.",
                conclusion="No data to analyze.",
                sections=[],
                sources_count=0,
            )

        # Filter by timeframe
        if timeframe_hours:
            cutoff = datetime.utcnow() - timedelta(hours=timeframe_hours)
            pieces = [p for p in pieces if p.published_at and p.published_at >= cutoff]

        # Cluster by topic
        clusters = self._cluster_by_topic(pieces)

        # Generate sections
        sections = []
        for cluster in clusters:
            section = await self._generate_section(cluster)
            sections.append(section)

        # Overall sentiment
        all_sentiments = defaultdict(int)
        for section in sections:
            for source in section.sources:
                if source.sentiment:
                    all_sentiments[source.sentiment.value] += 1

        overall_sentiment = None
        if all_sentiments:
            dominant = max(all_sentiments.items(), key=lambda x: x[1])
            overall_sentiment = Sentiment(dominant[0]) if dominant[0] in [s.value for s in Sentiment] else None

        # Generate executive summary and conclusion
        executive_summary = self._generate_executive_summary(sections, topic)
        conclusion = self._generate_conclusion(sections, overall_sentiment)

        # Build sections JSON
        sections_json = [
            {
                "title": s.title,
                "topic": s.topic,
                "content": s.content,
                "sources_count": len(s.sources),
                "symbols": s.symbols,
                "sentiment": s.sentiment.value if s.sentiment else None,
                "confidence": s.confidence,
            }
            for s in sections
        ]

        # Calculate overall confidence
        avg_confidence = sum(s.confidence for s in sections) / len(sections) if sections else 0.0

        report = ResearchReport(
            topic=topic,
            author=author,
            status=ResearchStatus.COMPLETED if avg_confidence >= self.config.auto_publish_threshold else ResearchStatus.DRAFT,
            executive_summary=executive_summary,
            conclusion=conclusion,
            sections=sections_json,
            sources_count=sum(len(s.sources) for s in sections),
            overall_sentiment=overall_sentiment,
            confidence_score=avg_confidence,
            timeframe_start=min(
                (min(p.published_at for p in pieces if p.published_at),)
            )[0] if any(p.published_at for p in pieces) else None,
            timeframe_end=max(
                (max(p.published_at for p in pieces if p.published_at),)
            )[0] if any(p.published_at for p in pieces) else None,
            symbols_covered=list(set().union(*[set(s.symbols) for s in sections])) if sections else [],
            categories_covered=list(set().union(*[set(s.categories) for s in sections])) if sections else [],
        )

        return report

    async def synthesize_from_clusters(
        self,
        clusters: List[TopicCluster],
        topic: str,
        author: str = "Axiom Research",
    ) -> ResearchReport:
        """Synthesize report from pre-computed clusters."""
        sections = []
        for cluster in clusters:
            section = await self._generate_section(cluster)
            sections.append(section)

        all_sentiments = defaultdict(int)
        for section in sections:
            for source in section.sources:
                if source.sentiment:
                    all_sentiments[source.sentiment.value] += 1

        overall_sentiment = None
        if all_sentiments:
            dominant = max(all_sentiments.items(), key=lambda x: x[1])
            overall_sentiment = Sentiment(dominant[0]) if dominant[0] in [s.value for s in Sentiment] else None

        executive_summary = self._generate_executive_summary(sections, topic)
        conclusion = self._generate_conclusion(sections, overall_sentiment)

        sections_json = [
            {
                "title": s.title,
                "topic": s.topic,
                "content": s.content,
                "sources_count": len(s.sources),
                "symbols": s.symbols,
                "sentiment": s.sentiment.value if s.sentiment else None,
                "confidence": s.confidence,
            }
            for s in sections
        ]

        avg_confidence = sum(s.confidence for s in sections) / len(sections) if sections else 0.0

        return ResearchReport(
            topic=topic,
            author=author,
            status=ResearchStatus.COMPLETED if avg_confidence >= self.config.auto_publish_threshold else ResearchStatus.DRAFT,
            executive_summary=executive_summary,
            conclusion=conclusion,
            sections=sections_json,
            sources_count=sum(len(s.sources) for s in sections),
            overall_sentiment=overall_sentiment,
            confidence_score=avg_confidence,
            symbols_covered=list(set().union(*[set(s.symbols) for s in sections])) if sections else [],
            categories_covered=list(set().union(*[set(s.categories) for s in sections])) if sections else [],
        )

    async def update_knowledge_base(
        self, pieces: List[ContentPiece]
    ) -> List[KnowledgeEntry]:
        """Extract knowledge entries from content pieces."""
        entries = []

        # Group by symbol
        by_symbol = defaultdict(list)
        for piece in pieces:
            for sym in piece.symbols or []:
                by_symbol[sym].append(piece)

        for symbol, symbol_pieces in by_symbol.items():
            # Latest sentiment
            sentiments = [p.sentiment for p in symbol_pieces if p.sentiment]
            if sentiments:
                from collections import Counter
                sentiment_counts = Counter(s.value for s in sentiments)
                dominant_sentiment = Sentiment(sentiment_counts.most_common(1)[0][0])

                # Key events
                events = []
                for p in symbol_pieces[:5]:
                    if p.summary:
                        events.append(f"{p.published_at.strftime('%Y-%m-%d')}: {p.summary[:200]}")

                entry = KnowledgeEntry(
                    key=f"symbol:{symbol}:latest",
                    title=f"{symbol} - Latest Market Intelligence",
                    summary=f"Recent sentiment: {dominant_sentiment.value}. {len(symbol_pieces)} sources analyzed.",
                    content="\n\n".join(events),
                    category="market_intelligence",
                    tags=[symbol, "market", "intelligence", dominant_sentiment.value],
                    symbols=[symbol],
                    entities={},
                    confidence=min(len(symbol_pieces) / 10.0, 1.0),
                    source_urls=[p.source_url for p in symbol_pieces if p.source_url],
                    source_type="news_synthesis",
                )
                entries.append(entry)

        # Topic-based knowledge
        by_category = defaultdict(list)
        for piece in pieces:
            for cat in piece.categories or []:
                by_category[cat].append(piece)

        for category, cat_pieces in by_category.items():
            if len(cat_pieces) >= self.config.min_sources_per_topic:
                entry = KnowledgeEntry(
                    key=f"topic:{category}:overview",
                    title=f"{category.title()} - Overview",
                    summary=f"Synthesis of {len(cat_pieces)} sources on {category}.",
                    content="\n\n".join([
                        f"- {p.title} ({p.source_type.value}): {p.summary[:200]}"
                        for p in cat_pieces[:10] if p.summary
                    ]),
                    category="topic_overview",
                    tags=[category, "overview", "synthesis"],
                    symbols=list(set().union(*[set(p.symbols or []) for p in cat_pieces])),
                    entities={},
                    confidence=min(len(cat_pieces) / 20.0, 1.0),
                    source_urls=[p.source_url for p in cat_pieces if p.source_url],
                    source_type="topic_synthesis",
                )
                entries.append(entry)

        return entries