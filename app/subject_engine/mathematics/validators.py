"""
Mathematics Engine Validators & Safety Guards
=============================================

PURPOSE:
    Provides safety constraints, recursion limits, timeout guards, and input sanitization
    to prevent Denial of Service (DoS) or runaway symbolic computation.
"""

import re
from typing import Any, Callable
from app.core.logging import get_logger

logger = get_logger(__name__)

# Security & Performance Limits
MAX_EXPRESSION_LENGTH = 1000
MAX_POLYNOMIAL_DEGREE = 20
MAX_MATRIX_DIMENSION = 10
MAX_FACTORIAL_INPUT = 1000
MAX_POWER_EXPONENT = 10000
MAX_RECURSION_DEPTH = 50
MAX_TERMS_COUNT = 100

# Blacklisted unsafe tokens
FORBIDDEN_PYTHON_TOKENS = {
    "import", "exec", "eval", "__", "builtins", "globals", "locals",
    "compile", "open", "file", "os", "sys", "subprocess", "socket",
    "shutil", "getattr", "setattr", "delattr", "hasattr", "breakpoint",
}


class MathValidationError(ValueError):
    """Raised when user math input violates security or complexity boundaries."""
    pass


def validate_expression_safety(expr_str: str) -> None:
    """
    Ensure the mathematical expression contains only safe characters and no forbidden Python tokens.
    """
    if not expr_str:
        raise MathValidationError("Empty mathematical expression.")

    if len(expr_str) > MAX_EXPRESSION_LENGTH:
        raise MathValidationError(f"Expression exceeds maximum allowed length of {MAX_EXPRESSION_LENGTH} characters.")

    # Check for forbidden words
    words = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', expr_str)
    for word in words:
        if word.lower() in FORBIDDEN_PYTHON_TOKENS or word.startswith("__"):
            logger.warning("security_blocked_forbidden_token", token=word)
            raise MathValidationError(f"Invalid identifier or unsafe token: '{word}'")


def validate_matrix_dimensions(rows: int, cols: int) -> None:
    """Validate matrix sizes to prevent memory exhaustion."""
    if rows > MAX_MATRIX_DIMENSION or cols > MAX_MATRIX_DIMENSION:
        raise MathValidationError(f"Matrix size {rows}x{cols} exceeds maximum limit of {MAX_MATRIX_DIMENSION}x{MAX_MATRIX_DIMENSION}.")


def validate_integer_bounds(val: int, name: str = "number", max_val: int = 10**6) -> None:
    """Ensure integer parameters for discrete math do not cause infinite loops."""
    if abs(val) > max_val:
        raise MathValidationError(f"{name} {val} exceeds safety computation limit of {max_val}.")
