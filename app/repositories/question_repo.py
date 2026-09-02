"""
Question Repository
===================

PURPOSE:
    Provides database access to the 'questions' collection in MongoDB.

DOCUMENT DESIGN (1 document per institution_id + role):
    Instead of one doc per question (136 docs), we store one consolidated doc
    per (institution_id, role) pair — only 4 docs total for all SJBHS configs.

    Schema:
    {
      "_id":            "sjbhs_student",       # f"{institution_id}_{role}"
      "institution_id": "sjbhs",
      "role":           "student",
      "modules": {
        "fees": {
          "category_label": "💰 Fees & Payments",
          "questions": [
            {
              "question":    "What is my total fee?",
              "field":       "total_fee",
              "description": "Returns total annual/term fee formatted in ₹.",
              "route":       "/fees"
            },
            ...
          ]
        },
        "attendance": { ... },
        ...
      },
      "updated_at": "2026-08-29T..."
    }

WHY THIS DESIGN?
    ✅ Maintainable — update one array entry instead of 42 separate docs.
    ✅ Readable   — one doc shows ALL questions for a client role at a glance.
    ✅ Fast       — single document fetch; MongoDB loads everything in one read.
    ✅ Scalable   — 16MB document limit is never a concern (42 questions ≈ 2KB).
"""

from datetime import datetime, timezone
from typing import Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory TTL cache: key = f"{inst_id}_{role}"
_questions_cache: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 300.0


def _doc_id(institution_id: str, role: str) -> str:
    """Canonical document _id for a (institution_id, role) pair."""
    return f"{institution_id}_{role}"


