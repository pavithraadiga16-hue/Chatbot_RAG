"""
Website Knowledge Answer Generator & Formatter
===============================================

Synthesizes clean, structured markdown answers with verified source citations,
bulleted highlights, and contextual suggestions from crawled web knowledge and Q&A items.
"""

from typing import Optional
from app.website_engine.models import KnowledgeSection, WebsiteAnswer, WebsiteQAItem, WebsiteSearchHit

INSTITUTION_NAMES = {
    "sjbhs": "St. Joseph's Boys' High School",
    "sags_school": "SAGS Academy",
    "sags": "SAGS Academy",
}

CATEGORY_ICONS = {
    "Leadership & Administration": "👨‍💼",
    "Leadership": "👨‍💼",
    "About & Heritage": "🏛️",
    "Heritage": "🏛️",
    "Values": "✨",
    "Facilities & Abilities": "🏟️",
    "Facilities": "🏟️",
    "Admissions": "📝",
    "Academics": "📚",
    "Academics & Info": "📚",
    "Alumni": "🎓",
    "Contact & Location": "📞",
    "General": "🏫",
}


class WebsiteAnswerGenerator:
    """Formats knowledge search results and structured Q&A matches into clean markdown answers."""

    def _get_institution_name(self, institution_id: str) -> str:
        """Get friendly institution display name."""
        clean = institution_id.strip().replace("-", " ").replace("_", " ")
        if clean.lower() == "sjbhs":
            return "St. Joseph's Boys' High School"
        return clean.title()

    def _generate_suggestions(
        self,
        hits: list[WebsiteSearchHit],
        institution_id: str,
    ) -> list[str]:
        """Generate smart follow-up suggestions dynamically from matched categories or generic topics."""
        suggestions = []
        for h in hits:
            if h.qa_item and h.qa_item.question:
                suggestions.append(h.qa_item.question)

        inst_name = self._get_institution_name(institution_id)
        default_topics = [
            f"Who is the Principal of {inst_name}?",
            f"What facilities and abilities does {inst_name} provide?",
            f"What is the school motto and values of {inst_name}?",
            f"Tell me about admissions at {inst_name}",
            f"How do I contact {inst_name}?",
        ]
        for dt in default_topics:
            if dt not in suggestions:
                suggestions.append(dt)

        return suggestions[:5]

    def generate_answer(
        self,
        question: str,
        institution_id: str,
        hits: list[WebsiteSearchHit],
        execution_time_ms: float = 0.0,
    ) -> WebsiteAnswer:
        """
        Synthesize top knowledge hits into a verified, structured markdown response.

        Args:
            question: Original question asked
            institution_id: School slug
            hits: Search hits returned by searcher
            execution_time_ms: Latency in ms

        Returns:
            WebsiteAnswer object with formatted markdown
        """
        inst_display = self._get_institution_name(institution_id)

        if not hits:
            # Fallback if no matching content found
            formatted_md = (
                f"### 🏫 **{inst_display} Website Knowledge**\n\n"
                f"I searched the official website knowledge base for **{inst_display}**, but couldn't find a direct match for:\n"
                f"> *\"{question}\"*\n\n"
                f"💡 **You can ask about:**\n"
                f"- Who is the Principal / Leadership\n"
                f"- School Overview, Heritage & History\n"
                f"- School Motto & Values\n"
                f"- Campus Abilities & Sports Facilities\n"
                f"- Admissions Process & Curriculum\n"
                f"- Distinguished Alumni\n"
            )
            return WebsiteAnswer(
                handled_locally=True,
                institution_id=institution_id,
                question=question,
                answer="No matching website content found.",
                formatted_markdown=formatted_md,
                confidence=0.2,
                source_url=f"https://{institution_id}.edu.in/",
                source_title=f"{inst_display} Portal",
                section_title="Website Knowledge Search",
                matched_sections_count=0,
                execution_time_ms=execution_time_ms,
                suggestion_questions=self._generate_suggestions([], institution_id),
            )

        top_hit = hits[0]

        # =========================================================================
        # Case A: Structured Q&A Item Match (High Confidence direct entity)
        # =========================================================================
        if top_hit.qa_item is not None:
            qa = top_hit.qa_item
            icon = CATEGORY_ICONS.get(qa.category, "🏫")
            page_label = qa.page_name or qa.question

            lines = [
                f"### {icon} **{qa.question}** ({inst_display})",
                "",
                f"{qa.answer}",
            ]

            # Source citation footer
            lines.extend([
                "",
                "---",
                f"🔗 **Official Source:** [{page_label}]({qa.source_url or f'https://{institution_id}.edu.in/'})  ",
                f"🏛️ **Institution:** `{inst_display}`",
            ])

            formatted_md = "\n".join(lines)
            suggestions = self._generate_suggestions(hits, institution_id)

            return WebsiteAnswer(
                handled_locally=True,
                institution_id=institution_id,
                question=question,
                answer=qa.answer,
                formatted_markdown=formatted_md,
                confidence=top_hit.relevance_score,
                source_url=qa.source_url or f"https://{institution_id}.edu.in/",
                source_title=page_label,
                section_title=qa.question,
                matched_sections_count=len(hits),
                execution_time_ms=execution_time_ms,
                suggestion_questions=suggestions,
                matched_alias=top_hit.matched_alias,
                category=qa.category,
                qa_item=qa,
            )

        # =========================================================================
        # Case B: Semantic Section Match
        # =========================================================================
        sec = top_hit.section or KnowledgeSection(
            section_id="fallback",
            title="School Information",
            content=top_hit.highlight_snippets[0] if top_hit.highlight_snippets else "School information.",
            url=f"https://{institution_id}.edu.in/",
            page_name="Portal",
        )

        icon = CATEGORY_ICONS.get(sec.category, "🏫")
        lines = [
            f"### {icon} **{sec.title}** ({inst_display})",
            "",
            "#### 📖 **Information from Website:**",
            f"{sec.content}",
        ]

        # Additional distinct hit excerpts
        if len(hits) > 1 and hits[1].section and hits[1].section.title != sec.title:
            other_sec = hits[1].section
            lines.extend([
                "",
                f"#### ℹ️ **Related Topic: {other_sec.title}**",
                f"{other_sec.content[:240]}...",
            ])

        page_label = sec.page_name or sec.title
        lines.extend([
            "",
            "---",
            f"🔗 **Official Source:** [{page_label}]({sec.url})  ",
            f"🏛️ **Institution:** `{inst_display}`",
        ])

        formatted_md = "\n".join(lines)
        suggestions = self._generate_suggestions(hits, institution_id)

        return WebsiteAnswer(
            handled_locally=True,
            institution_id=institution_id,
            question=question,
            answer=sec.content,
            formatted_markdown=formatted_md,
            confidence=top_hit.relevance_score,
            source_url=sec.url,
            source_title=page_label,
            section_title=sec.title,
            matched_sections_count=len(hits),
            execution_time_ms=execution_time_ms,
            suggestion_questions=suggestions,
            matched_alias=top_hit.matched_alias,
            category=sec.category,
        )


website_answer_generator = WebsiteAnswerGenerator()
