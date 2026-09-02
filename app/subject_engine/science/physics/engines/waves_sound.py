"""
Physics Waves & Sound Engine
============================

PURPOSE:
    Solves Wave Speed (v = f · λ), Frequency (f = v / λ), Wavelength (λ = v / f),
    Time Period (T = 1 / f), and Echo calculations (d = v·t / 2).
"""

from typing import Optional
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.physics.parser import ParsedPhysicsQuery


class WavesSoundEngine:
    """Solves wave velocity, frequency, wavelength, and echo problems."""

    def solve(self, parsed: ParsedPhysicsQuery) -> Optional[SubjectSolveResult]:
        vars_dict = parsed.variables
        target = parsed.target_quantity
        raw_q = parsed.original_query
        lower_q = raw_q.lower()

        # Case 1: Echo distance calculation
        if "echo" in lower_q and "time" in vars_dict:
            t = vars_dict["time"].value
            v_sound = 343.0  # Speed of sound in air in m/s
            d_val = (v_sound * t) / 2.0
            givens = {
                "Time elapsed for echo return (t)": f"{t} s",
                "Speed of sound in air (v)": f"{v_sound} m/s",
            }
            steps = [
                "In an echo, sound travels to the obstacle and back (total distance = 2d).",
                "Formula: `2d = v × t  ⟹  d = (v × t) / 2`",
                f"Substitute: `d = ({v_sound} m/s × {t} s) / 2`",
                f"Calculate obstacle distance: `d = **{d_val:.4g} meters (m)**`",
            ]
            answer = f"{d_val:.4g} m"
            md = science_formatter.format_numerical_solution(
                problem=raw_q,
                givens=givens,
                formula="d = (v · t) / 2",
                calculation_steps=steps,
                final_answer=answer,
                unit="m",
                topic_title="Echo Distance Calculation",
            )
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.PHYSICS,
                topic="waves_sound",
                concept_id="physics.waves.sound_waves",
                intent=QuestionIntent.CALCULATE,
                original_question=raw_q,
                formula="d = (v · t) / 2",
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                unit="m",
                confidence=0.99,
            )

        # Case 2: Wave velocity v = f * lambda
        if (target == "velocity" or "speed" in lower_q) and "frequency" in vars_dict and "wavelength" in vars_dict:
            f = vars_dict["frequency"].value
            lam = vars_dict["wavelength"].value
            v_val = f * lam
            givens = {
                "Frequency (f)": f"{f} Hz",
                "Wavelength (λ)": f"{lam} m",
            }
            steps = [
                "Universal Wave Equation: `v = f × λ`",
                f"Substitute: `v = {f} Hz × {lam} m`",
                f"Calculate: `v = **{v_val:.4g} m/s**`",
            ]
            answer = f"{v_val:.4g} m/s"
            md = science_formatter.format_numerical_solution(
                problem=raw_q,
                givens=givens,
                formula="v = f · λ",
                calculation_steps=steps,
                final_answer=answer,
                unit="m/s",
                topic_title="Wave Speed Calculation",
            )
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.PHYSICS,
                topic="waves_sound",
                concept_id="physics.waves.sound_waves",
                intent=QuestionIntent.CALCULATE,
                original_question=raw_q,
                formula="v = f · λ",
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                unit="m/s",
                confidence=0.99,
            )

        # Case 3: Wavelength lambda = v / f
        if (target == "wavelength" or "wavelength" in lower_q) and "frequency" in vars_dict and ("velocity" in vars_dict or "speed" in lower_q):
            v_val = vars_dict["velocity"].value if "velocity" in vars_dict else 343.0
            f = vars_dict["frequency"].value
            if f != 0:
                lam_val = v_val / f
                givens = {
                    "Wave Speed (v)": f"{v_val} m/s",
                    "Frequency (f)": f"{f} Hz",
                }
                steps = [
                    "Wave Equation: `λ = v / f`",
                    f"Substitute: `λ = {v_val} m/s / {f} Hz`",
                    f"Calculate: `λ = **{lam_val:.4g} meters (m)**`",
                ]
                answer = f"{lam_val:.4g} m"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="λ = v / f",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="m",
                    topic_title="Wavelength Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="waves_sound",
                    concept_id="physics.waves.sound_waves",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="λ = v / f",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="m",
                    confidence=0.99,
                )

        return None


# Global instance
waves_sound_engine = WavesSoundEngine()
