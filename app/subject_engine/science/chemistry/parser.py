"""
Chemical Formula Parser & Molar Mass Engine
===========================================

PURPOSE:
    Parses chemical formulas (including unicode subscripts, parentheses, hydrates,
    and case-insensitive student input like 'h2so4' or 'caco3') and computes exact
    molar mass and elemental percentage composition.
"""

import re
from typing import Optional
from pydantic import BaseModel, Field
from app.subject_engine.science.chemistry.periodic_table import periodic_table


class ParsedChemicalFormula(BaseModel):
    """Result of parsing a chemical formula."""
    canonical_formula: str
    elements_count: dict[str, int]
    total_molar_mass: float
    percentage_composition: dict[str, float]
    breakdown_steps: list[str] = Field(default_factory=list)


# Unicode subscript mappings
UNICODE_SUBSCRIPTS = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
}

# Sorted two-letter element symbols (lowercase)
TWO_LETTER_ELEMS = sorted(
    [e.symbol.lower() for e in periodic_table.elements if len(e.symbol) == 2],
    key=lambda s: len(s),
    reverse=True,
)
ONE_LETTER_ELEMS = sorted(
    [e.symbol.lower() for e in periodic_table.elements if len(e.symbol) == 1],
    key=lambda s: len(s),
    reverse=True,
)


class ChemicalFormulaParser:
    """Parses chemical formulas into atomic counts and calculates molar mass."""

    def normalize_formula(self, raw_formula: str) -> str:
        """Normalizes unicode subscripts, dots, case, and spacing."""
        text = raw_formula.strip()
        for u_sub, digit in UNICODE_SUBSCRIPTS.items():
            text = text.replace(u_sub, digit)
        text = text.replace('·', '.').replace('*', '.')
        parts = text.split('.')
        clean_parts = ["".join(p.split()) for p in parts]
        normalized = ".".join(clean_parts)

        # If user typed all lowercase (e.g. h2so4, caco3, h2o), auto-capitalize element symbols
        if normalized.islower() or not any(c.isupper() for c in normalized):
            normalized = self._autocaptialize_formula(normalized)

        return normalized

    def _autocaptialize_formula(self, text: str) -> str:
        """Converts lowercase formula like 'h2so4' to 'H2SO4' and 'caco3' to 'CaCO3'."""
        result = []
        i = 0
        n = len(text)
        while i < n:
            c = text[i]
            if c in "().0123456789":
                result.append(c)
                i += 1
                continue

            # Check 2-letter element match
            matched_2 = False
            if i + 1 < n:
                sub2 = text[i:i+2].lower()
                if sub2 in TWO_LETTER_ELEMS:
                    result.append(sub2[0].upper() + sub2[1].lower())
                    i += 2
                    matched_2 = True

            if not matched_2:
                sub1 = text[i].lower()
                if sub1 in ONE_LETTER_ELEMS:
                    result.append(sub1.upper())
                    i += 1
                else:
                    result.append(text[i])
                    i += 1

        return "".join(result)

    def parse_group(self, group_str: str) -> dict[str, int]:
        """
        Parses a nested chemical formula group with parentheses, e.g. Al2(SO4)3 or Ca(OH)2.
        """
        paren_pattern = re.compile(r'\(([^()]+)\)(\d*)')
        current = group_str

        # Expand innermost parentheses
        while True:
            match = paren_pattern.search(current)
            if not match:
                break
            inner_group = match.group(1)
            multiplier = int(match.group(2)) if match.group(2) else 1
            inner_counts = self._parse_simple_group(inner_group)
            expanded = "".join(f"{elem}{cnt * multiplier}" for elem, cnt in inner_counts.items())
            current = current[:match.start()] + expanded + current[match.end():]

        return self._parse_simple_group(current)

    def _parse_simple_group(self, simple_str: str) -> dict[str, int]:
        """Parses element-number tokens, e.g. H2S1O4 or Al2S3O12."""
        elem_pattern = re.compile(r'([A-Z][a-z]?)(\d*)')
        counts: dict[str, int] = {}

        for match in elem_pattern.finditer(simple_str):
            elem = match.group(1)
            num_str = match.group(2)
            count = int(num_str) if num_str else 1
            counts[elem] = counts.get(elem, 0) + count

        return counts

    def parse(self, formula_str: str) -> Optional[ParsedChemicalFormula]:
        """
        Parses a chemical formula and computes molar mass + percentage composition.
        """
        normalized = self.normalize_formula(formula_str)
        if not normalized:
            return None

        # Check for hydrate dot (e.g. CuSO4.5H2O)
        hydrate_parts = normalized.split('.')
        main_part = hydrate_parts[0]
        hydrate_multiplier = 1
        hydrate_formula = ""

        if len(hydrate_parts) > 1:
            hyd_str = hydrate_parts[1]
            hyd_num_match = re.match(r'^(\d+)(.*)', hyd_str)
            if hyd_num_match:
                hydrate_multiplier = int(hyd_num_match.group(1))
                hydrate_formula = hyd_num_match.group(2)
            else:
                hydrate_multiplier = 1
                hydrate_formula = hyd_str

        # Parse main molecule
        main_counts = self.parse_group(main_part)
        if not main_counts:
            return None

        # Parse hydrate molecule if present (usually H2O)
        if hydrate_formula:
            hyd_counts = self.parse_group(hydrate_formula)
            for elem, cnt in hyd_counts.items():
                main_counts[elem] = main_counts.get(elem, 0) + (cnt * hydrate_multiplier)

        # Validate elements exist in periodic table & calculate molar mass
        total_mass = 0.0
        breakdown_steps = []
        element_masses: dict[str, float] = {}

        for elem_sym, count in sorted(main_counts.items()):
            elem_data = periodic_table.get_by_symbol(elem_sym)
            if not elem_data:
                return None  # Unknown element symbol
            sub_mass = count * elem_data.atomic_mass
            element_masses[elem_sym] = sub_mass
            total_mass += sub_mass
            breakdown_steps.append(
                f"- **{elem_data.name} ({elem_sym}):** `{count} × {elem_data.atomic_mass:.4g} u` = **`{sub_mass:.4g} g/mol`**"
            )

        if total_mass == 0:
            return None

        # Compute percentage composition
        pct_comp = {}
        for elem_sym, sub_mass in element_masses.items():
            pct = (sub_mass / total_mass) * 100.0
            pct_comp[elem_sym] = pct

        return ParsedChemicalFormula(
            canonical_formula=normalized,
            elements_count=main_counts,
            total_molar_mass=total_mass,
            percentage_composition=pct_comp,
            breakdown_steps=breakdown_steps,
        )


# Global instance
chem_parser = ChemicalFormulaParser()
