"""Content Processor — Cleans, enriches, and structures raw content."""

import asyncio
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from axiom.data.models import (
    ContentPiece,
    ContentType,
    ContentStatus,
    Sentiment,
    KnowledgeEntry,
    NewsArticle,
    WebPage,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class ProcessingConfig(BaseModel):
    """Content processing configuration."""

    enable_cleaning: bool = True
    enable_summarization: bool = True
    enable_sentiment: bool = True
    enable_entity_extraction: bool = True
    enable_keyword_extraction: bool = True
    enable_classification: bool = True
    max_summary_length: int = 500
    min_content_length: int = 100
    language: str = "en"
    custom_stopwords: List[str] = Field(default_factory=list)
    entity_types: List[str] = Field(default_factory=lambda: ["PERSON", "ORG", "GPE", "MONEY", "DATE"])
    classification_categories: Dict[str, List[str]] = Field(default_factory=dict)


class ProcessedContent(BaseModel):
    """Processed content output."""

    content_id: str
    content_type: ContentType
    title: str
    content: str
    summary: Optional[str] = None
    cleaned_content: Optional[str] = None
    sentiment: Optional[Sentiment] = None
    sentiment_score: Optional[float] = None
    entities: Dict[str, List[str]] = Field(default_factory=dict)
    keywords: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    symbols: List[str] = Field(default_factory=list)
    language: str = "en"
    word_count: int = 0
    reading_time_minutes: int = 0
    quality_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentProcessor:
    """Content cleaning, enrichment, and structuring pipeline."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: Optional[ProcessingConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config or ProcessingConfig()
        self.logger = logger or RuntimeLogger()
        self._nlp = None  # Would initialize spaCy or similar

    async def _get_nlp(self):
        """Lazy load NLP pipeline."""
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("spaCy model not found, using basic processing")
                self._nlp = None
        return self._nlp

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\$\%\@\#\&]', '', text)

        # Fix common encoding issues
        text = text.replace('‘', "'").replace('’', "'")
        text = text.replace('“', '"').replace('”', '"')
        text = text.replace('–', '-').replace('—', '--')
        text = text.replace('…', '...')

        # Remove zero-width characters
        text = re.sub(r'[​-‏﻿]', '', text)

        return text.strip()

    def _extract_symbols(self, text: str) -> List[str]:
        """Extract financial symbols from text."""
        symbols = set()

        # $SYMBOL pattern
        for match in re.finditer(r'\$([A-Z]{1,5})\b', text):
            symbols.add(match.group(1))

        # SYMBOL/USDT or SYMBOL-USD patterns
        for match in re.finditer(r'\b([A-Z]{2,5})[/\-](USDT?|USD|BTC|ETH)\b', text):
            symbols.add(match.group(1))

        # Common crypto symbols
        crypto_symbols = {'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM'}
        for sym in crypto_symbols:
            if re.search(rf'\b{sym}\b', text, re.IGNORECASE):
                symbols.add(sym)

        return list(symbols)

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy or regex fallback."""
        entities = {
            "PERSON": [],
            "ORG": [],
            "GPE": [],  # Locations
            "MONEY": [],
            "DATE": [],
            "PRODUCT": [],
            "EVENT": [],
        }

        nlp = asyncio.run(self._get_nlp()) if self.config.enable_entity_extraction else None

        if nlp:
            doc = nlp(text[:100000])  # Limit for performance
            for ent in doc.ents:
                if ent.label_ in entities:
                    if ent.text not in entities[ent.label_]:
                        entities[ent.label_].append(ent.text)
        else:
            # Regex fallback for common patterns
            # Organizations (Inc., Corp., Ltd., etc.)
            org_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc\.|Corp\.|Ltd\.|LLC|Company|Corporation)\b'
            for match in re.finditer(org_pattern, text):
                entities["ORG"].append(match.group(0))

            # Money amounts
            money_pattern = r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|trillion|M|B|T))?'
            for match in re.finditer(money_pattern, text):
                entities["MONEY"].append(match.group(0))

            # Dates
            date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
            for match in re.finditer(date_pattern, text, re.IGNORECASE):
                entities["DATE"].append(match.group(0))

        return entities

    def _extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """Extract keywords using TF-IDF-like approach or spaCy."""
        nlp = asyncio.run(self._get_nlp()) if self.config.enable_keyword_extraction else None

        if nlp:
            doc = nlp(text[:50000])
            # Extract noun chunks and named entities
            keywords = []
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3 and len(chunk.text) > 2:
                    keywords.append(chunk.text.lower())
            # Add entities
            for ent in doc.ents:
                if len(ent.text) > 2:
                    keywords.append(ent.text.lower())
            # Frequency-based ranking
            from collections import Counter
            freq = Counter(keywords)
            return [kw for kw, _ in freq.most_common(top_k)]
        else:
            # Simple frequency-based extraction
            stopwords = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
                "be", "have", "has", "had", "do", "does", "did", "will", "would",
                "could", "should", "may", "might", "must", "can", "this", "that",
                "these", "those", "it", "its", "they", "them", "their", "we", "us",
                "our", "you", "your", "i", "me", "my", *set(self.config.custom_stopwords)
            }
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            filtered = [w for w in words if w not in stopwords]
            from collections import Counter
            freq = Counter(filtered)
            return [kw for kw, _ in freq.most_common(top_k)]

    def _classify_content(self, text: str, title: str) -> List[str]:
        """Classify content into categories."""
        categories = []
        combined = (title + " " + text).lower()

        # Financial categories
        financial_keywords = {
            "earnings": ["earnings", "revenue", "profit", "eps", "quarterly", "fiscal"],
            "mergers": ["merger", "acquisition", "buyout", "takeover", "merger"],
            "ipo": ["ipo", "initial public offering", "listing", "debut"],
            "crypto": ["bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft", "web3"],
            "stocks": ["stock", "share", "equity", "nasdaq", "nyse", "dow", "s&p"],
            "forex": ["forex", "currency", "exchange rate", "fx", "dollar", "euro"],
            "commodities": ["gold", "oil", "silver", "commodity", "futures"],
            "macro": ["inflation", "fed", "interest rate", "gdp", "unemployment", "cpi"],
            "tech": ["ai", "artificial intelligence", "machine learning", "cloud", "saas"],
            "regulation": ["sec", "regulation", "compliance", "law", "legal", "court"],
        }

        for cat, keywords in financial_keywords.items():
            if any(kw in combined for kw in keywords):
                categories.append(cat)

        # Use custom classification if configured
        for cat, keywords in self.config.classification_categories.items():
            if any(kw.lower() in combined for kw in keywords):
                categories.append(cat)

        return list(set(categories))

    async def _analyze_sentiment(self, text: str) -> Tuple[Optional[Sentiment], Optional[float]]:
        """Analyze sentiment using VADER or transformers."""
        if not self.config.enable_sentiment or not text:
            return None, None

        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            analyzer = SentimentIntensityAnalyzer()
            scores = analyzer.polarity_scores(text[:5000])
            compound = scores["compound"]

            if compound >= 0.05:
                return Sentiment.POSITIVE, compound
            elif compound <= -0.05:
                return Sentiment.NEGATIVE, compound
            else:
                return Sentiment.NEUTRAL, compound
        except ImportError:
            self.logger.warning("VADER not available, skipping sentiment")
            return None, None

    async def _summarize(self, text: str, max_length: int) -> Optional[str]:
        """Generate summary using extractive summarization."""
        if not self.config.enable_summarization or not text:
            return None

        nlp = await self._get_nlp()
        if not nlp:
            # Simple extractive: first N sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            summary = ' '.join(sentences[:3])
            return summary[:max_length]

        doc = nlp(text[:50000])
        # Score sentences by word frequency
        from collections import Counter
        word_freq = Counter(token.text.lower() for token in doc if not token.is_stop and token.is_alpha)

        sentences = list(doc.sents)
        sentence_scores = {}
        for sent in sentences:
            score = sum(word_freq.get(token.text.lower(), 0) for token in sent if not token.is_stop)
            sentence_scores[sent] = score

        # Top 3 sentences
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        summary = ' '.join(sent.text for sent, _ in top_sentences)
        return summary[:max_length]

    def _calculate_quality_score(
        self,
        content: str,
        title: str,
        entities: Dict[str, List[str]],
        keywords: List[str],
    ) -> float:
        """Calculate content quality score (0-1)."""
        score = 0.0

        # Length factor
        word_count = len(content.split())
        if word_count >= 300:
            score += 0.3
        elif word_count >= 100:
            score += 0.2
        elif word_count >= 50:
            score += 0.1

        # Title presence
        if title and len(title) > 10:
            score += 0.1

        # Entity richness
        total_entities = sum(len(v) for v in entities.values())
        if total_entities >= 10:
            score += 0.2
        elif total_entities >= 5:
            score += 0.15
        elif total_entities >= 2:
            score += 0.1

        # Keyword richness
        if len(keywords) >= 15:
            score += 0.2
        elif len(keywords) >= 8:
            score += 0.15
        elif len(keywords) >= 4:
            score += 0.1

        # Structure (paragraphs)
        paragraphs = content.count('\n\n') + 1
        if paragraphs >= 3:
            score += 0.1

        return min(score, 1.0)

    async def process_news(self, article: NewsArticle) -> ProcessedContent:
        """Process a news article."""
        raw_content = article.content or article.summary or ""
        cleaned = self._clean_text(raw_content) if self.config.enable_cleaning else raw_content

        # Extract components
        entities = self._extract_entities(cleaned) if self.config.enable_entity_extraction else {}
        keywords = self._extract_keywords(cleaned) if self.config.enable_keyword_extraction else []
        categories = self._classify_content(cleaned, article.title)
        symbols = self._extract_symbols(cleaned)
        sentiment, sentiment_score = await self._analyze_sentiment(cleaned)
        summary = await self._summarize(cleaned, self.config.max_summary_length)
        quality = self._calculate_quality_score(cleaned, article.title, entities, keywords)

        content_id = hashlib.md5(f"news:{article.external_id}:{article.source.value}".encode()).hexdigest()[:16]

        return ProcessedContent(
            content_id=content_id,
            content_type=ContentType.NEWS,
            title=article.title,
            content=cleaned,
            summary=summary,
            cleaned_content=cleaned,
            sentiment=sentiment or article.sentiment,
            sentiment_score=sentiment_score or article.sentiment_score,
            entities=entities,
            keywords=keywords,
            categories=categories,
            symbols=symbols,
            language=article.language or self.config.language,
            word_count=len(cleaned.split()),
            reading_time_minutes=max(1, len(cleaned.split()) // 200),
            quality_score=quality,
            metadata={
                "source": article.source.value,
                "external_id": article.external_id,
                "url": article.url,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "author": article.author,
            },
        )

    async def process_web_page(self, page: WebPage) -> ProcessedContent:
        """Process a web page."""
        raw_content = page.content or ""
        cleaned = self._clean_text(raw_content) if self.config.enable_cleaning else raw_content

        entities = self._extract_entities(cleaned) if self.config.enable_entity_extraction else {}
        keywords = self._extract_keywords(cleaned) if self.config.enable_keyword_extraction else []
        categories = self._classify_content(cleaned, page.title or "")
        symbols = self._extract_symbols(cleaned)
        sentiment, sentiment_score = await self._analyze_sentiment(cleaned)
        summary = await self._summarize(cleaned, self.config.max_summary_length)
        quality = self._calculate_quality_score(cleaned, page.title or "", entities, keywords)

        content_id = hashlib.md5(f"web:{page.url}".encode()).hexdigest()[:16]

        return ProcessedContent(
            content_id=content_id,
            content_type=ContentType.WEB,
            title=page.title or "Untitled",
            content=cleaned,
            summary=summary,
            cleaned_content=cleaned,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            entities=entities,
            keywords=keywords,
            categories=categories,
            symbols=symbols,
            language=page.language or self.config.language,
            word_count=len(cleaned.split()),
            reading_time_minutes=max(1, len(cleaned.split()) // 200),
            quality_score=quality,
            metadata={
                "url": page.url,
                "canonical_url": page.canonical_url,
                "meta_tags": page.meta_tags,
            },
        )

    async def process_to_content_piece(
        self, processed: ProcessedContent, research_report_id: Optional[int] = None
    ) -> ContentPiece:
        """Convert processed content to ContentPiece model."""
        return ContentPiece(
            content_id=processed.content_id,
            research_report_id=research_report_id,
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
            status=ContentStatus.PUBLISHED if processed.quality_score >= 0.3 else ContentStatus.DRAFT,
            extra_data=processed.metadata,
        )

    async def process_to_knowledge_entry(
        self, processed: ProcessedContent, category: str = "general"
    ) -> KnowledgeEntry:
        """Convert processed content to KnowledgeEntry."""
        return KnowledgeEntry(
            key=f"{processed.content_type.value}:{processed.content_id}",
            title=processed.title,
            summary=processed.summary or processed.content[:500],
            content=processed.content,
            category=category,
            tags=processed.keywords[:10],
            symbols=processed.symbols,
            entities=processed.entities,
            confidence=processed.quality_score,
            source_urls=[processed.metadata.get("url")] if processed.metadata.get("url") else [],
            source_type=processed.metadata.get("source", "unknown"),
        )