"""
Mathematics Response Formatter
==============================

PURPOSE:
    Transforms raw mathematical solver outputs, steps, formulas, and concepts
    into structured, pedagogical, student-friendly Markdown responses.
"""

from typing import Any, Optional


class MathFormatter:
    """Formats mathematical solutions for educational clarity."""

    def format_solution(
        self,
        problem: str,
        answer: str,
        steps: list[str],
        formula: Optional[str] = None,
        topic_title: Optional[str] = None,
        unit: Optional[str] = None,
        rules_applied: Optional[list[str]] = None,
        explanation: Optional[str] = None,
    ) -> str:
        """
        Builds a comprehensive educational markdown response.
        """
        title = topic_title or "Mathematical Solution"
        display_unit = f" {unit}" if unit else ""

        parts = []

        # 1. Header & Problem Restatement
        parts.append(f"### 📐 **{title}**")
        parts.append(f"**Problem:** `{problem}`\n")

        # 2. Formula / Rule Box (if available)
        if formula:
            parts.append(f"**📖 Formula / Method:**\n> `{formula}`\n")

        if rules_applied:
            rules_str = ", ".join(f"`{r}`" for r in rules_applied)
            parts.append(f"**💡 Applicable Rule(s):** {rules_str}\n")

        # 3. Explanation (if available)
        if explanation:
            parts.append(f"{explanation}\n")

        # 4. Step-by-Step Working
        if steps:
            parts.append("#### 📝 **Step-by-Step Working:**")
            for i, step in enumerate(steps, 1):
                parts.append(f"{i}. {step}")
            parts.append("")

        # 5. Final Result
        parts.append("---")
        parts.append(f"### 🎯 **Final Answer:**\n# **`{answer}{display_unit}`**")

        return "\n".join(parts)

    def format_concept_definition(
        self,
        name: str,
        definition: str,
        formula: Optional[str] = None,
        rules: Optional[list[str]] = None,
        examples: Optional[list[str]] = None,
    ) -> str:
        """
        Formats concept definitions, formulas, and properties.
        """
        parts = []
        parts.append(f"### 📚 **Concept: {name}**\n")
        parts.append(f"**Definition:**\n{definition}\n")

        if formula:
            parts.append(f"**📐 Key Formula:**\n> `{formula}`\n")

        if rules:
            parts.append("**📌 Key Properties & Rules:**")
            for r in rules:
                parts.append(f"- {r}")
            parts.append("")

        if examples:
            parts.append("**💡 Examples:**")
            for ex in examples:
                parts.append(f"• `{ex}`")
            parts.append("")

        return "\n".join(parts)

    def format_proof(
        self,
        theorem_name: str,
        statement: str,
        given: Optional[str] = None,
        to_prove: Optional[str] = None,
        construction: Optional[str] = None,
        proof_steps: Optional[list[str]] = None,
        conclusion: Optional[str] = None,
    ) -> str:
        """
        Formats rigorous mathematical proofs and Prameya.
        """
        parts = []
        parts.append(f"### 🏛️ **Theorem Proof: {theorem_name}**\n")
        parts.append(f"**Statement:**\n> *\"{statement}\"*\n")

        if given:
            parts.append(f"**Given:** {given}")
        if to_prove:
            parts.append(f"**To Prove:** {to_prove}")
        if construction:
            parts.append(f"**Construction:** {construction}")

        parts.append("")

        if proof_steps:
            parts.append("#### 📜 **Proof:**")
            for i, step in enumerate(proof_steps, 1):
                parts.append(f"{i}. {step}")
            parts.append("")

        conclusion_text = conclusion or "Hence proved (Q.E.D.)."
        parts.append(f"**Conclusion:** 🏁 **{conclusion_text}**")

        return "\n".join(parts)


# Global formatter
math_formatter = MathFormatter()
