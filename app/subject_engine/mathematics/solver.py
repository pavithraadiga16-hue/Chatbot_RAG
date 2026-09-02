"""
Mathematics Master Solver Orchestrator
======================================

PURPOSE:
    Central deterministic solver that orchestrates specialized concept engines,
    performs multi-layered routing, and constructs student-friendly pedagogical responses.
"""

import time
import re
from typing import Optional, Any
import sympy as sp

from app.subject_engine.base import (
    SubjectType,
    QuestionIntent,
    SubjectSolveResult,
)
from app.subject_engine.mathematics.normalizer import math_normalizer
from app.subject_engine.mathematics.classifier import math_classifier
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.concepts import concept_kb
from app.subject_engine.mathematics.engines import (
    arithmetic_engine,
    algebra_engine,
    equation_engine,
    polynomial_engine,
    geometry_engine,
    trigonometry_engine,
    coordinate_engine,
    matrix_engine,
    statistics_engine,
    probability_engine,
    calculus_engine,
    vector_engine,
    sequence_engine,
    perm_comb_engine,
    binomial_engine,
    set_theory_engine,
    financial_math_engine,
    units_engine,
    proof_engine,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class MathSolver:
    """Master solver orchestrator for mathematics."""

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        """
        Main solving pipeline.
        """
        start_time = time.monotonic()
        raw_query = query.strip()

        # Step 1: Normalization
        normalized = math_normalizer.normalize(raw_query)

        # Step 2: Classification
        classification = math_classifier.classify(raw_query)
        lower_q = raw_query.lower()
        extracted_expr = classification.extracted_expression or normalized

        # -------------------------------------------------------------
        # Dispatch Strategy: Route to specialized engines
        # -------------------------------------------------------------

        # 1. Theorems & Proofs / Prameya
        if classification.intent == QuestionIntent.PROVE or any(kw in lower_q for kw in ("prove", "proof", "prameya", "show that")):
            res = proof_engine.solve_proof(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 2. Concept Definitions & Formula Lookup
        if classification.intent in (QuestionIntent.DEFINE, QuestionIntent.FIND_FORMULA) or lower_q.startswith(("what is a ", "what is an ", "what is the formula", "formula for", "define ")):
            res = self._handle_concept_or_formula_lookup(raw_query, lower_q)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 3. Unit Conversions (e.g. 5 km to meters, 30 deg to rad, 100 C to F)
        if classification.intent == QuestionIntent.UNIT_CONVERSION or "convert" in lower_q:
            res = units_engine.solve_conversion(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 4. HCF, LCM, Prime Factorization, Prime Check
        if any(kw in lower_q for kw in ("hcf", "gcd", "lcm", "highest common", "lowest common", "least common")):
            res = arithmetic_engine.solve_hcf_lcm(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        if any(kw in lower_q for kw in ("prime", "composite", "prime factors", "prime factorization", "factors of")):
            res = arithmetic_engine.solve_prime_factors(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 5. Financial Math, Percentages, Interest, Profit & Loss
        if any(kw in lower_q for kw in ("%", "percent", "percentage")):
            res = financial_math_engine.solve_percentage(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        if any(kw in lower_q for kw in ("simple interest", "compound interest", "principal")) or bool(re.search(r'\b(si|ci)\b', lower_q)):
            res = financial_math_engine.solve_interest(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        if any(kw in lower_q for kw in ("profit", "loss", "cost price", "selling price")) or bool(re.search(r'\b(cp|sp)\b', lower_q)):
            res = financial_math_engine.solve_profit_loss(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)


        # 6. Sequences & Series (AP & GP)
        if any(kw in lower_q for kw in ("ap", "gp", "arithmetic progression", "geometric progression", "nth term", "sum of first")):
            res = sequence_engine.solve_ap_gp(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 7. Permutations, Combinations & Factorials
        if "!" in raw_query or re.search(r'\b(\d+\s*[PC]\s*\d+|factorial|permutations?|combinations?)\b', raw_query, re.IGNORECASE):
            res = perm_comb_engine.solve_combinatorics(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 8. Binomial Expansions
        if re.search(r'\((.+?)\)\s*(?:\^|\*\*)\s*(\d+)', raw_query):
            res = binomial_engine.solve_binomial_expansion(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 9. Statistics (Mean, Median, Mode, Variance, Standard Deviation)
        if any(kw in lower_q for kw in ("mean", "median", "mode", "variance", "standard deviation", "std dev")):
            res = statistics_engine.solve_statistics(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 10. Probability (Coin, Dice, Card)
        if "probability" in lower_q or "chance" in lower_q:
            res = probability_engine.solve_probability(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 11. Vectors (Magnitude, Dot product, Cross product)
        if any(kw in lower_q for kw in ("vector", "dot product", "cross product", "magnitude of")):
            res = vector_engine.solve_vector_operation(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 12. Matrices & Determinants
        if "[[" in raw_query or any(kw in lower_q for kw in ("matrix", "matrices", "determinant", "det")):
            res = matrix_engine.solve_matrix_operation(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 13. Coordinate Geometry (Distance, Midpoint, Slope, Line)
        if any(kw in lower_q for kw in ("distance between", "midpoint of", "slope of line", "equation of line", "coordinate")):
            res = coordinate_engine.solve_coordinate_problems(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 14. 2D Geometry & 3D Mensuration (Circle, Triangle, Pythagoras, Cylinder, Sphere, Cube)
        if any(kw in lower_q for kw in ("circle", "pythagoras", "hypotenuse", "right triangle", "cylinder", "sphere", "cube", "cuboid", "cone", "heron", "area of triangle")):
            if "circle" in lower_q:
                res = geometry_engine.solve_circle(raw_query)
                if res:
                    return self._finalize(res, start_time, raw_query, normalized)
            if any(kw in lower_q for kw in ("pythagoras", "hypotenuse", "right triangle")):
                res = geometry_engine.solve_pythagoras(raw_query)
                if res:
                    return self._finalize(res, start_time, raw_query, normalized)
            if "triangle" in lower_q:
                res = geometry_engine.solve_triangle_area(raw_query)
                if res:
                    return self._finalize(res, start_time, raw_query, normalized)
            if any(kw in lower_q for kw in ("cylinder", "sphere", "cube", "cuboid", "cone")):
                res = geometry_engine.solve_3d_mensuration(raw_query)
                if res:
                    return self._finalize(res, start_time, raw_query, normalized)

        # 15. Trigonometry (sin, cos, tan, sec, cosec, cot)
        if any(kw in lower_q for kw in ("sin", "cos", "tan", "sec", "csc", "cosec", "cot", "trig")):
            res = trigonometry_engine.evaluate_trig(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 16. Calculus (Differentiation, Integration, Limits)
        if classification.intent == QuestionIntent.DIFFERENTIATE or any(kw in lower_q for kw in ("differentiate", "derivative", "diff", "d/dx")):
            res = calculus_engine.solve_derivative(extracted_expr, raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        if classification.intent == QuestionIntent.INTEGRATE or any(kw in lower_q for kw in ("integrate", "integration", "antiderivative", "integral")):
            res = calculus_engine.solve_integral(extracted_expr, raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        if "limit" in lower_q or "lim " in lower_q:
            res = calculus_engine.solve_limit(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 17. Polynomial Division & Zeroes
        if any(kw in lower_q for kw in ("divide", "remainder when", "zeroes of", "roots of polynomial")):
            if "divide" in lower_q or "remainder" in lower_q:
                res = polynomial_engine.solve_polynomial_division(raw_query)
                if res:
                    return self._finalize(res, start_time, raw_query, normalized)
            if "zeroes" in lower_q:
                res = polynomial_engine.solve_zeroes(raw_query)
                if res:
                    return self._finalize(res, start_time, raw_query, normalized)

        # 18. Simultaneous Equations (2 variables)
        if re.search(r'\b(?:and|,|;)\b', raw_query) and "=" in raw_query:
            res = equation_engine.solve_linear_system_2var(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 19. Single Equations (Linear, Quadratic, Polynomial)
        if "=" in extracted_expr or "=" in normalized:
            res = equation_engine.solve_equation(extracted_expr, raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 20. Algebraic Factorization
        if classification.intent == QuestionIntent.FACTOR or "factor" in lower_q:
            res = algebra_engine.factor_expression(extracted_expr, raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 21. Algebraic Substitution
        if any(kw in lower_q for kw in ("if x =", "when x =", "for x =", "if a =", "when y =")):
            res = algebra_engine.evaluate_substitution(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 22. Sets & Subsets
        if "{" in raw_query and "}" in raw_query:
            res = set_theory_engine.solve_set_operations(raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 23. Algebraic Simplification & Expansion
        if any(c in extracted_expr for c in ('x', 'y', 'z', 'a', 'b')):
            res = algebra_engine.simplify_expression(extracted_expr, raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        # 24. Exact Fraction & BODMAS Arithmetic
        if "/" in extracted_expr:
            res = arithmetic_engine.solve_fractions(extracted_expr, raw_query)
            if res:
                return self._finalize(res, start_time, raw_query, normalized)

        res = arithmetic_engine.solve_general_arithmetic(extracted_expr, raw_query)
        if res:
            return self._finalize(res, start_time, raw_query, normalized)

        # -------------------------------------------------------------
        # Not handled locally / low confidence
        # -------------------------------------------------------------
        elapsed = (time.monotonic() - start_time) * 1000.0
        return SubjectSolveResult(
            handled_locally=False,
            subject=SubjectType.MATHEMATICS,
            intent=classification.intent,
            original_question=raw_query,
            normalized_expression=normalized,
            confidence=classification.confidence,
            execution_time_ms=elapsed,
        )

    def _handle_concept_or_formula_lookup(self, query: str, lower_q: str) -> Optional[SubjectSolveResult]:
        """Looks up mathematical concepts and returns structured definitions & formulas."""
        matched = concept_kb.find_by_query(query)
        if matched:
            concept, score = matched[0]
            md = math_formatter.format_concept_definition(
                name=concept.name,
                definition=concept.definition,
                formula=concept.formula,
                rules=concept.rules,
                examples=concept.examples,
            )
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic=concept.topic,
                concept_id=concept.concept_id,
                intent=QuestionIntent.DEFINE,
                original_question=query,
                formula=concept.formula,
                rules_applied=concept.rules,
                steps=[concept.definition],
                answer=concept.formula or concept.definition,
                formatted_markdown=md,
                confidence=0.99,
            )
        return None

    def _finalize(self, res: SubjectSolveResult, start_time: float, raw_q: str, norm_q: str) -> SubjectSolveResult:
        """Adds execution time and default fields."""
        res.execution_time_ms = (time.monotonic() - start_time) * 1000.0
        res.original_question = raw_q
        if not res.normalized_expression:
            res.normalized_expression = norm_q
        return res


# Global MathSolver
math_solver = MathSolver()
