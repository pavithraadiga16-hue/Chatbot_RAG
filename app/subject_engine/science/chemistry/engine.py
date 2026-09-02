"""
Chemistry Engine Facade
=======================

PURPOSE:
    Implements BaseSubjectEngine for Chemistry.
"""

from typing import Optional, Any
from app.subject_engine.base import BaseSubjectEngine, SubjectType, SubjectSolveResult
from app.subject_engine.science.classifier import science_classifier
from app.subject_engine.science.chemistry.solver import chemistry_solver


class ChemistryEngine(BaseSubjectEngine):
    """Local deterministic Chemistry Engine covering LKG through PUC."""

    @property
    def subject(self) -> SubjectType:
        return SubjectType.CHEMISTRY

    def can_handle(self, query: str) -> tuple[bool, float]:
        classification = science_classifier.classify(query)
        can_h = classification.is_science and classification.branch == SubjectType.CHEMISTRY
        return can_h, classification.confidence

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        return chemistry_solver.solve(query, context=context)


# Global instance
chemistry_engine = ChemistryEngine()
