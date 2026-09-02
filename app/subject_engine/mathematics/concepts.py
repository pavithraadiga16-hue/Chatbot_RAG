"""
Mathematics Concept Knowledge Base
==================================

PURPOSE:
    Comprehensive, maintainable concept and topic repository spanning LKG through PUC.
    Provides structured definitions, formulas, aliases, question patterns, and solver bindings.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class MathConcept(BaseModel):
    """Structured knowledge representation for an educational mathematics concept."""
    concept_id: str
    subject: str = "mathematics"
    topic: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    question_patterns: list[str] = Field(default_factory=list)
    definition: str
    formula: Optional[str] = None
    rules: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    solver_type: str
    difficulty: str = "general"  # primary, middle_school, high_school, puc
    supported_operations: list[str] = Field(default_factory=list)


# Central Concept Catalog
CONCEPTS_CATALOG: list[MathConcept] = [
    # ---------------- Number System & Basic Arithmetic (LKG - Grade 5) ----------------
    MathConcept(
        concept_id="math.arithmetic.basic",
        topic="arithmetic",
        name="Basic Arithmetic & BODMAS",
        aliases=["arithmetic", "addition", "subtraction", "multiplication", "division", "bodmas", "pemdas"],
        keywords=["add", "plus", "sum", "subtract", "minus", "difference", "multiply", "product", "into", "times", "divide", "quotient", "remainder", "bodmas"],
        definition="Fundamental arithmetic operations following the BODMAS order (Brackets, Orders/Exponents, Division, Multiplication, Addition, Subtraction).",
        formula="BODMAS Order: ( ) -> ^ -> ÷ / × -> + / -",
        examples=["25 + 48", "100 - 37", "12 * 15", "144 / 12", "5 + 2 * 3"],
        solver_type="arithmetic",
        difficulty="primary",
        supported_operations=["calculate", "simplify", "evaluate"],
    ),
    MathConcept(
        concept_id="math.number.primes",
        topic="number_theory",
        name="Prime Numbers & Factorization",
        aliases=["prime number", "prime", "composite number", "prime factors", "prime factorization"],
        keywords=["prime", "composite", "prime factors", "factorize", "prime factorization", "is prime"],
        definition="A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself. Prime factorization is expressing a number as a product of prime numbers.",
        formula="N = p₁^(a₁) × p₂^(a₂) × ... × pₖ^(aₖ)",
        examples=["is 97 prime?", "prime factors of 360", "prime factorization of 84"],
        solver_type="arithmetic",
        difficulty="middle_school",
        supported_operations=["find_value", "factor", "evaluate"],
    ),
    MathConcept(
        concept_id="math.number.hcf_lcm",
        topic="number_theory",
        name="HCF (GCD) and LCM",
        aliases=["hcf", "gcd", "highest common factor", "greatest common divisor", "lcm", "least common multiple", "lowest common multiple"],
        keywords=["hcf", "gcd", "lcm", "highest common factor", "lowest common multiple", "greatest common divisor"],
        definition="HCF (Highest Common Factor) is the largest integer dividing two or more numbers. LCM (Lowest Common Multiple) is the smallest positive integer divisible by all of them.",
        formula="HCF(a, b) × LCM(a, b) = a × b",
        examples=["find HCF of 24 and 36", "find LCM of 12, 18, and 24", "GCD of 48 and 180"],
        solver_type="arithmetic",
        difficulty="middle_school",
        supported_operations=["calculate", "find_value"],
    ),
    MathConcept(
        concept_id="math.number.fractions_decimals",
        topic="fractions",
        name="Fractions and Decimals",
        aliases=["fraction", "decimals", "mixed fraction", "recurring decimal", "proper fraction", "improper fraction"],
        keywords=["fraction", "numerator", "denominator", "decimal", "recurring", "simplest form"],
        definition="A fraction represents part of a whole (a/b). Recurring decimals are non-terminating repeating decimals convertable to rational fractions.",
        formula="a/b ± c/d = (ad ± bc) / bd, a/b × c/d = ac / bd, a/b ÷ c/d = ad / bc",
        examples=["2/3 + 4/5", "3/4 * 8/9", "convert 0.333... to fraction", "simplify 24/36"],
        solver_type="arithmetic",
        difficulty="middle_school",
        supported_operations=["calculate", "simplify", "convert"],
    ),

    # ---------------- Algebra & Polynomials (Grades 6 - 10) ----------------
    MathConcept(
        concept_id="math.algebra.simplification",
        topic="algebra",
        name="Algebraic Simplification & Identities",
        aliases=["algebra", "simplify expression", "expand expression", "algebraic identities"],
        keywords=["simplify", "expand", "algebraic", "terms", "coefficient", "monomial", "binomial", "polynomial"],
        definition="Simplifying algebraic expressions by combining like terms and expanding polynomials using algebraic identities.",
        formula="(a + b)² = a² + 2ab + b², (a - b)² = a² - 2ab + b², a² - b² = (a - b)(a + b)",
        examples=["expand (2x + 3)^2", "simplify 3x + 5y - x + 2y", "expand (x + 2)(x + 5)"],
        solver_type="algebra",
        difficulty="high_school",
        supported_operations=["simplify", "expand", "factor"],
    ),
    MathConcept(
        concept_id="math.algebra.linear_equation",
        topic="equations",
        name="Linear Equations (1 & 2 Variables)",
        aliases=["linear equation", "solve for x", "system of equations", "simultaneous equations"],
        keywords=["solve", "equation", "linear equation", "simultaneous", "elimination", "substitution"],
        definition="An equation of the first degree in one or two variables. For systems of two variables: a₁x + b₁y = c₁, a₂x + b₂y = c₂.",
        formula="ax + b = 0 => x = -b/a; 2-var solution via Cramer's Rule or Substitution",
        examples=["solve 2x + 5 = 15", "solve 3x - 7 = 2x + 8", "solve 2x + y = 7 and x - y = 2"],
        solver_type="equation",
        difficulty="high_school",
        supported_operations=["solve"],
    ),
    MathConcept(
        concept_id="math.algebra.quadratic",
        topic="quadratic_equations",
        name="Quadratic Equations",
        aliases=["quadratic", "quadratic equation", "second degree equation", "roots of quadratic"],
        keywords=["quadratic", "roots", "discriminant", "factorize", "quadratic formula", "parabola zeroes"],
        definition="A polynomial equation of degree 2 in standard form ax² + bx + c = 0 (a ≠ 0).",
        formula="x = (-b ± √(b² - 4ac)) / (2a); Discriminant Δ = b² - 4ac",
        rules=[
            "If Δ > 0: Two distinct real roots",
            "If Δ = 0: Two equal real roots (x = -b/2a)",
            "If Δ < 0: Two complex conjugate roots",
            "Sum of roots: α + β = -b/a",
            "Product of roots: αβ = c/a",
        ],
        examples=["solve x^2 - 5x + 6 = 0", "find roots of 2x^2 + 7x + 3 = 0", "discriminant of x^2 + 4x + 5 = 0"],
        solver_type="equation",
        difficulty="high_school",
        supported_operations=["solve", "factor", "find_value"],
    ),
    MathConcept(
        concept_id="math.algebra.polynomials",
        topic="polynomials",
        name="Polynomial Division & Remainder Theorem",
        aliases=["polynomial", "remainder theorem", "factor theorem", "zeroes of polynomial"],
        keywords=["polynomial", "remainder", "factor theorem", "degree", "zeroes", "divide polynomial"],
        definition="Remainder Theorem: If polynomial P(x) is divided by (x - a), the remainder is P(a). Factor Theorem: (x - a) is a factor of P(x) if and only if P(a) = 0.",
        formula="Dividend = Divisor × Quotient + Remainder",
        examples=["divide x^3 - 3x^2 + 5x - 3 by x - 1", "find remainder when x^4 - 2x + 1 is divided by x - 2", "find zeroes of x^3 - 6x^2 + 11x - 6"],
        solver_type="polynomial",
        difficulty="high_school",
        supported_operations=["divide", "find_value", "solve"],
    ),

    # ---------------- Commercial Math & Percentages (Grades 6 - 10) ----------------
    MathConcept(
        concept_id="math.commercial.percentage",
        topic="commercial_math",
        name="Percentages, Profit, Loss & Discount",
        aliases=["percentage", "percent", "profit", "loss", "discount", "marked price", "cost price", "selling price"],
        keywords=["percentage", "percent", "profit", "loss", "discount", "cp", "sp", "marked price", "profit percentage"],
        definition="Percentages represent hundredths. Profit = SP - CP, Loss = CP - SP, Discount = Marked Price - Selling Price.",
        formula="Profit % = (Profit / CP) × 100%, Loss % = (Loss / CP) × 100%, Discount % = (Discount / MP) × 100%",
        examples=["20% of 500", "CP = 400 and SP = 500 find profit percentage", "increase 120 by 15%"],
        solver_type="financial_math",
        difficulty="middle_school",
        supported_operations=["calculate", "find_value"],
    ),
    MathConcept(
        concept_id="math.commercial.interest",
        topic="commercial_math",
        name="Simple and Compound Interest",
        aliases=["simple interest", "compound interest", "si", "ci", "principal", "amount", "rate of interest"],
        keywords=["simple interest", "compound interest", "principal", "si", "ci", "interest rate"],
        definition="Simple interest is calculated on the principal only. Compound interest is calculated on the principal plus accumulated interest.",
        formula="SI = (P × R × T) / 100; Amount = P(1 + R/100)^T; CI = Amount - P",
        examples=["find simple interest on principal 10000 rate 5% for 3 years", "compound interest on 5000 at 10% per annum for 2 years"],
        solver_type="financial_math",
        difficulty="high_school",
        supported_operations=["calculate", "find_value"],
    ),

    # ---------------- Geometry & Mensuration (Grades 6 - 10) ----------------
    MathConcept(
        concept_id="math.geometry.2d",
        topic="geometry",
        name="2D Geometry & Triangle Properties",
        aliases=["triangle", "pythagoras theorem", "circle", "rectangle", "square", "area", "perimeter", "heron formula"],
        keywords=["area", "perimeter", "hypotenuse", "pythagoras", "circumference", "radius", "diameter", "triangle", "rectangle", "circle", "heron"],
        definition="Formulas and theorems governing 2D plane geometric figures including triangles, circles, and quadrilaterals.",
        formula="Circle: Area = πr², Circumference = 2πr; Pythagoras: a² + b² = c²; Heron: √(s(s-a)(s-b)(s-c))",
        examples=["find area of circle radius 7", "hypotenuse of right triangle with legs 3 and 4", "area of triangle with sides 5, 12, 13"],
        solver_type="geometry",
        difficulty="high_school",
        supported_operations=["calculate", "find_value", "prove"],
    ),
    MathConcept(
        concept_id="math.geometry.3d",
        topic="mensuration",
        name="3D Mensuration & Solids",
        aliases=["surface area", "volume", "cylinder", "cone", "sphere", "cube", "cuboid", "hemisphere", "frustum"],
        keywords=["volume", "surface area", "tsa", "csa", "cylinder", "cone", "sphere", "hemisphere", "cube", "cuboid"],
        definition="Measurement of volume, curved surface area (CSA), and total surface area (TSA) of solid 3D geometrical shapes.",
        formula="Cylinder Volume = πr²h, Sphere Volume = (4/3)πr³, Cone Volume = (1/3)πr²h",
        examples=["volume of cylinder radius 7 height 10", "total surface area of cube side 5", "volume of sphere radius 6"],
        solver_type="geometry",
        difficulty="high_school",
        supported_operations=["calculate", "find_value"],
    ),

    # ---------------- Coordinate Geometry & Vectors (Grades 9 - 12 / PUC) ----------------
    MathConcept(
        concept_id="math.coordinate_geometry",
        topic="coordinate_geometry",
        name="Coordinate Geometry & Straight Lines",
        aliases=["coordinate geometry", "distance formula", "midpoint", "slope of line", "equation of line", "section formula"],
        keywords=["distance between", "midpoint", "slope", "collinear", "equation of line", "cartesian", "intercept"],
        definition="Analytical geometry connecting algebra with geometric curves in the 2D Cartesian plane.",
        formula="Distance: √((x₂ - x₁)² + (y₂ - y₁)²); Midpoint: ((x₁+x₂)/2, (y₁+y₂)/2); Slope: m = (y₂ - y₁)/(x₂ - x₁); Line: y - y₁ = m(x - x₁)",
        examples=["distance between (2, 3) and (5, 7)", "midpoint of (4, 6) and (8, 10)", "slope of line passing through (1, 2) and (3, 8)"],
        solver_type="coordinate_geometry",
        difficulty="puc",
        supported_operations=["calculate", "find_value", "solve"],
    ),
    MathConcept(
        concept_id="math.vector",
        topic="vectors",
        name="Vector Algebra",
        aliases=["vector", "dot product", "cross product", "magnitude of vector", "unit vector", "scalar product", "vector product"],
        keywords=["vector", "dot product", "cross product", "magnitude", "unit vector", "angle between vectors", "projection"],
        definition="Quantities possessing both magnitude and direction, supporting scalar dot products (a · b) and vector cross products (a × b).",
        formula="|v| = √(x² + y² + z²); a · b = |a||b|cos(θ); a × b = |a||b|sin(θ) n̂",
        examples=["magnitude of 3i + 4j", "dot product of (1, 2, 3) and (4, -5, 6)", "cross product of (1, 0, 0) and (0, 1, 0)"],
        solver_type="vector",
        difficulty="puc",
        supported_operations=["calculate", "find_value"],
    ),

    # ---------------- Trigonometry & Inverse Trig (Grades 10 - 12 / PUC) ----------------
    MathConcept(
        concept_id="math.trigonometry",
        topic="trigonometry",
        name="Trigonometry & Inverse Trigonometry",
        aliases=["trigonometry", "sin", "cos", "tan", "sec", "cosec", "cot", "inverse trig", "arcsin", "arccos", "arctan"],
        keywords=["sin", "cos", "tan", "cot", "sec", "cosec", "csc", "arcsin", "arccos", "arctan", "degrees", "radians"],
        definition="Study of relationships between angles and side ratios in triangles, extended to periodic real functions and their inverse principal branches.",
        formula="sin²(θ) + cos²(θ) = 1, tan(θ) = sin(θ)/cos(θ), sin(30°) = 1/2, cos(60°) = 1/2, tan(45°) = 1",
        examples=["sin 30", "cos 60", "tan 45 degrees", "sin(pi/6)", "arctan(1)"],
        solver_type="trigonometry",
        difficulty="puc",
        supported_operations=["calculate", "evaluate", "simplify"],
    ),

    # ---------------- Matrices & Determinants (PUC / Grade 11 - 12) ----------------
    MathConcept(
        concept_id="math.matrix",
        topic="matrices",
        name="Matrices and Determinants",
        aliases=["matrix", "determinant", "matrix multiplication", "inverse matrix", "cramer rule", "transpose"],
        keywords=["matrix", "determinant", "det", "transpose", "inverse", "matrix multiplication", "adjoint", "cramer"],
        definition="Rectangular arrays of numbers subject to matrix algebraic operations, determinants, inverses, and solving linear systems.",
        formula="Det([[a, b], [c, d]]) = ad - bc; A⁻¹ = (1/det(A)) × adj(A)",
        examples=["determinant of [[1, 2], [3, 4]]", "multiply [[1, 2], [3, 4]] and [[5, 6], [7, 8]]", "transpose of [[1, 2, 3], [4, 5, 6]]"],
        solver_type="matrix",
        difficulty="puc",
        supported_operations=["calculate", "find_value", "solve"],
    ),

    # ---------------- Sequences & Series (Grades 10 - 11 / PUC) ----------------
    MathConcept(
        concept_id="math.sequence_series",
        topic="sequences_series",
        name="Arithmetic & Geometric Progressions (AP & GP)",
        aliases=["ap", "gp", "arithmetic progression", "geometric progression", "nth term of ap", "sum of ap", "infinite gp"],
        keywords=["ap", "gp", "arithmetic progression", "geometric progression", "nth term", "common difference", "common ratio", "sum of series"],
        definition="Sequences of numbers where difference between consecutive terms is constant (AP) or ratio is constant (GP).",
        formula="AP: Tₙ = a + (n - 1)d, Sₙ = (n/2)(2a + (n - 1)d); GP: Tₙ = a·r^(n-1), Sₙ = a(rⁿ - 1)/(r - 1), S_inf = a/(1 - r)",
        examples=["find 10th term of AP 2, 5, 8, ...", "sum of first 20 terms of AP 3, 7, 11, ...", "sum of infinite GP 1, 1/2, 1/4, ..."],
        solver_type="sequence_series",
        difficulty="high_school",
        supported_operations=["calculate", "find_value"],
    ),

    # ---------------- Permutations, Combinations & Binomial Theorem (PUC) ----------------
    MathConcept(
        concept_id="math.combinatorics",
        topic="combinatorics",
        name="Permutations, Combinations & Binomial Theorem",
        aliases=["permutation", "combination", "npr", "ncr", "factorial", "binomial expansion", "binomial theorem"],
        keywords=["factorial", "permutation", "combination", "npr", "ncr", "arrangements", "selections", "binomial theorem", "pascal triangle"],
        definition="Principles of counting, ordering (permutations nPr), selections (combinations nCr), and algebraic expansions (a + b)ⁿ.",
        formula="n! = n(n-1)...1; ⁿPᵣ = n! / (n - r)!; ⁿCᵣ = n! / (r!(n - r)!); (a + b)ⁿ = Σ ⁿCᵣ a^(n-r) bʳ",
        examples=["find 5!", "calculate 7P3", "calculate 10C3", "expand (x + y)^4"],
        solver_type="permutation_combination",
        difficulty="puc",
        supported_operations=["calculate", "expand", "find_value"],
    ),

    # ---------------- Calculus: Limits, Derivatives & Integrals (PUC) ----------------
    MathConcept(
        concept_id="math.calculus.differentiation",
        topic="calculus",
        name="Differential Calculus",
        aliases=["derivative", "differentiate", "differentiation", "d/dx", "tangent", "maxima", "minima"],
        keywords=["derivative", "differentiate", "differentiation", "diff", "d/dx", "rate of change", "critical points", "chain rule"],
        definition="The instantaneous rate of change of a function with respect to an independent variable.",
        formula="d/dx(xⁿ) = n·xⁿ⁻¹, d/dx(sin x) = cos x, d/dx(eˣ) = eˣ, d/dx(ln x) = 1/x; Product rule: (uv)' = u'v + uv'; Quotient rule: (u/v)' = (u'v - uv')/v²",
        examples=["differentiate x^3", "derivative of sin(x) + cos(x)", "d/dx of x^2 * e^x", "derivative of log(x)"],
        solver_type="calculus",
        difficulty="puc",
        supported_operations=["differentiate", "calculate"],
    ),
    MathConcept(
        concept_id="math.calculus.integration",
        topic="calculus",
        name="Integral Calculus",
        aliases=["integral", "integrate", "integration", "antiderivative", "definite integral", "area under curve"],
        keywords=["integrate", "integral", "integration", "antiderivative", "definite integral", "area under curve"],
        definition="The inverse operation of differentiation, computing accumulation and areas under curves.",
        formula="∫ xⁿ dx = (xⁿ⁺¹)/(n + 1) + C (n ≠ -1); ∫ eˣ dx = eˣ + C; ∫ 1/x dx = ln|x| + C; ∫ sin(x) dx = -cos(x) + C",
        examples=["integrate x^2", "integration of sin(x)", "integrate 3x^2 + 2x + 1", "definite integral of x from 0 to 2"],
        solver_type="calculus",
        difficulty="puc",
        supported_operations=["integrate", "calculate"],
    ),
    MathConcept(
        concept_id="math.calculus.limits",
        topic="calculus",
        name="Limits & Continuity",
        aliases=["limit", "limits", "continuity", "lim", "lhopital"],
        keywords=["limit", "limits", "lim", "as x approaches", "continuity", "discontinuity"],
        definition="The value that a function approaches as the input approaches some value.",
        formula="lim(x->0) sin(x)/x = 1; lim(x->0) (eˣ - 1)/x = 1; lim(x->0) (1 + x)^(1/x) = e",
        examples=["limit of (x^2 - 4)/(x - 2) as x -> 2", "limit of sin(x)/x as x -> 0", "lim x->0 (1 - cos(x))/x^2"],
        solver_type="calculus",
        difficulty="puc",
        supported_operations=["calculate", "evaluate"],
    ),

    # ---------------- Statistics & Probability (Grades 8 - 12 / PUC) ----------------
    MathConcept(
        concept_id="math.statistics",
        topic="statistics",
        name="Statistics (Mean, Median, Mode, Variance)",
        aliases=["statistics", "mean", "median", "mode", "variance", "standard deviation", "range", "quartiles"],
        keywords=["mean", "median", "mode", "average", "variance", "standard deviation", "range", "quartiles", "data"],
        definition="Collection, analysis, interpretation, and presentation of numerical data.",
        formula="Mean: x̄ = (Σ xᵢ)/N; Variance: σ² = Σ(xᵢ - x̄)²/N; Standard Deviation: σ = √(Variance)",
        examples=["mean of 10, 20, 30, 40, 50", "median of 3, 5, 7, 9, 11", "mode of 2, 3, 3, 5, 7", "standard deviation of 2, 4, 4, 4, 5, 5, 7, 9"],
        solver_type="statistics",
        difficulty="high_school",
        supported_operations=["calculate", "find_value"],
    ),
    MathConcept(
        concept_id="math.probability",
        topic="probability",
        name="Probability & Distributions",
        aliases=["probability", "chance", "sample space", "conditional probability", "bayes theorem", "binomial distribution"],
        keywords=["probability", "chance", "coin toss", "dice", "card", "conditional probability", "independent events", "bayes"],
        definition="Numerical description of how likely an event is to occur, ranging from 0 (impossible) to 1 (certain).",
        formula="P(E) = n(E) / n(S); P(A ∪ B) = P(A) + P(B) - P(A ∩ B); P(A|B) = P(A ∩ B) / P(B)",
        examples=["probability of getting a head in single coin toss", "probability of rolling an even number on a 6-sided die", "probability of drawing an ace from a deck of 52 cards"],
        solver_type="probability",
        difficulty="high_school",
        supported_operations=["calculate", "find_value"],
    ),

    # ---------------- Set Theory & Logic (PUC / Grade 11) ----------------
    MathConcept(
        concept_id="math.set_theory",
        topic="set_theory",
        name="Set Theory & Relations",
        aliases=["sets", "set theory", "union", "intersection", "subset", "venn diagram", "cartesian product", "power set"],
        keywords=["union", "intersection", "set", "subset", "power set", "cartesian product", "complement", "venn"],
        definition="Study of collections of well-defined distinct objects and their boolean algebraic operations.",
        formula="n(A ∪ B) = n(A) + n(B) - n(A ∩ B); A ∩ B = elements in both A and B; A ∪ B = elements in either A or B",
        examples=["union of {1, 2, 3} and {3, 4, 5}", "intersection of {a, b, c} and {b, c, d}", "power set of {1, 2}"],
        solver_type="set_theory",
        difficulty="puc",
        supported_operations=["calculate", "evaluate"],
    ),
]


class ConceptKnowledgeBase:
    """Indexed catalog allowing fast multi-keyword and alias matching."""

    def __init__(self) -> None:
        self.concepts = CONCEPTS_CATALOG
        self._concept_map = {c.concept_id: c for c in self.concepts}

    def get(self, concept_id: str) -> Optional[MathConcept]:
        """Retrieve concept by unique concept_id."""
        return self._concept_map.get(concept_id)

    def find_by_query(self, query: str) -> list[tuple[MathConcept, float]]:
        """
        Find matching concepts ranked by keyword and alias overlap score.
        """
        q_lower = query.lower()
        results: list[tuple[MathConcept, float]] = []

        for c in self.concepts:
            score = 0.0
            # Direct name/alias match
            if c.name.lower() in q_lower:
                score += 3.0
            for alias in c.aliases:
                if alias.lower() in q_lower:
                    score += 2.0

            # Keywords match
            for kw in c.keywords:
                if f" {kw.lower()} " in f" {q_lower} " or q_lower.startswith(f"{kw.lower()} ") or q_lower.endswith(f" {kw.lower()}"):
                    score += 1.0

            if score > 0.0:
                results.append((c, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results


# Global Knowledge Base
concept_kb = ConceptKnowledgeBase()
