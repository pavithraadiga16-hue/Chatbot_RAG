"""
Website Knowledge & Crawler Admin API Routes
=============================================

REST API endpoints to crawl, manage, inspect, and query institution website knowledge,
structured JSON documents, and Q&A items with NLP Aliases.
"""

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.website_engine.models import (
    CrawledPage,
    CrawlRequest,
    KnowledgeSection,
    WebsiteAnswer,
    WebsiteQAItem,
    WebsiteUrlEntry,
)
from app.website_engine.engine import website_engine

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/website", tags=["Admin - Website Knowledge & Crawler"])


class TestSearchRequest(BaseModel):
    institution_id: str = Field(..., description="Target institution ID (e.g. 'sjbhs')")
    question: str = Field(..., description="Question to search against stored website knowledge")
    role: Optional[str] = Field(default="all", description="Role context ('all', 'website', 'student', etc.)")


class DeleteKnowledgeRequest(BaseModel):
    institution_id: str = Field(..., description="Target institution ID")
    page_id_or_url: Optional[str] = Field(default=None, description="Specific page ID or URL to delete. If omitted, clears all.")


class SaveQAItemRequest(BaseModel):
    id: Optional[str] = Field(default=None, description="Optional QA ID (auto-generated if omitted)")
    institution_id: str = Field(..., description="Target institution ID (e.g. 'sjbhs')")
    field_key: str = Field(..., description="Field/topic key (e.g. 'principal', 'motto', 'facilities')")
    category: str = Field(default="General", description="Category")
    question: str = Field(..., description="Canonical question")
    answer: str = Field(..., description="Answer text/markdown")
    aliases: list[str] = Field(default_factory=list, description="NLP Aliases (comma-separated triggers)")
    role: str = Field(default="all", description="Target role ('all', 'website', 'student', 'parent', 'staff')")
    source_url: Optional[str] = Field(default="", description="Source URL")
    page_name: Optional[str] = Field(default="", description="Source page name")
    is_active: bool = Field(default=True, description="Whether active")


class BulkQASaveRequest(BaseModel):
    institution_id: str = Field(..., description="Target institution ID")
    items: list[WebsiteQAItem] = Field(..., description="List of Q&A items with NLP aliases to save")


@router.post(
    "/crawl",
    summary="Crawl and ingest website URLs into institution Knowledge DB",
    status_code=status.HTTP_200_OK,
)
async def crawl_website(request: CrawlRequest):
    """
    Asynchronously crawls registered website URLs, cleans HTML boilerplate,
    extracts structured JSON hierarchies, generates Q&A items with NLP aliases,
    and stores them in MongoDB Knowledge DB.
    """
    if not request.urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one URL entry is required to crawl.",
        )

    try:
        pages = await website_engine.crawl_and_index(
            institution_id=request.institution_id,
            urls=request.urls,
        )
        successful_count = sum(1 for p in pages if p.status == "success")
        total_sections = sum(p.total_sections for p in pages)
        total_qa_items = sum(len(p.qa_items) for p in pages)

        return {
            "success": True,
            "institution_id": request.institution_id,
            "total_urls_processed": len(pages),
            "successful_pages": successful_count,
            "total_sections_extracted": total_sections,
            "total_qa_items_generated": total_qa_items,
            "pages": pages,
        }
    except Exception as e:
        logger.error("api_website_crawl_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to crawl website: {str(e)}",
        )


@router.get(
    "/pages",
    summary="List all crawled pages for an institution",
    status_code=status.HTTP_200_OK,
)
async def get_crawled_pages(
    institution_id: str = Query(..., description="Institution identifier (e.g. 'sjbhs')"),
):
    """Fetch all indexed web pages, JSON representations, and sections for an institution."""
    pages = await website_engine.get_pages(institution_id)
    return {
        "success": True,
        "institution_id": institution_id,
        "total_pages": len(pages),
        "pages": pages,
    }


@router.get(
    "/knowledge",
    summary="Get all extracted semantic knowledge sections for an institution",
    status_code=status.HTTP_200_OK,
)
async def get_knowledge_sections(
    institution_id: str = Query(..., description="Institution identifier (e.g. 'sjbhs')"),
):
    """Fetch all flat semantic sections and keywords extracted from institution website."""
    sections = await website_engine.get_sections(institution_id)
    return {
        "success": True,
        "institution_id": institution_id,
        "total_sections": len(sections),
        "sections": sections,
    }


# =============================================================================
# Q&A & NLP ALIASES ENDPOINTS (MIRRORS ERP SCHEMA & NLP ALIASES)
# =============================================================================

@router.get(
    "/qa",
    summary="Get all structured Q&A items with NLP aliases for an institution",
    status_code=status.HTTP_200_OK,
)
async def get_qa_items(
    institution_id: str = Query(..., description="Institution identifier (e.g. 'sjbhs')"),
    role: Optional[str] = Query(default=None, description="Optional role filter ('website', 'student', etc.)"),
):
    """Fetch all structured Q&A items with their configured NLP aliases."""
    items = await website_engine.get_qa_items(institution_id, role=role)
    return {
        "success": True,
        "institution_id": institution_id,
        "role": role or "all",
        "total_qa_items": len(items),
        "items": items,
    }


