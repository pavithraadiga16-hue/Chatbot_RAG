"""
Mathematics Input Normalizer
============================

PURPOSE:
    Transforms natural language student typing, speech patterns, abbreviations,
    Unicode mathematical symbols, and spoken mathematical phrases into canonical
    mathematical expressions ready for parsing and symbolic processing.
"""

import re
import unicodedata
from typing import Optional


# Unicode Superscript Mapping
UNICODE_EXPONENTS = {
    '⁰': '^0', '¹': '^1', '²': '^2', '³': '^3', '⁴': '^4',
    '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9',
    'ⁿ': '^n', 'ˣ': '^x', 'ʸ': '^y',
}

# Unicode Math Symbols Replacement
UNICODE_SYMBOLS = {
    '×': '*',
    '÷': '/',
    '·': '*',
    '∙': '*',
    '√': ' sqrt ',
    'π': ' pi ',
    '∞': ' oo ',
    '≤': ' <= ',
    '≥': ' >= ',
    '≠': ' != ',
    '±': ' +- ',
    '∑': ' sum ',
    '∫': ' integrate ',
    'θ': ' theta ',
    'α': ' alpha ',
    'β': ' beta ',
    'γ': ' gamma ',
    'δ': ' delta ',
    'λ': ' lambda ',
    'μ': ' mu ',
    'σ': ' sigma ',
    'ω': ' omega ',
    'Δ': ' Delta ',
    '∈': ' in ',
    '∉': ' not in ',
    '∪': ' union ',
    '∩': ' intersection ',
    '⊂': ' subset ',
    '⊆': ' subseteq ',
    '∅': ' empty_set ',
}


