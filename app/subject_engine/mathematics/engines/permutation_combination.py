"""
Permutations & Combinations Engine
==================================

PURPOSE:
    Solves discrete counting, permutations, combinations, and factorials:
    - Factorials (n!)
    - Permutations (ⁿPᵣ = n! / (n - r)!)
    - Combinations (ⁿCᵣ = n! / (r!(n - r)!))
    - Circular Permutations ((n - 1)!)
"""

import math
import re
from typing import Optional

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.validators import validate_integer_bounds


class PermutationCombinationEngine:
    """Specialized engine for Factorials, Permutations and Combinations."""

    def solve_combinatorics(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves queries like '5!', '7P3', '10C3', 'permutations of 5 items taken 3 at a time', 'combinations of 10 items taking 4'.
        """
        lower_q = query.lower()

        # 1. Factorial check: e.g. "5!" or "factorial of 6"
        fact_match = re.search(r'(\d+)\s*!|\bfactorial\s+(?:of\s+)?(\d+)', lower_q)
        if fact_match:
            n_str = fact_match.group(1) or fact_match.group(2)
            n = int(n_str)
            validate_integer_bounds(n, max_val=100)
            fact_val = math.factorial(n)
            steps = [
                f"Factorial Definition: `n! = n × (n - 1) × (n - 2) × ... × 1`",
                f"Calculation: `{n}! = {' × '.join(str(i) for i in range(n, 0, -1)) if n <= 8 else f'{n} × {n-1} × ... × 1'} = **{fact_val}**`",
            ]
            answer = str(fact_val)
            title = f"Factorial Calculation ({n}!)"
            formula = "n! = n × (n - 1) × ... × 1"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="combinatorics",
                concept_id="math.combinatorics",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        # 2. nPr pattern (e.g. 7P3, 7 P 3, permutations of 7 taken 3)
        npr_match = re.search(r'(\d+)\s*P\s*(\d+)|\bpermutations?\s+of\s+(\d+)\s+(?:items\s+)?taken\s+(\d+)', query, re.IGNORECASE)
        if npr_match:
            n = int(npr_match.group(1) or npr_match.group(3))
            r = int(npr_match.group(2) or npr_match.group(4))
            if r > n or n < 0 or r < 0:
                return None
            validate_integer_bounds(n, max_val=100)

            npr_val = math.perm(n, r)
            steps = [
                f"Permutation: Number of ways to arrange `{r}` items chosen from `{n}` distinct items.",
                f"Formula: `ⁿPᵣ = n! / (n - r)!`",
                f"`^{n}P_{r} = {n}! / ({n} - {r})! = {n}! / {n - r}! = **{npr_val}**`",
            ]
            answer = str(npr_val)
            title = f"Permutation: ^{n}P_{r}"
            formula = "ⁿPᵣ = n! / (n - r)!"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="combinatorics",
                concept_id="math.combinatorics",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        # 3. nCr pattern (e.g. 10C3, 10 C 3, combinations of 10 items taking 3)
        ncr_match = re.search(r'(\d+)\s*C\s*(\d+)|\bcombinations?\s+of\s+(\d+)\s+(?:items\s+)?(?:taking|chosen)\s+(\d+)', query, re.IGNORECASE)
        if ncr_match:
            n = int(ncr_match.group(1) or ncr_match.group(3))
            r = int(ncr_match.group(2) or ncr_match.group(4))
            if r > n or n < 0 or r < 0:
                return None
            validate_integer_bounds(n, max_val=100)

            ncr_val = math.comb(n, r)
            steps = [
                f"Combination: Number of ways to select `{r}` items from `{n}` distinct items (order does not matter).",
                f"Formula: `ⁿCᵣ = n! / (r! × (n - r)!)`",
                f"`^{n}C_{r} = {n}! / ({r}! × ({n} - {r})!) = {n}! / ({r}! × {n - r}!) = **{ncr_val}**`",
            ]
            answer = str(ncr_val)
            title = f"Combination: ^{n}C_{r}"
            formula = "ⁿCᵣ = n! / [r!(n - r)!]"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="combinatorics",
                concept_id="math.combinatorics",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        return None


# Global instance
perm_comb_engine = PermutationCombinationEngine()
