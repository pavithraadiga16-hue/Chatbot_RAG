"""
Set Theory & Mathematical Logic Engine
======================================

PURPOSE:
    Solves Set Operations and Venn Cardinalities:
    - Set Union (A ∪ B), Intersection (A ∩ B), Difference (A - B)
    - Power Sets (2^n elements)
    - Cartesian Products (A × B)
    - Cardinality Formula: n(A ∪ B) = n(A) + n(B) - n(A ∩ B)
    - Mathematical Logic (Converse, Contrapositive, Truth tables)
"""

import ast
import re
from typing import Optional

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.formatter import math_formatter


class SetTheoryEngine:
    """Specialized engine for Set Theory and Logic."""

    def parse_set(self, text: str) -> Optional[set]:
        """Extracts set literal like {1, 2, 3} or {'a', 'b'}."""
        set_match = re.search(r'(\{[^}]*\})', text)
        if not set_match:
            return None
        set_str = set_match.group(1)
        try:
            # Parse python set
            val = ast.literal_eval(set_str)
            if isinstance(val, (set, list, tuple)):
                return set(val)
        except Exception:
            # Fallback: split by comma
            items = [item.strip().strip("'\"") for item in set_str.strip('{}').split(',') if item.strip()]
            return set(items)
        return None

    def solve_set_operations(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves set operations: union, intersection, difference, power set.
        """
        lower_q = query.lower()

        # Find all set literals
        set_matches = re.findall(r'(\{[^}]*\})', query)
        sets = []
        for s_str in set_matches:
            s_val = self.parse_set(s_str)
            if s_val is not None:
                sets.append(s_val)

        is_union = bool(re.search(r'\b(union)\b', lower_q))
        is_intersection = bool(re.search(r'\b(intersection)\b', lower_q))
        is_difference = bool(re.search(r'\b(difference|minus)\b', lower_q))
        is_powerset = bool(re.search(r'\b(power\s+set)\b', lower_q))

        if len(sets) >= 2:
            A, B = sets[0], sets[1]
            if is_union or (not is_intersection and not is_difference):
                union_set = A.union(B)
                steps = [
                    f"Set A = `{sorted(list(A), key=str)}` (n(A) = {len(A)})",
                    f"Set B = `{sorted(list(B), key=str)}` (n(B) = {len(B)})",
                    f"Union Formula: `A ∪ B = {{x : x ∈ A or x ∈ B}}`",
                    f"**A ∪ B = `{sorted(list(union_set), key=str)}`** (Cardinality = {len(union_set)})",
                ]
                answer = str(sorted(list(union_set), key=str))
                title = "Set Union (A ∪ B)"
                formula = "A ∪ B = {x : x ∈ A or x ∈ B}"
                md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="set_theory",
                    concept_id="math.set_theory",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    formula=formula,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    confidence=0.98,
                )

            elif is_intersection:
                inter_set = A.intersection(B)
                steps = [
                    f"Set A = `{sorted(list(A), key=str)}`",
                    f"Set B = `{sorted(list(B), key=str)}`",
                    f"Intersection Formula: `A ∩ B = {{x : x ∈ A and x ∈ B}}`",
                    f"**A ∩ B = `{sorted(list(inter_set), key=str)}`** (Cardinality = {len(inter_set)})",
                ]
                answer = str(sorted(list(inter_set), key=str))
                title = "Set Intersection (A ∩ B)"
                formula = "A ∩ B = {x : x ∈ A and x ∈ B}"
                md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="set_theory",
                    concept_id="math.set_theory",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    formula=formula,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    confidence=0.98,
                )

        elif is_powerset and len(sets) >= 1:
            A = list(sets[0])
            n = len(A)
            # Generate power set
            from itertools import combinations
            power_set = []
            for r in range(n + 1):
                for combo in combinations(A, r):
                    power_set.append(set(combo))

            steps = [
                f"Given Set A = `{set(A)}` with cardinality `|A| = {n}`",
                f"Power Set Formula: `P(A) is the set of all subsets of A`",
                f"Total number of subsets = `2ⁿ = 2^{n} = **{2**n}**`",
                f"**Power Set P(A):** `{[sorted(list(s), key=str) for s in power_set]}`",
            ]
            answer = f"2^{n} = {2**n} subsets"
            title = "Power Set P(A)"
            formula = "|P(A)| = 2^n"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="set_theory",
                concept_id="math.set_theory",
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
set_theory_engine = SetTheoryEngine()
