"""
Biology Concept Knowledge Ontology Database
============================================

PURPOSE:
    Comprehensive concept-based knowledge hierarchy for Biology from LKG to PUC.
    Supports RapidFuzz matching across canonical names, aliases, and student question patterns.
"""

from typing import Optional
from pydantic import BaseModel, Field
from rapidfuzz import fuzz


class BiologyConcept(BaseModel):
    """Metadata and content for a Biology concept."""
    concept_id: str
    topic: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    question_patterns: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    definition: str
    location_or_structure: Optional[str] = None
    functions: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    formula: Optional[str] = None
    importance: Optional[str] = None
    common_questions: dict[str, str] = Field(default_factory=dict)
    explanation: Optional[str] = None
    differences: Optional[list[tuple[str, str, str]]] = None  # [(Parameter, Item A, Item B)]



BIOLOGY_CONCEPTS_CATALOG: list[BiologyConcept] = [
    # --- Cell Biology ---
    BiologyConcept(
        concept_id="biology.cell.mitochondria",
        topic="cell",
        name="Mitochondria",
        aliases=["mitochondria", "mitochondrion", "powerhouse of the cell", "powerhouse of cell", "power house of cell"],
        question_patterns=[
            "why is mitochondria called powerhouse",
            "why mitochondria is called powerhouse of the cell",
            "function of mitochondria",
            "what is mitochondria",
            "what does mitochondria do",
            "role of mitochondria",
            "structure of mitochondria",
        ],
        keywords=["mitochondria", "mitochondrion", "powerhouse", "atp", "cellular respiration", "cristae", "matrix"],
        definition="Mitochondria are double-membrane-bound organelles present in eukaryotic cells, responsible for generating most of the cell's supply of adenosine triphosphate (ATP) through aerobic cellular respiration.",
        location_or_structure="Found in the cytoplasm of eukaryotic cells. It has an outer porous membrane and a deeply folded inner membrane forming cristae, enclosing the mitochondrial matrix. It contains its own circular DNA and 70S ribosomes.",
        functions=[
            "Synthesizes ATP (Adenosine Triphosphate), the universal energy currency of the cell.",
            "Site of Krebs Cycle (Citric Acid Cycle) and Electron Transport Chain (Oxidative Phosphorylation).",
            "Regulates cellular metabolism and apoptosis (programmed cell death).",
        ],
        importance="Known as the 'Powerhouse of the Cell' because it oxidizes nutrients (glucose) into ATP energy that powers all biological activities.",
        common_questions={
            "Why is mitochondria called the powerhouse of the cell?": "Because it carries out cellular respiration and produces ATP (Adenosine Triphosphate), which supplies energy for all cellular and metabolic activities.",
            "Why is mitochondria called a semi-autonomous organelle?": "Because it possesses its own circular DNA and ribosomes, allowing it to synthesize some of its own proteins and replicate independently.",
        },
        explanation="During cellular respiration, glucose breakdown products (pyruvate) enter the mitochondria where they undergo the Krebs cycle in the matrix and oxidative phosphorylation on the inner cristae membrane, yielding up to 36-38 ATP molecules per glucose molecule.",
    ),
    BiologyConcept(
        concept_id="biology.cell.chloroplast",
        topic="cell",
        name="Chloroplast",
        aliases=["chloroplast", "chloroplasts", "plastids", "kitchen of the cell"],
        question_patterns=[
            "what is chloroplast",
            "function of chloroplast",
            "why is chloroplast called kitchen of cell",
            "structure of chloroplast",
        ],
        keywords=["chloroplast", "chlorophyll", "photosynthesis", "thylakoid", "stroma", "grana", "plastid"],
        definition="Chloroplasts are double-membrane green plastids found in plant cells and algae that conduct photosynthesis, absorbing sunlight to synthesize glucose from carbon dioxide and water.",
        location_or_structure="Located in the mesophyll cells of green plant leaves. Structurally composed of double membranes, a fluid-filled stroma, and disc-like membrane sacs called thylakoids stacked into grana. Contains green chlorophyll pigment, its own DNA, and ribosomes.",
        functions=[
            "Captures radiant solar energy using green chlorophyll pigments.",
            "Site of Light-dependent reactions (in thylakoid grana producing ATP and NADPH).",
            "Site of Dark reactions / Calvin Cycle (in stroma converting CO₂ into glucose).",
        ],
        importance="Known as the 'Kitchen of the Cell' because it manufactures food (glucose) that sustains virtually all life on Earth.",
        common_questions={
            "Why is chloroplast called the kitchen of the cell?": "Because it captures sunlight and manufactures food (glucose/starch) for the plant via photosynthesis.",
        },
        explanation="Photosynthesis in chloroplasts converts solar energy into stable chemical energy stored in glucose bonds: 6CO₂ + 6H₂O + Sunlight ⟶ C₆H₁₂O₆ + 6O₂.",
    ),
    BiologyConcept(
        concept_id="biology.cell.nucleus",
        topic="cell",
        name="Nucleus",
        aliases=["nucleus", "cell nucleus", "brain of the cell", "control center of cell"],
        question_patterns=[
            "what is nucleus",
            "function of nucleus",
            "why is nucleus called control center of cell",
            "parts of nucleus",
        ],
        keywords=["nucleus", "dna", "chromatin", "nucleolus", "nuclear membrane", "genetic material"],
        definition="The nucleus is the master double-membrane-bound control organelle of eukaryotic cells that houses the organism's genetic blueprint (DNA) in the form of chromatin/chromosomes.",
        location_or_structure="Usually located near the center of eukaryotic cells. Enclosed by a double-layered nuclear envelope with nuclear pores, containing nucleoplasm, chromatin threads, and a dense nucleolus.",
        functions=[
            "Stores and protects the genetic material (DNA/genes) of the cell.",
            "Controls and regulates all cellular activities, cell growth, metabolism, and protein synthesis.",
            "Site of DNA replication and RNA transcription.",
            "Nucleolus manufactures ribosomal subunits (rRNA).",
        ],
        importance="Known as the 'Control Center' or 'Brain of the Cell' because it directs all cellular metabolic activities and transmits hereditary traits to offspring.",
    ),
    BiologyConcept(
        concept_id="biology.cell.ribosome",
        topic="cell",
        name="Ribosome",
        aliases=["ribosome", "ribosomes", "protein factory of cell", "protein factories"],
        question_patterns=[
            "what is ribosome",
            "function of ribosome",
            "why is ribosome called protein factory",
        ],
        keywords=["ribosome", "protein synthesis", "translation", "70s", "80s", "mrna", "trna"],
        definition="Ribosomes are non-membrane-bound complex molecular machines found in all living cells that perform biological protein synthesis (translation).",
        location_or_structure="Found floating free in the cytoplasm or bound to the Rough Endoplasmic Reticulum (RER). Consists of two ribonucleoprotein subunits (large and small).",
        functions=[
            "Translates mRNA genetic codons into amino acid polypeptide chains (Protein Synthesis).",
        ],
        importance="Known as the 'Protein Factory of the Cell' because proteins synthesized by ribosomes are essential for cell structure, enzymes, hormones, and cellular repair.",
    ),
    # --- Plant Physiology & Photosynthesis ---
    BiologyConcept(
        concept_id="biology.plant.photosynthesis",
        topic="plant_biology",
        name="Photosynthesis",
        aliases=["photosynthesis", "process of photosynthesis", "light reaction", "dark reaction", "calvin cycle"],
        question_patterns=[
            "what is photosynthesis",
            "explain photosynthesis",
            "photosynthesis equation",
            "why do plants need sunlight",
            "factors affecting photosynthesis",
        ],
        keywords=["photosynthesis", "chlorophyll", "sunlight", "stomata", "carbon dioxide", "glucose", "oxygen"],
        definition="Photosynthesis is the biochemical process by which green plants, algae, and certain bacteria convert light energy into chemical energy, synthesizing glucose from carbon dioxide and water in the presence of chlorophyll and sunlight, releasing oxygen as a byproduct.",
        formula="6CO₂ + 6H₂O + Sunlight (Chlorophyll) ⟶ C₆H₁₂O₆ + 6O₂",
        functions=[
            "Primary source of organic food and energy for all terrestrial and aquatic food webs.",
            "Replenishes atmospheric oxygen (O₂) required for aerobic respiration.",
            "Removes carbon dioxide (CO₂) from the atmosphere, mitigating greenhouse warming.",
        ],
        importance="The foundational autotrophic biological process that drives life on Earth.",
        common_questions={
            "What is the overall balanced chemical equation for photosynthesis?": "6CO₂ + 6H₂O + Sunlight (in presence of Chlorophyll) ⟶ C₆H₁₂O₆ (Glucose) + 6O₂ (Oxygen).",
            "Why do plants need sunlight for photosynthesis?": "Sunlight provides the photon energy required to split water molecules (photolysis) and excite chlorophyll electrons to produce ATP and NADPH for glucose synthesis.",
        },
        explanation="Photosynthesis occurs in two main phases:\n1. **Light Reactions (in Thylakoid Grana):** Solar energy is absorbed by chlorophyll, water is split (Photolysis: 2H₂O ⟶ 4H⁺ + 4e⁻ + O₂↑), producing ATP and NADPH.\n2. **Dark Reactions / Calvin Cycle (in Stroma):** CO₂ is reduced and fixed into glucose using the ATP and NADPH generated in the light phase.",
    ),
    BiologyConcept(
        concept_id="biology.plant.xylem_phloem",
        topic="plant_biology",
        name="Plant Vascular Tissues: Xylem and Phloem",
        aliases=["xylem", "phloem", "xylem and phloem", "vascular bundle", "translocation", "transpiration"],
        question_patterns=[
            "difference between xylem and phloem",
            "function of xylem",
            "function of phloem",
            "what is xylem",
            "what is phloem",
        ],
        keywords=["xylem", "phloem", "vascular tissue", "tracheids", "vessels", "sieve tubes", "companion cells", "translocation"],
        definition="Xylem and Phloem are complex conducting vascular tissues in plants. Xylem conducts water and dissolved mineral nutrients from roots upward to leaves, while Phloem translocates synthesized organic food (sugars) bidirectionally from leaves to all other plant parts.",
        functions=[
            "Xylem: Unidirectional transport of water and inorganic minerals (Transpiration pull & Root pressure); provides mechanical support.",
            "Phloem: Bidirectional translocation of synthesized carbohydrates/sucrose and amino acids.",
        ],
        differences=[
            ("Conduction Material", "Water and dissolved inorganic minerals", "Organic food (sucrose, amino acids)"),
            ("Direction of Transport", "Unidirectional (Upward only: Root ⟶ Leaves)", "Bidirectional (Upward and downward: Leaves ⟷ Storage organs)"),
            ("Living / Dead Cells", "Mostly dead elements (Tracheids, Vessels, Xylem fibers; only parenchyma is living)", "Mostly living elements (Sieve tubes, Companion cells; only phloem fibers are dead)"),
            ("Driving Mechanism", "Passive physical forces (Transpiration pull, Capillarity, Cohesion-Tension)", "Active transport requiring metabolic energy (ATP)"),
        ],
    ),
    # --- Cell Division ---
    BiologyConcept(
        concept_id="biology.cell.mitosis_meiosis",
        topic="cell_division",
        name="Cell Division: Mitosis vs Meiosis",
        aliases=["mitosis", "meiosis", "difference between mitosis and meiosis", "cell division", "cell cycle"],
        question_patterns=[
            "what is mitosis",
            "what is meiosis",
            "difference between mitosis and meiosis",
            "phases of mitosis",
        ],
        keywords=["mitosis", "meiosis", "prophase", "metaphase", "anaphase", "telophase", "crossing over", "diploid", "haploid", "gametes"],
        definition="Cell division is the process by which a parent cell divides into daughter cells. Mitosis is equational division producing two identical diploid somatic cells. Meiosis is reductional division producing four genetically diverse haploid gamete cells.",
        functions=[
            "Mitosis: Growth, tissue repair, asexual reproduction, and body regeneration.",
            "Meiosis: Formation of gametes (sperm and egg), maintaining species chromosome number across generations, and introducing genetic variation via crossing over.",
        ],
        differences=[
            ("Type of Cells", "Somatic (Body) cells", "Germ / Reproductive cells (Gonads)"),
            ("Number of Divisions", "Single division (Prophase, Metaphase, Anaphase, Telophase)", "Two successive divisions (Meiosis I and Meiosis II)"),
            ("Number of Daughter Cells", "2 Daughter cells produced", "4 Daughter cells produced"),
            ("Chromosome Number", "Equational: Diploid (2n) remains Diploid (2n)", "Reductional: Diploid (2n) reduced to Haploid (n)"),
            ("Crossing Over & Variation", "No crossing over; daughter cells are genetically identical clones", "Crossing over occurs in Prophase I (Pachytene); creates genetic diversity"),
        ],
    ),
    # --- Human Physiology: Heart & Circulation ---
    BiologyConcept(
        concept_id="biology.human.circulatory_system",
        topic="human_biology",
        name="Human Circulatory System and Heart",
        aliases=["circulatory system", "human heart", "blood circulation", "double circulation", "blood", "rbc", "wbc", "platelets"],
        question_patterns=[
            "what is double circulation",
            "structure of human heart",
            "function of blood",
            "difference between arteries and veins",
            "function of rbc",
            "function of wbc",
            "function of platelets",
        ],
        keywords=["heart", "blood", "rbc", "wbc", "platelet", "artery", "vein", "double circulation", "atrium", "ventricle", "hemoglobin"],
        definition="The human circulatory system is an organ system comprising the 4-chambered muscular heart, blood vessels (arteries, veins, capillaries), and blood that transports oxygen, nutrients, hormones, and metabolic wastes throughout the body.",
        location_or_structure="Heart is a muscular organ located in the thoracic cavity between lungs. Consists of 4 chambers: 2 upper thin-walled Atria (Auricles) and 2 lower thick-walled Ventricles.",
        functions=[
            "Double Circulation: Blood passes through the heart TWICE during each complete circuit (Pulmonary circulation to lungs + Systemic circulation to body tissues).",
            "RBC (Red Blood Cells / Erythrocytes): Contain iron-rich hemoglobin to transport oxygen (O₂) from lungs to cells.",
            "WBC (White Blood Cells / Leukocytes): Defend against infections and produce antibodies.",
            "Platelets (Thrombocytes): Essential for blood clotting and stopping hemorrhages.",
            "Plasma: Fluid matrix transporting dissolved nutrients, carbon dioxide (CO₂), urea, and hormones.",
        ],
        differences=[
            ("Blood Flow Direction", "Arteries carry blood AWAY from heart to body organs", "Veins carry blood TOWARDS heart from body organs"),
            ("Blood Oxygenation", "Carry oxygenated blood (except Pulmonary Artery)", "Carry deoxygenated blood (except Pulmonary Vein)"),
            ("Wall Thickness & Lumen", "Thick, elastic, muscular walls with narrow lumen", "Thin, less muscular walls with wide lumen"),
            ("Internal Valves", "No valves (high blood pressure prevents backflow)", "Contain semilunar valves to prevent backward flow of blood"),
        ],
    ),
    # --- Human Physiology: Excretion & Nephron ---
    BiologyConcept(
        concept_id="biology.human.excretory_system",
        topic="human_biology",
        name="Human Excretory System and Nephron",
        aliases=["excretory system", "kidney", "nephron", "urine formation", "dialysis"],
        question_patterns=[
            "what is nephron",
            "function of nephron",
            "structure of nephron",
            "how is urine formed",
            "what is dialysis",
        ],
        keywords=["nephron", "kidney", "urine", "bowman capsule", "glomerulus", "ultrafiltration", "dialysis", "excretion"],
        definition="The excretory system removes nitrogenous metabolic waste products (urea, uric acid) from the blood and maintains osmoregulation (water and electrolyte balance). The Nephron is the structural and functional filtration unit of the kidney (~1 million nephrons per kidney).",
        location_or_structure="Located in the renal cortex and medulla of kidneys. A nephron consists of a renal corpuscle (Bowman's capsule enclosing the Glomerulus capillary tuft) and a renal tubule (Proximal Convoluted Tubule, Loop of Henle, Distal Convoluted Tubule, and Collecting Duct).",
        functions=[
            "Ultrafiltration: Blood is filtered under high hydrostatic pressure in the glomerulus into Bowman's capsule.",
            "Selective Reabsorption: Essential substances (glucose, amino acids, salts, water) are reabsorbed back into peritubular capillaries from PCT and Loop of Henle.",
            "Tubular Secretion: Extra ions (K⁺, H⁺, creatinine) are actively secreted into the tubule to form final urine.",
            "Osmoregulation: Maintains blood volume, pH, and electrolyte equilibrium.",
        ],
        importance="Prevents toxic accumulation of nitrogenous urea in the bloodstream; failure of kidneys requires hemodialysis (artificial kidney) or renal transplant.",
    ),
    # --- Human Physiology: Nervous System & Neuron ---
    BiologyConcept(
        concept_id="biology.human.nervous_system",
        topic="human_biology",
        name="Nervous System and Neuron",
        aliases=["nervous system", "neuron", "nerve cell", "brain", "reflex arc", "synapse"],
        question_patterns=[
            "what is neuron",
            "structure of neuron",
            "function of neuron",
            "what is reflex action",
            "what is synapse",
            "parts of brain",
        ],
        keywords=["neuron", "brain", "dendrite", "axon", "synapse", "reflex action", "cerebrum", "cerebellum", "medulla"],
        definition="The nervous system is the control and communication network of the body. The Neuron (nerve cell) is the structural and functional unit of the nervous system, specialized for receiving, conducting, and transmitting electrical nerve impulses.",
        location_or_structure="A neuron consists of three main parts: 1. Cyton (Cell Body / Soma) containing nucleus, 2. Dendrites (short branched fibers receiving signals), and 3. Axon (long fiber insulated by myelin sheath transmitting impulses to nerve endings).",
        functions=[
            "Transmits electrical electrochemical nerve impulses across the body.",
            "Synapse: Microscopic junction between two neurons where neurotransmitter chemicals (e.g. acetylcholine) transmit signals.",
            "Reflex Arc: Rapid, automatic, involuntary nerve pathway bypassing conscious brain thought for immediate protection (Stimulus ⟶ Receptor ⟶ Sensory Neuron ⟶ Spinal Cord ⟶ Motor Neuron ⟶ Effector Muscle).",
            "Brain Functions: Cerebrum (Memory, thinking, sensory perception), Cerebellum (Motor balance, posture, coordination), Medulla Oblongata (Involuntary functions: Heartbeat, breathing, blood pressure).",
        ],
    ),
    # --- Genetics & Heredity ---
    BiologyConcept(
        concept_id="biology.genetics.mendel_dna",
        topic="genetics",
        name="Genetics, Mendel's Laws and DNA",
        aliases=["genetics", "heredity", "mendel's laws", "dna", "gene", "chromosome", "monohybrid cross", "dihybrid cross", "sex determination"],
        question_patterns=[
            "what is dna",
            "what is gene",
            "what is heredity",
            "explain mendel's laws",
            "what is monohybrid cross",
            "how is sex determined in humans",
        ],
        keywords=["genetics", "dna", "gene", "allele", "mendel", "heredity", "monohybrid", "punnett square", "chromosome", "xx", "xy"],
        definition="Genetics is the branch of biology that studies heredity (transmission of traits from parents to offspring) and genetic variation. Gregor Mendel is known as the 'Father of Genetics'. DNA (Deoxyribonucleic Acid) is the genetic material storing hereditary information.",
        formula="Monohybrid Phenotypic Ratio = 3:1 (Genotypic 1:2:1);  Dihybrid Phenotypic Ratio = 9:3:3:1",
        key_points=[
            "Mendel's First Law (Law of Segregation): During gamete formation, allele pairs segregate so each gamete carries only one allele.",
            "Mendel's Second Law (Law of Independent Assortment): Alleles of different genes assort independently during gamete formation.",
            "DNA Structure: Watson and Crick double helix with sugar-phosphate backbone and complementary base pairing (Adenine pairs with Thymine, Guanine pairs with Cytosine: A=T, G≡C).",
            "Sex Determination in Humans: Females have XX chromosomes; Males have XY chromosomes. The sperm carrying either X or Y chromosome determines the biological sex of the child (50% probability).",
        ],
        examples=["Crossing pure tall (TT) and pure dwarf (tt) pea plants yields 100% tall (Tt) in F1 and 3 Tall : 1 Dwarf in F2"],
    ),
    # --- Ecology & Environment ---
    BiologyConcept(
        concept_id="biology.ecology.ecosystem_food_chain",
        topic="ecology",
        name="Ecosystem, Food Chain and Trophic Levels",
        aliases=["ecosystem", "food chain", "food web", "trophic levels", "10 percent law", "energy flow"],
        question_patterns=[
            "what is an ecosystem",
            "what is food chain",
            "what is food web",
            "what is 10 percent law",
            "difference between food chain and food web",
        ],
        keywords=["ecosystem", "food chain", "food web", "trophic level", "10 percent law", "producers", "consumers", "decomposers"],
        definition="An ecosystem is a functional structural unit of nature where living biotic organisms (plants, animals, microbes) interact with their non-living abiotic physical environment (soil, water, air, sunlight). A Food Chain represents the sequential transfer of food energy from producers through various trophic levels.",
        formula="Lindeman's 10% Law: Energy at trophic level n+1 = 10% of Energy at trophic level n (90% lost as heat/metabolism)",
        functions=[
            "Trophic Levels: Producers (Plants / Autotrophs) ⟶ Primary Consumers (Herbivores) ⟶ Secondary Consumers (Carnivores) ⟶ Tertiary / Top Carnivores.",
            "10% Energy Law: In a food chain, only ~10% of the energy entering a trophic level is stored as biomass and available to the next trophic level.",
            "Food Web: A network of interconnected food chains providing ecological stability and alternative feeding pathways.",
            "Decomposers (Fungi, Bacteria): Recycle organic nutrients back into the soil and atmosphere.",
        ],
        examples=["Grass (10,000 J) ⟶ Deer (1,000 J) ⟶ Lion (100 J) following the 10% law"],
    ),
]


