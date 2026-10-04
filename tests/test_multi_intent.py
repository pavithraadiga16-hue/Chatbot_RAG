"""Coverage for multi-module ERP and mixed ERP/RAG questions."""

from app.rag.router import (
    build_knowledge_query,
    is_institutional_knowledge_query,
    knowledge_topic_modules,
)
from app.understanding.field_detector import field_detector
from app.understanding.module_detector import module_detector


def _intents(question: str) -> list[str]:
    return module_detector.classify_multiple(question)


def test_single_fee_balance_intent_is_preserved():
    assert _intents("What is my fee balance?") == ["fees"]


def test_single_absence_intent_is_preserved():
    assert _intents("How many days was I absent?") == ["attendance"]


def test_fee_balance_and_absence_are_both_detected_and_fields_resolve():
    question = "What is my fee balance and how many days was I absent?"
    assert _intents(question) == ["fees", "attendance"]

    fee_fields = field_detector.detect(question, [{
        "name": "pending_amount",
        "aliases": ["fee balance", "balance"],
    }])
    attendance_fields = field_detector.detect(question, [{
        "name": "absent_count",
        "aliases": ["absent", "days absent", "how many days absent"],
    }])
    assert "pending_amount" in fee_fields.fields
    assert "absent_count" in attendance_fields.fields


def test_cgpa_and_attendance_are_both_detected():
    assert set(_intents("What is my CGPA and attendance?")) == {"exam", "attendance"}


def test_fee_balance_and_attendance_requirement_route_to_erp_and_rag():
    question = "What is my fee balance and what is the minimum attendance requirement?"
    assert _intents(question) == ["fees", "attendance"]
    assert is_institutional_knowledge_query(question)
    assert knowledge_topic_modules(question) == {"attendance"}
    assert build_knowledge_query(question, {"attendance"}) == "attendance minimum requirement"
    assert [module for module in _intents(question) if module not in knowledge_topic_modules(question)] == ["fees"]


def test_next_exam_and_attendance_are_both_detected():
    assert set(_intents("When is my next exam and what is my attendance?")) == {"exam", "attendance"}
