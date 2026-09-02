"""
Admin Management API Tests
==========================
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client with FastAPI lifespan context manager (triggers DB connection)."""
    with TestClient(app) as test_client:
        yield test_client


def test_admin_institutions_crud(client: TestClient):
    payload = {
        "_id": "test_academy",
        "name": "Test Academy",
        "short_name": "TA",
        "status": "active",
        "roles": ["student", "staff"],
        "api_config": {
            "base_url": "https://erp.testacademy.example.com",
            "auth_type": "none",
            "headers": {"Content-Type": "application/json"}
        }
    }
    res = client.post("/api/v1/admin/institutions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # List
    res_list = client.get("/api/v1/admin/institutions")
    assert res_list.status_code == 200
    insts = res_list.json()
    assert any(i["_id"] == "test_academy" for i in insts)

    # Delete
    res_del = client.delete("/api/v1/admin/institutions/test_academy")
    assert res_del.status_code == 200


def test_admin_modules_crud(client: TestClient):
    payload = {
        "_id": "transport",
        "name": "Transport",
        "status": "active",
        "description": "School bus routes and fees"
    }
    res = client.post("/api/v1/admin/modules", json=payload)
    assert res.status_code == 200

    res_list = client.get("/api/v1/admin/modules")
    assert res_list.status_code == 200
    mods = res_list.json()
    assert any(m["_id"] == "transport" for m in mods)

    res_del = client.delete("/api/v1/admin/modules/transport")
    assert res_del.status_code == 200


def test_admin_registry_and_cache_flush(client: TestClient):
    payload = {
        "institution_id": "test_client",
        "role": "student",
        "module": "fees",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/fees",
            "body_template": {"uid": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {
            "total_fee": "totalfeepayment",
            "pending_amount": "due_bal"
        }
    }
    res = client.post("/api/v1/admin/registry", json=payload)
    assert res.status_code == 200

    # List
    res_list = client.get("/api/v1/admin/registry?institution_id=test_client")
    assert res_list.status_code == 200
    regs = res_list.json()
    assert len(regs) > 0
    assert regs[0]["response_mapping"]["total_fee"] == "totalfeepayment"

    # Flush cache
    res_flush = client.post("/api/v1/admin/cache/flush")
    assert res_flush.status_code == 200
    assert res_flush.json()["success"] is True

    # Clean up
    res_del = client.delete("/api/v1/admin/registry?institution_id=test_client&role=student&module=fees&action=summary")
    assert res_del.status_code == 200
