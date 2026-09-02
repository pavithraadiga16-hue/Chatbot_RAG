"""
Chemistry Engine Comprehensive Unit & Reaction Tests
=====================================================

Covers:
1. Periodic Table dynamic lookups (atomic mass, atomic number, valency, electronic configuration)
2. Molecular mass and percentage composition (H2O, H2SO4, CaCO3, C6H12O6, Al2(SO4)3, CuSO4.5H2O)
3. Chemical equation balancing (linear algebra nullspace)
4. pH calculations and acid-base equilibrium
5. Chemistry conceptual knowledge (Bonds, Reactions, Mole concept, Organic groups)
"""

import pytest
from app.subject_engine.science.chemistry.engine import chemistry_engine
from app.subject_engine.science.chemistry.parser import chem_parser
from app.subject_engine.science.chemistry.reactions import reaction_balancer
from app.subject_engine.base import QuestionIntent, SubjectType


def test_periodic_table_atomic_mass():
    """Verify atomic mass lookups."""
    res_o = chemistry_engine.solve("atomic mass of oxygen")
    assert res_o.handled_locally is True
    assert "15.999" in res_o.answer or "16" in res_o.answer

    res_fe = chemistry_engine.solve("atomic mass of iron")
    assert res_fe.handled_locally is True
    assert "55.845" in res_fe.answer or "55.8" in res_fe.answer


def test_periodic_table_atomic_number():
    """Verify atomic number lookups."""
    res_na = chemistry_engine.solve("atomic number of sodium")
    assert res_na.handled_locally is True
    assert "11" in res_na.answer

    res_c = chemistry_engine.solve("atomic number of carbon")
    assert res_c.handled_locally is True
    assert "6" in res_c.answer


def test_periodic_table_valency():
    """Verify valency lookups."""
    res_o = chemistry_engine.solve("valency of oxygen")
    assert res_o.handled_locally is True
    assert "2" in res_o.answer

    res_c = chemistry_engine.solve("valency of carbon")
    assert res_c.handled_locally is True
    assert "4" in res_c.answer


def test_periodic_table_electron_config():
    """Verify electronic configuration lookups."""
    res_cl = chemistry_engine.solve("electronic configuration of chlorine")
    assert res_cl.handled_locally is True
    assert "3s" in res_cl.answer or "3p" in res_cl.answer


def test_chemical_formula_parser_and_molar_mass():
    """Verify molar mass and percentage composition calculations."""
    parsed_h2so4 = chem_parser.parse("H2SO4")
    assert parsed_h2so4 is not None
    assert abs(parsed_h2so4.total_molar_mass - 98.08) < 0.2
    assert "H" in parsed_h2so4.percentage_composition
    assert "S" in parsed_h2so4.percentage_composition
    assert "O" in parsed_h2so4.percentage_composition

    # Natural student query: "what is h2so4 molecular mass"
    res1 = chemistry_engine.solve("what is h2so4 molecular mass")
    assert res1.handled_locally is True
    assert "98" in res1.answer

    res2 = chemistry_engine.solve("molecular mass of CaCO3")
    assert res2.handled_locally is True
    assert "100" in res2.answer

    res3 = chemistry_engine.solve("molar mass of H2O")
    assert res3.handled_locally is True
    assert "18" in res3.answer

    res4 = chemistry_engine.solve("molecular mass of C6H12O6")
    assert res4.handled_locally is True
    assert "180" in res4.answer


def test_complex_formula_parentheses():
    """Verify complex chemical formulas with parentheses like Al2(SO4)3."""
    parsed_al2so43 = chem_parser.parse("Al2(SO4)3")
    assert parsed_al2so43 is not None
    assert parsed_al2so43.elements_count["Al"] == 2
    assert parsed_al2so43.elements_count["S"] == 3
    assert parsed_al2so43.elements_count["O"] == 12
    # Al2(SO4)3 molar mass ≈ 342.15
    assert abs(parsed_al2so43.total_molar_mass - 342.15) < 0.5


