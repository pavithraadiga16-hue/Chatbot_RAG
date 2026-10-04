"""
PhinsIQ Chat Endpoint
=======================

POST /api/v1/phinsiq/chat

This is the entry point for ALL PhinsIQ queries from any client
(Flutter, website, Postman, etc.).

WHAT CHANGED FROM PHASE 1:
    Phase 1: Returned a placeholder "received your message" response
    Now:      Calls the real pipeline → ERP → template → actual answer

THE CHAT HANDLER IS INTENTIONALLY THIN:
    It does 3 things only:
    1. Log the incoming request
    2. Call pipeline.process()
    3. Return the result

    ALL business logic lives in the pipeline and its stages.
    This separation means:
    - The HTTP layer (this file) can be unit-tested without a pipeline
    - The pipeline can be tested without HTTP
    - Adding a new input channel (websockets, CLI) only needs a new handler,
      not a new copy of all the business logic
"""

import uuid
from fastapi import APIRouter, Request
from app.models.chat import ChatRequest, ChatResponse, ChatMetadata
from app.pipeline.pipeline import pipeline
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="PhinsIQ Chat",
    description=(
        "Send a natural language question to PhinsIQ. "
        "PhinsIQ understands the intent, calls the institution's ERP API, "
        "and returns a natural language answer.\n\n"
        "**Demo institution:** `sjbhs` | **Demo user_id:** `868`"
    ),
    response_description="Natural language answer with optional debug metadata",
    tags=["Chat"],
)
async def chat(
    request: ChatRequest,
    http_request: Request,
) -> ChatResponse:
    """
    Main PhinsIQ chat handler.

    Validates the request (Pydantic does this automatically before this
    function is called), then delegates to the pipeline for all processing.

    Args:
        request:      Validated and normalized ChatRequest
        http_request: Raw Starlette request (for future middleware use)

    Returns:
        ChatResponse with the answer and optional debug metadata
    """
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "chat_request_received",
        request_id=request_id,
        institution_id=request.institution_id,
        role=request.role,
        message_length=len(request.message),
    )

    # Delegate to the pipeline — this is the ONLY call this handler makes
    response = await pipeline.process(request, request_id)

    logger.info(
        "chat_request_completed",
        request_id=request_id,
        success=response.success,
        claude_used=response.metadata.claude_used if response.metadata else False,
        llm_provider=response.metadata.llm_provider if response.metadata else None,
        llm_model=response.metadata.llm_model if response.metadata else None,
        response_type=response.metadata.response_type if response.metadata else "unknown",
    )

    return response
