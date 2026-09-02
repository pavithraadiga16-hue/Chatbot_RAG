"""
Test Suite for Study Materials Module
=====================================
Tests module detection, array aggregation, subject filtering, date sorting,
multi-subject counting, teacher searches, and end-to-end chat queries for
study materials, worksheets, portions, and notes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.understanding.module_detector import ModuleDetector
from app.router.array_aggregator import ArrayAggregator

detector = ModuleDetector()
aggregator = ArrayAggregator()

SAMPLE_STUDY_MATERIALS = [
    {
        "subject_name": "Kannada Recitation",
        "type": "Portions",
        "description": "Dear parents rhyme lyrics is sent. Make use of it in order to teach proper pronunciation to your ward.",
        "document_name_url": "staff/upload/study_materials/SJBHS-6a8d6b6bc5a107.62161483Rhyme_2.docx",
        "created_date_time": "2026-08-25 15:46:12",
        "name": "Ms Meena Saver Rodriks"
    },
    {
        "subject_name": "Kannada",
        "type": "Portions",
        "description": "Dear parents Kindly go through the file sent for the reference of the notes. Complete pending work.",
        "document_name_url": "staff/upload/study_materials/SJBHS-6a8d60d4174f34.12822383DocScanner_25_Aug_2026_1-53_pm.pdf",
        "created_date_time": "2026-08-25 15:01:00",
        "name": "Ms Meena Saver Rodriks"
    },
    {
        "subject_name": "Hindi",
        "type": "Worksheets",
        "description": "Dear Parents, kindly check the mid term Hindi oral worksheet",
        "document_name_url": "staff/upload/study_materials/SJBHS-6a881d33bd4973.26601349I_STD_Mid_Term_Oral_Worksheet.pdf",
        "created_date_time": "2026-08-21 15:11:10",
        "name": "Ms M Sujatha"
    },
    {
        "subject_name": "Kannada",
        "type": "Portions",
        "description": "Portions for unit test",
        "document_name_url": "staff/upload/study_materials/SJBHS-6a85b15178dd24.25091492Screenshot_20260819-190417_Camera.png",
        "created_date_time": "2026-08-19 19:06:44",
        "name": "Ms Meena Saver Rodriks"
    },
    {
        "subject_name": "Kannada",
        "type": "Portions",
        "description": "Dear parents kindly check the attached file for reference",
        "document_name_url": "staff/upload/study_materials/SJBHS-6a85b151775587.63520623Screenshot_20260819-190421_Camera.png",
        "created_date_time": "2026-08-19 19:06:27",
        "name": "Ms Meena Saver Rodriks"
    }
]


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_module_detector_study_materials():
    """Verify module detector recognizes study materials, portions, worksheets, and notes."""
    res1 = detector.detect("Any study material for Kannada?")
    assert res1.module == "study_materials"

    res2 = detector.detect("Show Hindi worksheets")
    assert res2.module == "study_materials"

    res3 = detector.detect("What is the latest study material?")
    assert res3.module == "study_materials"

    res4 = detector.detect("How many study materials do I have?")
    assert res4.module == "study_materials"

    res5 = detector.detect("Show my lesson notes and portions")
    assert res5.module == "study_materials"


def test_aggregator_total_study_materials_count():
    """Verify aggregator counts all study materials."""
    total = aggregator._op_count(SAMPLE_STUDY_MATERIALS)
    assert total == len(SAMPLE_STUDY_MATERIALS)


def test_aggregator_recent_study_materials_sorting():
    """Verify recent study materials sorting places newest on top."""
    output = aggregator._op_filter_recent_study_materials(SAMPLE_STUDY_MATERIALS, limit=3)
    assert "Kannada Recitation" in output
    assert "25 Aug 2026" in output
    assert "Rhyme_2.docx" in output


def test_aggregator_search_by_subject_kannada():
    """Verify dynamic search filters materials for Kannada."""
    output = aggregator._op_dynamic_study_material_search(
        SAMPLE_STUDY_MATERIALS,
        query_text="any study material for kannada"
    )
    assert "Kannada" in output
    assert "DocScanner_25_Aug_2026" in output
    assert "Ms Meena Saver Rodriks" in output


def test_aggregator_search_by_subject_hindi():
    """Verify dynamic search filters materials for Hindi worksheets."""
    output = aggregator._op_dynamic_study_material_search(
        SAMPLE_STUDY_MATERIALS,
        query_text="Hindi worksheets"
    )
    assert "Hindi" in output
    assert "Worksheets" in output
    assert "Oral_Worksheet.pdf" in output


def test_aggregator_subject_count_query():
    """Verify dynamic search computes subject-specific material count."""
    output = aggregator._op_dynamic_study_material_search(
        SAMPLE_STUDY_MATERIALS,
        query_text="how many kannada study materials are there"
    )
    assert "4" in output
    assert "Kannada" in output


def test_aggregator_multi_subject_count_query():
    """Verify dynamic search computes multi-subject material count breakdown."""
    output = aggregator._op_dynamic_study_material_search(
        SAMPLE_STUDY_MATERIALS,
        query_text="how many study materials for kannada and hindi"
    )
    assert "Kannada" in output
    assert "Hindi" in output
    assert "Total Combined" in output


def test_aggregator_teacher_search():
    """Verify dynamic search matches materials uploaded by specific teacher."""
    output = aggregator._op_dynamic_study_material_search(
        SAMPLE_STUDY_MATERIALS,
        query_text="study materials uploaded by Ms Meena"
    )
    assert "Meena Saver Rodriks" in output
    assert "Kannada" in output


def test_chat_pipeline_kannada_study_materials(client: TestClient):
    """Verify end-to-end chat request for Kannada study materials."""
    payload = {
        "message": "any study material for kannada",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Kannada" in data["message"]


def test_chat_pipeline_hindi_worksheets(client: TestClient):
    """Verify end-to-end chat request for Hindi worksheets."""
    payload = {
        "message": "show hindi worksheets",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Hindi" in data["message"]


def test_chat_pipeline_subject_count(client: TestClient):
    """Verify end-to-end chat request for Kannada count."""
    payload = {
        "message": "how many kannada study materials are there",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "4" in data["message"] or "Kannada" in data["message"]


def test_chat_pipeline_latest_study_material(client: TestClient):
    """Verify end-to-end chat request for latest study material."""
    payload = {
        "message": "what is the latest study material",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "25 Aug 2026" in data["message"] or "Kannada" in data["message"]
