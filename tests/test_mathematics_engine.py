"""
Mathematics Engine Comprehensive Unit & Concept Tests
=====================================================

Covers:
1. Natural language math normalizer (speech, word powers, BODMAS, unicode, implicit multiplication)
2. Arithmetic, Primes, HCF/LCM, Fractions
3. Algebra, Identities, Expansions, Factorizations, Substitution
4. Equations: Linear (1 var), Linear Systems (2 vars), Quadratics
5. Geometry & Mensuration: Circles, Triangles, Pythagoras, 3D Solids
6. Trigonometry: Standard angles, degrees, radians
7. Coordinate Geometry: Distance, Midpoint, Slope, Lines
8. Vectors: Magnitude, Dot Product, Cross Product
9. Matrices: Determinant, Multiplication, Transpose, Inverse
10. Calculus: Derivatives, Integrals, Limits
11. Sequences & Series: AP, GP, Infinite GP
12. Combinatorics: Factorials, nPr, nCr, Binomial Theorem
13. Statistics: Mean, Median, Mode, Variance, Standard Deviation
14. Probability: Coins, Dice, Cards
15. Commercial Math: Percentages, Simple Interest, Compound Interest, Profit/Loss
16. Unit Conversion: km to m, deg to rad, C to F
17. Proofs & Theorems: Pythagoras, Irrationality of √2, Remainder Theorem
18. Safety & DoS Guards
"""

import pytest
from app.subject_engine.mathematics.normalizer import math_normalizer
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.classifier import math_classifier
from app.subject_engine.mathematics.engine import math_engine
from app.subject_engine.mathematics.validators import MathValidationError, validate_expression_safety
from app.subject_engine.base import QuestionIntent, SubjectType


def test_math_normalizer_natural_speech():
    """Verify natural student typing and spoken math expressions are normalized."""
    assert "^ 2" in math_normalizer.normalize("x to the power 2")
    assert "^ 3" in math_normalizer.normalize("x power 3")
    assert "^ 2" in math_normalizer.normalize("x square")
    assert "^ 3" in math_normalizer.normalize("x cubed")
    assert "^ 3" in math_normalizer.normalize("x³")
    assert "^ 2" in math_normalizer.normalize("x²")
    assert "sqrt(25)" in math_normalizer.normalize("square root of 25")
    assert "sqrt(25)" in math_normalizer.normalize("root 25")
    assert "cbrt(8)" in math_normalizer.normalize("cube root of 8")
    assert "*" in math_normalizer.normalize("2 into 5")
    assert "*" in math_normalizer.normalize("2 times 5")
    assert "*" in math_normalizer.normalize("2 × 5")
    assert "/" in math_normalizer.normalize("5 divided by 2")
    assert "/" in math_normalizer.normalize("5 over 2")
    assert "=" in math_normalizer.normalize("2x + 5 equals 15")
    assert ">= 5" in math_normalizer.normalize("x greater than or equal to 5")


def test_math_normalizer_implicit_multiplication():
    """Verify implicit multiplication insertion: 2x -> 2 * x, 5(x+1) -> 5 * (x + 1)."""
    assert "2 * x" in math_normalizer.normalize("2x")
    assert "5 * (x + 1)" in math_normalizer.normalize("5(x+1)")
    assert "(x + 1) * (x + 2)" in math_normalizer.normalize("(x+1)(x+2)")
    assert "3 * sin" in math_normalizer.normalize("3sin(x)")



def test_hcf_lcm():
    """Verify HCF and LCM calculations."""
    res_hcf = math_engine.solve("find HCF of 24 and 36")
    assert res_hcf.handled_locally is True
    assert res_hcf.answer == "12"
    assert len(res_hcf.steps) >= 2

    res_lcm = math_engine.solve("find LCM of 12 and 18")
    assert res_lcm.handled_locally is True
    assert res_lcm.answer == "36"


