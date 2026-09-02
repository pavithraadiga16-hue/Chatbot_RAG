"""
PhinsIQ Dynamic Questions Catalog
=================================

PURPOSE:
    Provides a comprehensive, verified catalog of natural language sample questions
    categorized by institution_id, role, and ERP module. Supports multi-tenant dynamic
    MongoDB persistence with fallback to default educational schemas.
"""

from typing import Any, Optional

QUESTION_CATALOG: dict[str, list[dict[str, Any]]] = {
    "fees": [
        {
            "question": "What is my total fee?",
            "field": "total_fee",
            "description": "Returns total annual/term fee amount formatted in ₹.",
            "route": "/fees",
        },
        {
            "question": "What is my pending fee balance?",
            "field": "pending_fee",
            "description": "Returns remaining unpaid fee balance.",
            "route": "/fees",
        },
        {
            "question": "How much fee have I paid so far?",
            "field": "paid_fee",
            "description": "Returns total fee already paid with receipts.",
            "route": "/fees",
        },
        {
            "question": "Show my fee payment details",
            "field": "summary",
            "description": "Returns full term fee overview including total, paid, and balance.",
            "route": "/fees",
        },
        {
            "question": "Is there any unpaid fee for this term?",
            "field": "pending_fee",
            "description": "Checks if there is any outstanding balance to be cleared.",
            "route": "/fees",
        },
    ],
    "attendance": [
        {
            "question": "What is my attendance percentage?",
            "field": "attendance_percentage",
            "description": "Calculates overall percentage from daily attendance records.",
            "route": "/attendance",
        },
        {
            "question": "How many days was I absent?",
            "field": "absent_count",
            "description": "Counts total days with status 'absent'.",
            "route": "/attendance",
        },
        {
            "question": "How many days was I present?",
            "field": "present_count",
            "description": "Counts total days attended class.",
            "route": "/attendance",
        },
        {
            "question": "Which dates was I marked absent?",
            "field": "absent_dates",
            "description": "Returns sorted list of absent dates in DD/MM/YYYY format.",
            "route": "/attendance",
        },
        {
            "question": "Show my full attendance summary",
            "field": "summary",
            "description": "Returns complete card with percentage, present, and absent counts.",
            "route": "/attendance",
        },
    ],
    "homework": [
        {
            "question": "Show my pending homework",
            "field": "pending_homework_count",
            "description": "Filters active homework assignments waiting for submission.",
            "route": "/homework",
        },
        {
            "question": "What is my homework for today?",
            "field": "homework_summary",
            "description": "Returns all assignments assigned with submission deadlines.",
            "route": "/homework",
        },
        {
            "question": "Do I have any math homework?",
            "field": "homework_search",
            "description": "Filters assignments specifically for Mathematics.",
            "route": "/homework",
        },
        {
            "question": "What is my English homework assignment?",
            "field": "homework_search",
            "description": "Filters assignments specifically for English.",
            "route": "/homework",
        },
        {
            "question": "List all my active assignments and submission dates",
            "field": "summary",
            "description": "Returns full homework table with subjects, topics, and due dates.",
            "route": "/homework",
        },
    ],
    "study_materials": [
        {
            "question": "Show available study materials",
            "field": "total_study_materials",
            "description": "Counts and lists available study resources uploaded by teachers.",
            "route": "/study-materials",
        },
        {
            "question": "Are there any study notes uploaded?",
            "field": "study_materials_summary",
            "description": "Lists recent study notes, PDFs, and lesson portions.",
            "route": "/study-materials",
        },
        {
            "question": "What are my science study portions?",
            "field": "study_material_search",
            "description": "Searches study portions for Science subject.",
            "route": "/study-materials",
        },
        {
            "question": "Give me math syllabus and chapter notes",
            "field": "study_material_search",
            "description": "Searches study portions for Math subject.",
            "route": "/study-materials",
        },
        {
            "question": "List all downloadable lesson notes",
            "field": "summary",
            "description": "Provides download links and titles for all class notes.",
            "route": "/study-materials",
        },
    ],
    "calendar_and_holidays": [
        {
            "question": "When and all do I have holidays?",
            "field": "upcoming_holidays",
            "description": "Lists upcoming school holidays from today onwards.",
            "route": "/calendar",
        },
        {
            "question": "When is the next school holiday?",
            "field": "next_holiday",
            "description": "Identifies the nearest upcoming holiday date and event name.",
            "route": "/calendar",
        },
        {
            "question": "How many holidays do we have this year?",
            "field": "total_holidays",
            "description": "Calculates total public and school holidays in calendar.",
            "route": "/calendar",
        },
        {
            "question": "When does school reopen after vacation?",
            "field": "school_reopen_date",
            "description": "Finds reopening date from academic calendar events.",
            "route": "/calendar",
        },
        {
            "question": "When is Dasara Vacation?",
            "field": "event_search",
            "description": "Searches start and end dates for Dasara Vacation.",
            "route": "/calendar",
        },
        {
            "question": "When is Final Assessment Commences PKG to Std 9?",
            "field": "event_search",
            "description": "Extracts scheduled date for Final Assessment.",
            "route": "/calendar",
        },
        {
            "question": "When is MERAKI?",
            "field": "event_search",
            "description": "Finds date for school cultural fest MERAKI.",
            "route": "/calendar",
        },
        {
            "question": "When is PTM?",
            "field": "event_search",
            "description": "Searches scheduled Parent Teacher Meeting dates.",
            "route": "/calendar",
        },
        {
            "question": "what is there on 20 Oct 2025?",
            "field": "date_lookup",
            "description": "Looks up scheduled school events on specific target date.",
            "route": "/calendar",
        },
        {
            "question": "Show my academic calendar",
            "field": "summary",
            "description": "Returns full chronological list of upcoming academic events.",
            "route": "/calendar",
        },
    ],
    "notifications": [
        {
            "question": "Show recent school notifications",
            "field": "notification_summary",
            "description": "Displays latest announcements and circulars.",
            "route": "/notifications",
        },
        {
            "question": "Are there any urgent circulars?",
            "field": "urgent_notifications",
            "description": "Filters notifications with high priority or urgent tags.",
            "route": "/notifications",
        },
        {
            "question": "Show general school notices",
            "field": "general_notifications",
            "description": "Lists general circulars and announcements.",
            "route": "/notifications",
        },
    ],
    "profile": [
        {
            "question": "Show my student profile",
            "field": "summary",
            "description": "Returns full student identity card with class, admission number, and parents.",
            "route": "/profile",
        },
        {
            "question": "What is my admission number?",
            "field": "admission_no",
            "description": "Returns student registration / admission identifier.",
            "route": "/profile",
        },
        {
            "question": "What class and section am I in?",
            "field": "class_name",
            "description": "Returns class and division (e.g. X-E).",
            "route": "/profile",
        },
        {
            "question": "Show my parent details and emergency contacts",
            "field": "parent_name",
            "description": "Returns father, mother name, and registered phone number.",
            "route": "/profile",
        },
    ],
    "academic_overview": [
        {
            "question": "How am I doing in my academic progress?",
            "field": "overview",
            "description": "Generates 360° student snapshot across attendance, homework, fees, and study portions.",
            "route": "/dashboard",
        },
        {
            "question": "Show my 360 overall academic standing",
            "field": "overview",
            "description": "Returns complete multi-module performance report.",
            "route": "/dashboard",
        },
    ],
    "multi_module": [
        {
            "question": "my attendance and total fee",
            "field": "attendance + fees",
            "description": "Queries and renders both attendance percentage and total term fee.",
            "route": "/attendance, /fees",
        },
        {
            "question": "show my pending homework and holiday calendar",
            "field": "homework + calendar",
            "description": "Queries pending assignments alongside upcoming holidays.",
            "route": "/homework, /calendar",
        },
        {
            "question": "what is my fee balance and how many days was I absent?",
            "field": "fees + attendance",
            "description": "Returns pending fee amount and absent count together.",
            "route": "/fees, /attendance",
        },
    ],
}

