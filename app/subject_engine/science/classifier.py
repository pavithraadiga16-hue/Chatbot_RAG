"""
Science Intent and Branch Classifier (RapidFuzz-Powered)
========================================================

PURPOSE:
    Classifies natural student questions into:
    - Subject/Branch: Physics, Chemistry, or Biology
    - Intent: Calculate, Explain Concept, Balance Equation, Periodic Lookup, Formula Lookup, Difference/Comparison
    - Confidence score (0.0 to 1.0)
"""

import re
from typing import Optional
from pydantic import BaseModel
from rapidfuzz import fuzz

from app.subject_engine.base import SubjectType, QuestionIntent


class ScienceClassification(BaseModel):
    """Result of science intent classification."""
    is_science: bool
    branch: Optional[SubjectType] = None
    topic: Optional[str] = None
    intent: QuestionIntent = QuestionIntent.UNKNOWN
    confidence: float = 0.0
    matched_keyword: Optional[str] = None


# Branch Keywords and Signatures
PHYSICS_KEYWORDS = [
    "velocity", "speed", "acceleration", "force", "mass", "weight", "gravity", "gravitation",
    "friction", "momentum", "impulse", "work", "kinetic energy", "potential energy", "power",
    "density", "pressure", "buoyancy", "archimedes", "pascal", "hooke", "stress", "strain",
    "heat", "temperature", "calorimetry", "thermodynamics", "isothermal", "adiabatic", "carnot",
    "wave", "wavelength", "frequency", "amplitude", "sound", "echo", "doppler", "pitch", "loudness",
    "optics", "reflection", "refraction", "mirror", "lens", "snell", "focal length", "prism", "dispersion",
    "electricity", "current", "voltage", "resistance", "resistivity", "ohm", "circuit", "capacitor",
    "capacitance", "electric field", "potential difference", "magnetism", "magnetic field", "lorentz",
    "biot savart", "ampere", "faraday", "lenz", "electromagnetic induction", "transformer", "generator",
    "alternating current", "rms", "impedance", "em wave", "photon", "photoelectric", "work function",
    "de broglie", "bohr", "hydrogen spectrum", "radioactivity", "half life", "nuclear fission", "nuclear fusion",
    "semiconductor", "diode", "transistor", "logic gate", "newton law", "kepler law", "ohm law",
]

CHEMISTRY_KEYWORDS = [
    "atomic mass", "atomic number", "valency", "valence", "electron", "proton", "neutron",
    "electronic configuration", "isotope", "isobar", "orbital", "aufbau", "hund", "pauli",
    "periodic table", "molar mass", "molecular mass", "formula mass", "mole", "avogadro",
    "stoichiometry", "limiting reagent", "percentage composition", "empirical formula",
    "balance", "chemical reaction", "equation", "redox", "oxidation", "reduction", "oxidizing agent",
    "reducing agent", "ionic bond", "covalent bond", "coordinate bond", "vsepr", "hybridization",
    "hydrogen bond", "acid", "base", "salt", "ph", "poh", "indicator", "neutralization", "buffer",
    "molarity", "molality", "solute", "solvent", "concentration", "osmosis", "boyle", "charles",
    "ideal gas", "enthalpy", "exothermic", "endothermic", "hess law", "equilibrium", "le chatelier",
    "galvanic cell", "electrolysis", "nernst", "faraday law of electrolysis", "rate of reaction",
    "rate constant", "activation energy", "arrhenius", "catalyst", "organic chemistry", "alkane",
    "alkene", "alkyne", "functional group", "alcohol", "aldehyde", "ketone", "carboxylic acid",
    "ester", "amine", "ether", "benzene", "polymer", "isomerism", "iupac", "metallurgy", "ore",
    "alloy", "greenhouse effect", "acid rain", "ozone depletion", "h2o", "h2so4", "caco3", "nacl",
    "water", "water formula", "formula of water", "common salt", "table salt", "baking soda",
    "washing soda", "caustic soda", "quicklime", "slaked lime", "limestone", "bleaching powder",
    "plaster of paris", "gypsum", "blue vitriol", "glucose", "sugar", "sucrose", "methane", "ammonia",
    "vinegar", "acetic acid", "ethanol", "dry ice", "rust", "ozone", "laughing gas", "nitric acid",
    "hydrochloric acid", "sulfuric acid", "chemical formula", "formula of",
]


BIOLOGY_KEYWORDS = [
    "cell", "mitochondria", "chloroplast", "nucleus", "ribosome", "endoplasmic reticulum",
    "golgi", "lysosome", "vacuole", "cell wall", "cell membrane", "prokaryotic", "eukaryotic",
    "plant cell", "animal cell", "cell theory", "dna", "rna", "chromosome", "gene", "protein",
    "enzyme", "carbohydrate", "lipid", "vitamin", "mitosis", "meiosis", "cell cycle", "prophase",
    "metaphase", "anaphase", "telophase", "photosynthesis", "chlorophyll", "stomata", "xylem",
    "phloem", "transpiration", "root", "stem", "leaf", "flower", "pollination", "germination",
    "cellular respiration", "glycolysis", "krebs cycle", "fermentation", "atp", "plant hormone",
    "auxin", "gibberellin", "cytokinin", "ethylene", "abscisic acid", "tropism", "phototropism",
    "digestive system", "respiratory system", "circulatory system", "excretory system", "nervous system",
    "endocrine system", "reproductive system", "heart", "blood", "rbc", "wbc", "platelet", "nephron",
    "kidney", "neuron", "brain", "reflex action", "synapse", "hormone", "insulin", "thyroxine",
    "adrenaline", "pituitary", "mendel", "heredity", "genetics", "monohybrid", "dihybrid",
    "dominant", "recessive", "allele", "evolution", "natural selection", "darwin", "speciation",
    "fossil", "homologous", "analogous", "taxonomy", "kingdom", "phylum", "species", "linnaeus",
    "bacteria", "virus", "fungi", "pathogen", "disease", "vaccine", "immunity", "antibody",
    "antigen", "ecosystem", "food chain", "food web", "trophic level", "biotechnology",
    "recombinant dna", "pcr", "cloning", "gmo", "stem cell", "powerhouse of cell",
]


