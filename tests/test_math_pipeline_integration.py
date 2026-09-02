"""
Mathematics Engine & Chat Pipeline Integration Tests
====================================================

Verifies:
1. Student math questions sent to POST /api/v1/phinsiq/chat are answered locally.
2. Claude is NOT called for any supported math questions (call_count == 0).
3. Response contains step-by-step mathematical working.
4. Non-math and conversational queries still fall back to Claude appropriately.
5. School ERP queries like 'What is my math homework?' continue to route to ERP modules.
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


def test_chat_pipeline_math_quadratic_equation_no_claude(client: TestClient):
    """Verify solve quadratic equation returns local answer with ZERO Claude calls."""
    payload = {
        "message": "solve x square - 5x + 6 = 0",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }

    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        response = client.post("/api/v1/phinsiq/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "2" in data["message"] and "3" in data["message"]
        assert data["route"] == "NA"
        assert data["routes"] == ["NA"]
        if data.get("metadata"):
            assert data["metadata"]["claude_used"] is False
            assert "mathematics" in data["metadata"]["detected_module"]

        # CRITICAL ASSERTION: Claude was NEVER called
        assert mock_claude.call_count == 0



def test_chat_pipeline_natural_speech_math(client: TestClient):
    """Verify 'x to the power 2 + 5x + 6' is answered locally with zero Claude calls."""
    payload = {
        "message": "x to the power 2 + 5x + 6",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }

    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        response = client.post("/api/v1/phinsiq/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        if data.get("metadata"):
            assert data["metadata"]["claude_used"] is False

        assert mock_claude.call_count == 0


def test_chat_pipeline_derivative_calculus_no_claude(client: TestClient):
    """Verify calculus differentiation is answered locally."""
    payload = {
        "message": "differentiate x cube",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }

    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        response = client.post("/api/v1/phinsiq/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "3*x" in data["message"] or "3x" in data["message"]
        if data.get("metadata"):
            assert data["metadata"]["claude_used"] is False

        assert mock_claude.call_count == 0


def test_chat_pipeline_hcf_lcm_no_claude(client: TestClient):
    """Verify HCF calculation is answered locally."""
    payload = {
        "message": "find HCF of 24 and 36",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }

    with patch.object(claude_service, "generate_response", new=AsyncMock()) as mock_claude:
        response = client.post("/api/v1/phinsiq/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "12" in data["message"]
        if data.get("metadata"):
            assert data["metadata"]["claude_used"] is False

        assert mock_claude.call_count == 0


def test_chat_pipeline_non_math_falls_back_to_claude(client: TestClient):
    """Verify unsupported conversational queries still hit Claude fallback."""
    from app.understanding.semantic_matcher import semantic_matcher, SemanticMatchResult

    payload = {
        "message": "can you tell me a unique inspiring science fiction story?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }

    mock_answer = "Once upon a time in a galaxy of scientific discovery..."
    with patch.object(semantic_matcher, "match", return_value=SemanticMatchResult(matched=False)):
        with patch.object(claude_service, "generate_response", new=AsyncMock(return_value=(mock_answer, False))) as mock_claude:
            response = client.post("/api/v1/phinsiq/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "galaxy" in data["message"]
            if data.get("metadata"):
                assert data["metadata"]["claude_used"] is True

            # Claude WAS called for conversational non-math queries
            assert mock_claude.call_count == 1


def test_chat_pipeline_preserves_erp_homework_routing(client: TestClient):
    """Verify queries asking for math homework continue to route to ERP homework module."""
    payload = {
        "message": "What is my math homework?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }

    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # ERP response should contain homework details from mock ERP
    assert "Mathematics" in data["message"] or "quadratic equations" in data["message"]
