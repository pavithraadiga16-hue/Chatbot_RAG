"""
Test suite for /questions and question catalog endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.router.question_catalog import QUESTION_CATALOG, get_all_questions_flat, get_catalog_summary


@pytest.fixture
def client():
    """Create a test client with FastAPI lifespan context manager."""
    with TestClient(app) as test_client:
        yield test_client


def test_question_catalog_functions():
    """Verify catalog structure, total counts, and module coverage."""
    summary = get_catalog_summary()
    assert summary["status"] == "success"
    assert summary["total_questions"] >= 30
    assert summary["total_modules"] >= 8
    assert "fees" in summary["categories"]
    assert "attendance" in summary["categories"]
    assert "homework" in summary["categories"]
    assert "study_materials" in summary["categories"]
    assert "calendar_and_holidays" in summary["categories"]

    flat = get_all_questions_flat()
    assert len(flat) == summary["total_questions"]
    assert "What is my total fee?" in flat
    assert "What is my attendance percentage?" in flat


def test_get_questions_api_endpoint(client: TestClient):
    """Verify GET /questions returns HTTP 200 with structured JSON catalog."""
    res = client.get("/questions")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_questions"] > 35
    assert isinstance(data["questions"], list)
    assert isinstance(data["categories"], dict)

    # Test alias routes
    res_v1 = client.get("/api/v1/questions?institution_id=sjbhs&role=student")
    assert res_v1.status_code == 200
    data_v1 = res_v1.json()
    assert data_v1["institution_id"] == "sjbhs"
    assert data_v1["role"] == "student"

    res_phinsiq = client.get("/api/v1/phinsiq/questions?institution_id=sags_school&role=student")
    assert res_phinsiq.status_code == 200
    data_sags = res_phinsiq.json()
    assert data_sags["institution_id"] == "sags_school"


def test_admin_questions_crud(client: TestClient):
    """Verify Admin CRUD operations for sample questions (consolidated per-role schema)."""
    # 1. Add a custom question to a new corporate client
    payload = {
        "institution_id": "corporate_client_x",
        "role": "employee",
        "module": "payroll",
        "category_label": "💼 Payroll & Salary",
        "question": "What is my net salary for this month?",
        "field": "net_salary",
        "route": "/payroll",
        "description": "Returns calculated take-home pay",
    }
    create_res = client.post("/api/v1/admin/questions", json=payload)
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["success"] is True
    assert create_data["_id"] == "corporate_client_x_employee"   # consolidated doc _id

    # 2. List questions for the new client — should see the question in expanded flat list
    list_res = client.get(
        "/api/v1/admin/questions",
        params={"institution_id": "corporate_client_x", "role": "employee"},
    )
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(item["question"] == "What is my net salary for this month?" for item in items)

    # 3. Verify question is visible via /questions endpoint too
    catalog_res = client.get(
        "/questions",
        params={"institution_id": "corporate_client_x", "role": "employee"},
    )
    assert catalog_res.status_code == 200
    cat_data = catalog_res.json()
    assert cat_data["institution_id"] == "corporate_client_x"
    assert "What is my net salary for this month?" in cat_data["questions"]

    # 4. Seed endpoint
    seed_res = client.post(
        "/api/v1/admin/questions/seed",
        params={"institution_id": "sjbhs", "role": "student"},
    )
    assert seed_res.status_code == 200
    assert seed_res.json()["success"] is True

    # 5. Delete the specific question from the module sub-array
    del_res = client.delete(
        "/api/v1/admin/questions/corporate_client_x",
        params={
            "role": "employee",
            "module": "payroll",
            "question_text": "What is my net salary for this month?",
        },
    )
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 6. Verify question is gone from the list
    verify_res = client.get(
        "/api/v1/admin/questions",
        params={"institution_id": "corporate_client_x", "role": "employee"},
    )
    assert verify_res.status_code == 200
    remaining = verify_res.json()
    assert not any(item["question"] == "What is my net salary for this month?" for item in remaining)
