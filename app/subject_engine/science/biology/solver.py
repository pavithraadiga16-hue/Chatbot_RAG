"""
Biology Master Concept Solver Orchestrator
==========================================

PURPOSE:
    Central deterministic Biology solver providing structured concept explanations,
    organelle functions, mechanism breakdowns, and comparison tables using RapidFuzz.
"""

import time
from typing import Optional, Any
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.biology.knowledge import biology_kb, BiologyConcept


class BiologySolver:
    """Master solver orchestrator for Biology."""

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        start_time = time.monotonic()
        raw_q = query.strip()
        lower_q = raw_q.lower()

        # Step 1: Match against Biology Concept Knowledge Base
        matches = biology_kb.find_by_query(raw_q, threshold=55.0)
        if matches:
            concept, score = matches[0]

            # Case A: Difference / Comparison Query
            is_difference_q = any(w in lower_q for w in ("difference", "versus", "vs", "compare", "distinguish"))
            if is_difference_q and concept.differences:
                parts = concept.name.split(":")
                title = concept.name
                item_a, item_b = ("Item A", "Item B")
                if " vs " in title or " and " in title:
                    clean_title = title.replace("vs", "and")
                    t_parts = [p.strip() for p in clean_title.split("and")]
                    if len(t_parts) >= 2:
                        item_a, item_b = t_parts[0], t_parts[1]

                md = science_formatter.format_comparison_table(
                    title=title,
                    item_a=item_a,
                    item_b=item_b,
                    differences=concept.differences,
                )
                res = SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.BIOLOGY,
                    topic=concept.topic,
                    concept_id=concept.concept_id,
                    intent=QuestionIntent.DIFFERENCE,
                    original_question=raw_q,
                    steps=[f"Compare {item_a} and {item_b}"],
                    answer=f"Comparison: {item_a} vs {item_b}",
                    formatted_markdown=md,
                    confidence=min(0.99, max(0.85, score / 100.0)),
                )
                return self._finalize(res, start_time, raw_q)

            # Case B: Standard Biological Explanation / Function / Structure
            md = science_formatter.format_biological_concept(
                name=concept.name,
                definition=concept.definition,
                functions=concept.functions,
                structure=concept.location_or_structure,
                importance=concept.importance,
                key_points=concept.key_points if hasattr(concept, "key_points") else None,
                common_questions=concept.common_questions,
                explanation=concept.explanation,
            )
            intent = QuestionIntent.EXPLAIN_FUNCTION if any(w in lower_q for w in ("function", "role", "why", "what does")) else QuestionIntent.DEFINE
            res = SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.BIOLOGY,
                topic=concept.topic,
                concept_id=concept.concept_id,
                intent=intent,
                original_question=raw_q,
                rules_applied=concept.functions,
                steps=[concept.definition],
                answer=concept.importance or concept.definition,
                formatted_markdown=md,
                confidence=min(0.99, max(0.80, score / 100.0)),
            )
            return self._finalize(res, start_time, raw_q)


        # Unhandled Biology query
        elapsed = (time.monotonic() - start_time) * 1000.0
        return SubjectSolveResult(
            handled_locally=False,
            subject=SubjectType.BIOLOGY,
            intent=QuestionIntent.UNKNOWN,
            original_question=raw_q,
            confidence=0.0,
            execution_time_ms=elapsed,
        )

    def _finalize(self, res: SubjectSolveResult, start_time: float, raw_q: str) -> SubjectSolveResult:
        res.execution_time_ms = (time.monotonic() - start_time) * 1000.0
        res.original_question = raw_q
        return res


# Global instance
biology_solver = BiologySolver()