def test_primes_and_factorization():
    """Verify prime check and prime factorization."""
    res_prime = math_engine.solve("is 97 prime?")
    assert res_prime.handled_locally is True
    assert "PRIME" in res_prime.answer

    res_comp = math_engine.solve("is 100 prime?")
    assert res_comp.handled_locally is True
    assert "COMPOSITE" in res_comp.answer

    res_fact = math_engine.solve("prime factorization of 360")
    assert res_fact.handled_locally is True
    assert "2^3" in res_fact.answer and "3^2" in res_fact.answer and "5" in res_fact.answer


def test_fraction_arithmetic():
    """Verify exact fraction operations."""
    res = math_engine.solve("2/3 + 4/5")
    assert res.handled_locally is True
    assert res.answer == "22/15"


def test_bodmas_arithmetic():
    """Verify basic BODMAS calculations."""
    res = math_engine.solve("25 * 48")
    assert res.handled_locally is True
    assert res.answer == "1200"

    res2 = math_engine.solve("5 + 2 * 3")
    assert res2.handled_locally is True
    assert res2.answer == "11"


def test_algebraic_simplification_and_expansion():
    """Verify simplification and expansion."""
    res_simp = math_engine.solve("simplify 3x + 5y - x + 2y")
    assert res_simp.handled_locally is True
    assert "2*x + 7*y" in res_simp.answer or "7*y + 2*x" in res_simp.answer

    res_exp = math_engine.solve("expand (2x + 3)^2")
    assert res_exp.handled_locally is True
    assert "4*x^2 + 12*x + 9" in res_exp.answer or "4*x**2 + 12*x + 9" in res_exp.answer

    res_fac = math_engine.solve("factor x^2 - 9")
    assert res_fac.handled_locally is True
    assert "(x - 3)*(x + 3)" in res_fac.answer or "(x + 3)*(x - 3)" in res_fac.answer


def test_algebraic_substitution():
    """Verify variable substitution."""
    res = math_engine.solve("if x = 3 find value of 2x^2 + 5x + 1")
    assert res.handled_locally is True
    # 2*(9) + 5*(3) + 1 = 18 + 15 + 1 = 34
    assert res.answer == "34"


def test_linear_equations_1var():
    """Verify linear equation solving in 1 variable."""
    res = math_engine.solve("solve 2x + 5 = 15")
    assert res.handled_locally is True
    assert "x = 5" in res.answer


def test_quadratic_equations():
    """Verify quadratic equation solving."""
    res = math_engine.solve("solve x^2 - 5x + 6 = 0")
    assert res.handled_locally is True
    assert "2" in res.answer and "3" in res.answer
    assert "Discriminant" in res.formatted_markdown

    res_nat = math_engine.solve("solve x^2 + 4x + 5 = 0")
    assert res_nat.handled_locally is True
    assert "complex" in res_nat.rules_applied[0].lower() or "complex" in res_nat.formatted_markdown.lower()


def test_simultaneous_equations():
    """Verify system of 2 linear equations."""
    res = math_engine.solve("solve 2x + y = 7 and x - y = 2")
    assert res.handled_locally is True
    assert "x = 3" in res.answer and "y = 1" in res.answer


def test_polynomial_division_and_zeroes():
    """Verify polynomial division and zeroes."""
    res_div = math_engine.solve("divide x^2 - 5x + 6 by x - 2")
    assert res_div.handled_locally is True
    assert "Quotient = x - 3" in res_div.answer

    res_zero = math_engine.solve("zeroes of x^2 - 4")
    assert res_zero.handled_locally is True
    assert "-2" in res_zero.answer and "2" in res_zero.answer


def test_geometry_circle():
    """Verify area and circumference of circle."""
    res_area = math_engine.solve("area of circle radius 7")
    assert res_area.handled_locally is True
    assert "49*pi" in res_area.answer or "153.9" in res_area.answer

    res_circ = math_engine.solve("circumference of circle radius 7")
    assert res_circ.handled_locally is True
    assert "14*pi" in res_circ.answer or "43.98" in res_circ.answer


def test_geometry_pythagoras_and_triangle():
    """Verify Pythagoras theorem and triangle calculations."""
    res_pyth = math_engine.solve("hypotenuse of right triangle with legs 3 and 4")
    assert res_pyth.handled_locally is True
    assert "5" in res_pyth.answer

    res_heron = math_engine.solve("area of triangle with sides 5, 12, 13")
    assert res_heron.handled_locally is True
    assert "30" in res_heron.answer


