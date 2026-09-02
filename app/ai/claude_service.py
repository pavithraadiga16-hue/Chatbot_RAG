"""
Claude AI Academic Assistant Service
====================================

PURPOSE:
    Provides production-grade Claude fallback when local keyword detection
    confidence is low or when conversational/complex multi-module questions
    are asked.

FEATURES:
    1. Strict Academic & Educational Scope Guardrails.
    2. Multi-Module Student ERP Context Injection.
    3. In-Memory TTL Response Caching (instant sub-50ms cache hits).
    4. MongoDB Logging into 'claude_responses' collection.
    5. Token limit enforcement (max_tokens = 500).
"""

import time
import hashlib
from typing import Any, Optional
import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.repositories.claude_repo import claude_repo

logger = get_logger(__name__)

# System prompt enforcing educational scope and role guidelines
ACADEMIC_SYSTEM_PROMPT = (
    "You are PhinsIQ, the official AI Academic Assistant for educational institutions and school portals.\n\n"
    "YOUR PRIMARY PURPOSE:\n"
    "• Assist students, parents, and educators with their academic life, student records, attendance, fees, "
    "homework, study materials, circulars/notices, exams, and school calendar events.\n"
    "• Utilize the provided verified Student ERP Context to deliver accurate, personalized, and warm answers.\n\n"
    "STRICT EDUCATIONAL & SCOPE GUARDRAILS:\n"
    "1. Answer ONLY queries related to the student, their school, academics, homework, lesson notes, portions, "
    "attendance, fees, circulars, and school portal services.\n"
    "2. If the user asks off-topic questions completely outside education or the school portal (e.g., coding scripts, "
    "video games, general politics, gossip, hacking, general chat), politely decline by stating that you are dedicated "
    "exclusively to school and academic assistance, and offer to help with their studies, homework, or portal data instead.\n"
    "3. When asked conversational identity questions (e.g. 'do you know me?', 'who am i?', 'tell about me'), warmly "
    "identify the student using the provided Student Context (Name, Class, Section, Admission Number, School).\n"
    "4. Keep responses concise, clear, polite, and formatted with clean Markdown. Do not exceed 500 tokens."
)


