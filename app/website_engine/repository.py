"""
Website Knowledge Repository (Pure Database-Driven)
===================================================

Manages crawled website pages, full JSON document trees, and structured Q&A entities
in MongoDB (collections: `website_knowledge` and `website_qa_items`) with active memory cache.

NO hardcoded data or fallback mock functions. Purely driven by user-configured URLs and database storage.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.logging import get_logger
from app.website_engine.models import CrawledPage, KnowledgeSection, WebsiteQAItem

logger = get_logger(__name__)

# Active in-memory caches (invalidated on crawls, edits, or deletes)
_website_cache: dict[str, list[CrawledPage]] = {}
_custom_qa_cache: dict[str, list[WebsiteQAItem]] = {}


class WebsiteRepository:
    """Repository for managing website crawled knowledge and structured Q&A entities."""

    @property
    def db(self) -> Optional[AsyncIOMotorDatabase]:
        try:
            return get_database()
        except Exception:
            return None

    async def get_pages_by_institution(self, institution_id: str) -> list[CrawledPage]:
        """Fetch all crawled pages for an institution from MongoDB or cache."""
        inst_id = institution_id.strip().lower()

        # Check in-memory cache
        if inst_id in _website_cache:
            return _website_cache[inst_id]

        # Query MongoDB
        pages: list[CrawledPage] = []
        if self.db is not None:
            try:
                cursor = self.db.website_knowledge.find({"institution_id": inst_id})
                docs = await cursor.to_list(length=100)
                for d in docs:
                    pages.append(CrawledPage.model_validate(d))
            except Exception as e:
                logger.warning("website_repo_mongodb_read_failed", error=str(e), institution_id=inst_id)

        _website_cache[inst_id] = pages
        return pages

    async def get_all_sections(self, institution_id: str) -> list[KnowledgeSection]:
        """Fetch all flat KnowledgeSection objects for an institution."""
        pages = await self.get_pages_by_institution(institution_id)
        sections: list[KnowledgeSection] = []
        for page in pages:
            if page.status == "success":
                sections.extend(page.sections)
        return sections

    async def get_all_qa_items(self, institution_id: str, role: Optional[str] = None) -> list[WebsiteQAItem]:
        """
        Fetch all structured WebsiteQAItem entities (with NLP aliases) for an institution strictly from DB.
        Aggregates items from crawled pages and standalone custom Q&As.
        """
        inst_id = institution_id.strip().lower()
        pages = await self.get_pages_by_institution(inst_id)

        all_qa: dict[str, WebsiteQAItem] = {}

        # 1. Collect QA items from crawled pages
        for page in pages:
            for item in page.qa_items:
                if item.is_active:
                    k = item.field_key if item.field_key else item.id
                    all_qa[k] = item

        # 2. Collect from standalone in-memory cache (overrides page extracted items)
        custom_items = _custom_qa_cache.get(inst_id, [])
        for item in custom_items:
            if item.is_active:
                k = item.field_key if item.field_key else item.id
                all_qa[k] = item

        # 3. Query MongoDB standalone collection (persisted custom Q&A overrides)
        if self.db is not None:
            try:
                cursor = self.db.website_qa_items.find({"institution_id": inst_id, "is_active": True})
                docs = await cursor.to_list(length=250)
                for d in docs:
                    q_item = WebsiteQAItem.model_validate(d)
                    k = q_item.field_key if q_item.field_key else q_item.id
                    all_qa[k] = q_item
            except Exception as e:
                logger.debug("website_qa_mongodb_read_failed", error=str(e), institution_id=inst_id)

        result = list(all_qa.values())

        # Role filtering if role specified
        if role and role not in ["all", ""]:
            role_clean = role.strip().lower()
            result = [q for q in result if q.role in ["all", "", role_clean]]

        return result

    async def save_qa_item(self, item: WebsiteQAItem) -> None:
        """Upsert a single WebsiteQAItem in cache and MongoDB."""
        inst_id = item.institution_id.strip().lower()
        current = _custom_qa_cache.get(inst_id, [])
        updated = [q for q in current if q.id != item.id]
        updated.append(item)
        _custom_qa_cache[inst_id] = updated

        if self.db is not None:
            try:
                await self.db.website_qa_items.update_one(
                    {"id": item.id},
                    {"$set": item.model_dump(by_alias=True)},
                    upsert=True
                )
            except Exception as e:
                logger.error("website_qa_mongodb_save_failed", error=str(e), item_id=item.id)

    async def bulk_save_qa_items(self, institution_id: str, items: list[WebsiteQAItem]) -> int:
        """Bulk save or import Q&A items."""
        inst_id = institution_id.strip().lower()
        for item in items:
            await self.save_qa_item(item)
        return len(items)

    async def delete_qa_item(self, institution_id: str, qa_id: str) -> bool:
        """Delete a Q&A item from cache and MongoDB."""
        inst_id = institution_id.strip().lower()
        if inst_id in _custom_qa_cache:
            _custom_qa_cache[inst_id] = [q for q in _custom_qa_cache[inst_id] if q.id != qa_id]

        if inst_id in _website_cache:
            for page in _website_cache[inst_id]:
                page.qa_items = [q for q in page.qa_items if q.id != qa_id]

        if self.db is not None:
            try:
                res = await self.db.website_qa_items.delete_one({"id": qa_id, "institution_id": inst_id})
                # Also remove from any crawled page documents
                await self.db.website_knowledge.update_many(
                    {"institution_id": inst_id},
                    {"$pull": {"qa_items": {"id": qa_id}}}
                )
                return res.deleted_count > 0
            except Exception as e:
                logger.error("website_qa_mongodb_delete_failed", error=str(e), qa_id=qa_id)
        return True

    async def save_crawled_page(self, page: CrawledPage) -> None:
        """Save a single crawled page (with raw JSON data and Q&A items) into MongoDB and cache."""
        inst_id = page.institution_id.strip().lower()
        if inst_id not in _website_cache:
            _website_cache[inst_id] = []

        # Replace existing page with same URL or append
        _website_cache[inst_id] = [p for p in _website_cache[inst_id] if p.url != page.url]
        _website_cache[inst_id].append(page)

        if self.db is not None:
            try:
                doc = page.model_dump(by_alias=True)
                doc_id = doc.get("id") or doc.get("_id") or f"{inst_id}_{page.url}"
                doc["_id"] = doc_id
                await self.db.website_knowledge.update_one(
                    {"url": page.url, "institution_id": inst_id},
                    {"$set": doc},
                    upsert=True
                )

                # Upsert each extracted Q&A item into website_qa_items collection
                for q_item in page.qa_items:
                    q_doc = q_item.model_dump(by_alias=True)
                    q_doc["_id"] = q_item.id
                    await self.db.website_qa_items.update_one(
                        {"id": q_item.id},
                        {"$set": q_doc},
                        upsert=True
                    )

                logger.info(
                    "website_page_saved_to_db",
                    institution_id=inst_id,
                    url=page.url,
                    qa_items_count=len(page.qa_items),
                )
            except Exception as e:
                logger.error("website_page_db_save_failed", error=str(e), institution_id=inst_id, url=page.url)

    async def save_crawled_pages(self, institution_id: str, pages: list[CrawledPage]) -> None:
        """Save newly crawled pages (with raw JSON data and Q&A items) into MongoDB and cache."""
        for page in pages:
            await self.save_crawled_page(page)

    async def clear_institution_knowledge(self, institution_id: str) -> None:
        """Clear all stored website pages and Q&A items for an institution."""
        inst_id = institution_id.strip().lower()
        _website_cache.pop(inst_id, None)
        _custom_qa_cache.pop(inst_id, None)

        if self.db is not None:
            try:
                await self.db.website_knowledge.delete_many({"institution_id": inst_id})
                await self.db.website_qa_items.delete_many({"institution_id": inst_id})
                logger.info("website_knowledge_cleared_from_db", institution_id=inst_id)
            except Exception as e:
                logger.error("website_knowledge_db_clear_failed", error=str(e), institution_id=inst_id)


website_repo = WebsiteRepository()
