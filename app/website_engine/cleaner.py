"""
Website HTML Content Cleaner & Extractor
=========================================

Extracts meaningful textual content from raw HTML documents while eliminating
navigation menus, footers, headers, advertisements, cookie banners, scripts,
and styles.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup, Comment
from app.core.logging import get_logger

logger = get_logger(__name__)

# Tags to completely remove along with their contents
STRIP_TAGS = {
    "script", "style", "noscript", "nav", "footer", "header", "aside",
    "svg", "form", "iframe", "button", "input", "select", "option",
    "textarea", "canvas", "audio", "video"
}

# CSS class/ID patterns commonly used for non-content boilerplate
BOILERPLATE_PATTERNS = [
    r"cookie", r"banner", r"advert", r"promo", r"modal", r"popup",
    r"\bmenu\b", r"\bnav\b", r"\bfooter\b", r"\bsidebar\b", r"\bsocial\b",
    r"\bshare\b", r"widget", r"breadcrumb"
]



class CleanedDocument:
    """Structured representation of cleaned web page content."""
    def __init__(
        self,
        title: str,
        meta_description: str,
        headings_and_paragraphs: list[tuple[str, str]],
        full_clean_text: str
    ):
        self.title = title
        self.meta_description = meta_description
        self.headings_and_paragraphs = headings_and_paragraphs  # [(heading_level_or_tag, text), ...]
        self.full_clean_text = full_clean_text


class HtmlContentCleaner:
    """Cleans and extracts structured content from raw HTML strings."""

    def clean(self, html_content: str, fallback_title: str = "") -> CleanedDocument:
        """
        Parse raw HTML, strip boilerplate, and extract structured text.

        Args:
            html_content: Raw HTML text
            fallback_title: Title to use if document <title> is missing

        Returns:
            CleanedDocument containing title, meta description, and structured text blocks
        """
        if not html_content or not html_content.strip():
            return CleanedDocument(
                title=fallback_title,
                meta_description="",
                headings_and_paragraphs=[],
                full_clean_text=""
            )

        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            logger.warning("html_parser_fallback", error=str(e))
            # Fallback regex strip
            clean_text = re.sub(r"<[^>]+>", " ", html_content)
            clean_text = " ".join(clean_text.split())
            return CleanedDocument(
                title=fallback_title,
                meta_description="",
                headings_and_paragraphs=[("p", clean_text)],
                full_clean_text=clean_text
            )

        # 1. Extract Title
        title = ""
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text():
            title = title_tag.get_text().strip()
        if not title:
            h1 = soup.find("h1")
            if h1 and h1.get_text():
                title = h1.get_text().strip()
        if not title:
            title = fallback_title

        # 2. Extract Meta Description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag.get("content").strip()

        # 3. Strip Comments
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

        # 4. Strip Blacklisted Tags
        for tag_name in STRIP_TAGS:
            for element in soup.find_all(tag_name):
                element.decompose()

        # 5. Remove Elements with Boilerplate Classes/IDs (except if inside main/article)
        for element in soup.find_all(True):
            if not hasattr(element, "attrs") or element.attrs is None:
                continue

            attrs_dict = element.attrs if isinstance(element.attrs, dict) else {}
            attrs_str = " ".join([
                str(attrs_dict.get("class", "")),
                str(attrs_dict.get("id", "")),
                str(attrs_dict.get("role", ""))
            ]).lower()

            for pattern in BOILERPLATE_PATTERNS:
                if re.search(pattern, attrs_str):
                    # Check if this element is the main content container; don't delete if it contains article/main
                    if element.name not in ["main", "article", "body", "html"]:
                        element.decompose()
                        break


        # 6. Extract Structured Blocks (h1-h6, p, ul, ol, table)
        target_root = soup.find("main") or soup.find("article") or soup.body or soup
        structured_blocks: list[tuple[str, str]] = []

        for element in target_root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table", "blockquote"]):
            text = element.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if not text or len(text) < 4:
                continue

            # Tag classification
            tag_name = element.name.lower()
            structured_blocks.append((tag_name, text))

        # 7. Fallback if no structured blocks found
        if not structured_blocks:
            body_text = target_root.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in body_text.split("\n") if len(l.strip()) > 10]
            for line in lines:
                structured_blocks.append(("p", line))

        full_text = " ".join([text for _, text in structured_blocks])

        return CleanedDocument(
            title=title,
            meta_description=meta_desc,
            headings_and_paragraphs=structured_blocks,
            full_clean_text=full_text
        )


html_cleaner = HtmlContentCleaner()
