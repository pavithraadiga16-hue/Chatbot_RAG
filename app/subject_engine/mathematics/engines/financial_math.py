"""
Financial & Commercial Mathematics Engine
=========================================

PURPOSE:
    Solves Commercial Mathematics and Word Problem rates:
    - Percentage of values & Percentage Increase/Decrease
    - Profit, Loss & Discount (CP, SP, MP, Profit %, Loss %)
    - Simple Interest (SI) and Compound Interest (CI)
    - Time, Speed & Distance (Average speed, relative speed)
    - Time & Work calculations
"""

import math
import re
from typing import Optional

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


class FinancialMathEngine:
    """Specialized engine for Commercial Math, Interest, and Percentages."""

    def solve_percentage(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves percentage queries:
        e.g. '20% of 500', '25 percent of 1200', 'percentage increase from 40 to 50'
        """
        lower_q = query.lower()

        # Match 'X% of Y' or 'X percent of Y'
        pct_of_match = re.search(r'(\d*\.?\d+)\s*(?:%|percent)\s+(?:of\s+)?(\d*\.?\d+)', lower_q)
        if pct_of_match:
            pct = float(pct_of_match.group(1))
            val = float(pct_of_match.group(2))
            res = (pct / 100.0) * val

            steps = [
                f"Calculate `{pct}%` of `{val}`",
                f"Formula: `Result = (Percentage / 100) × Value`",
                f"`Result = ({pct} / 100) × {val} = {pct/100} × {val} = **{res:.4g}**`",
            ]
            answer = f"{res:.4g}"
            title = f"{pct}% of {val}"
            formula = "(P / 100) × Value"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="commercial_math",
                concept_id="math.commercial.percentage",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        # Match 'percentage increase/decrease from X to Y'
        pct_change_match = re.search(r'percentage\s+(?:increase|decrease|change)\s+from\s+(\d*\.?\d+)\s+to\s+(\d*\.?\d+)', lower_q)
        if pct_change_match:
            old_val = float(pct_change_match.group(1))
            new_val = float(pct_change_match.group(2))
            if old_val == 0:
                return None
            diff = new_val - old_val
            pct_change = (diff / old_val) * 100.0
            change_type = "Increase" if diff >= 0 else "Decrease"

            steps = [
                f"Initial Value = `{old_val}`, Final Value = `{new_val}`",
                f"Change in Value = `Final - Initial = {new_val} - {old_val} = {diff}`",
                f"Percentage Change Formula: `(Change / Initial Value) × 100%`",
                f"`({diff} / {old_val}) × 100% = **{abs(pct_change):.4g}% {change_type}**`",
            ]
            answer = f"{abs(pct_change):.4g}% {change_type}"
            title = f"Percentage {change_type}"
            formula = "((Final - Initial) / Initial) × 100%"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="commercial_math",
                concept_id="math.commercial.percentage",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        return None

    def solve_interest(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves Simple and Compound Interest calculations:
        e.g. 'simple interest on principal 10000 rate 5% for 3 years'
        """
        lower_q = query.lower()
        is_si = bool(re.search(r'\b(simple\s+interest)\b', lower_q)) or bool(re.search(r'\bsi\b', lower_q))
        is_ci = bool(re.search(r'\b(compound\s+interest)\b', lower_q)) or bool(re.search(r'\bci\b', lower_q))

        if not is_si and not is_ci:
            return None


        # Extract P, R, T
        p_match = re.search(r'\b(?:principal|sum|p)\s*(?:of|=|is)?\s*(\d*\.?\d+)', lower_q)
        r_match = re.search(r'\b(?:rate|r)\s*(?:of|=|is)?\s*(\d*\.?\d+)', lower_q)
        t_match = re.search(r'\b(?:time|years|t)\s*(?:of|=|is)?\s*(\d*\.?\d+)', lower_q)

        nums = math_parser.extract_numbers(query)
        if not p_match or not r_match or not t_match:
            if len(nums) >= 3:
                P, R, T = float(nums[0]), float(nums[1]), float(nums[2])
            else:
                return None
        else:
            P = float(p_match.group(1))
            R = float(r_match.group(1))
            T = float(t_match.group(1))

        if is_si or not is_ci:
            si_val = (P * R * T) / 100.0
            total_amount = P + si_val
            steps = [
                f"Given: Principal `P = {P}`, Rate of Interest `R = {R}% per annum`, Time `T = {T} years`",
                f"Simple Interest Formula: `SI = (P × R × T) / 100`",
                f"`SI = ({P} × {R} × {T}) / 100 = **₹{si_val:.2f}**`",
                f"Total Maturity Amount: `A = P + SI = {P} + {si_val:.2f} = **₹{total_amount:.2f}**`",
            ]
            answer = f"Simple Interest = ₹{si_val:.2f}, Total Amount = ₹{total_amount:.2f}"
            title = "Simple Interest (SI)"
            formula = "SI = (P × R × T) / 100"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="commercial_math",
                concept_id="math.commercial.interest",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_ci:
            amount = P * ((1.0 + (R / 100.0)) ** T)
            ci_val = amount - P
            steps = [
                f"Given: Principal `P = {P}`, Annual Rate `R = {R}%`, Time Period `T = {T} years`",
                f"Compound Interest Formula: `Amount A = P × (1 + R/100)ᵀ`",
                f"`A = {P} × (1 + {R}/100)^{T} = {P} × ({1 + R/100:.4f})^{T} = **₹{amount:.2f}**`",
                f"`Compound Interest CI = A - P = {amount:.2f} - {P} = **₹{ci_val:.2f}**`",
            ]
            answer = f"Compound Interest = ₹{ci_val:.2f}, Total Amount = ₹{amount:.2f}"
            title = "Compound Interest (CI)"
            formula = "A = P(1 + R/100)ᵀ,  CI = A - P"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="commercial_math",
                concept_id="math.commercial.interest",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        return None

    def solve_profit_loss(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves Profit and Loss calculations:
        e.g. 'CP = 400 and SP = 500 find profit percentage'
        """
        lower_q = query.lower()
        if not re.search(r'\b(profit|loss|cost\s+price|selling\s+price|cp|sp|discount)\b', lower_q):
            return None

        cp_match = re.search(r'\b(?:cp|cost\s+price)\s*(?:of|=|is)?\s*(\d*\.?\d+)', lower_q)
        sp_match = re.search(r'\b(?:sp|selling\s+price)\s*(?:of|=|is)?\s*(\d*\.?\d+)', lower_q)

        if cp_match and sp_match:
            cp = float(cp_match.group(1))
            sp_val = float(sp_match.group(1))
            if cp <= 0:
                return None

            diff = sp_val - cp
            if diff >= 0:
                pct = (diff / cp) * 100.0
                status = "Profit"
            else:
                pct = (abs(diff) / cp) * 100.0
                status = "Loss"

            steps = [
                f"Cost Price (CP) = `₹{cp}`, Selling Price (SP) = `₹{sp_val}`",
                f"`SP {'≥' if diff >= 0 else '<'} CP` ⟹ There is a **{status}**.",
                f"{status} Amount = `|SP - CP| = ₹{abs(diff):.2f}`",
                f"{status} Percentage Formula: `({status} / CP) × 100%`",
                f"`({abs(diff):.2f} / {cp}) × 100% = **{pct:.2f}% {status}**`",
            ]
            answer = f"{status} = ₹{abs(diff):.2f} ({pct:.2f}%)"
            title = f"Profit & Loss ({status})"
            formula = "Profit % = (Profit/CP) × 100%,  Loss % = (Loss/CP) × 100%"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="commercial_math",
                concept_id="math.commercial.percentage",
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
financial_math_engine = FinancialMathEngine()
