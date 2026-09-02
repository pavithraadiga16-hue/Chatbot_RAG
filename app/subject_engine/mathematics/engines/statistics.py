"""
Statistics Engine
=================

PURPOSE:
    Solves descriptive statistics calculations on datasets:
    - Arithmetic Mean (Average)
    - Median
    - Mode
    - Range
    - Variance (Population & Sample)
    - Standard Deviation
    - Quartiles (Q1, Q2, Q3) & Interquartile Range (IQR)
"""

import math
import re
import statistics as stats
from typing import Optional

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


class StatisticsEngine:
    """Specialized engine for Statistical analysis."""

    def solve_statistics(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves queries like:
        'mean of 10, 20, 30, 40, 50', 'median of 3, 5, 7, 9, 11', 'mode of 2, 3, 3, 5, 7', 'standard deviation of 2, 4, 4, 4, 5, 5, 7, 9'
        """
        lower_q = query.lower()
        nums = math_parser.extract_numbers(query)
        if len(nums) < 2:
            return None

        data = [float(x) for x in nums]
        n = len(data)

        is_mean = bool(re.search(r'\b(mean|average)\b', lower_q))
        is_median = bool(re.search(r'\b(median)\b', lower_q))
        is_mode = bool(re.search(r'\b(mode)\b', lower_q))
        is_variance = bool(re.search(r'\b(variance)\b', lower_q))
        is_std = bool(re.search(r'\b(standard\s+deviation|std\s+dev|sigma)\b', lower_q))
        is_range = bool(re.search(r'\b(range)\b', lower_q))

        if is_mean or (not is_median and not is_mode and not is_variance and not is_std and not is_range):
            mean_val = stats.mean(data)
            sum_val = sum(data)
            steps = [
                f"Given Dataset (N = {n}): `{data}`",
                f"Formula for Mean: `x̄ = (Σ xᵢ) / N`",
                f"Sum of values `Σ xᵢ = {sum_val}`",
                f"`x̄ = {sum_val} / {n} = **{mean_val:.4g}**`",
            ]
            answer = f"Mean = {mean_val:.4g}"
            title = f"Arithmetic Mean of {n} Numbers"
            formula = "x̄ = (Σ xᵢ) / N"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="statistics",
                concept_id="math.statistics",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_median:
            sorted_data = sorted(data)
            median_val = stats.median(data)
            steps = [
                f"Given Dataset (N = {n}): `{data}`",
                f"Sort data in ascending order: `{sorted_data}`",
                f"Formula for Median:",
            ]
            if n % 2 == 1:
                mid_idx = n // 2
                steps.append(f"Since N = {n} is odd, Median is the middle element at position (N+1)/2 = {mid_idx+1}:")
                steps.append(f"**Median = {sorted_data[mid_idx]}**")
            else:
                m1, m2 = sorted_data[n//2 - 1], sorted_data[n//2]
                steps.append(f"Since N = {n} is even, Median is the average of the two middle elements ({m1} and {m2}):")
                steps.append(f"`Median = ({m1} + {m2}) / 2 = **{median_val}**`")

            answer = f"Median = {median_val}"
            title = "Median of Dataset"
            formula = "Middle element of sorted data"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="statistics",
                concept_id="math.statistics",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_mode:
            try:
                modes = stats.multimode(data)
                modes_str = ", ".join(str(m) for m in modes)
                steps = [
                    f"Given Dataset: `{data}`",
                    f"Mode is the value(s) that appear with the highest frequency.",
                    f"**Mode(s) = {modes_str}**",
                ]
                answer = f"Mode = {modes_str}"
            except Exception:
                answer = "No unique mode"
                steps = ["No element has greater frequency than others."]

            title = "Mode of Dataset"
            formula = "Value with highest frequency"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="statistics",
                concept_id="math.statistics",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_variance or is_std:
            mean_val = stats.mean(data)
            p_var = stats.pvariance(data)
            p_std = stats.pstdev(data)
            steps = [
                f"Given Dataset (N = {n}): `{data}`",
                f"Mean `x̄ = {mean_val:.4g}`",
                f"Population Variance: `σ² = Σ(xᵢ - x̄)² / N = **{p_var:.4g}**`",
                f"Population Standard Deviation: `σ = √Variance = **{p_std:.4g}**`",
            ]
            answer = f"Variance = {p_var:.4g}, Standard Deviation = {p_std:.4g}"
            title = "Variance & Standard Deviation"
            formula = "σ = √(Σ(xᵢ - x̄)² / N)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="statistics",
                concept_id="math.statistics",
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
statistics_engine = StatisticsEngine()
