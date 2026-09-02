"""
Biology Engine Comprehensive Unit & Concept Tests
=================================================

Covers:
1. Natural student language variations ("why is mitochondria called powerhouse", "function of mitochondria")
2. Comparison and difference tables (Mitosis vs Meiosis, Xylem vs Phloem, Arteries vs Veins)
3. Plant physiology (Photosynthesis, Xylem, Phloem)
4. Human anatomy and physiology (Heart, Blood components, Nephron, Neuron)
5. Genetics and Mendel's laws (DNA, Monohybrid cross)
6. Ecology (Food chains, 10% law)
"""

import pytest
from app.subject_engine.science.biology.engine import biology_engine
from app.subject_engine.base import QuestionIntent, SubjectType


def test_biology_mitochondria_variations():
    """Verify natural variations of student queries for Mitochondria."""
    queries = [
        "why is mitochondria called powerhouse",
        "why mitochondria is called powerhouse of the cell",
        "function of mitochondria",
        "what is mitochondria",
        "what does mitochondria do",
    ]
    for q in queries:
        res = biology_engine.solve(q)
        assert res.handled_locally is True, f"Failed on query: {q}"
        assert res.subject == SubjectType.BIOLOGY
        assert "ATP" in res.formatted_markdown or "cellular respiration" in res.formatted_markdown.lower()
        assert "Powerhouse" in res.formatted_markdown


def test_biology_chloroplast_and_photosynthesis():
    """Verify chloroplast and photosynthesis queries."""
    res_chl = biology_engine.solve("what is chloroplast")
    assert res_chl.handled_locally is True
    assert "photosynthesis" in res_chl.formatted_markdown.lower()

    res_photo = biology_engine.solve("what is photosynthesis")
    assert res_photo.handled_locally is True
    assert "6CO₂" in res_photo.formatted_markdown or "glucose" in res_photo.formatted_markdown.lower()


def test_biology_comparison_tables():
    """Verify markdown comparison table generation for key biological contrasts."""
    # 1. Mitosis vs Meiosis
    res_mit = biology_engine.solve("difference between mitosis and meiosis")
    assert res_mit.handled_locally is True
    assert res_mit.intent == QuestionIntent.DIFFERENCE
    assert "Mitosis" in res_mit.formatted_markdown
    assert "Meiosis" in res_mit.formatted_markdown
    assert "Diploid" in res_mit.formatted_markdown or "Somatic" in res_mit.formatted_markdown

    # 2. Xylem vs Phloem
    res_xy = biology_engine.solve("difference between xylem and phloem")
    assert res_xy.handled_locally is True
    assert "Xylem" in res_xy.formatted_markdown
    assert "Phloem" in res_xy.formatted_markdown
    assert "Water" in res_xy.formatted_markdown or "minerals" in res_xy.formatted_markdown.lower()

    # 3. Arteries vs Veins
    res_art = biology_engine.solve("difference between arteries and veins")
    assert res_art.handled_locally is True
    assert "Arteries" in res_art.formatted_markdown
    assert "Veins" in res_art.formatted_markdown


def test_biology_human_physiology():
    """Verify human organ and cell systems."""
    # Nephron
    res_neph = biology_engine.solve("what is nephron")
    assert res_neph.handled_locally is True
    assert "filtration" in res_neph.formatted_markdown.lower() or "kidney" in res_neph.formatted_markdown.lower()

    # Neuron
    res_neur = biology_engine.solve("what is neuron")
    assert res_neur.handled_locally is True
    assert "impulse" in res_neur.formatted_markdown.lower() or "axon" in res_neur.formatted_markdown.lower()

    # Blood components
    res_rbc = biology_engine.solve("function of rbc")
    assert res_rbc.handled_locally is True
    assert "oxygen" in res_rbc.formatted_markdown.lower() or "hemoglobin" in res_rbc.formatted_markdown.lower()


def test_biology_genetics_and_dna():
    """Verify genetics queries."""
    res_dna = biology_engine.solve("what is dna")
    assert res_dna.handled_locally is True
    assert "genetic" in res_dna.formatted_markdown.lower()

    res_mendel = biology_engine.solve("explain mendel's laws")
    assert res_mendel.handled_locally is True
    assert "Segregation" in res_mendel.formatted_markdown or "Assortment" in res_mendel.formatted_markdown


def test_biology_ecology_food_chain():
    """Verify ecology and 10% law."""
    res_ec = biology_engine.solve("what is 10 percent law")
    assert res_ec.handled_locally is True
    assert "10%" in res_ec.formatted_markdown or "trophic" in res_ec.formatted_markdown.lower()
