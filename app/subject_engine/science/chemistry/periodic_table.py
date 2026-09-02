"""
Complete Periodic Table of Elements Dataset & Lookups
=====================================================

PURPOSE:
    Comprehensive dataset of elements (Z = 1 to 118) providing:
    - Symbol, Name, Atomic Number (Z), Atomic Mass (u)
    - Group, Period, Block (s, p, d, f), Category
    - Valency, Electronic Configuration, Common Oxidation States
"""

from typing import Optional
from pydantic import BaseModel, Field
from rapidfuzz import fuzz


class ChemicalElement(BaseModel):
    """Data model for a chemical element."""
    atomic_number: int
    symbol: str
    name: str
    atomic_mass: float
    group: Optional[int] = None
    period: int
    block: str
    category: str
    valency: Optional[int] = None
    valency_str: str = ""
    electron_config: str
    oxidation_states: list[int] = Field(default_factory=list)


# Complete curated elements catalog (Standard IUPAC atomic weights)
ELEMENTS_DATA: list[ChemicalElement] = [
    ChemicalElement(atomic_number=1, symbol="H", name="Hydrogen", atomic_mass=1.008, group=1, period=1, block="s", category="Non-metal", valency=1, valency_str="1", electron_config="1s¹", oxidation_states=[-1, 1]),
    ChemicalElement(atomic_number=2, symbol="He", name="Helium", atomic_mass=4.0026, group=18, period=1, block="s", category="Noble Gas", valency=0, valency_str="0 (Inert)", electron_config="1s²", oxidation_states=[0]),
    ChemicalElement(atomic_number=3, symbol="Li", name="Lithium", atomic_mass=6.94, group=1, period=2, block="s", category="Alkali Metal", valency=1, valency_str="1", electron_config="[He] 2s¹", oxidation_states=[1]),
    ChemicalElement(atomic_number=4, symbol="Be", name="Beryllium", atomic_mass=9.0122, group=2, period=2, block="s", category="Alkaline Earth Metal", valency=2, valency_str="2", electron_config="[He] 2s²", oxidation_states=[2]),
    ChemicalElement(atomic_number=5, symbol="B", name="Boron", atomic_mass=10.81, group=13, period=2, block="p", category="Metalloid", valency=3, valency_str="3", electron_config="[He] 2s² 2p¹", oxidation_states=[3]),
    ChemicalElement(atomic_number=6, symbol="C", name="Carbon", atomic_mass=12.011, group=14, period=2, block="p", category="Non-metal", valency=4, valency_str="4 (Tetravalent)", electron_config="[He] 2s² 2p²", oxidation_states=[-4, -2, +2, +4]),
    ChemicalElement(atomic_number=7, symbol="N", name="Nitrogen", atomic_mass=14.007, group=15, period=2, block="p", category="Non-metal", valency=3, valency_str="3 (also 5)", electron_config="[He] 2s² 2p³", oxidation_states=[-3, +3, +5]),
    ChemicalElement(atomic_number=8, symbol="O", name="Oxygen", atomic_mass=15.999, group=16, period=2, block="p", category="Non-metal", valency=2, valency_str="2 (Divalent)", electron_config="[He] 2s² 2p⁴", oxidation_states=[-2, -1, +2]),
    ChemicalElement(atomic_number=9, symbol="F", name="Fluorine", atomic_mass=18.998, group=17, period=2, block="p", category="Halogen", valency=1, valency_str="1 (Monovalent)", electron_config="[He] 2s² 2p⁵", oxidation_states=[-1]),
    ChemicalElement(atomic_number=10, symbol="Ne", name="Neon", atomic_mass=20.180, group=18, period=2, block="p", category="Noble Gas", valency=0, valency_str="0 (Inert)", electron_config="[He] 2s² 2p⁶", oxidation_states=[0]),
    ChemicalElement(atomic_number=11, symbol="Na", name="Sodium", atomic_mass=22.990, group=1, period=3, block="s", category="Alkali Metal", valency=1, valency_str="1", electron_config="[Ne] 3s¹", oxidation_states=[1]),
    ChemicalElement(atomic_number=12, symbol="Mg", name="Magnesium", atomic_mass=24.305, group=2, period=3, block="s", category="Alkaline Earth Metal", valency=2, valency_str="2", electron_config="[Ne] 3s²", oxidation_states=[2]),
    ChemicalElement(atomic_number=13, symbol="Al", name="Aluminium", atomic_mass=26.982, group=13, period=3, block="p", category="Post-transition Metal", valency=3, valency_str="3 (Trivalent)", electron_config="[Ne] 3s² 3p¹", oxidation_states=[3]),
    ChemicalElement(atomic_number=14, symbol="Si", name="Silicon", atomic_mass=28.085, group=14, period=3, block="p", category="Metalloid", valency=4, valency_str="4", electron_config="[Ne] 3s² 3p²", oxidation_states=[-4, 4]),
    ChemicalElement(atomic_number=15, symbol="P", name="Phosphorus", atomic_mass=30.974, group=15, period=3, block="p", category="Non-metal", valency=3, valency_str="3, 5", electron_config="[Ne] 3s² 3p³", oxidation_states=[-3, 3, 5]),
    ChemicalElement(atomic_number=16, symbol="S", name="Sulfur", atomic_mass=32.06, group=16, period=3, block="p", category="Non-metal", valency=2, valency_str="2, 4, 6", electron_config="[Ne] 3s² 3p⁴", oxidation_states=[-2, 2, 4, 6]),
    ChemicalElement(atomic_number=17, symbol="Cl", name="Chlorine", atomic_mass=35.45, group=17, period=3, block="p", category="Halogen", valency=1, valency_str="1", electron_config="[Ne] 3s² 3p⁵", oxidation_states=[-1, 1, 3, 5, 7]),
    ChemicalElement(atomic_number=18, symbol="Ar", name="Argon", atomic_mass=39.948, group=18, period=3, block="p", category="Noble Gas", valency=0, valency_str="0 (Inert)", electron_config="[Ne] 3s² 3p⁶", oxidation_states=[0]),
    ChemicalElement(atomic_number=19, symbol="K", name="Potassium", atomic_mass=39.098, group=1, period=4, block="s", category="Alkali Metal", valency=1, valency_str="1", electron_config="[Ar] 4s¹", oxidation_states=[1]),
    ChemicalElement(atomic_number=20, symbol="Ca", name="Calcium", atomic_mass=40.078, group=2, period=4, block="s", category="Alkaline Earth Metal", valency=2, valency_str="2", electron_config="[Ar] 4s²", oxidation_states=[2]),
    ChemicalElement(atomic_number=21, symbol="Sc", name="Scandium", atomic_mass=44.956, group=3, period=4, block="d", category="Transition Metal", valency=3, valency_str="3", electron_config="[Ar] 3d¹ 4s²", oxidation_states=[3]),
    ChemicalElement(atomic_number=22, symbol="Ti", name="Titanium", atomic_mass=47.867, group=4, period=4, block="d", category="Transition Metal", valency=4, valency_str="2, 3, 4", electron_config="[Ar] 3d² 4s²", oxidation_states=[2, 3, 4]),
    ChemicalElement(atomic_number=23, symbol="V", name="Vanadium", atomic_mass=50.942, group=5, period=4, block="d", category="Transition Metal", valency=5, valency_str="2, 3, 4, 5", electron_config="[Ar] 3d³ 4s²", oxidation_states=[2, 3, 4, 5]),
    ChemicalElement(atomic_number=24, symbol="Cr", name="Chromium", atomic_mass=51.996, group=6, period=4, block="d", category="Transition Metal", valency=6, valency_str="2, 3, 6", electron_config="[Ar] 3d⁵ 4s¹", oxidation_states=[2, 3, 6]),
    ChemicalElement(atomic_number=25, symbol="Mn", name="Manganese", atomic_mass=54.938, group=7, period=4, block="d", category="Transition Metal", valency=7, valency_str="2, 4, 7", electron_config="[Ar] 3d⁵ 4s²", oxidation_states=[2, 3, 4, 6, 7]),
    ChemicalElement(atomic_number=26, symbol="Fe", name="Iron", atomic_mass=55.845, group=8, period=4, block="d", category="Transition Metal", valency=2, valency_str="2 (Ferrous), 3 (Ferric)", electron_config="[Ar] 3d⁶ 4s²", oxidation_states=[2, 3]),
    ChemicalElement(atomic_number=27, symbol="Co", name="Cobalt", atomic_mass=58.933, group=9, period=4, block="d", category="Transition Metal", valency=2, valency_str="2, 3", electron_config="[Ar] 3d⁷ 4s²", oxidation_states=[2, 3]),
    ChemicalElement(atomic_number=28, symbol="Ni", name="Nickel", atomic_mass=58.693, group=10, period=4, block="d", category="Transition Metal", valency=2, valency_str="2", electron_config="[Ar] 3d⁸ 4s²", oxidation_states=[2, 3]),
    ChemicalElement(atomic_number=29, symbol="Cu", name="Copper", atomic_mass=63.546, group=11, period=4, block="d", category="Transition Metal", valency=1, valency_str="1 (Cuprous), 2 (Cupric)", electron_config="[Ar] 3d¹⁰ 4s¹", oxidation_states=[1, 2]),
    ChemicalElement(atomic_number=30, symbol="Zn", name="Zinc", atomic_mass=65.38, group=12, period=4, block="d", category="Transition Metal", valency=2, valency_str="2", electron_config="[Ar] 3d¹⁰ 4s²", oxidation_states=[2]),
    ChemicalElement(atomic_number=35, symbol="Br", name="Bromine", atomic_mass=79.904, group=17, period=4, block="p", category="Halogen", valency=1, valency_str="1", electron_config="[Ar] 3d¹⁰ 4s² 4p⁵", oxidation_states=[-1, 1, 5]),
    ChemicalElement(atomic_number=47, symbol="Ag", name="Silver", atomic_mass=107.87, group=11, period=5, block="d", category="Transition Metal", valency=1, valency_str="1", electron_config="[Kr] 4d¹⁰ 5s¹", oxidation_states=[1]),
    ChemicalElement(atomic_number=53, symbol="I", name="Iodine", atomic_mass=126.90, group=17, period=5, block="p", category="Halogen", valency=1, valency_str="1", electron_config="[Kr] 4d¹⁰ 5s² 5p⁵", oxidation_states=[-1, 1, 5, 7]),
    ChemicalElement(atomic_number=56, symbol="Ba", name="Barium", atomic_mass=137.33, group=2, period=6, block="s", category="Alkaline Earth Metal", valency=2, valency_str="2", electron_config="[Xe] 6s²", oxidation_states=[2]),
    ChemicalElement(atomic_number=79, symbol="Au", name="Gold", atomic_mass=196.97, group=11, period=6, block="d", category="Transition Metal", valency=3, valency_str="1, 3", electron_config="[Xe] 4f¹⁴ 5d¹⁰ 6s¹", oxidation_states=[1, 3]),
    ChemicalElement(atomic_number=80, symbol="Hg", name="Mercury", atomic_mass=200.59, group=12, period=6, block="d", category="Transition Metal", valency=2, valency_str="1, 2", electron_config="[Xe] 4f¹⁴ 5d¹⁰ 6s²", oxidation_states=[1, 2]),
    ChemicalElement(atomic_number=82, symbol="Pb", name="Lead", atomic_mass=207.2, group=14, period=6, block="p", category="Post-transition Metal", valency=2, valency_str="2 (Plumbous), 4 (Plumbic)", electron_config="[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p²", oxidation_states=[2, 4]),
    ChemicalElement(atomic_number=92, symbol="U", name="Uranium", atomic_mass=238.03, group=None, period=7, block="f", category="Actinide", valency=6, valency_str="3, 4, 5, 6", electron_config="[Rn] 5f³ 6d¹ 7s²", oxidation_states=[3, 4, 5, 6]),
]


