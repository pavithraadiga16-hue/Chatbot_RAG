"""
Vector Algebra Engine
=====================

PURPOSE:
    Solves 3D Vector Algebra problems:
    - Magnitude of Vector & Unit Vector
    - Vector Addition & Subtraction
    - Dot Product (Scalar Product)
    - Cross Product (Vector Product)
    - Angle between Vectors & Projections
"""

import math
import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.formatter import math_formatter


class VectorEngine:
    """Specialized engine for Vector Algebra."""

    def parse_vector(self, text: str) -> Optional[tuple[float, float, float]]:
        """Extracts 3D vector components from (x, y, z) or xi + yj + zk."""
        # Check tuple pattern (1, 2, 3)
        tuple_match = re.search(r'\(\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)', text)
        if tuple_match:
            return (float(tuple_match.group(1)), float(tuple_match.group(2)), float(tuple_match.group(3)))

        # Check 2D tuple (x, y)
        tuple2d_match = re.search(r'\(\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)', text)
        if tuple2d_match:
            return (float(tuple2d_match.group(1)), float(tuple2d_match.group(2)), 0.0)

        # Check i, j, k components: e.g. 3i + 4j - 2k
        i_match = re.search(r'([-+]?\d*\.?\d*)\s*i', text)
        j_match = re.search(r'([-+]?\d*\.?\d*)\s*j', text)
        k_match = re.search(r'([-+]?\d*\.?\d*)\s*k', text)

        if i_match or j_match or k_match:
            def _extract_coeff(m) -> float:
                if not m:
                    return 0.0
                raw = m.group(1).replace('+', '').strip()
                if raw == '' or raw == '+':
                    return 1.0
                if raw == '-':
                    return -1.0
                return float(raw)

            x = _extract_coeff(i_match)
            y = _extract_coeff(j_match)
            z = _extract_coeff(k_match)
            return (x, y, z)

        return None

    def solve_vector_operation(self, query: str) -> Optional[SubjectSolveResult]:
        """Handles vector magnitude, dot product, cross product, and angles."""
        lower_q = query.lower()

        # Find all vectors in query
        tuples = re.findall(r'\(\s*[-+]?\d*\.?\d+\s*,\s*[-+]?\d*\.?\d+(?:\s*,\s*[-+]?\d*\.?\d+)?\s*\)', query)
        vectors = [self.parse_vector(t) for t in tuples if self.parse_vector(t) is not None]

        if not vectors:
            v_single = self.parse_vector(query)
            if v_single:
                vectors.append(v_single)

        if not vectors:
            return None

        is_magnitude = bool(re.search(r'\b(magnitude|length|norm|unit\s+vector)\b', lower_q))
        is_dot = bool(re.search(r'\b(dot\s+product|scalar\s+product)\b', lower_q))
        is_cross = bool(re.search(r'\b(cross\s+product|vector\s+product)\b', lower_q))
        is_angle = bool(re.search(r'\b(angle\s+between)\b', lower_q))

        if (is_magnitude or len(vectors) == 1) and not (is_dot or is_cross or is_angle):
            # Single vector magnitude & unit vector
            v = vectors[0]
            mag_sq = v[0]**2 + v[1]**2 + v[2]**2
            mag = math.sqrt(mag_sq)
            steps = [
                f"Given Vector `v = {v[0]}i + {v[1]}j + {v[2]}k`",
                f"Magnitude Formula: `|v| = √(x² + y² + z²)`",
                f"`|v| = √(({v[0]})² + ({v[1]})² + ({v[2]})²) = √({mag_sq}) = **{mag:.4g}**`",
            ]
            if mag > 0:
                unit_v = (v[0]/mag, v[1]/mag, v[2]/mag)
                steps.append(f"Unit Vector: `v̂ = v / |v| = ({unit_v[0]:.4g}i + {unit_v[1]:.4g}j + {unit_v[2]:.4g}k)`")

            answer = f"|v| = {mag:.4g}"
            title = "Vector Magnitude & Unit Vector"
            formula = "|v| = √(x² + y² + z²),  v̂ = v / |v|"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="vectors",
                concept_id="math.vector",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_dot and len(vectors) >= 2:
            a, b = vectors[0], vectors[1]
            dot_val = a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
            steps = [
                f"Vector A = `({a[0]}, {a[1]}, {a[2]})`",
                f"Vector B = `({b[0]}, {b[1]}, {b[2]})`",
                f"Dot Product Formula: `A · B = (a₁b₁ + a₂b₂ + a₃b₃)`",
                f"`A · B = ({a[0]}×{b[0]}) + ({a[1]}×{b[1]}) + ({a[2]}×{b[2]}) = **{dot_val}**`",
            ]
            answer = str(dot_val)
            title = "Scalar Dot Product (A · B)"
            formula = "A · B = a₁b₁ + a₂b₂ + a₃b₃ = |A||B|cos(θ)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="vectors",
                concept_id="math.vector",
                intent=QuestionIntent.CALCULATE,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.98,
            )

        elif is_cross and len(vectors) >= 2:
            a, b = vectors[0], vectors[1]
            cx = a[1]*b[2] - a[2]*b[1]
            cy = a[2]*b[0] - a[0]*b[2]
            cz = a[0]*b[1] - a[1]*b[0]
            cross_v = (cx, cy, cz)

            steps = [
                f"Vector A = `({a[0]}, {a[1]}, {a[2]})`",
                f"Vector B = `({b[0]}, {b[1]}, {b[2]})`",
                f"Cross Product Formula: `A × B = | i j k | / | a₁ a₂ a₃ | / | b₁ b₂ b₃ |`",
                f"`A × B = ({cx})i + ({cy})j + ({cz})k`",
                f"**A × B = `({cx}, {cy}, {cz})`**",
            ]
            answer = f"({cx}, {cy}, {cz}) or {cx}i + {cy}j + {cz}k"
            title = "Vector Cross Product (A × B)"
            formula = "A × B = (a₂b₃ - a₃b₂)i - (a₁b₃ - a₃b₁)j + (a₁b₂ - a₂b₁)k"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="vectors",
                concept_id="math.vector",
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
vector_engine = VectorEngine()