class ScienceClassifier:
    """Classifies science queries using token fuzzy matching and regex heuristics."""

    def classify(self, query: str) -> ScienceClassification:
        """
        Classifies incoming query.
        """
        lower_q = query.lower().strip()

        # Step 1: Detect Intent
        intent = self._detect_intent(lower_q)

        # Step 2: Score against each branch using RapidFuzz
        phys_score, phys_kw = self._score_branch(lower_q, PHYSICS_KEYWORDS)
        chem_score, chem_kw = self._score_branch(lower_q, CHEMISTRY_KEYWORDS)
        bio_score, bio_kw = self._score_branch(lower_q, BIOLOGY_KEYWORDS)

        # Strong syntax overrides for Chemistry
        if re.search(r'\b(?:balance|molar\s+mass|molecular\s+mass|valency\s+of|atomic\s+mass|atomic\s+number|electronic\s+configuration)\b', lower_q) or "->" in query or "→" in query:
            chem_score += 40.0

        # Strong numerical physics indicators (e.g. "mass 5 kg", "acceleration 2 m/s2", "velocity", "find force")
        if re.search(r'\b(?:find\s+force|find\s+velocity|calculate\s+kinetic\s+energy|find\s+acceleration|ohm\'?s\s+law|snell\'?s\s+law|mirror\s+formula|lens\s+formula)\b', lower_q) or (re.search(r'\b(?:mass|velocity|acceleration|force|power|energy|work|current|voltage|resistance)\b', lower_q) and re.search(r'\d+', lower_q)):
            phys_score += 40.0

        # Strong biology indicators (e.g. "mitochondria", "photosynthesis", "nephron", "xylem", "mitosis")
        if re.search(r'\b(?:powerhouse|mitochondria|chloroplast|photosynthesis|nephron|neuron|xylem|phloem|mitosis|meiosis|digestive\s+system|food\s+chain|ecosystem)\b', lower_q):
            bio_score += 40.0

        best_score = max(phys_score, chem_score, bio_score)
        if best_score < 40.0:
            return ScienceClassification(
                is_science=False,
                confidence=best_score / 100.0,
            )

        # Determine winning branch
        confidence = min(0.99, max(0.5, best_score / 100.0))

        if best_score == bio_score and bio_score > chem_score and bio_score > phys_score:
            return ScienceClassification(
                is_science=True,
                branch=SubjectType.BIOLOGY,
                topic=bio_kw,
                intent=intent if intent != QuestionIntent.UNKNOWN else QuestionIntent.EXPLAIN_CONCEPT,
                confidence=confidence,
                matched_keyword=bio_kw,
            )
        elif best_score == chem_score and chem_score >= phys_score:
            return ScienceClassification(
                is_science=True,
                branch=SubjectType.CHEMISTRY,
                topic=chem_kw,
                intent=intent if intent != QuestionIntent.UNKNOWN else QuestionIntent.CALCULATE,
                confidence=confidence,
                matched_keyword=chem_kw,
            )
        else:
            return ScienceClassification(
                is_science=True,
                branch=SubjectType.PHYSICS,
                topic=phys_kw,
                intent=intent if intent != QuestionIntent.UNKNOWN else QuestionIntent.CALCULATE,
                confidence=confidence,
                matched_keyword=phys_kw,
            )

    def _score_branch(self, query: str, keywords: list[str]) -> tuple[float, Optional[str]]:
        """Scores a query against a branch keyword catalog using RapidFuzz."""
        max_score = 0.0
        best_kw = None

        for kw in keywords:
            # Exact word boundary match
            if re.search(r'\b' + re.escape(kw) + r'\b', query):
                return 100.0, kw

            # Fuzzy match
            score = fuzz.token_set_ratio(kw, query)
            if score > max_score:
                max_score = score
                best_kw = kw

        return max_score, best_kw

    def _detect_intent(self, lower_q: str) -> QuestionIntent:
        """Detects the question intent."""
        if any(w in lower_q for w in ("difference between", "compare", "versus", "vs ")):
            return QuestionIntent.DIFFERENCE
        if "balance" in lower_q or "->" in lower_q or "→" in lower_q:
            return QuestionIntent.BALANCE_EQUATION
        if any(w in lower_q for w in ("function of", "role of", "what does", "why is", "why do")):
            return QuestionIntent.EXPLAIN_FUNCTION
        if any(w in lower_q for w in ("structure of", "diagram of", "parts of", "anatomy of")):
            return QuestionIntent.IDENTIFY_STRUCTURE
        if any(w in lower_q for w in ("formula for", "what is the formula", "formula of")):
            return QuestionIntent.FIND_FORMULA
        if any(w in lower_q for w in ("calculate", "find", "how much", "how many", "what is the force", "what is the velocity", "what is the mass")):
            return QuestionIntent.CALCULATE
        if any(w in lower_q for w in ("what is a ", "what is an ", "what is ", "define ", "meaning of", "explain ")):
            return QuestionIntent.DEFINE
        return QuestionIntent.UNKNOWN


# Global Science Classifier
science_classifier = ScienceClassifier()
