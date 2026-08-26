"""Research Ingestion Layer — News, Web, and Content providers."""

from .news_ingestion import NewsIngestionProvider, NewsProviderConfig, NewsArticleRaw
from .web_ingestion import WebIngestionProvider, WebProviderConfig, CrawlResult
from .content_processor import ContentProcessor, ProcessingConfig, ProcessedContent
from .research_synthesizer import ResearchSynthesizer, SynthesisConfig, TopicCluster, SectionDraft
from .pipeline import ResearchPipeline

__all__ = [
    "NewsIngestionProvider",
    "NewsProviderConfig",
    "NewsArticleRaw",
    "WebIngestionProvider",
    "WebProviderConfig",
    "CrawlResult",
    "ContentProcessor",
    "ProcessingConfig",
    "ProcessedContent",
    "ResearchSynthesizer",
    "SynthesisConfig",
    "TopicCluster",
    "SectionDraft",
    "ResearchPipeline",
]