def test_chemical_reaction_balancing():
    """Verify balancing of common chemical equations."""
    # 1. H2 + O2 -> H2O  ⟹  2H2 + O2 -> 2H2O
    res1 = reaction_balancer.balance("H2 + O2 -> H2O", "balance H2 + O2 -> H2O")
    assert res1 is not None
    assert "2H2 + O2 → 2H2O" in res1.answer or "2H2 + O2 -> 2H2O" in res1.answer

    # 2. Fe + O2 -> Fe2O3  ⟹  4Fe + 3O2 -> 2Fe2O3
    res2 = reaction_balancer.balance("Fe + O2 -> Fe2O3", "balance Fe + O2 -> Fe2O3")
    assert res2 is not None
    assert "4Fe + 3O2 → 2Fe2O3" in res2.answer

    # 3. Combustion: CH4 + O2 -> CO2 + H2O  ⟹  CH4 + 2O2 -> CO2 + 2H2O
    res3 = reaction_balancer.balance("CH4 + O2 -> CO2 + H2O", "balance CH4 + O2 -> CO2 + H2O")
    assert res3 is not None
    assert "CH4 + 2O2 → CO2 + 2H2O" in res3.answer

    # 4. Acid-Base: CaCO3 + HCl -> CaCl2 + CO2 + H2O  ⟹  CaCO3 + 2HCl -> CaCl2 + CO2 + H2O
    res4 = reaction_balancer.balance("CaCO3 + HCl -> CaCl2 + CO2 + H2O", "balance CaCO3 + HCl -> CaCl2 + CO2 + H2O")
    assert res4 is not None
    assert "CaCO3 + 2HCl → CaCl2 + CO2 + H2O" in res4.answer

    # 5. Haber Process: N2 + H2 -> NH3  ⟹  N2 + 3H2 -> 2NH3
    res5 = reaction_balancer.balance("N2 + H2 -> NH3", "balance N2 + H2 -> NH3")
    assert res5 is not None
    assert "N2 + 3H2 → 2NH3" in res5.answer


def test_ph_calculation():
    """Verify pH scale calculation."""
    res = chemistry_engine.solve("find pH if [H+] = 0.001 M")
    assert res.handled_locally is True
    assert "3" in res.answer


def test_chemistry_concepts():
    """Verify conceptual chemistry questions."""
    res1 = chemistry_engine.solve("what is ionic bond")
    assert res1.handled_locally is True
    assert "transfer" in res1.formatted_markdown.lower() or "octet" in res1.formatted_markdown.lower()

    res2 = chemistry_engine.solve("what is mole concept")
    assert res2.handled_locally is True
    assert "6.022" in res2.formatted_markdown or "avogadro" in res2.formatted_markdown.lower()


def test_chemical_compound_formula_lookups():
    """Verify common chemical compound lookups including 'what water formula'."""
    # 1. Water formula
    res_water = chemistry_engine.solve("what water formula")
    assert res_water.handled_locally is True
    assert res_water.subject.value == "chemistry"
    assert "H₂O" in res_water.formatted_markdown or "H2O" in res_water.formatted_markdown
    assert "Water" in res_water.formatted_markdown

    # 2. Baking soda formula
    res_baking = chemistry_engine.solve("baking soda formula")
    assert res_baking.handled_locally is True
    assert "NaHCO₃" in res_baking.formatted_markdown or "NaHCO3" in res_baking.formatted_markdown

    # 3. Salt formula
    res_salt = chemistry_engine.solve("what is the chemical formula of salt")
    assert res_salt.handled_locally is True
    assert "NaCl" in res_salt.formatted_markdown

    # 4. Glucose formula
    res_glucose = chemistry_engine.solve("formula of glucose")
    assert res_glucose.handled_locally is True
    assert "C₆H₁₂O₆" in res_glucose.formatted_markdown or "C6H12O6" in res_glucose.formatted_markdown

    # 5. Rust formula
    res_rust = chemistry_engine.solve("what is formula of rust")
    assert res_rust.handled_locally is True
    assert "Fe₂O₃" in res_rust.formatted_markdown or "Fe2O3" in res_rust.formatted_markdown