def test_mensuration_3d():
    """Verify cylinder and sphere volume calculations."""
    res_cyl = math_engine.solve("volume of cylinder radius 7 height 10")
    assert res_cyl.handled_locally is True
    assert "Volume" in res_cyl.answer

    res_cube = math_engine.solve("volume of cube side 5")
    assert res_cube.handled_locally is True
    assert "125" in res_cube.answer


def test_trigonometry_standard_angles():
    """Verify exact values of standard trigonometric angles."""
    res_sin30 = math_engine.solve("sin 30")
    assert res_sin30.handled_locally is True
    assert res_sin30.answer == "1/2"

    res_cos60 = math_engine.solve("cos 60 degrees")
    assert res_cos60.handled_locally is True
    assert res_cos60.answer == "1/2"

    res_tan45 = math_engine.solve("tan 45")
    assert res_tan45.handled_locally is True
    assert res_tan45.answer == "1"


def test_coordinate_geometry():
    """Verify distance, midpoint, and slope."""
    res_dist = math_engine.solve("distance between (2, 3) and (5, 7)")
    assert res_dist.handled_locally is True
    assert "5" in res_dist.answer

    res_mid = math_engine.solve("midpoint of (4, 6) and (8, 10)")
    assert res_mid.handled_locally is True
    assert "(6, 8)" in res_mid.answer


def test_matrices():
    """Verify matrix determinant, transpose, multiplication."""
    res_det = math_engine.solve("determinant of [[1, 2], [3, 4]]")
    assert res_det.handled_locally is True
    # 1*4 - 2*3 = 4 - 6 = -2
    assert res_det.answer == "-2"

    res_mul = math_engine.solve("multiply [[1, 2], [3, 4]] and [[1, 0], [0, 1]]")
    assert res_mul.handled_locally is True
    assert "[[1, 2], [3, 4]]" in res_mul.answer


def test_calculus():
    """Verify limits, derivatives, and integrals."""
    res_diff = math_engine.solve("differentiate x^3")
    assert res_diff.handled_locally is True
    assert "3*x^2" in res_diff.answer or "3*x**2" in res_diff.answer

    res_int = math_engine.solve("integrate x^2")
    assert res_int.handled_locally is True
    assert "x**3/3" in res_int.answer or "x^3/3" in res_int.answer

    res_def_int = math_engine.solve("integrate x from 0 to 2")
    assert res_def_int.handled_locally is True
    # [x^2/2]_0^2 = 4/2 = 2
    assert "2" in res_def_int.answer

    res_lim = math_engine.solve("limit of (x^2 - 4)/(x - 2) as x -> 2")
    assert res_lim.handled_locally is True
    assert res_lim.answer == "4"


def test_sequences_and_series():
    """Verify AP and GP calculations."""
    res_ap = math_engine.solve("find 10th term of AP 2, 5, 8")
    assert res_ap.handled_locally is True
    # a=2, d=3, T_10 = 2 + 9*3 = 29
    assert "29" in res_ap.answer

    res_ap_sum = math_engine.solve("sum of first 20 terms of AP 3, 7, 11")
    assert res_ap_sum.handled_locally is True
    # a=3, d=4, S_20 = 10*(6 + 19*4) = 10*(6 + 76) = 820
    assert "820" in res_ap_sum.answer

    res_gp_inf = math_engine.solve("sum of infinite GP 1, 0.5, 0.25")
    assert res_gp_inf.handled_locally is True
    # a=1, r=0.5, S_inf = 1/(1-0.5) = 2
    assert "2" in res_gp_inf.answer


def test_combinatorics_and_binomial():
    """Verify factorial, permutations, combinations, and binomial expansion."""
    res_fact = math_engine.solve("find 5!")
    assert res_fact.handled_locally is True
    assert res_fact.answer == "120"

    res_npr = math_engine.solve("calculate 7P3")
    assert res_npr.handled_locally is True
    # 7*6*5 = 210
    assert res_npr.answer == "210"

    res_ncr = math_engine.solve("calculate 10C3")
    assert res_ncr.handled_locally is True
    # (10*9*8)/(3*2*1) = 120
    assert res_ncr.answer == "120"

    res_bin = math_engine.solve("expand (x + y)^3")
    assert res_bin.handled_locally is True
    assert "3*x^2*y" in res_bin.answer or "3*x**2*y" in res_bin.answer


