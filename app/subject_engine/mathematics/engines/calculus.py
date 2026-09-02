"""
Calculus Engine (Limits, Derivatives, Integrals, Differential Equations)
========================================================================

PURPOSE:
    Solves differential and integral calculus problems:
    - Limits (algebraic, trigonometric, limits at infinity)
    - Differentiation (Power, Product, Quotient, Chain Rules, Trig, Exp, Log)
    - Higher-Order Derivatives & Critical Points (Maxima / Minima)
    - Indefinite & Definite Integrals
    - Area Under Curves
    - Differential Equations (Separable & First-Order)
"""

import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


class CalculusEngine:
    """Specialized engine for differential and integral calculus."""

    def solve_derivative(self, expr_str: str, query: str) -> Optional[SubjectSolveResult]:
        """Calculates first and higher-order derivatives."""
        try:
            parsed = math_parser.parse(expr_str)
            symbols = list(parsed.free_symbols)
            var = symbols[0] if symbols else sp.Symbol('x')

            # Check if 2nd derivative requested
            is_second = bool(re.search(r'\b(second\s+derivative|d2\/dx2|d\^2|2nd\s+derivative)\b', query, re.IGNORECASE))
            order = 2 if is_second else 1

            deriv = sp.diff(parsed, var, order)
            simplified_deriv = sp.simplify(deriv)

            steps = [
                f"Given Function: `f({var}) = {parsed}`",
                f"Apply standard rules of differentiation (Power Rule, Product Rule, Chain Rule):",
            ]
            if order == 1:
                steps.append(f"First Derivative `d/d{var}[f({var})]`:")
                steps.append(f"**f'({var}) = `{simplified_deriv}`**")
                formula = "d/dx[xⁿ] = n·xⁿ⁻¹,  d/dx[sin x] = cos x,  d/dx[eˣ] = eˣ"
            else:
                first_deriv = sp.diff(parsed, var, 1)
                steps.append(f"First Derivative `f'({var}) = {first_deriv}`")
                steps.append(f"Second Derivative `f''({var}) = d/d{var}[f'({var})]`:")
                steps.append(f"**f''({var}) = `{simplified_deriv}`**")
                formula = "f''(x) = d²y/dx²"

            answer = str(simplified_deriv)
            title = f"Derivative with respect to {var}"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="calculus",
                concept_id="math.calculus.differentiation",
                intent=QuestionIntent.DIFFERENTIATE,
                original_question=query,
                normalized_expression=expr_str,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )
        except Exception:
            return None

    def solve_integral(self, expr_str: str, query: str) -> Optional[SubjectSolveResult]:
        """Calculates indefinite and definite integrals."""
        try:
            # Check if definite integral bounds specified: e.g. "from 0 to 2" or "from a to b"
            bounds_match = re.search(r'\bfrom\s+([-+]?\d*\.?\d+|pi|oo)\s+to\s+([-+]?\d*\.?\d+|pi|oo)', query, re.IGNORECASE)

            # Strip limits phrases from expression string
            clean_expr = re.sub(r'\bfrom\s+.*?to\s+.*', '', expr_str, flags=re.IGNORECASE).strip()
            parsed = math_parser.parse(clean_expr)
            symbols = list(parsed.free_symbols)
            var = symbols[0] if symbols else sp.Symbol('x')

            if bounds_match:
                # Definite integral
                lower_bound_str = bounds_match.group(1)
                upper_bound_str = bounds_match.group(2)
                lower_bound = sp.pi if lower_bound_str.lower() == 'pi' else float(lower_bound_str)
                upper_bound = sp.pi if upper_bound_str.lower() == 'pi' else float(upper_bound_str)

                indef = sp.integrate(parsed, var)
                def_val = sp.integrate(parsed, (var, lower_bound, upper_bound))

                steps = [
                    f"Integrand: `f({var}) = {parsed}`",
                    f"Limits of Integration: Lower limit `a = {lower_bound}`, Upper limit `b = {upper_bound}`",
                    f"Indefinite Integral Antiderivative: `F({var}) = {indef}`",
                    f"Fundamental Theorem of Calculus: `∫[a to b] f({var})d{var} = F(b) - F(a)`",
                    f"`F({upper_bound}) - F({lower_bound}) = **{def_val}**`",
                ]
                answer = str(def_val)
                title = f"Definite Integral from {lower_bound} to {upper_bound}"
                formula = "∫[a to b] f(x)dx = F(b) - F(a)"
            else:
                # Indefinite integral
                indef = sp.integrate(parsed, var)
                steps = [
                    f"Integrand: `f({var}) = {parsed}`",
                    f"Apply integration formulas (Power rule of integration, standard trig & exponential integrals):",
                    f"**∫ f({var}) d{var} = `{indef} + C`** (where C is the constant of integration)",
                ]
                answer = f"{indef} + C"
                title = f"Indefinite Integral with respect to {var}"
                formula = "∫ xⁿ dx = (xⁿ⁺¹)/(n + 1) + C  (for n ≠ -1)"

            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="calculus",
                concept_id="math.calculus.integration",
                intent=QuestionIntent.INTEGRATE,
                original_question=query,
                normalized_expression=expr_str,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )
        except Exception:
            return None

    def solve_limit(self, query: str) -> Optional[SubjectSolveResult]:
        """Calculates limits: lim x->a f(x)."""
        # Match pattern: limit of <expr> as x -> <a> or lim x->a <expr>
        lim_match = re.search(r'\b(?:limit\s+of|lim)\s+(.+?)\s+(?:as\s+)?([a-zA-Z])\s*(?:->|approaches|to)\s*([-+]?\d*\.?\d+|oo|infinity|0)', query, re.IGNORECASE)
        if not lim_match:
            return None

        expr_str = lim_match.group(1).strip()
        var_str = lim_match.group(2).strip()
        point_str = lim_match.group(3).strip()

        try:
            parsed = math_parser.parse(expr_str)
            var = sp.Symbol(var_str)
            point = sp.oo if point_str in ('oo', 'infinity') else float(point_str) if '.' in point_str else int(point_str)

            limit_val = sp.limit(parsed, var, point)

            steps = [
                f"Given Function: `f({var}) = {parsed}`",
                f"Variable approaches: `{var} ⟶ {point}`",
                f"Evaluate limiting behavior (checking indeterminate forms like 0/0 or ∞/∞ and applying L'Hôpital's rule where necessary).",
                f"**Limit = `{limit_val}`**",
            ]
            answer = str(limit_val)
            title = f"Limit as {var} ⟶ {point}"
            formula = "lim(x→a) f(x)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="calculus",
                concept_id="math.calculus.limits",
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


# Global instance
calculus_engine = CalculusEngine()
