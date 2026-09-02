"""
Algebra & Expressions Engine
============================

PURPOSE:
    Handles algebraic expressions:
    - Simplification & Combining Like Terms
    - Polynomial Expansions
    - Factorization with Algebraic Identities
    - Substitution & Variable Evaluation
"""

import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.rules import ALGEBRAIC_IDENTITIES


class AlgebraEngine:
    """Specialized engine for algebraic operations."""

    def simplify_expression(self, expr_str: str, query: str) -> Optional[SubjectSolveResult]:
        """Simplifies algebraic expressions."""
        try:
            parsed = math_parser.parse(expr_str)
            simplified = sp.simplify(parsed)
            expanded = sp.expand(parsed)

            is_expand = bool(re.search(r'\b(expand|expansion)\b', query, re.IGNORECASE))
            result_expr = expanded if is_expand else simplified

            steps = [
                f"Given algebraic expression: `{expr_str}`",
                f"Combine like terms and apply algebraic exponent rules.",
            ]
            if is_expand:
                steps.append(f"Expand all terms: **{expanded}**")
            else:
                steps.append(f"Simplified form: **{simplified}**")

            answer = str(result_expr)
            title = "Algebraic Expansion" if is_expand else "Algebraic Simplification"
            md = math_formatter.format_solution(query, answer, steps, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="algebra",
                concept_id="math.algebra.simplification",
                intent=QuestionIntent.EXPAND if is_expand else QuestionIntent.SIMPLIFY,
                original_question=query,
                normalized_expression=expr_str,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.96,
            )
        except Exception:
            return None

    def factor_expression(self, expr_str: str, query: str) -> Optional[SubjectSolveResult]:
        """Factors polynomials and expressions using algebraic identities."""
        try:
            parsed = math_parser.parse(expr_str)
            factored = sp.factor(parsed)

            steps = [
                f"Given expression to factorize: `{expr_str}`",
                f"Look for common factors and recognizable algebraic identities (a² - b², (a ± b)², a³ ± b³).",
                f"Factored form: **{factored}**",
            ]
            answer = str(factored)
            title = "Polynomial Factorization"
            md = math_formatter.format_solution(query, answer, steps, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="algebra",
                concept_id="math.algebra.simplification",
                intent=QuestionIntent.FACTOR,
                original_question=query,
                normalized_expression=expr_str,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.96,
            )
        except Exception:
            return None

    def evaluate_substitution(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Evaluates algebraic expressions with variable substitution:
        e.g., 'if x = 3 and y = 4 find value of 2x^2 + y'
        """
        # Match pattern: if x = 3 ... expression
        sub_pattern = r'(?:if|when|for)\s+([a-zA-Z])\s*=\s*([-+]?\d*\.?\d+)'
        matches = re.findall(sub_pattern, query, re.IGNORECASE)
        if not matches:
            return None

        # Build substitution dictionary
        subs_dict = {}
        for var, val in matches:
            sym = sp.Symbol(var)
            subs_dict[sym] = float(val) if '.' in val else int(val)

        # Extract the remaining expression to evaluate
        expr_part = re.sub(sub_pattern, '', query, flags=re.IGNORECASE)
        expr_clean = re.sub(r'\b(find|calculate|evaluate|the\s+value\s+of|value\s+of|value\s+is|value)\b', '', expr_part, flags=re.IGNORECASE).strip()
        expr_norm = math_parser.parse(math_parser.__class__.__name__ and __import__("app.subject_engine.mathematics.normalizer", fromlist=["math_normalizer"]).math_normalizer.normalize(expr_clean))

        try:
            evaluated = expr_norm.subs(subs_dict)
            simplified = sp.simplify(evaluated)

            sub_steps_str = ", ".join(f"{var} = {val}" for var, val in matches)

            steps = [
                f"Given Expression: `{expr_clean}`",
                f"Substitute values: {sub_steps_str}",
                f"Result after substitution: **{simplified}**",
            ]
            answer = str(simplified)
            title = "Algebraic Substitution & Evaluation"
            md = math_formatter.format_solution(query, answer, steps, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="algebra",
                concept_id="math.algebra.simplification",
                intent=QuestionIntent.EVALUATE,
                original_question=query,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.95,
            )
        except Exception:
            return None


# Global instance
algebra_engine = AlgebraEngine()