@router.post(
    "/qa",
    summary="Create or update a structured Q&A item with NLP aliases",
    status_code=status.HTTP_200_OK,
)
async def save_qa_item(request: SaveQAItemRequest):
    """Create or update a Q&A item with NLP aliases for RapidFuzz matching."""
    qa_id = request.id or f"{request.institution_id}_qa_{request.field_key}"
    qa_item = WebsiteQAItem(
        id=qa_id,
        institution_id=request.institution_id,
        field_key=request.field_key,
        category=request.category,
        question=request.question,
        answer=request.answer,
        aliases=[a.strip() for a in request.aliases if a.strip()],
        role=request.role,
        source_url=request.source_url or "",
        page_name=request.page_name or "",
        is_active=request.is_active,
    )
    await website_engine.save_qa_item(qa_item)
    return {
        "success": True,
        "message": f"Saved Q&A item '{qa_item.field_key}' with {len(qa_item.aliases)} NLP aliases.",
        "item": qa_item,
    }


@router.delete(
    "/qa/{qa_id}",
    summary="Delete a structured Q&A item",
    status_code=status.HTTP_200_OK,
)
async def delete_qa_item(
    qa_id: str,
    institution_id: str = Query(..., description="Target institution ID"),
):
    """Delete a structured Q&A item."""
    deleted = await website_engine.delete_qa_item(institution_id, qa_id)
    return {
        "success": deleted,
        "institution_id": institution_id,
        "deleted_qa_id": qa_id,
        "message": f"Deleted Q&A item '{qa_id}'.",
    }


@router.post(
    "/qa/bulk",
    summary="Bulk import / save structured Q&A items with NLP aliases",
    status_code=status.HTTP_200_OK,
)
async def bulk_save_qa_items(request: BulkQASaveRequest):
    """Bulk save or import a collection of Q&A items with NLP aliases."""
    count = await website_engine.bulk_save_qa_items(request.institution_id, request.items)
    return {
        "success": True,
        "institution_id": request.institution_id,
        "saved_count": count,
        "message": f"Successfully saved {count} Q&A items.",
    }


@router.get(
    "/raw-json",
    summary="Get complete structured JSON page documents for an institution",
    status_code=status.HTTP_200_OK,
)
async def get_raw_json_knowledge(
    institution_id: str = Query(..., description="Institution identifier (e.g. 'sjbhs')"),
):
    """Fetch complete structured JSON hierarchy extracted from crawled website pages."""
    pages = await website_engine.get_pages(institution_id)
    json_docs = [
        {
            "page_id": p.id,
            "page_name": p.page_name,
            "url": p.url,
            "role": p.role,
            "crawled_at": p.crawled_at,
            "raw_json_data": p.raw_json_data,
            "qa_items_count": len(p.qa_items),
        }
        for p in pages
    ]
    return {
        "success": True,
        "institution_id": institution_id,
        "total_documents": len(json_docs),
        "documents": json_docs,
    }


# =============================================================================
# SEARCH & TESTING ENDPOINTS
# =============================================================================

@router.post(
    "/test-search",
    summary="Test query matching against website knowledge & NLP aliases",
    status_code=status.HTTP_200_OK,
)
async def test_search_website(
    request: Optional[TestSearchRequest] = None,
    institution_id: Optional[str] = Query(default=None),
    question: Optional[str] = Query(default=None),
    query: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default="all"),
):
    """Directly test search ranking and answer generation against stored website knowledge and NLP aliases."""
    inst = (request.institution_id if request else None) or institution_id
    q = (request.question if request else None) or question or query
    r = (request.role if request else None) or role or "all"

    if not inst or not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="institution_id and question (or query) are required.",
        )

    answer = await website_engine.search_and_answer(
        institution_id=inst,
        question=q,
        role=r,
    )
    return {
        "success": True,
        "institution_id": inst,
        "role": r,
        "question": q,
        "answer": answer,
    }


@router.delete(
    "/knowledge",
    summary="Delete website knowledge for an institution",
    status_code=status.HTTP_200_OK,
)
async def delete_website_knowledge(
    request: Optional[DeleteKnowledgeRequest] = None,
    institution_id: Optional[str] = Query(default=None),
    page_id_or_url: Optional[str] = Query(default=None),
):
    """Delete all knowledge or a single page for an institution."""
    inst = (request.institution_id if request else None) or institution_id
    target_page = (request.page_id_or_url if request else None) or page_id_or_url

    if not inst:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="institution_id is required to clear website knowledge.",
        )

    if target_page:
        deleted = await website_engine.delete_page(
            institution_id=inst,
            page_id_or_url=target_page,
        )
        return {
            "success": deleted,
            "institution_id": inst,
            "deleted_page": target_page,
            "message": f"Deleted page '{target_page}' for institution '{inst}'.",
        }
    else:
        count = await website_engine.clear_all(inst)
        return {
            "success": True,
            "institution_id": inst,
            "deleted_pages_count": count,
            "message": f"Cleared all website knowledge ({count} pages) for institution '{inst}'.",
        }
