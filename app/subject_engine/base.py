"""
Subject Engine Base Types & Abstract Definitions
================================================

PURPOSE:
    Defines generic types, data models, and base classes for all local Subject Engines
    (Mathematics, Physics, Chemistry, Biology).
"""

from enum import Enum
from typing import Any, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class SubjectType(str, Enum):
    """Supported Subject Engine Types."""
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"


class QuestionIntent(str, Enum):
    """Classification of mathematical and academic question intents."""
    CALCULATE = "CALCULATE"
    SIMPLIFY = "SIMPLIFY"
    SOLVE = "SOLVE"
    FACTOR = "FACTOR"
    EXPAND = "EXPAND"
    EVALUATE = "EVALUATE"
    CONVERT = "CONVERT"
    PROVE = "PROVE"
    DEFINE = "DEFINE"
    EXPLAIN_CONCEPT = "EXPLAIN_CONCEPT"
    FIND_FORMULA = "FIND_FORMULA"
    FIND_VALUE = "FIND_VALUE"
    DIFFERENTIATE = "DIFFERENTIATE"
    INTEGRATE = "INTEGRATE"
    GRAPH = "GRAPH"
    COMPARE = "COMPARE"
    CHECK_ANSWER = "CHECK_ANSWER"
    WORD_PROBLEM = "WORD_PROBLEM"
    UNIT_CONVERSION = "UNIT_CONVERSION"
    BALANCE_EQUATION = "BALANCE_EQUATION"
    FORMULA_LOOKUP = "FORMULA_LOOKUP"
    IDENTIFY_STRUCTURE = "IDENTIFY_STRUCTURE"
    EXPLAIN_FUNCTION = "EXPLAIN_FUNCTION"
    TAXONOMY_LOOKUP = "TAXONOMY_LOOKUP"
    DIFFERENCE = "DIFFERENCE"
    UNKNOWN = "UNKNOWN"




class SubjectSolveResult(BaseModel):
    """
    Standardized result payload returned by any Subject Engine.
    """
    handled_locally: bool = Field(
        default=False,
        description="True if the question was successfully and confidently answered locally",
    )
    subject: SubjectType = Field(
        default=SubjectType.MATHEMATICS,
        description="Subject area of the question",
    )
    topic: Optional[str] = Field(
        default=None,
        description="Specific academic topic (e.g., 'quadratic_equations', 'differentiation')",
    )
    concept_id: Optional[str] = Field(
        default=None,
        description="Unique identifier from the concept knowledge base",
    )
    intent: QuestionIntent = Field(
        default=QuestionIntent.UNKNOWN,
        description="Identified user goal or mathematical operation",
    )
    original_question: str = Field(
        default="",
        description="The raw input question received from the user",
    )
    normalized_expression: Optional[str] = Field(
        default=None,
        description="Canonical mathematical expression after text normalization",
    )
    formula: Optional[str] = Field(
        default=None,
        description="Key mathematical formula or identity utilized in the solution",
    )
    rules_applied: list[str] = Field(
        default_factory=list,
        description="List of educational rules or theorem names applied",
    )
    steps: list[str] = Field(
        default_factory=list,
        description="Step-by-step pedagogical working for student understanding",
    )
    answer: str = Field(
        default="",
        description="Final concise or formatted answer",
    )
    formatted_markdown: str = Field(
        default="",
        description="Rich pedagogical markdown response ready for UI rendering",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Physical or mathematical unit where applicable",
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence score of the understanding and solution (0.0 - 1.0)",
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Engine computation duration in milliseconds",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error detail if local solving failed",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional debug or domain-specific metadata",
    )


@runtime_checkable
class BaseSubjectEngine(Protocol):
    """Base interface that every Subject Engine must implement."""

    @property
    def subject(self) -> SubjectType:
        """The subject type this engine handles."""
        ...

    def can_handle(self, query: str) -> tuple[bool, float]:
        """
        Evaluate if the query belongs to this subject and can be handled.
        Returns (can_handle, confidence_score).
        """
        ...

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        """
        Parse, solve, and format the question deterministically.
        """
        ...
