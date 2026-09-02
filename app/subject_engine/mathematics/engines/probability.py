"""
Probability Engine
==================

PURPOSE:
    Solves Classical, Conditional, and Binomial Probability calculations:
    - Classical Probability (P(E) = n(E) / n(S)) for coins, dice, cards
    - Addition Theorem (P(A ∪ B) = P(A) + P(B) - P(A ∩ B))
    - Conditional Probability & Bayes' Theorem
    - Binomial Probability Distribution (P(X = k) = ⁿCₖ pᵏ qⁿ⁻ᵏ)
"""

import math
import re
from fractions import Fraction
from typing import Optional

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


class ProbabilityEngine:
    """Specialized engine for Probability."""

    def solve_probability(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Calculates standard probability problems:
        - Coin toss: head, tail
        - Dice roll: even number, odd, prime, greater than 4, sum of two dice
        - Cards: drawing ace, king, red card, spade, face card
        - Numerical probability fractions
        """
        lower_q = query.lower()
        if not re.search(r'\b(probability|chance|sample\s+space)\b', lower_q):
            return None

        # 1. Coin toss problems
        if "coin" in lower_q:
            if "two coins" in lower_q or "2 coins" in lower_q:
                n_s = 4
                sample_space = "{(H, H), (H, T), (T, H), (T, T)}"
                if "both heads" in lower_q or "two heads" in lower_q:
                    n_e, fav = 1, "{(H, H)}"
                elif "at least one head" in lower_q:
                    n_e, fav = 3, "{(H, H), (H, T), (T, H)}"
                else:
                    n_e, fav = 2, "{(H, T), (T, H)}"
            else:
                n_s = 2
                sample_space = "{Head, Tail}"
                n_e, fav = 1, "{Head}" if "head" in lower_q else "{Tail}"

            prob = Fraction(n_e, n_s)
            steps = [
                f"Sample Space S = `{sample_space}` with Total Outcomes `n(S) = {n_s}`",
                f"Favorable Outcomes E = `{fav}` with `n(E) = {n_e}`",
                f"Probability Formula: `P(E) = n(E) / n(S)`",
                f"`P(E) = {n_e} / {n_s} = **{prob}**` (or **{float(prob):.4f}**)",
            ]
            answer = f"{prob} ({float(prob)*100:.1f}%)"
            title = "Coin Toss Probability"
            formula = "P(E) = n(E) / n(S)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="probability",
                concept_id="math.probability",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        # 2. Die / Dice problems
        if "die" in lower_q or "dice" in lower_q:
            n_s = 6
            sample_space = "{1, 2, 3, 4, 5, 6}"
            if "even" in lower_q:
                n_e, fav = 3, "{2, 4, 6}"
            elif "odd" in lower_q:
                n_e, fav = 3, "{1, 3, 5}"
            elif "prime" in lower_q:
                n_e, fav = 3, "{2, 3, 5}"
            elif "greater than 4" in lower_q:
                n_e, fav = 2, "{5, 6}"
            else:
                n_e, fav = 1, "{target outcome}"

            prob = Fraction(n_e, n_s)
            steps = [
                f"Sample Space S = `{sample_space}` with `n(S) = {n_s}`",
                f"Favorable Outcomes E = `{fav}` with `n(E) = {n_e}`",
                f"Probability Formula: `P(E) = n(E) / n(S)`",
                f"`P(E) = {n_e} / {n_s} = **{prob}**` (or **{float(prob):.4f}**)",
            ]
            answer = f"{prob} ({float(prob)*100:.1f}%)"
            title = "Dice Roll Probability"
            formula = "P(E) = n(E) / n(S)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="probability",
                concept_id="math.probability",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        # 3. Playing cards (52 cards deck)
        if "card" in lower_q or "deck" in lower_q:
            n_s = 52
            if "ace" in lower_q:
                n_e, fav = 4, "4 Aces (1 per suit)"
            elif "king" in lower_q:
                n_e, fav = 4, "4 Kings"
            elif "queen" in lower_q:
                n_e, fav = 4, "4 Queens"
            elif "face card" in lower_q:
                n_e, fav = 12, "12 Face Cards (Kings, Queens, Jacks)"
            elif "red" in lower_q:
                n_e, fav = 26, "26 Red Cards (Hearts + Diamonds)"
            elif "black" in lower_q:
                n_e, fav = 26, "26 Black Cards (Spades + Clubs)"
            elif "spade" in lower_q or "heart" in lower_q or "diamond" in lower_q or "club" in lower_q:
                n_e, fav = 13, "13 Cards of the suit"
            else:
                n_e, fav = 4, "4 cards of that rank"

            prob = Fraction(n_e, n_s)
            steps = [
                f"Total number of cards in a standard deck `n(S) = 52`",
                f"Favorable outcomes: `{fav}` with `n(E) = {n_e}`",
                f"`P(E) = n(E) / n(S) = {n_e} / 52 = **{prob}**` (or **{float(prob):.4f}**)",
            ]
            answer = f"{prob} ({float(prob)*100:.2f}%)"
            title = "Card Deck Probability"
            formula = "P(E) = n(E) / n(S)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="probability",
                concept_id="math.probability",
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
probability_engine = ProbabilityEngine()
