"""
Subject Engine Dedicated REST API Tests
=======================================

Verifies:
1. POST /api/v1/subject-engine/mathematics/solve
2. POST /api/v1/subject-engine/solve
3. GET /api/v1/subject-engine/mathematics/concepts
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_api_solve_mathematics_endpoint(client: TestClient):
    """Test dedicated mathematics solving endpoint."""
    payload = {
        "question": "x to the power 3 + 5x square"
    }
    response = client.post("/api/v1/subject-engine/mathematics/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["handled_locally"] is True
    assert data["subject"] == "mathematics"
    assert "x" in data["answer"] and "5" in data["answer"]
    assert len(data["steps"]) >= 1



def test_api_generic_solve_endpoint(client: TestClient):
    """Test generic subject engine solve endpoint."""
    payload = {
        "question": "solve 2x + 5 = 15"
    }
    response = client.post("/api/v1/subject-engine/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["handled_locally"] is True
    assert "x = 5" in data["answer"]


def test_api_get_concepts_catalog(client: TestClient):
    """Test retrieving mathematics concept catalog."""
    response = client.get("/api/v1/subject-engine/mathematics/concepts")
    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    assert len(concepts) >= 10
    concept_ids = [c["concept_id"] for c in concepts]
    assert "math.algebra.quadratic" in concept_ids
    assert "math.calculus.differentiation" in concept_ids
    assert "math.geometry.2d" in concept_ids
