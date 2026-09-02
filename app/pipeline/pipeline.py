"""
PhinsIQ Main Pipeline
=======================

PURPOSE:
    The central orchestrator that wires together all pipeline stages.
    The chat endpoint calls pipeline.process() — that's all it knows.
    The pipeline handles everything else.

PIPELINE STAGES (Phase 1 Implementation):
    1. Pre-processing    — greetings, profanity, normalization
    2. Module Detection  — keyword-based (attendance, fees, exam...)
    3. Field Detection   — which specific data the user wants
    4. Institution Load  — fetch institution config from MongoDB (cached)
    5. API Registry Load — fetch ERP API config from MongoDB (cached)
    6. Fields Load       — fetch field aliases from MongoDB (cached)
    7. Permission Check  — is this module allowed for this role?
    8. ERP API Call      — hit the actual ERP endpoint via httpx
    9. Response Mapping  — translate ERP fields to PhinsIQ names
    10. Template Render  — fill template with real data
    11. Return response

CLAUDE FALLBACK (Phase 10 — placeholder in this phase):
    When module confidence < threshold OR module not found:
    → Claude fallback (not implemented yet, returns helpful message)

IMPORTANT DESIGN DECISION — Why pipeline.process() is async:
    Steps 4, 5, 6 query MongoDB (network I/O).
    Step 8 calls the ERP API (network I/O).
    Without async, the server would block during ALL of these waits.
    With async, other users' requests are processed while we wait.
"""

import asyncio
import time
from typing import Any, Optional

from app.ai.claude_service import claude_service
from app.core.config import settings
from app.core.exceptions import (
    ConfigurationError,
    ForbiddenError,
    InstitutionNotFoundError,
    PhinsIQException,
)
from app.core.logging import get_logger
from app.models.chat import ChatMetadata, ChatRequest, ChatResponse
from app.pipeline.preprocessor import preprocessor
from app.repositories.institution import institution_repo, role_repo
from app.repositories.registry import fields_repo, registry_repo, templates_repo
from app.response.template_engine import template_engine
from app.router.api_router import erp_router
from app.router.array_aggregator import array_aggregator
from app.router.response_mapper import response_mapper
from app.router.route_service import route_service
from app.router.suggestion_engine import suggestion_engine
from app.subject_engine.router import subject_router
from app.understanding.field_detector import field_detector
from app.understanding.module_detector import module_detector
from app.website_engine.engine import website_engine


logger = get_logger(__name__)


# Questions below this confidence go to Claude fallback
MODULE_CONFIDENCE_THRESHOLD = 0.35


