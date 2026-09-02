"""
Physics Concepts Knowledge Base
===============================

PURPOSE:
    Comprehensive concept catalog for Physics from LKG through PUC (Grade 12).
    Supports RapidFuzz matching, formula bindings, definitions, and real-world examples.
"""

from typing import Optional
from pydantic import BaseModel, Field
from rapidfuzz import fuzz


class PhysicsConcept(BaseModel):
    """Metadata and content for a Physics concept."""
    concept_id: str
    topic: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    definition: str
    formula: Optional[str] = None
    si_unit: Optional[str] = None
    scalar_vector: Optional[str] = None
    key_points: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    diagram_ascii: Optional[str] = None


PHYSICS_CONCEPTS_CATALOG: list[PhysicsConcept] = [
    # --- Mechanics & Kinematics ---
    PhysicsConcept(
        concept_id="physics.motion.velocity",
        topic="mechanics",
        name="Velocity",
        aliases=["velocity", "speed with direction", "rate of displacement", "average velocity"],
        keywords=["velocity", "displacement", "speed", "direction", "m/s"],
        definition="Velocity is the rate of change of displacement with respect to time. It is a vector quantity having both magnitude and direction.",
        formula="v = Δs / Δt  (or v = displacement / time)",
        si_unit="m/s (meters per second)",
        scalar_vector="Vector Quantity",
        key_points=[
            "Speed is scalar (distance/time), while velocity is vector (displacement/time).",
            "Average velocity is total displacement divided by total time: v_avg = Δx / Δt.",
            "Instantaneous velocity is the derivative: v = ds/dt.",
            "Can be positive, negative, or zero.",
        ],
        examples=["A car traveling 60 km/h due North", "A rocket launching upwards at 11 km/s"],
    ),
    PhysicsConcept(
        concept_id="physics.motion.acceleration",
        topic="mechanics",
        name="Acceleration",
        aliases=["acceleration", "rate of change of velocity", "deceleration", "retardation"],
        keywords=["acceleration", "velocity change", "deceleration", "m/s2", "m/s^2"],
        definition="Acceleration is the rate of change of velocity with respect to time. When velocity decreases over time, it is called negative acceleration, deceleration, or retardation.",
        formula="a = (v - u) / t  (where v = final velocity, u = initial velocity)",
        si_unit="m/s² (meters per second squared)",
        scalar_vector="Vector Quantity",
        key_points=[
            "a = (v - u) / t",
            "Instantaneous acceleration is the second derivative of position: a = d²s/dt² = dv/dt.",
            "Uniform acceleration means velocity changes by equal amounts in equal intervals of time.",
        ],
        examples=["A falling apple accelerating at 9.8 m/s² due to gravity", "A sports car accelerating from 0 to 100 km/h in 3 seconds"],
    ),
    PhysicsConcept(
        concept_id="physics.force.newton_laws",
        topic="mechanics",
        name="Newton's Laws of Motion",
        aliases=["newton's laws", "newton law", "newton second law", "newtons first law", "newton third law", "law of inertia", "f=ma"],
        keywords=["newton", "inertia", "f=ma", "action reaction", "momentum", "force"],
        definition="Newton's three laws form the foundation of classical mechanics, describing the relationship between a body and the forces acting upon it.",
        formula="First Law: ΣF = 0 ⟹ v = const;  Second Law: F = ma = dp/dt;  Third Law: F_AB = -F_BA",
        si_unit="Newton (N) = kg·m/s²",
        scalar_vector="Vector Quantity",
        key_points=[
            "First Law (Law of Inertia): An object remains at rest or in uniform motion unless acted upon by a net external force.",
            "Second Law (Fundamental Law): The rate of change of momentum is directly proportional to applied force (F = ma).",
            "Third Law (Action-Reaction): For every action, there is an equal and opposite reaction acting on different bodies.",
        ],
        examples=["Passengers lunging forward when a bus suddenly brakes (1st Law)", "Pushing a 5 kg block with 10 N yields 2 m/s² acceleration (2nd Law)", "Rocket propulsion pushing exhaust gases downward to propel upward (3rd Law)"],
    ),
    PhysicsConcept(
        concept_id="physics.force.momentum",
        topic="mechanics",
        name="Momentum and Conservation of Momentum",
        aliases=["momentum", "linear momentum", "conservation of momentum", "impulse"],
        keywords=["momentum", "mass times velocity", "p=mv", "impulse", "kg m/s"],
        definition="Linear momentum is the product of the mass and velocity of an object. In an isolated system (no external forces), total momentum is conserved.",
        formula="p = m · v;  Impulse J = F · Δt = Δp;  Conservation: m₁u₁ + m₂u₂ = m₁v₁ + m₂v₂",
        si_unit="kg·m/s (or N·s)",
        scalar_vector="Vector Quantity",
        key_points=[
            "Linear momentum: p = mv.",
            "Law of Conservation of Momentum: Total momentum before collision equals total momentum after collision.",
            "Impulse is force multiplied by time interval: J = F·Δt = Δp.",
        ],
        examples=["Recoil of a gun after firing a bullet", "Collision of billiard balls on a pool table"],
    ),
    PhysicsConcept(
        concept_id="physics.energy.work_power_energy",
        topic="work_energy",
        name="Work, Energy and Power",
        aliases=["work", "kinetic energy", "potential energy", "power", "mechanical energy", "conservation of energy"],
        keywords=["work", "kinetic energy", "potential energy", "power", "joule", "watt", "ke", "pe"],
        definition="Work is done when a force causes a displacement. Energy is the capacity to do work. Power is the rate of doing work or transferring energy.",
        formula="Work: W = F · d · cos(θ);  KE = (1/2)mv²;  PE = mgh;  Power: P = W / t = F · v",
        si_unit="Work & Energy: Joule (J);  Power: Watt (W) = J/s",
        scalar_vector="Scalar Quantities",
        key_points=[
            "Work done is zero if displacement is perpendicular to force (e.g. Earth orbiting Sun).",
            "Kinetic Energy (KE): Energy possessed due to motion = (1/2)mv².",
            "Gravitational Potential Energy (PE): Energy stored due to position = mgh.",
            "Law of Conservation of Energy: Energy can neither be created nor destroyed, only transformed.",
            "Power = Work / Time (1 horsepower = 746 Watts).",
        ],
        examples=["Lifting a 10 kg box to a height of 2 m (PE = 10 × 9.8 × 2 = 196 J)", "A 1000 kg car moving at 20 m/s (KE = 0.5 × 1000 × 400 = 200,000 J)"],
    ),
    PhysicsConcept(
        concept_id="physics.gravitation.universal_gravity",
        topic="gravitation",
        name="Universal Law of Gravitation",
        aliases=["gravitation", "gravity", "universal law of gravitation", "acceleration due to gravity", "escape velocity", "kepler's laws"],
        keywords=["gravitation", "gravity", "newton gravity", "escape velocity", "kepler", "g=9.8"],
        definition="Every particle of matter in the universe attracts every other particle with a force directly proportional to the product of their masses and inversely proportional to the square of the distance between them.",
        formula="F = G · (m₁ · m₂) / r²;  g = GM / R²;  Escape Velocity: v_e = √(2gR)",
        si_unit="Gravitational Force: N;  Gravitational Constant G = 6.674 × 10⁻¹¹ N·m²/kg²",
        scalar_vector="Force is Vector; Potential is Scalar",
        key_points=[
            "Gravitational force is always attractive and acts along the line joining the centers.",
            "g on Earth's surface ≈ 9.8 m/s² (varies slightly: higher at poles, lower at equator).",
            "Mass is constant everywhere, but Weight (W = mg) varies with gravity.",
            "Escape velocity from Earth is ~11.2 km/s.",
            "Kepler's 3rd Law: The square of orbital period is proportional to cube of semi-major axis (T² ∝ r³).",
        ],
        examples=["The Moon orbiting the Earth due to gravitational attraction", "Ocean tides caused by gravitational pull of Moon and Sun"],
    ),
    # --- Properties of Matter & Fluids ---
    PhysicsConcept(
        concept_id="physics.matter.density_pressure",
        topic="properties_matter",
        name="Density, Pressure and Archimedes' Principle",
        aliases=["density", "pressure", "archimedes principle", "buoyancy", "pascal's law", "fluid pressure", "hooke's law"],
        keywords=["density", "pressure", "pascal", "archimedes", "buoyant force", "upthrust", "hooke"],
        definition="Density is mass per unit volume. Pressure is thrust per unit area. Archimedes' Principle states that a body immersed in fluid experiences an upward buoyant force equal to the weight of the fluid displaced.",
        formula="Density: ρ = m / V;  Pressure: P = F / A = ρgh;  Buoyant Force: F_b = ρ_fluid · V_submerged · g",
        si_unit="Density: kg/m³;  Pressure: Pascal (Pa) = N/m²",
        scalar_vector="Scalar Quantities",
        key_points=[
            "Pascal's Law: Pressure applied to an enclosed fluid is transmitted equally in all directions.",
            "Archimedes' Principle explains why heavy steel ships float while small iron nails sink.",
            "Hooke's Law for elasticity: Stress is directly proportional to Strain (Stress = Y × Strain).",
        ],
        examples=["Hydraulic brakes and hydraulic lifts working on Pascal's law", "Submarines submerging by filling ballast tanks with water"],
    ),
    # --- Heat & Thermodynamics ---
    PhysicsConcept(
        concept_id="physics.thermo.heat_laws",
        topic="heat_thermo",
        name="Heat and Thermodynamics",
        aliases=["heat", "temperature", "specific heat", "latent heat", "first law of thermodynamics", "second law of thermodynamics", "carnot engine"],
        keywords=["heat", "thermodynamics", "specific heat", "latent heat", "calorimetry", "entropy", "carnot"],
        definition="Heat is thermal energy in transit between systems due to a temperature difference. Thermodynamics governs heat, work, internal energy, and entropy transformations.",
        formula="Heat: Q = m · c · ΔT;  Latent Heat: Q = m · L;  First Law: ΔU = Q - W;  Carnot Efficiency: η = 1 - (T_C / T_H)",
        si_unit="Heat: Joule (J);  Specific Heat: J/(kg·K);  Temperature: Kelvin (K)",
        scalar_vector="Scalar Quantities",
        key_points=[
            "Zeroth Law: Defines thermal equilibrium and temperature.",
            "First Law: Conservation of energy for thermodynamic systems (ΔU = Q - W).",
            "Second Law: Heat cannot spontaneously flow from colder to hotter body; total entropy of an isolated system always increases.",
            "Modes of heat transfer: Conduction (solids), Convection (fluids), Radiation (electromagnetic waves).",
        ],
        examples=["Boiling water absorbing latent heat of vaporization at constant 100°C", "Car engine converting heat energy into mechanical work"],
    ),
    # --- Waves & Sound ---
    PhysicsConcept(
        concept_id="physics.waves.sound_waves",
        topic="waves_sound",
        name="Waves and Sound",
        aliases=["waves", "sound", "frequency", "wavelength", "wave velocity", "doppler effect", "echo", "resonance"],
        keywords=["wave", "sound", "frequency", "wavelength", "hertz", "doppler", "echo", "v=f*lambda"],
        definition="A wave is an oscillation accompanied by a transfer of energy through a medium or space. Sound is a mechanical longitudinal wave produced by vibrating bodies.",
        formula="Wave equation: v = f · λ;  Time Period: T = 1 / f;  Echo Distance: d = (v · t) / 2",
        si_unit="Frequency: Hertz (Hz);  Wavelength: meters (m);  Velocity: m/s",
        scalar_vector="Frequency/Wavelength are Scalar; Wave velocity is Vector",
        key_points=[
            "Transverse waves (e.g. Light): oscillations perpendicular to wave propagation.",
            "Longitudinal waves (e.g. Sound): oscillations parallel to wave propagation (compressions & rarefactions).",
            "Sound cannot travel in a vacuum; its speed in air at 20°C is ~343 m/s.",
            "Audible human frequency range: 20 Hz to 20,000 Hz (Infrasound < 20 Hz, Ultrasound > 20 kHz).",
            "Doppler Effect: Apparent change in frequency due to relative motion between source and observer.",
        ],
        examples=["SONAR measuring ocean depth using reflected ultrasound pulses", "Pitch of an ambulance siren sounding higher as it approaches and lower as it recedes"],
    ),
    # --- Optics ---
    PhysicsConcept(
        concept_id="physics.optics.light_laws",
        topic="optics",
        name="Optics: Reflection, Refraction and Lenses",
        aliases=["optics", "light", "reflection", "refraction", "snell's law", "mirror formula", "lens formula", "power of lens", "total internal reflection"],
        keywords=["optics", "light", "mirror", "lens", "snell", "focal length", "diopter", "refractive index"],
        definition="Optics is the branch of physics that studies the behavior and properties of light. Reflection is the bouncing of light, and refraction is the bending of light when passing between media.",
        formula="Mirror Formula: 1/f = 1/v + 1/u;  Lens Formula: 1/f = 1/v - 1/u;  Snell's Law: n₁ sin(θ₁) = n₂ sin(θ₂);  Lens Power: P = 1/f (in meters)",
        si_unit="Power of lens: Diopter (D) = m⁻¹;  Refractive index is dimensionless",
        scalar_vector="Scalar",
        key_points=[
            "Laws of Reflection: Angle of incidence = Angle of reflection (∠i = ∠r).",
            "Snell's Law of Refraction: n₁ sin(θ₁) = n₂ sin(θ₂).",
            "Total Internal Reflection (TIR) occurs when light travels from denser to rarer medium at an angle greater than critical angle (θ_c = sin⁻¹(1/n)).",
            "Convex lens is converging (positive focal length); Concave lens is diverging (negative focal length).",
            "Power of lens P = 1/f (f in meters).",
        ],
        examples=["Optical fibers transmitting high-speed internet data via Total Internal Reflection", "Eyeglasses correcting myopia (concave lens) or hypermetropia (convex lens)"],
    ),
    # --- Electricity & Magnetism ---
    PhysicsConcept(
        concept_id="physics.electricity.ohm_circuits",
        topic="electricity",
        name="Electricity, Ohm's Law and Circuits",
        aliases=["electricity", "electric current", "ohm's law", "resistance", "resistivity", "series circuit", "parallel circuit", "electrical power", "capacitance"],
        keywords=["electricity", "current", "voltage", "resistance", "ohm", "circuit", "v=ir", "power"],
        definition="Electric current is the rate of flow of electric charge. Ohm's law states that current through a conductor between two points is directly proportional to voltage across the points, at constant temperature.",
        formula="Ohm's Law: V = I · R;  Series: R_s = R₁ + R₂ + ...;  Parallel: 1/R_p = 1/R₁ + 1/R₂;  Power: P = V·I = I²R = V²/R;  Capacitor: Q = C·V",
        si_unit="Current: Ampere (A);  Voltage: Volt (V);  Resistance: Ohm (Ω);  Capacitance: Farad (F)",
        scalar_vector="Current, Voltage, Resistance are Scalar",
        key_points=[
            "Current I = Q / t (1 Ampere = 1 Coulomb per second).",
            "Resistance R = ρ · L / A (depends on material resistivity ρ, length L, cross-sectional area A).",
            "In Series circuits: Current is the same through all resistors; total resistance increases (R_s = R₁ + R₂).",
            "In Parallel circuits: Voltage is the same across all resistors; total resistance decreases (1/R_p = 1/R₁ + 1/R₂).",
            "Electrical Energy = Power × Time = V·I·t (Commercial unit: 1 kWh = 3.6 × 10⁶ J).",
        ],
        examples=["A 100 W bulb connected to 220 V drawing current I = 100/220 ≈ 0.45 A", "Household electrical appliances connected in parallel so each receives full 230 V"],
    ),
    PhysicsConcept(
        concept_id="physics.magnetism.electromagnetism",
        topic="magnetism_emi",
        name="Magnetism and Electromagnetic Induction",
        aliases=["magnetism", "magnetic field", "lorentz force", "faraday's law", "lenz's law", "electromagnetic induction", "transformer"],
        keywords=["magnetism", "magnetic field", "faraday", "lenz", "transformer", "induction", "emi"],
        definition="Magnetic fields are produced by moving electric charges and intrinsic magnetic dipoles. Faraday's Law states that a changing magnetic flux induces an electromotive force (EMF) in a conductor.",
        formula="Lorentz Force: F = q(v × B) + qE;  Faraday's Law: ε = -N(ΔΦ / Δt);  Transformer: V_p / V_s = N_p / N_s = I_s / I_p",
        si_unit="Magnetic Field: Tesla (T);  Magnetic Flux: Weber (Wb) = T·m²",
        scalar_vector="Magnetic Field is Vector; Flux is Scalar",
        key_points=[
            "Right-Hand Rule determines the direction of magnetic field and force.",
            "Lenz's Law: The direction of induced current opposes the change in magnetic flux that produces it (Conservation of Energy).",
            "Step-Up Transformer increases voltage (N_s > N_p); Step-Down Transformer decreases voltage (N_s < N_p).",
        ],
        examples=["Electric generators converting mechanical energy into AC electrical power", "Substation transformers stepping up voltage to 400 kV for long-distance power grid transmission"],
    ),
    # --- Modern Physics & Electronics ---
    PhysicsConcept(
        concept_id="physics.modern.quantum_photoelectric",
        topic="modern_physics",
        name="Modern Physics and Photoelectric Effect",
        aliases=["modern physics", "photoelectric effect", "work function", "de broglie wavelength", "photon", "radioactivity", "half life", "bohr model"],
        keywords=["photoelectric", "photon", "de broglie", "half life", "radioactivity", "e=hf", "bohr"],
        definition="Modern physics encompasses quantum theory and relativity. The Photoelectric Effect demonstrates the particle nature of light, where photons eject electrons from a metal surface.",
        formula="Photon Energy: E = h · f = hc / λ;  Einstein's Equation: hf = W₀ + KE_max;  de Broglie: λ = h / p = h / (mv);  Decay: N(t) = N₀ · (1/2)^(t / T_half)",
        si_unit="Energy: Joule (J) or Electron-Volt (eV; 1 eV = 1.602 × 10⁻¹⁹ J)",
        scalar_vector="Scalar",
        key_points=[
            "Wave-Particle Duality: Light and matter exhibit both wave-like and particle-like properties.",
            "Threshold frequency (f₀): Minimum frequency below which no photoelectrons are emitted, regardless of intensity.",
            "Radioactive half-life (T_half): Time required for half of the radioactive nuclei in a sample to decay.",
        ],
        examples=["Solar cells and light sensors utilizing the Photoelectric Effect", "Carbon-14 radioactive dating used to determine the age of ancient artifacts"],
    ),
    PhysicsConcept(
        concept_id="physics.electronics.semiconductors",
        topic="electronics",
        name="Semiconductors and Logic Gates",
        aliases=["semiconductor", "logic gates", "p-n junction", "diode", "transistor", "and gate", "or gate", "not gate", "nand gate", "nor gate", "xor gate"],
        keywords=["semiconductor", "diode", "transistor", "logic gate", "truth table", "nand gate", "nor gate", "and gate", "or gate", "not gate", "xor gate", "p-n junction", "boolean logic"],
        definition="Semiconductors have electrical conductivity between conductors and insulators. Digital logic gates perform fundamental Boolean operations in computing.",
        formula="AND: Y = A · B;  OR: Y = A + B;  NOT: Y = Ā;  NAND: Y = (A · B)̄;  NOR: Y = (A + B)̄;  XOR: Y = A ⊕ B",
        si_unit="Dimensionless Boolean logic (0 or 1)",
        scalar_vector="Scalar",
        key_points=[
            "Intrinsic semiconductors: Pure silicon (Si) and Germanium (Ge).",
            "Doping creates Extrinsic semiconductors: P-type (trivalent dopants like Boron) and N-type (pentavalent dopants like Phosphorus).",
            "P-N Junction diode allows current to flow primarily in one direction (Forward bias conducts; Reverse bias blocks).",
            "NAND and NOR are Universal Gates (any boolean logic function can be constructed using only NAND or NOR).",
        ],
        examples=["Silicon computer microprocessors containing billions of nanoscale transistors", "LED (Light Emitting Diode) illuminating smartphone screens"],
    ),
]


