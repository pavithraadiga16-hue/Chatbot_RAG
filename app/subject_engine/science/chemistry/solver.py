"""
Chemistry Master Solver Orchestrator
====================================

PURPOSE:
    Central deterministic Chemistry solver coordinating:
    - Periodic Table lookups (atomic mass, atomic number, valency, electronic configuration)
    - Molar Mass & Percentage Composition calculations
    - Chemical Equation Balancing
    - pH & Acid-Base calculations
    - Organic Chemistry functional group identification
    - Concept explanations and law lookups
"""

import time
import re
import math
from typing import Optional, Any
from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.chemistry.periodic_table import periodic_table, ChemicalElement
from app.subject_engine.science.chemistry.parser import chem_parser
from app.subject_engine.science.chemistry.reactions import reaction_balancer
from app.subject_engine.science.chemistry.compounds import compounds_kb
from app.subject_engine.science.chemistry.concepts import chemistry_kb


class ChemistrySolver:
    """Master solver orchestrator for Chemistry."""

    def solve(self, query: str, context: Optional[dict[str, Any]] = None) -> SubjectSolveResult:
        start_time = time.monotonic()
        raw_q = query.strip()
        lower_q = raw_q.lower()

        # Step 1: Chemical Equation Balancing (reactions containing ->, →, or 'balance')
        if any(arrow in raw_q for arrow in ("->", "-->", "=>", "→")) or "balance " in lower_q:
            bal_res = reaction_balancer.balance(raw_q, raw_q)
            if bal_res:
                return self._finalize(bal_res, start_time, raw_q)

        # Step 2: Periodic Table Specific Property Lookups (atomic mass, atomic number, valency, config)
        if any(prop in lower_q for prop in ("atomic mass", "atomic number", "valency", "valence", "electronic configuration", "electron configuration", "group of", "period of")):
            pt_res = self._handle_periodic_lookup(raw_q, lower_q)
            if pt_res:
                return self._finalize(pt_res, start_time, raw_q)

        # Step 3: Molar Mass & Formula Percentage Composition (e.g. "molecular mass of H2SO4", "molar mass of H2O")
        if any(kw in lower_q for kw in ("molecular mass", "molar mass", "formula mass", "percentage composition", "mass of")) or re.match(r'^[A-Z][a-z]?\d*([A-Z][a-z]?\d*)*(\.[0-9]*[A-Z].*)?$', raw_q.strip()):
            mol_res = self._handle_molar_mass(raw_q, lower_q)
            if mol_res:
                return self._finalize(mol_res, start_time, raw_q)

        # Step 4: Chemical Compound & Formula Lookup (e.g. "what water formula", "baking soda formula", "formula of salt")
        comp_matches = compounds_kb.find_by_query(raw_q, threshold=65.0)
        if comp_matches:
            comp, score = comp_matches[0]
            md = science_formatter.format_chemical_compound(
                common_name=comp.common_name,
                chemical_name=comp.chemical_name,
                formula=comp.formula,
                unicode_formula=comp.unicode_formula,
                molar_mass=comp.molar_mass,
                elements=comp.elements,
                structure_or_type=comp.structure_or_type,
                properties_and_uses=comp.properties_and_uses,
                key_points=comp.key_points,
            )
            res = SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.CHEMISTRY,
                topic="chemical_compounds",
                concept_id=comp.compound_id,
                intent=QuestionIntent.FORMULA_LOOKUP,
                original_question=raw_q,
                formula=comp.unicode_formula,
                rules_applied=comp.key_points,
                steps=[f"Identify compound: {comp.common_name}", f"Chemical Formula: {comp.unicode_formula}"],
                answer=comp.unicode_formula,
                formatted_markdown=md,
                confidence=min(0.99, max(0.80, score / 100.0)),
            )
            return self._finalize(res, start_time, raw_q)

        # Step 5: General Periodic Table Lookup if not matched above
        pt_res = self._handle_periodic_lookup(raw_q, lower_q)
        if pt_res:
            return self._finalize(pt_res, start_time, raw_q)


        # Step 5: pH & pOH Calculations (e.g. "find pH if [H+] = 0.001 M" or "pH of 0.01 M HCl")
        if "ph" in lower_q or "poh" in lower_q:
            ph_res = self._handle_ph_calculation(raw_q, lower_q)
            if ph_res:
                return self._finalize(ph_res, start_time, raw_q)

        # Step 6: Concept Knowledge Base Lookup

        matches = chemistry_kb.find_by_query(raw_q, threshold=60.0)
        if matches:
            concept, score = matches[0]
            md = science_formatter.format_concept_explanation(
                name=concept.name,
                subject="Chemistry",
                definition=concept.definition,
                key_points=concept.key_points,
                formula=concept.formula,
                examples=concept.examples,
            )
            res = SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.CHEMISTRY,
                topic=concept.topic,
                concept_id=concept.concept_id,
                intent=QuestionIntent.DEFINE if any(w in lower_q for w in ("what is", "define", "meaning")) else QuestionIntent.EXPLAIN_CONCEPT,
                original_question=raw_q,
                formula=concept.formula,
                rules_applied=concept.key_points,
                steps=[concept.definition],
                answer=concept.formula or concept.definition,
                formatted_markdown=md,
                confidence=min(0.99, max(0.70, score / 100.0)),
            )
            return self._finalize(res, start_time, raw_q)

        # Unhandled Chemistry query
        elapsed = (time.monotonic() - start_time) * 1000.0
        return SubjectSolveResult(
            handled_locally=False,
            subject=SubjectType.CHEMISTRY,
            intent=QuestionIntent.UNKNOWN,
            original_question=raw_q,
            confidence=0.0,
            execution_time_ms=elapsed,
        )

    def _handle_periodic_lookup(self, query: str, lower_q: str) -> Optional[SubjectSolveResult]:
        """Handles targeted periodic table element lookups."""
        # Detect target property
        prop_type = None
        if "atomic mass" in lower_q or "mass of atom" in lower_q or "atomic weight" in lower_q:
            prop_type = "atomic_mass"
        elif "atomic number" in lower_q or "number of protons in" in lower_q:
            prop_type = "atomic_number"
        elif "valency" in lower_q or "valence" in lower_q:
            prop_type = "valency"
        elif "electronic configuration" in lower_q or "electron configuration" in lower_q:
            prop_type = "electron_config"
        elif "group" in lower_q and "period" in lower_q:
            prop_type = "position"

        # Try to find element mentioned in query
        matched_elem = None
        for elem in periodic_table.elements:
            if re.search(r'\b' + re.escape(elem.name.lower()) + r'\b', lower_q) or \
               (len(elem.symbol) > 1 and re.search(r'\b' + re.escape(elem.symbol.lower()) + r'\b', lower_q)):
                matched_elem = elem
                break

        if not matched_elem:
            # Fallback: check 1-letter symbols with "element X" or "of X"
            for elem in periodic_table.elements:
                if re.search(r'\b(?:element|of)\s+' + re.escape(elem.symbol.lower()) + r'\b', lower_q):
                    matched_elem = elem
                    break

        if matched_elem:
            elem = matched_elem
            if prop_type == "atomic_mass":
                answer = f"{elem.atomic_mass:.4g} u (or g/mol)"
                steps = [
                    f"Element: **{elem.name} ({elem.symbol})**",
                    f"Atomic Number (Z): `{elem.atomic_number}`",
                    f"Standard IUPAC Atomic Mass: **`{elem.atomic_mass:.4g} u`** (approx. `{round(elem.atomic_mass)} u`)",
                ]
                md = science_formatter.format_concept_explanation(
                    name=f"Atomic Mass of {elem.name} ({elem.symbol})",
                    subject="Chemistry",
                    definition=f"The standard atomic mass of {elem.name} ({elem.symbol}) is **{elem.atomic_mass:.4g} u** (unified atomic mass units).",
                    key_points=steps,
                    formula=f"Atomic Mass = {elem.atomic_mass:.4g} u",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.CHEMISTRY,
                    topic="periodic_table",
                    concept_id="chem.periodic.element_property",
                    intent=QuestionIntent.FIND_VALUE,
                    original_question=query,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="u",
                    confidence=0.99,
                )

            elif prop_type == "atomic_number":
                answer = f"Z = {elem.atomic_number}"
                steps = [
                    f"Element: **{elem.name} ({elem.symbol})**",
                    f"Atomic Number (Z): **`{elem.atomic_number}`**",
                    f"Number of Protons = `{elem.atomic_number}`, Number of Electrons = `{elem.atomic_number}`",
                ]
                md = science_formatter.format_concept_explanation(
                    name=f"Atomic Number of {elem.name} ({elem.symbol})",
                    subject="Chemistry",
                    definition=f"The atomic number of {elem.name} ({elem.symbol}) is **{elem.atomic_number}**, corresponding to {elem.atomic_number} protons in its nucleus.",
                    key_points=steps,
                    formula=f"Z = {elem.atomic_number}",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.CHEMISTRY,
                    topic="periodic_table",
                    concept_id="chem.periodic.element_property",
                    intent=QuestionIntent.FIND_VALUE,
                    original_question=query,
                    steps=steps,
                    answer=str(elem.atomic_number),
                    formatted_markdown=md,
                    confidence=0.99,
                )

            elif prop_type == "valency":
                answer = elem.valency_str or str(elem.valency)
                steps = [
                    f"Element: **{elem.name} ({elem.symbol})**",
                    f"Atomic Number: `{elem.atomic_number}`",
                    f"Electronic Configuration: `{elem.electron_config}`",
                    f"Combining Capacity (Valency): **`{elem.valency_str}`**",
                ]
                md = science_formatter.format_concept_explanation(
                    name=f"Valency of {elem.name} ({elem.symbol})",
                    subject="Chemistry",
                    definition=f"The valency of {elem.name} ({elem.symbol}) is **{elem.valency_str}**, representing its combining capacity to achieve a stable noble gas configuration.",
                    key_points=steps,
                    formula=f"Valency = {elem.valency_str}",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.CHEMISTRY,
                    topic="periodic_table",
                    concept_id="chem.periodic.element_property",
                    intent=QuestionIntent.FIND_VALUE,
                    original_question=query,
                    steps=steps,
                    answer=elem.valency_str,
                    formatted_markdown=md,
                    confidence=0.99,
                )

            elif prop_type == "electron_config":
                answer = elem.electron_config
                steps = [
                    f"Element: **{elem.name} ({elem.symbol})**",
                    f"Atomic Number (Z): `{elem.atomic_number}`",
                    f"Ground State Electronic Configuration: **`{elem.electron_config}`**",
                    f"Period: `{elem.period}`, Group: `{elem.group}`, Block: `{elem.block}-block`",
                ]
                md = science_formatter.format_concept_explanation(
                    name=f"Electronic Configuration of {elem.name} ({elem.symbol})",
                    subject="Chemistry",
                    definition=f"The ground-state electronic configuration of {elem.name} (Z = {elem.atomic_number}) is **{elem.electron_config}**.",
                    key_points=steps,
                    formula=elem.electron_config,
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.CHEMISTRY,
                    topic="periodic_table",
                    concept_id="chem.periodic.element_property",
                    intent=QuestionIntent.FIND_VALUE,
                    original_question=query,
                    steps=steps,
                    answer=elem.electron_config,
                    formatted_markdown=md,
                    confidence=0.99,
                )

        return None

    def _handle_molar_mass(self, query: str, lower_q: str) -> Optional[SubjectSolveResult]:
        """Calculates molecular mass and percentage composition for chemical formulas."""
        # Extract potential formula tokens
        words = query.split()
        candidate_formulas = []
        for w in words:
            clean_w = w.strip("?,.:;()[]\"'")
            if any(c in "0123456789₀₁₂₃₄₅₆₇₈₉" for c in clean_w) and any(c.isalpha() for c in clean_w):
                candidate_formulas.append(clean_w)
            elif any(c.isupper() for c in clean_w) and len(clean_w) >= 2:
                candidate_formulas.append(clean_w)

        # If no formula token found, check regex patterns after 'mass of' or 'formula mass of'
        mass_match = re.search(r'\b(?:mass\s+of|molar\s+mass\s+of|molecular\s+mass\s+of|formula\s+mass\s+of)\s+([A-Za-z0-9₀-₉().]+)', query, re.IGNORECASE)
        if mass_match:
            candidate_formulas.insert(0, mass_match.group(1))

        for cand in candidate_formulas:
            parsed = chem_parser.parse(cand)
            if parsed:
                answer = f"{parsed.total_molar_mass:.4g} g/mol (or u)"
                steps = [
                    f"Chemical Formula: **`{parsed.canonical_formula}`**",
                    "Atomic Mass Breakdown:",
                ]
                steps.extend(parsed.breakdown_steps)
                steps.append(f"Sum of atomic masses: **`{parsed.total_molar_mass:.4g} g/mol`**")

                lines = [f"### 🧪 **Molecular Mass Calculation: {parsed.canonical_formula}**\n"]
                lines.append(f"**Chemical Compound:** `{parsed.canonical_formula}`\n")
                lines.append("#### 📊 **Element Breakdown & Atomic Masses:**")
                for s in parsed.breakdown_steps:
                    lines.append(s)
                lines.append("")

                lines.append("#### 📈 **Percentage Composition by Mass:**")
                for elem_sym, pct in sorted(parsed.percentage_composition.items()):
                    lines.append(f"- **{elem_sym}:** `{pct:.2f}%`")
                lines.append("")

                lines.append("---")
                lines.append("### 🎯 **Total Molar Mass:**")
                lines.append(f"# **`{parsed.total_molar_mass:.4g} g/mol`** (`{parsed.total_molar_mass:.4g} u`)")

                md = "\n".join(lines)
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.CHEMISTRY,
                    topic="mole_stoichiometry",
                    concept_id="chem.mole.molar_mass",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    unit="g/mol",
                    confidence=0.99,
                )

        return None


    def _handle_ph_calculation(self, query: str, lower_q: str) -> Optional[SubjectSolveResult]:
        """Calculates pH from [H+] concentration."""
        # Pattern: [H+] = 0.001 or 1e-3 or 10^-3
        conc_match = re.search(r'\[?\s*(?:h\+|h3o\+)\s*\]?\s*=\s*(\d*\.?\d+(?:e[-+]?\d+)?)', lower_q) or \
                     re.search(r'(\d*\.?\d+(?:e[-+]?\d+)?)\s*(?:m|molar)\s*(?:hcl|hno3|acid|\[h\+\])', lower_q)
        if conc_match:
            conc = float(conc_match.group(1))
            if conc > 0:
                ph_val = -math.log10(conc)
                poh_val = 14.0 - ph_val
                nature = "Strongly Acidic" if ph_val < 3 else "Weakly Acidic" if ph_val < 7 else "Neutral" if ph_val == 7 else "Basic"
                givens = {"Hydrogen Ion Concentration [H⁺]": f"{conc:.4g} M"}
                steps = [
                    "pH Formula: `pH = -log₁₀[H⁺]`",
                    f"Substitute: `pH = -log₁₀({conc:.4g})`",
                    f"Calculate: `pH = **{ph_val:.4g}**`",
                    f"pOH = `14 - pH = 14 - {ph_val:.4g} = **{poh_val:.4g}**`",
                    f"Nature of Solution: **{nature}**",
                ]
                answer = f"pH = {ph_val:.4g}"
                md = science_formatter.format_numerical_solution(
                    problem=query,
                    givens=givens,
                    formula="pH = -log₁₀[H⁺]",
                    calculation_steps=steps,
                    final_answer=answer,
                    topic_title="pH Scale & Acidity Calculation",
                )
                return SubjectSolveResult(
                    handled_locally=True,
                    subject=SubjectType.CHEMISTRY,
                    topic="equilibrium_acids",
                    concept_id="chem.acids_bases.ph",
                    intent=QuestionIntent.CALCULATE,
                    original_question=query,
                    formula="pH = -log₁₀[H⁺]",
                    steps=steps,
                    answer=answer,
                    formatted_markdown=md,
                    confidence=0.99,
                )

        return None

    def _finalize(self, res: SubjectSolveResult, start_time: float, raw_q: str) -> SubjectSolveResult:
        res.execution_time_ms = (time.monotonic() - start_time) * 1000.0
        res.original_question = raw_q
        return res


# Global instance
chemistry_solver = ChemistrySolver()
