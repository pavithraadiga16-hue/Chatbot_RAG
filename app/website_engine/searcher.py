"""
Website Knowledge Searcher
===========================

High-performance fuzzy and semantic ranking engine using RapidFuzz multi-tier
matching across NLP Aliases, Canonical Q&A pairs, and Semantic Sections.
"""

import re
from typing import Optional
from rapidfuzz import fuzz
from app.core.logging import get_logger
from app.website_engine.models import KnowledgeSection, WebsiteQAItem, WebsiteSearchHit
from app.website_engine.repository import website_repo

logger = get_logger(__name__)

STOPWORDS = {
    "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
    "the", "is", "are", "was", "were", "tell", "about", "give", "details",
    "info", "information", "can", "you", "please", "know", "show", "school",
    "does", "have", "with", "from", "for", "and", "me", "my", "your", "today",
    "share", "some", "any", "like", "want"
}


class WebsiteKnowledgeSearcher:
    """Multi-Tier RapidFuzz searcher matching NLP Aliases, Q&A entities, and web sections."""

    def _extract_query_tokens(self, text: str) -> list[str]:
        """Extract alphanumeric search tokens from question."""
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
        return [t for t in tokens if t not in STOPWORDS]

    def _clean_query(self, text: str) -> str:
        """Clean and normalize query string."""
        return re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).strip()

    async def search(
        self,
        institution_id: str,
        question: str,
        role: Optional[str] = None,
        top_k: int = 3,
        min_score_threshold: float = 0.35,
    ) -> list[WebsiteSearchHit]:
        """
        Search stored website knowledge using multi-tier ranking.

        Tier 1: NLP Aliases Matching on structured WebsiteQAItems (Highest Priority)
        Tier 2: Canonical Question & Field Title Matching
        Tier 3: Semantic Section & Keyword Content Matching

        Args:
            institution_id: The school slug (e.g. "sjbhs")
            question: The natural language question
            role: Optional role filter ('website', 'student', 'parent', etc.)
            top_k: Max matching items to return
            min_score_threshold: Minimum normalized confidence score (0-1)

        Returns:
            Ranked list of WebsiteSearchHit items
        """
        q_raw = question.strip()
        q_clean = self._clean_query(q_raw)
        q_tokens = self._extract_query_tokens(q_clean)
        q_match = " ".join(q_tokens) or q_clean

        scored_hits: list[WebsiteSearchHit] = []

        # =========================================================================
        # TIER 1 & 2: Match Structured Q&A Entities via NLP Aliases & Questions
        # =========================================================================
        qa_items = await website_repo.get_all_qa_items(institution_id, role=role)

        for item in qa_items:
            best_alias_score = 0.0
            best_matched_alias = ""

            # Check every alias in item.aliases
            for alias in item.aliases:
                alias_clean = self._clean_query(alias)
                if not alias_clean:
                    continue

                alias_tokens = self._extract_query_tokens(alias_clean)
                alias_match = " ".join(alias_tokens) or alias_clean
                has_token_overlap = bool(set(q_tokens) & set(alias_tokens))

                # Score content words instead of shared question scaffolding
                # such as "what is"; otherwise unrelated short queries can
                # look like a strong fuzzy match.
                ts_ratio = fuzz.token_set_ratio(q_match, alias_match) / 100.0
                ratio = fuzz.ratio(q_match, alias_match) / 100.0
                partial = fuzz.partial_ratio(q_match, alias_match) / 100.0
                sort_ratio = fuzz.token_sort_ratio(q_match, alias_match) / 100.0

                # If no token overlap at all and basic ratio is low, avoid false match
                if not has_token_overlap and ratio < 0.60:
                    continue

                # Weighted alias score
                score = max(
                    (ts_ratio * 0.70) + (ratio * 0.30),
                    (sort_ratio * 0.75) + (ratio * 0.25),
                    (partial * 0.85) if (has_token_overlap and len(alias_clean) >= 5) else 0.0,
                )

                # Substring containment bonus (e.g. "principal" in "who is principal of sjbhs")
                if alias_match in q_match or q_match in alias_match:
                    score = min(1.0, score + 0.15)

                if score > best_alias_score:
                    best_alias_score = score
                    best_matched_alias = alias

            # Check canonical question
            q_canonical_clean = self._clean_query(item.question)
            canonical_tokens = self._extract_query_tokens(q_canonical_clean)
            has_canonical_overlap = bool(set(q_tokens) & set(canonical_tokens))

            canonical_score = 0.0
            if has_canonical_overlap:
                canonical_score = fuzz.token_set_ratio(
                    q_match, " ".join(canonical_tokens) or q_canonical_clean
                ) / 100.0

            # Composite Q&A score
            final_qa_score = max(best_alias_score, canonical_score * 0.90)

            # Keyword containment bonus on field_key
            field_tokens = set(self._extract_query_tokens(item.field_key))
            if item.field_key.lower() in q_match or bool(set(q_tokens) & field_tokens):
                final_qa_score = min(1.0, final_qa_score + 0.12)

            if final_qa_score >= min_score_threshold:
                match_type = "qa_alias" if best_alias_score >= canonical_score else "qa_question"
                scored_hits.append(
                    WebsiteSearchHit(
                        institution_id=institution_id,
                        relevance_score=round(final_qa_score, 3),
                        match_type=match_type,
                        matched_alias=best_matched_alias or item.question,
                        qa_item=item,
                        section=None,
                        highlight_snippets=[item.answer[:120]],
                    )
                )

        # =========================================================================
        # TIER 3: Semantic Section Search
        # =========================================================================
        sections = await website_repo.get_all_sections(institution_id)

        for sec in sections:
            title_clean = self._clean_query(sec.title)
            content_clean = sec.content.lower()
            kw_clean = " ".join(sec.keywords).lower()

            overlap_count = sum(1 for t in q_tokens if t in content_clean or t in title_clean or t in kw_clean)
            if q_tokens and overlap_count == 0:
                continue

            title_score = fuzz.token_set_ratio(q_clean, title_clean) / 100.0
            content_token_score = fuzz.token_set_ratio(q_clean, content_clean) / 100.0
            content_partial_score = fuzz.partial_ratio(q_clean, content_clean) / 100.0
            kw_score = fuzz.token_set_ratio(q_clean, kw_clean) / 100.0

            overlap_ratio = (overlap_count / len(q_tokens)) if q_tokens else 0.0

            sec_score = (
                (title_score * 0.35) +
                (content_token_score * 0.25) +
                (content_partial_score * 0.15) +
                (kw_score * 0.15) +
                (overlap_ratio * 0.10)
            )

            if any(t in title_clean for t in q_tokens if len(t) >= 4):
                sec_score = min(1.0, sec_score + 0.15)

            # Highlights
            highlights: list[str] = []
            sentences = re.split(r"(?<=[.!?])\s+", sec.content)
            for s in sentences:
                s_lower = s.lower()
                if any(t in s_lower for t in q_tokens if len(t) >= 4):
                    highlights.append(s.strip())

            if sec_score >= min_score_threshold:
                scored_hits.append(
                    WebsiteSearchHit(
                        institution_id=institution_id,
                        relevance_score=round(sec_score, 3),
                        match_type="semantic_fuzzy",
                        matched_alias=sec.title,
                        qa_item=None,
                        section=sec,
                        highlight_snippets=highlights[:3],
                    )
                )

        # Sort by relevance score descending
        def _hit_sort_key(h: WebsiteSearchHit) -> float:
            base = h.relevance_score
            if h.match_type == "qa_alias":
                base += 0.05
            return base

        scored_hits.sort(key=_hit_sort_key, reverse=True)
        return scored_hits[:top_k]


website_searcher = WebsiteKnowledgeSearcher()