STAFF_QUESTION_CATALOG: dict[str, list[dict[str, Any]]] = {
    "attendance": [
        {
            "question": "Show my staff attendance summary",
            "field": "attendance_percentage",
            "description": "Returns staff working days and attendance percentage.",
            "route": "/attendance",
        },
        {
            "question": "How many days was I present this month?",
            "field": "present_count",
            "description": "Counts total working days attended this month.",
            "route": "/attendance",
        },
        {
            "question": "Show my leaves taken",
            "field": "absent_count",
            "description": "Lists approved and recorded leave dates.",
            "route": "/attendance",
        },
    ],
    "calendar_and_holidays": [
        {
            "question": "Show school event calendar for staff",
            "field": "event_calendar",
            "description": "Displays academic schedule, exam dates, and staff meetings.",
            "route": "/calendar",
        },
        {
            "question": "When is the next school holiday?",
            "field": "next_holiday",
            "description": "Finds upcoming official school holidays.",
            "route": "/calendar",
        },
        {
            "question": "When is PTM scheduled?",
            "field": "search_event",
            "description": "Finds upcoming Parent-Teacher Meeting dates.",
            "route": "/calendar",
        },
    ],
    "notifications": [
        {
            "question": "Show staff circulars and notices",
            "field": "recent_notifications",
            "description": "Lists latest official administrative notices for faculty.",
            "route": "/notifications",
        },
        {
            "question": "Are there any urgent admin circulars?",
            "field": "urgent_notifications",
            "description": "Highlights high-priority staff circulars.",
            "route": "/notifications",
        },
    ],
    "profile": [
        {
            "question": "Show my staff profile",
            "field": "profile_summary",
            "description": "Returns faculty name, department, role, and contact information.",
            "route": "/profile",
        },
        {
            "question": "What is my employee ID?",
            "field": "employee_id",
            "description": "Displays institutional staff identifier.",
            "route": "/profile",
        },
    ],
}

