"""Tests for policy document ingestion, retrieval, and routing separation."""

from pathlib import Path

from app.rag.ingestion import KNOWLEDGE_DIR, build_index
from app.rag.retriever import MIN_RELEVANCE, RetrievedChunk
from app.rag.rag_service import RAGService
from app.rag.router import (
    is_dynamic_campus_information_query,
    is_institutional_knowledge_query,
)
from app.rag.vector_store import SQLiteVectorStore
from app.understanding.module_detector import module_detector


def _build_test_store(tmp_path: Path) -> SQLiteVectorStore:
    database_path = tmp_path / "rag.sqlite3"
    count = build_index(KNOWLEDGE_DIR, database_path)
    assert count > 0
    return SQLiteVectorStore(database_path)


def test_minimum_attendance_query_retrieves_attendance_policy(tmp_path):
    store = _build_test_store(tmp_path)
    hits = store.search("What is the minimum attendance required?", top_k=3)
    assert hits[0][0].source == "attendance_policy.txt"
    assert hits[0][1] >= MIN_RELEVANCE
    assert "75%" in hits[0][0].content


def test_attendance_answer_uses_source_facts_without_leaking_sample_heading(tmp_path):
    store = _build_test_store(tmp_path)
    ranked = store.search("Explain the attendance policy.", top_k=3)
    chunks = [RetrievedChunk(r.source, r.document_type, r.chunk_id, r.content, score) for r, score in ranked]
    answer = RAGService._extract_evidence("Explain the attendance policy.", chunks)
    assert "75% attendance" in answer
    assert "DUMMY DEVELOPMENT SAMPLE" not in answer


def test_scholarship_documents_query_retrieves_scholarship_policy(tmp_path):
    store = _build_test_store(tmp_path)
    hits = store.search("What documents are required for scholarship?", top_k=3)
    assert hits[0][0].source == "scholarship_policy.txt"
    assert hits[0][1] >= MIN_RELEVANCE


def test_student_cgpa_remains_on_existing_exam_module():
    question = "What is my CGPA?"
    assert not is_institutional_knowledge_query(question)
    assert module_detector.detect(question).module == "exam"


def test_personal_attendance_remains_on_existing_attendance_module():
    question = "What is my attendance?"
    assert not is_institutional_knowledge_query(question)
    assert module_detector.detect(question).module == "attendance"


def test_explaining_attendance_policy_routes_to_rag(tmp_path):
    store = _build_test_store(tmp_path)
    question = "Explain the attendance policy."
    assert is_institutional_knowledge_query(question)
    hits = store.search(question, top_k=3)
    assert hits[0][0].source == "attendance_policy.txt"


def test_unknown_cafeteria_question_has_no_rag_match(tmp_path):
    store = _build_test_store(tmp_path)
    question = "What is the cafeteria menu today?"
    assert is_institutional_knowledge_query(question)
    assert is_dynamic_campus_information_query(question)
    hits = [(record, score) for record, score in store.search(question, top_k=3) if score >= MIN_RELEVANCE]
    assert hits == []

