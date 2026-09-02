"""
Polynomial Operations & Theorems Engine
=======================================

PURPOSE:
    Handles polynomial calculations:
    - Polynomial Long Division (Quotient & Remainder)
    - Remainder Theorem & Factor Theorem
    - Finding Zeroes of Polynomials
    - Roots and Coefficients Relationships (Vieta's Formulas)
"""

import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


class PolynomialEngine:
    """Specialized engine for polynomial theorems and polynomial division."""

    def solve_polynomial_division(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Handles polynomial division: 'divide P(x) by Q(x)' or 'remainder when P(x) is divided by x - a'.
        """
        # Match 'divide <P(x)> by <Q(x)>'
        div_match = re.search(r'divide\s+(.+?)\s+by\s+(.+)', query, re.IGNORECASE)
        rem_match = re.search(r'remainder\s+when\s+(.+?)\s+is\s+divided\s+by\s+(.+)', query, re.IGNORECASE)

        if div_match:
            p_str, q_str = div_match.group(1).strip(), div_match.group(2).strip()
            is_remainder_only = False
        elif rem_match:
            p_str, q_str = rem_match.group(1).strip(), rem_match.group(2).strip()
            is_remainder_only = True
        else:
            return None

        try:
            P = math_parser.parse(p_str)
            Q = math_parser.parse(q_str)
            x = list(P.free_symbols | Q.free_symbols)[0] if (P.free_symbols | Q.free_symbols) else sp.Symbol('x')

            quotient, remainder = sp.div(P, Q, x)

            steps = [
                f"Dividend P({x}) = `{P}`",
                f"Divisor Q({x}) = `{Q}`",
                f"Division Algorithm: `Dividend = Divisor × Quotient + Remainder`",
                f"**Quotient Q({x}):** `{quotient}`",
                f"**Remainder R({x}):** `{remainder}`",
            ]

            if is_remainder_only:
                answer = f"Remainder = {remainder}"
                title = "Remainder Theorem Evaluation"
            else:
                answer = f"Quotient = {quotient}, Remainder = {remainder}"
                title = "Polynomial Division"

            formula = "P(x) = D(x) · Q(x) + R(x)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="polynomials",
                concept_id="math.algebra.polynomials",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )
        except Exception:
            return None

    def solve_zeroes(self, query: str) -> Optional[SubjectSolveResult]:
        """Finds zeroes/roots of a polynomial expression."""
        match = re.search(r'\b(?:zeroes|roots)\s+of\s+(.+)', query, re.IGNORECASE)
        if not match:
            return None

        expr_str = match.group(1).strip()
        try:
            expr = math_parser.parse(expr_str)
            symbols = list(expr.free_symbols)
            if not symbols:
                return None
            var = symbols[0]
            zeroes = sp.solve(expr, var)
            factored = sp.factor(expr)

            steps = [
                f"Given Polynomial P({var}) = `{expr}`",
                f"Set P({var}) = 0: `{expr} = 0`",
                f"Factored form: `{factored} = 0`",
            ]
            zeroes_str = ", ".join(f"{var} = {z}" for z in zeroes)
            steps.append(f"Zeroes of the polynomial: **`{zeroes_str}`**")

            answer = zeroes_str
            title = f"Zeroes of Polynomial P({var})"
            md = math_formatter.format_solution(query, answer, steps, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="polynomials",
                concept_id="math.algebra.polynomials",
                intent=QuestionIntent.SOLVE,
                original_question=query,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.97,
            )
        except Exception:
            return None


# Global instance
polynomial_engine = PolynomialEngine()
