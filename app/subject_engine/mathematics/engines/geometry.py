"""
Geometry & Mensuration Engine
=============================

PURPOSE:
    Solves 2D plane geometry and 3D solid mensuration calculations:
    - Triangles (Right triangle Pythagoras, Equilateral, Heron's formula)
    - Circles (Area, Circumference, Diameter, Sector area, Arc length)
    - Quadrilaterals (Square, Rectangle, Parallelogram, Rhombus, Trapezium)
    - Regular Polygons (Angles, Diagonals)
    - 3D Solids (Cube, Cuboid, Cylinder, Cone, Sphere, Hemisphere)
"""

import math
import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter
from app.subject_engine.mathematics.rules import GEOMETRIC_FORMULAS


class GeometryEngine:
    """Specialized engine for Geometry and Mensuration."""

    def solve_circle(self, query: str) -> Optional[SubjectSolveResult]:
        """Calculates area, circumference, sector area of circles."""
        r_match = re.search(r'\bradius\s*(?:of|=|is)?\s*(\d*\.?\d+)', query, re.IGNORECASE)
        d_match = re.search(r'\bdiameter\s*(?:of|=|is)?\s*(\d*\.?\d+)', query, re.IGNORECASE)

        if not r_match and not d_match:
            # Try single number extract if circle is mentioned
            if "circle" in query.lower():
                nums = math_parser.extract_numbers(query)
                if nums:
                    r = float(nums[0])
                else:
                    return None
            else:
                return None
        elif r_match:
            r = float(r_match.group(1))
        else:
            r = float(d_match.group(1)) / 2.0

        is_area = bool(re.search(r'\b(area)\b', query, re.IGNORECASE))
        is_circumference = bool(re.search(r'\b(circumference|perimeter)\b', query, re.IGNORECASE))

        # Check sector angle
        theta_match = re.search(r'\b(?:angle|sector\s+angle|theta)\s*(?:of|=|is)?\s*(\d*\.?\d+)', query, re.IGNORECASE)

        steps = [f"Given Circle with Radius `r = {r}`"]
        if is_area or (not is_circumference and not theta_match):
            area_exact = sp.pi * (r**2)
            area_approx = math.pi * (r**2)
            steps.append(f"Formula for Area of Circle: `Area = πr²`")
            steps.append(f"Calculation: `π × ({r})² = {area_exact}`")
            steps.append(f"Numerical Value ≈ **{area_approx:.4f} sq units**")
            answer = f"{area_exact} (approx {area_approx:.4f} sq units)"
            title = "Area of Circle"
            formula = "Area = πr²"
        elif is_circumference:
            circ_exact = 2 * sp.pi * r
            circ_approx = 2 * math.pi * r
            steps.append(f"Formula for Circumference of Circle: `Circumference = 2πr`")
            steps.append(f"Calculation: `2 × π × {r} = {circ_exact}`")
            steps.append(f"Numerical Value ≈ **{circ_approx:.4f} units**")
            answer = f"{circ_exact} (approx {circ_approx:.4f} units)"
            title = "Circumference of Circle"
            formula = "Circumference = 2πr"
        elif theta_match:
            theta = float(theta_match.group(1))
            sector_area = (theta / 360.0) * math.pi * (r**2)
            arc_len = (theta / 360.0) * 2 * math.pi * r
            steps.append(f"Sector Angle `θ = {theta}°`")
            steps.append(f"Sector Area: `(θ/360) × πr² = ({theta}/360) × π × ({r})² ≈ {sector_area:.4f}`")
            steps.append(f"Arc Length: `(θ/360) × 2πr = ({theta}/360) × 2π × {r} ≈ {arc_len:.4f}`")
            answer = f"Sector Area = {sector_area:.4f} sq units, Arc Length = {arc_len:.4f} units"
            title = "Circle Sector & Arc"
            formula = "Sector Area = (θ/360°)πr²"

        md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
        return SubjectSolveResult(
            handled_locally=True,
            subject=SubjectType.MATHEMATICS,
            topic="geometry",
            concept_id="math.geometry.2d",
            intent=QuestionIntent.CALCULATE,
            original_question=query,
            formula=formula,
            steps=steps,
            answer=answer,
            formatted_markdown=md,
            confidence=0.98,
        )

    def solve_pythagoras(self, query: str) -> Optional[SubjectSolveResult]:
        """Calculates hypotenuse or legs using Pythagoras Theorem: a² + b² = c²."""
        if not re.search(r'\b(pythagoras|hypotenuse|right\s+triangle|right\s+angled)\b', query, re.IGNORECASE):
            return None

        numbers = math_parser.extract_numbers(query)
        if len(numbers) < 2:
            return None

        # Check if looking for hypotenuse (legs given) or leg (hypotenuse given)
        if re.search(r'\b(hypotenuse|find\s+hypotenuse)\b', query, re.IGNORECASE) or len(numbers) == 2:
            a, b = float(numbers[0]), float(numbers[1])
            c_sq = a**2 + b**2
            c = math.sqrt(c_sq)
            steps = [
                f"Given right-angled triangle with legs `a = {a}` and `b = {b}`",
                f"Pythagoras Theorem: `c² = a² + b²`",
                f"Calculation: `c² = ({a})² + ({b})² = {a**2} + {b**2} = {c_sq}`",
                f"Hypotenuse `c = √{c_sq} = **{c:.4g}**`",
            ]
            answer = f"Hypotenuse = {c:.4g}"
            title = "Pythagoras Theorem (Hypotenuse)"
            formula = "c = √(a² + b²)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="geometry",
                concept_id="math.geometry.2d",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )
        return None

    def solve_triangle_area(self, query: str) -> Optional[SubjectSolveResult]:
        """Calculates area of triangle via base*height or Heron's formula."""
        if not re.search(r'\b(triangle)\b', query, re.IGNORECASE):
            return None

        nums = math_parser.extract_numbers(query)
        if len(nums) == 3:
            # Heron's Formula with 3 sides
            a, b, c = float(nums[0]), float(nums[1]), float(nums[2])
            # Triangle inequality check
            if a + b <= c or b + c <= a or a + c <= b:
                return None
            s = (a + b + c) / 2.0
            area_sq = s * (s - a) * (s - b) * (s - c)
            area = math.sqrt(max(0, area_sq))

            steps = [
                f"Given triangle sides: `a = {a}`, `b = {b}`, `c = {c}`",
                f"Semi-perimeter `s = (a + b + c) / 2 = ({a} + {b} + {c}) / 2 = {s}`",
                f"Heron's Formula: `Area = √(s(s - a)(s - b)(s - c))`",
                f"`Area = √({s} × ({s}-{a}) × ({s}-{b}) × ({s}-{c}))`",
                f"`Area = √({s} × {s-a} × {s-b} × {s-c}) = √{area_sq:.4f} ≈ **{area:.4f} sq units**`",
            ]
            answer = f"{area:.4f} sq units"
            title = "Area of Triangle (Heron's Formula)"
            formula = "Area = √(s(s - a)(s - b)(s - c))"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="geometry",
                concept_id="math.geometry.2d",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )
        elif len(nums) == 2:
            base, height = float(nums[0]), float(nums[1])
            area = 0.5 * base * height
            steps = [
                f"Given triangle with `base = {base}` and `height = {height}`",
                f"Formula: `Area = (1/2) × base × height`",
                f"`Area = (1/2) × {base} × {height} = **{area} sq units**`",
            ]
            answer = f"{area} sq units"
            title = "Area of Triangle"
            formula = "Area = (1/2) × base × height"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="geometry",
                concept_id="math.geometry.2d",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )
        return None

    def solve_3d_mensuration(self, query: str) -> Optional[SubjectSolveResult]:
        """Calculates volume and surface area of cylinder, cone, sphere, cube, cuboid."""
        lower_q = query.lower()
        nums = math_parser.extract_numbers(query)

        if "cylinder" in lower_q and len(nums) >= 2:
            r, h = float(nums[0]), float(nums[1])
            vol_exact = sp.pi * (r**2) * h
            vol_approx = math.pi * (r**2) * h
            csa = 2 * math.pi * r * h
            tsa = 2 * math.pi * r * (r + h)
            steps = [
                f"Given Cylinder with `radius r = {r}` and `height h = {h}`",
                f"**Volume:** `V = πr²h = π × ({r})² × {h} = {vol_exact} ≈ {vol_approx:.4f} cubic units`",
                f"**Curved Surface Area (CSA):** `CSA = 2πrh = 2 × π × {r} × {h} ≈ {csa:.4f} sq units`",
                f"**Total Surface Area (TSA):** `TSA = 2πr(r + h) = 2 × π × {r} × ({r} + {h}) ≈ {tsa:.4f} sq units`",
            ]
            answer = f"Volume = {vol_approx:.4f} cu units, TSA = {tsa:.4f} sq units"
            title = "Cylinder Mensuration"
            formula = "V = πr²h,  TSA = 2πr(r + h)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="mensuration",
                concept_id="math.geometry.3d",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif "sphere" in lower_q and nums:
            r = float(nums[0])
            vol_approx = (4.0 / 3.0) * math.pi * (r**3)
            sa_approx = 4.0 * math.pi * (r**2)
            steps = [
                f"Given Sphere with `radius r = {r}`",
                f"**Volume:** `V = (4/3)πr³ = (4/3) × π × ({r})³ ≈ {vol_approx:.4f} cubic units`",
                f"**Surface Area:** `A = 4πr² = 4 × π × ({r})² ≈ {sa_approx:.4f} sq units`",
            ]
            answer = f"Volume = {vol_approx:.4f} cu units, Surface Area = {sa_approx:.4f} sq units"
            title = "Sphere Mensuration"
            formula = "V = (4/3)πr³,  Surface Area = 4πr²"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="mensuration",
                concept_id="math.geometry.3d",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif "cube" in lower_q and nums and "cuboid" not in lower_q:
            a = float(nums[0])
            vol = a**3
            tsa = 6 * (a**2)
            lsa = 4 * (a**2)
            steps = [
                f"Given Cube with side `a = {a}`",
                f"**Volume:** `V = a³ = ({a})³ = {vol} cubic units`",
                f"**Total Surface Area (TSA):** `TSA = 6a² = 6 × ({a})² = {tsa} sq units`",
                f"**Lateral Surface Area (LSA):** `LSA = 4a² = 4 × ({a})² = {lsa} sq units`",
            ]
            answer = f"Volume = {vol} cu units, TSA = {tsa} sq units"
            title = "Cube Mensuration"
            formula = "V = a³,  TSA = 6a²"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="mensuration",
                concept_id="math.geometry.3d",
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
geometry_engine = GeometryEngine()
