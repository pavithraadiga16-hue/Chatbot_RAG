"""
Chemistry Concepts Knowledge Base
=================================

PURPOSE:
    Comprehensive concept catalog for Chemistry spanning LKG through PUC (Grade 12).
    Provides definitions, formulas, rules, and pedagogical explanations.
"""

from typing import Optional
from pydantic import BaseModel, Field
from rapidfuzz import fuzz


class ChemistryConcept(BaseModel):
    """Metadata and content for a Chemistry concept."""
    concept_id: str
    topic: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    definition: str
    formula: Optional[str] = None
    key_points: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


CHEMISTRY_CONCEPTS_CATALOG: list[ChemistryConcept] = [
    # --- Atomic Structure & Periodicity ---
    ChemistryConcept(
        concept_id="chem.atomic.structure",
        topic="atomic_structure",
        name="Atomic Structure and Subatomic Particles",
        aliases=["atomic structure", "atom", "proton", "neutron", "electron", "atomic number", "mass number", "isotopes", "isobars"],
        keywords=["atom", "proton", "neutron", "electron", "atomic number", "mass number", "isotope", "isobar"],
        definition="An atom is the fundamental constituent unit of ordinary matter, composed of a dense positively charged nucleus (containing protons and neutrons) surrounded by a cloud of negatively charged electrons.",
        formula="Atomic Number Z = number of protons;  Mass Number A = Protons + Neutrons (Z + N)",
        key_points=[
            "Proton: Positively charged (+1.602 × 10⁻¹⁹ C), mass ≈ 1.007 u.",
            "Neutron: Electrically neutral (0 C), mass ≈ 1.008 u.",
            "Electron: Negatively charged (-1.602 × 10⁻¹⁹ C), mass ≈ 1/1836 u.",
            "Isotopes: Atoms of the same element having the SAME atomic number (Z) but DIFFERENT mass numbers (A) (e.g. Carbon-12 and Carbon-14).",
            "Isobars: Atoms of different elements having DIFFERENT atomic numbers (Z) but the SAME mass number (A) (e.g. ⁴⁰Ar and ⁴⁰Ca).",
        ],
        examples=["Hydrogen isotopes: Protium (¹H), Deuterium (²H), and Tritium (³H)"],
    ),
    ChemistryConcept(
        concept_id="chem.periodic.classification",
        topic="periodic_table",
        name="Periodic Table Trends and Periodicity",
        aliases=["periodic table", "periodic trends", "modern periodic law", "electronegativity", "ionization enthalpy", "atomic radius", "valency"],
        keywords=["periodic table", "mendeleev", "moseley", "group", "period", "electronegativity", "valency"],
        definition="The Modern Periodic Table arranges chemical elements in increasing order of their atomic numbers (Z), structured into 18 vertical Groups and 7 horizontal Periods.",
        formula="Modern Periodic Law: Physical and chemical properties of elements are periodic functions of their atomic numbers.",
        key_points=[
            "Atomic Radius: Decreases across a period (left to right) due to increasing nuclear charge; increases down a group.",
            "Ionization Enthalpy: Energy required to remove the outermost electron; increases across a period, decreases down a group.",
            "Electronegativity: Tendency of an atom to attract shared pair of electrons; Fluorine (F) is the most electronegative element (4.0).",
            "Metallic Character: Decreases across a period, increases down a group.",
        ],
        examples=["Alkali metals (Group 1: Li, Na, K) are highly reactive metals", "Halogens (Group 17: F, Cl, Br, I) are highly reactive non-metals"],
    ),
    # --- Chemical Bonding ---
    ChemistryConcept(
        concept_id="chem.bonding.types",
        topic="chemical_bonding",
        name="Chemical Bonding: Ionic and Covalent Bonds",
        aliases=["chemical bonding", "ionic bond", "covalent bond", "coordinate bond", "octet rule", "vsepr theory", "hydrogen bonding"],
        keywords=["bonding", "ionic bond", "covalent bond", "octet rule", "lewis structure", "vsepr", "hydrogen bond"],
        definition="Chemical bonding refers to the attractive forces that hold atoms or ions together to achieve a stable octet (8 valence electrons) electronic configuration.",
        formula="Octet Rule: Atoms gain, lose, or share valence electrons to achieve stable noble gas configuration (ns² np⁶).",
        key_points=[
            "Ionic Bond (Electrovalent): Formed by complete TRANSFER of electrons from metal to non-metal (e.g. Na⁺ + Cl⁻ ⟹ NaCl). High melting points, conduct electricity in molten/aqueous states.",
            "Covalent Bond: Formed by mutual SHARING of electron pairs between non-metal atoms (e.g. H₂O, CH₄). Lower melting points, non-conductors.",
            "Coordinate (Dative) Bond: A covalent bond where both shared electrons are supplied by one atom (e.g. NH₄⁺).",
            "Hydrogen Bonding: Strong dipole-dipole attraction between H bonded to F, O, or N and another electronegative atom (explains high boiling point of water).",
        ],
        examples=["Sodium Chloride (NaCl) crystal lattice held by ionic bonds", "Methane (CH₄) with 4 single covalent C-H bonds"],
    ),
    # --- Mole Concept & Stoichiometry ---
    ChemistryConcept(
        concept_id="chem.mole.concept",
        topic="mole_stoichiometry",
        name="Mole Concept and Avogadro's Number",
        aliases=["mole concept", "mole", "avogadro number", "molar mass", "molarity", "molality", "stoichiometry"],
        keywords=["mole", "avogadro", "molar mass", "molarity", "molality", "stoichiometry", "6.022"],
        definition="A mole is the SI unit of amount of substance containing exactly 6.02214076 × 10²³ elementary entities (atoms, molecules, or ions).",
        formula="Number of Moles n = mass (m) / Molar Mass (M) = N / N_A;  Molarity M = moles of solute / Volume of solution in Liters",
        key_points=[
            "1 Mole of any substance = 6.022 × 10²³ particles (Avogadro's constant N_A).",
            "Molar volume of any ideal gas at STP (Standard Temperature & Pressure) = 22.4 Liters.",
            "Molarity (M) = mol / L (temperature dependent); Molality (m) = mol / kg of solvent (temperature independent).",
        ],
        examples=["1 mole of Carbon-12 weighs exactly 12 grams and contains 6.022 × 10²³ carbon atoms", "1 mole of H₂O weighs 18 grams"],
    ),
    # --- Acids, Bases, Salts and pH ---
    ChemistryConcept(
        concept_id="chem.acids_bases.ph",
        topic="equilibrium_acids",
        name="Acids, Bases, Salts and pH Scale",
        aliases=["acids and bases", "acid", "base", "salt", "ph", "ph scale", "poh", "neutralization", "indicators", "buffer solution"],
        keywords=["acid", "base", "salt", "ph", "poh", "neutralization", "litmus", "buffer", "alkali"],
        definition="Acids are substances that produce hydrogen ions (H⁺ or H₃O⁺) in aqueous solution (pH < 7). Bases produce hydroxide ions (OH⁻) in aqueous solution (pH > 7). Neutral substances have pH = 7.",
        formula="pH = -log₁₀[H⁺];  pOH = -log₁₀[OH⁻];  pH + pOH = 14 (at 25°C);  Neutralization: Acid + Base → Salt + Water",
        key_points=[
            "Arrhenius Theory: Acid gives H⁺ in water; Base gives OH⁻ in water.",
            "Bronsted-Lowry Theory: Acid is a proton (H⁺) donor; Base is a proton acceptor.",
            "Lewis Theory: Acid is an electron-pair acceptor; Base is an electron-pair donor.",
            "Indicators: Litmus turns RED in acid and BLUE in base; Phenolphthalein is COLORLESS in acid and PINK in base.",
            "Strong acids (HCl, H₂SO₄, HNO₃) dissociate completely; Weak acids (CH₃COOH) dissociate partially.",
        ],
        examples=["Hydrochloric acid (HCl) in gastric juice (pH ~ 1.5 - 2.0)", "Sodium hydroxide (NaOH) used in soap manufacturing (pH ~ 14)"],
    ),
    # --- Chemical Reactions & Redox ---
    ChemistryConcept(
        concept_id="chem.reactions.types",
        topic="reactions",
        name="Types of Chemical Reactions and Redox",
        aliases=["chemical reactions", "types of reactions", "combination reaction", "decomposition reaction", "displacement reaction", "double displacement", "redox", "oxidation", "reduction"],
        keywords=["reaction", "combination", "decomposition", "displacement", "redox", "oxidation", "reduction"],
        definition="A chemical reaction transforms one or more substances (reactants) into new substances (products) by breaking and forming chemical bonds.",
        formula="Redox: Oxidation = Loss of electrons (LEO) / Increase in oxidation number;  Reduction = Gain of electrons (GER) / Decrease in oxidation number",
        key_points=[
            "Combination: A + B → AB (e.g. 2Mg + O₂ → 2MgO).",
            "Decomposition: AB → A + B (e.g. CaCO₃ → CaO + CO₂).",
            "Displacement: A + BC → AC + B (e.g. Fe + CuSO₄ → FeSO₄ + Cu).",
            "Double Displacement / Precipitation: AB + CD → AD + CB (e.g. AgNO₃ + NaCl → AgCl↓ + NaNO₃).",
            "Oxidizing agent gets reduced; Reducing agent gets oxidized.",
        ],
        examples=["Rusting of iron (4Fe + 3O₂ + 2xH₂O → 2Fe₂O₃·xH₂O) as a slow redox reaction", "Photosynthesis in green plants as an endothermic redox process"],
    ),
    # --- Organic Chemistry ---
    ChemistryConcept(
        concept_id="chem.organic.functional_groups",
        topic="organic",
        name="Organic Chemistry: Hydrocarbons and Functional Groups",
        aliases=["organic chemistry", "hydrocarbons", "alkanes", "alkenes", "alkynes", "functional groups", "iupac nomenclature", "alcohols", "carboxylic acids", "isomers"],
        keywords=["organic", "alkane", "alkene", "alkyne", "functional group", "alcohol", "aldehyde", "ketone", "carboxylic acid", "ester", "iupac"],
        definition="Organic chemistry is the study of carbon compounds. Carbon forms vast diverse structures due to its unique tetravalency and catenation (self-linking ability).",
        formula="Alkanes: CₙH₂ₙ₊₂;  Alkenes: CₙH₂ₙ;  Alkynes: CₙH₂ₙ₋₂;  Alcohols: R-OH;  Carboxylic Acids: R-COOH",
        key_points=[
            "Catenation: Carbon atoms form stable single, double, and triple covalent bonds with other carbon atoms.",
            "Functional Groups: -OH (Alcohol), -CHO (Aldehyde), >C=O (Ketone), -COOH (Carboxylic Acid), -NH₂ (Amine), -COOR (Ester).",
            "Homologous Series: Series of compounds with the same functional group where successive members differ by a -CH₂- unit (14 u mass).",
            "Structural Isomerism: Compounds having the same molecular formula but different structural arrangements.",
        ],
        examples=["Methane (CH₄) is the primary component of natural gas/CNG", "Ethanol (C₂H₅OH) used in beverages and sanitizers", "Acetic acid (CH₃COOH) in household vinegar"],
    ),
    # --- Environmental Chemistry ---
    ChemistryConcept(
        concept_id="chem.env.pollution",
        topic="inorganic_env",
        name="Environmental Chemistry: Greenhouse Effect and Acid Rain",
        aliases=["environmental chemistry", "greenhouse effect", "global warming", "acid rain", "ozone layer depletion", "air pollution"],
        keywords=["greenhouse", "global warming", "acid rain", "ozone depletion", "cfc", "pollution"],
        definition="Environmental chemistry examines chemical processes in the atmosphere, soil, and aquatic environments and the impact of human activity.",
        formula="Acid Rain: SO₂ + H₂O → H₂SO₃;  2SO₂ + O₂ + 2H₂O → 2H₂SO₄;  Ozone Depletion: Cl· + O₃ → ClO· + O₂",
        key_points=[
            "Greenhouse Gases: CO₂, CH₄, N₂O, H₂O vapor, and CFCs trap infrared radiation causing global warming.",
            "Acid Rain: Precipitation with pH < 5.6 caused by emissions of sulfur dioxide (SO₂) and nitrogen oxides (NOₓ).",
            "Ozone Layer Depletion: Chlorofluorocarbons (CFCs) release chlorine radicals that catalytically break down stratospheric ozone (O₃).",
        ],
        examples=["Taj Mahal discoloration and marble cancer due to acid rain (CaCO₃ + H₂SO₄ → CaSO₄ + H₂O + CO₂)", "Melting polar ice caps due to enhanced greenhouse effect"],
    ),
]


class ChemistryKnowledgeBase:
    """Indexed Chemistry knowledge repository."""

    def __init__(self) -> None:
        self.catalog = CHEMISTRY_CONCEPTS_CATALOG
        self._index: dict[str, ChemistryConcept] = {c.concept_id: c for c in self.catalog}

    def find_by_query(self, query: str, threshold: float = 65.0) -> list[tuple[ChemistryConcept, float]]:
        """Matches query using RapidFuzz."""
        lower_q = query.lower().strip()
        matches = []

        for concept in self.catalog:
            best_score = 0.0
            score_name = fuzz.token_set_ratio(concept.name.lower(), lower_q)
            best_score = max(best_score, score_name)

            for alias in concept.aliases:
                score_alias = fuzz.token_set_ratio(alias.lower(), lower_q)
                best_score = max(best_score, score_alias)

            for kw in concept.keywords:
                if kw in lower_q:
                    best_score = max(best_score, 85.0)

            if best_score >= threshold:
                matches.append((concept, best_score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def get_by_id(self, concept_id: str) -> Optional[ChemistryConcept]:
        return self._index.get(concept_id)


# Global instance
chemistry_kb = ChemistryKnowledgeBase()
