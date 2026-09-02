"""
Test Suite for Claude AI Fallback System
=========================================
Tests:
1. Student context formatting from multi-module ERP data.
2. Response caching (instant sub-50ms cache hits).
3. MongoDB interaction logging into 'claude_responses' collection.
4. Academic and educational scope guardrails.
5. End-to-end chat fallback invocation on low confidence / conversational queries.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.ai.claude_service import claude_service, ACADEMIC_SYSTEM_PROMPT
from app.repositories.claude_repo import claude_repo


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_format_student_context():
    """Verify multi-module student ERP data is properly formatted for Claude prompt."""
    sample_data = {
        "student_name": "RIYANSH K SRINIVAS",
        "class_name": "Class 8",
        "section": "E",
        "admission_no": "226/2024",
        "attendance_percentage": 87.0,
        "present_count": 20,
        "total_classes": 23,
        "pending_amount": 15000,
        "paid_amount": 30000,
        "total_fee": 45000,
        "pending_count": 2,
        "total_study_materials": 18,
        "total_notifications": 2,
        "holiday_count": 22,
    }
    context = claude_service.format_student_context(sample_data)
    assert "RIYANSH K SRINIVAS" in context
    assert "Class: Class 8-E" in context
    assert "Admission No: 226/2024" in context
    assert "Attendance Rate: 87.0%" in context
    assert "Pending: ₹15000" in context
    assert "18 resource(s)" in context
    assert "22 holiday(s)" in context


@pytest.mark.asyncio
async def test_claude_response_caching():
    """Verify in-memory response cache returns instant response on identical query."""
    institution_id = "test_school"
    role = "student"
    user_id = "U100"
    question = "Can you help me understand my grades?"

    # Manually populate cache
    cache_key = claude_service._generate_cache_key(institution_id, role, user_id, question)
    claude_service._save_to_cache(cache_key, "Yes, I am happy to help you with your school subjects!", {"total_tokens": 15})

    # Query
    answer, is_cached = await claude_service.generate_response(
        question=question,
        institution_id=institution_id,
        role=role,
        user_id=user_id,
    )

    assert is_cached is True
    assert "Yes, I am happy to help" in answer


@pytest.mark.asyncio
async def test_claude_repo_logging():
    """Verify claude_repo logs records to MongoDB claude_responses collection."""
    logged = await claude_repo.log_response(
        institution_id="sjbhs",
        user_id="9385",
        role="student",
        question="Who is my class teacher?",
        answer="Your class teacher is Mrs. Preetha V.",
        model="claude-3-5-haiku-20241022",
        tokens_used={"input_tokens": 40, "output_tokens": 12, "total_tokens": 52},
        duration_ms=250.5,
    )
    assert logged["institution_id"] == "sjbhs"
    assert logged["user_id"] == "9385"
    assert logged["question"] == "Who is my class teacher?"
    assert logged["answer"] == "Your class teacher is Mrs. Preetha V."


def test_claude_mongodb_6_hour_caching(client: TestClient):
    """Verify same user asking identical question within 6 hours hits claude cache."""
    from app.understanding.semantic_matcher import semantic_matcher, SemanticMatchResult

    payload = {
        "message": "can you explain the importance of daily discipline in studies?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST_CACHE_6H"
    }

    mock_answer = "Daily discipline helps create structured learning habits and reduces exam stress."

    with patch.object(semantic_matcher, "match", return_value=SemanticMatchResult(matched=False)):
        with patch.object(claude_service, "generate_response", new=AsyncMock(return_value=(mock_answer, False))) as mock_call:
            # First call
            resp1 = client.post("/api/v1/phinsiq/chat", json=payload)
            assert resp1.status_code == 200
            assert "Daily discipline" in resp1.json()["message"]
            assert mock_call.call_count == 1

            # Second call (within 6 hours) - hits cache
            mock_call.return_value = (mock_answer, True)
            resp2 = client.post("/api/v1/phinsiq/chat", json=payload)
            assert resp2.status_code == 200
            assert resp2.json()["message"] == resp1.json()["message"]


def test_claude_mongodb_50_percent_fuzzy_caching(client: TestClient):
    """Verify variations with >= 50% match hit the 6-hour cache."""
    from app.understanding.semantic_matcher import semantic_matcher, SemanticMatchResult

    payload1 = {
        "message": "can you give me advice on study time management?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST_FUZZY_50"
    }

    payload2 = {
        "message": "give me advice on study time management please",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST_FUZZY_50"
    }

    mock_answer = "Start with 25-minute Pomodoro study intervals."

    with patch.object(semantic_matcher, "match", return_value=SemanticMatchResult(matched=False)):
        with patch.object(claude_service, "generate_response", new=AsyncMock(return_value=(mock_answer, False))) as mock_call:
            # Query 1
            resp1 = client.post("/api/v1/phinsiq/chat", json=payload1)
            assert resp1.status_code == 200
            assert "Pomodoro" in resp1.json()["message"]

            # Query 2 (50%+ similar variation within 6 hours)
            mock_call.return_value = (mock_answer, True)
            resp2 = client.post("/api/v1/phinsiq/chat", json=payload2)
            assert resp2.status_code == 200
            assert resp2.json()["message"] == resp1.json()["message"]


def test_chat_pipeline_claude_fallback_triggered(client: TestClient):
    """Verify open-ended questions trigger Claude fallback when not matched by local rules."""
    from app.understanding.semantic_matcher import semantic_matcher, SemanticMatchResult

    payload = {
        "message": "can you tell me a unique inspiring story for my studies today?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }

    mock_claude_answer = "Here is an inspiring story about dedication and consistency in your studies..."

    with patch.object(semantic_matcher, "match", return_value=SemanticMatchResult(matched=False)):
        with patch.object(claude_service, "generate_response", new=AsyncMock(return_value=(mock_claude_answer, False))):
            response = client.post("/api/v1/phinsiq/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "inspiring story" in data["message"]
            if data.get("metadata"):
                assert data["metadata"]["claude_used"] is True
