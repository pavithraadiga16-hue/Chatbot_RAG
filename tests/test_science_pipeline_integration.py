"""
Science Engine Pipeline & API Integration Tests
===============================================

PURPOSE:
    Tests end-to-end Chat Pipeline and dedicated REST API endpoints for
    Science queries across Physics, Chemistry, and Biology.
    Ensures ZERO Claude calls on supported questions and verifies ERP exclusion rules.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.ai.claude_service import claude_service


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_physics_chat_pipeline_local_resolution(client: TestClient):
    """Verify Physics question resolves in pipeline with ZERO Claude calls."""
    payload = {
        "message": "mass is 5 kg and acceleration is 2 find force",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        resp = client.post("/api/v1/phinsiq/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["route"] == "NA"
        assert data["routes"] == ["NA"]

        # Verify Claude was NOT called
        assert mock_claude.call_count == 0

        # Verify response metadata
        if data.get("metadata"):
            assert data["metadata"]["claude_used"] is False
            assert "physics" in data["metadata"]["detected_module"] or "science" in data["metadata"]["detected_module"]

        # Verify answer content
        assert "10 N" in data["message"] or "10" in data["message"]
        assert "F = m · a" in data["message"]


def test_chemistry_chat_pipeline_local_resolution(client: TestClient):
    """Verify Chemistry reaction balancing resolves in pipeline with ZERO Claude calls."""
    payload = {
        "message": "balance H2 + O2 -> H2O",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        resp = client.post("/api/v1/phinsiq/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["route"] == "NA"
        assert data["routes"] == ["NA"]

        assert mock_claude.call_count == 0
        if data.get("metadata"):
            assert data["metadata"]["claude_used"] is False
        assert "2H2 + O2 → 2H2O" in data["message"] or "2H2 + O2 -> 2H2O" in data["message"]


def test_chemistry_water_formula_chat_pipeline(client: TestClient):
    """Verify 'what water formula' resolves to H2O Chemistry card with ZERO Claude calls."""
    payload = {
        "message": "what water formula",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        resp = client.post("/api/v1/phinsiq/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["route"] == "NA"
        assert data["routes"] == ["NA"]

        # Ensure Zero Claude calls
        assert mock_claude.call_count == 0

        # Ensure correct Chemistry response and H2O formula
        assert "H₂O" in data["message"] or "H2O" in data["message"]
        assert "Water" in data["message"]
        assert "Chemistry" in data["message"]


def test_biology_chat_pipeline_local_resolution(client: TestClient):

    """Verify Biology concept resolves in pipeline with ZERO Claude calls."""
    payload = {
        "message": "why is mitochondria called powerhouse of the cell",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        resp = client.post("/api/v1/phinsiq/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["route"] == "NA"
        assert data["routes"] == ["NA"]

        assert mock_claude.call_count == 0
        if data.get("metadata"):
            assert data["metadata"]["claude_used"] is False
        assert "ATP" in data["message"] or "respiration" in data["message"].lower()



def test_science_erp_homework_exclusion(client: TestClient):
    """Ensure ERP query containing 'homework' is NOT hijacked by Science Engine."""
    payload = {
        "message": "What is my science homework for tomorrow?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    if data.get("metadata"):
        assert data["metadata"]["detected_module"] == "homework"


def test_subject_engine_science_rest_endpoints(client: TestClient):
    """Verify dedicated REST endpoints for Science Engine."""
    # 1. POST /api/v1/subject-engine/science/solve
    resp_sci = client.post(
        "/api/v1/subject-engine/science/solve",
        json={"question": "what is h2so4 molecular mass"},
    )
    assert resp_sci.status_code == 200
    data_sci = resp_sci.json()
    assert data_sci["handled_locally"] is True
    assert "98" in data_sci["answer"]

    # 2. POST /api/v1/subject-engine/physics/solve
    resp_phys = client.post(
        "/api/v1/subject-engine/physics/solve",
        json={"question": "current 2A resistance 10 ohm find voltage"},
    )
    assert resp_phys.status_code == 200
    data_phys = resp_phys.json()
    assert data_phys["handled_locally"] is True
    assert "20" in data_phys["answer"]

    # 3. POST /api/v1/subject-engine/biology/solve
    resp_bio = client.post(
        "/api/v1/subject-engine/biology/solve",
        json={"question": "difference between mitosis and meiosis"},
    )
    assert resp_bio.status_code == 200
    data_bio = resp_bio.json()
    assert data_bio["handled_locally"] is True
    assert "Mitosis" in data_bio["formatted_markdown"]

    # 4. GET /api/v1/subject-engine/science/concepts
    resp_conc = client.get("/api/v1/subject-engine/science/concepts")
    assert resp_conc.status_code == 200
    data_conc = resp_conc.json()
    assert "physics" in data_conc
    assert "chemistry" in data_conc
    assert "biology" in data_conc
    assert len(data_conc["physics"]) > 0
    assert len(data_conc["chemistry"]) > 0
    assert len(data_conc["biology"]) > 0