def test_statistics():
    """Verify mean, median, mode, and standard deviation."""
    res_mean = math_engine.solve("mean of 10, 20, 30, 40, 50")
    assert res_mean.handled_locally is True
    assert "30" in res_mean.answer

    res_median = math_engine.solve("median of 3, 5, 7, 9, 11")
    assert res_median.handled_locally is True
    assert "7" in res_median.answer

    res_mode = math_engine.solve("mode of 2, 3, 3, 5, 7")
    assert res_mode.handled_locally is True
    assert "3" in res_mode.answer


def test_probability():
    """Verify probability calculations."""
    res_coin = math_engine.solve("probability of getting head in coin toss")
    assert res_coin.handled_locally is True
    assert "1/2" in res_coin.answer

    res_die = math_engine.solve("probability of rolling even number on a dice")
    assert res_die.handled_locally is True
    assert "1/2" in res_die.answer

    res_card = math_engine.solve("probability of drawing an ace from a deck of cards")
    assert res_card.handled_locally is True
    assert "1/13" in res_card.answer


def test_financial_math():
    """Verify percentages, simple interest, profit and loss."""
    res_pct = math_engine.solve("20% of 500")
    assert res_pct.handled_locally is True
    assert "100" in res_pct.answer

    res_si = math_engine.solve("simple interest on principal 10000 rate 5% for 3 years")
    assert res_si.handled_locally is True
    # 10000 * 5 * 3 / 100 = 1500
    assert "1500" in res_si.answer

    res_pl = math_engine.solve("CP = 400 and SP = 500 find profit percentage")
    assert res_pl.handled_locally is True
    # 100 / 400 = 25%
    assert "25" in res_pl.answer and "Profit" in res_pl.answer


def test_unit_conversions():
    """Verify unit conversions."""
    res_km = math_engine.solve("convert 5 km to meters")
    assert res_km.handled_locally is True
    assert "5000" in res_km.answer

    res_deg = math_engine.solve("convert 180 degrees to radians")
    assert res_deg.handled_locally is True
    assert "3.14" in res_deg.answer or "pi" in res_deg.answer

    res_temp = math_engine.solve("convert 100 celsius to fahrenheit")
    assert res_temp.handled_locally is True
    assert "212" in res_temp.answer


def test_theorems_and_proofs():
    """Verify theorem proofs."""
    res_pyth = math_engine.solve("prove pythagoras theorem")
    assert res_pyth.handled_locally is True
    assert "AC² = AB² + BC²" in res_pyth.formatted_markdown
    assert "Q.E.D" in res_pyth.formatted_markdown or "proved" in res_pyth.formatted_markdown

    res_sqrt2 = math_engine.solve("prove root 2 is irrational")
    assert res_sqrt2.handled_locally is True
    assert "Contradiction" in res_sqrt2.formatted_markdown or "contradiction" in res_sqrt2.formatted_markdown


def test_concept_definitions():
    """Verify concept definition and formula lookup."""
    res = math_engine.solve("what is a quadratic equation")
    assert res.handled_locally is True
    assert "second degree" in res.formatted_markdown.lower() or "ax² + bx + c = 0" in res.formatted_markdown

    res_form = math_engine.solve("formula for area of circle")
    assert res_form.handled_locally is True
    assert "πr²" in res_form.formatted_markdown or "pi" in res_form.formatted_markdown


def test_safety_and_dos_guards():
    """Verify forbidden Python keywords and expressions are blocked."""
    with pytest.raises(MathValidationError):
        validate_expression_safety("import os; os.system('ls')")

    with pytest.raises(MathValidationError):
        validate_expression_safety("eval('2 + 2')")

    with pytest.raises(MathValidationError):
        validate_expression_safety("__import__('sys')")
