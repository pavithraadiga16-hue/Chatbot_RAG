"""
PhinsIQ Mathematics Engine Package
==================================

Covers the complete mathematics curriculum from LKG through PUC (Grade 12).
100% Deterministic (Zero external LLM / Claude dependency).
"""

from app.subject_engine.mathematics.engine import MathematicsEngine, math_engine
from app.subject_engine.mathematics.normalizer import math_normalizer
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.classifier import math_classifier
from app.subject_engine.mathematics.solver import math_solver
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.concepts import concept_kb

__all__ = [
    "MathematicsEngine",
    "math_engine",
    "math_normalizer",
    "math_parser",
    "math_classifier",
    "math_solver",
    "math_formatter",
    "concept_kb",
]
