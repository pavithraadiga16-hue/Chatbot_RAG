"""
PhinsIQ Main Processing Pipeline
=================================

TWO-PATH ARCHITECTURE:
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
    The central orchestrator for all chat queries.
    1. Checks Redis cache (with strict student-data isolation).
    2. Runs Pre-processing (greetings, profanity).
    3. Routes query to ERP/API, RAG, or both (for multi-part queries).
    4. Executes ERP and/or RAG paths.
    5. Combines answers into final natural language response.
    6. Stores response in Redis cache.
    7. Returns response to client.

ZERO CLOUD LLM DEPENDENCY:
    No Gemini, OpenAI, Claude, Anthropic, Qwen, or Ollama fallback.
    All answers are strictly grounded in verified ERP records or retrieved
    institutional documents.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Optional

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
from app.router.query_router import query_router, RoutedIntentPlan, ERP_MODULE_NAMES
from app.services.cache_service import cache_service
from app.understanding.field_detector import field_detector
from app.understanding.module_detector import module_detector
from app.website_engine.engine import website_engine
from app.rag.rag_service import rag_service, RAGAnswer
from app.rag.retriever import rag_retriever

logger = get_logger(__name__)


class PhinsIQPipeline:
    """The simplified PhinsIQ request processing pipeline."""

    async def process(
        self,
        request: ChatRequest,
        request_id: str,
    ) -> ChatResponse:
        """
        Process a chat request through Redis cache, query router, ERP/API, and RAG.
        """
        start_time = time.monotonic()

        try:
            # 1. Preprocessor check (greetings, thanks, goodbyes)
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

            # 2. Plan the query routing to identify ERP vs RAG
            plan = query_router.route(request.message, request.role)

            # 3. Redis Cache Check
            cache_key = cache_service.build_key(
                institution_id=request.institution_id,
                query=request.message,
                user_id=request.user_id if plan.has_erp else None,
                is_student_specific=plan.has_erp,
            )
            cached_payload = await cache_service.get(cache_key)
            if cached_payload:
                logger.info("pipeline_cache_hit_returning", request_id=request_id)
                cached_resp = ChatResponse.model_validate(cached_payload)
                return cached_resp

            # 4. Execute the query
            response = await self._execute(request, request_id, plan)

            # 5. Store result in Redis Cache
            if response.success:
                ttl = settings.redis_ttl_student if plan.has_erp else settings.redis_ttl_general
                await cache_service.set(cache_key, response.model_dump(), ttl_seconds=ttl)

            return response

        except PhinsIQException as e:
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
            logger.info("pipeline_completed", request_id=request_id, duration_ms=duration_ms)

    async def _execute(
        self,
        request: ChatRequest,
        request_id: str,
        plan: Optional[RoutedIntentPlan] = None,
    ) -> ChatResponse:
        """Internal execution of ERP and RAG paths according to routed plan."""
        if plan is None:
            plan = query_router.route(request.message, request.role)

        # Website / Institutional Q&A interception (when query is not an ERP query or role is website)
        if request.role == "website" or not plan.has_erp:
            website_ans = await website_engine.search_and_answer(
                institution_id=request.institution_id,
                question=request.message,
                role=request.role,
            )
            if website_ans and website_ans.confidence >= 0.50 and website_ans.matched_sections_count > 0:
                logger.info("pipeline_website_knowledge_answered", request_id=request_id, confidence=website_ans.confidence)
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

        erp_message: Optional[str] = None
        erp_used_modules: list[str] = []
        erp_field_names: list[str] = []
        rag_message: Optional[str] = None
        rag_sources: list[str] = []
        rag_confidence: float = 0.0

        # ==================================================================
        # PATH A: ERP / API Execution
        # ==================================================================
        if plan.has_erp:
            logger.info("[ROUTER] Executing ERP Path", modules=plan.erp_modules, user_id=request.user_id)
            print(f"[ROUTER] Executing ERP Path for modules: {plan.erp_modules}")

            institution = await institution_repo.get_active_by_id(request.institution_id)
            if not institution:
                raise InstitutionNotFoundError(request.institution_id)

            allowed_modules = await role_repo.get_allowed_modules(request.role)

            if plan.is_overall_overview:
                candidate_modules = [
                    m for m in allowed_modules
                    if m not in ("timetable", "library", "leave", "payroll", "notice", "holiday", "study_material")
                ]
                if "profile" in candidate_modules:
                    candidate_modules.remove("profile")
                    candidate_modules.insert(0, "profile")
            else:
                candidate_modules = [m for m in plan.erp_modules if m in allowed_modules]
                if not candidate_modules:
                    denied = next((m for m in plan.erp_modules if m not in allowed_modules), None)
                    if denied:
                        raise ForbiddenError(role=request.role, module=denied)
                    candidate_modules = plan.erp_modules

            async def _process_module(mod: str):
                logger.info(f"[ERP] Fetching student data for module: {mod}")
                print(f"[ERP] Fetching student data for: {mod}")

                f_defs = await fields_repo.get_field_list(mod)
                f_res = field_detector.detect(request.message, f_defs)

                reg = await registry_repo.get_registry(
                    institution_id=request.institution_id,
                    role=request.role,
                    module=mod,
                    action="summary",
                )
                if not reg:
                    # Provide fallback mock registry so mock provider can execute even if MongoDB registry collection is empty
                    reg = {
                        "institution_id": request.institution_id,
                        "module": mod,
                        "role": request.role,
                        "action": "summary",
                        "request": {"method": "GET", "path": f"api/{mod}", "body_template": {"row_id": "{user_id}"}},
                        "response_root": "",
                        "response_mapping": {},
                    }

                raw_resp = await erp_router.call(
                    institution_config=institution,
                    registry_entry=reg,
                    user_id=request.user_id,
                )

                r_mapping = reg.get("response_mapping", {})
                r_root = reg.get("response_root")
                m_data = response_mapper.map(
                    raw_response=raw_resp,
                    response_mapping=r_mapping,
                    response_root=r_root,
                )

                agg_data = array_aggregator.aggregate(
                    raw_response=raw_resp,
                    field_definitions=f_defs,
                    response_root=r_root,
                    query_text=request.message,
                )
                m_data.update(agg_data)

                # If no specific static field was detected but dynamic event_search/homework_search/notification_search/study_material_search found a match, use it
                if not plan.is_overall_overview:
                    if not f_res.fields and agg_data.get("event_search"):
                        f_res.fields.append("event_search")
                    elif not f_res.fields and agg_data.get("homework_search"):
                        f_res.fields.append("homework_search")
                    elif not f_res.fields and agg_data.get("notification_search"):
                        f_res.fields.append("notification_search")
                    elif not f_res.fields and agg_data.get("study_material_search"):
                        f_res.fields.append("study_material_search")

                tmpl_doc = await templates_repo.get_templates(mod) or {}

                return {
                    "module": mod,
                    "field_result": f_res,
                    "field_definitions": f_defs,
                    "mapped_data": m_data,
                    "templates_doc": tmpl_doc,
                }

            module_outputs = await asyncio.gather(
                *[_process_module(m) for m in candidate_modules],
                return_exceptions=True,
            )

            valid_outputs = [
                out for out in module_outputs
                if out is not None and not isinstance(out, Exception)
            ]

            if valid_outputs:
                all_mapped_data: dict[str, Any] = {}
                all_field_defs: list[dict] = []
                all_fields: list[str] = []
                merged_templates: dict[str, Any] = {
                    "field_templates": {},
                    "summary_template": valid_outputs[0]["templates_doc"].get("summary_template", ""),
                }

                for out in valid_outputs:
                    all_mapped_data.update(out["mapped_data"])
                    all_field_defs.extend(out["field_definitions"])
                    merged_templates["field_templates"].update(
                        out["templates_doc"].get("field_templates", {})
                    )
                    all_fields.extend(out["field_result"].fields)
                    erp_used_modules.append(out["module"])

                erp_field_names = all_fields

                if plan.is_overall_overview:
                    erp_message = self._build_academic_dashboard(all_mapped_data, valid_outputs)
                elif len(valid_outputs) > 1:
                    rendered_parts: list[str] = []
                    for out in valid_outputs:
                        mod_fields = out["field_result"].fields
                        wants_summary = not mod_fields
                        msg = template_engine.render(
                            requested_fields=mod_fields,
                            wants_summary=wants_summary,
                            mapped_data=out["mapped_data"],
                            templates_doc=out["templates_doc"],
                            field_definitions=out["field_definitions"],
                        )
                        if msg and msg.strip():
                            rendered_parts.append(msg.strip())
                    erp_message = "\n\n".join(rendered_parts)
                else:
                    wants_summary = not all_fields
                    erp_message = template_engine.render(
                        requested_fields=all_fields,
                        wants_summary=wants_summary,
                        mapped_data=all_mapped_data,
                        templates_doc=merged_templates,
                        field_definitions=all_field_defs,
                    )

                logger.info("[RESPONSE] ERP result generated")
                print("[RESPONSE] ERP result generated")

        # ==================================================================
        # PATH B: RAG Execution (Documents, Policies, Lecturer Notes, PDFs)
        # ==================================================================
        if plan.has_rag:
            logger.info("[ROUTER] Executing RAG Path", queries=plan.rag_queries)
            print(f"[ROUTER] Executing RAG Path for queries: {plan.rag_queries}")

            rag_parts: list[str] = []
            for q in plan.rag_queries:
                rag_ans = await rag_service.answer(q)
                if rag_ans:
                    rag_parts.append(rag_ans.answer.strip())
                    rag_sources.extend(rag_ans.sources)
                    rag_confidence = max(rag_confidence, rag_ans.confidence)

            if rag_parts:
                rag_message = "\n\n".join(rag_parts)
                rag_sources = list(dict.fromkeys(rag_sources))

        # Holiday Fallback to RAG if ERP had no holiday records
        if plan.is_holiday_query and (not erp_message or "holiday" not in erp_message.lower()):
            holiday_rag = await rag_service.answer("holiday calendar schedule vacation")
            if holiday_rag:
                if not erp_message:
                    rag_message = holiday_rag.answer
                    rag_sources.extend(holiday_rag.sources)
                else:
                    rag_message = holiday_rag.answer
                    rag_sources.extend(holiday_rag.sources)

        # ==================================================================
        # Combine Results & Final Formatting
        # ==================================================================
        final_parts: list[str] = []
        if erp_message and erp_message.strip():
            final_parts.append(erp_message.strip())
        if rag_message and rag_message.strip():
            final_parts.append(rag_message.strip())

        if not final_parts:
            # Neither ERP nor RAG found relevant content
            final_message = "I couldn't find relevant information in the available institutional/academic documents."
            response_type = "rag_no_match"
            sources_out = None
        else:
            final_message = "\n\n".join(final_parts)
            sources_out = rag_sources if rag_sources else None
            if erp_message and rag_message:
                response_type = "multi_intent"
            elif erp_message:
                response_type = "erp"
            else:
                response_type = "rag"

        primary_mod = erp_used_modules[0] if erp_used_modules else (
            "institutional_knowledge" if rag_message else "general"
        )
        is_overall = plan.is_overall_overview or len(erp_used_modules) > 1

        routes = await route_service.get_routes(
            institution_id=request.institution_id,
            modules=erp_used_modules if erp_used_modules else None,
            is_overall_overview=is_overall,
            answer_text=final_message,
        )
        suggestions = suggestion_engine.get_suggestions(
            module=primary_mod if primary_mod in ERP_MODULE_NAMES else "academic_overview",
            is_overall_overview=is_overall,
        )

        return ChatResponse.ok(
            message=final_message,
            routes=routes,
            route=routes[0] if routes else "/dashboard",
            suggestion_questions=suggestions,
            sources=sources_out,
            metadata=ChatMetadata(
                claude_used=False,
                llm_provider=None,
                llm_model=None,
                detected_module=",".join(erp_used_modules) if erp_used_modules else "institutional_knowledge",
                detected_action="summary",
                confidence=rag_confidence if response_type == "rag" else 1.0,
                response_type=response_type,
                request_id=request_id,
            ) if settings.is_development else None,
        )

    def _build_academic_dashboard(
        self,
        mapped_data: dict[str, Any],
        valid_outputs: list[dict[str, Any]],
    ) -> str:
        """Builds a personalized 360-degree Academic Dashboard from live ERP records."""
        from app.router.response_mapper import format_value

        name = mapped_data.get("student_name") or "Student"
        first_name = name.split()[0].title() if name else "there"
        cls = mapped_data.get("class_name") or ""
        sec = mapped_data.get("section") or ""
        adm_no = mapped_data.get("admission_no") or mapped_data.get("student_id") or "N/A"
        class_display = f"{cls}-{sec}" if cls and sec else (cls or "N/A")

        att_pct = mapped_data.get("attendance_percentage") if mapped_data.get("attendance_percentage") is not None else mapped_data.get("percentage")
        pres_days = mapped_data.get("present_count") if mapped_data.get("present_count") is not None else mapped_data.get("present_days")
        tot_days = mapped_data.get("total_classes") if mapped_data.get("total_classes") is not None else mapped_data.get("total_days")
        abs_days = mapped_data.get("absent_count")
        if abs_days is None and tot_days is not None and pres_days is not None:
            abs_days = max(0, tot_days - pres_days)

        if att_pct is not None:
            att_formatted = format_value(att_pct, "percentage")
            att_badge = "✅ (Good!)" if att_pct >= 85.0 else ("⚠️ (Fair)" if att_pct >= 75.0 else "🔴 (Needs Attention)")
            att_detail = f"{att_formatted} {att_badge}"
            if pres_days is not None and tot_days is not None:
                att_detail += f" ({pres_days} attended / {tot_days} total days, {abs_days or 0} absent)"
        else:
            att_detail = "Record in progress"

        pending_hw = mapped_data.get("pending_count") if mapped_data.get("pending_count") is not None else mapped_data.get("pending_homework_count")
        tot_mat = mapped_data.get("total_study_materials")
        pending_fee = mapped_data.get("pending_amount")
        tot_holidays = mapped_data.get("holiday_count") if mapped_data.get("holiday_count") is not None else mapped_data.get("total_holidays")

        strengths = []
        if att_pct is not None and att_pct >= 80.0:
            strengths.append(f"Your attendance is solid at {att_detail.split()[0]}—you're showing strong commitment!")
        if pending_hw == 0:
            strengths.append("All your homework assignments are completed! Excellent discipline.")
        if pending_fee == 0:
            strengths.append("Your school fee account is completely clear with no pending dues.")
        if tot_mat and tot_mat > 0:
            strengths.append(f"You have access to {tot_mat} study portions & resources in your portal.")
        if not strengths:
            strengths.append("You are actively participating in your academic curriculum.")

        focus_areas = []
        if abs_days and abs_days > 0:
            focus_areas.append(f"You've had **{abs_days} absences**—try to minimize these for optimal exam readiness.")
        if pending_hw and pending_hw > 0:
            focus_areas.append(f"You have **{pending_hw} pending homework assignment(s)** requiring your attention.")
        if pending_fee and pending_fee > 0:
            focus_areas.append(f"There is a pending fee balance of **₹{format_value(pending_fee, 'currency')}** to settle.")
        if not focus_areas:
            focus_areas.append("Keep maintaining your consistent daily study routine and homework completion!")

        hw_display = f"⚠️ {pending_hw} Pending" if pending_hw and pending_hw > 0 else "✅ All Completed"
        fee_formatted = format_value(pending_fee, "currency") if pending_fee is not None else "0"
        fee_display = f"₹{fee_formatted} Pending" if pending_fee and pending_fee > 0 else "✅ Settled"

        steps = [
            f"**Boost Attendance** → Aim for 95%+ (consistent attendance is key for top performance!)",
            f"**Check Study Materials** → Review all portions and lesson notes regularly ({tot_mat or 0} available in portal)",
            f"**Stay on Top of Fees** → " + (f"There's a pending fee balance of ₹{format_value(pending_fee, 'currency')} to settle" if pending_fee and pending_fee > 0 else "Fee payments are up to date"),
            f"**Regular Practice** → " + (f"Submit your {pending_hw} pending assignment(s) promptly" if pending_hw and pending_hw > 0 else "Focus on consistent homework completion and revision"),
        ]
        strengths_md = "\n".join(f"- {s}" for s in strengths)
        focus_md = "\n".join(f"- {f}" for f in focus_areas)
        steps_md = "\n".join(f"{i+1}. {st}" for i, st in enumerate(steps))

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
            f"I'm here to support your learning journey! 📚"
        )
        return response


pipeline = PhinsIQPipeline()
