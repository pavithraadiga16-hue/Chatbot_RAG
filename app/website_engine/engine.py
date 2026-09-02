"""
Website Engine Main Controller
===============================

Orchestrates web crawling, structured JSON knowledge persistence, semantic search,
NLP aliases matching, and verified question-answering for institution websites.
"""

import time
from typing import Optional
from app.core.logging import get_logger
from app.website_engine.models import (
    CrawledPage,
    CrawlRequest,
    KnowledgeSection,
    WebsiteAnswer,
    WebsiteQAItem,
    WebsiteSearchHit,
    WebsiteUrlEntry,
)
from app.website_engine.crawler import crawler
from app.website_engine.repository import website_repo
from app.website_engine.searcher import website_searcher
from app.website_engine.answer_generator import website_answer_generator

logger = get_logger(__name__)


class WebsiteEngine:
    """Central engine for institution website crawling, indexing, and question answering."""

    async def crawl_and_index(
        self,
        institution_id: str,
        urls: list[WebsiteUrlEntry],
    ) -> list[CrawledPage]:
        """
        Crawl a list of URLs for an institution, clean, chunk, extract JSON & Q&As, and store.

        Args:
            institution_id: Target institution slug (e.g. 'sjbhs')
            urls: List of WebsiteUrlEntry items

        Returns:
            List of indexed CrawledPage models
        """
        start_time = time.monotonic()
        logger.info(
            "website_engine_crawl_started",
            institution_id=institution_id,
            url_count=len(urls),
        )

        crawled_pages = await crawler.crawl_urls(institution_id, urls)

        # Persist all successfully crawled pages into MongoDB
        for page in crawled_pages:
            if page.status == "success":
                await website_repo.save_crawled_page(page)

        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "website_engine_crawl_completed",
            institution_id=institution_id,
            duration_ms=duration_ms,
            pages_indexed=sum(1 for p in crawled_pages if p.status == "success"),
        )
        return crawled_pages

    async def search_and_answer(
        self,
        institution_id: str,
        question: str,
        role: Optional[str] = None,
    ) -> WebsiteAnswer:
        """
        Search stored website knowledge and synthesize a verified answer.

        Args:
            institution_id: Institution identifier (e.g. 'sjbhs')
            question: Natural language question
            role: Optional role filter ('website', 'student', 'parent', etc.)

        Returns:
            WebsiteAnswer with formatted markdown, confidence, and source citations
        """
        start_time = time.monotonic()

        hits = await website_searcher.search(
            institution_id=institution_id,
            question=question,
            role=role,
            top_k=2,
            min_score_threshold=0.30,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)

        answer = website_answer_generator.generate_answer(
            question=question,
            institution_id=institution_id,
            hits=hits,
            execution_time_ms=duration_ms,
        )

        logger.info(
            "website_engine_answered",
            institution_id=institution_id,
            role=role,
            matched_sections=len(hits),
            matched_alias=answer.matched_alias,
            confidence=answer.confidence,
            duration_ms=duration_ms,
        )
        return answer

    async def get_pages(self, institution_id: str) -> list[CrawledPage]:
        """Fetch all indexed pages for an institution."""
        return await website_repo.get_pages_by_institution(institution_id)

    async def get_sections(self, institution_id: str) -> list[KnowledgeSection]:
        """Fetch all indexed semantic sections for an institution."""
        return await website_repo.get_all_sections(institution_id)

    async def get_qa_items(self, institution_id: str, role: Optional[str] = None) -> list[WebsiteQAItem]:
        """Fetch all structured WebsiteQAItems with NLP aliases for an institution."""
        return await website_repo.get_all_qa_items(institution_id, role=role)

    async def save_qa_item(self, item: WebsiteQAItem) -> None:
        """Save/update a single WebsiteQAItem with custom NLP aliases."""
        await website_repo.save_qa_item(item)

    async def delete_qa_item(self, institution_id: str, qa_id: str) -> bool:
        """Delete a WebsiteQAItem."""
        return await website_repo.delete_qa_item(institution_id, qa_id)

    async def bulk_save_qa_items(self, institution_id: str, items: list[WebsiteQAItem]) -> int:
        """Bulk save WebsiteQAItems."""
        return await website_repo.bulk_save_qa_items(institution_id, items)

    async def delete_page(self, institution_id: str, page_id_or_url: str) -> bool:
        """Delete an indexed page."""
        return await website_repo.delete_page(institution_id, page_id_or_url)

    async def clear_all(self, institution_id: str) -> int:
        """Clear all knowledge for an institution."""
        return await website_repo.clear_institution_knowledge(institution_id)


website_engine = WebsiteEngine()
