"""
Physics Engine Facade
=====================

PURPOSE:
    Implements BaseSubjectEngine for Physics.
"""

from typing import Optional, Any
from app.subject_engine.base import BaseSubjectEngine, SubjectType, SubjectSolveResult
from app.subject_engine.science.classifier import science_classifier
from app.subject_engine.science.physics.solver import physics_solver


class PhysicsEngine(BaseSubjectEngine):
    """Local deterministic Physics Engine covering LKG through PUC."""

    @property
    def subject(self) -> SubjectType:
        return SubjectType.PHYSICS

    def can_handle(self, query: str) -> tuple[bool, float]:
        classification = science_classifier.classify(query)
        can_h = classification.is_science and classification.branch == SubjectType.PHYSICS
        return can_h, classification.confidence

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        return physics_solver.solve(query, context=context)


# Global instance
physics_engine = PhysicsEngine()
