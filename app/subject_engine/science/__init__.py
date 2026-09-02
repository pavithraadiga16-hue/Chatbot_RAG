"""
Science Engine Package
======================

Covers Physics, Chemistry, and Biology from LKG through PUC (Grade 12).
100% Deterministic (Zero Claude / External LLM dependency).
"""

from app.subject_engine.science.router import ScienceEngine, science_engine
from app.subject_engine.science.classifier import science_classifier
from app.subject_engine.science.formatter import science_formatter
from app.subject_engine.science.knowledge import SCIENTIFIC_CONSTANTS, get_constant
from app.subject_engine.science.physics.engine import physics_engine
from app.subject_engine.science.chemistry.engine import chemistry_engine
from app.subject_engine.science.biology.engine import biology_engine

__all__ = [
    "ScienceEngine",
    "science_engine",
    "physics_engine",
    "chemistry_engine",
    "biology_engine",
    "science_classifier",
    "science_formatter",
    "SCIENTIFIC_CONSTANTS",
    "get_constant",
]
