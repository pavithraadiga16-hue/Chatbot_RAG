"""
Homework Module Tests
=====================

Verifies:
1. ArrayAggregator homework operations:
   - _op_count (total homework)
   - _op_count_where_not (pending count where status != 'completed')
   - _op_filter_homework_list (pending & completed lists)
   - _op_dynamic_homework_search (subject search, due date search, pending search)
2. Intent classification and module detection for homework queries.
3. Chat pipeline integration with mock ERP homework data for SJBHS.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.router.array_aggregator import array_aggregator
from mock_erp.mock_provider import MOCK_ERP_DATA
from app.understanding.module_detector import ModuleDetector


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


SAMPLE_HOMEWORK = MOCK_ERP_DATA["sjbhs:student:homework"]


def test_aggregator_total_homework_count():
    """Verify counting total homework items."""
    total = array_aggregator._op_count(SAMPLE_HOMEWORK)
    assert total == 4


def test_aggregator_pending_homework_count():
    """Verify counting pending homework where status is not completed."""
    pending = array_aggregator._op_count_where_not(
        source_array=SAMPLE_HOMEWORK,
        filter_key="status",
        filter_value="completed,1,submitted"
    )
    assert pending == 3


def test_aggregator_filter_pending_homework():
    """Verify extracting pending homework list."""
    pending_list = array_aggregator._op_filter_homework_list(
        source_array=SAMPLE_HOMEWORK,
        filter_key="status",
        filter_value="completed,1,submitted",
        filter_mode="not_equals",
        subject_key="subject",
        desc_key="homework_discription",
        due_key="submission_date",
        teacher_key="sent_by",
        status_key="status",
    )
    assert len(pending_list) == 3
    assert any("Mathematics" in item for item in pending_list)
    assert any("Science" in item for item in pending_list)
    assert any("Social Studies" in item for item in pending_list)
    assert not any("English" in item for item in pending_list)  # English is completed


def test_aggregator_filter_completed_homework():
    """Verify extracting completed homework list."""
    completed_list = array_aggregator._op_filter_homework_list(
        source_array=SAMPLE_HOMEWORK,
        filter_key="status",
        filter_value="completed,1,submitted",
        filter_mode="equals",
        subject_key="subject",
        desc_key="homework_discription",
        due_key="submission_date",
        teacher_key="sent_by",
        status_key="status",
    )
    assert len(completed_list) == 1
    assert "English" in completed_list[0]
    assert "Completed" in completed_list[0]


def test_aggregator_search_by_subject():
    """Verify dynamic subject search (e.g. Math homework)."""
    res = array_aggregator._op_dynamic_homework_search(
        source_array=SAMPLE_HOMEWORK,
        search_query="What is my math homework?",
        subject_key="subject",
        desc_key="homework_discription",
        due_key="submission_date",
        teacher_key="sent_by",
        status_key="status",
    )
    assert res is not None
    assert "Mathematics" in res
    assert "quadratic equations" in res
    assert "Mrs. Anita Sharma" in res


def test_aggregator_search_submission_deadlines():
    """Verify deadline queries sorted by date."""
    res = array_aggregator._op_dynamic_homework_search(
        source_array=SAMPLE_HOMEWORK,
        search_query="When is the submission date for homework?",
        subject_key="subject",
        desc_key="homework_discription",
        due_key="submission_date",
        teacher_key="sent_by",
        status_key="status",
    )
    assert res is not None
    assert "Submission Deadlines" in res


def test_module_detector_homework():
    """Verify ModuleDetector recognizes homework questions."""
    detector = ModuleDetector()
    res1 = detector.detect("How much homework is pending?")
    assert res1.module == "homework"

    res2 = detector.detect("What is my science assignment?")
    assert res2.module == "homework"

    res3 = detector.detect("When is the homework submission date?")
    assert res3.module == "homework"


def test_chat_pipeline_pending_homework(client):
    """Verify end-to-end chat request for pending homework."""
    payload = {
        "message": "how much homework pending",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pending" in data["message"].lower() or "2" in data["message"]
    assert "fee" not in data["message"].lower()


def test_chat_pipeline_math_homework(client):
    """Verify end-to-end chat request for specific subject homework."""
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
    assert "Mathematics" in data["message"]
    assert "quadratic equations" in data["message"]
