"""Web Ingestion Provider — Crawls and extracts content from web pages."""

import asyncio
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, SecretStr
from readability import Document

from axiom.data.models import ContentType, ContentStatus, WebPage
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class WebProviderConfig(BaseModel):
    """Configuration for web ingestion."""

    name: str
    enabled: bool = True
    base_urls: List[str] = Field(default_factory=list)
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    max_depth: int = 2
    max_pages_per_domain: int = 100
    rate_limit_rpm: int = 30
    timeout_seconds: int = 30
    respect_robots_txt: bool = True
    user_agent: str = "AxiomBot/1.0 (+https://axiom.ai/bot)"
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    follow_redirects: bool = True
    max_content_size: int = 10 * 1024 * 1024  # 10MB
    extract_links: bool = True
    extract_images: bool = False
    javascript_render: bool = False  # Would need Playwright/Selenium


class CrawlResult(BaseModel):
    """Result of a crawl operation."""

    url: str
    status_code: int
    content: Optional[str] = None
    html: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    meta_tags: Dict[str, str] = Field(default_factory=dict)
    content_hash: Optional[str] = None
    error: Optional[str] = None
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    response_headers: Dict[str, str] = Field(default_factory=dict)
    final_url: Optional[str] = None  # After redirects


class WebIngestionProvider:
    """Web crawling and content extraction provider."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: WebProviderConfig,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config
        self.logger = logger or RuntimeLogger()
        self._session: Optional[aiohttp.ClientSession] = None
        self._visited: Set[str] = set()
        self._domain_counts: Dict[str, int] = {}
        self._robots_cache: Dict[str, Any] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "User-Agent": self.config.user_agent,
                    **self.config.custom_headers,
                },
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _is_allowed_domain(self, url: str) -> bool:
        """Check if domain is allowed."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if domain in [d.lower() for d in self.config.blocked_domains]:
            return False

        if self.config.allowed_domains:
            return any(domain.endswith(d.lower()) for d in self.config.allowed_domains)

        return True

    def _normalize_url(self, url: str, base: Optional[str] = None) -> str:
        """Normalize URL."""
        if base:
            url = urljoin(base, url)
        parsed = urlparse(url)
        # Remove fragment
        return parsed._replace(fragment="").geturl()

    def _should_crawl(self, url: str, depth: int) -> bool:
        """Check if URL should be crawled."""
        if depth > self.config.max_depth:
            return False

        normalized = self._normalize_url(url)
        if normalized in self._visited:
            return False

        if not self._is_allowed_domain(normalized):
            return False

        parsed = urlparse(normalized)
        domain = parsed.netloc.lower()
        count = self._domain_counts.get(domain, 0)
        if count >= self.config.max_pages_per_domain:
            return False

        return True

    async def _fetch_page(self, url: str) -> CrawlResult:
        """Fetch and parse a single page."""
        session = await self._get_session()
        normalized = self._normalize_url(url)

        try:
            async with session.get(
                normalized,
                allow_redirects=self.config.follow_redirects,
                max_redirects=5,
            ) as resp:
                if resp.status >= 400:
                    return CrawlResult(
                        url=normalized,
                        status_code=resp.status,
                        error=f"HTTP {resp.status}",
                    )

                # Check content size
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > self.config.max_content_size:
                    return CrawlResult(
                        url=normalized,
                        status_code=resp.status,
                        error="Content too large",
                    )

                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    return CrawlResult(
                        url=normalized,
                        status_code=resp.status,
                        error=f"Non-HTML content: {content_type}",
                    )

                html = await resp.text()
                final_url = str(resp.url)

                # Parse with readability
                doc = Document(html)
                title = doc.title()
                content = doc.summary()

                # Parse with BeautifulSoup for metadata
                soup = BeautifulSoup(html, "html.parser")

                # Description
                description = None
                for meta in soup.find_all("meta"):
                    if meta.get("name") == "description" or meta.get("property") == "og:description":
                        description = meta.get("content")
                        break

                # Meta tags
                meta_tags = {}
                for meta in soup.find_all("meta"):
                    name = meta.get("name") or meta.get("property")
                    content_val = meta.get("content")
                    if name and content_val:
                        meta_tags[name] = content_val

                # Links
                links = []
                if self.config.extract_links:
                    for a in soup.find_all("a", href=True):
                        href = self._normalize_url(a["href"], final_url)
                        if self._is_allowed_domain(href):
                            links.append(href)

                # Images
                images = []
                if self.config.extract_images:
                    for img in soup.find_all("img", src=True):
                        src = self._normalize_url(img["src"], final_url)
                        images.append(src)

                # Content hash
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16] if content else None

                return CrawlResult(
                    url=normalized,
                    final_url=final_url,
                    status_code=resp.status,
                    html=html,
                    title=title,
                    description=description,
                    content=content,
                    links=links,
                    images=images,
                    meta_tags=meta_tags,
                    content_hash=content_hash,
                    response_headers=dict(resp.headers),
                )

        except asyncio.TimeoutError:
            return CrawlResult(url=normalized, status_code=408, error="Timeout")
        except aiohttp.ClientError as e:
            return CrawlResult(url=normalized, status_code=0, error=str(e))
        except Exception as e:
            self.logger.error(f"Fetch error for {normalized}: {e}")
            return CrawlResult(url=normalized, status_code=0, error=str(e))

    async def crawl(self, start_urls: Optional[List[str]] = None) -> List[CrawlResult]:
        """Crawl starting from URLs."""
        urls = start_urls or self.config.base_urls
        if not urls:
            self.logger.warning("No start URLs configured")
            return []

        results = []
        queue = [(url, 0) for url in urls]

        while queue:
            url, depth = queue.pop(0)

            if not self._should_crawl(url, depth):
                continue

            normalized = self._normalize_url(url)
            self._visited.add(normalized)

            parsed = urlparse(normalized)
            domain = parsed.netloc.lower()
            self._domain_counts[domain] = self._domain_counts.get(domain, 0) + 1

            result = await self._fetch_page(normalized)
            results.append(result)

            # Add links to queue
            if depth < self.config.max_depth:
                for link in result.links:
                    if self._should_crawl(link, depth + 1):
                        queue.append((link, depth + 1))

            # Small delay to be respectful
            await asyncio.sleep(60 / self.config.rate_limit_rpm)

        return results

    async def crawl_single(self, url: str) -> CrawlResult:
        """Crawl a single URL without following links."""
        normalized = self._normalize_url(url)
        if not self._is_allowed_domain(normalized):
            return CrawlResult(url=normalized, status_code=403, error="Domain not allowed")
        return await self._fetch_page(normalized)

    def to_web_page(self, result: CrawlResult) -> WebPage:
        """Convert crawl result to WebPage model."""
        return WebPage(
            url=result.final_url or result.url,
            canonical_url=result.url,
            title=result.title,
            description=result.description,
            content=result.content,
            html=result.html,
            meta_tags=result.meta_tags,
            links=result.links,
            images=result.images,
            content_hash=result.content_hash,
            status=ContentStatus.PUBLISHED if result.status_code == 200 else ContentStatus.FAILED,
            error_message=result.error,
            crawled_at=result.crawled_at,
            response_headers=result.response_headers,
        )