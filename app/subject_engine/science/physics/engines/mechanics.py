"""
Physics Mechanics Engine
========================

PURPOSE:
    Solves kinematics, Newton's laws (F=ma), momentum, impulse, and centripetal motion.
"""

from typing import Optional
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.physics.parser import ParsedPhysicsQuery


class MechanicsEngine:
    """Calculates mechanics and kinematics problems deterministically."""

    def solve(self, parsed: ParsedPhysicsQuery) -> Optional[SubjectSolveResult]:
        vars_dict = parsed.variables
        target = parsed.target_quantity
        raw_q = parsed.original_query

        # Case 1: Force F = m * a
        if target == "force" and "mass" in vars_dict and "acceleration" in vars_dict:
            m = vars_dict["mass"].value
            a = vars_dict["acceleration"].value
            f_val = m * a
            givens = {
                "Mass (m)": f"{m} kg",
                "Acceleration (a)": f"{a} m/s²",
            }
            steps = [
                "Apply Newton's Second Law of Motion: `F = m × a`",
                f"Substitute values: `F = {m} kg × {a} m/s²`",
                f"Calculate magnitude: `F = **{f_val:.4g} N**`",
            ]
            answer = f"{f_val:.4g} N"
            md = science_formatter.format_numerical_solution(
                problem=raw_q,
                givens=givens,
                formula="F = m · a",
                calculation_steps=steps,
                final_answer=answer,
                unit="N",
                topic_title="Newton's Second Law (Force Calculation)",
            )
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.PHYSICS,
                topic="mechanics",
                concept_id="physics.force.newton_laws",
                intent=QuestionIntent.CALCULATE,
                original_question=raw_q,
                formula="F = m · a",
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                unit="N",
                confidence=0.99,
            )

        # Case 2: Acceleration a = F / m
        if target == "acceleration" and "force" in vars_dict and "mass" in vars_dict:
            f_val = vars_dict["force"].value
            m = vars_dict["mass"].value
            if m != 0:
                a_val = f_val / m
                givens = {
                    "Force (F)": f"{f_val} N",
                    "Mass (m)": f"{m} kg",
                }
                steps = [
                    "Apply Newton's Second Law: `a = F / m`",
                    f"Substitute: `a = {f_val} N / {m} kg`",
                    f"Calculate: `a = **{a_val:.4g} m/s²**`",
                ]
                answer = f"{a_val:.4g} m/s²"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="a = F / m",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="m/s²",
                    topic_title="Acceleration Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="mechanics",
                    concept_id="physics.motion.acceleration",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="a = F / m",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="m/s²",
                    confidence=0.99,
                )

        # Case 3: Velocity / Speed v = s / t
        if target == "velocity" and "distance" in vars_dict and "time" in vars_dict:
            s = vars_dict["distance"].value
            t = vars_dict["time"].value
            if t != 0:
                v_val = s / t
                givens = {
                    "Distance / Displacement (s)": f"{s} m",
                    "Time elapsed (t)": f"{t} s",
                }
                steps = [
                    "Formula: `v = Distance / Time`",
                    f"Substitute: `v = {s} m / {t} s`",
                    f"Calculate: `v = **{v_val:.4g} m/s**` (equivalent to `{(v_val * 3.6):.4g} km/h`)",
                ]
                answer = f"{v_val:.4g} m/s"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="v = s / t",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="m/s",
                    topic_title="Velocity & Speed Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="mechanics",
                    concept_id="physics.motion.velocity",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="v = s / t",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="m/s",
                    confidence=0.99,
                )

        # Case 4: Momentum p = m * v
        if target == "momentum" and "mass" in vars_dict and "velocity" in vars_dict:
            m = vars_dict["mass"].value
            v = vars_dict["velocity"].value
            p_val = m * v
            givens = {
                "Mass (m)": f"{m} kg",
                "Velocity (v)": f"{v} m/s",
            }
            steps = [
                "Linear Momentum Formula: `p = m × v`",
                f"Substitute: `p = {m} kg × {v} m/s`",
                f"Calculate: `p = **{p_val:.4g} kg·m/s**`",
            ]
            answer = f"{p_val:.4g} kg·m/s"
            md = science_formatter.format_numerical_solution(
                problem=raw_q,
                givens=givens,
                formula="p = m · v",
                calculation_steps=steps,
                final_answer=answer,
                unit="kg·m/s",
                topic_title="Linear Momentum Calculation",
            )
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.PHYSICS,
                topic="mechanics",
                concept_id="physics.force.momentum",
                intent=QuestionIntent.CALCULATE,
                original_question=raw_q,
                formula="p = m · v",
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                unit="kg·m/s",
                confidence=0.99,
            )

        return None


# Global instance
mechanics_engine = MechanicsEngine()
