"""News Ingestion Provider — Fetches and normalizes news from multiple sources."""

import asyncio
import hashlib
import hmac
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from urllib.parse import urlencode

import aiohttp
import feedparser
from pydantic import BaseModel, Field, SecretStr

from axiom.data.models import NewsSource, Sentiment
from axiom.runtime.logging import RuntimeLogger

if TYPE_CHECKING:
    from axiom.integrations.layer import IntegrationLayer


class NewsProviderConfig(BaseModel):
    """Configuration for a news provider."""

    name: str
    enabled: bool = True
    api_key: Optional[SecretStr] = None
    api_secret: Optional[SecretStr] = None
    base_url: str
    rate_limit_rpm: int = 60
    timeout_seconds: int = 30
    symbols_filter: List[str] = Field(default_factory=list)
    sources_filter: List[NewsSource] = Field(default_factory=list)
    min_relevance_score: float = 0.3
    custom_headers: Dict[str, str] = Field(default_factory=dict)


class NewsArticleRaw(BaseModel):
    """Raw news article from provider."""

    external_id: str
    title: str
    url: str
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: datetime
    source: NewsSource
    symbols: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    sentiment: Optional[Sentiment] = None
    sentiment_score: Optional[float] = None
    content_hash: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class NewsProviderBase(ABC):
    """Abstract base for news providers."""

    def __init__(self, config: NewsProviderConfig, logger: Optional[RuntimeLogger] = None):
        self.config = config
        self.logger = logger or RuntimeLogger()
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    @abstractmethod
    def source_type(self) -> NewsSource:
        """News source enum value."""
        pass

    @abstractmethod
    async def fetch_latest(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> List[NewsArticleRaw]:
        """Fetch latest articles."""
        pass

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.config.custom_headers,
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _compute_content_hash(self, title: str, content: str) -> str:
        """Compute content hash for deduplication."""
        combined = f"{title}:{content}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _filter_symbols(self, articles: List[NewsArticleRaw]) -> List[NewsArticleRaw]:
        """Filter articles by configured symbols."""
        if not self.config.symbols_filter:
            return articles
        filtered = []
        for article in articles:
            if any(sym in article.symbols for sym in self.config.symbols_filter):
                filtered.append(article)
            elif self._extract_symbols_from_text(article.title + " " + (article.content or "")):
                # Add extracted symbols
                extracted = self._extract_symbols_from_text(
                    article.title + " " + (article.content or "")
                )
                article.symbols.extend(extracted)
                if any(sym in self.config.symbols_filter for sym in extracted):
                    filtered.append(article)
        return filtered

    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """Extract stock/crypto symbols from text."""
        import re
        # Match $SYMBOL or SYMBOL/USDT patterns
        patterns = [
            r'\$([A-Z]{1,5})\b',  # $AAPL
            r'\b([A-Z]{2,5})/USDT?\b',  # BTC/USDT
            r'\b([A-Z]{2,5})USD\b',  # BTCUSD
        ]
        symbols = set()
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            symbols.update(matches)
        return list(symbols)


class NewsAPIProvider(NewsProviderBase):
    """NewsAPI.org provider."""

    @property
    def source_type(self) -> NewsSource:
        return NewsSource.NEWSAPI

    async def fetch_latest(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> List[NewsArticleRaw]:
        session = await self._get_session()
        params = {
            "apiKey": self.config.api_key.get_secret_value() if self.config.api_key else "",
            "pageSize": min(limit, 100),
            "language": "en",
            "sortBy": "publishedAt",
        }
        if since:
            params["from"] = since.strftime("%Y-%m-%d")

        url = f"{self.config.base_url}/v2/everything"
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                self.logger.error(f"NewsAPI error: {resp.status}")
                return []
            data = await resp.json()

        articles = []
        for item in data.get("articles", []):
            if not item.get("title") or item.get("title") == "[Removed]":
                continue
            article = NewsArticleRaw(
                external_id=hashlib.md5(item["url"].encode()).hexdigest()[:16],
                title=item["title"],
                url=item["url"],
                content=item.get("content"),
                summary=item.get("description"),
                author=item.get("author"),
                published_at=datetime.fromisoformat(
                    item["publishedAt"].replace("Z", "+00:00")
                ),
                source=self.source_type,
                raw_data=item,
            )
            article.content_hash = self._compute_content_hash(article.title, article.content or "")
            articles.append(article)

        return self._filter_symbols(articles)


class AlphaVantageNewsProvider(NewsProviderBase):
    """Alpha Vantage news provider."""

    @property
    def source_type(self) -> NewsSource:
        return NewsSource.ALPHA_VANTAGE

    async def fetch_latest(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> List[NewsArticleRaw]:
        session = await self._get_session()
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.config.api_key.get_secret_value() if self.config.api_key else "",
            "limit": min(limit, 1000),
        }
        if self.config.symbols_filter:
            params["tickers"] = ",".join(self.config.symbols_filter[:50])

        url = self.config.base_url
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                self.logger.error(f"AlphaVantage error: {resp.status}")
                return []
            data = await resp.json()

        articles = []
        for item in data.get("feed", []):
            article = NewsArticleRaw(
                external_id=item.get("url", "").split("/")[-1][:16],
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("summary"),
                summary=item.get("summary"),
                author=item.get("authors", [None])[0] if item.get("authors") else None,
                published_at=datetime.fromisoformat(
                    item["time_published"].replace("Z", "+00:00")
                ),
                source=self.source_type,
                symbols=item.get("ticker_sentiment", [{}])[0].get("ticker", "").split(",") if item.get("ticker_sentiment") else [],
                sentiment=Sentiment(item.get("overall_sentiment_label", "neutral").lower()),
                sentiment_score=item.get("overall_sentiment_score"),
                raw_data=item,
            )
            article.content_hash = self._compute_content_hash(article.title, article.content or "")
            articles.append(article)

        return self._filter_symbols(articles)


class CryptoPanicProvider(NewsProviderBase):
    """CryptoPanic news provider for crypto."""

    @property
    def source_type(self) -> NewsSource:
        return NewsSource.CRYPTO_PANIC

    async def fetch_latest(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> List[NewsArticleRaw]:
        session = await self._get_session()
        params = {
            "auth_token": self.config.api_key.get_secret_value() if self.config.api_key else "",
            "public": "true",
            "kind": "news",
            "limit": min(limit, 100),
        }
        if self.config.symbols_filter:
            params["currencies"] = ",".join(self.config.symbols_filter[:20])

        url = f"{self.config.base_url}/v1/posts/"
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                self.logger.error(f"CryptoPanic error: {resp.status}")
                return []
            data = await resp.json()

        articles = []
        for item in data.get("results", []):
            published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
            if since and published < since:
                continue

            currencies = [c["code"] for c in item.get("currencies", [])]
            article = NewsArticleRaw(
                external_id=str(item["id"]),
                title=item["title"],
                url=item["url"],
                content=item.get("body"),
                summary=item.get("body", "")[:500],
                published_at=published,
                source=self.source_type,
                symbols=currencies,
                sentiment=Sentiment(item.get("kind", "news").lower()),
                raw_data=item,
            )
            article.content_hash = self._compute_content_hash(article.title, article.content or "")
            articles.append(article)

        return self._filter_symbols(articles)


class RSSFeedProvider(NewsProviderBase):
    """Generic RSS feed provider."""

    def __init__(self, config: NewsProviderConfig, feed_urls: List[str], logger: Optional[RuntimeLogger] = None):
        super().__init__(config, logger)
        self.feed_urls = feed_urls

    @property
    def source_type(self) -> NewsSource:
        return NewsSource.CUSTOM

    async def fetch_latest(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> List[NewsArticleRaw]:
        articles = []
        for feed_url in self.feed_urls:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:limit]:
                    published = datetime(*entry.published_parsed[:6]) if entry.get("published_parsed") else datetime.utcnow()
                    if since and published < since:
                        continue

                    article = NewsArticleRaw(
                        external_id=hashlib.md5(entry.link.encode()).hexdigest()[:16],
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        content=entry.get("summary", "") or (entry.content[0].value if entry.get("content") else ""),
                        summary=entry.get("summary", "")[:500],
                        author=entry.get("author"),
                        published_at=published,
                        source=self.source_type,
                        categories=[tag.term for tag in entry.get("tags", [])],
                        raw_data={"feed": feed_url, "entry": dict(entry)},
                    )
                    article.content_hash = self._compute_content_hash(article.title, article.content or "")
                    articles.append(article)
            except Exception as e:
                self.logger.error(f"RSS feed error for {feed_url}: {e}")

        return self._filter_symbols(articles)


class NewsIngestionProvider:
    """Main news ingestion orchestrator."""

    def __init__(
        self,
        integration_layer: "IntegrationLayer",
        configs: List[NewsProviderConfig],
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.logger = logger or RuntimeLogger()
        self.providers: Dict[NewsSource, NewsProviderBase] = {}
        self._initialize_providers(configs)

    def _initialize_providers(self, configs: List[NewsProviderConfig]):
        """Initialize configured providers."""
        for config in configs:
            if not config.enabled:
                continue
            if "newsapi" in config.base_url.lower():
                self.providers[NewsSource.NEWSAPI] = NewsAPIProvider(config, self.logger)
            elif "alphavantage" in config.base_url.lower():
                self.providers[NewsSource.ALPHA_VANTAGE] = AlphaVantageNewsProvider(config, self.logger)
            elif "cryptopanic" in config.base_url.lower():
                self.providers[NewsSource.CRYPTO_PANIC] = CryptoPanicProvider(config, self.logger)
            elif config.base_url.startswith("http") and "rss" in config.base_url.lower():
                # Extract RSS URLs from custom config
                feed_urls = config.custom_headers.get("feed_urls", "").split(",")
                self.providers[NewsSource.CUSTOM] = RSSFeedProvider(config, [u.strip() for u in feed_urls], self.logger)
            else:
                self.logger.warning(f"Unknown provider type for {config.name}")

    async def fetch_all_news(
        self,
        since: Optional[datetime] = None,
        limit_per_provider: int = 50,
    ) -> List[NewsArticleRaw]:
        """Fetch news from all enabled providers."""
        tasks = []
        for provider in self.providers.values():
            tasks.append(provider.fetch_latest(since, limit_per_provider))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        for provider, result in zip(self.providers.values(), results):
            if isinstance(result, Exception):
                self.logger.error(f"Provider {provider.config.name} failed: {result}")
                continue
            all_articles.extend(result)

        # Deduplicate by content hash
        seen_hashes: Set[str] = set()
        unique_articles = []
        for article in all_articles:
            if article.content_hash and article.content_hash not in seen_hashes:
                seen_hashes.add(article.content_hash)
                unique_articles.append(article)

        # Sort by published date
        unique_articles.sort(key=lambda a: a.published_at, reverse=True)

        return unique_articles[:limit_per_provider * len(self.providers)]

    async def close(self):
        """Close all provider sessions."""
        for provider in self.providers.values():
            await provider.close()