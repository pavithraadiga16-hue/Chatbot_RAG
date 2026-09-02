"""
Science Engine Master Facade & Branch Router
============================================

PURPOSE:
    Unifies Physics, Chemistry, and Biology under the Science Subject Engine umbrella,
    providing seamless cross-branch resolution and routing.
"""

import time
from typing import Optional, Any
from app.subject_engine.base import BaseSubjectEngine, SubjectType, SubjectSolveResult, QuestionIntent
from app.subject_engine.science.classifier import science_classifier
from app.subject_engine.science.physics.engine import physics_engine
from app.subject_engine.science.chemistry.engine import chemistry_engine
from app.subject_engine.science.biology.engine import biology_engine
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScienceEngine(BaseSubjectEngine):
    """Local deterministic Science Engine coordinating Physics, Chemistry, and Biology."""

    @property
    def subject(self) -> SubjectType:
        return SubjectType.SCIENCE

    def can_handle(self, query: str) -> tuple[bool, float]:
        classification = science_classifier.classify(query)
        return classification.is_science, classification.confidence

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        start_time = time.monotonic()
        raw_q = query.strip()

        # Step 1: Classify target science branch
        classification = science_classifier.classify(raw_q)
        target_branch = classification.branch

        # Step 2: Route to preferred branch first
        if target_branch == SubjectType.BIOLOGY:
            res = biology_engine.solve(raw_q, context=context)
            if res and res.handled_locally:
                return self._finalize(res, start_time)

        elif target_branch == SubjectType.CHEMISTRY:
            res = chemistry_engine.solve(raw_q, context=context)
            if res and res.handled_locally:
                return self._finalize(res, start_time)

        elif target_branch == SubjectType.PHYSICS:
            res = physics_engine.solve(raw_q, context=context)
            if res and res.handled_locally:
                return self._finalize(res, start_time)

        # Step 3: Fallback sweep across all three branches
        for eng in (physics_engine, chemistry_engine, biology_engine):
            res = eng.solve(raw_q, context=context)
            if res and res.handled_locally:
                return self._finalize(res, start_time)

        elapsed = (time.monotonic() - start_time) * 1000.0
        return SubjectSolveResult(
            handled_locally=False,
            subject=SubjectType.SCIENCE,
            intent=classification.intent,
            original_question=raw_q,
            confidence=classification.confidence,
            execution_time_ms=elapsed,
        )

    def _finalize(self, res: SubjectSolveResult, start_time: float) -> SubjectSolveResult:
        if not res.execution_time_ms:
            res.execution_time_ms = (time.monotonic() - start_time) * 1000.0
        return res


# Global Science Engine
science_engine = ScienceEngine()
