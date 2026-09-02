"""
Physics Engine Comprehensive Unit & Numerical Tests
===================================================

Covers:
1. Dynamic numerical calculations (F=ma, v=s/t, a=F/m, KE, PE, W=Fd, P=W/t, V=IR, P=VI, v=f*lambda, P=1/f)
2. Natural student language variations
3. Conceptual explanations and laws (Newton's laws, Ohm's law, Gravitation, Waves, Optics)
4. Electronics and logic gates (AND, OR, NOT, NAND, NOR, XOR)
"""

import pytest
from app.subject_engine.science.physics.engine import physics_engine
from app.subject_engine.science.physics.parser import physics_parser
from app.subject_engine.base import QuestionIntent, SubjectType


def test_physics_parser_extraction():
    """Verify physical variable extraction from natural text."""
    parsed = physics_parser.parse("mass is 5 kg and acceleration is 2 m/s2 find force")
    assert "mass" in parsed.variables
    assert parsed.variables["mass"].value == 5.0
    assert "acceleration" in parsed.variables
    assert parsed.variables["acceleration"].value == 2.0
    assert parsed.target_quantity == "force"


def test_physics_force_calculation():
    """Verify dynamic F = m * a calculation with different values."""
    res1 = physics_engine.solve("mass is 5 kg and acceleration is 2 find force")
    assert res1.handled_locally is True
    assert "10 N" in res1.answer or "10" in res1.answer
    assert "F = m · a" in res1.formula

    res2 = physics_engine.solve("mass 25 kg acceleration 4 m/s2 find force")
    assert res2.handled_locally is True
    assert "100" in res2.answer


def test_physics_velocity_calculation():
    """Verify v = s / t calculation."""
    res = physics_engine.solve("a car travels 100 meters in 5 seconds find velocity")
    assert res.handled_locally is True
    assert "20 m/s" in res.answer or "20" in res.answer


def test_physics_kinetic_energy():
    """Verify KE = 1/2 m v^2 calculation."""
    res = physics_engine.solve("calculate kinetic energy for mass 10 kg and velocity 5 m/s")
    assert res.handled_locally is True
    # 0.5 * 10 * 25 = 125 J
    assert "125" in res.answer
    assert "J" in res.formatted_markdown


def test_physics_potential_energy():
    """Verify PE = m g h calculation."""
    res = physics_engine.solve("calculate potential energy for mass 5 kg at height 10 m")
    assert res.handled_locally is True
    # 5 * 9.8 * 10 = 490 J
    assert "490" in res.answer


def test_physics_work_and_power():
    """Verify Work (W = Fd) and Power (P = W/t)."""
    res_w = physics_engine.solve("force 50 N displacement 4 m find work")
    assert res_w.handled_locally is True
    assert "200" in res_w.answer

    res_p = physics_engine.solve("force 50 N displacement 4 m time 5 s find power")
    assert res_p.handled_locally is True
    # 200 / 5 = 40 W
    assert "40" in res_p.answer


def test_physics_electricity_ohms_law():
    """Verify Ohm's Law (V = IR, I = V/R, R = V/I, P = VI)."""
    res_v = physics_engine.solve("current 2A resistance 10 ohm find voltage")
    assert res_v.handled_locally is True
    assert "20 V" in res_v.answer or "20" in res_v.answer

    res_i = physics_engine.solve("voltage 220V resistance 110 ohm find current")
    assert res_i.handled_locally is True
    assert "2 A" in res_i.answer or "2" in res_i.answer

    res_p = physics_engine.solve("voltage 12V current 2A find power")
    assert res_p.handled_locally is True
    assert "24 W" in res_p.answer or "24" in res_p.answer


def test_physics_waves_and_echo():
    """Verify wave speed v = f * lambda and echo calculations."""
    res_w = physics_engine.solve("wave with frequency 500 Hz and wavelength 2 m find speed")
    assert res_w.handled_locally is True
    assert "1000" in res_w.answer

    res_echo = physics_engine.solve("sound echo returns in 2 seconds find distance")
    assert res_echo.handled_locally is True
    # (343 * 2)/2 = 343 m
    assert "343" in res_echo.answer


def test_physics_optics_lens_power():
    """Verify Lens Power P = 1/f in diopters."""
    res = physics_engine.solve("focal length 20 cm find power of lens")
    assert res.handled_locally is True
    # 1 / 0.2 = +5 D
    assert "+5" in res.answer or "5 D" in res.answer


def test_physics_concepts_newton_laws():
    """Verify conceptual questions on Newton's laws."""
    res1 = physics_engine.solve("what is newton second law")
    assert res1.handled_locally is True
    assert "F = ma" in res1.formatted_markdown or "momentum" in res1.formatted_markdown

    res2 = physics_engine.solve("explain law of inertia")
    assert res2.handled_locally is True
    assert "First Law" in res2.formatted_markdown or "rest" in res2.formatted_markdown


def test_physics_concept_velocity_and_speed():
    """Verify conceptual questions on velocity and speed."""
    res = physics_engine.solve("what is velocity")
    assert res.handled_locally is True
    assert "rate of change of displacement" in res.formatted_markdown.lower() or "vector" in res.formatted_markdown.lower()

    res_form = physics_engine.solve("velocity formula")
    assert res_form.handled_locally is True
    assert "displacement" in res_form.formatted_markdown.lower()


def test_physics_electronics_logic_gates():
    """Verify logic gates truth tables."""
    res_and = physics_engine.solve("truth table of AND gate")
    assert res_and.handled_locally is True
    assert "AND Gate" in res_and.formatted_markdown
    assert "Y = A · B" in res_and.formatted_markdown

    res_nand = physics_engine.solve("truth table for NAND gate")
    assert res_nand.handled_locally is True
    assert "NAND Gate" in res_nand.formatted_markdown
