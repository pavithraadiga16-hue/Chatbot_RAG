"""
Phase 1 Tests — Server, Health, and Basic Chat
=================================================

PURPOSE:
    Verify that Phase 1 implementation works:
    1. The server starts without errors
    2. /health returns 200 with correct structure
    3. /phinsiq/chat accepts valid requests and returns a structured response
    4. /phinsiq/chat rejects invalid requests with 422

HOW PYTEST WORKS:
    pytest discovers test files by looking for files named test_*.py or *_test.py
    Inside these files, it runs any function that starts with test_
    No manual registration needed — just write functions starting with 'test_'

HOW FASTAPI TESTING WORKS:
    FastAPI provides a TestClient (built on httpx) that makes HTTP requests
    WITHOUT starting a real server. This makes tests fast and isolated.

    The TestClient simulates the complete request lifecycle:
    1. Request body validation
    2. Route handler execution
    3. Response serialization

    WHY NOT TEST WITH A REAL SERVER?
        Real server tests (called "integration tests") need the server running.
        Unit tests with TestClient are faster and don't need network ports.

IMPORTANT NOTE:
    These tests do NOT connect to MongoDB in Phase 1.
    The chat endpoint returns a placeholder, so no database is needed.
    Database integration tests come in Phase 3.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


# =============================================================================
# Test Client Setup
# =============================================================================


@pytest.fixture
def client():
    """
    Create a test client with FastAPI lifespan context manager.
    Ensures MongoDB connection pool initializes at startup.
    """
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# Health Endpoint Tests
# =============================================================================


def test_health_returns_200(client: TestClient) -> None:
    """Health endpoint must return HTTP 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_structure(client: TestClient) -> None:
    """Health response must contain 'status': 'ok'."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "environment" in data


# =============================================================================
# Chat Endpoint — Valid Requests
# =============================================================================


def test_chat_valid_request(client: TestClient) -> None:
    """Valid chat request must return HTTP 200 with success=True."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sags_school",
            "role": "student",
            "user_id": "ST123",
            "message": "What is my attendance?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    assert len(data["message"]) > 0


def test_chat_response_structure(client: TestClient) -> None:
    """Chat response must follow the ChatResponse model structure."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sags_school",
            "role": "student",
            "user_id": "ST123",
            "message": "What is my attendance?",
        },
    )
    data = response.json()
    # Required fields
    assert "success" in data
    assert "message" in data


def test_chat_normalizes_institution_id(client: TestClient) -> None:
    """institution_id should be normalized to lowercase — SAGS_SCHOOL == sags_school."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "SAGS_SCHOOL",  # uppercase — should be normalized
            "role": "Student",  # mixed case
            "user_id": "ST123",
            "message": "Hello",
        },
    )
    # The server should process it without error (normalization happens in the model)
    assert response.status_code == 200


# =============================================================================
# Chat Endpoint — Invalid Requests (Validation Tests)
# =============================================================================


def test_chat_missing_institution_id(client: TestClient) -> None:
    """Missing required field must return 422 Unprocessable Entity."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "role": "student",
            "user_id": "ST123",
            "message": "What is my attendance?",
        },
    )
    assert response.status_code == 422


def test_chat_empty_message(client: TestClient) -> None:
    """Empty message must return 422."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sags_school",
            "role": "student",
            "user_id": "ST123",
            "message": "",  # empty string
        },
    )
    assert response.status_code == 422


def test_chat_whitespace_only_message(client: TestClient) -> None:
    """Whitespace-only message must return 422 after stripping."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sags_school",
            "role": "student",
            "user_id": "ST123",
            "message": "   ",  # spaces only
        },
    )
    assert response.status_code == 422


def test_chat_message_too_long(client: TestClient) -> None:
    """Message exceeding 2000 characters must return 422."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sags_school",
            "role": "student",
            "user_id": "ST123",
            "message": "x" * 2001,  # 2001 chars — exceeds max_length=2000
        },
    )
    assert response.status_code == 422


def test_chat_missing_body(client: TestClient) -> None:
    """Request without a body must return 422."""
    response = client.post("/api/v1/phinsiq/chat")
    assert response.status_code == 422


# =============================================================================
# 404 — Route Not Found
# =============================================================================


def test_unknown_route_returns_404(client: TestClient) -> None:
    """Requests to non-existent routes must return 404."""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
