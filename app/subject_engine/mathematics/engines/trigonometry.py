"""
Trigonometry & Inverse Trigonometry Engine
==========================================

PURPOSE:
    Evaluates trigonometric functions, inverse trigonometric functions,
    standard angle values (in degrees and radians), and trigonometric identity simplifications.
"""

import math
import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.mathematics.parser import math_parser
from app.subject_engine.mathematics.formatter import math_formatter


# Standard Exact Trigonometric Table for Degrees
STANDARD_TRIG_DEGREES = {
    ("sin", 0): ("0", 0.0),
    ("sin", 30): ("1/2", 0.5),
    ("sin", 45): ("1/√2", 1 / math.sqrt(2)),
    ("sin", 60): ("√3/2", math.sqrt(3) / 2),
    ("sin", 90): ("1", 1.0),
    ("sin", 180): ("0", 0.0),
    ("sin", 270): ("-1", -1.0),
    ("sin", 360): ("0", 0.0),

    ("cos", 0): ("1", 1.0),
    ("cos", 30): ("√3/2", math.sqrt(3) / 2),
    ("cos", 45): ("1/√2", 1 / math.sqrt(2)),
    ("cos", 60): ("1/2", 0.5),
    ("cos", 90): ("0", 0.0),
    ("cos", 180): ("-1", -1.0),
    ("cos", 270): ("0", 0.0),
    ("cos", 360): ("1", 1.0),

    ("tan", 0): ("0", 0.0),
    ("tan", 30): ("1/√3", 1 / math.sqrt(3)),
    ("tan", 45): ("1", 1.0),
    ("tan", 60): ("√3", math.sqrt(3)),
    ("tan", 90): ("Undefined (∞)", None),
    ("tan", 180): ("0", 0.0),

    ("cot", 0): ("Undefined (∞)", None),
    ("cot", 30): ("√3", math.sqrt(3)),
    ("cot", 45): ("1", 1.0),
    ("cot", 60): ("1/√3", 1 / math.sqrt(3)),
    ("cot", 90): ("0", 0.0),

    ("sec", 0): ("1", 1.0),
    ("sec", 30): ("2/√3", 2 / math.sqrt(3)),
    ("sec", 45): ("√2", math.sqrt(2)),
    ("sec", 60): ("2", 2.0),
    ("sec", 90): ("Undefined (∞)", None),

    ("csc", 0): ("Undefined (∞)", None),
    ("csc", 30): ("2", 2.0),
    ("csc", 45): ("√2", math.sqrt(2)),
    ("csc", 60): ("2/√3", 2 / math.sqrt(3)),
    ("csc", 90): ("1", 1.0),
}


class TrigonometryEngine:
    """Specialized engine for Trigonometric evaluation and simplification."""

    def evaluate_trig(self, query: str) -> Optional[SubjectSolveResult]:
        """
        Evaluates standard trigonometric expressions:
        e.g. 'sin 30', 'cos 60 degrees', 'tan 45', 'sin(pi/6)', 'arctan(1)'
        """
        lower_q = query.lower()

        # Check for standard degree angle pattern: e.g. "sin 30", "cos 60 deg", "tan 45 degrees"
        match = re.search(r'\b(sin|cos|tan|cot|sec|csc|cosec)\s*\(?\s*(\d+)\s*(?:deg|degrees|°)?\s*\)?', lower_q)
        if match:
            func = match.group(1)
            if func == "cosec":
                func = "csc"
            angle = int(match.group(2))

            key = (func, angle % 360)
            if key in STANDARD_TRIG_DEGREES:
                exact_val, dec_val = STANDARD_TRIG_DEGREES[key]
                rad_val = math.radians(angle)
                steps = [
                    f"Trigonometric Function: `{func}({angle}°)`",
                    f"Convert Angle to Radians: `{angle}° × (π/180) = {angle}π/180 = {sp.Rational(angle, 180)}π rad`",
                    f"Standard Angle Value from Trigonometric Table: **`{func}({angle}°) = {exact_val}`**",
                ]
                if dec_val is not None:
                    steps.append(f"Decimal Equivalent ≈ **{dec_val:.6g}**")

                answer = exact_val
                title = f"Trigonometric Evaluation: {func}({angle}°)"
                md = math_formatter.format_solution(query, answer, steps, topic_title=title)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.MATHEMATICS,
                    topic="trigonometry",
                    concept_id="math.trigonometry",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    confidence=0.98,
                )

        # SymPy Symbolic Trig Evaluation
        try:
            # Clean expression
            clean_expr = re.sub(r'\b(calculate|evaluate|find|value\s+of|what\s+is)\b', '', query, flags=re.IGNORECASE).strip()
            parsed = math_parser.parse(clean_expr)
            simplified = sp.trigsimp(parsed)

            steps = [
                f"Given Trigonometric Expression: `{clean_expr}`",
                f"Apply fundamental trigonometric identities: `sin²θ + cos²θ = 1`, `tanθ = sinθ/cosθ`.",
                f"Evaluated / Simplified Result: **`{simplified}`**",
            ]
            answer = str(simplified)
            title = "Trigonometric Simplification"
            md = math_formatter.format_solution(query, answer, steps, topic_title=title)
            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.MATHEMATICS,
                topic="trigonometry",
                concept_id="math.trigonometry",
                intent=QuestionIntent.SIMPLIFY,
                original_question=query,
                steps=steps,
                answer=answer,
                formatted_markdown=md,
                confidence=0.95,
            )
        except Exception:
            return None


# Global instance
trigonometry_engine = TrigonometryEngine()