class BiologyKnowledgeBase:
    """Indexed Biology knowledge repository with RapidFuzz semantic search."""

    def __init__(self) -> None:
        self.catalog = BIOLOGY_CONCEPTS_CATALOG
        self._index: dict[str, BiologyConcept] = {c.concept_id: c for c in self.catalog}

    def find_by_query(self, query: str, threshold: float = 65.0) -> list[tuple[BiologyConcept, float]]:
        """Matches a student query against biology concepts using RapidFuzz."""
        import re
        lower_q = query.lower().strip()
        matches = []

        for concept in self.catalog:
            # Require at least one concept alias, keyword, or name anchor to be relevant
            concept_terms = [concept.name.lower()] + [a.lower() for a in concept.aliases] + [k.lower() for k in concept.keywords]
            has_anchor = any(
                re.search(r"\b" + re.escape(term) + r"\b", lower_q)
                for term in concept_terms
                if len(term) >= 3
            ) or any(
                fuzz.partial_ratio(term, lower_q) >= 85.0
                for term in concept_terms
                if len(term) >= 4
            )
            if not has_anchor:
                continue

            best_score = 0.0

            # Match question patterns (highest priority)
            for pat in concept.question_patterns:
                score_pat = fuzz.token_set_ratio(pat, lower_q)
                best_score = max(best_score, score_pat)

            # Match canonical name
            score_name = fuzz.token_set_ratio(concept.name.lower(), lower_q)
            best_score = max(best_score, score_name)

            # Match aliases
            for alias in concept.aliases:
                score_alias = fuzz.token_set_ratio(alias.lower(), lower_q)
                best_score = max(best_score, score_alias)

            # Match keywords
            for kw in concept.keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", lower_q):
                    best_score = max(best_score, 85.0)

            if best_score >= threshold:
                matches.append((concept, best_score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


    def get_by_id(self, concept_id: str) -> Optional[BiologyConcept]:
        return self._index.get(concept_id)


# Global instance
biology_kb = BiologyKnowledgeBase()