class QuestionRepository:
    """
    Repository for the 'questions' collection.
    One document per (institution_id + role) — all questions stored as sub-documents
    within the 'modules' map.
    """

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return get_database()

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    async def get_doc(
        self,
        institution_id: str,
        role: str,
    ) -> Optional[dict[str, Any]]:
        """
        Fetch the single questions document for a given (institution_id, role).
        Returns None if not found.
        """
        cache_key = _doc_id(institution_id, role)
        now = datetime.now(timezone.utc).timestamp()

        cached = _questions_cache.get(cache_key)
        if cached:
            ts, data = cached
            if now - ts < CACHE_TTL_SECONDS:
                return data

        doc = await self.db.questions.find_one(
            {"institution_id": institution_id, "role": role}
        )

        if doc:
            _questions_cache[cache_key] = (now, doc)
        return doc

    async def get_questions(
        self,
        institution_id: Optional[str] = None,
        role: Optional[str] = None,
        module: Optional[str] = None,
        is_active: Optional[bool] = True,  # kept for API compatibility
    ) -> list[dict[str, Any]]:
        """
        Fetch questions as a flat list, compatible with the existing API contract.
        Reads from the single consolidated document per (institution_id, role).
        Falls back to 'sjbhs'/'default' if no specific doc found.
        """
        if not institution_id:
            institution_id = "sjbhs"
        if not role:
            role = "student"

        doc = await self.get_doc(institution_id, role)

        # Fallback: try sjbhs if institution has no questions yet
        if not doc and institution_id not in ("sjbhs", "default"):
            doc = await self.get_doc("sjbhs", role)

        if not doc:
            return []

        modules_map: dict[str, Any] = doc.get("modules", {})
        results: list[dict[str, Any]] = []

        for mod_name, mod_data in modules_map.items():
            if module and mod_name != module:
                continue
            cat_label = mod_data.get("category_label", mod_name.replace("_", " ").title())
            for i, q in enumerate(mod_data.get("questions", [])):
                results.append({
                    "_id": f"{institution_id}_{role}_{mod_name}_{i+1:03d}",
                    "institution_id": institution_id,
                    "role": role,
                    "module": mod_name,
                    "category_label": cat_label,
                    "question": q.get("question", ""),
                    "field": q.get("field", ""),
                    "description": q.get("description", ""),
                    "route": q.get("route", "/dashboard"),
                    "display_order": i + 1,
                    "is_active": True,
                })

        return results

    # -------------------------------------------------------------------------
    # WRITE
    # -------------------------------------------------------------------------

    async def upsert_doc(
        self,
        institution_id: str,
        role: str,
        modules: dict[str, Any],
    ) -> str:
        """
        Save (create or replace) the complete questions document for an
        (institution_id, role) pair. 'modules' must be a dict of:
            { "<module_name>": { "category_label": "...", "questions": [...] } }
        """
        self.flush_cache()
        doc_id = _doc_id(institution_id, role)
        doc = {
            "_id": doc_id,
            "institution_id": institution_id,
            "role": role,
            "modules": modules,
            "updated_at": datetime.now(timezone.utc),
        }
        await self.db.questions.replace_one({"_id": doc_id}, doc, upsert=True)
        logger.info("upserted_questions_doc", doc_id=doc_id)
        return doc_id

    async def upsert_question(self, question_data: dict[str, Any]) -> str:
        """
        Upsert a SINGLE question entry into the correct module sub-array.
        Expects: institution_id, role, module, question, field, description, route.
        """
        self.flush_cache()
        institution_id = question_data.get("institution_id", "sjbhs")
        role = question_data.get("role", "student")
        mod = question_data.get("module", "general")
        cat_label = question_data.get("category_label", mod.replace("_", " ").title())

        q_entry = {
            "question": question_data.get("question", ""),
            "field": question_data.get("field", ""),
            "description": question_data.get("description", ""),
            "route": question_data.get("route", "/dashboard"),
        }

        doc_id = _doc_id(institution_id, role)

        # Try to push to existing array; create module sub-doc if not present
        update_result = await self.db.questions.update_one(
            {"_id": doc_id},
            {
                "$setOnInsert": {
                    "_id": doc_id,
                    "institution_id": institution_id,
                    "role": role,
                },
                "$set": {f"modules.{mod}.category_label": cat_label, "updated_at": datetime.now(timezone.utc)},
                "$push": {f"modules.{mod}.questions": q_entry},
            },
            upsert=True,
        )
        return doc_id

    async def delete_question(self, institution_id: str, role: str, module: str, question_text: str) -> bool:
        """Remove a specific question from the questions sub-array by matching question text."""
        self.flush_cache()
        doc_id = _doc_id(institution_id, role)
        res = await self.db.questions.update_one(
            {"_id": doc_id},
            {
                "$pull": {f"modules.{module}.questions": {"question": question_text}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            }
        )
        return res.modified_count > 0

    async def seed_questions_if_empty(self, questions_list: list[dict[str, Any]]) -> int:
        """
        Seed from a flat list of question dicts (same format as old per-doc schema).
        Converts them to the new consolidated (institution_id, role) document.
        """
        self.flush_cache()
        # Group by (institution_id, role)
        grouped: dict[str, dict[str, Any]] = {}
        for q in questions_list:
            inst = q.get("institution_id", "sjbhs")
            r = q.get("role", "student")
            mod = q.get("module", "general")
            key = _doc_id(inst, r)
            if key not in grouped:
                grouped[key] = {"institution_id": inst, "role": r, "modules": {}}
            modules = grouped[key]["modules"]
            if mod not in modules:
                modules[mod] = {
                    "category_label": q.get("category_label", mod.replace("_", " ").title()),
                    "questions": [],
                }
            modules[mod]["questions"].append({
                "question": q.get("question", ""),
                "field": q.get("field", ""),
                "description": q.get("description", ""),
                "route": q.get("route", "/dashboard"),
            })

        count = 0
        for doc_id, doc_data in grouped.items():
            full_doc = {
                "_id": doc_id,
                "institution_id": doc_data["institution_id"],
                "role": doc_data["role"],
                "modules": doc_data["modules"],
                "updated_at": datetime.now(timezone.utc),
            }
            await self.db.questions.replace_one({"_id": doc_id}, full_doc, upsert=True)
            q_count = sum(len(m["questions"]) for m in doc_data["modules"].values())
            logger.info("seeded_questions_doc", doc_id=doc_id, questions=q_count)
            count += q_count

        return count

    def flush_cache(self) -> None:
        """Clear in-memory question query cache."""
        _questions_cache.clear()


question_repo = QuestionRepository()
