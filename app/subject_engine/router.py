"""
Generic Subject Engine Router
=============================

PURPOSE:
    Central router that coordinates all local subject engines (Mathematics, Physics,
    Chemistry, Biology) and routes incoming student academic questions without hitting Claude.
"""

from typing import Any, Optional
from app.subject_engine.base import BaseSubjectEngine, SubjectType, SubjectSolveResult
from app.subject_engine.mathematics.engine import math_engine
from app.subject_engine.science.router import science_engine
from app.subject_engine.science.physics.engine import physics_engine
from app.subject_engine.science.chemistry.engine import chemistry_engine
from app.subject_engine.science.biology.engine import biology_engine
from app.core.logging import get_logger

logger = get_logger(__name__)


class SubjectEngineRouter:
    """Routes academic queries to corresponding local subject engines."""

    def __init__(self) -> None:
        self._engines: dict[SubjectType, BaseSubjectEngine] = {}
        # Register Mathematics Engine
        self.register_engine(math_engine)
        # Register Science Engines (Physics, Chemistry, Biology, Unified Science)
        self.register_engine(science_engine)
        self.register_engine(physics_engine)
        self.register_engine(chemistry_engine)
        self.register_engine(biology_engine)

    def register_engine(self, engine: BaseSubjectEngine) -> None:
        """Register a subject engine."""
        self._engines[engine.subject] = engine
        logger.info("subject_engine_registered", subject=engine.subject.value)

    def get_engine(self, subject: SubjectType) -> Optional[BaseSubjectEngine]:
        """Retrieve a specific registered subject engine."""
        return self._engines.get(subject)

    def route_and_solve(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        min_confidence: float = 0.35,
    ) -> Optional[SubjectSolveResult]:
        """
        Evaluates the query across all registered subject engines in order:
        Science (Physics, Chemistry, Biology) and Mathematics.
        If any subject engine can solve it confidently, returns the solved result.
        Otherwise returns None.
        """
        # Step 1: Check Science Engine (Physics, Chemistry, Biology)
        sci_eng = self._engines.get(SubjectType.SCIENCE)
        if sci_eng:
            can_handle, conf = sci_eng.can_handle(query)
            if can_handle and conf >= min_confidence:
                result = sci_eng.solve(query, context=context)
                if result and result.handled_locally:
                    logger.info(
                        "subject_engine_solved_locally",
                        subject=result.subject.value,
                        topic=result.topic,
                        intent=result.intent.value,
                        confidence=result.confidence,
                        execution_time_ms=result.execution_time_ms,
                    )
                    return result

        # Step 2: Check Mathematics Engine
        math_eng = self._engines.get(SubjectType.MATHEMATICS)
        if math_eng:
            can_handle, conf = math_eng.can_handle(query)
            if can_handle and conf >= min_confidence:
                result = math_eng.solve(query, context=context)
                if result and result.handled_locally:
                    logger.info(
                        "subject_engine_solved_locally",
                        subject=result.subject.value,
                        topic=result.topic,
                        intent=result.intent.value,
                        confidence=result.confidence,
                        execution_time_ms=result.execution_time_ms,
                    )
                    return result

        return None



# Global Subject Engine Router
subject_router = SubjectEngineRouter()
