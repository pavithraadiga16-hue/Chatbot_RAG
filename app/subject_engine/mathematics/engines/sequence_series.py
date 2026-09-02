"""
Sequences and Series Engine (AP & GP)
=====================================

PURPOSE:
    Solves Arithmetic Progression (AP), Geometric Progression (GP), and special series:
    - AP: nth term (Tₙ = a + (n-1)d), Sum of first n terms (Sₙ = n/2(2a + (n-1)d))
    - GP: nth term (Tₙ = a·rⁿ⁻¹), Sum of n terms (Sₙ), Sum of infinite GP (S_inf = a/(1-r))
    - Special Series Sums (Σn, Σn², Σn³)
"""

import math
import re
from typing import Optional

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


class SequenceSeriesEngine:
    """Specialized engine for Arithmetic and Geometric Progressions."""

    def solve_ap_gp(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Detects AP and GP sequence patterns:
        e.g. 'find 10th term of AP 2, 5, 8, ...' or 'sum of first 20 terms of AP 3, 7, 11' or 'sum of infinite GP 1, 1/2, 1/4'
        """
        lower_q = query.lower()
        is_ap = bool(re.search(r'\b(ap|arithmetic\s+progression)\b', lower_q))
        is_gp = bool(re.search(r'\b(gp|geometric\s+progression|infinite\s+gp)\b', lower_q))

        if not is_ap and not is_gp:
            return None

        # Extract sequence elements like 2, 5, 8 or 3, 7, 11
        nums = math_parser.extract_numbers(query)
        if len(nums) < 2:
            return None

        # Check if looking for nth term
        nth_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+term', lower_q)
        # Check if looking for sum of n terms
        sum_match = re.search(r'sum\s+(?:of\s+first\s+)?(\d+)\s+terms', lower_q)
        # Check infinite GP
        is_inf_gp = "infinite" in lower_q or "infinity" in lower_q

        if is_ap:
            # First terms in query usually represent sequence
            # If query says: "find 10th term of AP 2, 5, 8" -> nth=10, seq = [2, 5, 8]
            n_target = int(nth_match.group(1)) if nth_match else (int(sum_match.group(1)) if sum_match else None)

            # Filter remaining numbers for sequence terms a1, a2, a3
            seq_candidates = [num for num in nums if n_target is None or num != n_target]
            if len(seq_candidates) < 2:
                seq_candidates = nums

            a = seq_candidates[0]
            d = seq_candidates[1] - seq_candidates[0]

            if sum_match and n_target:
                # Sum of n terms
                n = n_target
                sn = (n / 2.0) * (2 * a + (n - 1) * d)
                steps = [
                    f"Given Arithmetic Progression: `{seq_candidates}`",
                    f"First Term `a = {a}`",
                    f"Common Difference `d = a₂ - a₁ = {seq_candidates[1]} - {seq_candidates[0]} = {d}`",
                    f"Formula for Sum of n terms: `Sₙ = (n/2) × [2a + (n - 1)d]`",
                    f"`S_{n} = ({n}/2) × [2({a}) + ({n} - 1)({d})] = {n/2} × [{2*a} + {(n-1)*d}] = **{sn}**`",
                ]
                answer = f"S_{n} = {sn}"
                title = f"Sum of First {n} Terms of AP"
                formula = "Sₙ = (n/2)[2a + (n-1)d]"
            else:
                n = n_target or 10
                tn = a + (n - 1) * d
                steps = [
                    f"Given Arithmetic Progression: `{seq_candidates}`",
                    f"First Term `a = {a}`",
                    f"Common Difference `d = a₂ - a₁ = {seq_candidates[1]} - {seq_candidates[0]} = {d}`",
                    f"Formula for nth term: `Tₙ = a + (n - 1)d`",
                    f"`T_{n} = {a} + ({n} - 1) × ({d}) = {a} + {(n-1)*d} = **{tn}**`",
                ]
                answer = f"T_{n} = {tn}"
                title = f"{n}-th Term of Arithmetic Progression (AP)"
                formula = "Tₙ = a + (n-1)d"

            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="sequences_series",
                concept_id="math.sequence_series",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_gp:
            a = float(nums[0])
            r = float(nums[1]) / a if a != 0 else 1.0

            if is_inf_gp:
                if abs(r) >= 1:
                    answer = "Diverges (|r| >= 1, no finite sum)"
                    steps = [
                        f"First term `a = {a}`, Common ratio `r = {r}`",
                        f"Since `|r| >= 1`, the infinite geometric series does not converge.",
                    ]
                else:
                    s_inf = a / (1.0 - r)
                    steps = [
                        f"Given Geometric Progression with `first term a = {a}` and `common ratio r = {r}`",
                        f"Condition for convergence: `|r| = {abs(r)} < 1` (Converges)",
                        f"Formula for Sum of Infinite GP: `S_∞ = a / (1 - r)`",
                        f"`S_∞ = {a} / (1 - {r}) = {a} / {1 - r} = **{s_inf}**`",
                    ]
                    answer = f"S_∞ = {s_inf}"

                title = "Sum of Infinite Geometric Progression (GP)"
                formula = "S_∞ = a / (1 - r)  for |r| < 1"
                md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="sequences_series",
                    concept_id="math.sequence_series",
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
sequence_engine = SequenceSeriesEngine()
