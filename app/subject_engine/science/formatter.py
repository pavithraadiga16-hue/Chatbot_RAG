"""
Scientific Pedagogical Markdown Formatter
=========================================

PURPOSE:
    Provides pedagogical, student-friendly Markdown templates for scientific responses
    across Physics (numerical calculations & laws), Chemistry (reactions, periodic table, formulas),
    and Biology (structures, functions, comparisons, mechanisms).
"""

from typing import Optional, Any


class ScienceFormatter:
    """Scientific response formatting engine."""

    def format_numerical_solution(
        self,
        problem: str,
        givens: dict[str, str],
        formula: str,
        calculation_steps: list[str],
        final_answer: str,
        unit: Optional[str] = None,
        topic_title: Optional[str] = "Physics Calculation",
        notes: Optional[list[str]] = None,
    ) -> str:
        """
        Formats a dynamic physics/chemistry numerical calculation.
        """
        lines = [f"### 🔬 **{topic_title}**\n"]
        lines.append(f"**Question:** `{problem}`\n")

        # Given section
        if givens:
            lines.append("#### 📥 **Given Data:**")
            for var, val in givens.items():
                lines.append(f"- **{var}:** `{val}`")
            lines.append("")

        # Formula section
        if formula:
            lines.append("#### 📖 **Governing Formula / Scientific Principle:**")
            lines.append(f"> `{formula}`\n")

        # Step-by-step calculation
        if calculation_steps:
            lines.append("#### 📝 **Step-by-Step Calculation:**")
            for i, step in enumerate(calculation_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        # Notes / Key insights if any
        if notes:
            lines.append("#### 💡 **Key Takeaways & Concept Insights:**")
            for note in notes:
                lines.append(f"- {note}")
            lines.append("")

        # Final answer box
        lines.append("---")
        unit_str = f" {unit}" if unit and not final_answer.endswith(unit) else ""
        lines.append("### 🎯 **Final Answer:**")
        lines.append(f"# **`{final_answer}{unit_str}`**")

        return "\n".join(lines)

    def format_concept_explanation(
        self,
        name: str,
        subject: str,
        definition: str,
        key_points: Optional[list[str]] = None,
        formula: Optional[str] = None,
        unit: Optional[str] = None,
        examples: Optional[list[str]] = None,
        diagram_ascii: Optional[str] = None,
    ) -> str:
        """
        Formats a structured conceptual definition and scientific explanation.
        """
        lines = [f"### 🔬 **{name}** ({subject.capitalize()})\n"]
        lines.append("#### 📖 **Definition & Principle:**")
        lines.append(f"{definition}\n")

        if formula:
            lines.append("#### 📐 **Mathematical Formula & Law:**")
            lines.append(f"> `{formula}`")
            if unit:
                lines.append(f"> **SI Unit:** `{unit}`")
            lines.append("")

        if key_points:
            lines.append("#### ⚡ **Key Scientific Principles & Characteristics:**")
            for pt in key_points:
                lines.append(f"- {pt}")
            lines.append("")

        if diagram_ascii:
            lines.append("```text")
            lines.append(diagram_ascii)
            lines.append("```\n")

        if examples:
            lines.append("#### 💡 **Real-World Examples & Applications:**")
            for ex in examples:
                lines.append(f"- {ex}")
            lines.append("")

        return "\n".join(lines)

    def format_chemical_compound(
        self,
        common_name: str,
        chemical_name: str,
        formula: str,
        unicode_formula: str,
        molar_mass: str,
        elements: list[str],
        structure_or_type: Optional[str] = None,
        properties_and_uses: Optional[list[str]] = None,
        key_points: Optional[list[str]] = None,
    ) -> str:
        """
        Formats a structured chemical compound and formula card.
        """
        lines = [f"### 🧪 **{common_name} ({unicode_formula})** (Chemistry)\n"]
        lines.append("#### 📖 **Chemical Information:**")
        lines.append(f"- **Chemical Formula:** # **`{unicode_formula}`** (`{formula}`)")
        lines.append(f"- **Chemical Name:** {chemical_name}")
        lines.append(f"- **Molar Mass:** `{molar_mass}`")
        if elements:
            lines.append(f"- **Constituent Elements:** {', '.join(elements)}")
        lines.append("")

        if structure_or_type:
            lines.append("#### 🔬 **Structure & Bonding:**")
            lines.append(f"{structure_or_type}\n")

        if key_points:
            lines.append("#### ⚡ **Key Principles & Facts:**")
            for pt in key_points:
                lines.append(f"- {pt}")
            lines.append("")

        if properties_and_uses:
            lines.append("#### 💡 **Properties & Real-World Applications:**")
            for prop in properties_and_uses:
                lines.append(f"- {prop}")
            lines.append("")

        return "\n".join(lines)

    def format_chemical_reaction(

        self,
        unbalanced: str,
        balanced: str,
        element_tally: Optional[dict[str, tuple[int, int]]] = None,
        reaction_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Formats a chemical equation balancing result.
        """
        lines = ["### 🧪 **Chemical Reaction Balancer**\n"]
        lines.append(f"**Unbalanced Equation:** `{unbalanced}`\n")
        lines.append("#### ⚖️ **Balanced Chemical Equation:**")
        lines.append(f"> # **`{balanced}`**\n")

        if reaction_type:
            lines.append(f"**Reaction Type:** `{reaction_type}`\n")

        if element_tally:
            lines.append("#### 📊 **Atom Conservation Table (Law of Conservation of Mass):**")
            lines.append("| Element | Reactant Atoms | Product Atoms | Balanced? |")
            lines.append("|:---:|:---:|:---:|:---:|")
            for elem, (react_cnt, prod_cnt) in sorted(element_tally.items()):
                status = "✅ Balanced" if react_cnt == prod_cnt else "❌ Unbalanced"
                lines.append(f"| **{elem}** | {react_cnt} | {prod_cnt} | {status} |")
            lines.append("")

        if description:
            lines.append("#### 📝 **Reaction Explanation:**")
            lines.append(f"{description}\n")

        return "\n".join(lines)

    def format_biological_concept(
        self,
        name: str,
        definition: str,
        functions: Optional[list[str]] = None,
        structure: Optional[str] = None,
        location: Optional[str] = None,
        importance: Optional[str] = None,
        key_points: Optional[list[str]] = None,
        common_questions: Optional[dict[str, str]] = None,
        explanation: Optional[str] = None,
    ) -> str:
        """
        Formats a biological concept explanation.
        """
        lines = [f"### 🧬 **{name}** (Biology)\n"]
        lines.append("#### 📖 **Definition:**")
        lines.append(f"{definition}\n")

        if location:
            lines.append(f"**📍 Location in Organism/Cell:** {location}\n")

        if structure:
            lines.append("#### 🔬 **Structure & Characteristics:**")
            lines.append(f"{structure}\n")

        if key_points:
            lines.append("#### ⚡ **Key Principles & Laws:**")
            for pt in key_points:
                lines.append(f"- {pt}")
            lines.append("")

        if functions:
            lines.append("#### ⚙️ **Key Functions & Roles:**")
            for fn in functions:
                lines.append(f"- {fn}")
            lines.append("")

        if importance:
            lines.append("#### 🌟 **Biological Significance:**")
            lines.append(f"{importance}\n")

        if explanation:
            lines.append("#### 📚 **Detailed Mechanism & Explanation:**")
            lines.append(f"{explanation}\n")

        if common_questions:
            lines.append("#### ❓ **Frequently Asked Exam Questions:**")
            for q, a in common_questions.items():
                lines.append(f"- **Q: {q}**\n  - **A:** {a}")
            lines.append("")

        return "\n".join(lines)


    def format_comparison_table(
        self,
        title: str,
        item_a: str,
        item_b: str,
        differences: list[tuple[str, str, str]],
    ) -> str:
        """
        Formats a comparative difference table (e.g. Mitosis vs Meiosis, Speed vs Velocity).
        differences format: [(Parameter/Feature, Item A value, Item B value)]
        """
        lines = [f"### ⚖️ **Comparison: {item_a} vs {item_b}**\n"]
        lines.append(f"**Topic:** {title}\n")
        lines.append(f"| Feature / Parameter | **{item_a}** | **{item_b}** |")
        lines.append("|:---|:---|:---|")
        for param, val_a, val_b in differences:
            lines.append(f"| **{param}** | {val_a} | {val_b} |")
        lines.append("")
        return "\n".join(lines)


# Global Science Formatter
science_formatter = ScienceFormatter()