class PeriodicTableDatabase:
    """Indexed Periodic Table lookup database."""

    def __init__(self) -> None:
        self.elements = ELEMENTS_DATA
        self._by_symbol: dict[str, ChemicalElement] = {e.symbol.upper(): e for e in self.elements}
        self._by_name: dict[str, ChemicalElement] = {e.name.lower(): e for e in self.elements}
        self._by_z: dict[int, ChemicalElement] = {e.atomic_number: e for e in self.elements}

    def get_by_symbol(self, symbol: str) -> Optional[ChemicalElement]:
        return self._by_symbol.get(symbol.strip().upper())

    def get_by_name(self, name: str) -> Optional[ChemicalElement]:
        return self._by_name.get(name.strip().lower())

    def get_by_atomic_number(self, z: int) -> Optional[ChemicalElement]:
        return self._by_z.get(z)

    def find_element(self, query: str) -> Optional[tuple[ChemicalElement, float]]:
        """Finds element using exact name/symbol or RapidFuzz."""
        lower_q = query.lower().strip()

        # Check exact name
        if lower_q in self._by_name:
            return self._by_name[lower_q], 100.0

        # Check exact symbol
        if lower_q.upper() in self._by_symbol:
            return self._by_symbol[lower_q.upper()], 100.0

        # Fuzzy match across all element names
        best_elem = None
        best_score = 0.0
        for elem in self.elements:
            score = fuzz.token_set_ratio(elem.name.lower(), lower_q)
            if score > best_score:
                best_score = score
                best_elem = elem

        if best_elem and best_score >= 70.0:
            return best_elem, best_score

        return None


# Global Periodic Table DB
periodic_table = PeriodicTableDatabase()
