"""
Unit Conversion Engine
======================

PURPOSE:
    Solves mathematical unit conversions using Pint and conversion tables:
    - Length, Area, Volume, Mass, Time, Speed
    - Angle (Degrees ⟷ Radians)
    - Temperature (Celsius ⟷ Fahrenheit ⟷ Kelvin)
"""

import math
import re
from typing import Optional
import pint

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter

# Initialize Pint Unit Registry
ureg = pint.UnitRegistry()


class UnitConversionEngine:
    """Specialized engine for Physical and Mathematical Unit Conversions."""

    def solve_conversion(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Solves queries like:
        'convert 5 km to meters', 'convert 30 degrees to radians', 'convert 100 celsius to fahrenheit', 'convert 75 km/h to m/s'
        """
        lower_q = query.lower()

        # 1. Degrees to Radians / Radians to Degrees
        deg_rad_match = re.search(r'convert\s+(\d*\.?\d+)\s*(?:deg|degrees|°)\s+to\s+radians', lower_q)
        rad_deg_match = re.search(r'convert\s+(\d*\.?\d+)\s*(?:rad|radians)\s+to\s+degrees', lower_q)

        if deg_rad_match:
            deg = float(deg_rad_match.group(1))
            rad = math.radians(deg)
            steps = [
                f"Angle in Degrees = `{deg}°`",
                f"Conversion Formula: `Radians = Degrees × (π / 180)`",
                f"`{deg}° × (π / 180) = ({deg}/180)π = **{rad:.4g} rad**`",
            ]
            answer = f"{rad:.4g} rad"
            title = "Degrees to Radians Conversion"
            formula = "rad = deg × (π / 180)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title, unit="rad")
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="units",
                concept_id="math.units",
                intent=QuestionIntent.UNIT_CONVERSION,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                unit="rad",
                formatted_markdown=md,
                confidence=0.98,
            )

        elif rad_deg_match:
            rad = float(rad_deg_match.group(1))
            deg = math.degrees(rad)
            steps = [
                f"Angle in Radians = `{rad} rad`",
                f"Conversion Formula: `Degrees = Radians × (180 / π)`",
                f"`{rad} × (180 / π) = **{deg:.4g}°**`",
            ]
            answer = f"{deg:.4g}°"
            title = "Radians to Degrees Conversion"
            formula = "deg = rad × (180 / π)"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title, unit="deg")
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="units",
                concept_id="math.units",
                intent=QuestionIntent.UNIT_CONVERSION,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                unit="deg",
                formatted_markdown=md,
                confidence=0.98,
            )

        # 2. Temperature Conversions
        c_to_f_match = re.search(r'convert\s+(\d*\.?\d+)\s*(?:c|celsius)\s+to\s+(?:f|fahrenheit)', lower_q)
        f_to_c_match = re.search(r'convert\s+(\d*\.?\d+)\s*(?:f|fahrenheit)\s+to\s+(?:c|celsius)', lower_q)

        if c_to_f_match:
            c = float(c_to_f_match.group(1))
            f = (c * 9.0 / 5.0) + 32.0
            steps = [
                f"Given Temperature = `{c}°C`",
                f"Conversion Formula: `°F = (°C × 9/5) + 32`",
                f"`({c} × 9/5) + 32 = {c * 1.8} + 32 = **{f:.2f}°F**`",
            ]
            answer = f"{f:.2f}°F"
            title = "Celsius to Fahrenheit Conversion"
            formula = "°F = (°C × 9/5) + 32"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title, unit="°F")
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="units",
                concept_id="math.units",
                intent=QuestionIntent.UNIT_CONVERSION,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                unit="°F",
                formatted_markdown=md,
                confidence=0.98,
            )

        elif f_to_c_match:
            f = float(f_to_c_match.group(1))
            c = (f - 32.0) * 5.0 / 9.0
            steps = [
                f"Given Temperature = `{f}°F`",
                f"Conversion Formula: `°C = (°F - 32) × 5/9`",
                f"`({f} - 32) × 5/9 = {f - 32} × 5/9 = **{c:.2f}°C**`",
            ]
            answer = f"{c:.2f}°C"
            title = "Fahrenheit to Celsius Conversion"
            formula = "°C = (°F - 32) × 5/9"
            md = math_formatter.format_solution(query, answer, steps, formula=formula, topic_title=title, unit="°C")
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="units",
                concept_id="math.units",
                intent=QuestionIntent.UNIT_CONVERSION,
                original_question=query,
                formula=formula,
                steps=steps,
                answer=answer,
                unit="°C",
                formatted_markdown=md,
                confidence=0.98,
            )

        # 3. Generic Physical Quantity Conversion with Pint (e.g. 5 km to meters, 75 km/h to m/s, 2 hours to seconds)
        pint_match = re.search(r'convert\s+(\d*\.?\d+)\s+([a-zA-Z\/_]+)\s+to\s+([a-zA-Z\/_]+)', lower_q)
        if pint_match:
            val = float(pint_match.group(1))
            src_u = pint_match.group(2).strip()
            dst_u = pint_match.group(3).strip()

            try:
                src_qty = val * ureg(src_u)
                dst_qty = src_qty.to(dst_u)
                res_val = dst_qty.magnitude

                steps = [
                    f"Convert `{val} {src_u}` to `{dst_u}`",
                    f"Conversion Calculation: `{val} {src_u} = **{res_val:.4g} {dst_u}**`",
                ]
                answer = f"{res_val:.4g} {dst_u}"
                title = f"Unit Conversion: {src_u} ⟶ {dst_u}"
                md = math_formatter.format_solution(query, answer, steps, topic_title=title, unit=dst_u)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="units",
                    concept_id="math.units",
                    intent=QuestionIntent.UNIT_CONVERSION,
                    original_question=query,
                    steps=steps,
                    answer=answer,
                    unit=dst_u,
                    formatted_markdown=md,
                    confidence=0.98,
                )
            except Exception:
                pass

        return None


# Global instance
units_engine = UnitConversionEngine()
