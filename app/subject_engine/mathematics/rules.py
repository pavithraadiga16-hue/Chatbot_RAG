"""
Mathematics Rules, Identities & Mathematical Formulas Repository
================================================================

PURPOSE:
    Provides canonical references, standard algebraic identities, trigonometric formulas,
    calculus rules, mensuration formulas, and pedagogical rule descriptions.
"""

from typing import Any, Optional


ALGEBRAIC_IDENTITIES: dict[str, dict[str, str]] = {
    "square_of_sum": {
        "name": "Square of a Binomial Sum",
        "formula": "(a + b)² = a² + 2ab + b²",
        "description": "The square of the sum of two terms is the sum of their squares plus twice their product.",
    },
    "square_of_difference": {
        "name": "Square of a Binomial Difference",
        "formula": "(a - b)² = a² - 2ab + b²",
        "description": "The square of the difference of two terms is the sum of their squares minus twice their product.",
    },
    "difference_of_squares": {
        "name": "Difference of Two Squares",
        "formula": "a² - b² = (a + b)(a - b)",
        "description": "The difference of two squares factors into the sum times the difference of the bases.",
    },
    "cube_of_sum": {
        "name": "Cube of a Binomial Sum",
        "formula": "(a + b)³ = a³ + 3a²b + 3ab² + b³ = a³ + b³ + 3ab(a + b)",
        "description": "The cube of the sum of two terms.",
    },
    "cube_of_difference": {
        "name": "Cube of a Binomial Difference",
        "formula": "(a - b)³ = a³ - 3a²b + 3ab² - b³ = a³ - b³ - 3ab(a - b)",
        "description": "The cube of the difference of two terms.",
    },
    "sum_of_cubes": {
        "name": "Sum of Two Cubes",
        "formula": "a³ + b³ = (a + b)(a² - ab + b²)",
        "description": "Sum of two cubes factorization.",
    },
    "difference_of_cubes": {
        "name": "Difference of Two Cubes",
        "formula": "a³ - b³ = (a - b)(a² + ab + b²)",
        "description": "Difference of two cubes factorization.",
    },
    "square_of_trinomial": {
        "name": "Square of a Trinomial",
        "formula": "(a + b + c)² = a² + b² + c² + 2ab + 2bc + 2ca",
        "description": "The square of a sum of three terms.",
    },
    "sum_of_three_cubes": {
        "name": "Sum of Three Cubes Identity",
        "formula": "a³ + b³ + c³ - 3abc = (a + b + c)(a² + b² + c² - ab - bc - ca)",
        "description": "If a + b + c = 0, then a³ + b³ + c³ = 3abc.",
    },
}

EXPONENT_RULES: list[dict[str, str]] = [
    {"rule": "Product of Powers", "formula": "a^m × a^n = a^(m + n)"},
    {"rule": "Quotient of Powers", "formula": "a^m ÷ a^n = a^(m - n)"},
    {"rule": "Power of a Power", "formula": "(a^m)^n = a^(m × n)"},
    {"rule": "Power of a Product", "formula": "(ab)^n = a^n × b^n"},
    {"rule": "Zero Exponent", "formula": "a^0 = 1 (where a ≠ 0)"},
    {"rule": "Negative Exponent", "formula": "a^(-n) = 1 / a^n"},
    {"rule": "Fractional Exponent", "formula": "a^(m/n) = n-th root of a^m"},
]

TRIGONOMETRIC_IDENTITIES: dict[str, str] = {
    "pythagorean_1": "sin²(θ) + cos²(θ) = 1",
    "pythagorean_2": "1 + tan²(θ) = sec²(θ)",
    "pythagorean_3": "1 + cot²(θ) = cosec²(θ)",
    "double_angle_sin": "sin(2θ) = 2sin(θ)cos(θ) = 2tan(θ)/(1 + tan²(θ))",
    "double_angle_cos": "cos(2θ) = cos²(θ) - sin²(θ) = 2cos²(θ) - 1 = 1 - 2sin²(θ)",
    "double_angle_tan": "tan(2θ) = 2tan(θ)/(1 - tan²(θ))",
    "compound_sin_sum": "sin(A + B) = sin(A)cos(B) + cos(A)sin(B)",
    "compound_sin_diff": "sin(A - B) = sin(A)cos(B) - cos(A)sin(B)",
    "compound_cos_sum": "cos(A + B) = cos(A)cos(B) - sin(A)sin(B)",
    "compound_cos_diff": "cos(A - B) = cos(A)cos(B) + sin(A)sin(B)",
}

GEOMETRIC_FORMULAS: dict[str, dict[str, str]] = {
    "circle": {
        "area": "Area = πr²",
        "perimeter": "Circumference = 2πr = πd",
        "sector_area": "Sector Area = (θ/360°) × πr²",
        "arc_length": "Arc Length = (θ/360°) × 2πr",
    },
    "triangle": {
        "area": "Area = (1/2) × base × height",
        "heron": "Heron's Formula: Area = √(s(s - a)(s - b)(s - c)), where s = (a + b + c)/2",
        "equilateral_area": "Area = (√3 / 4) × a²",
        "perimeter": "Perimeter = a + b + c",
        "pythagoras": "Pythagoras Theorem: Hypotenuse² = Base² + Perpendicular² (c² = a² + b²)",
    },
    "rectangle": {
        "area": "Area = length × breadth",
        "perimeter": "Perimeter = 2 × (length + breadth)",
        "diagonal": "Diagonal = √(length² + breadth²)",
    },
    "square": {
        "area": "Area = side²",
        "perimeter": "Perimeter = 4 × side",
        "diagonal": "Diagonal = side × √2",
    },
    "parallelogram": {
        "area": "Area = base × height",
        "perimeter": "Perimeter = 2 × (a + b)",
    },
    "rhombus": {
        "area": "Area = (1/2) × d₁ × d₂",
        "perimeter": "Perimeter = 4 × side",
    },
    "trapezium": {
        "area": "Area = (1/2) × (a + b) × height",
    },
    "cube": {
        "volume": "Volume = a³",
        "total_surface_area": "TSA = 6a²",
        "lateral_surface_area": "LSA = 4a²",
    },
    "cuboid": {
        "volume": "Volume = length × breadth × height",
        "total_surface_area": "TSA = 2(lb + bh + hl)",
        "lateral_surface_area": "LSA = 2h(l + b)",
    },
    "cylinder": {
        "volume": "Volume = πr²h",
        "curved_surface_area": "CSA = 2πrh",
        "total_surface_area": "TSA = 2πr(r + h)",
    },
    "cone": {
        "volume": "Volume = (1/3)πr²h",
        "slant_height": "l = √(r² + h²)",
        "curved_surface_area": "CSA = πrl",
        "total_surface_area": "TSA = πr(r + l)",
    },
    "sphere": {
        "volume": "Volume = (4/3)πr³",
        "surface_area": "Surface Area = 4πr²",
    },
    "hemisphere": {
        "volume": "Volume = (2/3)πr³",
        "curved_surface_area": "CSA = 2πr²",
        "total_surface_area": "TSA = 3πr²",
    },
}
