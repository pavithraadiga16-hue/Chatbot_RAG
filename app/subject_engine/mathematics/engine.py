"""
Mathematics Engine Facade
=========================

PURPOSE:
    Implements the BaseSubjectEngine protocol for Mathematics, wrapping the normalizer,
    classifier, parser, and master solver.
"""

from typing import Optional, Any
from app.subject_engine.base import BaseSubjectEngine, SubjectType, SubjectSolveResult
from app.subject_engine.mathematics.classifier import math_classifier
from app.subject_engine.mathematics.solver import math_solver


class MathematicsEngine(BaseSubjectEngine):
    """Local, deterministic Mathematics Engine covering LKG through PUC."""

    @property
    def subject(self) -> SubjectType:
        return SubjectType.MATHEMATICS

    def can_handle(self, query: str) -> tuple[bool, float]:
        """
        Evaluates whether the query is mathematics and can be handled locally.
        Returns (can_handle, confidence_score).
        """
        classification = math_classifier.classify(query)
        return classification.is_mathematics, classification.confidence

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        """
        Solves the mathematical question deterministically.
        """
        return math_solver.solve(query, context=context)


# Global engine instance
math_engine = MathematicsEngine()
