"""
Scientific Universal Constants & Base Knowledge Subsystem
=========================================================

PURPOSE:
    Provides exact physical and chemical fundamental constants, standard SI units,
    and universal scientific reference values across Physics, Chemistry, and Biology.
"""

from typing import Any
from pydantic import BaseModel, Field


class ScientificConstant(BaseModel):
    """Metadata and values for universal scientific constants."""
    symbol: str
    name: str
    value: float
    unit: str
    latex_symbol: str
    description: str


# Fundamental Scientific Constants Catalog
SCIENTIFIC_CONSTANTS: dict[str, ScientificConstant] = {
    "c": ScientificConstant(
        symbol="c",
        name="Speed of Light in Vacuum",
        value=299792458.0,
        unit="m/s",
        latex_symbol="c",
        description="Speed at which conventional matter and light travel in a vacuum (~3 × 10⁸ m/s).",
    ),
    "g": ScientificConstant(
        symbol="g",
        name="Acceleration due to Gravity on Earth",
        value=9.8,
        unit="m/s²",
        latex_symbol="g",
        description="Standard gravitational acceleration at Earth's surface (~9.8 m/s² or ~9.81 m/s²).",
    ),
    "G": ScientificConstant(
        symbol="G",
        name="Universal Gravitational Constant",
        value=6.67430e-11,
        unit="N·m²/kg²",
        latex_symbol="G",
        description="Newton's constant of universal gravitation.",
    ),
    "h": ScientificConstant(
        symbol="h",
        name="Planck's Constant",
        value=6.62607015e-34,
        unit="J·s",
        latex_symbol="h",
        description="Quantum of electromagnetic action relating photon energy to frequency (E = hν).",
    ),
    "hbar": ScientificConstant(
        symbol="ħ",
        name="Reduced Planck Constant (Dirac Constant)",
        value=1.054571817e-34,
        unit="J·s",
        latex_symbol="\\hbar",
        description="h / (2π), fundamental in quantum mechanics and angular momentum.",
    ),
    "N_A": ScientificConstant(
        symbol="N_A",
        name="Avogadro's Number",
        value=6.02214076e23,
        unit="mol⁻¹",
        latex_symbol="N_A",
        description="Number of constituent particles (atoms or molecules) in one mole of substance.",
    ),
    "R": ScientificConstant(
        symbol="R",
        name="Universal Gas Constant",
        value=8.314462618,
        unit="J/(mol·K)",
        latex_symbol="R",
        description="Molar gas constant in the ideal gas equation (PV = nRT). Also 0.0821 L·atm/(mol·K).",
    ),
    "k_B": ScientificConstant(
        symbol="k_B",
        name="Boltzmann Constant",
        value=1.380649e-23,
        unit="J/K",
        latex_symbol="k_B",
        description="Relates the average relative kinetic energy of particles in a gas with temperature.",
    ),
    "e": ScientificConstant(
        symbol="e",
        name="Elementary Electric Charge",
        value=1.602176634e-19,
        unit="C",
        latex_symbol="e",
        description="Magnitude of electric charge carried by a single proton or electron.",
    ),
    "m_e": ScientificConstant(
        symbol="m_e",
        name="Electron Mass",
        value=9.1093837015e-31,
        unit="kg",
        latex_symbol="m_e",
        description="Rest mass of an electron (~9.11 × 10⁻³¹ kg).",
    ),
    "m_p": ScientificConstant(
        symbol="m_p",
        name="Proton Mass",
        value=1.67262192369e-27,
        unit="kg",
        latex_symbol="m_p",
        description="Rest mass of a proton (~1.673 × 10⁻²⁷ kg).",
    ),
    "m_n": ScientificConstant(
        symbol="m_n",
        name="Neutron Mass",
        value=1.67492749804e-27,
        unit="kg",
        latex_symbol="m_n",
        description="Rest mass of a neutron (~1.675 × 10⁻²⁷ kg).",
    ),
    "eps_0": ScientificConstant(
        symbol="ε₀",
        name="Vacuum Permittivity (Electric Constant)",
        value=8.8541878128e-12,
        unit="F/m",
        latex_symbol="\\varepsilon_0",
        description="Permittivity of free space in Coulomb's Law and Maxwell's equations.",
    ),
    "mu_0": ScientificConstant(
        symbol="μ₀",
        name="Vacuum Permeability (Magnetic Constant)",
        value=1.25663706212e-6,
        unit="T·m/A",
        latex_symbol="\\mu_0",
        description="Magnetic permeability in a vacuum (4π × 10⁻⁷ T·m/A).",
    ),
    "sigma": ScientificConstant(
        symbol="σ",
        name="Stefan-Boltzmann Constant",
        value=5.670374419e-8,
        unit="W/(m²·K⁴)",
        latex_symbol="\\sigma",
        description="Constant of proportionality in Stefan-Boltzmann black-body radiation law.",
    ),
    "atm": ScientificConstant(
        symbol="1 atm",
        name="Standard Atmospheric Pressure",
        value=101325.0,
        unit="Pa",
        latex_symbol="1\\text{ atm}",
        description="Standard sea-level atmospheric pressure (101,325 Pa or 1.01325 bar or 760 mmHg).",
    ),
    "v_sound": ScientificConstant(
        symbol="v_sound",
        name="Speed of Sound in Air at 20°C",
        value=343.0,
        unit="m/s",
        latex_symbol="v_{\\text{sound}}",
        description="Speed of sound through dry air at 20 °C (68 °F).",
    ),
    "rho_water": ScientificConstant(
        symbol="ρ_water",
        name="Density of Pure Water at 4°C",
        value=1000.0,
        unit="kg/m³",
        latex_symbol="\\rho_{\\text{water}}",
        description="Maximum density of pure water (1000 kg/m³ or 1 g/cm³).",
    ),
}


def get_constant(key: str) -> ScientificConstant | None:
    """Lookup a constant by symbol or common alias."""
    clean_k = key.strip().lower()
    for symbol, c in SCIENTIFIC_CONSTANTS.items():
        if symbol.lower() == clean_k or c.name.lower() == clean_k:
            return c
    return None
