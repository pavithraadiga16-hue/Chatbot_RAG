"""
Physics Electricity & Circuits Engine
=====================================

PURPOSE:
    Solves Ohm's Law (V = IR), Electrical Power (P = VI = I²R = V²/R),
    Resistors in Series/Parallel, and Capacitance calculations.
"""

from typing import Optional
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.physics.parser import ParsedPhysicsQuery


class ElectricityEngine:
    """Calculates electrical quantities deterministically."""

    def solve(self, parsed: ParsedPhysicsQuery) -> Optional[SubjectSolveResult]:
        vars_dict = parsed.variables
        target = parsed.target_quantity
        raw_q = parsed.original_query

        # Case 1: Voltage V = I * R
        if target == "voltage" and "current" in vars_dict and "resistance" in vars_dict:
            i_val = vars_dict["current"].value
            r_val = vars_dict["resistance"].value
            v_val = i_val * r_val
            givens = {
                "Electric Current (I)": f"{i_val} A",
                "Resistance (R)": f"{r_val} Ω",
            }
            steps = [
                "Apply Ohm's Law: `V = I × R`",
                f"Substitute: `V = {i_val} A × {r_val} Ω`",
                f"Calculate: `V = **{v_val:.4g} Volts (V)**`",
            ]
            answer = f"{v_val:.4g} V"
            md = science_formatter.format_numerical_solution(
                problem=raw_q,
                givens=givens,
                formula="V = I · R",
                calculation_steps=steps,
                final_answer=answer,
                unit="V",
                topic_title="Ohm's Law: Voltage Calculation",
            )
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.PHYSICS,
                topic="electricity",
                concept_id="physics.electricity.ohm_circuits",
                intent=QuestionIntent.CALCULATE,
                original_question=raw_q,
                formula="V = I · R",
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                unit="V",
                confidence=0.99,
            )

        # Case 2: Current I = V / R
        if target == "current" and "voltage" in vars_dict and "resistance" in vars_dict:
            v_val = vars_dict["voltage"].value
            r_val = vars_dict["resistance"].value
            if r_val != 0:
                i_val = v_val / r_val
                givens = {
                    "Voltage / Potential Difference (V)": f"{v_val} V",
                    "Resistance (R)": f"{r_val} Ω",
                }
                steps = [
                    "Apply Ohm's Law: `I = V / R`",
                    f"Substitute: `I = {v_val} V / {r_val} Ω`",
                    f"Calculate: `I = **{i_val:.4g} Amperes (A)**`",
                ]
                answer = f"{i_val:.4g} A"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="I = V / R",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="A",
                    topic_title="Ohm's Law: Current Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="electricity",
                    concept_id="physics.electricity.ohm_circuits",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="I = V / R",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="A",
                    confidence=0.99,
                )

        # Case 3: Resistance R = V / I
        if target == "resistance" and "voltage" in vars_dict and "current" in vars_dict:
            v_val = vars_dict["voltage"].value
            i_val = vars_dict["current"].value
            if i_val != 0:
                r_val = v_val / i_val
                givens = {
                    "Voltage (V)": f"{v_val} V",
                    "Current (I)": f"{i_val} A",
                }
                steps = [
                    "Apply Ohm's Law: `R = V / I`",
                    f"Substitute: `R = {v_val} V / {i_val} A`",
                    f"Calculate: `R = **{r_val:.4g} Ohms (Ω)**`",
                ]
                answer = f"{r_val:.4g} Ω"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula="R = V / I",
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="Ω",
                    topic_title="Ohm's Law: Resistance Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="electricity",
                    concept_id="physics.electricity.ohm_circuits",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula="R = V / I",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="Ω",
                    confidence=0.99,
                )

        # Case 4: Electrical Power P = V * I or I^2 * R
        if target == "power" and ("voltage" in vars_dict or "current" in vars_dict or "resistance" in vars_dict):
            p_val = None
            formula = ""
            steps = []
            givens = {}
            if "voltage" in vars_dict and "current" in vars_dict:
                v = vars_dict["voltage"].value
                i = vars_dict["current"].value
                p_val = v * i
                formula = "P = V · I"
                givens = {"Voltage (V)": f"{v} V", "Current (I)": f"{i} A"}
                steps = [
                    "Electrical Power Formula: `P = V × I`",
                    f"Substitute: `P = {v} V × {i} A`",
                    f"Calculate: `P = **{p_val:.4g} Watts (W)**`",
                ]
            elif "current" in vars_dict and "resistance" in vars_dict:
                i = vars_dict["current"].value
                r = vars_dict["resistance"].value
                p_val = (i ** 2) * r
                formula = "P = I² · R"
                givens = {"Current (I)": f"{i} A", "Resistance (R)": f"{r} Ω"}
                steps = [
                    "Electrical Power (Joule Heating) Formula: `P = I² × R`",
                    f"Substitute: `P = ({i} A)² × {r} Ω`",
                    f"Calculate: `P = **{p_val:.4g} Watts (W)**`",
                ]

            if p_val is not None:
                answer = f"{p_val:.4g} W"
                md = science_formatter.format_numerical_solution(
                    problem=raw_q,
                    givens=givens,
                    formula=formula,
                    calculation_steps=steps,
                    final_answer=answer,
                    unit="W",
                    topic_title="Electrical Power Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="electricity",
                    concept_id="physics.electricity.ohm_circuits",
                    intent=QuestionIntent.CALCULATE,
                    original_question=raw_q,
                    formula=formula,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="W",
                    confidence=0.99,
                )

        return None


# Global instance
electricity_engine = ElectricityEngine()
