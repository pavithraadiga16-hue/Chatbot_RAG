"""
PhinsIQ MongoDB Seed Script — Institutions, Modules, Fields, API Registry, Templates
=====================================================================================

PURPOSE:
    Populates MongoDB with complete configurations for:
    - SJBHS (`sjbhs` and `sjbhs_student`)
    - SAGS School (`sags_school`)

HOW TO RUN:
    cd /Users/parrophins/Desktop/PhinsIQ
    ./venv/bin/python scripts/seed_sjbhs.py
"""

import asyncio
import certifi
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings


# =============================================================================
# Institutions
# =============================================================================

INSTITUTIONS = [
    {
        "_id": "sjbhs",
        "name": "St. Joseph's Boys' High School (SJBHS)",
        "short_name": "SJBHS",
        "status": "active",
        "api_config": {
            "base_url": "https://demo.parrophins.in/sjbhs",
            "auth_type": "none",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        },
        "module_routes": {
            "profile": "/profile",
            "fees": "/fees",
            "attendance": "/attendance",
            "homework": "/homework",
            "study_materials": "/study-materials",
            "notification": "/notifications",
            "calendar": "/calendar",
            "academic_overview": "/dashboard",
            "exam": "/exams",
        },
        "roles": ["student", "staff"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "_id": "sjbhs_student",
        "name": "St. Joseph's Boys' High School (Student Portal)",
        "short_name": "SJBHS Student",
        "status": "active",
        "api_config": {
            "base_url": "https://demo.parrophins.in/sjbhs",
            "auth_type": "none",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        },
        "module_routes": {
            "profile": "/profile",
            "fees": "/fees",
            "attendance": "/attendance",
            "homework": "/homework",
            "study_materials": "/study-materials",
            "notification": "/notifications",
            "calendar": "/calendar",
            "academic_overview": "/dashboard",
            "exam": "/exams",
        },
        "roles": ["student"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "_id": "sags_school",
        "name": "SAGS School",
        "short_name": "SAGS",
        "status": "active",
        "api_config": {
            "base_url": "https://erp.sags.example.com",
            "auth_type": "bearer",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        },
        "module_routes": {
            "profile": "/profile",
            "fees": "/fees",
            "attendance": "/attendance",
            "homework": "/homework",
            "study_materials": "/study-materials",
            "notification": "/notifications",
            "calendar": "/calendar",
            "academic_overview": "/dashboard",
            "exam": "/exams",
        },
        "roles": ["student", "staff"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
]

# =============================================================================
# Roles
# =============================================================================

ROLES = [
    {
        "_id": "student",
        "name": "Student",
        "modules": ["fees", "attendance", "exam", "calendar", "holiday", "homework", "notification", "notice", "profile", "study_materials", "timetable", "library"],
        "description": "Student role — read-only access to academic data",
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "_id": "staff",
        "name": "Staff",
        "modules": ["attendance", "leave", "payroll", "calendar", "timetable", "notice", "notification", "profile", "study_materials"],
        "description": "Staff role — access to personal employment and academic data",
        "updated_at": datetime.now(timezone.utc),
    }
]

# =============================================================================
# Modules & Actions
# =============================================================================

MODULES = [
    {"_id": "fees",            "name": "Fees",              "status": "active", "description": "Fee payment and balance information"},
    {"_id": "attendance",      "name": "Attendance",        "status": "active", "description": "Class attendance records"},
    {"_id": "exam",            "name": "Exam",              "status": "active", "description": "Examination schedules and results"},
    {"_id": "calendar",        "name": "Academic Calendar", "status": "active", "description": "Academic calendar, holidays, assessments, fests, and school events"},
    {"_id": "holiday",         "name": "Holiday",           "status": "active", "description": "Academic calendar and holidays"},
    {"_id": "homework",        "name": "Homework",          "status": "active", "description": "Student homework, assignments, and submission deadlines"},
    {"_id": "notification",    "name": "Notification",      "status": "active", "description": "School notices, circulars, and announcements"},
    {"_id": "notice",          "name": "Notice Board",      "status": "active", "description": "School notices, circulars, and announcements"},
    {"_id": "profile",         "name": "Student Profile",   "status": "active", "description": "Personal profile, parent details, academic IDs, and contact information"},
    {"_id": "study_materials", "name": "Study Materials",   "status": "active", "description": "Subject study materials, portions, worksheets, and teacher notes"},
    {"_id": "timetable",       "name": "Timetable",         "status": "active", "description": "Class timetable"},
    {"_id": "library",         "name": "Library",           "status": "active", "description": "Library books and due dates"},
    {"_id": "leave",           "name": "Leave",             "status": "active", "description": "Staff leave management"},
    {"_id": "payroll",         "name": "Payroll",           "status": "active", "description": "Staff salary and payroll"},
]

ACTIONS = [
    {
        "_id": "fees_summary",
        "module": "fees",
        "action": "summary",
        "description": "Fetch fee payment details (total, paid, pending, installment, concession)",
    },
    {
        "_id": "attendance_percentage",
        "module": "attendance",
        "action": "percentage",
        "description": "Get current attendance percentage",
    },
]

# =============================================================================
# Fields
# =============================================================================

FIELDS = [
    {
        "module": "fees",
        "fields": [
            {
                "name": "pending_amount",
                "label": "Pending Fee",
                "erp_key": "pending_amount",
                "format": "currency",
                "aliases": [
                    "pending", "pending fee", "pending amount", "remaining fee",
                    "remaining amount", "due", "due amount", "balance",
                    "outstanding", "how much to pay", "unpaid", "left to pay",
                    "what do i owe", "amount due", "fee balance", "dues",
                ]
            },
            {
                "name": "total_fee",
                "label": "Total Fee",
                "erp_key": "total_fee_amount",
                "format": "currency",
                "aliases": [
                    "total", "total fee", "total amount", "fee amount",
                    "how much is my fee", "overall fee", "full fee",
                    "complete fee", "entire fee", "whole fee",
                ]
            },
            {
                "name": "paid_amount",
                "label": "Paid Amount",
                "erp_key": "paid_amount",
                "format": "currency",
                "aliases": [
                    "paid", "paid amount", "amount paid", "already paid",
                    "payment done", "paid fee", "how much i paid",
                    "what i have paid", "fee paid",
                ]
            },
            {
                "name": "installment_amount",
                "label": "Installment Amount",
                "erp_key": "instalment_amt",
                "format": "currency",
                "aliases": [
                    "installment", "instalment", "installment amount",
                    "instalment amount", "emi", "monthly payment", "installment fee"
                ]
            },
            {
                "name": "first_installment",
                "label": "First Installment",
                "erp_key": "first_installmet",
                "format": "currency",
                "aliases": [
                    "first installment", "1st installment", "first instalment",
                    "first emi", "first payment"
                ]
            },
            {
                "name": "second_installment",
                "label": "Second Installment",
                "erp_key": "second_installmet",
                "format": "currency",
                "aliases": [
                    "second installment", "2nd installment", "second instalment",
                    "second emi", "second payment"
                ]
            },
            {
                "name": "concession",
                "label": "Fee Concession",
                "erp_key": "concession",
                "format": "currency",
                "aliases": [
                    "concession", "discount", "fee discount", "waiver",
                    "scholarship discount", "fee waiver", "fee reduction"
                ]
            },
            {
                "name": "installment_status",
                "label": "Installment Status",
                "erp_key": "instalment_status",
                "format": "boolean",
                "aliases": [
                    "installment status", "instalment status", "payment plan",
                    "is installment", "installment enabled"
                ]
            },
            {
                "name": "exam_total_fee",
                "label": "Total Exam Fee",
                "erp_key": "exam_total_fee",
                "format": "currency",
                "aliases": ["exam fee", "exam total fee", "exam total", "total exam fee"]
            },
            {
                "name": "exam_pending_amount",
                "label": "Exam Pending Fee",
                "erp_key": "exam_pending_amt",
                "format": "currency",
                "aliases": ["exam pending", "exam fee pending", "exam due", "exam balance", "pending exam fee"]
            },
            {
                "name": "exam_paid_fee",
                "label": "Exam Paid Fee",
                "erp_key": "exam_paid_fee",
                "format": "currency",
                "aliases": ["exam paid", "exam fee paid", "paid exam fee"]
            },
            {
                "name": "min_amount",
                "label": "Minimum Payment Amount",
                "erp_key": "min_amount",
                "format": "currency",
                "aliases": ["minimum amount", "min amount", "minimum payment", "minimum fee"]
            },
        ]
    },
    {
        "module": "attendance",
        "fields": [
            # ---------------------------------------------------------------
            # Scalar computed fields (from aggregation on attendance_data array)
            # ---------------------------------------------------------------
            {
                "name": "absent_count",
                "label": "Total Absences",
                "format": "text",
                "aliases": [
                    "absent", "absences", "absent count", "how many absent",
                    "total absent", "number of absences", "how many absences",
                    "absent days", "days absent", "how many days absent",
                    "absent total", "my absences", "missed classes", "missed days",
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "count_where",
                    "filter_key": "status",
                    "filter_value": "absent"
                }
            },
            {
                "name": "present_count",
                "label": "Days Present",
                "format": "text",
                "aliases": [
                    "present", "my present", "present count", "how many present",
                    "present days", "days present", "total present",
                    "number of present days", "how many i attended",
                    "attended days", "attended", "classes attended",
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "count_where",
                    "filter_key": "status",
                    "filter_value": "present"
                }
            },
            {
                "name": "total_classes",
                "label": "Total Classes",
                "format": "text",
                "aliases": [
                    "total classes", "total days", "school days", "total school days",
                    "how many classes", "how many days school", "total working days"
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "count"
                }
            },
            {
                "name": "attendance_percentage",
                "label": "Attendance Percentage",
                "format": "percentage",
                "aliases": [
                    "percentage", "attendance percent", "attendance percentage",
                    "how much attendance", "attendance rate", "percent",
                    "attendance score", "what is my attendance"
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "percentage",
                    "filter_key": "status",
                    "filter_value": "present",
                    "decimal_places": 1
                }
            },
            # ---------------------------------------------------------------
            # List fields — return arrays of dates
            # ---------------------------------------------------------------
            {
                "name": "absent_dates",
                "label": "Absent Dates",
                "format": "date_list",
                "aliases": [
                    "absent dates", "when was i absent", "which days absent",
                    "dates i was absent", "absent day list", "show absent dates",
                    "list absent dates", "when absent", "which dates absent"
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "filter_dates",
                    "filter_key": "status",
                    "filter_value": "absent",
                    "date_key": "date"
                }
            },
            {
                "name": "present_dates",
                "label": "Present Dates",
                "format": "date_list",
                "aliases": [
                    "present dates", "when was i present", "which days present",
                    "dates i was present", "present day list", "show present dates",
                    "list present dates", "days i attended"
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "filter_dates",
                    "filter_key": "status",
                    "filter_value": "present",
                    "date_key": "date"
                }
            },
            # ---------------------------------------------------------------
            # Scalar date fields — single date result
            # ---------------------------------------------------------------
            {
                "name": "last_present_date",
                "label": "Last Present Date",
                "format": "text",
                "aliases": [
                    "last present", "last attended", "when was i last present",
                    "latest present date", "last school day", "last day present"
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "max_date",
                    "filter_key": "status",
                    "filter_value": "present",
                    "date_key": "date"
                }
            },
            {
                "name": "first_absent_date",
                "label": "First Absent Date",
                "format": "text",
                "aliases": [
                    "first absent", "first absence", "when was i first absent",
                    "earliest absent date", "first miss"
                ],
                "aggregation": {
                    "source_field": "attendance_data",
                    "operation": "min_date",
                    "filter_key": "status",
                    "filter_value": "absent",
                    "date_key": "date"
                }
            },
            # ---------------------------------------------------------------
            # Scalar metadata fields (from response_mapping, not aggregation)
            # ---------------------------------------------------------------
            {
                "name": "start_date",
                "label": "Start Date",
                "format": "text",
                "aliases": ["start date", "from date", "attendance start", "period start"]
            },
            {
                "name": "end_date",
                "label": "End Date",
                "format": "text",
                "aliases": ["end date", "to date", "attendance end", "period end", "till date"]
            },
        ]
    },
    {
        "module": "calendar",
        "fields": [
            {
                "name": "event_search",
                "label": "Dynamic Event Search",
                "format": "text",
                "aliases": [
                    "when is", "date of", "when will", "timing of", "schedule of", "when does",
                    "event date", "when starts", "when commences"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "dynamic_event_search",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "holiday_list",
                "label": "Holiday List",
                "format": "list",
                "aliases": [
                    "holiday", "holidays", "holiday list", "holidays list", "when are the holidays",
                    "upcoming holidays", "school holidays", "list holidays", "which days are holiday",
                    "when and all i have holidays", "when do we have holidays", "holiday dates",
                    "when are holidays", "holiday schedule"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "(Holiday)",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "holiday_count",
                "label": "Total Holidays",
                "format": "text",
                "aliases": [
                    "how many holidays", "total holidays", "count of holidays", "holiday count",
                    "number of holidays", "total holiday count", "how many vacation days",
                    "number of holidays this year"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count_where_contains",
                    "search_key": "title",
                    "contains_value": "(Holiday)"
                }
            },
            {
                "name": "school_reopening",
                "label": "School Reopening Dates",
                "format": "list",
                "aliases": [
                    "when school reopens", "school reopen", "reopening date", "school reopen date",
                    "reopen", "reopening", "when will school start", "school start date",
                    "when is school reopening", "school reopens", "reopening schedule"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "reopen",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "vacation_list",
                "label": "Vacation Dates",
                "format": "list",
                "aliases": [
                    "vacation", "vacations", "vacation dates", "dasara vacation", "christmas vacation",
                    "when is vacation", "school vacation", "vacation schedule"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "vacation",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "ptm_dates",
                "label": "PTM Dates",
                "format": "list",
                "aliases": [
                    "ptm", "ptm dates", "parent teacher meeting", "when is ptm", "ptm schedule",
                    "parents meeting"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "ptm",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "all_events",
                "label": "Academic Calendar Events",
                "format": "list",
                "aliases": [
                    "calendar", "calender", "events", "academic calendar", "all events", "event list",
                    "schedule of events", "school events", "school calendar", "annual calendar"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            }
        ]
    },
    {
        "module": "holiday",
        "fields": [
            {
                "name": "event_search",
                "label": "Dynamic Event Search",
                "format": "text",
                "aliases": [
                    "when is", "date of", "when will", "timing of", "schedule of", "when does"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "dynamic_event_search",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "holiday_list",
                "label": "Holiday List",
                "format": "list",
                "aliases": [
                    "holiday", "holidays", "holiday list", "holidays list", "when are the holidays",
                    "upcoming holidays", "school holidays", "list holidays", "which days are holiday",
                    "when and all i have holidays", "when do we have holidays", "holiday dates",
                    "when are holidays", "holiday schedule"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "(Holiday)",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "holiday_count",
                "label": "Total Holidays",
                "format": "text",
                "aliases": [
                    "how many holidays", "total holidays", "count of holidays", "holiday count",
                    "number of holidays", "total holiday count", "how many vacation days",
                    "number of holidays this year"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count_where_contains",
                    "search_key": "title",
                    "contains_value": "(Holiday)"
                }
            },
            {
                "name": "school_reopening",
                "label": "School Reopening Dates",
                "format": "list",
                "aliases": [
                    "when school reopens", "school reopen", "reopening date", "school reopen date",
                    "reopen", "reopening", "when will school start", "school start date",
                    "when is school reopening", "school reopens", "reopening schedule"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "reopen",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            },
            {
                "name": "all_events",
                "label": "Academic Calendar Events",
                "format": "list",
                "aliases": [
                    "calendar", "calender", "events", "academic calendar", "all events", "event list",
                    "schedule of events", "school events", "school calendar", "annual calendar"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_events_contains",
                    "search_key": "title",
                    "contains_value": "",
                    "title_key": "title",
                    "start_key": "start",
                    "end_key": "end"
                }
            }
        ]
    },
    {
        "module": "homework",
        "fields": [
            {
                "name": "homework_search",
                "label": "Dynamic Homework Search & Deadlines",
                "format": "text",
                "aliases": [
                    "when is submission date", "submission date", "submit date", "due date", "deadline",
                    "when to submit", "math homework", "maths homework", "science homework", "english homework",
                    "social homework", "physics homework", "chemistry homework", "biology homework",
                    "computer homework", "hindi homework", "kannada homework", "homework due", "assignment due",
                    "when is homework due", "when is homework submission"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "dynamic_homework_search",
                    "subject_key": "subject",
                    "desc_key": "homework_discription",
                    "due_key": "submission_date",
                    "teacher_key": "sent_by",
                    "status_key": "status"
                }
            },
            {
                "name": "pending_homework",
                "label": "Pending Homework List",
                "format": "list",
                "aliases": [
                    "pending homework", "homework pending", "what homework is pending", "homework left",
                    "incomplete homework", "homework to do", "homework not completed", "uncompleted homework",
                    "pending assignments", "assignments to submit", "which homework pending"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_homework_list",
                    "filter_key": "status",
                    "filter_value": "completed,1,submitted",
                    "filter_mode": "not_equals",
                    "subject_key": "subject",
                    "desc_key": "homework_discription",
                    "due_key": "submission_date",
                    "teacher_key": "sent_by",
                    "status_key": "status"
                }
            },
            {
                "name": "pending_count",
                "label": "Pending Homework Count",
                "format": "text",
                "aliases": [
                    "how much homework pending", "pending homework count", "how many pending homework",
                    "number of pending homework", "count of pending assignments", "how many homework left",
                    "how many homework to do"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count_where_not",
                    "filter_key": "status",
                    "filter_value": "completed,1,submitted"
                }
            },
            {
                "name": "completed_homework",
                "label": "Completed Homework List",
                "format": "list",
                "aliases": [
                    "completed homework", "homework completed", "finished homework", "submitted homework",
                    "done homework", "completed assignments", "submitted assignments"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_homework_list",
                    "filter_key": "status",
                    "filter_value": "completed,1,submitted",
                    "filter_mode": "equals",
                    "subject_key": "subject",
                    "desc_key": "homework_discription",
                    "due_key": "submission_date",
                    "teacher_key": "sent_by",
                    "status_key": "status"
                }
            },
            {
                "name": "completed_count",
                "label": "Completed Homework Count",
                "format": "text",
                "aliases": [
                    "completed count", "how many homework completed", "number of completed homework",
                    "count of completed homework", "how many assignments done"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count_where",
                    "filter_key": "status",
                    "filter_value": "completed"
                }
            },
            {
                "name": "total_homework",
                "label": "Total Homework Count",
                "format": "text",
                "aliases": [
                    "how much homework", "total homework", "count of homework", "homework count",
                    "number of homeworks", "how many assignments", "total assignments", "total homework count"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count"
                }
            },
            {
                "name": "all_homework",
                "label": "All Assigned Homework",
                "format": "list",
                "aliases": [
                    "homework", "homeworks", "all homework", "homework list", "my homework",
                    "assignments", "all assignments", "show homework", "give homework",
                    "what is my homework", "show all homework", "list all homework"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_homework_list",
                    "filter_mode": "all",
                    "subject_key": "subject",
                    "desc_key": "homework_discription",
                    "due_key": "submission_date",
                    "teacher_key": "sent_by",
                    "status_key": "status"
                }
            }
        ]
    },
    {
        "module": "notification",
        "fields": [
            {
                "name": "total_notifications",
                "label": "Total Notifications Count",
                "format": "number",
                "aliases": [
                    "how many notifications", "total notifications", "notification count",
                    "number of notifications", "how many circulars", "total circulars",
                    "how many notices", "total notices", "count of notifications", "count of notices"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count"
                }
            },
            {
                "name": "recent_notifications",
                "label": "Recent Notifications",
                "format": "list",
                "aliases": [
                    "recent notification", "recent notifications", "latest notification", "latest notifications",
                    "latest circular", "latest circulars", "recent circular", "recent circulars",
                    "latest notice", "latest notices", "recent notice", "recent notices",
                    "new notifications", "new circulars", "what is the recent notification",
                    "latest announcement", "latest announcements", "recent announcement", "recent announcements"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_recent_notifications",
                    "limit": 3,
                    "title_key": "subject",
                    "desc_key": "message",
                    "date_key": "date_time",
                    "sender_key": "sent_by",
                    "type_key": "type"
                }
            },
            {
                "name": "notification_search",
                "label": "Dynamic Notification Search",
                "format": "text",
                "aliases": [
                    "notification on", "notice on", "circular on", "announcement on",
                    "any notification", "any notice", "any circular", "notification about",
                    "notice about", "circular about", "announcement about",
                    "principal notification", "admin notification", "sports notification",
                    "exam notification", "fee notification", "holiday notification"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "dynamic_notification_search",
                    "title_key": "subject",
                    "desc_key": "message",
                    "date_key": "date_time",
                    "sender_key": "sent_by",
                    "type_key": "type"
                }
            },
            {
                "name": "all_notifications",
                "label": "All Notifications & Circulars",
                "format": "list",
                "aliases": [
                    "notifications", "notices", "all notifications", "all notices",
                    "show notifications", "show notices", "show circulars", "list notifications",
                    "list notices", "my notifications", "circulars", "all circulars",
                    "announcements", "all announcements", "notice board"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_notifications_list",
                    "title_key": "subject",
                    "desc_key": "message",
                    "date_key": "date_time",
                    "sender_key": "sent_by",
                    "type_key": "type"
                }
            }
        ]
    },
    {
        "module": "notice",
        "fields": [
            {
                "name": "total_notifications",
                "label": "Total Notices Count",
                "format": "number",
                "aliases": [
                    "how many notices", "total notices", "notice count", "number of notices",
                    "how many circulars", "total circulars", "how many notifications"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count"
                }
            },
            {
                "name": "recent_notifications",
                "label": "Recent Notices",
                "format": "list",
                "aliases": [
                    "recent notice", "recent notices", "latest notice", "latest notices",
                    "latest circular", "recent circular", "new notices", "recent notification"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_recent_notifications",
                    "limit": 3,
                    "title_key": "subject",
                    "desc_key": "message",
                    "date_key": "date_time",
                    "sender_key": "sent_by",
                    "type_key": "type"
                }
            },
            {
                "name": "notification_search",
                "label": "Dynamic Notice Search",
                "format": "text",
                "aliases": [
                    "notice on", "notice about", "circular on", "circular about", "any notice"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "dynamic_notification_search",
                    "title_key": "subject",
                    "desc_key": "message",
                    "date_key": "date_time",
                    "sender_key": "sent_by",
                    "type_key": "type"
                }
            },
            {
                "name": "all_notifications",
                "label": "All Notices",
                "format": "list",
                "aliases": [
                    "notices", "all notices", "notice board", "show notices", "list notices"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_notifications_list",
                    "title_key": "subject",
                    "desc_key": "message",
                    "date_key": "date_time",
                    "sender_key": "sent_by",
                    "type_key": "type"
                }
            }
        ]
    },
    {
        "module": "profile",
        "fields": [
            {
                "name": "student_name",
                "label": "Student Name",
                "format": "text",
                "aliases": ["what is my name", "my name", "tell my name", "who am i", "student name", "name", "full name", "my full name", "tell me my name"]
            },
            {
                "name": "dob",
                "label": "Date of Birth",
                "format": "date",
                "aliases": ["dob", "date of birth", "birthday", "when is my birthday", "my date of birth", "my dob", "birth date", "birthdate"]
            },
            {
                "name": "father_name",
                "label": "Father's Name",
                "format": "text",
                "aliases": ["father name", "father's name", "my father name", "my father's name", "what is my father's name", "tell my father name", "father"]
            },
            {
                "name": "mother_name",
                "label": "Mother's Name",
                "format": "text",
                "aliases": ["mother name", "mother's name", "my mother name", "my mother's name", "what is my mother's name", "tell my mother name", "mother"]
            },
            {
                "name": "guardian_name",
                "label": "Guardian's Name",
                "format": "text",
                "aliases": ["guardian name", "guardian's name", "who is my guardian", "my guardian", "guardian"]
            },
            {
                "name": "mobile",
                "label": "Registered Mobile Number",
                "format": "text",
                "aliases": ["registered mobile", "registered phone", "contact number", "mobile number", "my mobile number", "my phone number", "phone", "phone number"]
            },
            {
                "name": "father_mobile",
                "label": "Father's Mobile Number",
                "format": "text",
                "aliases": ["father mobile", "father's mobile", "father contact", "father phone", "father's phone"]
            },
            {
                "name": "mother_mobile",
                "label": "Mother's Mobile Number",
                "format": "text",
                "aliases": ["mother mobile", "mother's mobile", "mother contact", "mother phone", "mother's phone"]
            },
            {
                "name": "email",
                "label": "Registered Email Address",
                "format": "text",
                "aliases": ["email", "registered email", "my email", "email address", "my email address", "student email"]
            },
            {
                "name": "address",
                "label": "Residential Address",
                "format": "text",
                "aliases": ["address", "my address", "residential address", "present address", "current address", "where do i live", "home address"]
            },
            {
                "name": "permanent_address",
                "label": "Permanent Address",
                "format": "text",
                "aliases": ["permanent address", "my permanent address"]
            },
            {
                "name": "blood_group",
                "label": "Blood Group",
                "format": "text",
                "aliases": ["blood group", "blood type", "my blood group", "what is my blood group", "blood"]
            },
            {
                "name": "gender",
                "label": "Gender",
                "format": "text",
                "aliases": ["gender", "my gender", "sex"]
            },
            {
                "name": "class_name",
                "label": "Class / Standard",
                "format": "text",
                "aliases": ["class", "grade", "my class", "which class", "which grade", "which standard", "standard", "current class", "my grade"]
            },
            {
                "name": "section",
                "label": "Section",
                "format": "text",
                "aliases": ["section", "my section", "which section", "section name", "current section"]
            },
            {
                "name": "class_teacher",
                "label": "Class Teacher",
                "format": "text",
                "aliases": ["class teacher", "my class teacher", "who is my class teacher", "class teacher name", "teacher name"]
            },
            {
                "name": "house_color",
                "label": "House / House Color",
                "format": "text",
                "aliases": ["house", "my house", "house color", "house name", "which house", "what is my house", "school house"]
            },
            {
                "name": "admission_no",
                "label": "Admission Number",
                "format": "text",
                "aliases": ["admission number", "admission no", "my admission number", "my admission no", "admission", "admission code"]
            },
            {
                "name": "application_no",
                "label": "Application Number",
                "format": "text",
                "aliases": ["application number", "application no", "my application number", "application code"]
            },
            {
                "name": "student_id",
                "label": "Student ID / Roll Number",
                "format": "text",
                "aliases": ["student id", "my student id", "roll number", "roll no", "my roll number", "student roll number"]
            },
            {
                "name": "aadhar_no",
                "label": "Aadhaar Card Number",
                "format": "text",
                "aliases": ["aadhaar", "aadhar", "aadhaar number", "aadhar number", "my aadhar number", "my aadhaar number", "aadhaar card", "aadhar card"]
            },
            {
                "name": "apaar_id",
                "label": "APAAR ID",
                "format": "text",
                "aliases": ["apaar", "apaar id", "my apaar id", "apaar number", "apaar card", "apaar code"]
            },
            {
                "name": "pen_no",
                "label": "Student PEN Number",
                "format": "text",
                "aliases": ["pen number", "pen no", "my pen number", "student pen number", "permanent education number", "pen"]
            },
            {
                "name": "sts_no",
                "label": "STS Number",
                "format": "text",
                "aliases": ["sts number", "sts no", "my sts number", "student tracking system", "sts"]
            },
            {
                "name": "sat_no",
                "label": "SAT Number",
                "format": "text",
                "aliases": ["sat number", "sat no", "my sat number", "sat"]
            },
            {
                "name": "second_language",
                "label": "Second Language",
                "format": "text",
                "aliases": ["second language", "2nd language", "my second language", "language two"]
            },
            {
                "name": "third_language",
                "label": "Third Language",
                "format": "text",
                "aliases": ["third language", "3rd language", "my third language", "language three"]
            },
            {
                "name": "religion",
                "label": "Religion",
                "format": "text",
                "aliases": ["religion", "my religion"]
            },
            {
                "name": "caste",
                "label": "Caste",
                "format": "text",
                "aliases": ["caste", "my caste"]
            },
            {
                "name": "category",
                "label": "Category",
                "format": "text",
                "aliases": ["category", "my category", "caste category"]
            },
            {
                "name": "nationality",
                "label": "Nationality",
                "format": "text",
                "aliases": ["nationality", "my nationality"]
            },
            {
                "name": "mother_tongue",
                "label": "Mother Tongue",
                "format": "text",
                "aliases": ["mother tongue", "my mother tongue", "native language"]
            },
            {
                "name": "father_profession",
                "label": "Father's Profession",
                "format": "text",
                "aliases": ["father profession", "father's profession", "father occupation", "what does my father do"]
            },
            {
                "name": "mother_profession",
                "label": "Mother's Profession",
                "format": "text",
                "aliases": ["mother profession", "mother's profession", "mother occupation", "what does my mother do"]
            }
        ]
    },
    {
        "module": "study_materials",
        "fields": [
            {
                "name": "study_material_search",
                "label": "Dynamic Study Material Search",
                "format": "text",
                "aliases": [
                    "study material", "study materials", "materials", "notes", "worksheets", "portions",
                    "any study material", "show study material", "show notes", "show worksheets", "show portions",
                    "how many study materials", "how many materials", "kannada study material", "hindi study material",
                    "english study material", "maths study material", "science study material"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "dynamic_study_material_search",
                    "subject_key": "subject_name",
                    "type_key": "type",
                    "desc_key": "description",
                    "doc_key": "document_name_url",
                    "date_key": "created_date_time",
                    "teacher_key": "name"
                }
            },
            {
                "name": "total_study_materials",
                "label": "Total Study Materials",
                "format": "number",
                "aliases": [
                    "total study materials", "total materials", "how many study materials do i have",
                    "total count of study materials", "study materials count"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "count"
                }
            },
            {
                "name": "recent_study_materials",
                "label": "Recent Study Materials",
                "format": "text",
                "aliases": [
                    "latest study material", "recent study material", "new study material", "latest notes",
                    "recent notes", "latest worksheets", "recent worksheets", "latest portions", "recent portions"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_recent_study_materials",
                    "limit": 3,
                    "subject_key": "subject_name",
                    "type_key": "type",
                    "desc_key": "description",
                    "doc_key": "document_name_url",
                    "date_key": "created_date_time",
                    "teacher_key": "name"
                }
            },
            {
                "name": "all_study_materials",
                "label": "All Study Materials",
                "format": "list",
                "aliases": [
                    "all study materials", "all materials", "list study materials", "show all study materials"
                ],
                "aggregation": {
                    "source_field": "",
                    "operation": "filter_study_materials_list",
                    "subject_key": "subject_name",
                    "type_key": "type",
                    "desc_key": "description",
                    "doc_key": "document_name_url",
                    "date_key": "created_date_time",
                    "teacher_key": "name"
                }
            }
        ]
    }
]

# =============================================================================
# API Registry
# =============================================================================

FEE_RESPONSE_MAPPING = {
    "pending_amount":      "pending_amount",
    "total_fee":           "total_fee_amount",
    "paid_amount":         "paid_amount",
    "installment_amount":  "instalment_amt",
    "first_installment":   "first_installmet",
    "second_installment":  "second_installmet",
    "concession":          "concession",
    "installment_status":  "instalment_status",
    "is_paid":             "is_paid",
    "min_amount":          "min_amount",
    "exam_total_fee":      "exam_total_fee",
    "exam_pending_amount": "exam_pending_amt",
    "exam_paid_fee":       "exam_paid_fee",
    "student_name":        "studentInfo.student_name",
    "student_id":          "studentInfo.student_id",
    "term":                "studentInfo.term_name",
    "semester":            "studentInfo.semester",
    "section":             "studentInfo.section_name",
    "stream":              "studentInfo.applied_course",
    "father_name":         "studentInfo.father_name",
    "medium":              "medium",
    "pay_button":          "pay_button",
    "show_manual_entry":   "show_manual_entry",
    "note_status":         "note_status",
    "note_title":          "note_title",
    "note_desc":           "note_desc",
}

PROFILE_RESPONSE_MAPPING = {
    "student_name":       "student_name",
    "student_id":         "student_id",
    "dob":                "dob",
    "father_name":        "father_name",
    "mother_name":        "mother_name",
    "guardian_name":      "guardian_name",
    "mobile":             "father_mobile_one",
    "father_mobile":      "father_mobile_one",
    "mother_mobile":      "mother_mobile_one",
    "email":              "email",
    "father_email":       "father_email",
    "mother_email":       "mother_email",
    "guardian_email":     "guardian_email",
    "guardian_mobile":    "guardian_mobile_no",
    "address":            "present_address",
    "permanent_address":  "permanent_address",
    "blood_group":        "blood_group",
    "gender":             "gender",
    "class_name":         "term_name",
    "section":            "section_name",
    "class_teacher":      "name",
    "house_color":        "house_color",
    "admission_no":       "admission_no",
    "application_no":     "application_no",
    "aadhar_no":          "aadhar_no",
    "father_aadhar":      "father_aadhar",
    "mother_aadhar":      "mother_aadhar",
    "father_profession":  "father_profession",
    "mother_profession":  "mother_profession",
    "mother_tongue":      "mother_tongue",
    "apaar_id":           "apaar_id",
    "pen_no":             "student_pen_no",
    "sts_no":             "sts_no",
    "sat_no":             "sat_number",
    "second_language":    "language_two",
    "third_language":     "language_three",
    "religion":           "religion_name",
    "caste":              "caste",
    "category":           "category_name",
    "nationality":        "nationality_name",
}

API_REGISTRIES = [
    # SJBHS Student Fees
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "fees",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiviewFeePaymentInfo",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": FEE_RESPONSE_MAPPING,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SJBHS_STUDENT alias
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "fees",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiviewFeePaymentInfo",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": FEE_RESPONSE_MAPPING,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SAGS School Fees
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "fees",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/student/fees",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {
            "total_fee": "total_fee",
            "paid_amount": "paid_fee",
            "pending_amount": "pending_fee",
            "concession": "discount",
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SAGS School Attendance
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "attendance",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/student/attendance",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {
            "start_date": "start_date",
            "end_date": "end_date",
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SJBHS Student Attendance
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "attendance",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiviewAttendance",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        # Scalar fields from the raw response (start_date, end_date)
        # Aggregated fields (absent_count, absent_dates, etc.) are computed
        # by the ArrayAggregator from attendance_data array — NOT from this mapping.
        "response_mapping": {
            "start_date": "start_date",
            "end_date": "end_date",
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SJBHS_STUDENT alias — Attendance
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "attendance",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiviewAttendance",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {
            "start_date": "start_date",
            "end_date": "end_date",
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SJBHS Student Holiday & Academic Calendar
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "calendar",
        "action": "summary",
        "request": {
            "method": "GET",
            "path": "/student/apicalender/",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "holiday",
        "action": "summary",
        "request": {
            "method": "GET",
            "path": "/student/apicalender/",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SJBHS_STUDENT alias — Calendar & Holiday
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "calendar",
        "action": "summary",
        "request": {
            "method": "GET",
            "path": "/student/apicalender/",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "holiday",
        "action": "summary",
        "request": {
            "method": "GET",
            "path": "/student/apicalender/",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SAGS School Holiday & Calendar
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "calendar",
        "action": "summary",
        "request": {
            "method": "GET",
            "path": "/api/student/calendar",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "holiday",
        "action": "summary",
        "request": {
            "method": "GET",
            "path": "/api/student/calendar",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    # SJBHS Student Homework
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "homework",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apimyHomework",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "homework",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apimyHomework",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "homework",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/student/homework",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "notification",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apimyNotificationsApi",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "notice",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apimyNotificationsApi",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "notification",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apimyNotificationsApi",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "notice",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apimyNotificationsApi",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "notification",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/student/notifications",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "notice",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/student/notifications",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "profile",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiprofile",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": PROFILE_RESPONSE_MAPPING,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "profile",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiprofile",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": PROFILE_RESPONSE_MAPPING,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "profile",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/student/profile",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": PROFILE_RESPONSE_MAPPING,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs",
        "role": "student",
        "module": "study_materials",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiviewstudyMaterials",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sjbhs_student",
        "role": "student",
        "module": "study_materials",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/student/apiviewstudyMaterials",
            "body_template": {"row_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "institution_id": "sags_school",
        "role": "student",
        "module": "study_materials",
        "action": "summary",
        "request": {
            "method": "POST",
            "path": "/api/student/study_materials",
            "body_template": {"user_id": "{user_id}"},
            "content_type": "application/json"
        },
        "response_root": None,
        "response_mapping": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
]

# =============================================================================
# Templates
# =============================================================================

TEMPLATES = [
    {
        "module": "fees",
        "action": "summary",
        "field_templates": {
            "pending_amount":      "Your pending fee amount is ₹{pending_amount}.",
            "total_fee":           "Your total fee for this term is ₹{total_fee}.",
            "paid_amount":         "You have paid ₹{paid_amount} so far.",
            "installment_amount":  "Your installment amount is ₹{installment_amount}.",
            "first_installment":   "Your first installment amount is ₹{first_installment}.",
            "second_installment":  "Your second installment amount is ₹{second_installment}.",
            "concession":          "Your fee concession is ₹{concession}.",
            "installment_status":  "Installment payment is {installment_status}.",
            "exam_total_fee":      "Your total exam fee is ₹{exam_total_fee}.",
            "exam_pending_amount": "Your pending exam fee is ₹{exam_pending_amount}.",
            "exam_paid_fee":       "You have paid ₹{exam_paid_fee} towards exam fees.",
            "min_amount":          "The minimum payment amount is ₹{min_amount}.",
        },
        "summary_template": (
            "Here is your fee summary:\n\n"
            "💰 Total Fee:    ₹{total_fee}\n"
            "✅ Paid:          ₹{paid_amount}\n"
            "⏳ Pending:       ₹{pending_amount}\n"
            "🎁 Concession:   ₹{concession}"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "attendance",
        "action": "summary",
        "field_templates": {
            "attendance_percentage": "Your attendance is {attendance_percentage}%.",
            "overall_percentage": "Your overall attendance is {attendance_percentage}%.",
            "present_count":      "You were present for {present_count} days.",
            "absent_count":       "You were absent for {absent_count} days.",
            "total_classes":      "There are {total_classes} total classes.",
            "total_working_days": "There are {total_classes} total working days.",
            "status":             "Your attendance status is {status}.",
        },
        "summary_template": (
            "Here is your attendance summary:\n\n"
            "📊 Overall:      {attendance_percentage}\n"
            "✅ Present:      {present_count} days\n"
            "❌ Absent:       {absent_count} days\n"
            "📅 Total Classes: {total_classes} days"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "calendar",
        "action": "summary",
        "field_templates": {
            "event_search": "{event_search}",
            "holiday_count": "There are {holiday_count} holiday(s) scheduled in the academic calendar.",
            "holiday_list": "🌴 **Upcoming Holidays:**\n\n{holiday_list}",
            "school_reopening": "🏫 **School Reopening Dates:**\n\n{school_reopening}",
        },
        "summary_template": (
            "📅 **Academic Calendar & Holiday Overview:**\n\n"
            "🎉 **Total Holidays:** {holiday_count}\n\n"
            "🏫 **School Reopening Dates:**\n{school_reopening}\n\n"
            "🌴 **Upcoming Holidays:**\n{holiday_list}"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "holiday",
        "action": "summary",
        "field_templates": {
            "event_search": "{event_search}",
            "holiday_count": "There are {holiday_count} holiday(s) scheduled in the academic calendar.",
        },
        "summary_template": (
            "📅 **Academic Calendar & Holiday Overview:**\n\n"
            "🎉 **Total Holidays:** {holiday_count}\n\n"
            "🏫 **School Reopening Dates:**\n{school_reopening}\n\n"
            "🌴 **Upcoming Holidays:**\n{holiday_list}"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "homework",
        "action": "summary",
        "field_templates": {
            "homework_search": "{homework_search}",
            "pending_count": "You have {pending_count} pending homework assignment(s).",
            "completed_count": "You have completed {completed_count} homework assignment(s).",
            "total_homework": "You have a total of {total_homework} homework assignment(s) assigned.",
            "pending_homework": "⏳ **Pending Homework Assignments:**\n\n{pending_homework}",
            "completed_homework": "✅ **Completed Homework Assignments:**\n\n{completed_homework}",
            "all_homework": "📚 **All Assigned Homework:**\n\n{all_homework}",
        },
        "summary_template": (
            "📚 **Homework & Assignment Summary:**\n\n"
            "📊 **Total Assigned:** {total_homework} | ⏳ **Pending:** {pending_count}\n\n"
            "📝 **Pending Assignments:**\n{pending_homework}"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "notification",
        "action": "summary",
        "field_templates": {
            "notification_search": "{notification_search}",
            "total_notifications": "You have {total_notifications} notification(s) / circular(s).",
            "recent_notifications": "{recent_notifications}",
            "all_notifications": "📢 **All School Notifications & Circulars:**\n\n{all_notifications}",
        },
        "summary_template": (
            "📢 **School Notifications & Circulars Overview:**\n\n"
            "📊 **Total Notifications:** {total_notifications}\n\n"
            "{recent_notifications}"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "notice",
        "action": "summary",
        "field_templates": {
            "notification_search": "{notification_search}",
            "total_notifications": "You have {total_notifications} notice(s) on the notice board.",
            "recent_notifications": "{recent_notifications}",
            "all_notifications": "📢 **All School Notices:**\n\n{all_notifications}",
        },
        "summary_template": (
            "📢 **Notice Board Overview:**\n\n"
            "📊 **Total Notices:** {total_notifications}\n\n"
            "{recent_notifications}"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "profile",
        "action": "summary",
        "field_templates": {
            "student_name":       "Your name is {student_name}.",
            "dob":                "Your Date of Birth is {dob}.",
            "father_name":        "Your father's name is {father_name}.",
            "mother_name":        "Your mother's name is {mother_name}.",
            "guardian_name":      "Your guardian's name is {guardian_name}.",
            "mobile":             "Your registered mobile number is {mobile}.",
            "father_mobile":      "Your father's contact number is {father_mobile}.",
            "mother_mobile":      "Your mother's contact number is {mother_mobile}.",
            "email":              "Your registered email address is {email}.",
            "address":            "Your registered residential address is {address}.",
            "permanent_address":  "Your permanent address is {permanent_address}.",
            "blood_group":        "Your blood group is {blood_group}.",
            "gender":             "Your gender is {gender}.",
            "class_name":         "You are studying in {class_name}.",
            "section":            "You are in section {section}.",
            "class_teacher":      "Your class teacher is {class_teacher}.",
            "house_color":        "You are in house {house_color}.",
            "admission_no":       "Your admission number is {admission_no}.",
            "application_no":     "Your application number is {application_no}.",
            "student_id":         "Your Student ID is {student_id}.",
            "aadhar_no":          "Your Aadhaar number is {aadhar_no}.",
            "apaar_id":           "Your APAAR ID is {apaar_id}.",
            "pen_no":             "Your student PEN number is {pen_no}.",
            "sts_no":             "Your STS number is {sts_no}.",
            "sat_no":             "Your SAT number is {sat_no}.",
            "second_language":    "Your second language is {second_language}.",
            "third_language":     "Your third language is {third_language}.",
            "religion":           "Your religion is {religion}.",
            "caste":              "Your caste is {caste}.",
            "category":           "Your category is {category}.",
            "nationality":        "Your nationality is {nationality}.",
            "mother_tongue":      "Your mother tongue is {mother_tongue}.",
            "father_profession":  "Your father's profession is {father_profession}.",
            "mother_profession":  "Your mother's profession is {mother_profession}.",
        },
        "summary_template": (
            "👤 **Student Profile Details:**\n\n"
            "• **Name:** {student_name} (ID: {student_id} | Adm No: {admission_no})\n"
            "• **Class & Section:** {class_name} - {section}\n"
            "• **Class Teacher:** {class_teacher}\n"
            "• **Date of Birth:** {dob} | **Blood Group:** {blood_group} | **Gender:** {gender}\n"
            "• **Parents:** Father: {father_name} | Mother: {mother_name}\n"
            "• **Contact:** 📞 {mobile} | ✉️ {email}\n"
            "• **House:** {house_color}\n"
            "• **Address:** {address}\n"
            "• **Academic IDs:** APAAR: {apaar_id} | Aadhaar: {aadhar_no} | PEN: {pen_no}"
        ),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "module": "study_materials",
        "action": "summary",
        "field_templates": {
            "study_material_search": "{study_material_search}",
            "total_study_materials": "You have {total_study_materials} study material(s) available.",
            "recent_study_materials": "{recent_study_materials}",
            "all_study_materials": "📚 **All Study Materials & Portions:**\n\n{all_study_materials}",
        },
        "summary_template": (
            "📚 **Study Materials & Portions Overview:**\n\n"
            "📊 **Total Materials:** {total_study_materials}\n\n"
            "{recent_study_materials}"
        ),
        "updated_at": datetime.now(timezone.utc),
    }
]


# =============================================================================
# Seed Runner
# =============================================================================

async def seed() -> None:
    print("\n🌱 PhinsIQ Complete MongoDB Seed Runner")
    print("=" * 60)

    client = AsyncIOMotorClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=10000,
        tlsCAFile=certifi.where(),
    )
    db = client[settings.mongodb_database]

    try:
        await client.admin.command("ping")
        print(f"✅ Connected to MongoDB: {settings.mongodb_database}\n")

        # Cleanup legacy duplicate study_material entries
        await db.modules.delete_one({"_id": "study_material"})
        await db.fields.delete_one({"module": "study_material"})
        await db.api_registry.delete_many({"module": "study_material"})
        await db.templates.delete_one({"module": "study_material"})

        # 1. Institutions
        for inst in INSTITUTIONS:
            await db.institutions.replace_one({"_id": inst["_id"]}, inst, upsert=True)
            print(f"  ✓ Institution: {inst['_id']} ({inst['name']})")

        # 2. Roles
        for role in ROLES:
            await db.roles.replace_one({"_id": role["_id"]}, role, upsert=True)
            print(f"  ✓ Role: {role['_id']}")

        # 3. Modules
        for mod in MODULES:
            await db.modules.replace_one({"_id": mod["_id"]}, mod, upsert=True)
            print(f"  ✓ Module: {mod['_id']}")

        # 4. Actions
        for act in ACTIONS:
            await db.actions.replace_one({"_id": act["_id"]}, act, upsert=True)
            print(f"  ✓ Action: {act['_id']}")

        # 5. Fields
        for f in FIELDS:
            await db.fields.replace_one({"module": f["module"]}, f, upsert=True)
            print(f"  ✓ Fields for: {f['module']} ({len(f['fields'])} fields configured)")

        # 6. API Registry
        for reg in API_REGISTRIES:
            await db.api_registry.replace_one(
                {
                    "institution_id": reg["institution_id"],
                    "role": reg["role"],
                    "module": reg["module"],
                    "action": reg["action"],
                },
                reg,
                upsert=True
            )
            print(f"  ✓ API Registry: {reg['institution_id']}/{reg['role']}/{reg['module']}/{reg['action']}")

        # 7. Templates
        for t in TEMPLATES:
            await db.templates.replace_one(
                {"module": t["module"], "action": t["action"]},
                t,
                upsert=True
            )
            print(f"  ✓ Templates: {t['module']}/{t['action']}")

        # 8. Questions (Multi-tenant sample questions table)
        from app.router.question_catalog import get_default_seed_questions
        total_seeded_q = 0
        for inst_id, role in [
            ("sjbhs", "student"),
            ("sjbhs", "staff"),
            ("sjbhs_student", "student"),
            ("sags_school", "student"),
        ]:
            q_docs = get_default_seed_questions(institution_id=inst_id, role=role)
            for q in q_docs:
                await db.questions.replace_one({"_id": q["_id"]}, q, upsert=True)
                total_seeded_q += 1
            print(f"  ✓ Questions: {len(q_docs)} questions seeded for {inst_id} ({role})")

        print("\n" + "=" * 60)
        print(f"🎉 Database seeding completed successfully! ({total_seeded_q} questions seeded into 'questions' table)")
        print("=" * 60)

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed())
