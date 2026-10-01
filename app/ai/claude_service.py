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
    "• Assist students, parents, and educators with all education-related questions: subjects, mathematics, "
    "science, physics, chemistry, biology, homework help, conceptual explanations, study guidance, exam tips, "
    "and general academic queries.\n"
    "• Assist with school portal services and student records: attendance, fees, homework, study materials, "
    "circulars, exams, and calendar events.\n"
    "• When available, utilize the provided Student ERP Context to deliver accurate, personalized, and warm answers.\n\n"
    "CORE GUIDELINES:\n"
    "1. Readily explain concepts, solve academic problems, and answer all educational inquiries across any subject.\n"
    "2. If asked whether you know a subject or topic (e.g. 'do you know mathematics?'), warmly confirm your capabilities "
    "and invite the student to ask their question.\n"
    "3. When asked conversational identity questions ('who am i?', 'do you know me?'), identify the student using the Student Context if available.\n"
    "4. If asked questions completely outside education or the school portal (e.g. video games, celebrity gossip, hacking), "
    "politely steer the student back to their studies, homework, or portal records.\n"
    "5. Keep responses concise, clear, polite, and formatted with clean Markdown. Do not exceed 500 tokens."
)


class ClaudeService:
    """Async client and manager for Claude AI Fallback."""

    def __init__(self, cache_ttl_seconds: int = 600) -> None:
        self.cache_ttl = cache_ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}
        # Legacy Claude API URL (commented out):
        # self.api_url = "https://api.anthropic.com/v1/messages"
        self.api_url = settings.llm_api_url

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
        force_fresh: bool = False,
    ) -> tuple[str, bool]:
        """
        Generates an academic response via LLM API or Cache.

        Args:
            force_fresh: When True (default), bypasses cache and directly hits LLM API,
                         saving every call to the database table.

        Returns:
            Tuple of (response_text, is_cache_hit)
        """
        if not force_fresh:
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

        cache_key = self._generate_cache_key(institution_id, role, user_id, question)

        # Format context
        context_str = self.format_student_context(student_context_data or {})

        # ---------------------------------------------------------------------
        # 1. Primary Fallback: RunPod Qwen3:14b / Ollama API (/api/generate)
        # ---------------------------------------------------------------------
        llm_url = settings.llm_api_url
        if llm_url:
            prompt_parts = [ACADEMIC_SYSTEM_PROMPT.strip()]
            if context_str and context_str.strip() != "=== VERIFIED STUDENT ERP RECORDS ===":
                prompt_parts.append(f"STUDENT ACADEMIC & INSTITUTION PORTAL CONTEXT:\n{context_str.strip()}")
            prompt_parts.append(f"Student Question: {question.strip()}")
            prompt_parts.append("Answer:")
            full_prompt = "\n\n".join(prompt_parts)

            payload = {
                "model": settings.llm_model,
                "prompt": full_prompt,
                "stream": settings.llm_stream,
                "think": settings.llm_think,
                "options": {
                    "num_predict": settings.llm_num_predict,
                    "temperature": settings.llm_temperature,
                },
            }

            start_time = time.time()
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        llm_url,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                    )
                    duration_ms = (time.time() - start_time) * 1000

                    if resp.status_code == 200:
                        data = resp.json()
                        answer_text = (data.get("response") or "").strip()
                        if not answer_text and isinstance(data.get("message"), dict):
                            answer_text = (data["message"].get("content") or "").strip()

                        if answer_text:
                            prompt_eval_count = data.get("prompt_eval_count", 0)
                            eval_count = data.get("eval_count", 0)
                            tokens_used = {
                                "input_tokens": prompt_eval_count,
                                "output_tokens": eval_count,
                                "total_tokens": prompt_eval_count + eval_count,
                            }

                            logger.info(
                                "llm_qwen_response_success",
                                model=settings.llm_model,
                                prompt_eval_count=prompt_eval_count,
                                eval_count=eval_count,
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
                                model=settings.llm_model,
                                tokens_used=tokens_used,
                                duration_ms=duration_ms,
                            )

                            return answer_text, False
                    else:
                        logger.error(
                            "llm_api_error_response",
                            status_code=resp.status_code,
                            response_body=resp.text,
                        )
            except Exception as exc:
                logger.error("llm_api_call_exception", error=str(exc))

        # ---------------------------------------------------------------------
        # 2. Claude API Integration (Removed / Commented out as requested)
        # ---------------------------------------------------------------------
        # In favor of the RunPod Qwen3:14b Ollama API (/api/generate), direct Claude calls are disabled:
        # api_key = getattr(settings, "claude_api_key", "")
        # if api_key:
        #     ... [Claude API Integration Removed] ...

        # Default fallback if all remote services are unreachable
        return (
            "I'm here to help with your school portal! You can ask about your pending fees, "
            "attendance percentage, homework, study materials, notices, or personal profile.",
            False,
        )


claude_service = ClaudeService()
