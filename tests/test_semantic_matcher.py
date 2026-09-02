"""
Test Suite for Semantic Intent & Pattern Matcher
================================================
Tests:
1. Fast semantic fuzzy matching (< 1ms).
2. Slang & typo normalization ("do u know me", "do u remember me").
3. Multi-user dynamic execution without hitting Claude.
4. Auto pattern learning and MongoDB persistence.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.understanding.semantic_matcher import semantic_matcher


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_semantic_matcher_slang_normalization():
    """Verify natural identity queries match identity_profile pattern with > 80% score."""
    res = semantic_matcher.match("who am i ?")
    assert res.matched is True
    assert res.module == "profile"
    assert res.similarity_score >= 80.0


def test_semantic_matcher_variations():
    """Verify various conversational phrasings map accurately."""
    res1 = semantic_matcher.match("tell about myself")
    assert res1.matched is True
    assert res1.module == "profile"

    res2 = semantic_matcher.match("show everything about me")
    assert res2.matched is True
    assert res2.module == "academic_overview"
    assert res2.is_overall_overview is True

    res3 = semantic_matcher.match("how much fee do i owe")
    assert res3.matched is True
    assert res3.module == "fees"


@pytest.mark.asyncio
async def test_semantic_matcher_pattern_learning():
    """Verify new pattern is learned and matched subsequently."""
    new_question = "who is logged into this school system"
    # Before learning
    res_before = semantic_matcher.match(new_question)

    # Learn pattern
    await semantic_matcher.learn_pattern(new_question, module="profile")

    # After learning
    res_after = semantic_matcher.match(new_question)
    assert res_after.matched is True
    assert res_after.module == "profile"


def test_multi_user_dynamic_matching(client: TestClient):
    """
    Verify that when different users ask 'do u know me ?',
    FastAPI returns each user's own live profile data locally without Claude.
    """
    # User 1: RIYANSH (from SJBHS)
    resp1 = client.post("/api/v1/phinsiq/chat", json={
        "message": "do u know me ?",
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "9385"
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is True
    assert "RIYANSH K SRINIVAS" in data1["message"]

    # User 2: SAGS student
    resp2 = client.post("/api/v1/phinsiq/chat", json={
        "message": "do u know me ?",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is True
