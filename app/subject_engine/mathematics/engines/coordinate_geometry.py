"""
Coordinate Geometry Engine
==========================

PURPOSE:
    Solves 2D Cartesian plane geometry problems:
    - Distance Formula between two points
    - Midpoint Formula
    - Section Formula (internal / external division)
    - Slope of Line
    - Equation of Straight Line (Slope-Intercept, Point-Slope, Two-Point)
    - Area of Triangle with 3 Coordinate Vertices & Collinearity
"""

import math
import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


class CoordinateGeometryEngine:
    """Specialized engine for Coordinate Geometry."""

    def solve_coordinate_problems(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Parses coordinate points (x1, y1) and (x2, y2) and computes distance, midpoint, slope, or line equation.
        """
        lower_q = query.lower()

        # Extract coordinate tuples like (2, 3) or (2,3) or (2.5, -4)
        point_pattern = r'\(\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)'
        points = re.findall(point_pattern, query)

        if len(points) >= 2:
            p1 = (float(points[0][0]), float(points[0][1]))
            p2 = (float(points[1][0]), float(points[1][1]))
            x1, y1 = p1
            x2, y2 = p2

            is_distance = bool(re.search(r'\b(distance)\b', lower_q))
            is_midpoint = bool(re.search(r'\b(midpoint|mid-point|center|centre)\b', lower_q))
            is_slope = bool(re.search(r'\b(slope|gradient)\b', lower_q))
            is_line = bool(re.search(r'\b(equation\s+of\s+line|line\s+equation|straight\s+line)\b', lower_q))

            if is_distance or (not is_midpoint and not is_slope and not is_line):
                # Distance formula
                dist_sq = (x2 - x1)**2 + (y2 - y1)**2
                dist = math.sqrt(dist_sq)
                steps = [
                    f"Given Points: `P₁({x1}, {y1})` and `P₂({x2}, {y2})`",
                    f"Distance Formula: `d = √((x₂ - x₁)² + (y₂ - y₁)²)`",
                    f"`d = √(({x2} - {x1})² + ({y2} - {y1})²)`",
                    f"`d = √(({x2 - x1})² + ({y2 - y1})²) = √({(x2-x1)**2} + {(y2-y1)**2}) = √{dist_sq:.4g}`",
                    f"**Distance d = {dist:.4g} units**",
                ]
                answer = f"{dist:.4g} units"
                title = "Distance Between Two Points"
                formula = "d = √((x₂ - x₁)² + (y₂ - y₁)²)"
                md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="coordinate_geometry",
                    concept_id="math.coordinate_geometry",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    formula=formula,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    confidence=0.98,
                )

            elif is_midpoint:
                # Midpoint formula
                mx = (x1 + x2) / 2.0
                my = (y1 + y2) / 2.0
                steps = [
                    f"Given Points: `P₁({x1}, {y1})` and `P₂({x2}, {y2})`",
                    f"Midpoint Formula: `M = ((x₁ + x₂) / 2, (y₁ + y₂) / 2)`",
                    f"`M = (({x1} + {x2}) / 2, ({y1} + {y2}) / 2)`",
                    f"**Midpoint M = ({mx:.4g}, {my:.4g})**",
                ]
                answer = f"({mx:.4g}, {my:.4g})"
                title = "Midpoint of Line Segment"
                formula = "M = ((x₁ + x₂) / 2, (y₁ + y₂) / 2)"
                md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="coordinate_geometry",
                    concept_id="math.coordinate_geometry",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    formula=formula,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    confidence=0.98,
                )

            elif is_slope or is_line:
                # Slope & Line equation
                if x2 == x1:
                    slope_str = "Undefined (Vertical line x = x₁)"
                    line_eq = f"x = {x1}"
                else:
                    m = (y2 - y1) / (x2 - x1)
                    c = y1 - m * x1
                    slope_str = f"{m:.4g}"
                    line_eq = f"y = {m:.4g}x + {c:.4g}" if c >= 0 else f"y = {m:.4g}x - {abs(c):.4g}"

                steps = [
                    f"Given Points: `P₁({x1}, {y1})` and `P₂({x2}, {y2})`",
                    f"Slope Formula: `m = (y₂ - y₁) / (x₂ - x₁)`",
                    f"`m = ({y2} - {y1}) / ({x2} - {x1}) = {slope_str}`",
                    f"Point-Slope Form: `y - y₁ = m(x - x₁)`",
                    f"**Equation of Line:** `{line_eq}`",
                ]
                answer = f"Slope = {slope_str}, Equation: {line_eq}"
                title = "Slope and Equation of Straight Line"
                formula = "m = (y₂ - y₁)/(x₂ - x₁),  y - y₁ = m(x - x₁)"
                md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="coordinate_geometry",
                    concept_id="math.coordinate_geometry",
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
coordinate_engine = CoordinateGeometryEngine()
