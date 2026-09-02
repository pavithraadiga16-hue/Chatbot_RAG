"""
Physics Electronics & Logic Gates Engine
========================================

PURPOSE:
    Solves Logic Gate truth tables, Boolean expressions, and semiconductor principles.
"""

import re
from typing import Optional
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent


LOGIC_GATES = {
    "nand": {
        "name": "NAND Gate (Universal Gate)",
        "symbol": "Y = (A · B)̄",
        "desc": "Inverted AND gate. Output is LOW (0) ONLY when both inputs are 1.",
        "table": [("0", "0", "1"), ("0", "1", "1"), ("1", "0", "1"), ("1", "1", "0")],
    },
    "nor": {
        "name": "NOR Gate (Universal Gate)",
        "symbol": "Y = (A + B)̄",
        "desc": "Inverted OR gate. Output is HIGH (1) ONLY when both inputs are 0.",
        "table": [("0", "0", "1"), ("0", "1", "0"), ("1", "0", "0"), ("1", "1", "0")],
    },
    "xnor": {
        "name": "XNOR Gate (Equivalence Gate)",
        "symbol": "Y = (A ⊕ B)̄ = AB + ĀB̄",
        "desc": "Output is HIGH (1) when both inputs are IDENTICAL.",
        "table": [("0", "0", "1"), ("0", "1", "0"), ("1", "0", "0"), ("1", "1", "1")],
    },
    "xor": {
        "name": "XOR Gate (Exclusive OR)",
        "symbol": "Y = A ⊕ B = ĀB + AB̄",
        "desc": "Output is HIGH (1) when inputs are DIFFERENT (odd number of 1s).",
        "table": [("0", "0", "0"), ("0", "1", "1"), ("1", "0", "1"), ("1", "1", "0")],
    },
    "and": {
        "name": "AND Gate",
        "symbol": "Y = A · B",
        "desc": "Output is HIGH (1) only when BOTH inputs A and B are HIGH (1).",
        "table": [("0", "0", "0"), ("0", "1", "0"), ("1", "0", "0"), ("1", "1", "1")],
    },
    "or": {
        "name": "OR Gate",
        "symbol": "Y = A + B",
        "desc": "Output is HIGH (1) when AT LEAST ONE input (A or B) is HIGH (1).",
        "table": [("0", "0", "0"), ("0", "1", "1"), ("1", "0", "1"), ("1", "1", "1")],
    },
    "not": {
        "name": "NOT Gate (Inverter)",
        "symbol": "Y = Ā",
        "desc": "Output is the INVERSE / COMPLEMENT of the input A.",
        "table": [("0", "-", "1"), ("1", "-", "0")],
    },
}


class ElectronicsEngine:
    """Handles digital electronics and logic gates queries."""

    def solve(self, query: str) -> Optional[SubjectSolveResult]:
        lower_q = query.lower()

        for gate_key, gate_info in LOGIC_GATES.items():
            if re.search(r'\b' + re.escape(gate_key) + r'\s+gate\b', lower_q) or \
               re.search(r'\btruth\s+table\s+(?:of|for)\s+' + re.escape(gate_key) + r'\b', lower_q) or \
               (re.search(r'\b' + re.escape(gate_key) + r'\b', lower_q) and "truth table" in lower_q):
                lines = [f"### 🔌 **{gate_info['name']}**\n"]
                lines.append(f"**Boolean Expression:** `{gate_info['symbol']}`\n")
                lines.append(f"**Principle:** {gate_info['desc']}\n")
                lines.append("#### 📊 **Truth Table:**")
                if gate_key == "not":
                    lines.append("| Input (A) | Output (Y) |")
                    lines.append("|:---:|:---:|")
                    for a, _, y in gate_info["table"]:
                        lines.append(f"| {a} | **{y}** |")
                else:
                    lines.append("| Input A | Input B | Output (Y) |")
                    lines.append("|:---:|:---:|:---:|")
                    for a, b, y in gate_info["table"]:
                        lines.append(f"| {a} | {b} | **{y}** |")
                lines.append("")

                md = "\n".join(lines)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.PHYSICS,
                    topic="electronics",
                    concept_id="physics.electronics.semiconductors",
                    intent=QuestionIntent.EXPLAIN_CONCEPT,
                    original_question=query,
                    formula=gate_info["symbol"],
                    steps=[f"Generate truth table for {gate_info['name']}"],
                    answer=f"Truth Table of {gate_info['name']}",
                    formatted_markdown=md,
                    confidence=0.99,
                )

        return None


# Global instance
electronics_engine = ElectronicsEngine()
