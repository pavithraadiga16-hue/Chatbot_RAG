"""
Deterministic Chemical Equation Balancer
=========================================

PURPOSE:
    Balances chemical equations using linear algebra nullspace computation (Law of Conservation of Mass).
    Examples:
    - H2 + O2 -> H2O  ⟹  2H₂ + O₂ → 2H₂O
    - Fe + O2 -> Fe2O3  ⟹  4Fe + 3O₂ → 2Fe₂O₃
    - CH4 + O2 -> CO2 + H2O  ⟹  CH₄ + 2O₂ → CO₂ + 2H₂O
    - CaCO3 + HCl -> CaCl2 + CO2 + H2O  ⟹  CaCO₃ + 2HCl → CaCl₂ + CO₂ + H₂O
    - N2 + H2 -> NH3  ⟹  N₂ + 3H₂ → 2NH₃
"""

import re
from typing import Optional
import sympy as sp

from app.subject_engine.base import SubjectSolveResult, SubjectType, QuestionIntent
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.chemistry.parser import chem_parser


class ReactionBalancer:
    """Balances chemical equations deterministically."""

    def balance(self, equation_str: str, original_query: str) -> Optional[SubjectSolveResult]:
        """
        Balances equation string, e.g. 'H2 + O2 -> H2O'
        """
        # Split into reactants and products
        eq_clean = re.sub(r'\b(balance|balanced\s+equation\s+for|reaction)\b', '', equation_str, flags=re.IGNORECASE).strip()

        # Split across arrows: ->, -->, =>, =, →
        arrow_match = re.search(r'\s*(?:-->|->|=>|=|→)\s*', eq_clean)
        if not arrow_match:
            return None

        lhs_str = eq_clean[:arrow_match.start()].strip()
        rhs_str = eq_clean[arrow_match.end():].strip()

        if not lhs_str or not rhs_str:
            return None

        reactants = [c.strip() for c in re.split(r'\s*\+\s*', lhs_str) if c.strip()]
        products = [c.strip() for c in re.split(r'\s*\+\s*', rhs_str) if c.strip()]

        if not reactants or not products:
            return None

        # Parse all compounds
        all_compounds = reactants + products
        num_reactants = len(reactants)
        num_products = len(products)
        total_compounds = len(all_compounds)

        compound_atoms: list[dict[str, int]] = []
        all_elements: set[str] = set()

        for comp in all_compounds:
            # Strip leading coefficients if user typed them
            comp_clean = re.sub(r'^\d+\s*', '', comp)
            norm = chem_parser.normalize_formula(comp_clean)
            counts = chem_parser.parse_group(norm)
            if not counts:
                return None
            compound_atoms.append(counts)
            all_elements.update(counts.keys())

        elements_list = sorted(all_elements)

        # Build stoichiometric matrix: rows = elements, cols = compounds
        # Reactants have positive counts, products have negative counts
        matrix_rows = []
        for elem in elements_list:
            row = []
            for i, comp_counts in enumerate(compound_atoms):
                count = comp_counts.get(elem, 0)
                if i >= num_reactants:
                    count = -count
                row.append(count)
            matrix_rows.append(row)

        try:
            m = sp.Matrix(matrix_rows)
            nullspace = m.nullspace()
            if not nullspace:
                return None

            # Get the first basis vector of the nullspace
            basis = nullspace[0]

            # Convert all elements of the basis vector to positive integers
            # Find least common multiple of denominators
            denominators = [val.q for val in basis]
            lcm_denom = sp.lcm(denominators)
            int_coeffs = [int(val * lcm_denom) for val in basis]

            # If all are negative, invert signs
            if all(c <= 0 for c in int_coeffs):
                int_coeffs = [-c for c in int_coeffs]

            # Ensure all coefficients are positive
            if any(c <= 0 for c in int_coeffs):
                return None

            # Simplify by GCD of all coefficients
            overall_gcd = sp.gcd(int_coeffs)
            coeffs = [c // overall_gcd for c in int_coeffs]

            # Reconstruct balanced equation
            react_terms = []
            for i in range(num_reactants):
                c = coeffs[i]
                comp_name = reactants[i]
                comp_clean = re.sub(r'^\d+\s*', '', comp_name)
                term = f"{c}{comp_clean}" if c > 1 else comp_clean
                react_terms.append(term)

            prod_terms = []
            for j in range(num_products):
                idx = num_reactants + j
                c = coeffs[idx]
                comp_name = products[j]
                comp_clean = re.sub(r'^\d+\s*', '', comp_name)
                term = f"{c}{comp_clean}" if c > 1 else comp_clean
                prod_terms.append(term)

            balanced_str = f"{' + '.join(react_terms)} → {' + '.join(prod_terms)}"

            # Compute atom conservation tally
            atom_tally: dict[str, tuple[int, int]] = {}
            for elem in elements_list:
                r_total = sum(compound_atoms[i].get(elem, 0) * coeffs[i] for i in range(num_reactants))
                p_total = sum(compound_atoms[num_reactants + j].get(elem, 0) * coeffs[num_reactants + j] for j in range(num_products))
                atom_tally[elem] = (r_total, p_total)

            steps = [
                f"Identify Reactants: `{', '.join(reactants)}`",
                f"Identify Products: `{', '.join(products)}`",
                f"Apply Law of Conservation of Mass: Number of atoms of each element must remain equal on both sides.",
                f"Balanced Equation: **`{balanced_str}`**",
            ]

            md = science_formatter.format_chemical_reaction(
                unbalanced=f"{' + '.join(reactants)} → {' + '.join(products)}",
                balanced=balanced_str,
                element_tally=atom_tally,
                description="The stoichiometric coefficients ensure exact conservation of mass and atom parity.",
            )

            return SubjectSolveResult(
                handled_locally=True,
                subject=SubjectType.CHEMISTRY,
                topic="reactions",
                concept_id="chem.reactions.balancing",
                intent=QuestionIntent.BALANCE_EQUATION,
                original_question=original_query,
                formula="Law of Conservation of Mass",
                steps=steps,
                answer=balanced_str,
                formatted_markdown=md,
                confidence=0.99,
            )
        except Exception:
            return None


# Global instance
reaction_balancer = ReactionBalancer()
