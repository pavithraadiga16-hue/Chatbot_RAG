"""
Test Suite for Personal Profile ("About Me") vs. 360° Academic Dashboard ("My Academic Info")
=============================================================================================
Verifies:
1. "about me" / "tell me about myself" / "who am i" routes to student profile.
2. "my academic info" / "overall performance" / "overall summary" / "everything about me"
   dynamically triggers all active modules in parallel and returns a comprehensive
   executive 360° Academic Dashboard.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.understanding.module_detector import ModuleDetector

detector = ModuleDetector()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_detector_about_me_routes_to_profile():
    """Verify personal identity queries route to profile module."""
    res1 = detector.detect("about me")
    assert res1.module == "profile"
    assert res1.is_overall_overview is False

    res2 = detector.detect("tell me about myself")
    assert res2.module == "profile"
    assert res2.is_overall_overview is False

    res3 = detector.detect("who am i")
    assert res3.module == "profile"
    assert res3.is_overall_overview is False

    res4 = detector.detect("my profile details")
    assert res4.module == "profile"
    assert res4.is_overall_overview is False


def test_detector_academic_overview_queries():
    """Verify academic overview and overall queries trigger 360 dashboard."""
    res1 = detector.detect("my academic info")
    assert res1.is_overall_overview is True

    res2 = detector.detect("academic details")
    assert res2.is_overall_overview is True

    res3 = detector.detect("overall performance")
    assert res3.is_overall_overview is True

    res4 = detector.detect("overall summary")
    assert res4.is_overall_overview is True

    res5 = detector.detect("everything about me")
    assert res5.is_overall_overview is True

    res6 = detector.detect("how am i doing in school")
    assert res6.is_overall_overview is True


def test_chat_pipeline_about_me_personal_details(client: TestClient):
    """Verify 'about me' returns rich student personal profile."""
    payload = {
        "message": "about me",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    msg = data["message"]
    assert "Student Profile Details" in msg
    assert "RIYANSH K SRINIVAS" in msg
    assert "Preetha" in msg
    assert "SRINIVAS K N" in msg


def test_chat_pipeline_my_academic_info_360_dashboard(client: TestClient):
    """Verify 'my academic info' executes all modules and builds the progress snapshot."""
    payload = {
        "message": "my academic info",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    msg = data["message"]

    # Must contain the progress snapshot header
    assert "academic progress snapshot" in msg or "Current Status" in msg

    # Must contain student identity
    assert "RIYANSH K SRINIVAS" in msg

    # Must contain attendance details
    assert "Attendance" in msg
    assert "%" in msg

    # Must contain fee status
    assert "Fee Status" in msg

    # Must contain homework details
    assert "Homework" in msg

    # Must contain strengths & areas of focus
    assert "Strengths" in msg
    assert "Areas to Focus On" in msg


def test_chat_pipeline_how_much_i_better(client: TestClient):
    """Verify 'hi phinsiq i want know my self how much i better' returns academic progress snapshot with live ERP data."""
    payload = {
        "message": "hi phinsiq i want know my self how much i better",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    msg = data["message"]

    assert "academic progress snapshot" in msg
    assert "Riyansh" in msg
    assert "Attendance" in msg
    assert "Strengths" in msg
    assert "Areas to Focus On" in msg
    assert "How to Improve Further" in msg


def test_chat_pipeline_overall_performance(client: TestClient):
    """Verify 'overall performance' triggers the 360° dashboard snapshot."""
    payload = {
        "message": "overall performance",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    msg = data["message"]
    assert "academic progress snapshot" in msg
    assert "Attendance" in msg
    assert "Fee Status" in msg


def test_chat_pipeline_everything_about_me(client: TestClient):
    """Verify 'everything about me' triggers the 360° dashboard snapshot."""
    payload = {
        "message": "everything about me",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    msg = data["message"]
    assert "academic progress snapshot" in msg
    assert "RIYANSH K SRINIVAS" in msg
