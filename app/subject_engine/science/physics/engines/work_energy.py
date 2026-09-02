"""
Physics Work, Energy & Power Engine
===================================

PURPOSE:
    Solves Work (W = F·d), Kinetic Energy (KE = 1/2 m v²),
    Potential Energy (PE = m g h), and Power (P = W / t).
"""

from typing import Optional
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.physics.parser import ParsedPhysicsQuery


class WorkEnergyEngine:
    """Calculates work, kinetic energy, potential energy, and power."""

    def solve(self, parsed: ParsedPhysicsQuery) -> Optional[SubjectSolveResult]:
        vars_dict = parsed.variables
        target = parsed.target_quantity
        raw_q = parsed.original_query

        # Case 1: Kinetic Energy KE = 0.5 * m * v^2
        if target == "kinetic_energy" or ("mass" in vars_dict and "velocity" in vars_dict and "kinetic" in raw_q.lower()):
            if "mass" in vars_dict and "velocity" in vars_dict:
                m = vars_dict["mass"].value
                v = vars_dict["velocity"].value
                ke_val = 0.5 * m * (v ** 2)
                givens = {
                    "Mass (m)": f"{m} kg",
                    "Velocity (v)": f"{v} m/s",
                }
                steps = [
                    "Kinetic Energy Formula: `KE = (1/2) × m × v²`",
                    f"Substitute values: `KE = 0.5 × {m} kg × ({v} m/s)²`",
                    f"`KE = 0.5 × {m} × {v**2}`",
                    f"Calculate: `KE = **{ke_val:.4g} Joules (J)**`",
                ]
                answer = f"{ke_val:.4g} J"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="KE = (1/2) · m · v²",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="J",
                    topic_title="Kinetic Energy Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="work_energy",
                    concept_id="physics.energy.work_power_energy",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="KE = (1/2) · m · v²",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="J",
                    confidence=0.99,
                )

        # Case 2: Potential Energy PE = m * g * h
        if target == "potential_energy" or ("potential" in raw_q.lower() and "mass" in vars_dict):
            if "mass" in vars_dict and "distance" in vars_dict:
                m = vars_dict["mass"].value
                h = vars_dict["distance"].value
                g = 9.8
                pe_val = m * g * h
                givens = {
                    "Mass (m)": f"{m} kg",
                    "Height (h)": f"{h} m",
                    "Acceleration due to gravity (g)": "9.8 m/s²",
                }
                steps = [
                    "Gravitational Potential Energy Formula: `PE = m × g × h`",
                    f"Substitute: `PE = {m} kg × 9.8 m/s² × {h} m`",
                    f"Calculate: `PE = **{pe_val:.4g} Joules (J)**`",
                ]
                answer = f"{pe_val:.4g} J"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="PE = m · g · h",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="J",
                    topic_title="Gravitational Potential Energy Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="work_energy",
                    concept_id="physics.energy.work_power_energy",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="PE = m · g · h",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="J",
                    confidence=0.99,
                )

        # Case 3: Work Done W = F * d
        if target == "work" and "force" in vars_dict and "distance" in vars_dict:
            f_val = vars_dict["force"].value
            d = vars_dict["distance"].value
            w_val = f_val * d
            givens = {
                "Applied Force (F)": f"{f_val} N",
                "Displacement (d)": f"{d} m",
            }
            steps = [
                "Work Done Formula: `W = F × d` (assuming force along direction of displacement)",
                f"Substitute: `W = {f_val} N × {d} m`",
                f"Calculate: `W = **{w_val:.4g} Joules (J)**`",
            ]
            answer = f"{w_val:.4g} J"
            md = science_formatter.format_numerical_solution(
                problem=raw_q,
                givens=givens,
                formula="W = F · d",
                calculation_steps=steps,
                final_answer=answer,
                unit="J",
                topic_title="Work Done Calculation",
            )
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.PHYSICS,
                topic="work_energy",
                concept_id="physics.energy.work_power_energy",
                intent=QuestionIntent.CALCULATE,
                original_question=raw_q,
                formula="W = F · d",
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                unit="J",
                confidence=0.99,
            )

        # Case 4: Power P = W / t
        if target == "power" and "time" in vars_dict:
            t = vars_dict["time"].value
            w_val = None
            if "force" in vars_dict and "distance" in vars_dict:
                w_val = vars_dict["force"].value * vars_dict["distance"].value
            elif "mass" in vars_dict and "distance" in vars_dict:
                w_val = vars_dict["mass"].value * 9.8 * vars_dict["distance"].value

            if w_val is not None and t != 0:
                p_val = w_val / t
                givens = {
                    "Work / Energy (W)": f"{w_val:.4g} J",
                    "Time (t)": f"{t} s",
                }
                steps = [
                    "Power Formula: `P = Work / Time = W / t`",
                    f"Substitute: `P = {w_val:.4g} J / {t} s`",
                    f"Calculate: `P = **{p_val:.4g} Watts (W)**`",
                ]
                answer = f"{p_val:.4g} W"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="P = W / t",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="W",
                    topic_title="Power Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="work_energy",
                    concept_id="physics.energy.work_power_energy",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="P = W / t",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="W",
                    confidence=0.99,
                )

        return None


# Global instance
work_energy_engine = WorkEnergyEngine()
