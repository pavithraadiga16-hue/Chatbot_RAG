"""
Website Knowledge Engine Subsystem
===================================

Provides web page crawling, boilerplate cleaning, semantic section chunking,
MongoDB knowledge DB persistence, fast fuzzy search, and question answering.
"""

from app.website_engine.models import (
    CrawledPage,
    CrawlRequest,
    KnowledgeSection,
    WebsiteAnswer,
    WebsiteSearchHit,
    WebsiteUrlEntry,
)
from app.website_engine.engine import website_engine, WebsiteEngine
from app.website_engine.repository import website_repo, WebsiteRepository
from app.website_engine.searcher import website_searcher, WebsiteKnowledgeSearcher

__all__ = [
    "website_engine",
    "WebsiteEngine",
    "website_repo",
    "WebsiteRepository",
    "website_searcher",
    "WebsiteKnowledgeSearcher",
    "CrawledPage",
    "CrawlRequest",
    "KnowledgeSection",
    "WebsiteAnswer",
    "WebsiteSearchHit",
    "WebsiteUrlEntry",
]
