"""
Mathematics Specialized Concept Engines
=======================================
"""

from app.subject_engine.mathematics.engines.arithmetic import arithmetic_engine
from app.subject_engine.mathematics.engines.algebra import algebra_engine
from app.subject_engine.mathematics.engines.equation import equation_engine
from app.subject_engine.mathematics.engines.polynomial import polynomial_engine
from app.subject_engine.mathematics.engines.geometry import geometry_engine
from app.subject_engine.mathematics.engines.trigonometry import trigonometry_engine
from app.subject_engine.mathematics.engines.coordinate_geometry import coordinate_engine
from app.subject_engine.mathematics.engines.matrix import matrix_engine
from app.subject_engine.mathematics.engines.statistics import statistics_engine
from app.subject_engine.mathematics.engines.probability import probability_engine
from app.subject_engine.mathematics.engines.calculus import calculus_engine
from app.subject_engine.mathematics.engines.vector import vector_engine
from app.subject_engine.mathematics.engines.sequence_series import sequence_engine
from app.subject_engine.mathematics.engines.permutation_combination import perm_comb_engine
from app.subject_engine.mathematics.engines.binomial import binomial_engine
from app.subject_engine.mathematics.engines.set_theory import set_theory_engine
from app.subject_engine.mathematics.engines.financial_math import financial_math_engine
from app.subject_engine.mathematics.engines.units import units_engine
from app.subject_engine.mathematics.engines.proof import proof_engine

__all__ = [
    "arithmetic_engine",
    "algebra_engine",
    "equation_engine",
    "polynomial_engine",
    "geometry_engine",
    "trigonometry_engine",
    "coordinate_engine",
    "matrix_engine",
    "statistics_engine",
    "probability_engine",
    "calculus_engine",
    "vector_engine",
    "sequence_engine",
    "perm_comb_engine",
    "binomial_engine",
    "set_theory_engine",
    "financial_math_engine",
    "units_engine",
    "proof_engine",
]
