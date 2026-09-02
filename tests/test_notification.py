"""
Test Suite for Notification Module
===================================
Tests array aggregation, dynamic date/subject searches, and end-to-end chat pipeline
for student notifications, circulars, and notices.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.router.array_aggregator import ArrayAggregator
from app.understanding.module_detector import ModuleDetector

aggregator = ArrayAggregator()
detector = ModuleDetector()

SAMPLE_NOTIFICATIONS = [
    {
        "row_id": "1",
        "subject": "Sports Day Selection Trials",
        "message": "Selection trials for Inter-House Athletic Meet will be held on 20 Oct 2025 at 8:00 AM on the main ground.",
        "date_time": "2025-10-20 08:00:00",
        "filepath": "uploads/sports_meet.pdf",
        "filepath_two": "",
        "sent_by": "Physical Education Dept",
        "type": "event"
    },
    {
        "row_id": "2",
        "subject": "Parent Teacher Meeting (PTM)",
        "message": "Term 1 PTM for Standards 5 to 10 will be conducted on 02 Jun 2025 in respective classrooms.",
        "date_time": "2025-06-02 11:47:44",
        "filepath": "",
        "filepath_two": "",
        "sent_by": "Principal",
        "type": "circular"
    },
    {
        "row_id": "3",
        "subject": "School Reopening & Uniform Guidelines",
        "message": "Students are required to wear complete formal uniform with black shoes from Monday.",
        "date_time": "2025-06-01 09:30:00",
        "filepath": "uploads/uniform_rules.pdf",
        "filepath_two": "",
        "sent_by": "Principal",
        "type": "circular"
    },
    {
        "row_id": "4",
        "subject": "Science Exhibition 2026",
        "message": "Registration for the Annual Science Fair is open till next Friday. Submit project abstracts to your science teacher.",
        "date_time": "2026-08-28 10:30:00",
        "filepath": "",
        "filepath_two": "",
        "sent_by": "Science Dept",
        "type": "announcement"
    }
]


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_aggregator_total_notification_count():
    """Verify total notification count."""
    res = aggregator.aggregate(
        raw_response=SAMPLE_NOTIFICATIONS,
        field_definitions=[{
            "name": "total_notifications",
            "aggregation": {"source_field": "", "operation": "count"}
        }]
    )
    assert res.get("total_notifications") == 4


def test_aggregator_recent_notifications_sorting():
    """Verify recent notifications are sorted latest first (2026-08-28, then 2025-10-20, then 2025-06-02)."""
    res = aggregator.aggregate(
        raw_response=SAMPLE_NOTIFICATIONS,
        field_definitions=[{
            "name": "recent_notifications",
            "aggregation": {
                "source_field": "",
                "operation": "filter_recent_notifications",
                "limit": 3,
                "title_key": "subject",
                "desc_key": "message",
                "date_key": "date_time",
                "sender_key": "sent_by"
            }
        }]
    )
    recent = res.get("recent_notifications")
    assert isinstance(recent, list)
    assert len(recent) == 3
    # Top item must be Science Exhibition (2026-08-28)
    assert "Science Exhibition 2026" in recent[0]
    # Second item must be Sports Day (2025-10-20)
    assert "Sports Day Selection Trials" in recent[1]


def test_aggregator_search_by_date_natural():
    """Verify date-specific notification search for 'any notification on 20 October?'."""
    query = "Is there any notification on 20 October?"
    res = aggregator.aggregate(
        raw_response=SAMPLE_NOTIFICATIONS,
        field_definitions=[{
            "name": "notification_search",
            "aggregation": {
                "source_field": "",
                "operation": "dynamic_notification_search",
                "title_key": "subject",
                "desc_key": "message",
                "date_key": "date_time",
                "sender_key": "sent_by"
            }
        }],
        query_text=query
    )
    search_res = res.get("notification_search")
    assert search_res is not None
    assert "Sports Day Selection Trials" in search_res
    assert "Inter-House Athletic Meet" in search_res


def test_aggregator_search_by_subject():
    """Verify keyword subject search for 'circular about sports day'."""
    query = "circular about sports day"
    res = aggregator.aggregate(
        raw_response=SAMPLE_NOTIFICATIONS,
        field_definitions=[{
            "name": "notification_search",
            "aggregation": {
                "source_field": "",
                "operation": "dynamic_notification_search",
                "title_key": "subject",
                "desc_key": "message",
                "date_key": "date_time",
                "sender_key": "sent_by"
            }
        }],
        query_text=query
    )
    search_res = res.get("notification_search")
    assert search_res is not None
    assert "Sports Day Selection Trials" in search_res


def test_aggregator_search_by_sender():
    """Verify sender search for notifications sent by Principal."""
    query = "notifications sent by Principal"
    res = aggregator.aggregate(
        raw_response=SAMPLE_NOTIFICATIONS,
        field_definitions=[{
            "name": "notification_search",
            "aggregation": {
                "source_field": "",
                "operation": "dynamic_notification_search",
                "title_key": "subject",
                "desc_key": "message",
                "date_key": "date_time",
                "sender_key": "sent_by"
            }
        }],
        query_text=query
    )
    search_res = res.get("notification_search")
    assert search_res is not None
    assert "Parent Teacher Meeting" in search_res or "School Reopening" in search_res


def test_module_detector_notification():
    """Verify module detector correctly recognizes notification and circular intents."""
    res1 = detector.detect("How many notifications do I have?")
    assert res1.module in ("notification", "notice")

    res2 = detector.detect("What is the recent circular?")
    assert res2.module in ("notification", "notice")

    res3 = detector.detect("Any notice on the notice board?")
    assert res3.module in ("notification", "notice")


def test_chat_pipeline_notification_count(client: TestClient):
    """Verify end-to-end chat request for notification count."""
    payload = {
        "message": "how many notifications do I have",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "notification" in data["message"].lower() or "2" in data["message"]


def test_chat_pipeline_recent_notification(client: TestClient):
    """Verify end-to-end chat request for recent notifications."""
    payload = {
        "message": "what is the recent notification",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Sports Day" in data["message"] or "Parent Teacher Meeting" in data["message"]


def test_chat_pipeline_date_notification(client: TestClient):
    """Verify end-to-end chat request for date-specific notification search."""
    payload = {
        "message": "any notification on 20 October?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Sports Day Selection Trials" in data["message"]