class PhysicsKnowledgeBase:
    """Indexed Physics knowledge repository."""

    def __init__(self) -> None:
        self.catalog = PHYSICS_CONCEPTS_CATALOG
        self._index: dict[str, PhysicsConcept] = {c.concept_id: c for c in self.catalog}

    def find_by_query(self, query: str, threshold: float = 70.0) -> list[tuple[PhysicsConcept, float]]:
        """Matches a student query against physics concepts using RapidFuzz."""
        lower_q = query.lower().strip()
        matches = []

        for concept in self.catalog:
            best_score = 0.0
            # Match canonical name
            score_name = fuzz.token_set_ratio(concept.name.lower(), lower_q)
            ratio_name = fuzz.ratio(concept.name.lower(), lower_q)
            best_score = max(best_score, ratio_name, score_name * 0.85)

            # Match aliases
            for alias in concept.aliases:
                if alias == lower_q:
                    best_score = max(best_score, 100.0)
                elif alias in lower_q:
                    best_score = max(best_score, 90.0)
                else:
                    score_alias = fuzz.ratio(alias.lower(), lower_q)
                    best_score = max(best_score, score_alias)

            # Match keywords
            for kw in concept.keywords:
                if kw in lower_q:
                    best_score = max(best_score, 85.0)

            if best_score >= threshold:
                matches.append((concept, best_score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


    def get_by_id(self, concept_id: str) -> Optional[PhysicsConcept]:
        return self._index.get(concept_id)


# Global instance
physics_kb = PhysicsKnowledgeBase()