CATEGORY_LABELS: dict[str, str] = {
    "fees": "💰 Fees & Payments",
    "attendance": "📊 Attendance Tracking",
    "homework": "📚 Homework & Assignments",
    "study_materials": "📖 Study Materials & Syllabus",
    "calendar_and_holidays": "🌴 Calendar & School Holidays",
    "notifications": "📢 Notifications & Circulars",
    "profile": "👤 Student & Staff Profile",
    "academic_overview": "🏆 Academic 360 Progress",
    "multi_module": "🔗 Multi-Module Cross Queries",
}


def get_default_seed_questions(
    institution_id: str = "sjbhs",
    role: str = "student",
) -> list[dict[str, Any]]:
    """Generate default seed question documents for a client institution and role."""
    catalog = STAFF_QUESTION_CATALOG if role == "staff" else QUESTION_CATALOG
    docs: list[dict[str, Any]] = []
    for mod, qlist in catalog.items():
        cat_label = CATEGORY_LABELS.get(mod, mod.replace("_", " ").title())
        for q in qlist:
            docs.append({
                "_id": f"{institution_id}_{role}_{mod}_{len(docs)+1:03d}",
                "institution_id": institution_id,
                "role": role,
                "module": mod,
                "category_label": cat_label,
                "question": q["question"],
                "field": q.get("field", ""),
                "description": q.get("description", ""),
                "route": q.get("route", "/dashboard"),
                "display_order": len(docs) + 1,
                "is_active": True,
            })
    return docs


def get_all_questions_flat() -> list[str]:
    """Return flat list of all default sample question strings."""
    flat_list: list[str] = []
    for module_questions in QUESTION_CATALOG.values():
        for item in module_questions:
            flat_list.append(item["question"])
    return flat_list


def get_catalog_summary(
    institution_id: Optional[str] = None,
    role: Optional[str] = None,
) -> dict[str, Any]:
    """Return static catalog with metadata and total counts."""
    all_flat = get_all_questions_flat()
    return {
        "status": "success",
        "institution_id": institution_id or "default",
        "role": role or "all",
        "total_questions": len(all_flat),
        "total_modules": len(QUESTION_CATALOG),
        "modules": list(QUESTION_CATALOG.keys()),
        "categories": QUESTION_CATALOG,
        "questions": all_flat,
    }


async def get_catalog_for_institution(
    institution_id: Optional[str] = "sjbhs",
    role: Optional[str] = "student",
    module: Optional[str] = None,
) -> dict[str, Any]:
    """
    Fetch questions from MongoDB for the specified institution and role.
    If no questions found, falls back to default schema catalog.
    """
    try:
        from app.repositories.question_repo import question_repo
        db_questions = await question_repo.get_questions(
            institution_id=institution_id,
            role=role,
            module=module,
            is_active=True,
        )
    except Exception:
        db_questions = []

    if db_questions:
        categories: dict[str, list[dict[str, Any]]] = {}
        flat_questions: list[str] = []
        for q in db_questions:
            mod = q.get("module", "general")
            cat_item = {
                "_id": str(q.get("_id", "")),
                "institution_id": q.get("institution_id", institution_id or "all"),
                "role": q.get("role", role or "all"),
                "module": mod,
                "category_label": q.get("category_label") or CATEGORY_LABELS.get(mod, mod.replace("_", " ").title()),
                "question": q["question"],
                "field": q.get("field", ""),
                "description": q.get("description", ""),
                "route": q.get("route", "/dashboard"),
                "display_order": q.get("display_order", 0),
            }
            categories.setdefault(mod, []).append(cat_item)
            if q["question"] not in flat_questions:
                flat_questions.append(q["question"])

        return {
            "status": "success",
            "institution_id": institution_id or "all",
            "role": role or "all",
            "total_questions": len(flat_questions),
            "total_modules": len(categories),
            "modules": list(categories.keys()),
            "categories": categories,
            "questions": flat_questions,
        }

    return get_catalog_summary(institution_id=institution_id, role=role)
