"""
Equation Solver Engine
======================

PURPOSE:
    Solves algebraic equations and systems:
    - Linear Equations in 1 variable
    - Linear Systems in 2 variables (Substitution, Elimination, Cramer's Rule)
    - Quadratic Equations (Factorization, Quadratic Formula, Discriminant, Nature of Roots)
    - Higher Degree Polynomial Equations
"""

import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.normalizer import math_normalizer



class EquationEngine:
    """Specialized engine for solving equations deterministically."""

    def solve_equation(self, expr_str: str, query: str) -> Optional[SubjectSolveResult]:
        """
        Main equation solver routing to linear, quadratic, or general polynomial solver.
        """
        # Split into LHS and RHS
        if "=" in expr_str:
            parts = expr_str.split("=")
            lhs_str, rhs_str = parts[0].strip(), parts[1].strip()
        else:
            lhs_str, rhs_str = expr_str.strip(), "0"

        try:
            lhs = math_parser.parse(lhs_str)
            rhs = math_parser.parse(rhs_str)
            eq_expr = sp.simplify(lhs - rhs)
        except Exception:
            return None

        # Find variables
        symbols = list(eq_expr.free_symbols)
        if not symbols:
            return None

        if len(symbols) == 1:
            var = symbols[0]
            # Check polynomial degree
            poly = sp.Poly(eq_expr, var)
            degree = poly.degree()

            if degree == 1:
                return self._solve_linear_1var(poly, var, lhs_str, rhs_str, query)
            elif degree == 2:
                return self._solve_quadratic(poly, var, lhs_str, rhs_str, query)
            else:
                return self._solve_higher_degree(eq_expr, var, lhs_str, rhs_str, query, degree)

        return None

    def _solve_linear_1var(self, poly: sp.Poly, var: sp.Symbol, lhs_str: str, rhs_str: str, query: str) -> SubjectSolveResult:
        """Step-by-step linear equation in 1 variable: ax + b = 0."""
        coeffs = poly.all_coeffs()  # [a, b]
        a, b = coeffs[0], coeffs[1]
        solution = -b / a

        steps = [
            f"Given Equation: `{lhs_str} = {rhs_str}`",
            f"Rearrange terms into standard form `ax + b = 0`:",
            f"`{poly.as_expr()} = 0`",
            f"Isolate `{var}`: `{a}*{var} = {-b}`",
            f"Divide by coefficient `{a}`: `{var} = ({-b}) / {a}`",
            f"Solution: **`{var} = {solution}`**",
        ]
        answer = f"{var} = {solution}"
        title = f"Linear Equation in One Variable ({var})"
        formula = "ax + b = 0  ⟹  x = -b / a"
        md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
        return SubjectSolveResult(
            handled_locally=True,
            subject=SubjectType.MATHEMATICS,
            topic="equations",
            concept_id="math.algebra.linear_equation",
            intent=QuestionIntent.SOLVE,
            original_question=query,
            formula=formula,
            steps=steps,
            answer=answer,
            formatted_markdown=md,
            confidence=0.98,
        )

    def _solve_quadratic(self, poly: sp.Poly, var: sp.Symbol, lhs_str: str, rhs_str: str, query: str) -> SubjectSolveResult:
        """Step-by-step quadratic equation solver."""
        coeffs = poly.all_coeffs()  # [a, b, c]
        a, b, c = coeffs[0], coeffs[1], coeffs[2]

        # Discriminant: Δ = b² - 4ac
        disc = b**2 - 4*a*c
        roots = sp.solve(poly.as_expr(), var)

        # Factorized form
        factored = sp.factor(poly.as_expr())

        # Determine nature of roots
        if disc > 0:
            nature = "Two distinct real roots (Δ > 0)"
        elif disc == 0:
            nature = "Two real and equal roots (Δ = 0)"
        else:
            nature = "Two complex conjugate roots (Δ < 0)"

        sum_of_roots = -b / a
        product_of_roots = c / a

        steps = [
            f"Given Quadratic Equation: `{lhs_str} = {rhs_str}`",
            f"Standard Form `ax² + bx + c = 0`: **`{poly.as_expr()} = 0`**",
            f"Coefficients: `a = {a}`, `b = {b}`, `c = {c}`",
            f"**Discriminant (Δ):** `b² - 4ac = ({b})² - 4({a})({c}) = {disc}`",
            f"**Nature of Roots:** {nature}",
            f"**Sum of Roots (α + β):** `-b/a = {sum_of_roots}`",
            f"**Product of Roots (αβ):** `c/a = {product_of_roots}`",
        ]

        # Factorization Step if factorable over integers/rationals
        if factored != poly.as_expr():
            steps.append(f"**Factorisation:** `{factored} = 0`")

        steps.append(f"Applying Quadratic Formula: `{var} = (-b ± √Δ) / 2a`")
        roots_display = " or ".join(f"{var} = {r}" for r in roots)
        steps.append(f"**Roots:** **`{roots_display}`**")

        answer = roots_display
        title = "Quadratic Equation Solution"
        formula = "x = (-b ± √(b² - 4ac)) / 2a"
        md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
        return SubjectSolveResult(
            handled_locally=True,
            subject=SubjectType.MATHEMATICS,
            topic="quadratic_equations",
            concept_id="math.algebra.quadratic",
            intent=QuestionIntent.SOLVE,
            original_question=query,
            formula=formula,
            rules_applied=[nature],
            steps=steps,
            answer=answer,
            formatted_markdown=md,
            confidence=0.98,
        )

    def _solve_higher_degree(self, eq_expr: sp.Expr, var: sp.Symbol, lhs_str: str, rhs_str: str, query: str, degree: int) -> SubjectSolveResult:
        """Solves cubic or higher degree polynomial equations."""
        roots = sp.solve(eq_expr, var)
        factored = sp.factor(eq_expr)

        steps = [
            f"Given Polynomial Equation of Degree {degree}: `{lhs_str} = {rhs_str}`",
            f"Standard Form: `{eq_expr} = 0`",
            f"Factored form: `{factored} = 0`",
            f"Solving for zeroes:",
        ]
        roots_display = ", ".join(f"{var} = {r}" for r in roots)
        steps.append(f"Roots: **`{roots_display}`**")

        answer = roots_display
        title = f"Degree {degree} Polynomial Equation"
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
            confidence=0.95,
        )

    def solve_linear_system_2var(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves simultaneous linear equations in 2 variables:
        e.g. 'solve 2x + y = 7 and x - y = 2' or '2x + 3y = 12, x - y = 1'
        """
        # Split by 'and', ',', ';'
        parts = re.split(r'\b(?:and|,|;)\b', query, flags=re.IGNORECASE)
        if len(parts) < 2:
            return None

        eqs = []
        for p in parts:
            p_clean = re.sub(r'\b(solve|find|system\s+of\s+equations)\b', '', p, flags=re.IGNORECASE).strip()
            if "=" in p_clean:
                lhs_str, rhs_str = p_clean.split("=", 1)
                try:
                    norm_lhs = math_normalizer.normalize(lhs_str)
                    norm_rhs = math_normalizer.normalize(rhs_str)
                    lhs = math_parser.parse(norm_lhs)
                    rhs = math_parser.parse(norm_rhs)
                    eqs.append(sp.Eq(lhs, rhs))
                except Exception:
                    pass


        if len(eqs) == 2:
            try:
                solution = sp.solve(eqs)
                if solution and isinstance(solution, dict):
                    steps = [
                        f"Given System of Linear Equations:",
                        f"Equation (1): `{eqs[0].lhs} = {eqs[0].rhs}`",
                        f"Equation (2): `{eqs[1].lhs} = {eqs[1].rhs}`",
                        f"Apply Elimination / Substitution / Cramer's Method.",
                    ]
                    ans_parts = []
                    for sym, val in solution.items():
                        steps.append(f"Value of `{sym}` = **{val}**")
                        ans_parts.append(f"{sym} = {val}")

                    answer = ", ".join(ans_parts)
                    title = "System of Linear Equations (2 Variables)"
                    formula = "Matrix Method / Cramer's Rule / Elimination"
                    md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
                    return SubjectSolveResult(
                        handled_locally=True,
                        subject=SubjectType.MATHEMATICS,
                        topic="equations",
                        concept_id="math.algebra.linear_equation",
                        intent=QuestionIntent.SOLVE,
                        original_question=query,
                        formula=formula,
                        steps=steps,
                        answer=answer,
                        formatted_markdown=md,
                        confidence=0.98,
                    )
            except Exception:
                pass
        return None


# Global instance
equation_engine = EquationEngine()
