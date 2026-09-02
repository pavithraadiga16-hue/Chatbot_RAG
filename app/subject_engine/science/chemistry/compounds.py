"""
Common Chemical Compounds Knowledge Base & Formula Resolver
============================================================

PURPOSE:
    Curated database of standard chemical compounds from LKG through PUC (Grade 12).
    Enables instant, deterministic lookups for questions like:
    - "what is the chemical formula of water"
    - "what water formula"
    - "formula of baking soda"
    - "chemical formula for common salt"
    - "glucose formula"
    - "rust formula"
"""

import re
from typing import Optional
from pydantic import BaseModel, Field
from rapidfuzz import fuzz


class ChemicalCompound(BaseModel):
    """Structured data for a chemical compound."""
    compound_id: str
    common_name: str
    chemical_name: str
    formula: str
    unicode_formula: str
    molar_mass: str
    elements: list[str]
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    structure_or_type: Optional[str] = None
    properties_and_uses: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)


COMPOUNDS_CATALOG: list[ChemicalCompound] = [
    # 1. Water & Hydrides
    ChemicalCompound(
        compound_id="chem.comp.water",
        common_name="Water",
        chemical_name="Dihydrogen Monoxide / Oxidane",
        formula="H2O",
        unicode_formula="H₂O",
        molar_mass="18.015 g/mol",
        elements=["Hydrogen (H)", "Oxygen (O)"],
        aliases=["water", "drinking water", "aqua", "dihydrogen monoxide", "h2o", "water formula", "formula of water", "what water formula"],
        keywords=["water", "h2o", "dihydrogen", "aqua", "oxidane", "universal solvent"],
        structure_or_type="Covalent compound with bent / V-shaped geometry (bond angle ≈ 104.5°).",
        properties_and_uses=[
            "Universal solvent with high dielectric constant.",
            "Maximum density of 1.00 g/cm³ at 4°C due to anomalous expansion.",
            "Neutral pH = 7.0 at 25°C.",
            "Crucial for biological cellular respiration, hydration, and enzymatic transport.",
        ],
        key_points=[
            "Chemical formula is **H₂O** (2 atoms of Hydrogen, 1 atom of Oxygen).",
            "Molar mass is 18.015 g/mol (Hydrogen: 1.008 × 2, Oxygen: 16.00).",
            "Exhibits strong intermolecular hydrogen bonding resulting in high boiling point (100°C) and surface tension.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.heavy_water",
        common_name="Heavy Water",
        chemical_name="Deuterium Oxide",
        formula="D2O",
        unicode_formula="D₂O",
        molar_mass="20.028 g/mol",
        elements=["Deuterium (²H or D)", "Oxygen (O)"],
        aliases=["heavy water", "deuterium oxide", "d2o"],
        keywords=["heavy water", "deuterium", "d2o", "nuclear moderator"],
        structure_or_type="Isotopic variant of water with deuterium (heavy hydrogen).",
        properties_and_uses=[
            "Used as a neutron moderator and coolant in nuclear reactors (e.g. CANDU reactors).",
            "Denser than ordinary water (density ≈ 1.11 g/cm³ at 20°C).",
        ],
        key_points=["Chemical formula is **D₂O**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.hydrogen_peroxide",
        common_name="Hydrogen Peroxide",
        chemical_name="Hydrogen Peroxide",
        formula="H2O2",
        unicode_formula="H₂O₂",
        molar_mass="34.015 g/mol",
        elements=["Hydrogen (H)", "Oxygen (O)"],
        aliases=["hydrogen peroxide", "h2o2"],
        keywords=["hydrogen peroxide", "peroxide", "h2o2", "antiseptic", "bleaching agent"],
        structure_or_type="Open-book non-planar structure containing an -O-O- peroxide bond.",
        properties_and_uses=["Used as a mild antiseptic, disinfectant, and industrial bleaching agent."],
        key_points=["Chemical formula is **H₂O₂**."],
    ),

    # 2. Common Salts & Minerals
    ChemicalCompound(
        compound_id="chem.comp.sodium_chloride",
        common_name="Common Salt / Table Salt / Rock Salt",
        chemical_name="Sodium Chloride",
        formula="NaCl",
        unicode_formula="NaCl",
        molar_mass="58.44 g/mol",
        elements=["Sodium (Na)", "Chlorine (Cl)"],
        aliases=["salt", "common salt", "table salt", "rock salt", "sodium chloride", "halite", "nacl", "salt formula", "formula of salt"],
        keywords=["salt", "table salt", "common salt", "sodium chloride", "nacl", "saline"],
        structure_or_type="Face-Centered Cubic (FCC) giant ionic lattice (Na⁺ : Cl⁻ = 1 : 1).",
        properties_and_uses=[
            "Essential dietary electrolyte maintaining fluid balance and nerve transmission.",
            "Raw material for manufacturing NaOH (caustic soda), chlorine gas, and sodium carbonate.",
            "Used for food preservation and de-icing snowy roads.",
        ],
        key_points=[
            "Chemical formula is **NaCl** (1 Sodium ion Na⁺, 1 Chloride ion Cl⁻).",
            "Molar mass is 58.44 g/mol (Sodium: 22.99, Chlorine: 35.45).",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.baking_soda",
        common_name="Baking Soda",
        chemical_name="Sodium Bicarbonate / Sodium Hydrogen Carbonate",
        formula="NaHCO3",
        unicode_formula="NaHCO₃",
        molar_mass="84.007 g/mol",
        elements=["Sodium (Na)", "Hydrogen (H)", "Carbon (C)", "Oxygen (O)"],
        aliases=["baking soda", "sodium bicarbonate", "sodium hydrogen carbonate", "nahco3", "baking soda formula", "formula of baking soda"],
        keywords=["baking soda", "sodium bicarbonate", "nahco3", "baking powder", "antacid", "leavening"],
        structure_or_type="Ionic salt formed from sodium cation Na⁺ and bicarbonate anion HCO₃⁻.",
        properties_and_uses=[
            "Leavening agent in baking: decomposes on heating to release CO₂ gas (making dough fluffy).",
            "Used as an antacid to relieve stomach acidity and in soda-acid fire extinguishers.",
        ],
        key_points=[
            "Chemical formula is **NaHCO₃**.",
            "Thermal decomposition: 2 NaHCO₃ ⟶ Na₂CO₃ + H₂O + CO₂↑.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.washing_soda",
        common_name="Washing Soda",
        chemical_name="Sodium Carbonate Decahydrate",
        formula="Na2CO3.10H2O",
        unicode_formula="Na₂CO₃·10H₂O",
        molar_mass="286.14 g/mol (Decahydrate) / 105.99 g/mol (Anhydrous Soda Ash)",
        elements=["Sodium (Na)", "Carbon (C)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["washing soda", "sodium carbonate", "soda ash", "na2co3", "na2co3.10h2o", "washing soda formula"],
        keywords=["washing soda", "sodium carbonate", "soda ash", "decahydrate", "laundry", "hard water"],
        structure_or_type="Hydrated crystalline carbonate salt with 10 water molecules of crystallization.",
        properties_and_uses=[
            "Used in laundry detergent and soap manufacturing.",
            "Removes permanent hardness of water by precipitating Ca²⁺ and Mg²⁺ ions as carbonates.",
            "Used in glass, paper, and textile manufacturing.",
        ],
        key_points=[
            "Chemical formula is **Na₂CO₃·10H₂O** (anhydrous form: Na₂CO₃).",
            "Efflorescent: loses 9 water molecules when exposed to dry air to form monohydrate.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.caustic_soda",
        common_name="Caustic Soda / Lye",
        chemical_name="Sodium Hydroxide",
        formula="NaOH",
        unicode_formula="NaOH",
        molar_mass="39.997 g/mol",
        elements=["Sodium (Na)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["caustic soda", "lye", "sodium hydroxide", "naoh", "caustic soda formula"],
        keywords=["caustic soda", "lye", "sodium hydroxide", "naoh", "strong base", "alkali", "saponification"],
        structure_or_type="Strong ionic alkali base dissociating fully into Na⁺ and OH⁻ in water.",
        properties_and_uses=[
            "Strong base (pH ≈ 14 in 1 M solution) used in soap and paper manufacturing.",
            "Highly deliquescent white solid that absorbs moisture and CO₂ from air.",
        ],
        key_points=["Chemical formula is **NaOH**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.caustic_potash",
        common_name="Caustic Potash",
        chemical_name="Potassium Hydroxide",
        formula="KOH",
        unicode_formula="KOH",
        molar_mass="56.106 g/mol",
        elements=["Potassium (K)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["caustic potash", "potassium hydroxide", "koh", "potash lye"],
        keywords=["caustic potash", "potassium hydroxide", "koh", "soft soap", "alkali"],
        structure_or_type="Strong alkali base forming K⁺ and OH⁻ ions.",
        properties_and_uses=["Used in making soft soaps, alkaline batteries electrolyte, and biodiesels."],
        key_points=["Chemical formula is **KOH**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.bleaching_powder",
        common_name="Bleaching Powder",
        chemical_name="Calcium Oxychloride / Calcium Hypochlorite",
        formula="CaOCl2",
        unicode_formula="CaOCl₂",
        molar_mass="126.98 g/mol",
        elements=["Calcium (Ca)", "Oxygen (O)", "Chlorine (Cl)"],
        aliases=["bleaching powder", "calcium oxychloride", "calcium hypochlorite", "caocl2", "bleaching powder formula"],
        keywords=["bleaching powder", "calcium oxychloride", "caocl2", "chlorination", "disinfectant water"],
        structure_or_type="Mixed calcium salt Ca(OCl)Cl synthesized by reacting slaked lime with chlorine gas.",
        properties_and_uses=[
            "Disinfectant and sterilizer for drinking water purification.",
            "Bleaching agent for cotton and linen textiles, and wood pulp in paper factories.",
        ],
        key_points=[
            "Chemical formula is **CaOCl₂** (or Ca(OCl)Cl).",
            "Synthesis: Ca(OH)₂ + Cl₂ ⟶ CaOCl₂ + H₂O.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.quicklime",
        common_name="Quicklime / Burnt Lime",
        chemical_name="Calcium Oxide",
        formula="CaO",
        unicode_formula="CaO",
        molar_mass="56.077 g/mol",
        elements=["Calcium (Ca)", "Oxygen (O)"],
        aliases=["quicklime", "quick lime", "burnt lime", "calcium oxide", "cao", "quicklime formula"],
        keywords=["quicklime", "calcium oxide", "cao", "burnt lime", "white lime"],
        structure_or_type="Basic metal oxide with high melting point (2,613°C).",
        properties_and_uses=[
            "Reacts vigorously with water (slaking) in an exothermic reaction releasing immense heat.",
            "Used in cement, steelmaking, mortar, and flue-gas desulfurization.",
        ],
        key_points=[
            "Chemical formula is **CaO**.",
            "Slaking reaction: CaO + H₂O ⟶ Ca(OH)₂ + Heat.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.slaked_lime",
        common_name="Slaked Lime / Lime Water / Milk of Lime",
        chemical_name="Calcium Hydroxide",
        formula="Ca(OH)2",
        unicode_formula="Ca(OH)₂",
        molar_mass="74.093 g/mol",
        elements=["Calcium (Ca)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["slaked lime", "limewater", "lime water", "milk of lime", "calcium hydroxide", "ca(oh)2", "slaked lime formula"],
        keywords=["slaked lime", "limewater", "calcium hydroxide", "ca(oh)2", "white wash", "co2 test"],
        structure_or_type="Sparingly soluble basic hydroxide.",
        properties_and_uses=[
            "Turns milky when CO₂ gas is bubbled through it due to insoluble CaCO₃ precipitate formation.",
            "Used for white washing walls, neutralizing acidic soils, and wastewater treatment.",
        ],
        key_points=[
            "Chemical formula is **Ca(OH)₂**.",
            "CO₂ test: Ca(OH)₂ + CO₂ ⟶ CaCO₃↓ (milky) + H₂O.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.limestone",
        common_name="Limestone / Marble / Chalk",
        chemical_name="Calcium Carbonate",
        formula="CaCO3",
        unicode_formula="CaCO₃",
        molar_mass="100.086 g/mol",
        elements=["Calcium (Ca)", "Carbon (C)", "Oxygen (O)"],
        aliases=["limestone", "marble", "chalk", "calcite", "calcium carbonate", "caco3", "limestone formula", "marble formula", "chalk formula"],
        keywords=["limestone", "marble", "chalk", "calcium carbonate", "caco3", "eggshell"],
        structure_or_type="Insoluble carbonate mineral; major component of rocks, marble, and eggshells.",
        properties_and_uses=[
            "Primary building material, marble stone, classroom chalk, and antacid tablets.",
            "Thermal decomposition gives quicklime: CaCO₃ ⟶ CaO + CO₂.",
        ],
        key_points=["Chemical formula is **CaCO₃**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.plaster_of_paris",
        common_name="Plaster of Paris (POP)",
        chemical_name="Calcium Sulfate Hemihydrate",
        formula="CaSO4.0.5H2O",
        unicode_formula="CaSO₄·½H₂O",
        molar_mass="145.15 g/mol",
        elements=["Calcium (Ca)", "Sulfur (S)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["plaster of paris", "pop", "calcium sulfate hemihydrate", "caso4.1/2h2o", "caso4.0.5h2o", "pop formula"],
        keywords=["plaster of paris", "pop", "hemihydrate", "fracture cast", "statues", "gypsum heating"],
        structure_or_type="Hemihydrate sulfate salt.",
        properties_and_uses=[
            "Used in orthopedic casts for setting fractured bones.",
            "Making decorative casts, false ceilings, pottery, and statues.",
            "Sets into hard solid mass (Gypsum) upon mixing with water.",
        ],
        key_points=[
            "Chemical formula is **CaSO₄·½H₂O** (or (CaSO₄)₂·H₂O).",
            "Setting reaction: CaSO₄·½H₂O + 1½ H₂O ⟶ CaSO₄·2H₂O (Gypsum).",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.gypsum",
        common_name="Gypsum",
        chemical_name="Calcium Sulfate Dihydrate",
        formula="CaSO4.2H2O",
        unicode_formula="CaSO₄·2H₂O",
        molar_mass="172.17 g/mol",
        elements=["Calcium (Ca)", "Sulfur (S)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["gypsum", "calcium sulfate dihydrate", "caso4.2h2o", "gypsum formula"],
        keywords=["gypsum", "dihydrate", "cement retarding", "fertilizer gypsum"],
        structure_or_type="Naturally occurring sulfate mineral with 2 water molecules of crystallization.",
        properties_and_uses=[
            "Added to Portland cement (2-3%) to retard and control initial setting time.",
            "Heated to 373 K (100°C) to manufacture Plaster of Paris: CaSO₄·2H₂O ⟶ CaSO₄·½H₂O + 1½ H₂O.",
        ],
        key_points=["Chemical formula is **CaSO₄·2H₂O**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.blue_vitriol",
        common_name="Blue Vitriol",
        chemical_name="Copper(II) Sulfate Pentahydrate",
        formula="CuSO4.5H2O",
        unicode_formula="CuSO₄·5H₂O",
        molar_mass="249.68 g/mol",
        elements=["Copper (Cu)", "Sulfur (S)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["blue vitriol", "copper sulfate", "cupric sulfate", "cuso4.5h2o", "blue vitriol formula"],
        keywords=["blue vitriol", "copper sulfate", "pentahydrate", "blue crystals", "fungicide"],
        structure_or_type="Bright blue crystalline hydrated salt.",
        properties_and_uses=["Used as an agricultural fungicide (Bordeaux mixture), electroplating electrolyte, and in chemical analysis."],
        key_points=[
            "Chemical formula is **CuSO₄·5H₂O**.",
            "Anhydrous CuSO₄ is white; turns blue upon absorbing moisture (test for water).",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.green_vitriol",
        common_name="Green Vitriol",
        chemical_name="Ferrous Sulfate Heptahydrate",
        formula="FeSO4.7H2O",
        unicode_formula="FeSO₄·7H₂O",
        molar_mass="278.01 g/mol",
        elements=["Iron (Fe)", "Sulfur (S)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["green vitriol", "ferrous sulfate", "feso4.7h2o", "iron sulfate"],
        keywords=["green vitriol", "ferrous sulfate", "heptahydrate", "green crystals"],
        structure_or_type="Light green crystalline hydrated iron salt.",
        properties_and_uses=["Used as an iron supplement for anemia, water purification flocculant, and dye mordant."],
        key_points=["Chemical formula is **FeSO₄·7H₂O**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.potash_alum",
        common_name="Potash Alum / Fitkari / Alum",
        chemical_name="Potassium Aluminium Sulfate Dodecahydrate",
        formula="KAl(SO4)2.12H2O",
        unicode_formula="KAl(SO₄)₂·12H₂O",
        molar_mass="474.39 g/mol",
        elements=["Potassium (K)", "Aluminium (Al)", "Sulfur (S)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["potash alum", "alum", "fitkari", "kal(so4)2.12h2o", "alum formula"],
        keywords=["potash alum", "alum", "fitkari", "water coagulant", "aftershave astringent"],
        structure_or_type="Double salt crystalline compound.",
        properties_and_uses=["Used for rapid coagulation and purification of turbid water, and as a styptic (stops bleeding from minor cuts)."],
        key_points=["Chemical formula is **KAl(SO₄)₂·12H₂O**."],
    ),

    # 3. Acids
    ChemicalCompound(
        compound_id="chem.comp.hydrochloric_acid",
        common_name="Hydrochloric Acid / Muriatic Acid",
        chemical_name="Hydrochloric Acid",
        formula="HCl",
        unicode_formula="HCl",
        molar_mass="36.46 g/mol",
        elements=["Hydrogen (H)", "Chlorine (Cl)"],
        aliases=["hydrochloric acid", "hcl", "muriatic acid", "hydrochloric acid formula"],
        keywords=["hydrochloric acid", "hcl", "muriatic acid", "gastric acid", "strong acid"],
        structure_or_type="Strong monoprotic mineral acid.",
        properties_and_uses=[
            "Gastric acid present in human stomach (pH ≈ 1.5 - 2.0) for protein digestion and destroying bacteria.",
            "Industrial acid for pickling steel, pH regulation, and leather processing.",
        ],
        key_points=["Chemical formula is **HCl**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.sulfuric_acid",
        common_name="Sulfuric Acid / King of Chemicals / Battery Acid / Oil of Vitriol",
        chemical_name="Sulfuric Acid",
        formula="H2SO4",
        unicode_formula="H₂SO₄",
        molar_mass="98.079 g/mol",
        elements=["Hydrogen (H)", "Sulfur (S)", "Oxygen (O)"],
        aliases=["sulfuric acid", "sulphuric acid", "h2so4", "oil of vitriol", "battery acid", "king of chemicals", "sulfuric acid formula"],
        keywords=["sulfuric acid", "sulphuric acid", "h2so4", "king of chemicals", "battery acid", "dehydrating agent"],
        structure_or_type="Strong diprotic mineral acid and powerful dehydrating agent.",
        properties_and_uses=[
            "Known as the 'King of Chemicals' due to immense industrial utility (fertilizers, chemicals, petroleum refining).",
            "Lead-acid car batteries electrolyte.",
        ],
        key_points=[
            "Chemical formula is **H₂SO₄**.",
            "Strongly exothermic on dilution (Always add Acid to Water, NEVER Water to Acid).",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.nitric_acid",
        common_name="Nitric Acid / Aqua Fortis",
        chemical_name="Nitric Acid",
        formula="HNO3",
        unicode_formula="HNO₃",
        molar_mass="63.012 g/mol",
        elements=["Hydrogen (H)", "Nitrogen (N)", "Oxygen (O)"],
        aliases=["nitric acid", "hno3", "aqua fortis", "nitric acid formula"],
        keywords=["nitric acid", "hno3", "aqua fortis", "oxidizing acid", "fertilizers", "explosives"],
        structure_or_type="Strong monoprotic acid and powerful oxidizing agent.",
        properties_and_uses=[
            "Manufacturing ammonium nitrate fertilizers and explosives (TNT, nitroglycerin).",
            "Mixed with HCl in 1:3 ratio to prepare Aqua Regia (dissolves gold and platinum).",
        ],
        key_points=["Chemical formula is **HNO₃**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.acetic_acid",
        common_name="Vinegar / Acetic Acid / Ethanoic Acid",
        chemical_name="Ethanoic Acid",
        formula="CH3COOH",
        unicode_formula="CH₃COOH",
        molar_mass="60.052 g/mol",
        elements=["Carbon (C)", "Hydrogen (H)", "Oxygen (O)"],
        aliases=["vinegar", "acetic acid", "ethanoic acid", "ch3cooh", "vinegar formula", "acetic acid formula"],
        keywords=["vinegar", "acetic acid", "ethanoic acid", "ch3cooh", "glacial acetic acid"],
        structure_or_type="Weak organic carboxylic acid (contains -COOH functional group).",
        properties_and_uses=[
            "Vinegar is a 5-8% aqueous solution of acetic acid used in food cooking and pickling preservation.",
            "Pure anhydrous form freezes at 16.6°C (Glacial Acetic Acid).",
        ],
        key_points=["Chemical formula is **CH₃COOH** (or C₂H₄O₂)."],
    ),

    # 4. Organic Compounds & Fuels
    ChemicalCompound(
        compound_id="chem.comp.glucose",
        common_name="Glucose / Dextrose / Blood Sugar",
        chemical_name="D-Glucose",
        formula="C6H12O6",
        unicode_formula="C₆H₁₂O₆",
        molar_mass="180.156 g/mol",
        elements=["Carbon (C)", "Hydrogen (H)", "Oxygen (O)"],
        aliases=["glucose", "dextrose", "blood sugar", "c6h12o6", "glucose formula", "formula of glucose"],
        keywords=["glucose", "dextrose", "c6h12o6", "monosaccharide", "cellular energy", "photosynthesis product"],
        structure_or_type="Simple aldohexose monosaccharide carbohydrate.",
        properties_and_uses=[
            "Primary energy source for living cells in cellular respiration: C₆H₁₂O₆ + 6O₂ ⟶ 6CO₂ + 6H₂O + 38 ATP.",
            "Main product synthesized by plants during photosynthesis.",
        ],
        key_points=[
            "Chemical formula is **C₆H₁₂O₆**.",
            "Molar mass is 180.156 g/mol.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.sucrose",
        common_name="Sucrose / Table Sugar / Cane Sugar",
        chemical_name="Sucrose",
        formula="C12H22O11",
        unicode_formula="C₁₂H₂₂O₁₁",
        molar_mass="342.30 g/mol",
        elements=["Carbon (C)", "Hydrogen (H)", "Oxygen (O)"],
        aliases=["sucrose", "sugar", "table sugar", "cane sugar", "c12h22o11", "sugar formula", "formula of sugar"],
        keywords=["sucrose", "sugar", "cane sugar", "c12h22o11", "disaccharide", "sweetener"],
        structure_or_type="Disaccharide carbohydrate composed of glucose and fructose linked by glycosidic bond.",
        properties_and_uses=["Common everyday table sweetener extracted from sugarcane and sugar beets."],
        key_points=["Chemical formula is **C₁₂H₂₂O₁₁**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.methane",
        common_name="Methane / Natural Gas / Marsh Gas / Biogas / Gobar Gas",
        chemical_name="Methane",
        formula="CH4",
        unicode_formula="CH₄",
        molar_mass="16.043 g/mol",
        elements=["Carbon (C)", "Hydrogen (H)"],
        aliases=["methane", "natural gas", "marsh gas", "biogas", "gobar gas", "ch4", "methane formula", "formula of methane"],
        keywords=["methane", "ch4", "marsh gas", "natural gas", "biogas", "alkane", "cng"],
        structure_or_type="Simplest saturated hydrocarbon (alkane) with tetrahedral geometry (bond angle 109.5°).",
        properties_and_uses=[
            "Principal constituent (70-90%) of CNG (Compressed Natural Gas) and Biogas (Gobar Gas).",
            "Clean burning domestic and vehicular fuel: CH₄ + 2O₂ ⟶ CO₂ + 2H₂O + Heat.",
            "Potent greenhouse gas with high global warming potential.",
        ],
        key_points=["Chemical formula is **CH₄**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.ethanol",
        common_name="Ethanol / Ethyl Alcohol / Grain Alcohol",
        chemical_name="Ethanol",
        formula="C2H5OH",
        unicode_formula="C₂H₅OH",
        molar_mass="46.069 g/mol",
        elements=["Carbon (C)", "Hydrogen (H)", "Oxygen (O)"],
        aliases=["ethanol", "alcohol", "ethyl alcohol", "grain alcohol", "c2h5oh", "ethanol formula", "alcohol formula"],
        keywords=["ethanol", "alcohol", "ethyl alcohol", "c2h5oh", "biofuel", "hand sanitizer"],
        structure_or_type="Primary alcohol containing the hydroxyl (-OH) functional group.",
        properties_and_uses=[
            "Active ingredient in alcoholic beverages, perfume solvents, and 70% hand sanitizers.",
            "Renewable biofuel blended with gasoline (E20 petrol).",
        ],
        key_points=["Chemical formula is **C₂H₅OH** (or CH₃CH₂OH)."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.benzene",
        common_name="Benzene",
        chemical_name="Benzene",
        formula="C6H6",
        unicode_formula="C₆H₆",
        molar_mass="78.114 g/mol",
        elements=["Carbon (C)", "Hydrogen (H)"],
        aliases=["benzene", "c6h6", "benzene formula"],
        keywords=["benzene", "c6h6", "aromatic", "kekule", "resonance ring"],
        structure_or_type="Planar cyclic aromatic hydrocarbon with delocalized pi-electron ring (Hückel 4n+2 rule).",
        properties_and_uses=["Precursor for synthesis of plastics, resins, synthetic fibers, dyes, and detergents."],
        key_points=["Chemical formula is **C₆H₆**."],
    ),

    # 5. Gases & Environmental
    ChemicalCompound(
        compound_id="chem.comp.carbon_dioxide",
        common_name="Carbon Dioxide / Dry Ice (Solid)",
        chemical_name="Carbon Dioxide",
        formula="CO2",
        unicode_formula="CO₂",
        molar_mass="44.01 g/mol",
        elements=["Carbon (C)", "Oxygen (O)"],
        aliases=["carbon dioxide", "co2", "dry ice", "carbon dioxide formula", "dry ice formula"],
        keywords=["carbon dioxide", "co2", "dry ice", "greenhouse gas", "photosynthesis reactant", "fire extinguisher"],
        structure_or_type="Linear non-polar covalent molecule (O=C=O) with zero net dipole moment.",
        properties_and_uses=[
            "Solid CO₂ is called 'Dry Ice' which sublimes directly at -78.5°C without melting into liquid.",
            "Reactant absorbed by green plants during photosynthesis to generate glucose.",
            "Key greenhouse gas and compressed extinguishing agent in fire extinguishers.",
        ],
        key_points=["Chemical formula is **CO₂**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.ammonia",
        common_name="Ammonia",
        chemical_name="Ammonia / Azane",
        formula="NH3",
        unicode_formula="NH₃",
        molar_mass="17.031 g/mol",
        elements=["Nitrogen (N)", "Hydrogen (H)"],
        aliases=["ammonia", "nh3", "ammonia formula", "formula of ammonia"],
        keywords=["ammonia", "nh3", "haber process", "fertilizers urea", "pungent gas", "basic gas"],
        structure_or_type="Trigonal pyramidal covalent molecule with one lone pair on nitrogen (bond angle ≈ 107°).",
        properties_and_uses=[
            "Pungent smelling basic gas synthesized via the industrial Haber Process (N₂ + 3H₂ ⇌ 2NH₃).",
            "Essential precursor for 80%+ of commercial nitrogenous fertilizers (Urea, Ammonium Nitrate).",
        ],
        key_points=["Chemical formula is **NH₃**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.nitrous_oxide",
        common_name="Laughing Gas / Nitrous Oxide",
        chemical_name="Dinitrogen Monoxide",
        formula="N2O",
        unicode_formula="N₂O",
        molar_mass="44.013 g/mol",
        elements=["Nitrogen (N)", "Oxygen (O)"],
        aliases=["laughing gas", "nitrous oxide", "dinitrogen monoxide", "n2o", "laughing gas formula"],
        keywords=["laughing gas", "nitrous oxide", "n2o", "dental anesthetic"],
        structure_or_type="Linear neutral nitrogen oxide.",
        properties_and_uses=["Used as a mild anesthetic in dentistry and surgery, and rocket motor oxidizer."],
        key_points=["Chemical formula is **N₂O**."],
    ),
    ChemicalCompound(
        compound_id="chem.comp.ozone",
        common_name="Ozone",
        chemical_name="Trioxygen",
        formula="O3",
        unicode_formula="O₃",
        molar_mass="48.00 g/mol",
        elements=["Oxygen (O)"],
        aliases=["ozone", "o3", "ozone formula", "trioxygen"],
        keywords=["ozone", "o3", "ozone layer", "uv absorption", "stratosphere", "cfc depletion"],
        structure_or_type="Allotrope of oxygen with bent resonance structure.",
        properties_and_uses=[
            "Forms the protective Ozone Layer in the stratosphere shielding Earth from harmful Solar UV-B radiation.",
            "Powerful disinfectant and water purifier.",
        ],
        key_points=[
            "Chemical formula is **O₃** (composed of 3 oxygen atoms).",
            "Depleted by chlorofluorocarbons (CFCs) forming the Antarctic ozone hole.",
        ],
    ),
    ChemicalCompound(
        compound_id="chem.comp.rust",
        common_name="Rust",
        chemical_name="Hydrated Iron(III) Oxide",
        formula="Fe2O3.xH2O",
        unicode_formula="Fe₂O₃·xH₂O",
        molar_mass="Variable (~159.69 g/mol anhydrous)",
        elements=["Iron (Fe)", "Oxygen (O)", "Hydrogen (H)"],
        aliases=["rust", "rusting", "iron rust", "fe2o3.xh2o", "rust formula", "formula of rust"],
        keywords=["rust", "corrosion", "fe2o3", "galvanization", "iron oxide"],
        structure_or_type="Reddish-brown flaky corrosion product formed when iron reacts with oxygen and moisture.",
        properties_and_uses=["Product of electrochemical corrosion of iron. Prevented by galvanization (zinc coating), painting, and greasing."],
        key_points=[
            "Chemical formula is **Fe₂O₃·xH₂O** (Hydrated Ferric Oxide).",
            "Both Oxygen (O₂) and Moisture (H₂O) are mandatory for rusting.",
        ],
    ),
]


class CompoundsKB:
    """In-memory searchable knowledge base for Chemical Compounds."""

    def __init__(self):
        self._catalog = COMPOUNDS_CATALOG
        self._id_map: dict[str, ChemicalCompound] = {c.compound_id: c for c in self._catalog}

    def get(self, compound_id: str) -> Optional[ChemicalCompound]:
        return self._id_map.get(compound_id)

    def find_by_query(self, query: str, threshold: float = 70.0) -> list[tuple[ChemicalCompound, float]]:
        """Finds matching chemical compounds using fuzzy and exact pattern matching."""
        lower_q = query.lower().strip()
        # Clean common prefixes/fillers
        cleaned = re.sub(r'^(what\s+is\s+(the\s+)?(chemical\s+)?formula\s+(of|for)\s+|formula\s+(of|for)\s+|chemical\s+formula\s+(of|for)\s+|what\s+is\s+|what\s+)', '', lower_q).strip()
        cleaned = re.sub(r'\s+formula$', '', cleaned).strip()
        cleaned = re.sub(r'[?!.]', '', cleaned).strip()

        scored: list[tuple[ChemicalCompound, float]] = []

        for comp in self._catalog:
            best_score = 0.0

            # 1. Check aliases & formula names
            for alias in comp.aliases:
                alias_l = alias.lower()
                if alias_l == lower_q or alias_l == cleaned:
                    best_score = max(best_score, 100.0)
                elif len(alias_l) <= 4:
                    # Short formulas (e.g. h2o, d2o, cao, nacl, co2) require whole word match
                    if re.search(r'\b' + re.escape(alias_l) + r'\b', lower_q):
                        best_score = max(best_score, 95.0)
                else:
                    if alias_l in lower_q:
                        best_score = max(best_score, 90.0)
                    else:
                        ratio = fuzz.ratio(alias_l, cleaned)
                        token = fuzz.token_sort_ratio(alias_l, cleaned)
                        best_score = max(best_score, ratio, token)

            # 2. Match compound common name
            if len(comp.common_name) > 4:
                ratio_name = fuzz.ratio(comp.common_name.lower(), cleaned)
                token_name = fuzz.token_sort_ratio(comp.common_name.lower(), cleaned)
                best_score = max(best_score, ratio_name, token_name)

            if best_score >= threshold:
                scored.append((comp, best_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored



# Global CompoundsKB instance
compounds_kb = CompoundsKB()
