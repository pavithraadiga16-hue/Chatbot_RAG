"""
PhinsIQ Clean Two-Path Query & Intent Router
============================================

ARCHITECTURE:
                    USER QUERY
                        |
                        v
                Query / Intent Router
                        |
             ┌──────────┴──────────┐
             |                     |
             v                     v
       ERP / API DATA             RAG
       Existing Data       Institutional Documents / PDFs
             |                     |
             └──────────┬──────────┘
                        |
                        v
                 FINAL RESPONSE

PURPOSE:
    Routes incoming user queries exclusively into TWO paths:
    1. ERP/API Path: Student-specific records and system data (fee balance,
       attendance, absence count, CGPA, profile, marks, exams, calendar).
    2. RAG Path: Institutional policies, guidelines, lecturer notes, uploaded
       module PDFs, and academic document content.

MULTI-PART HANDLING:
    Decomposes multi-clause queries (e.g. "What is my fee balance and what is
    the minimum attendance requirement?"), executes both paths independently,
    and returns a combined response. Never drops secondary intents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import get_logger
from app.understanding.module_detector import module_detector
from app.rag.router import (
    is_institutional_knowledge_query,
    knowledge_topic_modules,
    build_knowledge_query,
)

logger = get_logger(__name__)

ERP_MODULE_NAMES = {
    "fees", "attendance", "exam", "calendar", "timetable", "library",
    "leave", "payroll", "homework", "notification", "notice", "profile",
    "study_materials", "gallery", "admission", "transport", "academic_overview",
}

PERSONAL_STUDENT_CUES = re.compile(
    r"\b(my|mine|me|i|was i|i was|am i|who am i|about me|student id|cgpa|gpa|balance|"
    r"fee balance|fees balance|due|dues|pending fee|pending amount|attended|absent|absence|"
    r"how many days|percentage|marks|grades|score|scores|profile|class|section|admission no|"
    r"next exam|my exam|homework|pending homework|assignments?)\b",
    re.IGNORECASE,
)

INSTITUTIONAL_DOCUMENT_CUES = re.compile(
    r"\b(policy|policies|rules?|regulations?|guidelines?|handbook|minimum|required|"
    r"requirement|requirements|threshold|criteria|eligibility|condonation|scholarship|"
    r"module|module \d+|module_\d+|chapter|notes?|lecture notes?|syllabus|handbook|"
    r"exam rules|leave policy|attendance policy|attendance requirement)\b",
    re.IGNORECASE,
)

HOLIDAY_CUES = re.compile(
    r"\b(holiday|holidays|vacation|school reopen|reopens?|calendar)\b",
    re.IGNORECASE,
)


@dataclass
class RoutedIntentPlan:
    """Decomposed intent plan for query execution."""
    raw_query: str
    erp_modules: list[str] = field(default_factory=list)
    rag_queries: list[str] = field(default_factory=list)
    is_holiday_query: bool = False
    is_overall_overview: bool = False

    @property
    def has_erp(self) -> bool:
        return bool(self.erp_modules)

    @property
    def has_rag(self) -> bool:
        return bool(self.rag_queries)

    @property
    def is_multi_part(self) -> bool:
        total = len(self.erp_modules) + len(self.rag_queries)
        return total > 1


class QueryRouter:
    """Simple, clean query router for ERP and RAG two-path architecture."""

    def route(self, message: str, role: str = "student") -> RoutedIntentPlan:
        """
        Analyze the incoming user query and determine which parts go to ERP
        and which parts go to RAG.
        """
        logger.info("[ROUTER] Query received: " + message.strip())
        print(f"[ROUTER] Query received: {message.strip()}")

        text = message.strip()
        plan = RoutedIntentPlan(raw_query=text)

        # Website role is institutional website crawl only
        if role == "website":
            plan.rag_queries.append(text)
            return plan

        # Split on coordinating conjunctions for multi-part questions
        clauses = [
            c.strip()
            for c in re.split(r"\s+(?:and|also|plus)\s+|[;,]\s*", text, flags=re.IGNORECASE)
            if c.strip()
        ]
        if not clauses:
            clauses = [text]

        # Check for 360-degree academic dashboard overview
        overall_detect = module_detector.detect(text)
        if overall_detect.is_overall_overview:
            plan.is_overall_overview = True
            plan.erp_modules.append("academic_overview")
            logger.info("[ROUTER] ERP intent detected: academic_overview")
            print("[ROUTER] ERP intent detected: academic_overview")
            return plan

        # Check for holiday inquiry
        if HOLIDAY_CUES.search(text):
            plan.is_holiday_query = True

        for clause in clauses:
            clause_lower = clause.lower()

            # Check if this clause explicitly asks for institutional documents/policy
            is_doc_query = is_institutional_knowledge_query(clause) or bool(INSTITUTIONAL_DOCUMENT_CUES.search(clause_lower))
            has_personal_cue = bool(PERSONAL_STUDENT_CUES.search(clause_lower))

            clause_module_res = module_detector.detect(clause)
            detected_mods = [m for m in clause_module_res.modules if m in ERP_MODULE_NAMES]
            if not detected_mods and clause_module_res.module in ERP_MODULE_NAMES:
                detected_mods = [clause_module_res.module]

            if is_doc_query and not (has_personal_cue and not INSTITUTIONAL_DOCUMENT_CUES.search(clause_lower)):
                # Institutional Document / RAG path
                rag_topic_mods = knowledge_topic_modules(clause)
                focused_query = build_knowledge_query(clause, rag_topic_mods) if rag_topic_mods else clause
                if focused_query not in plan.rag_queries:
                    plan.rag_queries.append(focused_query)
                logger.info("[ROUTER] RAG query detected: " + focused_query)
                print(f"[ROUTER] RAG query detected: {focused_query}")

                # If this clause ALSO had an ERP intent separate from the RAG policy, keep it
                remaining_erp = [m for m in detected_mods if m not in rag_topic_mods]
                for mod in remaining_erp:
                    if mod not in plan.erp_modules:
                        plan.erp_modules.append(mod)
                        logger.info(f"[ROUTER] ERP intent detected: {mod}")
                        print(f"[ROUTER] ERP intent detected: {mod}")

            elif detected_mods and (has_personal_cue or clause_module_res.confidence >= 0.35):
                # ERP Path
                for mod in detected_mods:
                    if mod not in plan.erp_modules:
                        plan.erp_modules.append(mod)
                        logger.info(f"[ROUTER] ERP intent detected: {mod}")
                        print(f"[ROUTER] ERP intent detected: {mod}")

            else:
                # No ERP data available -> Route to RAG (Section 6: ERP available? YES -> ERP, NO -> RAG)
                if clause not in plan.rag_queries:
                    plan.rag_queries.append(clause)
                logger.info("[ROUTER] RAG query detected (non-ERP): " + clause)
                print(f"[ROUTER] RAG query detected: {clause}")

        # If holiday query was detected and no explicit calendar module added, add calendar to ERP check
        if plan.is_holiday_query and "calendar" not in plan.erp_modules:
            plan.erp_modules.append("calendar")
            logger.info("[ROUTER] ERP intent detected: calendar (holiday query)")

        return plan


query_router = QueryRouter()
