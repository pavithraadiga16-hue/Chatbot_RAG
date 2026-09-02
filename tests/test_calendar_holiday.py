"""
Academic Calendar & Holiday Module Tests
=========================================

Verifies:
1. ArrayAggregator calendar operations (filter_events_contains, count_where_contains, calculate_event_duration, search_event_title)
2. Handling timestamps with time components (e.g., '2025-06-02 12:06:00')
3. Chat pipeline integration with Schoolphins SJBHS calendar API data
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.router.array_aggregator import array_aggregator
from mock_erp.mock_provider import MOCK_ERP_DATA


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


SAMPLE_CALENDAR = MOCK_ERP_DATA["sjbhs:student:calendar"]


def test_aggregator_filter_holidays():
    """Verify filter_events_contains extracts only items containing '(Holiday)'."""
    result = array_aggregator._op_filter_events_contains(
        source_array=SAMPLE_CALENDAR,
        search_key="title",
        contains_value="(Holiday)",
        title_key="title",
        start_key="start",
        end_key="end",
    )
    assert len(result) >= 2
    assert any("Bakrid (Holiday)" in r for r in result)
    assert any("Muharram (Holiday)" in r for r in result)


def test_aggregator_count_holidays():
    """Verify count_where_contains accurately counts holiday events."""
    count = array_aggregator._op_count_where_contains(
        source_array=SAMPLE_CALENDAR,
        search_key="title",
        contains_value="(Holiday)",
    )
    assert count >= 2


def test_aggregator_filter_reopening():
    """Verify filter_events_contains extracts school reopening dates."""
    reopen_events = array_aggregator._op_filter_events_contains(
        source_array=SAMPLE_CALENDAR,
        search_key="title",
        contains_value="reopen",
        title_key="title",
        start_key="start",
        end_key="end",
    )
    assert len(reopen_events) >= 3
    assert any("School Reopens Stds 5 to 10 & 12 — 02 Jun 2025" in e for e in reopen_events)
    assert any("School Reopens Stds 1 to 4 — 04 Jun 2025" in e for e in reopen_events)
    assert any("School Reopens UKG — 09 Jun 2025" in e for e in reopen_events)


def test_aggregator_event_duration_multi_day():
    """Verify calculate_event_duration accurately calculates date differences + 1."""
    # INIGO FEST is from 2025-07-28 to 2025-07-30 (3 days)
    duration_res = array_aggregator._op_calculate_event_duration(
        source_array=SAMPLE_CALENDAR,
        match_title="INIGO FEST",
        title_key="title",
        start_key="start",
        end_key="end",
    )
    assert duration_res is not None
    assert "3 days" in duration_res
    assert "28 Jul 2025 to 30 Jul 2025" in duration_res

    # 1st Unit Assessment is from 2025-07-21 to 2025-07-25 (5 days)
    assessment_res = array_aggregator._op_calculate_event_duration(
        source_array=SAMPLE_CALENDAR,
        match_title="1st Unit Assessment",
        title_key="title",
        start_key="start",
        end_key="end",
    )
    assert assessment_res is not None
    assert "5 days" in assessment_res


def test_aggregator_search_event_title():
    """Verify search_event_title locates specific events by title keywords."""
    res = array_aggregator._op_search_event_title(
        source_array=SAMPLE_CALENDAR,
        search_query="When is Yoga Day",
        title_key="title",
        start_key="start",
        end_key="end",
    )
    assert res is not None
    assert "Yoga Day" in res
    assert "21 Jun 2025" in res


def test_chat_holiday_list_query(client: TestClient):
    """Test full chat pipeline for 'When and all do I have holidays?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "When and all do I have holidays?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Bakrid (Holiday)" in data["message"]
    assert "Muharram (Holiday)" in data["message"]


def test_chat_holiday_count_query(client: TestClient):
    """Test full chat pipeline for 'How many holidays do we have?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "How many holidays do we have?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "holiday(s) scheduled in the academic calendar" in data["message"]


def test_chat_school_reopen_query(client: TestClient):
    """Test full chat pipeline for 'When does school reopen?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "When does school reopen?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "School Reopens Stds 5 to 10 & 12" in data["message"]
    assert "02 Jun 2025" in data["message"]


def test_chat_arbitrary_event_final_assessment(client: TestClient):
    """Test full chat pipeline for 'When is Final Assessment Commences PKG to Std 9?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "When is Final Assessment Commences PKG to Std 9?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Final Assessment Commences PKG to Std 9" in data["message"]
    assert "23 Feb 2026" in data["message"]


def test_chat_arbitrary_event_meraki(client: TestClient):
    """Test full chat pipeline for 'When is MERAKI?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "When is MERAKI?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "MERAKI" in data["message"]
    assert "31 Oct 2025" in data["message"]


def test_chat_arbitrary_event_dasara_vacation(client: TestClient):
    """Test full chat pipeline for 'When is Dasara Vacation?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "When is Dasara Vacation?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Dasara Vacation" in data["message"]
    assert "27 Sep 2025" in data["message"]


def test_chat_arbitrary_event_sjbhs_mun(client: TestClient):
    """Test full chat pipeline for 'When is SJBHS MUN?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "When is SJBHS MUN?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "SJBHS MUN" in data["message"]
    assert "16 Oct 2025" in data["message"]


def test_chat_date_query_naraka_chaturdashi(client: TestClient):
    """Test full chat pipeline for 'what is there on 20 Oct 2025?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "what is there on 20 Oct 2025?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Naraka Chaturdashi (Holiday)" in data["message"]
    assert "20 Oct 2025" in data["message"]


def test_chat_date_query_natural_october(client: TestClient):
    """Test full chat pipeline for 'what is there on 20 october 2025'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "what is there on 20 october 2025",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Naraka Chaturdashi (Holiday)" in data["message"]


def test_chat_date_query_slash_format(client: TestClient):
    """Test full chat pipeline for 'what is there on 20/09/2025'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "what is there on 20/09/2025",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "no events scheduled" in data["message"]
    assert "20 Sep 2025" in data["message"]


def test_chat_date_query_hyphen_format(client: TestClient):
    """Test full chat pipeline for 'what is there on 20-09-2025'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "what is there on 20-09-2025",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "no events scheduled" in data["message"]
    assert "20 Sep 2025" in data["message"]


def test_chat_date_query_sep_20_natural(client: TestClient):
    """Test full chat pipeline for 'what is there on 20 Sep 2025?'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "what is there on 20 Sep 2025?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "no events scheduled" in data["message"]
    assert "20 Sep 2025" in data["message"]


def test_chat_date_query_dasara_vacation(client: TestClient):
    """Test full chat pipeline for date falling in a multi-day event range 'what is there on 27 Sep 2025'."""
    response = client.post(
        "/api/v1/phinsiq/chat",
        json={
            "institution_id": "sjbhs",
            "role": "student",
            "user_id": "ST123",
            "message": "what is there on 27 Sep 2025?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Dasara Vacation" in data["message"]
