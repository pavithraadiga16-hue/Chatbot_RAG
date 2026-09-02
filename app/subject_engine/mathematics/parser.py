"""
Safe Mathematical Parser
========================

PURPOSE:
    Parses normalized mathematical expressions into SymPy symbolic objects and abstract
    syntax representations with strict safety checks.
    NEVER uses Python eval() or arbitrary code execution.
"""

import ast
import re
from typing import Any, Optional, Union
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

from app.subject_engine.mathematics.validators import (
    validate_expression_safety,
    MathValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# Custom safe local dict for SymPy parsing
SAFE_SYMPY_LOCALS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "sec": sp.sec,
    "csc": sp.csc,
    "cosec": sp.csc,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "arcsin": sp.asin,
    "arccos": sp.acos,
    "arctan": sp.atan,
    "sqrt": sp.sqrt,
    "cbrt": sp.cbrt,
    "log": sp.log,
    "ln": sp.log,
    "exp": sp.exp,
    "abs": sp.Abs,
    "pi": sp.pi,
    "E": sp.E,
    "oo": sp.oo,
    "infinity": sp.oo,
    "diff": sp.diff,
    "integrate": sp.integrate,
    "limit": sp.limit,
    "gcd": sp.gcd,
    "lcm": sp.lcm,
    "factorial": sp.factorial,
}


class MathParser:
    """Safe SymPy parser wrapper."""

    def parse(self, expr_str: str) -> sp.Expr:
        """
        Safely parse mathematical string into a SymPy expression.
        """
        expr_str = expr_str.strip()
        if not expr_str:
            raise MathValidationError("Cannot parse empty mathematical expression.")

        # 1. Security validation check
        validate_expression_safety(expr_str)

        # 2. Pre-process caret ^ to ** if not already handled
        clean_expr = expr_str.replace("^", "**")

        # 3. Parse with restricted transformations and safe symbol tables
        try:
            parsed = parse_expr(
                clean_expr,
                local_dict=SAFE_SYMPY_LOCALS,
                transformations=TRANSFORMATIONS,
                evaluate=False,  # Keep un-evaluated initially so structure is preserved
            )
            return parsed
        except Exception as e:
            # Fallback attempt: evaluate=True
            try:
                parsed = parse_expr(
                    clean_expr,
                    local_dict=SAFE_SYMPY_LOCALS,
                    transformations=TRANSFORMATIONS,
                    evaluate=True,
                )
                return parsed
            except Exception as inner_e:
                logger.debug("math_parser_failed", expr=expr_str, error=str(e))
                raise MathValidationError(f"Could not parse mathematical expression '{expr_str}': {str(e)}")

    def extract_equation(self, text: str) -> Optional[tuple[sp.Expr, sp.Expr]]:
        """
        Detects and parses an equation containing '=' or '=='.
        Returns (LHS, RHS) expressions.
        """
        if "=" in text:
            parts = text.split("=", 1)
            lhs_str = parts[0].strip()
            rhs_str = parts[1].strip()
            if lhs_str and rhs_str:
                try:
                    lhs = self.parse(lhs_str)
                    rhs = self.parse(rhs_str)
                    return lhs, rhs
                except Exception:
                    pass
        return None

    def extract_numbers(self, text: str) -> list[Union[int, float]]:
        """
        Extract numerical literals from a text string (e.g. 'find HCF of 24 and 36' -> [24, 36]).
        """
        # Match integers, decimals, negative numbers
        pattern = r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?'
        matches = re.findall(pattern, text)
        nums = []
        for m in matches:
            if not m:
                continue
            try:
                if '.' in m or 'e' in m.lower():
                    nums.append(float(m))
                else:
                    nums.append(int(m))
            except ValueError:
                pass
        return nums


# Global instance
math_parser = MathParser()