class MathNormalizer:
    """Normalizes natural student math input to canonical math syntax."""

    def __init__(self) -> None:
        self._init_regex_rules()

    def _init_regex_rules(self) -> None:
        """Pre-compile regex transformation rules."""
        # Word power patterns
        self.power_rules = [
            (re.compile(r'(\b\w+|\))\s+to\s+the\s+power\s+of\s+(\b\w+|\()', re.IGNORECASE), r'\1^\2'),
            (re.compile(r'(\b\w+|\))\s+to\s+the\s+power\s+(\b\w+|\()', re.IGNORECASE), r'\1^\2'),
            (re.compile(r'(\b\w+|\))\s+raised\s+to\s+the\s+power\s+of\s+(\b\w+|\()', re.IGNORECASE), r'\1^\2'),
            (re.compile(r'(\b\w+|\))\s+raised\s+to\s+the\s+power\s+(\b\w+|\()', re.IGNORECASE), r'\1^\2'),
            (re.compile(r'(\b\w+|\))\s+raised\s+to\s+(\b\w+|\()', re.IGNORECASE), r'\1^\2'),
            (re.compile(r'(\b\w+|\))\s+power\s+(\b\w+|\()', re.IGNORECASE), r'\1^\2'),
            (re.compile(r'(\b\w+|\))\s+squared\b', re.IGNORECASE), r'\1^2'),
            (re.compile(r'(\b\w+|\))\s+square\b', re.IGNORECASE), r'\1^2'),
            (re.compile(r'(\b\w+|\))\s+cubed\b', re.IGNORECASE), r'\1^3'),
            (re.compile(r'(\b\w+|\))\s+cube\b', re.IGNORECASE), r'\1^3'),
        ]

        # Root patterns
        self.root_rules = [
            (re.compile(r'\bsquare\s+root\s+of\s+([a-zA-Z0-9_().+\-*/^]+)', re.IGNORECASE), r'sqrt(\1)'),
            (re.compile(r'\bsquare\s+root\s+([a-zA-Z0-9_().+\-*/^]+)', re.IGNORECASE), r'sqrt(\1)'),
            (re.compile(r'\bcube\s+root\s+of\s+([a-zA-Z0-9_().+\-*/^]+)', re.IGNORECASE), r'cbrt(\1)'),
            (re.compile(r'\bcube\s+root\s+([a-zA-Z0-9_().+\-*/^]+)', re.IGNORECASE), r'cbrt(\1)'),
            (re.compile(r'\broot\s+([a-zA-Z0-9_().+\-*/^]+)', re.IGNORECASE), r'sqrt(\1)'),
        ]

        # Operator word phrases
        self.operator_rules = [
            (re.compile(r'\bmultiplied\s+by\b', re.IGNORECASE), '*'),
            (re.compile(r'\btimes\b', re.IGNORECASE), '*'),
            (re.compile(r'\binto\b', re.IGNORECASE), '*'),
            (re.compile(r'\bdivided\s+by\b', re.IGNORECASE), '/'),
            (re.compile(r'\bover\b', re.IGNORECASE), '/'),
            (re.compile(r'\bplus\b', re.IGNORECASE), '+'),
            (re.compile(r'\bminus\b', re.IGNORECASE), '-'),
            (re.compile(r'\bgreater\s+than\s+or\s+equal\s+to\b', re.IGNORECASE), '>='),
            (re.compile(r'\bless\s+than\s+or\s+equal\s+to\b', re.IGNORECASE), '<='),
            (re.compile(r'\bgreater\s+than\b', re.IGNORECASE), '>'),
            (re.compile(r'\bless\s+than\b', re.IGNORECASE), '<'),
            (re.compile(r'\bnot\s+equal\s+to\b', re.IGNORECASE), '!='),
            (re.compile(r'\bnot\s+equals\b', re.IGNORECASE), '!='),
            (re.compile(r'\bis\s+equal\s+to\b', re.IGNORECASE), '='),
            (re.compile(r'\bequal\s+to\b', re.IGNORECASE), '='),
            (re.compile(r'\bequals\b', re.IGNORECASE), '='),
        ]

    def normalize(self, text: str) -> str:
        """
        Main entry point: transforms student natural language into canonical mathematical string.
        """
        if not text:
            return ""

        # Step 1: Replace unicode exponents (e.g. x², x³) before NFKC decomposition
        normalized = text.strip()
        for u_char, replacement in UNICODE_EXPONENTS.items():
            normalized = normalized.replace(u_char, replacement)

        for u_char, replacement in UNICODE_SYMBOLS.items():
            normalized = normalized.replace(u_char, replacement)

        # Step 2: Strip leading/trailing whitespaces and normalize remaining unicode
        normalized = unicodedata.normalize('NFKC', normalized)


        # Step 4: Apply root rules (e.g. "square root of 25" -> "sqrt(25)")
        for pattern, replacement in self.root_rules:
            normalized = pattern.sub(replacement, normalized)

        # Step 5: Apply word power rules (e.g. "x to the power 3" -> "x^3")
        for pattern, replacement in self.power_rules:
            normalized = pattern.sub(replacement, normalized)

        # Step 6: Apply operator word rules (e.g. "plus", "minus", "divided by", "into")
        for pattern, replacement in self.operator_rules:
            normalized = pattern.sub(replacement, normalized)

        # Step 7: Handle implicit multiplication (e.g. 2x -> 2*x, 5(x+1) -> 5*(x+1))
        normalized = self.insert_implicit_multiplication(normalized)

        # Step 8: Standardize spacing around operators
        normalized = self.clean_whitespace(normalized)

        return normalized

    def insert_implicit_multiplication(self, expr: str) -> str:
        """
        Inserts explicit '*' operator for algebraic shorthand:
        - 2x -> 2*x
        - 5(x+1) -> 5*(x+1)
        - (x+1)(x+2) -> (x+1)*(x+2)
        - x(x+1) -> x*(x+1)
        - 3sin(x) -> 3*sin(x)
        - 2sqrt(5) -> 2*sqrt(5)
        - 4pi -> 4*pi
        """
        # Math identifiers allowed to be implicitly multiplied
        math_identifiers = {
            "sin", "cos", "tan", "cot", "sec", "csc", "cosec",
            "asin", "acos", "atan", "arcsin", "arccos", "arctan",
            "log", "ln", "exp", "sqrt", "cbrt", "abs", "limit",
            "diff", "integrate", "pi", "oo", "factorial", "gcd", "lcm",
            "theta", "alpha", "beta", "gamma", "delta", "lambda", "mu", "sigma", "omega"
        }

        # 1. Number immediately followed by variable or function: 2x -> 2*x, 2sin -> 2*sin, 4pi -> 4*pi
        def _num_word_replacer(match: re.Match) -> str:
            num = match.group(1)
            word = match.group(2)
            # If word is single character variable (e.g. x, y, z, a, b) or known math function/constant
            if len(word) == 1 or word.lower() in math_identifiers:
                return f"{num}*{word}"
            return match.group(0)

        expr = re.sub(r'(\d+)\s*([a-zA-Z_]\w*)', _num_word_replacer, expr)

        # 2. Number immediately followed by open parenthesis: 2(x+1) -> 2*(x+1)
        expr = re.sub(r'(\d+)\s*\(', r'\1*(', expr)

        # 3. Close parenthesis immediately followed by open parenthesis: (x+1)(x+2) -> (x+1)*(x+2)
        expr = re.sub(r'\)\s*\(', r')*(', expr)

        # 4. Close parenthesis followed by single variable/number: (x+1)x -> (x+1)*x, (x+1)2 -> (x+1)*2
        def _paren_word_replacer(match: re.Match) -> str:
            word = match.group(1)
            if len(word) == 1 or word.lower() in math_identifiers or word.isdigit():
                return f")*{word}"
            return match.group(0)

        expr = re.sub(r'\)\s*([a-zA-Z0-9_]+)', _paren_word_replacer, expr)

        # 5. Variable (single char like x, y, z) followed by open parenthesis that is NOT a recognized function:
        # e.g., x(x+1) -> x*(x+1), but NOT sin(x) -> sin*(x)
        def _var_paren_replacer(match: re.Match) -> str:
            ident = match.group(1)
            if ident.lower() in math_identifiers:
                return match.group(0)
            if len(ident) == 1:
                return f"{ident}*("
            return match.group(0)

        expr = re.sub(r'([a-zA-Z_]\w*)\s*\(', _var_paren_replacer, expr)
        return expr


    def clean_whitespace(self, expr: str) -> str:
        """Cleans up excess whitespace."""
        # Replace multiple spaces with a single space
        expr = re.sub(r'\s+', ' ', expr).strip()
        # Clean up spacing around arithmetic operators while preserving compound operators (<=, >=, !=, ==, **)
        expr = re.sub(r'\s*(<=|>=|!=|==|\*\*|\^|\*|\/|\+|\-|=|<|>)\s*', r' \1 ', expr)
        # Consolidate double spaces
        expr = re.sub(r'\s+', ' ', expr).strip()
        return expr



# Global instance
math_normalizer = MathNormalizer()
