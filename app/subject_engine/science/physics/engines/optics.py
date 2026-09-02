"""
Physics Optics Engine
=====================

PURPOSE:
    Solves Power of Lens (P = 1/f in Diopters), Mirror Formula, Lens Formula,
    and Snell's Law calculations.
"""

from typing import Optional
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.physics.parser import ParsedPhysicsQuery


class OpticsEngine:
    """Solves geometric and physical optics numericals."""

    def solve(self, parsed: ParsedPhysicsQuery) -> Optional[SubjectSolveResult]:
        vars_dict = parsed.variables
        target = parsed.target_quantity
        raw_q = parsed.original_query
        lower_q = raw_q.lower()

        # Case 1: Power of lens P = 1 / f (meters)
        if "power" in lower_q and ("focal length" in lower_q or "lens" in lower_q or "focal_length" in vars_dict):
            if "focal_length" in vars_dict or "distance" in vars_dict:
                f_obj = vars_dict.get("focal_length") or vars_dict.get("distance")
                f_meters = f_obj.value
                if f_meters != 0:
                    p_val = 1.0 / f_meters
                    lens_type = "Convex (Converging) Lens" if p_val > 0 else "Concave (Diverging) Lens"
                    givens = {
                        "Focal Length (f)": f"{f_meters} m ({f_meters * 100:.4g} cm)",
                    }
                    steps = [
                        "Power of Lens Formula: `P = 1 / f (in meters)`",
                        f"Substitute: `P = 1 / ({f_meters} m)`",
                        f"Calculate: `P = **{p_val:+.4g} Diopters (D)**`",
                        f"Lens Nature: **{lens_type}**",
                    ]
                    answer = f"{p_val:+.4g} D"
                    md = science_formatter.format_numerical_solution(
                        problem=raw_q,
                        givens=givens,
                        formula="P = 1 / f (in meters)",
                        calculation_steps=steps,
                        final_answer=answer,
                        unit="D",
                        topic_title="Power of Lens Calculation",
                    )
                    return SubjectSolveResult(
                        handled_locally=True,
                        subject=SubjectType.PHYSICS,
                        topic="optics",
                        concept_id="physics.optics.light_laws",
                        intent=QuestionIntent.CALCULATE,
                        original_question=raw_q,
                        formula="P = 1 / f",
                        steps=steps,
                        answer=answer,
                        formatted_markdown=md,
                        unit="D",
                        confidence=0.99,
                    )

        return None


# Global instance
optics_engine = OpticsEngine()
