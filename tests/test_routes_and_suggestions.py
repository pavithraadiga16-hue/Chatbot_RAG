"""
Tests for Module Navigation Routes and 3 Suggestion Questions
=============================================================
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.ai.claude_service import claude_service


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_fees_route_and_suggestions(client: TestClient):
    """Verify fees queries return /fees route and 3 relevant suggestion questions."""
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "ST123",
        "message": "What is my total fee?"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["route"] == "/fees"
    assert "response" in data
    assert "message" in data
    assert data["response"] == data["message"]

    assert isinstance(data["suggestion_questions"], list)
    assert len(data["suggestion_questions"]) == 3
    assert any("attendance" in q.lower() for q in data["suggestion_questions"])
    assert any("homework" in q.lower() for q in data["suggestion_questions"])


def test_homework_route_and_suggestions(client: TestClient):
    """Verify homework queries return /homework route and 3 suggestions."""
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "9385",
        "message": "show my pending homework"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["route"] == "/homework"
    assert len(data["suggestion_questions"]) == 3


def test_attendance_route_and_suggestions(client: TestClient):
    """Verify attendance queries return /attendance route and 3 suggestions."""
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "ST123",
        "message": "what is my attendance percentage?"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["route"] == "/attendance"
    assert len(data["suggestion_questions"]) == 3


def test_calendar_route_and_suggestions(client: TestClient):
    """Verify calendar queries return /calendar route and 3 suggestions."""
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "9385",
        "message": "when does school reopen?"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["route"] == "/calendar"
    assert len(data["suggestion_questions"]) == 3


def test_greeting_route_and_suggestions(client: TestClient):
    """Verify greetings return /dashboard route and 3 suggestions."""
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "ST123",
        "message": "hello"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["route"] == "/dashboard"
    assert len(data["suggestion_questions"]) == 3


def test_claude_fallback_route_and_suggestions(client: TestClient):
    """Verify Claude fallback responses return routes array and 3 suggestions."""
    from app.understanding.semantic_matcher import semantic_matcher, SemanticMatchResult
    from app.understanding.module_detector import module_detector, ModuleDetectionResult

    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "9385",
        "message": "can you share an inspiring study advice for me today?"
    }
    mock_ai_answer = (
        "Your attendance is 83.6%. Your pending fee balance is ₹29,300. "
        "Make sure to complete your homework and assignments regularly."
    )

    with patch.object(semantic_matcher, "match", return_value=SemanticMatchResult(matched=False)):
        with patch.object(module_detector, "detect", return_value=ModuleDetectionResult(module="unknown", confidence=0.1, method="none", all_scores={})):
            with patch.object(claude_service, "generate_response", new=AsyncMock(return_value=(mock_ai_answer, False))):
                resp = client.post("/api/v1/phinsiq/chat", json=payload)
                assert resp.status_code == 200
                data = resp.json()

                assert data["success"] is True
                assert isinstance(data["routes"], list)
                # Answer mentions attendance, fee, and homework -> all 3 routes returned
                assert "/attendance" in data["routes"]
                assert "/fees" in data["routes"]
                assert "/homework" in data["routes"]
                assert len(data["routes"]) >= 3
                assert data["response"] == mock_ai_answer
                assert len(data["suggestion_questions"]) == 3


def test_multi_module_query_routes(client: TestClient):
    """Verify asking a query touching attendance and fees returns both routes."""
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "ST123",
        "message": "tell me my attendance and fees"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert isinstance(data["routes"], list)
    assert "/attendance" in data["routes"]
    assert "/fees" in data["routes"]