class ClaudeService:
    """Async client and manager for Claude AI Fallback."""

    def __init__(self, cache_ttl_seconds: int = 600) -> None:
        self.cache_ttl = cache_ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}
        self.api_url = "https://api.anthropic.com/v1/messages"

    def _generate_cache_key(self, institution_id: str, role: str, user_id: str, question: str) -> str:
        raw = f"{institution_id}:{role}:{user_id}:{question.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[dict[str, Any]]:
        entry = self._cache.get(cache_key)
        if entry:
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry
            else:
                self._cache.pop(cache_key, None)
        return None

    def _save_to_cache(self, cache_key: str, answer: str, tokens_used: dict) -> None:
        # Keep cache bounded (max 500 items)
        if len(self._cache) > 500:
            oldest_key = min(self._cache, key=lambda k: self._cache[k]["timestamp"])
            self._cache.pop(oldest_key, None)

        self._cache[cache_key] = {
            "answer": answer,
            "tokens_used": tokens_used,
            "timestamp": time.time(),
        }

    def format_student_context(self, mapped_data: dict[str, Any]) -> str:
        """Format multi-module ERP student records into structured context for Claude."""
        lines = ["=== VERIFIED STUDENT ERP RECORDS ==="]

        # Profile
        name = mapped_data.get("student_name")
        cls = mapped_data.get("class_name")
        sec = mapped_data.get("section")
        adm_no = mapped_data.get("admission_no")
        stu_id = mapped_data.get("student_id")
        dob = mapped_data.get("dob")
        teacher = mapped_data.get("class_teacher")
        father = mapped_data.get("father_name")
        mother = mapped_data.get("mother_name")

        profile_parts = []
        if name:
            profile_parts.append(f"Student Name: {name}")
        if cls and sec:
            profile_parts.append(f"Class: {cls}-{sec}")
        elif cls:
            profile_parts.append(f"Class: {cls}")
        if adm_no:
            profile_parts.append(f"Admission No: {adm_no}")
        if stu_id:
            profile_parts.append(f"Student ID: {stu_id}")
        if dob:
            profile_parts.append(f"DOB: {dob}")
        if teacher:
            profile_parts.append(f"Class Teacher: {teacher}")
        if father:
            profile_parts.append(f"Father: {father}")
        if mother:
            profile_parts.append(f"Mother: {mother}")

        if profile_parts:
            lines.append("• Student Profile: " + " | ".join(profile_parts))

        # Attendance
        att_pct = mapped_data.get("attendance_percentage") or mapped_data.get("percentage")
        pres_count = mapped_data.get("present_count") or mapped_data.get("present_days")
        total_cls = mapped_data.get("total_classes") or mapped_data.get("total_days")
        abs_count = mapped_data.get("absent_count")
        if att_pct is not None:
            att_info = f"Attendance Rate: {att_pct}%"
            if pres_count is not None and total_cls is not None:
                att_info += f" ({pres_count} attended / {total_cls} total days, {abs_count or 0} absent)"
            lines.append("• Attendance: " + att_info)

        # Fees
        pending_fee = mapped_data.get("pending_amount")
        paid_fee = mapped_data.get("paid_amount")
        total_fee = mapped_data.get("total_fee")
        if pending_fee is not None or total_fee is not None:
            lines.append(f"• Fees: Pending: ₹{pending_fee or 0} | Paid: ₹{paid_fee or 0} | Total: ₹{total_fee or 0}")

        # Homework
        pending_hw = mapped_data.get("pending_count") or mapped_data.get("pending_homework_count")
        total_hw = mapped_data.get("total_homework") or mapped_data.get("total_homework_count")
        if pending_hw is not None or total_hw is not None:
            lines.append(f"• Homework: {pending_hw or 0} pending assignment(s), {total_hw or 0} total")

        # Study Materials
        total_mat = mapped_data.get("total_study_materials")
        if total_mat is not None:
            lines.append(f"• Study Materials: {total_mat} resource(s) and portion(s) available")

        # Notifications
        total_notif = mapped_data.get("total_notifications")
        if total_notif is not None:
            lines.append(f"• Notifications: {total_notif} school circular(s) / notice(s)")

        # Calendar
        holidays = mapped_data.get("holiday_count") or mapped_data.get("total_holidays")
        if holidays is not None:
            lines.append(f"• Calendar: {holidays} holiday(s) scheduled")

        return "\n".join(lines)

    async def generate_response(
        self,
        question: str,
        institution_id: str,
        role: str,
        user_id: str,
        student_context_data: Optional[dict[str, Any]] = None,
    ) -> tuple[str, bool]:
        """
        Generates an academic response via Claude or Cache.

        Returns:
            Tuple of (response_text, is_cache_hit)
        """
        # 1. Check MongoDB persistent 6-hour cache
        try:
            cached_doc = await claude_repo.find_recent_response(
                institution_id=institution_id,
                user_id=user_id,
                question=question,
                max_age_hours=6,
            )
            if cached_doc and cached_doc.get("answer"):
                logger.info(
                    "claude_mongodb_cache_hit_within_6_hours",
                    institution_id=institution_id,
                    user_id=user_id,
                    created_at=str(cached_doc.get("created_at")),
                )
                return cached_doc["answer"], True
        except Exception as exc:
            logger.warning("claude_mongodb_cache_check_failed", error=str(exc))

        # 2. Check local in-memory fallback cache
        cache_key = self._generate_cache_key(institution_id, role, user_id, question)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.info("claude_in_memory_cache_hit", institution_id=institution_id, user_id=user_id)
            return cached["answer"], True

        # Format context
        context_str = self.format_student_context(student_context_data or {})
        user_message_content = f"{context_str}\n\nStudent Question: {question}"

        api_key = settings.claude_api_key
        if not api_key:
            logger.warning("claude_api_key_missing_returning_fallback")
            return (
                "I'm here to help with your school portal! You can ask about your pending fees, "
                "attendance percentage, homework, study materials, notices, or personal profile.",
                False,
            )

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31",
            "content-type": "application/json",
        }

        payload = {
            "model": settings.claude_model,
            "max_tokens": settings.claude_max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": ACADEMIC_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"STUDENT ACADEMIC & INSTITUTION PORTAL CONTEXT:\n{context_str}",
                            "cache_control": {"type": "ephemeral"},
                        },
                        {
                            "type": "text",
                            "text": f"Student Question: {question}",
                        },
                    ],
                }
            ],
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(self.api_url, headers=headers, json=payload)
                duration_ms = (time.time() - start_time) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    answer_text = ""
                    content_blocks = data.get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text":
                            answer_text += block.get("text", "")

                    answer_text = answer_text.strip()
                    usage = data.get("usage", {})
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    cache_created = usage.get("cache_creation_input_tokens", 0)
                    input_toks = usage.get("input_tokens", 0)
                    output_toks = usage.get("output_tokens", 0)
                    tokens_used = {
                        "input_tokens": input_toks,
                        "output_tokens": output_toks,
                        "cache_read_input_tokens": cache_read,
                        "cache_creation_input_tokens": cache_created,
                        "total_tokens": input_toks + output_toks + cache_read + cache_created,
                    }
                    logger.info(
                        "claude_prompt_caching_metrics",
                        cache_read_input_tokens=cache_read,
                        cache_creation_input_tokens=cache_created,
                        input_tokens=input_toks,
                        output_toks=output_toks,
                        duration_ms=int(duration_ms),
                    )

                    # Cache response
                    self._save_to_cache(cache_key, answer_text, tokens_used)

                    # Log to MongoDB
                    await claude_repo.log_response(
                        institution_id=institution_id,
                        user_id=user_id,
                        role=role,
                        question=question,
                        answer=answer_text,
                        model=settings.claude_model,
                        tokens_used=tokens_used,
                        duration_ms=duration_ms,
                    )

                    return answer_text, False
                else:
                    logger.error(
                        "claude_api_error_response",
                        status_code=resp.status_code,
                        response_body=resp.text,
                    )
                    return (
                        "I'm here to help with your school portal! You can ask about your fees, "
                        "attendance, homework assignments, study materials, or school calendar.",
                        False,
                    )

        except Exception as exc:
            logger.error("claude_api_call_exception", error=str(exc))
            return (
                "I'm here to help with your school portal! You can ask about your pending fees, "
                "attendance percentage, homework, study materials, notices, or personal profile.",
                False,
            )


claude_service = ClaudeService()
