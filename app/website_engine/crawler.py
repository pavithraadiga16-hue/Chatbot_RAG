"""
Async Website Crawler & Content Ingestor
=========================================

Fetches web pages asynchronously using httpx, extracts structured content,
cleans boilerplates, and chunks content into semantic knowledge sections.
"""

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Optional
import httpx

from app.core.logging import get_logger
from app.website_engine.cleaner import html_cleaner
from app.website_engine.chunker import semantic_chunker
from app.website_engine.models import CrawledPage, KnowledgeSection, WebsiteUrlEntry

logger = get_logger(__name__)

# Request Headers
CRAWLER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 "
        "PhinsIQ-WebsiteCrawler/2.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class WebsiteCrawler:
    """Async web crawler and content parser."""

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    def _generate_page_id(self, institution_id: str, url: str) -> str:
        """Generate a deterministic MongoDB document _id from institution and URL."""
        url_clean = url.strip().rstrip("/").lower()
        url_hash = hashlib.sha256(url_clean.encode("utf-8")).hexdigest()[:16]
        return f"{institution_id}_{url_hash}"

    async def fetch_page(
        self,
        client: httpx.AsyncClient,
        entry: WebsiteUrlEntry,
        institution_id: str,
    ) -> CrawledPage:
        """
        Fetch a single URL, clean its HTML, and extract semantic knowledge sections.

        Args:
            client: Shared httpx.AsyncClient instance
            entry: WebsiteUrlEntry containing name and URL
            institution_id: Target institution identifier

        Returns:
            CrawledPage model with extracted sections
        """
        page_id = self._generate_page_id(institution_id, entry.url)
        logger.info(
            "crawler_fetching_page",
            institution_id=institution_id,
            page_name=entry.name,
            url=entry.url,
        )

        try:
            # 1. Try headless Playwright browser first for full SPA / React / dynamic DOM rendering
            rendered_html, page_title = await self._render_with_playwright(entry.url)
            html_text = rendered_html
            title_override = page_title

            # 2. Fallback to async httpx if Playwright is unavailable
            if not html_text:
                resp = await client.get(entry.url, timeout=self.timeout_seconds)
                resp.raise_for_status()
                html_text = resp.text

            # 3. Clean and structure content
            cleaned_doc = html_cleaner.clean(html_text, fallback_title=entry.name)
            if title_override and not cleaned_doc.title:
                cleaned_doc.title = title_override

            # 4. Chunk into semantic sections
            sections = semantic_chunker.chunk(
                doc=cleaned_doc,
                url=entry.url,
                page_name=entry.name,
            )

            # 5. Extract structured JSON hierarchy and Q&A items with NLP aliases
            from app.website_engine.extractor import json_extractor
            raw_json_data, qa_items = json_extractor.extract_full_json(
                html_content=html_text,
                url=entry.url,
                page_name=entry.name,
                institution_id=institution_id,
                role=getattr(entry, "role", "all"),
            )

            # 6. If static HTML body was an empty SPA shell, extract from JS bundles
            if len(sections) == 0:
                spa_sections = await self._extract_spa_bundle_content(
                    client=client,
                    html_text=html_text,
                    base_url=entry.url,
                    entry=entry,
                )
                if spa_sections:
                    sections = spa_sections

            crawled_page = CrawledPage(
                _id=page_id,
                institution_id=institution_id,
                page_name=entry.name,
                url=entry.url,
                role=getattr(entry, "role", "all"),
                category=getattr(entry, "category", "General"),
                title=cleaned_doc.title if cleaned_doc.title else entry.name,
                meta_description=cleaned_doc.meta_description,
                crawled_at=datetime.now(timezone.utc).isoformat(),
                status="success",
                error_message=None,
                total_sections=len(sections),
                sections=sections,
                raw_json_data=raw_json_data,
                qa_items=qa_items,
            )

            logger.info(
                "crawler_page_success",
                institution_id=institution_id,
                url=entry.url,
                total_sections=len(sections),
                qa_items_count=len(qa_items),
            )
            return crawled_page

        except httpx.HTTPStatusError as e:
            logger.warning(
                "crawler_http_error",
                institution_id=institution_id,
                url=entry.url,
                status_code=e.response.status_code,
            )
            return CrawledPage(
                _id=page_id,
                institution_id=institution_id,
                page_name=entry.name,
                url=entry.url,
                title=entry.name,
                crawled_at=datetime.now(timezone.utc).isoformat(),
                status="error",
                error_message=f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                total_sections=0,
                sections=[],
            )

        except Exception as e:
            logger.warning(
                "crawler_fetch_failed",
                institution_id=institution_id,
                url=entry.url,
                error=str(e),
            )
            return CrawledPage(
                _id=page_id,
                institution_id=institution_id,
                page_name=entry.name,
                url=entry.url,
                title=entry.name,
                crawled_at=datetime.now(timezone.utc).isoformat(),
                status="error",
                error_message=str(e),
                total_sections=0,
                sections=[],
            )

    async def _render_with_playwright(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Render dynamic client-side SPA web page (React/Vite/Next/Vue) with headless Chromium.
        Returns (html_content, page_title) or (None, None) if failed.
        """
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=int(self.timeout_seconds * 1000))
                html = await page.content()
                title = await page.title()
                await browser.close()
                return html, title
        except Exception as e:
            logger.debug("playwright_render_fallback", url=url, error=str(e))
            return None, None

    async def _extract_spa_bundle_content(
        self,
        client: httpx.AsyncClient,
        html_text: str,
        base_url: str,
        entry: WebsiteUrlEntry,
    ) -> list[KnowledgeSection]:
        """
        Extract structured sections from Client-Side SPA JS bundles (React/Vite/Vue/Next).
        """
        import re
        from urllib.parse import urljoin

        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html_text, re.IGNORECASE)
        if not script_srcs:
            return []

        all_sections: list[KnowledgeSection] = []
        for src in script_srcs[:4]:
            if any(ext in src.lower() for ext in ["cloudflare", "analytics", "googletagmanager", "facebook"]):
                continue
            script_url = urljoin(base_url, src)
            try:
                resp = await client.get(script_url, timeout=12.0)
                if resp.status_code != 200:
                    continue
                js_code = resp.text

                # 1. Extract markdown/structured responses from React bundles: response:`...`
                responses = re.findall(r'response:\`((?:[^\`]|\\.)+)\`', js_code)
                for idx, r_text in enumerate(responses):
                    clean_r = r_text.replace("\\n", "\n").replace("\\r", "").strip()
                    if len(clean_r) < 15:
                        continue
                    first_line = clean_r.split("\n")[0].strip("#* \t")
                    sec_title = first_line[:70] if first_line else f"Page Section {idx+1}"
                    words = re.findall(r'[a-zA-Z]{3,}', clean_r.lower())
                    kw = list(dict.fromkeys([w for w in words if w not in {"the", "and", "for", "with", "this", "that", "from", "you", "your", "are", "have", "this"}]))[:12]
                    all_sections.append(
                        KnowledgeSection(
                            section_id=f"spa_sec_{idx}",
                            title=sec_title,
                            content=clean_r,
                            keywords=kw,
                            url=entry.url,
                            page_name=entry.name,
                            char_count=len(clean_r),
                        )
                    )

            except Exception as e:
                logger.debug("spa_bundle_extract_failed", error=str(e), url=script_url)

        # Route matching filter
        path_lower = entry.url.lower().rstrip("/").split("/")[-1]
        name_lower = entry.name.lower()
        if path_lower and path_lower not in {"", "home", "index"}:
            matched = [
                s for s in all_sections
                if path_lower in s.title.lower()
                or path_lower in " ".join(s.keywords)
                or path_lower in s.content.lower()
            ]
            if matched:
                return matched
        elif "principal" in name_lower or "principal" in path_lower:
            matched = [
                s for s in all_sections
                if "principal" in s.title.lower()
                or "principal" in " ".join(s.keywords)
                or "norwin" in s.content.lower()
            ]
            if matched:
                return matched

        return all_sections

    async def crawl_urls(
        self,
        institution_id: str,
        entries: list[WebsiteUrlEntry],
    ) -> list[CrawledPage]:
        """
        Concurrently fetch and process multiple URL entries for an institution.

        Args:
            institution_id: Target institution ID
            entries: List of WebsiteUrlEntry items

        Returns:
            List of processed CrawledPage models
        """
        async with httpx.AsyncClient(
            headers=CRAWLER_HEADERS,
            follow_redirects=True,
            timeout=self.timeout_seconds,
            verify=False,  # Allow self-signed or internal institutional certificates
        ) as client:
            tasks = [
                self.fetch_page(client, entry, institution_id)
                for entry in entries
            ]
            results = await asyncio.gather(*tasks, return_exceptions=False)
            return list(results)


crawler = WebsiteCrawler()
