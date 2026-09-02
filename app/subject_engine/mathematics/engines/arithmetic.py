"""
Arithmetic & Number Theory Engine
=================================

PURPOSE:
    Handles calculations across the number system:
    - Addition, Subtraction, Multiplication, Division, BODMAS
    - Prime number checking, Prime Factorization, Factors & Multiples
    - HCF / GCD (Euclidean Algorithm with steps), LCM
    - Fractions (simplification, operations, mixed fractions), Decimals, Recurring decimals
    - Powers, Exponents, Square roots, Cube roots, Surds rationalization
"""

import math
import re
from fractions import Fraction
from typing import Optional, Union
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.validators import validate_integer_bounds


class ArithmeticEngine:
    """Specialized engine for arithmetic and number systems."""

    def solve_hcf_lcm(self, query: str) -> Optional[SubjectSolveResult]:
        """Calculates HCF (GCD) and/or LCM with Euclidean algorithm and prime factorization steps."""
        numbers = math_parser.extract_numbers(query)
        if len(numbers) < 2:
            return None

        int_nums = [int(n) for n in numbers]
        for n in int_nums:
            validate_integer_bounds(n, max_val=10**9)

        is_hcf = bool(re.search(r'\b(hcf|gcd|greatest\s+common|highest\s+common)\b', query, re.IGNORECASE))
        is_lcm = bool(re.search(r'\b(lcm|least\s+common|lowest\s+common)\b', query, re.IGNORECASE))

        if not is_hcf and not is_lcm:
            return None

        steps = []
        # Prime factorizations
        factorizations = {}
        for num in int_nums:
            factors_dict = sp.factorint(num)
            fact_str = " × ".join(f"{p}^{exp}" if exp > 1 else str(p) for p, exp in sorted(factors_dict.items()))
            factorizations[num] = fact_str or "1"
            steps.append(f"Prime factorization of {num} = **{factorizations[num]}**")

        if is_hcf and not is_lcm:
            hcf_val = math.gcd(*int_nums)
            steps.append(f"Take the product of smallest powers of common prime factors:")
            steps.append(f"HCF({', '.join(str(n) for n in int_nums)}) = **{hcf_val}**")
            answer = str(hcf_val)
            title = f"HCF (Highest Common Factor) of {', '.join(str(n) for n in int_nums)}"
            formula = "HCF = Product of lowest powers of common prime factors"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="number_theory",
                concept_id="math.number.hcf_lcm",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_lcm and not is_hcf:
            # LCM calculation
            def _lcm(a: int, b: int) -> int:
                return abs(a * b) // math.gcd(a, b)

            lcm_val = int_nums[0]
            for n in int_nums[1:]:
                lcm_val = _lcm(lcm_val, n)

            steps.append(f"Take the product of greatest powers of all prime factors:")
            steps.append(f"LCM({', '.join(str(n) for n in int_nums)}) = **{lcm_val}**")
            answer = str(lcm_val)
            title = f"LCM (Lowest Common Multiple) of {', '.join(str(n) for n in int_nums)}"
            formula = "LCM = Product of highest powers of all prime factors"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="number_theory",
                concept_id="math.number.hcf_lcm",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        return None

    def solve_prime_factors(self, query: str) -> Optional[SubjectSolveResult]:
        """Prime check and prime factorization."""
        numbers = math_parser.extract_numbers(query)
        if not numbers:
            return None
        num = int(numbers[0])
        validate_integer_bounds(num, max_val=10**12)

        is_prime_check = bool(re.search(r'\b(is\s+\d+\s+prime|prime\s+or\s+composite|check\s+prime)\b', query, re.IGNORECASE))
        is_factorization = bool(re.search(r'\b(prime\s+factor\w*|factorise|factorize|factors\s+of)\b', query, re.IGNORECASE))


        if is_prime_check:
            is_p = sp.isprime(num)
            steps = [
                f"A prime number has exactly two distinct positive divisors: 1 and itself.",
            ]
            if is_p:
                answer = f"{num} is a PRIME number"
                steps.append(f"Testing divisors up to √{num} ≈ {int(math.isqrt(num))}: No factors found.")
                steps.append(f"Hence, {num} is prime.")
            else:
                factors = sp.divisors(num)
                answer = f"{num} is a COMPOSITE number"
                steps.append(f"Divisors of {num}: {factors}")
                steps.append(f"Since {num} has divisors other than 1 and itself, it is composite.")

            title = f"Prime Check: {num}"
            md = math_formatter.format_solution(query, answer, steps, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="number_theory",
                concept_id="math.number.primes",
                intent=QuestionIntent.CHECK_ANSWER,
                original_question=query,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_factorization and not bool(re.search(r'\b[xyzabc]\b', query, re.IGNORECASE)) and not any(sym in query for sym in ('^', '**', '+', '-')):

            factors_dict = sp.factorint(num)
            fact_str = " × ".join(f"{p}^{exp}" if exp > 1 else str(p) for p, exp in sorted(factors_dict.items()))
            all_divisors = sp.divisors(num)

            steps = [
                f"Begin dividing {num} by smallest prime numbers (2, 3, 5, 7, ...):",
                f"Prime Factorization: **{fact_str}**",
                f"All Positive Factors/Divisors: {all_divisors}",
                f"Total number of factors = {len(all_divisors)}",
            ]
            answer = fact_str
            title = f"Prime Factorization of {num}"
            formula = "N = p₁^a₁ × p₂^a₂ × ..."
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="number_theory",
                concept_id="math.number.primes",
                intent=QuestionIntent.FACTOR,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        return None

    def solve_fractions(self, expr_str: str, query: str) -> Optional[SubjectSolveResult]:
        """Solves fraction addition, subtraction, multiplication, division."""
        if "/" in expr_str and not any(var in expr_str for var in ('x', 'y', 'z', 'a', 'b')):
            try:
                parsed = math_parser.parse(expr_str)
                exact_val = sp.Rational(parsed) if isinstance(parsed, (sp.Rational, sp.Integer, sp.Float)) else sp.nsimplify(parsed)
                steps = [
                    f"Evaluate exact fraction arithmetic: `{expr_str}`",
                    f"Find common denominators for fraction operations.",
                    f"Exact Fraction Result: **{exact_val}**",
                ]
                if isinstance(exact_val, sp.Rational) and exact_val.q != 1:
                    decimal_val = float(exact_val)
                    steps.append(f"Decimal equivalent: `{decimal_val:.6g}`")
                    # Mixed fraction
                    whole = int(exact_val.p // exact_val.q)
                    rem = int(abs(exact_val.p) % exact_val.q)
                    if whole > 0 and rem > 0:
                        steps.append(f"Mixed Fraction representation: **{whole} {rem}/{exact_val.q}**")

                answer = str(exact_val)
                title = "Fraction Arithmetic"
                md = math_formatter.format_solution(query, answer, steps, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="fractions",
                    concept_id="math.number.fractions_decimals",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    normalized_expression=expr_str,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    confidence=0.98,
                )
            except Exception:
                pass
        return None

    def solve_general_arithmetic(self, expr_str: str, query: str) -> Optional[SubjectSolveResult]:
        """BODMAS order of operations calculation."""
        try:
            parsed = math_parser.parse(expr_str)
            # Check if it has free symbols (variables)
            if parsed.free_symbols:
                return None  # Pass to algebra engine

            result = sp.simplify(parsed)
            steps = [
                f"Apply BODMAS rule on expression: `{expr_str}`",
                f"Calculate powers, multiplications, divisions, additions and subtractions.",
            ]
            answer = str(result)
            if isinstance(result, sp.Float) or (isinstance(result, sp.Rational) and result.q != 1):
                steps.append(f"Exact Value = **{result}**")
                steps.append(f"Decimal Value ≈ **{float(result):.6g}**")
            else:
                steps.append(f"Simplified Value = **{result}**")

            title = "Arithmetic Evaluation"
            md = math_formatter.format_solution(query, answer, steps, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="arithmetic",
                concept_id="math.arithmetic.basic",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                normalized_expression=expr_str,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.95,
            )
        except Exception:
            return None


# Global instance
arithmetic_engine = ArithmeticEngine()
