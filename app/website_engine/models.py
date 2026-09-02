"""
Website Knowledge Engine Models
================================

Pydantic schemas and dataclasses for the website crawling, structured JSON extraction,
semantic chunking, Q&A NLP aliases, knowledge storage, and question-answering subsystem.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class WebsiteUrlEntry(BaseModel):
    """A single website URL entry registered by an admin."""
    name: str = Field(..., description="Friendly label (e.g. 'Home Page', 'Overview', 'Admissions')")
    url: str = Field(..., description="Full HTTP/HTTPS URL")
    role: str = Field(default="all", description="Target role (e.g. 'all', 'website', 'student', 'parent', 'staff')")
    category: str = Field(default="General", description="Page category (e.g. 'Leadership', 'Academics', 'Campus')")


class CrawlRequest(BaseModel):
    """Request payload to crawl one or more website URLs for an institution."""
    institution_id: str = Field(..., description="Target institution ID (e.g. 'sjbhs')")
    urls: list[WebsiteUrlEntry] = Field(..., description="List of URL entries to crawl and ingest")
    crawl_depth: int = Field(default=1, ge=1, le=3, description="Depth for link discovery (default 1)")
    role: str = Field(default="all", description="Default role tag for crawled pages")


class KnowledgeSection(BaseModel):
    """A single semantic section extracted from a crawled web page."""
    section_id: str = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section or heading title")
    content: str = Field(..., description="Cleaned, readable section text")
    keywords: list[str] = Field(default_factory=list, description="Extracted keywords/entities")
    url: str = Field(..., description="Source page URL")
    page_name: str = Field(default="", description="Friendly page name")
    char_count: int = Field(default=0, description="Character count of content")
    category: str = Field(default="General", description="Section category")


class WebsiteQAItem(BaseModel):
    """
    A structured Q&A entity extracted or manually defined for an institution's website.
    Features NLP Aliases identical to ERP Schema Field Definitions for ultra-precise RapidFuzz matching.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique identifier (e.g. 'sjbhs_qa_principal')")
    institution_id: str = Field(..., description="Target institution slug (e.g. 'sjbhs')")
    field_key: str = Field(..., description="Standard field/topic key (e.g. 'principal', 'motto', 'facilities', 'admissions')")
    category: str = Field(default="General", description="Category (e.g. 'Leadership', 'About', 'Facilities', 'Admissions')")
    question: str = Field(..., description="Canonical natural language question")
    answer: str = Field(..., description="Direct concise or rich markdown answer")
    aliases: list[str] = Field(
        default_factory=list,
        description="NLP Aliases (comma-separated triggers — what users can say to trigger this answer)"
    )
    role: str = Field(default="all", description="Role access ('all', 'website', 'student', 'parent', 'staff')")
    source_url: str = Field(default="", description="Source page URL")
    page_name: str = Field(default="", description="Source page label")
    is_active: bool = Field(default=True, description="Whether this Q&A is active")


class CrawledPage(BaseModel):
    """A complete crawled and processed web page stored in the Knowledge DB with JSON representation."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique ID: {institution_id}_{url_hash_or_slug}")
    institution_id: str = Field(..., description="Institution ID")
    page_name: str = Field(..., description="Friendly page name")
    url: str = Field(..., description="Page URL")
    role: str = Field(default="all", description="Assigned role ('all', 'website', 'student', etc.)")
    category: str = Field(default="General", description="Page category")
    title: str = Field(default="", description="HTML Document title")
    meta_description: str = Field(default="", description="Meta description content")
    crawled_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of crawl"
    )
    status: str = Field(default="success", description="Crawl status ('success', 'error', 'cached')")
    error_message: Optional[str] = Field(default=None, description="Error detail if crawl failed")
    total_sections: int = Field(default=0, description="Number of semantic sections extracted")
    sections: list[KnowledgeSection] = Field(default_factory=list, description="Extracted sections")
    raw_json_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Complete structured JSON document extracted from the page"
    )
    qa_items: list[WebsiteQAItem] = Field(
        default_factory=list,
        description="Structured Q&A entities with NLP aliases extracted from this page"
    )


class WebsiteSearchHit(BaseModel):
    """A matched knowledge section or structured Q&A entity with relevance scoring."""
    institution_id: str
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Match confidence score (0-1)")
    match_type: str = Field(default="qa_alias", description="Match type: qa_alias, qa_question, semantic_fuzzy")
    matched_alias: Optional[str] = Field(default=None, description="The specific NLP alias that triggered the match")
    qa_item: Optional[WebsiteQAItem] = Field(default=None, description="Matched Q&A item if matched via Q&A tier")
    section: Optional[KnowledgeSection] = Field(default=None, description="Matched section if matched via section tier")
    highlight_snippets: list[str] = Field(default_factory=list, description="Key matching sentences")


class WebsiteAnswer(BaseModel):
    """Synthesized answer generated from the website knowledge base."""
    handled_locally: bool = True
    institution_id: str
    question: str
    answer: str
    formatted_markdown: str
    confidence: float
    source_url: str
    source_title: str
    section_title: str
    matched_sections_count: int = 1
    execution_time_ms: float = 0.0
    suggestion_questions: list[str] = Field(default_factory=list)
    matched_alias: Optional[str] = None
    category: Optional[str] = None
    qa_item: Optional[WebsiteQAItem] = None
