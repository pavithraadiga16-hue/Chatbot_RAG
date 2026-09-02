"""
Physics Numerical Natural Language Variable Parser
==================================================

PURPOSE:
    Extracts physical quantities, numerical values, and associated units from
    natural student language queries.
"""

import re
from typing import Optional, Any
from pydantic import BaseModel, Field


class ExtractedVariable(BaseModel):
    """A single extracted physical quantity."""
    quantity: str
    symbol: str
    value: float
    unit: str
    raw_text: str


class ParsedPhysicsQuery(BaseModel):
    """Complete parsed physics numerical problem."""
    original_query: str
    variables: dict[str, ExtractedVariable] = Field(default_factory=dict)
    target_quantity: Optional[str] = None
    target_symbol: Optional[str] = None


class PhysicsParser:
    """Extracts known variables and target quantities from natural language text."""

    def parse(self, query: str) -> ParsedPhysicsQuery:
        """Parses physical quantities and target variable from query."""
        lower_q = query.lower()
        extracted: dict[str, ExtractedVariable] = {}

        # 1. Mass (m): kg, g, grams, kilograms
        m_match = re.search(r'\b(?:mass|m)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(kg|kilograms?|g|grams?)?\b', lower_q) or \
                  re.search(r'(\d*\.?\d+)\s*(?:kg|kilograms?)\b', lower_q)
        if m_match:
            val_str = m_match.group(1)
            val = float(val_str)
            unit = m_match.group(2) if len(m_match.groups()) >= 2 and m_match.group(2) else "kg"
            if unit in ("g", "gram", "grams"):
                val = val / 1000.0
                unit = "kg"
            extracted["mass"] = ExtractedVariable(quantity="mass", symbol="m", value=val, unit="kg", raw_text=m_match.group(0))

        # 2. Acceleration (a): m/s^2, m/s2, ms-2
        a_match = re.search(r'\b(?:acceleration|acc|a)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(m/s\^?2|m/s2|ms-2)?\b', lower_q) or \
                  re.search(r'(\d*\.?\d+)\s*(?:m/s\^?2|m/s2|ms-2)\b', lower_q)
        if a_match:
            val = float(a_match.group(1))
            extracted["acceleration"] = ExtractedVariable(quantity="acceleration", symbol="a", value=val, unit="m/s²", raw_text=a_match.group(0))

        # 3. Distance / Displacement / Height / Length (s, d, h, l): meters, m, km, cm
        d_match = re.search(r'\b(?:distance|displacement|height|length|radius|depth|d|s|h|r)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(km|kilometers?|m|meters?|cm|centimeters?)?\b', lower_q) or \
                  re.search(r'(\d*\.?\d+)\s*(?:km|kilometers?|m|meters?|cm|centimeters?)\b', lower_q)
        if d_match:
            val = float(d_match.group(1))
            unit = d_match.group(2) if len(d_match.groups()) >= 2 and d_match.group(2) else "m"
            if unit in ("km", "kilometer", "kilometers"):
                val = val * 1000.0
            elif unit in ("cm", "centimeter", "centimeters"):
                val = val / 100.0
            extracted["distance"] = ExtractedVariable(quantity="distance", symbol="s", value=val, unit="m", raw_text=d_match.group(0))

        # 4. Time (t): seconds, s, minutes, min, hours, hr
        t_match = re.search(r'\b(?:time|t)\s*(?:is|=|of|:|in)?\s*(\d*\.?\d+)\s*(seconds?|sec|s|minutes?|min|hours?|hr|h)?\b', lower_q) or \
                  re.search(r'(?:in|for|over)?\s*(\d*\.?\d+)\s*(?:seconds?|sec|s|minutes?|min|hours?|hr|h)\b', lower_q)
        if t_match:
            val = float(t_match.group(1))
            unit = t_match.group(2) if len(t_match.groups()) >= 2 and t_match.group(2) else "s"
            if unit in ("min", "minute", "minutes"):
                val = val * 60.0
            elif unit in ("hr", "h", "hour", "hours"):
                val = val * 3600.0
            extracted["time"] = ExtractedVariable(quantity="time", symbol="t", value=val, unit="s", raw_text=t_match.group(0))

        # 5. Velocity / Speed (v, u): m/s, km/h, kmph
        v_match = re.search(r'\b(?:velocity|speed|v|u)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(m/s|km/h|kmph)?\b', lower_q) or \
                  re.search(r'(\d*\.?\d+)\s*(?:m/s|km/h|kmph)\b', lower_q)
        if v_match:
            val = float(v_match.group(1))
            unit = v_match.group(2) if len(v_match.groups()) >= 2 and v_match.group(2) else "m/s"
            if unit in ("km/h", "kmph"):
                val = val * (5.0 / 18.0)  # Convert km/h to m/s
            extracted["velocity"] = ExtractedVariable(quantity="velocity", symbol="v", value=val, unit="m/s", raw_text=v_match.group(0))

        # 6. Force (F): N, newton, newtons
        f_match = re.search(r'\b(?:force|f)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(n|newtons?)?\b', lower_q) or \
                  re.search(r'(\d*\.?\d+)\s*(?:n|newtons?)\b', lower_q)
        if f_match and "find force" not in lower_q and "calculate force" not in lower_q:
            val = float(f_match.group(1))
            extracted["force"] = ExtractedVariable(quantity="force", symbol="F", value=val, unit="N", raw_text=f_match.group(0))

        # 7. Voltage / Potential Difference (V): volts, V
        vol_match = re.search(r'\b(?:voltage|potential\s+difference|emf|v)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(v|volts?)?\b', lower_q) or \
                    re.search(r'(\d*\.?\d+)\s*(?:v|volts?)\b', lower_q)
        if vol_match and "find voltage" not in lower_q:
            val = float(vol_match.group(1))
            extracted["voltage"] = ExtractedVariable(quantity="voltage", symbol="V", value=val, unit="V", raw_text=vol_match.group(0))

        # 8. Current (I): A, amperes, mA
        cur_match = re.search(r'\b(?:current|i)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(a|amperes?|ma|milliamperes?)?\b', lower_q) or \
                    re.search(r'(\d*\.?\d+)\s*(?:a|amperes?|ma)\b', lower_q)
        if cur_match and "find current" not in lower_q:
            val = float(cur_match.group(1))
            unit = cur_match.group(2) if len(cur_match.groups()) >= 2 and cur_match.group(2) else "A"
            if unit in ("ma", "milliampere", "milliamperes"):
                val = val / 1000.0
            extracted["current"] = ExtractedVariable(quantity="current", symbol="I", value=val, unit="A", raw_text=cur_match.group(0))

        # 9. Resistance (R): ohm, ohms, Ω
        res_match = re.search(r'\b(?:resistance|resistor|r)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(ohms?|k\s*ohms?|kilo\s*ohms?|Ω)?\b', lower_q) or \
                    re.search(r'(\d*\.?\d+)\s*(?:ohms?|Ω)\b', lower_q)
        if res_match and "find resistance" not in lower_q:
            val = float(res_match.group(1))
            extracted["resistance"] = ExtractedVariable(quantity="resistance", symbol="R", value=val, unit="Ω", raw_text=res_match.group(0))

        # 10. Frequency (f): Hz, hertz, kHz
        freq_match = re.search(r'\b(?:frequency|f)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(hz|hertz|khz)?\b', lower_q) or \
                     re.search(r'(\d*\.?\d+)\s*(?:hz|hertz|khz)\b', lower_q)
        if freq_match and "find frequency" not in lower_q:
            val = float(freq_match.group(1))
            unit = freq_match.group(2) if len(freq_match.groups()) >= 2 and freq_match.group(2) else "Hz"
            if unit and "k" in unit:
                val = val * 1000.0
            extracted["frequency"] = ExtractedVariable(quantity="frequency", symbol="f", value=val, unit="Hz", raw_text=freq_match.group(0))

        # 11. Wavelength (lambda): m, nm, cm
        wl_match = re.search(r'\b(?:wavelength|lambda)\s*(?:is|=|of|:)?\s*(\d*\.?\d+)\s*(m|meters?|nm|nanometers?|cm)?\b', lower_q)
        if wl_match and "find wavelength" not in lower_q:
            val = float(wl_match.group(1))
            unit = wl_match.group(2) if len(wl_match.groups()) >= 2 and wl_match.group(2) else "m"
            if unit in ("nm", "nanometer", "nanometers"):
                val = val * 1e-9
            elif unit in ("cm",):
                val = val / 100.0
            extracted["wavelength"] = ExtractedVariable(quantity="wavelength", symbol="λ", value=val, unit="m", raw_text=wl_match.group(0))

        # 12. Focal length (f): cm, m
        foc_match = re.search(r'\b(?:focal\s+length|f)\s*(?:is|=|of|:)?\s*([+-]?\d*\.?\d+)\s*(cm|centimeters?|m|meters?)?\b', lower_q)
        if foc_match and "find focal length" not in lower_q:
            val = float(foc_match.group(1))
            unit = foc_match.group(2) if len(foc_match.groups()) >= 2 and foc_match.group(2) else "m"
            if unit in ("cm", "centimeter", "centimeters"):
                val = val / 100.0
            extracted["focal_length"] = ExtractedVariable(quantity="focal_length", symbol="f", value=val, unit="m", raw_text=foc_match.group(0))

        # Determine target quantity
        target_qty = None
        target_sym = None
        target_patterns = [
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+force\b', "force", "F"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+(?:velocity|speed)\b', "velocity", "v"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+acceleration\b', "acceleration", "a"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+(?:kinetic\s+energy|ke)\b', "kinetic_energy", "KE"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+(?:potential\s+energy|pe)\b', "potential_energy", "PE"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+work\b', "work", "W"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+power\b', "power", "P"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+momentum\b', "momentum", "p"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+(?:voltage|potential\s+difference)\b', "voltage", "V"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+current\b', "current", "I"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+resistance\b', "resistance", "R"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+density\b', "density", "ρ"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+pressure\b', "pressure", "P"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+(?:wavelength|frequency)\b', "wavelength", "λ"),
            (r'\b(?:find|calculate|what\s+is\s+the|determine)\s+(?:power\s+of\s+lens|lens\s+power)\b', "power_of_lens", "P"),
        ]
        for pat, qty, sym in target_patterns:
            if re.search(pat, lower_q):
                target_qty = qty
                target_sym = sym
                break

        # If no explicit "find X" was matched, infer target from available variables
        if not target_qty:
            if "mass" in extracted and "acceleration" in extracted:
                target_qty, target_sym = "force", "F"
            elif "distance" in extracted and "time" in extracted:
                target_qty, target_sym = "velocity", "v"
            elif "voltage" in extracted and "current" in extracted:
                target_qty, target_sym = "resistance", "R"
            elif "voltage" in extracted and "resistance" in extracted:
                target_qty, target_sym = "current", "I"
            elif "current" in extracted and "resistance" in extracted:
                target_qty, target_sym = "voltage", "V"
            elif "mass" in extracted and "velocity" in extracted:
                target_qty, target_sym = "kinetic_energy", "KE"
            elif "frequency" in extracted and "wavelength" in extracted:
                target_qty, target_sym = "velocity", "v"

        return ParsedPhysicsQuery(
            original_query=query,
            variables=extracted,
            target_quantity=target_qty,
            target_symbol=target_sym,
        )


# Global instance
physics_parser = PhysicsParser()
