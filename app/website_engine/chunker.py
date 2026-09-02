"""
Website Semantic Chunker
=========================

Divides cleaned web page documents into structured, search-optimized sections
keyed by heading titles, extracted keywords, and source URLs.
"""

import re
from typing import Optional
from app.website_engine.cleaner import CleanedDocument
from app.website_engine.models import KnowledgeSection


# Stopwords to filter out during keyword extraction
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "did", "do", "does", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours"
}


class SemanticChunker:
    """Chunks cleaned web documents into coherent semantic sections."""

    def extract_keywords(self, text: str, max_keywords: int = 12) -> list[str]:
        """Extract dominant meaningful tokens and phrases from text."""
        words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", text.lower())
        meaningful = [w for w in words if w not in STOPWORDS and not w.isdigit()]
        
        # Word frequency count
        counts: dict[str, int] = {}
        for w in meaningful:
            counts[w] = counts.get(w, 0) + 1

        sorted_words = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_keywords]]

    def chunk(
        self,
        doc: CleanedDocument,
        url: str,
        page_name: str,
        min_section_length: int = 40,
        max_section_length: int = 1500,
    ) -> list[KnowledgeSection]:
        """
        Split document into semantic sections based on headings and paragraph clusters.

        Args:
            doc: CleanedDocument output from HtmlContentCleaner
            url: Source page URL
            page_name: Friendly page name
            min_section_length: Minimum chars per section to avoid tiny fragments
            max_section_length: Maximum target chars per section

        Returns:
            List of KnowledgeSection objects
        """
        sections: list[KnowledgeSection] = []
        current_title = doc.title or page_name or "Overview"
        current_paragraphs: list[str] = []
        section_idx = 0

        def _flush_section():
            nonlocal section_idx, current_title, current_paragraphs
            if not current_paragraphs:
                return

            full_content = " ".join(current_paragraphs).strip()
            if len(full_content) >= min_section_length:
                keywords = self.extract_keywords(f"{current_title} {full_content}")
                sec = KnowledgeSection(
                    section_id=f"sec_{section_idx}",
                    title=current_title,
                    content=full_content,
                    keywords=keywords,
                    url=url,
                    page_name=page_name or doc.title or "Web Page",
                    char_count=len(full_content),
                )
                sections.append(sec)
                section_idx += 1

            current_paragraphs = []

        heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}

        for tag, text in doc.headings_and_paragraphs:
            if tag in heading_tags:
                # If we hit a new heading and already have content, flush the previous section
                if current_paragraphs:
                    _flush_section()
                current_title = text
            else:
                # Accumulate paragraph text
                current_paragraphs.append(text)
                # If current section is becoming too long, flush
                current_len = sum(len(p) for p in current_paragraphs)
                if current_len >= max_section_length:
                    _flush_section()

        # Flush any remaining paragraphs
        _flush_section()

        # If document had no headings or produced no sections, create a single fallback section
        if not sections and doc.full_clean_text.strip():
            fallback_text = doc.full_clean_text.strip()
            keywords = self.extract_keywords(f"{doc.title} {fallback_text}")
            sections.append(
                KnowledgeSection(
                    section_id=f"sec_0",
                    title=doc.title or page_name or "Overview",
                    content=fallback_text[:max_section_length],
                    keywords=keywords,
                    url=url,
                    page_name=page_name or doc.title or "Web Page",
                    char_count=len(fallback_text[:max_section_length]),
                )
            )

        return sections


semantic_chunker = SemanticChunker()
