"""
Subject Engine Dedicated API Endpoints
======================================

PURPOSE:
    Provides direct REST endpoints for testing, frontend integration, and developer usage
    of the local Subject Engines (Mathematics, etc.).
"""

from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.subject_engine.base import SubjectSolveResult, SubjectType
from app.subject_engine.router import subject_router
from app.subject_engine.mathematics.engine import math_engine
from app.subject_engine.mathematics.concepts import CONCEPTS_CATALOG, MathConcept
from app.subject_engine.science.router import science_engine
from app.subject_engine.science.physics.engine import physics_engine
from app.subject_engine.science.chemistry.engine import chemistry_engine
from app.subject_engine.science.biology.engine import biology_engine
from app.subject_engine.science.physics.concepts import PHYSICS_CONCEPTS_CATALOG, PhysicsConcept
from app.subject_engine.science.chemistry.concepts import CHEMISTRY_CONCEPTS_CATALOG, ChemistryConcept
from app.subject_engine.science.biology.knowledge import BIOLOGY_CONCEPTS_CATALOG, BiologyConcept


router = APIRouter(prefix="/subject-engine", tags=["Subject Engine"])


class MathSolveRequest(BaseModel):
    """Request body for solving mathematics questions directly."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The mathematical question or expression (natural language or standard math syntax)",
        examples=["solve x square - 5x + 6 = 0", "x to the power 3 + 5x square", "differentiate x cube", "find HCF of 24 and 36"],
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional student context or grade level",
    )


class ScienceSolveRequest(BaseModel):
    """Request body for solving science questions (Physics, Chemistry, Biology)."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The science question (Physics numericals, Chemistry formulas/reactions, Biology concepts)",
        examples=[
            "mass is 5 kg and acceleration is 2 find force",
            "molecular mass of H2SO4",
            "balance H2 + O2 -> H2O",
            "why is mitochondria called powerhouse of cell",
            "atomic number of sodium",
            "difference between mitosis and meiosis",
        ],
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional student context or grade level",
    )


class GenericSolveRequest(BaseModel):
    """Request body for solving questions across any subject engine."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The academic question to solve",
    )
    subject: Optional[str] = Field(
        default=None,
        description="Optional target subject (e.g. 'mathematics', 'physics', 'chemistry', 'biology', 'science')",
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional context data",
    )


@router.post(
    "/mathematics/solve",
    response_model=SubjectSolveResult,
    summary="Solve Mathematics Question Locally",
    description="Understands and solves LKG through PUC mathematics questions locally with zero Claude / LLM calls.",
)
async def solve_mathematics(request: MathSolveRequest) -> SubjectSolveResult:
    """Solve mathematics question deterministically."""
    if not settings.enable_subject_engine or not settings.enable_math_engine:
        raise HTTPException(
            status_code=400,
            detail="Mathematics Engine is currently disabled.",
        )
    return math_engine.solve(request.question, context=request.context)


@router.post(
    "/science/solve",
    response_model=SubjectSolveResult,
    summary="Solve Science Question Locally",
    description="Understands and solves LKG through PUC Science questions (Physics, Chemistry, Biology) with zero Claude / LLM calls.",
)
async def solve_science(request: ScienceSolveRequest) -> SubjectSolveResult:
    """Solve science question deterministically across Physics, Chemistry, Biology."""
    if not settings.enable_subject_engine or not settings.enable_science_engine:
        raise HTTPException(
            status_code=400,
            detail="Science Engine is currently disabled.",
        )
    return science_engine.solve(request.question, context=request.context)


@router.post(
    "/physics/solve",
    response_model=SubjectSolveResult,
    summary="Solve Physics Question Locally",
    description="Solves Physics numericals and conceptual questions deterministically.",
)
async def solve_physics(request: ScienceSolveRequest) -> SubjectSolveResult:
    """Solve Physics question deterministically."""
    if not settings.enable_subject_engine or not settings.enable_science_engine:
        raise HTTPException(
            status_code=400,
            detail="Physics Engine is currently disabled.",
        )
    return physics_engine.solve(request.question, context=request.context)


@router.post(
    "/chemistry/solve",
    response_model=SubjectSolveResult,
    summary="Solve Chemistry Question Locally",
    description="Solves Chemistry formulas, periodic table lookups, and equation balancing deterministically.",
)
async def solve_chemistry(request: ScienceSolveRequest) -> SubjectSolveResult:
    """Solve Chemistry question deterministically."""
    if not settings.enable_subject_engine or not settings.enable_science_engine:
        raise HTTPException(
            status_code=400,
            detail="Chemistry Engine is currently disabled.",
        )
    return chemistry_engine.solve(request.question, context=request.context)


@router.post(
    "/biology/solve",
    response_model=SubjectSolveResult,
    summary="Solve Biology Question Locally",
    description="Provides deterministic Biology concept explanations, mechanisms, and comparison tables.",
)
async def solve_biology(request: ScienceSolveRequest) -> SubjectSolveResult:
    """Solve Biology question deterministically."""
    if not settings.enable_subject_engine or not settings.enable_science_engine:
        raise HTTPException(
            status_code=400,
            detail="Biology Engine is currently disabled.",
        )
    return biology_engine.solve(request.question, context=request.context)


@router.post(
    "/solve",
    response_model=SubjectSolveResult,
    summary="Generic Subject Engine Solver",
    description="Routes and solves academic questions through local Subject Engines.",
)
async def solve_subject(request: GenericSolveRequest) -> SubjectSolveResult:
    """Route and solve across registered subject engines."""
    if not settings.enable_subject_engine:
        raise HTTPException(
            status_code=400,
            detail="Subject Engine is currently disabled.",
        )
    result = subject_router.route_and_solve(request.question, context=request.context)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="The question could not be confidently understood or solved by local Subject Engines.",
        )
    return result


@router.get(
    "/mathematics/concepts",
    response_model=list[MathConcept],
    summary="Get Mathematics Concept Catalog",
    description="Returns the complete curriculum concept knowledge base spanning LKG to PUC.",
)
async def get_math_concepts() -> list[MathConcept]:
    """Retrieve all supported mathematics concepts."""
    return CONCEPTS_CATALOG


@router.get(
    "/science/concepts",
    summary="Get Science Concept Catalog",
    description="Returns the complete curriculum concept knowledge base for Physics, Chemistry, and Biology.",
)
async def get_science_concepts() -> dict[str, Any]:
    """Retrieve all supported science concepts across Physics, Chemistry, and Biology."""
    return {
        "physics": [c.model_dump() for c in PHYSICS_CONCEPTS_CATALOG],
        "chemistry": [c.model_dump() for c in CHEMISTRY_CONCEPTS_CATALOG],
        "biology": [c.model_dump() for c in BIOLOGY_CONCEPTS_CATALOG],
    }