class PhinsIQPipeline:
    """
    The main PhinsIQ request processing pipeline.

    Orchestrates all stages from raw user message to final natural language answer.
    One instance is created at application startup and reused for every request.
    """

    async def process(
        self,
        request: ChatRequest,
        request_id: str,
    ) -> ChatResponse:
        """
        Process a chat request through the complete PhinsIQ pipeline.

        Args:
            request:    Validated ChatRequest (institution_id, role, user_id, message)
            request_id: Unique request ID for log correlation

        Returns:
            ChatResponse with the natural language answer and metadata
        """
        start_time = time.monotonic()

        try:
            result = await self._execute(request, request_id)
        except PhinsIQException as e:
            # Our own exceptions — return safe user-facing message
            logger.warning(
                "pipeline_phinsiq_error",
                request_id=request_id,
                error_code=e.error_code,
                detail=e.detail,
            )
            routes = await route_service.get_routes(request.institution_id, modules=None, is_overall_overview=True)
            suggestions = suggestion_engine.get_suggestions()
            return ChatResponse.error(
                message=e.message,
                error_code=e.error_code,
                routes=routes,
                route=routes[0] if routes else "/dashboard",
                suggestion_questions=suggestions,
            )
        except Exception as e:
            # Unexpected error — log full details, return safe message
            logger.error(
                "pipeline_unexpected_error",
                request_id=request_id,
                error=str(e),
                exc_info=True,
            )
            routes = await route_service.get_routes(request.institution_id, modules=None, is_overall_overview=True)
            suggestions = suggestion_engine.get_suggestions()
            return ChatResponse.error(
                message="Something went wrong. Please try again in a moment.",
                error_code="INTERNAL_ERROR",
                routes=routes,
                route=routes[0] if routes else "/dashboard",
                suggestion_questions=suggestions,
            )
        finally:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(
                "pipeline_completed",
                request_id=request_id,
                duration_ms=duration_ms,
            )

        return result

    async def _execute(
        self,
        request: ChatRequest,
        request_id: str,
    ) -> ChatResponse:
        """
        Internal execution — runs all pipeline stages.
        Separated from process() so we can catch exceptions cleanly.
        """

        # ==================================================================
        # STAGE 1: Pre-processing
        # Handles greetings, thanks, goodbyes, profanity — no ERP needed
        # ==================================================================
        preprocess_result = preprocessor.process(request.message)
        if preprocess_result.handled:
            logger.info(
                "pipeline_preprocess_handled",
                request_id=request_id,
                response_type=preprocess_result.response_type,
            )
            routes = await route_service.get_routes(
                institution_id=request.institution_id,
                modules=None,
                is_overall_overview=True,
            )
            suggestions = suggestion_engine.get_suggestions(
                module="academic_overview",
                is_overall_overview=True,
            )
            return ChatResponse.ok(
                message=preprocess_result.response,
                routes=routes,
                route=routes[0] if routes else "/dashboard",
                suggestion_questions=suggestions,
                metadata=ChatMetadata(
                    claude_used=False,
                    response_type=preprocess_result.response_type,
                    request_id=request_id,
                ) if settings.is_development else None,
            )

        normalized_message = preprocess_result.normalized_msg

        # ==================================================================
        # STAGE 1.5: Role == "website" Query Interception
        # If the request role is "website", answer directly from the
        # institution's crawled Knowledge DB with zero ERP / LLM calls.
        # ==================================================================
        if request.role == "website":
            website_ans = await website_engine.search_and_answer(
                institution_id=request.institution_id,
                question=request.message,
                role=request.role,
            )
            logger.info(
                "pipeline_website_role_answered",
                request_id=request_id,
                institution_id=request.institution_id,
                confidence=website_ans.confidence,
            )
            return ChatResponse.ok(
                message=website_ans.formatted_markdown,
                routes=["NA"],
                route="NA",
                suggestion_questions=website_ans.suggestion_questions,
                metadata=ChatMetadata(
                    claude_used=False,
                    detected_module="website_knowledge",
                    detected_action="search",
                    confidence=website_ans.confidence,
                    response_type="website_knowledge",
                    request_id=request_id,
                ) if settings.is_development else None,
            )

        # ==================================================================
        # STAGE 2: Module Detection
        # What is the user's question about? (fees, attendance, exam...)
        # Can detect multiple modules if query is a cross-module question
        # ==================================================================
        module_result = module_detector.detect(normalized_message)

        logger.info(
            "pipeline_module_detected",
            request_id=request_id,
            primary_module=module_result.module,
            all_modules=module_result.modules,
            confidence=module_result.confidence,
        )

        # ==================================================================
        # STAGE 2.1: Local Subject Engine (Mathematics Engine, Science Engine, etc.)
        # If the student's question is an academic problem-solving query
        # and not an administrative ERP query (e.g. fees, calendar, profile, attendance, homework),
        # solve deterministically locally.
        # ==================================================================
        erp_modules = {
            "fees", "attendance", "exam", "calendar", "timetable", "library",
            "leave", "payroll", "homework", "notification", "notice", "profile",
            "study_materials", "gallery", "admission", "transport", "academic_overview"
        }
        is_admin_erp = (
            (module_result.module in erp_modules or module_result.is_overall_overview)
            and module_result.confidence >= MODULE_CONFIDENCE_THRESHOLD
        )

        if not is_admin_erp:
            subject_res = subject_router.route_and_solve(request.message)
            if subject_res and subject_res.handled_locally:
                logger.info(
                    "pipeline_subject_engine_solved",
                    request_id=request_id,
                    subject=subject_res.subject.value,
                    topic=subject_res.topic,
                    intent=subject_res.intent.value,
                    confidence=subject_res.confidence,
                )
                routes = await route_service.get_routes(
                    institution_id=request.institution_id,
                    modules=["study_material"],
                    is_overall_overview=False,
                    answer_text=subject_res.formatted_markdown,
                )
                suggestions = suggestion_engine.get_suggestions(
                    module="study_material",
                    is_overall_overview=False,
                )
                return ChatResponse.ok(
                    message=subject_res.formatted_markdown,
                    routes=["NA"],
                    route="NA",
                    suggestion_questions=suggestions,
                    metadata=ChatMetadata(
                        claude_used=False,
                        detected_module=f"{subject_res.subject.value}_engine",
                        detected_action=subject_res.intent.value.lower(),
                        confidence=subject_res.confidence,
                        response_type=f"{subject_res.subject.value}_engine",
                        request_id=request_id,
                    ) if settings.is_development else None,
                )

        # ==================================================================
        # STAGE 2.2: Website Knowledge Search (for General School Questions)
        # If not an ERP module, check if the question relates to the
        # institution's crawled website (overview, history, motto, facilities)
        # ==================================================================
        if not is_admin_erp:
            website_ans = await website_engine.search_and_answer(
                institution_id=request.institution_id,
                question=request.message,
                role=request.role,
            )
            if website_ans and website_ans.confidence >= 0.50 and website_ans.matched_sections_count > 0:
                logger.info(
                    "pipeline_website_knowledge_matched",
                    request_id=request_id,
                    institution_id=request.institution_id,
                    confidence=website_ans.confidence,
                )
                return ChatResponse.ok(
                    message=website_ans.formatted_markdown,
                    routes=["NA"],
                    route="NA",
                    suggestion_questions=website_ans.suggestion_questions,
                    metadata=ChatMetadata(
                        claude_used=False,
                        detected_module="website_knowledge",
                        detected_action="search",
                        confidence=website_ans.confidence,
                        response_type="website_knowledge",
                        request_id=request_id,
                    ) if settings.is_development else None,
                )

        # If confidence too low, fall back to Claude (Phase 10)
        if not module_result.module or module_result.confidence < MODULE_CONFIDENCE_THRESHOLD:
            return await self._execute_claude_fallback(
                request=request,
                request_id=request_id,
                reason="low_module_confidence",
                confidence=module_result.confidence,
            )




        # ==================================================================
        # STAGE 3: Institution Load
        # Load institution configuration from MongoDB (cached)
        # ==================================================================
        institution = await institution_repo.get_active_by_id(request.institution_id)
        if not institution:
            raise InstitutionNotFoundError(request.institution_id)

        # ==================================================================
        # STAGE 4: Permission Check & Module Selection
        # Filter detected modules to those accessible for this role
        # ==================================================================
        allowed_modules = await role_repo.get_allowed_modules(request.role)

        if module_result.is_overall_overview or module_result.module == "academic_overview":
            # For 360-degree overview, dynamically query all allowed modules configured for the student
            candidate_modules = [
                m for m in allowed_modules
                if m not in ("timetable", "library", "leave", "payroll", "notice", "holiday", "study_material")
            ]
            # Ensure "profile" is processed first to capture student identity
            if "profile" in candidate_modules:
                candidate_modules.remove("profile")
                candidate_modules.insert(0, "profile")
        else:
            candidate_modules = [m for m in module_result.modules if m in allowed_modules]
            if not candidate_modules:
                if module_result.module and module_result.module not in allowed_modules:
                    raise ForbiddenError(role=request.role, module=module_result.module)
                candidate_modules = [module_result.module]

        # ==================================================================
        # STAGES 5-8b: Concurrent Module Processing (Parallel ERP calls)
        # Process all qualifying modules in parallel with asyncio.gather()
        # ==================================================================
        async def _process_single_module(mod: str):
            # STAGE 5: Field detection for this module
            f_defs = await fields_repo.get_field_list(mod)
            f_res = field_detector.detect(normalized_message, f_defs)

            # STAGE 6: Load API Registry
            reg = await registry_repo.get_registry(
                institution_id=request.institution_id,
                role=request.role,
                module=mod,
                action="summary",
            )
            if not reg:
                logger.warning("no_registry_for_module", institution_id=request.institution_id, module=mod)
                return None

            # STAGE 7: Call ERP API (or mock fallback)
            raw_resp = await erp_router.call(
                institution_config=institution,
                registry_entry=reg,
                user_id=request.user_id,
            )

            # STAGE 8: Map Response
            r_mapping = reg.get("response_mapping", {})
            r_root = reg.get("response_root")
            m_data = response_mapper.map(
                raw_response=raw_resp,
                response_mapping=r_mapping,
                response_root=r_root,
            )

            # STAGE 8b: Array Aggregation
            agg_data = array_aggregator.aggregate(
                raw_response=raw_resp,
                field_definitions=f_defs,
                response_root=r_root,
                query_text=normalized_message,
            )
            m_data.update(agg_data)

            # If no specific static field was detected but dynamic event_search/homework_search/notification_search/study_material_search found a match, use it
            if not module_result.is_overall_overview and module_result.module != "academic_overview":
                if not f_res.fields and agg_data.get("event_search"):
                    f_res.fields.append("event_search")
                elif not f_res.fields and agg_data.get("homework_search"):
                    f_res.fields.append("homework_search")
                elif not f_res.fields and agg_data.get("notification_search"):
                    f_res.fields.append("notification_search")
                elif not f_res.fields and agg_data.get("study_material_search"):
                    f_res.fields.append("study_material_search")

            # STAGE 9 Prep: Load templates
            tmpl_doc = await templates_repo.get_templates(mod) or {}

            return {
                "module": mod,
                "field_result": f_res,
                "field_definitions": f_defs,
                "mapped_data": m_data,
                "templates_doc": tmpl_doc,
            }

        # Execute all modules concurrently
        module_outputs = await asyncio.gather(
            *[_process_single_module(m) for m in candidate_modules],
            return_exceptions=True
        )

        valid_outputs = [
            out for out in module_outputs
            if out is not None and not isinstance(out, Exception)
        ]

        if not valid_outputs:
            # Fall back to Claude AI or FastAPI academic synthesizer when requested module has no registry
            return await self._execute_claude_fallback(
                request=request,
                request_id=request_id,
                reason="unconfigured_or_unregistered_modules",
                confidence=module_result.confidence,
            )

        # ==================================================================
        # STAGE 9: Multi-Module Merging & Template Rendering
        # Merge field detections, mapped data, and templates across modules
        # ==================================================================
        active_outputs = valid_outputs

        all_requested_fields: list[str] = []
        all_mapped_data: dict[str, Any] = {}
        all_field_defs: list[dict] = []
        merged_templates: dict[str, Any] = {
            "field_templates": {},
            "summary_template": active_outputs[0]["templates_doc"].get("summary_template", "") if active_outputs else ""
        }

        for out in active_outputs:
            all_mapped_data.update(out["mapped_data"])
            all_field_defs.extend(out["field_definitions"])
            merged_templates["field_templates"].update(
                out["templates_doc"].get("field_templates", {})
            )
            if not module_result.is_overall_overview and module_result.module != "academic_overview":
                all_requested_fields.extend(out["field_result"].fields)

        if module_result.is_overall_overview or module_result.module == "academic_overview":
            final_message = self._build_academic_dashboard(all_mapped_data, valid_outputs)
        elif len(valid_outputs) > 1:
            rendered_parts: list[str] = []
            for out in valid_outputs:
                mod_fields = out["field_result"].fields
                wants_summary = not mod_fields
                mod_msg = template_engine.render(
                    requested_fields=mod_fields,
                    wants_summary=wants_summary,
                    mapped_data=out["mapped_data"],
                    templates_doc=out["templates_doc"],
                    field_definitions=out["field_definitions"],
                )
                if mod_msg and mod_msg.strip():
                    rendered_parts.append(mod_msg.strip())
            final_message = "\n\n".join(rendered_parts)
        else:
            wants_summary = not all_requested_fields
            final_message = template_engine.render(
                requested_fields=all_requested_fields,
                wants_summary=wants_summary,
                mapped_data=all_mapped_data,
                templates_doc=merged_templates,
                field_definitions=all_field_defs,
            )

        used_modules = [out["module"] for out in active_outputs]
        logger.info(
            "pipeline_response_generated",
            request_id=request_id,
            modules=used_modules,
            fields_used=all_requested_fields,
            claude_used=False,
        )

        primary_mod = used_modules[0] if used_modules else module_result.module
        is_overall = module_result.is_overall_overview or module_result.module == "academic_overview" or len(used_modules) > 1
        routes = await route_service.get_routes(
            institution_id=request.institution_id,
            modules=used_modules if used_modules else ([primary_mod] if primary_mod else []),
            is_overall_overview=is_overall,
            answer_text=final_message,
        )
        suggestions = suggestion_engine.get_suggestions(
            module=primary_mod,
            is_overall_overview=is_overall,
        )

        return ChatResponse.ok(
            message=final_message,
            routes=routes,
            route=routes[0] if routes else "/dashboard",
            suggestion_questions=suggestions,
            metadata=ChatMetadata(
                claude_used=False,
                detected_module=used_modules[0] if len(used_modules) == 1 else ",".join(used_modules),
                detected_action="summary",
                confidence=module_result.confidence,
                response_type="template",
                request_id=request_id,
            ) if settings.is_development else None,
        )

    def _build_academic_dashboard(
        self,
        mapped_data: dict[str, Any],
        valid_outputs: list[dict[str, Any]],
    ) -> str:
        """
        Builds a personalized, encouraging Academic Progress & Performance Snapshot
        (matching Claude's advisory style with real dynamic ERP student data).
        """
        from app.router.response_mapper import format_value

        # 1. Student Identity Header
        name = mapped_data.get("student_name") or "Student"
        first_name = name.split()[0].title() if name else "there"
        cls = mapped_data.get("class_name") or ""
        sec = mapped_data.get("section") or ""
        adm_no = mapped_data.get("admission_no") or mapped_data.get("student_id") or "N/A"
        class_display = f"{cls}-{sec}" if cls and sec else (cls or "N/A")

        # 2. Attendance Status
        att_pct = mapped_data.get("attendance_percentage") if mapped_data.get("attendance_percentage") is not None else mapped_data.get("percentage")
        pres_days = mapped_data.get("present_count") if mapped_data.get("present_count") is not None else mapped_data.get("present_days")
        tot_days = mapped_data.get("total_classes") if mapped_data.get("total_classes") is not None else mapped_data.get("total_days")
        abs_days = mapped_data.get("absent_count")
        if abs_days is None and tot_days is not None and pres_days is not None:
            abs_days = max(0, tot_days - pres_days)

        if att_pct is not None:
            att_formatted = format_value(att_pct, 'percentage')
            if att_pct >= 85.0:
                att_badge = "✅ (Good!)"
            elif att_pct >= 75.0:
                att_badge = "⚠️ (Fair)"
            else:
                att_badge = "🔴 (Needs Attention)"

            att_detail = f"{att_formatted} {att_badge}"
            if pres_days is not None and tot_days is not None:
                att_detail += f" (You've attended {pres_days} out of {tot_days} days)"
        else:
            att_detail = "Record in progress"

        # 3. Homework
        pending_hw = mapped_data.get("pending_count") if mapped_data.get("pending_count") is not None else mapped_data.get("pending_homework_count")
        tot_hw = mapped_data.get("total_homework") if mapped_data.get("total_homework") is not None else mapped_data.get("total_homework_count")

        # 4. Study Materials
        tot_mat = mapped_data.get("total_study_materials")

        # 5. Fees
        pending_fee = mapped_data.get("pending_amount")
        paid_fee = mapped_data.get("paid_amount")
        tot_fee = mapped_data.get("total_fee")

        # 6. Notifications & Calendar
        tot_notif = mapped_data.get("total_notifications")
        tot_holidays = mapped_data.get("holiday_count") if mapped_data.get("holiday_count") is not None else mapped_data.get("total_holidays")

        # Dynamic Strengths
        strengths = []
        if att_pct is not None and att_pct >= 80.0:
            strengths.append(f"Your attendance is solid at {att_formatted}—you're showing commitment to class!")
        if pending_hw == 0:
            strengths.append("All your homework assignments are completed! Excellent discipline.")
        if pending_fee == 0:
            strengths.append("Your school fee account is completely clear with no pending dues.")
        if tot_mat and tot_mat > 0:
            strengths.append(f"You have access to {tot_mat} study portions & resources in your portal.")
        if not strengths:
            strengths.append("You are actively participating in your academic curriculum.")

        # Dynamic Focus Areas
        focus_areas = []
        if abs_days and abs_days > 0:
            focus_areas.append(f"You've had **{abs_days} absences**—try to minimize these for optimal exam readiness.")
        if pending_hw and pending_hw > 0:
            focus_areas.append(f"You have **{pending_hw} pending homework assignment(s)** that require your attention.")
        if tot_mat == 0:
            focus_areas.append("No study materials uploaded yet in the portal—make sure you're accessing all lesson notes shared by teachers.")
        if pending_fee and pending_fee > 0:
            focus_areas.append(f"There is a pending fee balance of **₹{format_value(pending_fee, 'currency')}** to settle.")
        if not focus_areas:
            focus_areas.append("Keep maintaining your consistent daily study routine and homework completion!")

        # Dynamic Improvement Steps
        steps = [
            f"**Boost Attendance** → Aim for 95%+ (consistent attendance is key for top performance!)",
            f"**Check Study Materials** → Review all portions and lesson notes regularly ({tot_mat or 0} available in portal)",
            f"**Stay on Top of Fees** → " + (f"There's a pending fee balance of ₹{format_value(pending_fee, 'currency')} to settle" if pending_fee and pending_fee > 0 else "Fee payments are up to date"),
            f"**Regular Practice** → " + (f"Submit your {pending_hw} pending assignment(s) promptly" if pending_hw and pending_hw > 0 else "Focus on consistent homework completion and revision"),
        ]

        strengths_md = "\n".join(f"- {s}" for s in strengths)
        focus_md = "\n".join(f"- {f}" for f in focus_areas)
        steps_md = "\n".join(f"{i+1}. {st}" for i, st in enumerate(steps))

        hw_display = f"⚠️ {pending_hw} Pending" if pending_hw and pending_hw > 0 else "✅ All Completed"
        fee_formatted = format_value(pending_fee, "currency") if pending_fee is not None else "0"
        fee_display = f"₹{fee_formatted} Pending" if pending_fee and pending_fee > 0 else "✅ Settled"

        response = (
            f"# Hey {first_name}! 👋\n\n"
            f"Here is your **academic progress snapshot** based on your school records:\n\n"
            f"## 📊 Your Current Status:\n\n"
            f"| Metric | Details |\n"
            f"|--------|---------|\n"
            f"| **Student Name** | {name} |\n"
            f"| **Class** | {class_display} |\n"
            f"| **Admission No** | {adm_no} |\n"
            f"| **Attendance** | {att_detail} |\n"
            f"| **Homework** | {hw_display} |\n"
            f"| **Fee Status** | {fee_display} |\n\n"
            f"## 💡 Here's What I Notice:\n\n"
            f"✅ **Your Strengths:**\n{strengths_md}\n\n"
            f"⚠️ **Areas to Focus On:**\n{focus_md}\n\n"
            f"## 🚀 How to Improve Further:\n\n{steps_md}\n\n"
            f"---\n\n"
            f"**Want help with:**\n"
            f"• Your **holiday calendar** ({tot_holidays or 0} holidays scheduled)?\n"
            f"• Specific **homework or study portions** ({tot_mat or 0} resources available)?\n"
            f"• **Fee details** or payment receipt info?\n\n"
            f"I'm here to support your learning journey! 📚"
        )
        return response

    async def _execute_claude_fallback(
        self,
        request: ChatRequest,
        request_id: str,
        reason: str,
        confidence: float,
    ) -> ChatResponse:
        """
        Production Claude AI Fallback:
        1. Loads institution configuration.
        2. Queries active allowed student modules in parallel to assemble student ERP context.
        3. Invokes ClaudeService (with caching, academic guardrails, and max_tokens=500).
        4. Logs to MongoDB claude_responses collection.
        5. Returns ChatResponse with claude_used=True.
        """
        logger.info(
            "pipeline_claude_fallback_triggered",
            request_id=request_id,
            reason=reason,
            confidence=confidence,
        )

        # Interception Guard: Check if Subject Engine can solve locally (Zero Claude call)
        subject_res = subject_router.route_and_solve(request.message)
        if subject_res and subject_res.handled_locally:
            logger.info(
                "claude_fallback_intercepted_by_subject_engine",
                request_id=request_id,
                subject=subject_res.subject.value,
                topic=subject_res.topic,
            )
            suggestions = suggestion_engine.get_suggestions(
                module="study_material",
                is_overall_overview=False,
            )
            return ChatResponse.ok(
                message=subject_res.formatted_markdown,
                routes=["NA"],
                route="NA",
                suggestion_questions=suggestions,
                metadata=ChatMetadata(
                    claude_used=False,
                    detected_module=f"{subject_res.subject.value}_engine",
                    detected_action=subject_res.intent.value.lower(),
                    confidence=subject_res.confidence,
                    response_type=f"{subject_res.subject.value}_engine",
                    request_id=request_id,
                ) if settings.is_development else None,
            )


        institution = await institution_repo.get_active_by_id(request.institution_id)
        if not institution:
            institution = {"_id": request.institution_id, "name": request.institution_id}


        # Gather student context across active modules in parallel
        allowed_modules = await role_repo.get_allowed_modules(request.role)
        candidate_modules = [
            m for m in allowed_modules
            if m not in ("timetable", "library", "leave", "payroll", "notice", "holiday", "study_material")
        ]
        if "profile" in candidate_modules:
            candidate_modules.remove("profile")
            candidate_modules.insert(0, "profile")

        async def _fetch_module_data(mod: str):
            f_defs = await fields_repo.get_field_list(mod)
            reg = await registry_repo.get_registry(
                institution_id=request.institution_id,
                role=request.role,
                module=mod,
                action="summary",
            )
            if not reg:
                return {}
            try:
                raw_resp = await erp_router.call(
                    institution_config=institution,
                    registry_entry=reg,
                    user_id=request.user_id,
                )
                m_data = response_mapper.map(
                    raw_response=raw_resp,
                    response_mapping=reg.get("response_mapping", {}),
                    response_root=reg.get("response_root"),
                )
                agg_data = array_aggregator.aggregate(
                    raw_response=raw_resp,
                    field_definitions=f_defs,
                    response_root=reg.get("response_root"),
                    query_text=request.message,
                )
                m_data.update(agg_data)
                return m_data
            except Exception as exc:
                logger.warning("claude_fallback_context_fetch_error", module=mod, error=str(exc))
                return {}

        context_results = await asyncio.gather(
            *[_fetch_module_data(m) for m in candidate_modules],
            return_exceptions=True
        )

        consolidated_context: dict[str, Any] = {}
        for res in context_results:
            if isinstance(res, dict):
                consolidated_context.update(res)

        # Check if Claude is disabled by client request
        if not getattr(request, "claude", True):
            logger.info("claude_disabled_by_request_fastapi_only", request_id=request_id)
            answer = self._build_academic_dashboard(consolidated_context, [])
            routes = await route_service.get_routes(
                institution_id=request.institution_id,
                modules=list(candidate_modules) if candidate_modules else None,
                is_overall_overview=True,
            )
            suggestions = suggestion_engine.get_suggestions(
                module="academic_overview",
                is_overall_overview=True,
            )
            return ChatResponse.ok(
                message=answer,
                routes=routes,
                route=routes[0] if routes else "/dashboard",
                suggestion_questions=suggestions,
                metadata=ChatMetadata(
                    claude_used=False,
                    confidence=confidence,
                    response_type="fastapi_deterministic",
                    request_id=request_id,
                ) if settings.is_development else None,
            )

        # Call Claude service
        answer, is_cached = await claude_service.generate_response(
            question=request.message,
            institution_id=request.institution_id,
            role=request.role,
            user_id=request.user_id,
            student_context_data=consolidated_context,
        )

        routes = await route_service.get_routes(
            institution_id=request.institution_id,
            modules=list(candidate_modules) if candidate_modules else None,
            is_overall_overview=True,
            answer_text=answer,
        )
        suggestions = suggestion_engine.get_suggestions(
            claude_used=True,
        )

        return ChatResponse.ok(
            message=answer,
            routes=routes,
            route=routes[0] if routes else "/dashboard",
            suggestion_questions=suggestions,
            metadata=ChatMetadata(
                claude_used=True,
                confidence=confidence,
                response_type="claude" if not is_cached else "claude_cached",
                request_id=request_id,
            ) if settings.is_development else None,
        )


# Single pipeline instance shared across all requests
# (stateless — safe to share)
pipeline = PhinsIQPipeline()
