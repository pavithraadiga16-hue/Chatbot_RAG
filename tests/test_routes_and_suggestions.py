"""
Tests for Module Navigation Routes and 3 Suggestion Questions
=============================================================
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app


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


def test_rag_route_and_suggestions(client: TestClient):
    """Verify RAG responses return relevant routes array and 3 suggestions."""
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "9385",
        "message": "what is the minimum attendance requirement?"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert isinstance(data["routes"], list)
    assert "/attendance" in data["routes"]
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

