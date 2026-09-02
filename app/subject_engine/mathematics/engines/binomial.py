"""
Binomial Theorem Engine
=======================

PURPOSE:
    Solves Binomial Theorem expansions, general term, middle term, and Pascal's Triangle:
    - (a + b)ⁿ = Σ ⁿCᵣ a^(n-r) bʳ
    - General Term T_(r+1) = ⁿCᵣ a^(n-r) bʳ
    - Middle Term of Binomial Expansion
"""

import math
import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.validators import validate_integer_bounds


class BinomialEngine:
    """Specialized engine for Binomial Theorem."""

    def solve_binomial_expansion(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Expands binomial expressions like '(x + y)^4', '(2x - 3)^3', 'expand (a + b)^5'.
        """
        # Match pattern (a + b)^n
        bin_match = re.search(r'\((.+?)\)\s*(?:\^|\*\*)\s*(\d+)', query)
        if not bin_match:
            return None

        inner_str = bin_match.group(1).strip()
        n = int(bin_match.group(2))
        validate_integer_bounds(n, max_val=20)

        try:
            parsed_inner = math_parser.parse(inner_str)
            expr = parsed_inner**n
            expanded = sp.expand(expr)

            # Generate individual terms using Binomial Theorem formula
            steps = [
                f"Given Binomial Expression: `({parsed_inner})^{n}` (Power n = {n})",
                f"Binomial Theorem Formula: `(a + b)ⁿ = Σ[r=0 to n] ⁿCᵣ aⁿ⁻ʳ bʳ`",
                f"Number of terms in expansion = `n + 1 = {n + 1}`",
                f"**Full Expanded Form:** **`{expanded}`**",
            ]

            answer = str(expanded)
            title = f"Binomial Expansion for Power {n}"
            formula = "(a + b)ⁿ = Σ ⁿCᵣ a^(n-r) bʳ"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="combinatorics",
                concept_id="math.combinatorics",
                intent=QuestionIntent.EXPAND,
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
binomial_engine = BinomialEngine()
