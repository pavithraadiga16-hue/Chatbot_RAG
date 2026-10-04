"""
PhinsIQ Chat Request & Response Models
=========================================

PURPOSE:
    Defines the exact shape of data that comes IN to and goes OUT of the
    PhinsIQ chat API endpoint.

WHAT IS A PYDANTIC MODEL?
    A Pydantic model is a Python class that defines the expected shape of data.
    When FastAPI receives a request, it passes the request body through the model.
    If any field is missing, wrong type, or invalid — FastAPI automatically returns
    a 422 error with a precise description of what's wrong.

    EXAMPLE:
        Client sends:
            {"institution_id": 123, "role": "student"}
        Pydantic rejects it:
            {"detail": [{"loc": ["body", "institution_id"], "msg": "str type expected"}]}

    This validation happens BEFORE our code runs — we never see invalid data.

WHY SEPARATE REQUEST AND RESPONSE MODELS?
    Input and output shapes are different:
    - Input: We need institution_id, role, user_id, message
    - Output: We return success, message, metadata

    Mixing them into one model leads to confusion about which fields are
    for input vs. output.

FIELD VALIDATORS:
    Pydantic validators run custom logic on individual fields.
    EXAMPLE: We strip whitespace from messages and reject empty strings.
    This prevents edge cases like "   " (spaces only) reaching the pipeline.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """
    The request body for POST /api/v1/phinsiq/chat

    Every field here is required unless it has a default value.
    FastAPI validates this automatically before our route handler runs.

    FIELD DESIGN DECISIONS:
        institution_id: Lowercase slug (e.g., "sags_school" not "SAGS School")
            Makes MongoDB lookups predictable — no case conversion needed.

        role: Lowercase string (e.g., "student", "staff")
            Validated against the institution's allowed roles.

        user_id: The user's identifier in the ERP system.
            PhinsIQ uses this to make ERP API calls on behalf of the user.
            We never store user credentials — only the ID.

        message: The natural language question.
            We validate it's not empty and not too long.
    """

    institution_id: str = Field(
        ...,
        description="Unique identifier of the institution (e.g., 'sags_school')",
        examples=["sags_school"],
    )

    role: str = Field(
        ...,
        description="User's role within the institution (e.g., 'student', 'staff')",
        examples=["student"],
    )

    user_id: str = Field(
        ...,
        description="User's unique ID in the institution's ERP system",
        examples=["ST123"],
    )

    message: str = Field(
        ...,
        description="The natural language question from the user",
        min_length=1,
        max_length=2000,
        examples=["What is my current attendance percentage?"],
    )

    claude: bool = Field(
        default=True,
        description="Legacy client field; normal general fallback always uses configured local Qwen",
        examples=[True],
    )

    @field_validator("institution_id", "role", "user_id")
    @classmethod
    def strip_and_lowercase(cls, value: str) -> str:
        """
        Normalize identifiers to lowercase with no surrounding whitespace.

        WHY THIS MATTERS:
            "SAGS_SCHOOL", "sags_school", " sags_school " — all refer to the same institution.
            Without normalization, MongoDB lookups would fail for "SAGS_SCHOOL"
            even if "sags_school" exists.

            We normalize at the API boundary so all internal code can assume
            these identifiers are clean lowercase strings.
        """
        return value.strip().lower()

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        """
        Strip leading/trailing whitespace from the message.

        A message of "   " (spaces only) has length 3, passing min_length=1.
        After stripping, it becomes "" which fails min_length=1.
        Pydantic raises a validation error before our code sees the message.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return stripped


class ChatMetadata(BaseModel):
    """
    Debug and observability metadata included in the chat response.

    In production, this should be minimal or omitted for performance.
    In development, it shows exactly how PhinsIQ processed the request.

    This is the transparency layer — it tells the developer/client exactly
    what happened without exposing internal implementation details.
    """

    claude_used: bool = Field(
        default=False,
        description="Legacy compatibility flag; false for the local Qwen provider",
    )

    llm_provider: Optional[str] = Field(
        default=None,
        description="Inference provider used for this response, such as local Ollama",
    )

    llm_model: Optional[str] = Field(
        default=None,
        description="Local model identifier used for this response",
    )

    detected_module: Optional[str] = Field(
        default=None,
        description="The ERP module PhinsIQ identified (e.g., 'attendance', 'fees')",
    )

    detected_action: Optional[str] = Field(
        default=None,
        description="The specific action within the module (e.g., 'percentage')",
    )

    confidence: Optional[float] = Field(
        default=None,
        description="How confident PhinsIQ was about the request interpretation (0.0–1.0)",
    )

    response_type: Optional[str] = Field(
        default=None,
        description=(
            "How the response was generated: "
            "'greeting', 'template', 'rag', 'local_llm', 'fallback'"
        ),
    )

    request_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this request (for log correlation)",
    )


class ChatResponse(BaseModel):
    """
    The response body for POST /api/v1/phinsiq/chat

    DESIGN DECISIONS:
        success: Always present. Clients can check this first.
        message: The natural language answer shown to the user.
        metadata: Optional debug info. Can be null in production to save bandwidth.
        error_code: Only present when success=False. Clients can handle specific errors.

    WHY NOT JUST RETURN A STRING?
        A structured response lets clients:
        1. Check success before displaying the message
        2. Show different UI for errors vs. answers
        3. Log metadata for analytics
        4. Handle specific error codes programmatically
    """

    success: bool = Field(description="Whether the request was processed successfully")

    response: str = Field(
        default="",
        description="The natural language response text (matches message for client compatibility)",
    )

    message: str = Field(
        default="",
        description="The natural language response to show the user",
    )

    route: str = Field(
        default="",
        description="Primary navigation route (e.g. '/homework', '/fees', '/dashboard')",
    )

    routes: list[str] = Field(
        default_factory=list,
        description="Array of navigation routes for all involved modules (e.g. ['/attendance', '/fees'])",
    )

    suggestion_questions: list[str] = Field(
        default_factory=list,
        description="3 contextual follow-up question suggestions",
    )

    sources: Optional[list[str]] = Field(
        default=None,
        description="Source document names when the response came from institutional knowledge",
    )

    metadata: Optional[ChatMetadata] = Field(
        default=None,
        description="Processing metadata. May be null in production.",
    )

    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code. Only present when success=False.",
    )

    @classmethod
    def ok(
        cls,
        message: str,
        routes: Optional[list[str]] = None,
        route: str = "",
        suggestion_questions: Optional[list[str]] = None,
        metadata: Optional[ChatMetadata] = None,
        sources: Optional[list[str]] = None,
    ) -> "ChatResponse":
        """
        Factory method for successful responses with routes array and suggestion questions.
        """
        routes_list = routes if routes is not None else ([route] if route else [])
        primary_route = route or (routes_list[0] if routes_list else "")
        return cls(
            success=True,
            response=message,
            message=message,
            route=primary_route,
            routes=routes_list,
            suggestion_questions=suggestion_questions or [],
            metadata=metadata,
            sources=sources,
        )

    @classmethod
    def error(
        cls,
        message: str,
        error_code: str,
        routes: Optional[list[str]] = None,
        route: str = "",
        suggestion_questions: Optional[list[str]] = None,
    ) -> "ChatResponse":
        """
        Factory method for error responses.
        """
        routes_list = routes if routes is not None else ([route] if route else [])
        primary_route = route or (routes_list[0] if routes_list else "")
        return cls(
            success=False,
            response=message,
            message=message,
            route=primary_route,
            routes=routes_list,
            suggestion_questions=suggestion_questions or [],
            error_code=error_code,
        )
