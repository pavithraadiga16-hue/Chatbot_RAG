"""
Test Suite for Student Profile Module
=====================================
Tests module detection, field mapping, and end-to-end chat queries for
personal student details, parent/guardian info, government IDs, and profile summary.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.understanding.module_detector import ModuleDetector
from app.router.response_mapper import ResponseMapper

detector = ModuleDetector()
mapper = ResponseMapper()

SAMPLE_RAW_PROFILE = {
    "row_id": "ST123",
    "student_id": "ST123",
    "dob": "2012-05-15",
    "father_name": "Mr. Rajesh Sharma",
    "mother_name": "Mrs. Anita Sharma",
    "guardian_name": "Mr. Rajesh Sharma",
    "father_mobile_one": "+91 98765 43210",
    "mother_mobile_one": "+91 98765 43211",
    "guardian_mobile_no": "+91 98765 43210",
    "email": "arjun.sharma@example.com",
    "father_email": "rajesh.sharma@example.com",
    "mother_email": "anita.sharma@example.com",
    "guardian_email": "rajesh.sharma@example.com",
    "present_address": "Flat 402, Palm Meadows, Museum Road, Bengaluru - 560001",
    "permanent_address": "Flat 402, Palm Meadows, Museum Road, Bengaluru - 560001",
    "blood_group": "O+",
    "gender": "Male",
    "religion_name": "Hindu",
    "nationality_name": "Indian",
    "caste": "General",
    "category_name": "General",
    "application_no": "APP2024089",
    "admission_no": "SJBHS-2022-458",
    "term_name": "Class 8",
    "section_name": "A",
    "house_color": "St Patrick (Green)",
    "name": "Mrs. Preetha V",
    "aadhar_no": "XXXX-XXXX-8921",
    "apaar_id": "9823-4567-1234",
    "sat_number": "SAT-890123",
    "student_pen_no": "PEN-2022-7712",
    "sts_no": "STS-994120",
    "language_two": "Kannada",
    "language_three": "Hindi",
    "photo_url": "uploads/student_photos/st123.jpg",
    "file_path_jpg": "uploads/student_photos/st123.jpg",
    "note": "Active participant in school debate."
}

MAPPING = {
    "student_id": "student_id",
    "dob": "dob",
    "father_name": "father_name",
    "mother_name": "mother_name",
    "guardian_name": "guardian_name",
    "mobile": "father_mobile_one",
    "father_mobile": "father_mobile_one",
    "mother_mobile": "mother_mobile_one",
    "email": "email",
    "address": "present_address",
    "permanent_address": "permanent_address",
    "blood_group": "blood_group",
    "gender": "gender",
    "class_name": "term_name",
    "section": "section_name",
    "class_teacher": "name",
    "house_color": "house_color",
    "admission_no": "admission_no",
    "application_no": "application_no",
    "aadhar_no": "aadhar_no",
    "apaar_id": "apaar_id",
    "pen_no": "student_pen_no",
    "sts_no": "sts_no",
    "sat_no": "sat_number",
    "second_language": "language_two",
    "third_language": "language_three",
    "religion": "religion_name",
    "caste": "caste",
    "category": "category_name",
    "nationality": "nationality_name",
}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_module_detector_profile_queries():
    """Verify module detector recognizes personal profile queries."""
    res1 = detector.detect("What is my date of birth?")
    assert res1.module == "profile"

    res2 = detector.detect("Tell my father name")
    assert res2.module == "profile"

    res3 = detector.detect("What is my mother's name?")
    assert res3.module == "profile"

    res4 = detector.detect("Who is my class teacher?")
    assert res4.module == "profile"

    res5 = detector.detect("What is my blood group?")
    assert res5.module == "profile"

    res6 = detector.detect("What is my Aadhaar number?")
    assert res6.module == "profile"

    res7 = detector.detect("What is my APAAR ID?")
    assert res7.module == "profile"

    res8 = detector.detect("Show my personal information")
    assert res8.module == "profile"


def test_response_mapper_profile():
    """Verify response mapping extracts all profile fields correctly."""
    mapped = mapper.map(
        raw_response=SAMPLE_RAW_PROFILE,
        response_mapping=MAPPING
    )
    assert mapped["dob"] == "2012-05-15"
    assert mapped["father_name"] == "Mr. Rajesh Sharma"
    assert mapped["mother_name"] == "Mrs. Anita Sharma"
    assert mapped["blood_group"] == "O+"
    assert mapped["class_teacher"] == "Mrs. Preetha V"
    assert mapped["class_name"] == "Class 8"
    assert mapped["section"] == "A"
    assert mapped["admission_no"] == "SJBHS-2022-458"
    assert mapped["apaar_id"] == "9823-4567-1234"


def test_chat_pipeline_dob(client: TestClient):
    """Verify end-to-end chat request for Date of Birth."""
    payload = {
        "message": "what is my date of birth",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "2019-06-06" in data["message"] or "06 Jun 2019" in data["message"]


def test_chat_pipeline_father_name(client: TestClient):
    """Verify end-to-end chat request for Father's name."""
    payload = {
        "message": "tell my father name",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "SRINIVAS K N" in data["message"]


def test_chat_pipeline_mother_name(client: TestClient):
    """Verify end-to-end chat request for Mother's name."""
    payload = {
        "message": "what is my mother name",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "MANASA N" in data["message"]


def test_chat_pipeline_class_teacher(client: TestClient):
    """Verify end-to-end chat request for Class Teacher name."""
    payload = {
        "message": "who is my class teacher",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Mrs. Preetha V" in data["message"]


def test_chat_pipeline_blood_group(client: TestClient):
    """Verify end-to-end chat request for Blood Group."""
    payload = {
        "message": "what is my blood group",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "O+" in data["message"]


def test_chat_pipeline_apaar_id(client: TestClient):
    """Verify end-to-end chat request for APAAR ID."""
    payload = {
        "message": "what is my apaar id",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "9823-4567-1234" in data["message"]


def test_chat_pipeline_student_name(client: TestClient):
    """Verify end-to-end chat request for Student Name."""
    payload = {
        "message": "what is my name",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "RIYANSH K SRINIVAS" in data["message"]


def test_chat_pipeline_who_am_i(client: TestClient):
    """Verify end-to-end chat request for 'who am i'."""
    payload = {
        "message": "who am i",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "RIYANSH K SRINIVAS" in data["message"]


def test_chat_pipeline_profile_summary(client: TestClient):
    """Verify end-to-end chat request for full profile overview."""
    payload = {
        "message": "show my personal information",
        "institution_id": "sags_school",
        "role": "student",
        "user_id": "ST123"
    }
    response = client.post("/api/v1/phinsiq/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "RIYANSH K SRINIVAS" in data["message"]
    assert "SRINIVAS K N" in data["message"]
    assert "MANASA N" in data["message"]
    assert "Preetha V" in data["message"]
