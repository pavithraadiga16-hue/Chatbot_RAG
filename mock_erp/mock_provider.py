"""
PhinsIQ Mock ERP Provider
=========================

PURPOSE:
    Provides realistic mock responses for local development and testing
    when external ERP servers are unreachable, down, or return 500 errors.

IMPORTANT:
    **DEMO & DEVELOPMENT ONLY**
    This is completely separated from production logic.
    Real ERP integrations in production will always hit the real HTTP endpoints.

DATA STRUCTURE:
    Includes full data models for:
    - SJBHS / Schoolphins Fee Payment API (row_id: 868)
    - SAGS School Attendance, Fees, Exams, Leaves
"""

from typing import Any, Optional


MOCK_ERP_DATA: dict[str, dict[str, Any]] = {
    # SJBHS Fee Payment Info (matches exact Schoolphins response schema)
    "sjbhs:student:fees": {
        "instalment_status": False,
        "first_installmet": 25000,
        "second_installmet": 25000,
        "pending_amount": 15000,
        "total_fee_amount": 50000,
        "instalment_amt": 25000,
        "paid_amount": 35000,
        "concession": 5000,
        "is_paid": 0,
        "min_amount": 5000,
        "exam_paid_fee": 1000,
        "exam_pending_amt": 500,
        "exam_total_fee": 1500,
        "medium": "English",
        "pay_button": "1",
        "show_manual_entry": "1",
        "note_status": "1",
        "note_title": "Fee Reminder",
        "note_desc": "Please clear all pending dues before semester examination.",
        "studentInfo": {
            "student_id": "868",
            "student_name": "Arjun Kumar",
            "term_name": "Academic Term 2026-27",
            "semester": "1",
            "section_name": "A",
            "applied_course": "Computer Science",
            "father_name": "Ramesh Kumar",
            "pan_card_address": "Bangalore, Karnataka",
            "pan_card_holder_name": "Ramesh Kumar",
            "pan_card_number": "ABCDE1234F"
        }
    },

    # SJBHS Student Attendance (matches real Schoolphins attendance API response)
    # 61 records, June 2026 - August 2026, 8 absences, 53 present
    "sjbhs:student:attendance": {
        "start_date": "2026-06-01",
        "end_date": "2026-08-28",
        "attendance_data": [
            {"id": 1,  "date": "2026-06-03", "status": "present"},
            {"id": 2,  "date": "2026-06-04", "status": "present"},
            {"id": 3,  "date": "2026-06-05", "status": "present"},
            {"id": 4,  "date": "2026-06-08", "status": "absent"},
            {"id": 5,  "date": "2026-06-09", "status": "present"},
            {"id": 6,  "date": "2026-06-10", "status": "present"},
            {"id": 7,  "date": "2026-06-11", "status": "present"},
            {"id": 8,  "date": "2026-06-12", "status": "present"},
            {"id": 9,  "date": "2026-06-15", "status": "present"},
            {"id": 10, "date": "2026-06-16", "status": "present"},
            {"id": 11, "date": "2026-06-17", "status": "present"},
            {"id": 12, "date": "2026-06-18", "status": "present"},
            {"id": 13, "date": "2026-06-19", "status": "present"},
            {"id": 14, "date": "2026-06-22", "status": "absent"},
            {"id": 15, "date": "2026-06-23", "status": "present"},
            {"id": 16, "date": "2026-06-24", "status": "present"},
            {"id": 17, "date": "2026-06-25", "status": "present"},
            {"id": 18, "date": "2026-06-29", "status": "present"},
            {"id": 19, "date": "2026-06-30", "status": "present"},
            {"id": 20, "date": "2026-07-01", "status": "absent"},
            {"id": 21, "date": "2026-07-02", "status": "present"},
            {"id": 22, "date": "2026-07-03", "status": "present"},
            {"id": 23, "date": "2026-07-06", "status": "present"},
            {"id": 24, "date": "2026-07-07", "status": "present"},
            {"id": 25, "date": "2026-07-08", "status": "present"},
            {"id": 26, "date": "2026-07-09", "status": "present"},
            {"id": 27, "date": "2026-07-10", "status": "present"},
            {"id": 28, "date": "2026-07-13", "status": "absent"},
            {"id": 29, "date": "2026-07-14", "status": "present"},
            {"id": 30, "date": "2026-07-15", "status": "present"},
            {"id": 31, "date": "2026-07-16", "status": "present"},
            {"id": 32, "date": "2026-07-17", "status": "present"},
            {"id": 33, "date": "2026-07-20", "status": "present"},
            {"id": 34, "date": "2026-07-21", "status": "present"},
            {"id": 35, "date": "2026-07-22", "status": "present"},
            {"id": 36, "date": "2026-07-23", "status": "present"},
            {"id": 37, "date": "2026-07-24", "status": "present"},
            {"id": 38, "date": "2026-07-27", "status": "present"},
            {"id": 39, "date": "2026-07-28", "status": "present"},
            {"id": 40, "date": "2026-07-29", "status": "present"},
            {"id": 41, "date": "2026-07-30", "status": "absent"},
            {"id": 42, "date": "2026-08-03", "status": "present"},
            {"id": 43, "date": "2026-08-04", "status": "absent"},
            {"id": 44, "date": "2026-08-05", "status": "absent"},
            {"id": 45, "date": "2026-08-06", "status": "absent"},
            {"id": 46, "date": "2026-08-07", "status": "present"},
            {"id": 47, "date": "2026-08-10", "status": "present"},
            {"id": 48, "date": "2026-08-11", "status": "present"},
            {"id": 49, "date": "2026-08-12", "status": "present"},
            {"id": 50, "date": "2026-08-13", "status": "present"},
            {"id": 51, "date": "2026-08-14", "status": "present"},
            {"id": 52, "date": "2026-08-17", "status": "present"},
            {"id": 53, "date": "2026-08-18", "status": "present"},
            {"id": 54, "date": "2026-08-19", "status": "present"},
            {"id": 55, "date": "2026-08-20", "status": "present"},
            {"id": 56, "date": "2026-08-21", "status": "present"},
            {"id": 57, "date": "2026-08-22", "status": "present"},
            {"id": 58, "date": "2026-08-24", "status": "present"},
            {"id": 59, "date": "2026-08-25", "status": "present"},
            {"id": 60, "date": "2026-08-27", "status": "absent"},
            {"id": 61, "date": "2026-08-28", "status": "absent"},
        ]
    },

    # SAGS School Attendance
    "sags_school:student:attendance": {
        "start_date": "2026-06-01",
        "end_date": "2026-08-28",
        "attendance_data": [
            {"id": 1,  "date": "2026-06-03", "status": "present"},
            {"id": 2,  "date": "2026-06-04", "status": "present"},
            {"id": 3,  "date": "2026-06-05", "status": "present"},
            {"id": 4,  "date": "2026-06-08", "status": "absent"},
            {"id": 5,  "date": "2026-06-09", "status": "present"},
            {"id": 6,  "date": "2026-06-10", "status": "present"},
            {"id": 7,  "date": "2026-06-11", "status": "present"},
            {"id": 8,  "date": "2026-06-12", "status": "present"},
            {"id": 9,  "date": "2026-06-15", "status": "present"},
            {"id": 10, "date": "2026-06-16", "status": "present"},
            {"id": 11, "date": "2026-06-17", "status": "present"},
            {"id": 12, "date": "2026-06-18", "status": "present"},
            {"id": 13, "date": "2026-06-19", "status": "present"},
            {"id": 14, "date": "2026-06-22", "status": "absent"},
            {"id": 15, "date": "2026-06-23", "status": "present"},
            {"id": 16, "date": "2026-06-24", "status": "present"},
            {"id": 17, "date": "2026-06-25", "status": "present"},
            {"id": 18, "date": "2026-06-29", "status": "present"},
            {"id": 19, "date": "2026-06-30", "status": "present"},
            {"id": 20, "date": "2026-07-01", "status": "absent"},
            {"id": 21, "date": "2026-07-02", "status": "present"},
            {"id": 22, "date": "2026-07-03", "status": "present"},
            {"id": 23, "date": "2026-07-06", "status": "present"}
        ]
    },

    # SAGS School Fees
    "sags_school:student:fees": {
        "total_fee": 45000,
        "paid_fee": 30000,
        "pending_fee": 15000,
        "discount": 0
    },

    # SAGS School Exams
    "sags_school:student:exam": {
        "upcoming_exams": [
            {"subject": "Mathematics", "date": "2026-09-15", "time": "09:30 AM"},
            {"subject": "Physics", "date": "2026-09-18", "time": "09:30 AM"},
            {"subject": "Computer Science", "date": "2026-09-21", "time": "09:30 AM"}
        ],
        "last_gpa": 3.8
    },

    # SAGS School Staff Leaves
    "sags_school:staff:leave": {
        "total_leaves": 24,
        "used_leaves": 8,
        "remaining_leaves": 16,
        "sick_leaves": 5,
        "casual_leaves": 11
    },

    # SJBHS / Schoolphins Academic Calendar & Holidays
    "sjbhs:student:calendar": [
        {"row_id": "2", "title": "School Reopens Stds 5 to 10 & 12", "start": "2025-06-02 12:06:00", "end": "2025-06-02 12:06:00", "all_day": "1", "created_by": "Parrophins", "created_date_time": "2025-06-02 10:20:14", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "3", "title": "School Reopens Stds 1 to 4", "start": "2025-06-04 12:06:00", "end": "2025-06-04 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-02 11:47:44", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "4", "title": "World Environment Day", "start": "2025-06-05 12:06:00", "end": "2025-06-05 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-02 11:48:13", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "5", "title": "Orientation for Std 11", "start": "2025-06-06 12:06:00", "end": "2025-06-06 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:01:25", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "6", "title": "Bakrid (Holiday)", "start": "2025-06-07 12:06:00", "end": "2025-06-07 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:01:36", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "7", "title": "School Reopens UKG", "start": "2025-06-09 12:06:00", "end": "2025-06-09 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:01:48", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "8", "title": "11 School Commences LKG Orientation for Parents", "start": "2025-06-11 12:06:00", "end": "2025-06-11 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:01:58", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "9", "title": "Mass of the Holy Spirit", "start": "2025-06-13 12:06:00", "end": "2025-06-13 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:02:11", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "10", "title": "Inter-House Chess & Hockey Tournament", "start": "2025-06-14 12:06:00", "end": "2025-06-14 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:02:20", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "11", "title": "16 School Commences Pre-KG", "start": "2025-06-16 12:06:00", "end": "2025-06-16 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:02:43", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "12", "title": "Inter-House Basketball Tournament", "start": "2025-06-10 12:06:00", "end": "2025-06-12 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:03:13", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "13", "title": "Personality Development PTA - AGM", "start": "2025-06-20 12:06:00", "end": "2025-06-20 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:03:38", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "14", "title": "Yoga Day", "start": "2025-06-21 12:06:00", "end": "2025-06-21 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:04:10", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "15", "title": "Inter-Faith Prayer Service", "start": "2025-06-25 12:06:00", "end": "2025-06-25 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:04:28", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "16", "title": "Transendence", "start": "2025-06-27 12:06:00", "end": "2025-06-28 12:06:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-06-26 05:04:45", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "17", "title": "Harmony Day", "start": "2025-07-01 12:07:00", "end": "2025-07-01 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:44:32", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "18", "title": "Annual Prize Day / Inter-House Badminton Tourament", "start": "2025-07-05 12:07:00", "end": "2025-07-05 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:45:14", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "19", "title": "Muharram (Holiday)", "start": "2025-07-06 12:07:00", "end": "2025-07-06 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:45:35", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "20", "title": "OBA Buzz", "start": "2025-07-07 12:07:00", "end": "2025-07-11 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:46:19", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "21", "title": "DYNAMIX Dance Fest ( Stds 7 to 12 ) / Inter-House Football / Table Tennis Tournament", "start": "2025-07-12 12:07:00", "end": "2025-07-12 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:46:47", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "22", "title": "Grandparents' Day (only for LKG Parents)", "start": "2025-07-18 12:07:00", "end": "2025-07-18 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:47:15", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "23", "title": "1st Unit Assessment Stds 1 To 12 / Athletic Heats (Pre-Primary)", "start": "2025-07-21 12:07:00", "end": "2025-07-25 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:47:55", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "24", "title": "INIGO FEST / Athletic Heats", "start": "2025-07-28 12:07:00", "end": "2025-07-30 12:07:00", "all_day": "1", "created_by": "Mr Muniraju K", "created_date_time": "2025-08-26 12:48:15", "updated_by": "", "updated_date_time": "0000-00-00 00:00:00", "is_deleted": "0"},
        {"row_id": "50", "title": "Dasara Vacation", "start": "2025-09-27 12:09:00", "end": "2025-10-07 12:10:00", "all_day": "1"},
        {"row_id": "53", "title": "SJBHS MUN", "start": "2025-10-16 12:10:00", "end": "2025-10-18 12:10:00", "all_day": "1"},
        {"row_id": "59", "title": "MERAKI", "start": "2025-10-31 12:10:00", "end": "2025-10-31 12:10:00", "all_day": "1"},
        {"row_id": "85", "title": "Investiture Ceremony & Annual Day", "start": "2026-01-23 12:01:00", "end": "2026-01-23 12:01:00", "all_day": "1"},
        {"row_id": "106", "title": "Final Assessment Commences PKG to Std 9", "start": "2026-02-23 12:02:00", "end": "2026-02-27 12:02:00", "all_day": "1"}
    ],
    "sjbhs:student:holiday": [
        {"row_id": "6", "title": "Bakrid (Holiday)", "start": "2025-06-07 12:06:00", "end": "2025-06-07 12:06:00", "all_day": "1"},
        {"row_id": "19", "title": "Muharram (Holiday)", "start": "2025-07-06 12:07:00", "end": "2025-07-06 12:07:00", "all_day": "1"}
    ],

    # SAGS School Academic Calendar & Holidays
    "sags_school:student:calendar": [
        {"row_id": "1", "title": "School Reopens", "start": "2025-06-02", "end": "2025-06-02", "all_day": "1"},
        {"row_id": "2", "title": "Bakrid (Holiday)", "start": "2025-06-07", "end": "2025-06-07", "all_day": "1"},
        {"row_id": "3", "title": "Muharram (Holiday)", "start": "2025-07-06", "end": "2025-07-06", "all_day": "1"},
        {"row_id": "4", "title": "Annual Sports Fest", "start": "2025-07-25", "end": "2025-07-27", "all_day": "1"}
    ],
    "sags_school:student:holiday": [
        {"row_id": "2", "title": "Bakrid (Holiday)", "start": "2025-06-07", "end": "2025-06-07", "all_day": "1"},
        {"row_id": "3", "title": "Muharram (Holiday)", "start": "2025-07-06", "end": "2025-07-06", "all_day": "1"}
    ],

    # SJBHS Homework Dataset
    "sjbhs:student:homework": [
        {
            "row_id": "101",
            "sent_by": "Mrs. Anita Sharma",
            "subject": "Mathematics",
            "homework_discription": "Complete exercise 4.2 questions 1 to 10 on quadratic equations.",
            "filepath": "uploads/hw_math_4_2.pdf",
            "filepath2": "",
            "submission_date": "2026-09-05",
            "completed_status": "0",
            "status": "pending",
            "date_time": "2026-08-28 10:30:00"
        },
        {
            "row_id": "102",
            "sent_by": "Mr. Joseph D'Souza",
            "subject": "Science",
            "homework_discription": "Draw and label the human respiratory system diagram in lab notebook.",
            "filepath": "uploads/science_respiratory.pdf",
            "filepath2": "",
            "submission_date": "2026-09-07",
            "completed_status": "0",
            "status": "pending",
            "date_time": "2026-08-27 14:15:00"
        },
        {
            "row_id": "103",
            "sent_by": "Ms. Priya Menon",
            "subject": "English",
            "homework_discription": "Write an essay on 'The Role of Technology in Education' (300 words).",
            "filepath": "",
            "filepath2": "",
            "submission_date": "2026-09-02",
            "completed_status": "1",
            "status": "completed",
            "date_time": "2026-08-25 09:00:00"
        },
        {
            "row_id": "104",
            "sent_by": "Mr. Ramesh Kumar",
            "subject": "Social Studies",
            "homework_discription": "Read Chapter 3 on Indian Constitution and answer question numbers 1 to 5.",
            "filepath": "",
            "filepath2": "",
            "submission_date": "2026-09-10",
            "completed_status": "0",
            "status": "pending",
            "date_time": "2026-08-29 11:00:00"
        }
    ],
    "sags_school:student:homework": [
        {
            "row_id": "101",
            "sent_by": "Mrs. Anita Sharma",
            "subject": "Mathematics",
            "homework_discription": "Complete exercise 4.2 questions 1 to 10 on quadratic equations.",
            "filepath": "uploads/hw_math_4_2.pdf",
            "filepath2": "",
            "submission_date": "2026-09-05",
            "completed_status": "0",
            "status": "pending",
            "date_time": "2026-08-28 10:30:00"
        },
        {
            "row_id": "102",
            "sent_by": "Mr. Joseph D'Souza",
            "subject": "Science",
            "homework_discription": "Draw and label the human respiratory system diagram in lab notebook.",
            "filepath": "uploads/science_respiratory.pdf",
            "filepath2": "",
            "submission_date": "2026-09-07",
            "completed_status": "0",
            "status": "pending",
            "date_time": "2026-08-27 14:15:00"
        },
        {
            "row_id": "103",
            "sent_by": "Ms. Priya Menon",
            "subject": "English",
            "homework_discription": "Write an essay on 'The Role of Technology in Education' (300 words).",
            "filepath": "",
            "filepath2": "",
            "submission_date": "2026-09-02",
            "completed_status": "1",
            "status": "completed",
            "date_time": "2026-08-25 09:00:00"
        }
    ],

    # SJBHS Notifications Dataset
    "sjbhs:student:notification": [
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
    ],
    "sags_school:student:notification": [
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
        }
    ],

    # Student Profile Datasets
    "sjbhs:student:profile": {
        "row_id": "2",
        "student_id": "ST123",
        "student_name": "RIYANSH K SRINIVAS",
        "dob": "2019-06-06",
        "father_name": "SRINIVAS K N",
        "mother_name": "MANASA N",
        "guardian_name": "SRINIVAS K N",
        "father_mobile_one": "9986255558",
        "mother_mobile_one": "9986255558",
        "guardian_mobile_no": "9986255558",
        "email": "Seene2007@yahoo.co.in",
        "father_email": "seene2007@yahoo.co.in",
        "mother_email": "manasa6899@gmail.com",
        "guardian_email": "seene2007@yahoo.co.in",
        "present_address": "NO4,SRILAKSHMI VENKATESHWARA NILAYA,NEAR BHUPATHI TENNIS COURT,VIRUPAKSHAPURA,VIDYARANYAPURA POST,BENGALURU 560097",
        "permanent_address": "",
        "blood_group": "O+",
        "gender": "MALE",
        "religion_name": "Hindu",
        "nationality_name": "Indian",
        "caste": "Gowda",
        "category_name": "2A",
        "application_no": "APP2024089",
        "admission_no": "226/2024",
        "term_name": "Class 8",
        "section_name": "E",
        "house_color": "St Patrick (Green)",
        "name": "Mrs. Preetha V",
        "aadhar_no": "",
        "father_aadhar": "473302550687",
        "mother_aadhar": "821905803376",
        "father_profession": "Self employed",
        "mother_profession": "House wife",
        "mother_tongue": "Kannada",
        "apaar_id": "9823-4567-1234",
        "sat_number": "SAT-890123",
        "student_pen_no": "PEN-2022-7712",
        "sts_no": "STS-994120",
        "language_two": "Kannada",
        "language_three": "Hindi",
        "photo_url": "uploads/student_photos/st123.jpg",
        "file_path_jpg": "staff/upload/student_image/SJ24E10003.jpg",
        "note": "Active participant in school debate and swimming team."
    },
    "sags_school:student:profile": {
        "row_id": "ST123",
        "student_id": "ST123",
        "student_name": "RIYANSH K SRINIVAS",
        "dob": "2019-06-06",
        "father_name": "SRINIVAS K N",
        "mother_name": "MANASA N",
        "guardian_name": "SRINIVAS K N",
        "father_mobile_one": "9986255558",
        "mother_mobile_one": "9986255558",
        "guardian_mobile_no": "9986255558",
        "email": "Seene2007@yahoo.co.in",
        "father_email": "seene2007@yahoo.co.in",
        "mother_email": "manasa6899@gmail.com",
        "guardian_email": "seene2007@yahoo.co.in",
        "present_address": "NO4,SRILAKSHMI VENKATESHWARA NILAYA,NEAR BHUPATHI TENNIS COURT,VIRUPAKSHAPURA,VIDYARANYAPURA POST,BENGALURU 560097",
        "permanent_address": "",
        "blood_group": "O+",
        "gender": "MALE",
        "religion_name": "Hindu",
        "nationality_name": "Indian",
        "caste": "Gowda",
        "category_name": "2A",
        "application_no": "APP2024089",
        "admission_no": "226/2024",
        "term_name": "Class 8",
        "section_name": "E",
        "house_color": "Green House",
        "name": "Mrs. Preetha V",
        "aadhar_no": "",
        "father_aadhar": "473302550687",
        "mother_aadhar": "821905803376",
        "father_profession": "Self employed",
        "mother_profession": "House wife",
        "mother_tongue": "Kannada",
        "apaar_id": "9823-4567-1234",
        "sat_number": "SAT-890123",
        "student_pen_no": "PEN-2022-7712",
        "sts_no": "STS-994120",
        "language_two": "Kannada",
        "language_three": "Hindi",
        "photo_url": "uploads/student_photos/st123.jpg",
        "file_path_jpg": "staff/upload/student_image/SJ24E10003.jpg",
        "note": "Active participant in school debate."
    },

    # Study Materials Datasets
    "sjbhs:student:study_materials": [
        {
            "subject_name": "Kannada Recitation",
            "type": "Portions",
            "description": "Dear parents \r\nRhyme lyrics is sent. Make use of it in order to teach proper pronunciation to your ward. \r\nThank you \r\n",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a8d6b6bc5a107.62161483Rhyme_2.docx",
            "created_date_time": "2026-08-25 15:46:12",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Portions",
            "description": "Dear parents Kindly go through the file sent for the reference of the notes.\r\nThe should complete the pending work and submit the notebook for correction by Thursday.\r\nThank you \r\n",
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
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a85b15178dd24.25091492Screenshot_20260819-190417_Camera.png",
            "created_date_time": "2026-08-19 19:06:44",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Portions",
            "description": "Dear parents kindly check the attached file for reference ",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a85b151775587.63520623Screenshot_20260819-190421_Camera.png",
            "created_date_time": "2026-08-19 19:06:27",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "FIRST UNIT ASSESSMENT - PAPERS GIVEN.\r\nKannada answer scripts have been corrected and distributed today.\r\nParents are requested to kindly sign the answer scripts and return them by tomorrow without fail.",
            "document_name_url": "",
            "created_date_time": "2026-08-05 16:13:10",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "Dear parents it's a reminder that kannada dictation test will be conducted on Thursday.(16-07-26)\r\nThank you ",
            "document_name_url": "",
            "created_date_time": "2026-07-14 15:40:04",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Mental Math",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3ab1eb5.54479185Std_1_Mental_Math_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:11",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Environmental Science",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3aad240.60574260Std_1_EVS_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:10",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Literature",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3aaa083.53504190Std_1_English_Literature_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:09",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Language",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3aa31e9.66054370Std_1_English_Language_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:09",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Mathematics",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3a989b3.02889990Std_1_Arithmetic_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:07",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Language",
            "type": "Others ",
            "description": "Name List, kindly list the Roll number.",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a4e1adfd9b912.79460963IMG_20260708_144759.jpg",
            "created_date_time": "2026-07-08 15:09:43",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "Dear parents \r\nThe recitation is conducted. Some boys have not finished for them it will be conducted tomorrow. \r\nReading: (The 15 words )will be conducted tomorrow \r\n",
            "document_name_url": "",
            "created_date_time": "2026-07-06 15:44:48",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Hindi",
            "type": "Worksheets",
            "description": "Dear Parents, Kindly send the photocopy of the attached worksheets. Thank you ",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a4798a4d92fc6.770470931STD_1FA_REVISION_WORKSHEET_2026-27.pdf",
            "created_date_time": "2026-07-03 16:40:30",
            "name": "Ms M Sujatha"
        },
        {
            "subject_name": "English Language",
            "type": "Exam Time Table",
            "description": "Time Table ",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a47715a1acdc4.58090639IMG-20260703-WA0007(1).jpg",
            "created_date_time": "2026-07-03 13:52:50",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Language",
            "type": "Exam Time Table",
            "description": "Dear Parents \r\nSending the Time Table for First term Assessment.",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a477051763351.22762246Std_1_-_First_Unit_Assessment_Portions_2026-1.pdf",
            "created_date_time": "2026-07-03 13:48:25",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "Good evening parents \r\nKindly go through the link given below.\r\nYour ward should learn the Rhymes for kannada recitation.\r\nhttps://youtu.be/WDhXzrVW0QY?feature=shared\r\n",
            "document_name_url": "",
            "created_date_time": "2026-07-02 19:00:06",
            "name": "Ms Meena Saver Rodriks"
        }
    ],
    "sags_school:student:study_materials": [
        {
            "subject_name": "Kannada Recitation",
            "type": "Portions",
            "description": "Dear parents \r\nRhyme lyrics is sent. Make use of it in order to teach proper pronunciation to your ward. \r\nThank you \r\n",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a8d6b6bc5a107.62161483Rhyme_2.docx",
            "created_date_time": "2026-08-25 15:46:12",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Portions",
            "description": "Dear parents Kindly go through the file sent for the reference of the notes.\r\nThe should complete the pending work and submit the notebook for correction by Thursday.\r\nThank you \r\n",
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
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a85b15178dd24.25091492Screenshot_20260819-190417_Camera.png",
            "created_date_time": "2026-08-19 19:06:44",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Portions",
            "description": "Dear parents kindly check the attached file for reference ",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a85b151775587.63520623Screenshot_20260819-190421_Camera.png",
            "created_date_time": "2026-08-19 19:06:27",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "FIRST UNIT ASSESSMENT - PAPERS GIVEN.\r\nKannada answer scripts have been corrected and distributed today.\r\nParents are requested to kindly sign the answer scripts and return them by tomorrow without fail.",
            "document_name_url": "",
            "created_date_time": "2026-08-05 16:13:10",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "Dear parents it's a reminder that kannada dictation test will be conducted on Thursday.(16-07-26)\r\nThank you ",
            "document_name_url": "",
            "created_date_time": "2026-07-14 15:40:04",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Mental Math",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3ab1eb5.54479185Std_1_Mental_Math_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:11",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Environmental Science",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3aad240.60574260Std_1_EVS_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:10",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Literature",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3aaa083.53504190Std_1_English_Literature_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:09",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Language",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3aa31e9.66054370Std_1_English_Language_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:09",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Mathematics",
            "type": "Worksheets",
            "description": "",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a51e2b3a989b3.02889990Std_1_Arithmetic_Revision_Worksheet_2026_1st_UA.pdf",
            "created_date_time": "2026-07-11 11:59:07",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Language",
            "type": "Others ",
            "description": "Name List, kindly list the Roll number.",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a4e1adfd9b912.79460963IMG_20260708_144759.jpg",
            "created_date_time": "2026-07-08 15:09:43",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "Dear parents \r\nThe recitation is conducted. Some boys have not finished for them it will be conducted tomorrow. \r\nReading: (The 15 words )will be conducted tomorrow \r\n",
            "document_name_url": "",
            "created_date_time": "2026-07-06 15:44:48",
            "name": "Ms Meena Saver Rodriks"
        },
        {
            "subject_name": "Hindi",
            "type": "Worksheets",
            "description": "Dear Parents, Kindly send the photocopy of the attached worksheets. Thank you ",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a4798a4d92fc6.770470931STD_1FA_REVISION_WORKSHEET_2026-27.pdf",
            "created_date_time": "2026-07-03 16:40:30",
            "name": "Ms M Sujatha"
        },
        {
            "subject_name": "English Language",
            "type": "Exam Time Table",
            "description": "Time Table ",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a47715a1acdc4.58090639IMG-20260703-WA0007(1).jpg",
            "created_date_time": "2026-07-03 13:52:50",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "English Language",
            "type": "Exam Time Table",
            "description": "Dear Parents \r\nSending the Time Table for First term Assessment.",
            "document_name_url": "staff/upload/study_materials/SJBHS-6a477051763351.22762246Std_1_-_First_Unit_Assessment_Portions_2026-1.pdf",
            "created_date_time": "2026-07-03 13:48:25",
            "name": "Ms Rebecca P"
        },
        {
            "subject_name": "Kannada",
            "type": "Others ",
            "description": "Good evening parents \r\nKindly go through the link given below.\r\nYour ward should learn the Rhymes for kannada recitation.\r\nhttps://youtu.be/WDhXzrVW0QY?feature=shared\r\n",
            "document_name_url": "",
            "created_date_time": "2026-07-02 19:00:06",
            "name": "Ms Meena Saver Rodriks"
        }
    ]
}


class MockERPProvider:
    """
    Simulates ERP API responses for local testing when live ERP endpoints are unavailable.
    """

    @staticmethod
    def get_mock_data(institution_id: str, role: str, module: str) -> Optional[Any]:
        # Normalize institution IDs (e.g. sjbhs_student -> sjbhs)
        inst_key = "sjbhs" if "sjbhs" in institution_id.lower() else institution_id.lower()
        if module.lower() in ("calendar", "holiday"):
            mod_key = "calendar"
        elif module.lower() in ("notice", "notification"):
            mod_key = "notification"
        else:
            mod_key = module.lower()

        key = f"{inst_key}:{role.lower()}:{mod_key}"
        res = MOCK_ERP_DATA.get(key)
        if not res and module.lower() in ("holiday", "notice"):
            res = MOCK_ERP_DATA.get(f"{inst_key}:{role.lower()}:{module.lower()}")
        return res

