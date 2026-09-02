"""
Claude Response Repository
==========================

PURPOSE:
    Data access layer for logging all Claude AI interactions into the
    'claude_responses' collection in MongoDB.

SCHEMA:
    {
        "_id": ObjectId,
        "institution_id": str,
        "user_id": str,
        "role": str,
        "question": str,
        "answer": str,
        "model": str,
        "tokens_used": {
            "input_tokens": int,
            "output_tokens": int,
            "total_tokens": int
        },
        "duration_ms": float,
        "created_at": datetime
    }
"""

from datetime import datetime, timezone
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClaudeResponseRepository:
    """Logs and queries Claude fallback interactions in MongoDB."""

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return get_database()

    async def log_response(
        self,
        institution_id: str,
        user_id: str,
        role: str,
        question: str,
        answer: str,
        model: str,
        tokens_used: Optional[dict[str, int]] = None,
        duration_ms: float = 0.0,
    ) -> dict[str, Any]:
        """Save a Claude fallback interaction record."""
        doc = {
            "institution_id": institution_id,
            "user_id": user_id,
            "role": role,
            "question": question,
            "answer": answer,
            "model": model,
            "tokens_used": tokens_used or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "duration_ms": round(duration_ms, 2),
            "created_at": datetime.now(timezone.utc),
        }

        try:
            res = await self.db.claude_responses.insert_one(doc)
            doc["_id"] = str(res.inserted_id)
            logger.info(
                "claude_response_logged",
                institution_id=institution_id,
                user_id=user_id,
                model=model,
                tokens=tokens_used,
            )
        except Exception as exc:
            logger.error("claude_response_log_failed", error=str(exc))

        return doc

    async def find_recent_response(
        self,
        institution_id: str,
        user_id: str,
        question: str,
        max_age_hours: int = 6,
        similarity_threshold: float = 50.0,
    ) -> Optional[dict[str, Any]]:
        """
        Finds an existing cached Claude response for the same institution and user
        created within the last max_age_hours (default: 6 hours) where the question
        is identical or has >= similarity_threshold (default: 50%) semantic match.
        """
        import re
        from datetime import timedelta
        from rapidfuzz import fuzz

        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        clean_q = question.strip().lower()

        # Step 1: Fast Exact Match Check
        escaped_q = re.escape(question.strip())
        query = {
            "institution_id": institution_id,
            "user_id": user_id,
            "question": {"$regex": f"^{escaped_q}$", "$options": "i"},
            "created_at": {"$gte": cutoff},
        }

        try:
            doc = await self.db.claude_responses.find_one(query, sort=[("created_at", -1)])
            if doc:
                return doc
        except Exception as exc:
            logger.warning("claude_find_exact_response_failed", error=str(exc))

        # Step 2: >= 50% Semantic / Fuzzy Match within 6-Hour Window
        try:
            recent_query = {
                "institution_id": institution_id,
                "user_id": user_id,
                "created_at": {"$gte": cutoff},
            }
            cursor = self.db.claude_responses.find(recent_query).sort("created_at", -1).limit(50)
            recent_docs = await cursor.to_list(length=50)

            best_doc = None
            best_score = 0.0

            for d in recent_docs:
                saved_q = (d.get("question") or "").strip().lower()
                if not saved_q:
                    continue

                score1 = fuzz.token_set_ratio(clean_q, saved_q)
                score2 = fuzz.ratio(clean_q, saved_q)
                max_score = max(score1, score2)

                if max_score >= similarity_threshold and max_score > best_score:
                    best_score = max_score
                    best_doc = d

            if best_doc:
                logger.info(
                    "claude_fuzzy_cache_hit_within_6_hours",
                    institution_id=institution_id,
                    user_id=user_id,
                    similarity_score=best_score,
                    matched_saved_question=best_doc.get("question"),
                    incoming_question=question,
                )
                return best_doc

            return None
        except Exception as exc:
            logger.warning("claude_find_fuzzy_response_failed", error=str(exc))
            return None

    async def get_recent_logs(
        self,
        institution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch recent Claude interaction logs."""
        query: dict[str, Any] = {}
        if institution_id:
            query["institution_id"] = institution_id
        if user_id:
            query["user_id"] = user_id

        cursor = self.db.claude_responses.find(query).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)


claude_repo = ClaudeResponseRepository()
