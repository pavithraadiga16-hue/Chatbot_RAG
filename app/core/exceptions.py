"""
PhinsIQ Exception Hierarchy
==============================

PURPOSE:
    Defines the complete set of custom exceptions used throughout PhinsIQ.
    Having a custom exception hierarchy allows centralized error handling
    in one place (the exception handler in main.py).

WHY CUSTOM EXCEPTIONS INSTEAD OF BUILT-IN ONES?
    Built-in Python exceptions (ValueError, RuntimeError) carry no structured
    information. Our custom exceptions carry:
    - A human-friendly message (shown to users in safe form)
    - An HTTP status code
    - An error code string (for client-side error handling)
    - Optional debug detail (only shown in development mode)

    EXAMPLE WITHOUT CUSTOM EXCEPTIONS:
        try:
            ...
        except Exception as e:
            return {"error": str(e)}  # Might expose internal details!

    EXAMPLE WITH CUSTOM EXCEPTIONS:
        try:
            ...
        except PhinsIQException as e:
            return {"error": e.user_message, "code": e.error_code}

HOW IT WORKS AT RUNTIME:
    1. Any module raises a PhinsIQException subclass
    2. FastAPI's exception handler (registered in main.py) catches it
    3. The handler formats a safe, consistent JSON error response
    4. The client receives a clean error without stack traces

ARCHITECTURE DECISION:
    We use a flat hierarchy (all exceptions inherit from PhinsIQException)
    rather than a deep tree. This keeps it simple and easy to catch-all
    with a single handler.
"""

from typing import Optional


class PhinsIQException(Exception):
    """
    Base exception for all PhinsIQ errors.

    All custom exceptions inherit from this class. This allows catching any
    PhinsIQ-specific error with a single `except PhinsIQException` block.

    Args:
        message: User-friendly error message (safe to show to end users)
        error_code: Machine-readable error identifier for client-side handling
        status_code: HTTP status code to return
        detail: Technical detail for debugging (only shown in development mode)
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        detail: Optional[str] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


# =============================================================================
# Institution Errors
# =============================================================================


class InstitutionNotFoundError(PhinsIQException):
    """
    Raised when a request references an institution that doesn't exist in MongoDB.

    WHY THIS MATTERS:
        With 150+ institutions, a typo in institution_id is common.
        This error gives a clear, actionable message instead of a generic 500.
    """

    def __init__(self, institution_id: str) -> None:
        super().__init__(
            message="Institution not found or not active.",
            error_code="INSTITUTION_NOT_FOUND",
            status_code=404,
            detail=f"No active institution found with id: {institution_id}",
        )


class InstitutionInactiveError(PhinsIQException):
    """Raised when the institution exists but is marked inactive."""

    def __init__(self, institution_id: str) -> None:
        super().__init__(
            message="This institution is currently inactive.",
            error_code="INSTITUTION_INACTIVE",
            status_code=403,
            detail=f"Institution {institution_id} has status 'inactive'",
        )


# =============================================================================
# Permission / Authorization Errors
# =============================================================================


class UnauthorizedError(PhinsIQException):
    """
    Raised when a request is made without a valid authentication token.

    HTTP 401 Unauthorized: "Who are you? I don't know you."
    """

    def __init__(self, detail: Optional[str] = None) -> None:
        super().__init__(
            message="Authentication required.",
            error_code="UNAUTHORIZED",
            status_code=401,
            detail=detail,
        )


class ForbiddenError(PhinsIQException):
    """
    Raised when a user is authenticated but doesn't have permission for the action.

    HTTP 403 Forbidden: "I know who you are, but you can't do this."
    EXAMPLE: A student trying to access staff payroll data.
    """

    def __init__(self, role: str, module: str) -> None:
        super().__init__(
            message="You don't have permission to access this.",
            error_code="FORBIDDEN",
            status_code=403,
            detail=f"Role '{role}' does not have access to module '{module}'",
        )


# =============================================================================
# Request Understanding Errors
# =============================================================================


class LowConfidenceError(PhinsIQException):
    """
    Raised when the system cannot confidently understand the user's request
    AND Claude fallback is disabled or also fails.

    This is NOT a system error — it's an expected case when a user asks
    something completely outside PhinsIQ's knowledge domain.
    """

    def __init__(self, confidence: float) -> None:
        super().__init__(
            message=(
                "I'm not sure I understood your question. "
                "Could you rephrase it?"
            ),
            error_code="LOW_CONFIDENCE",
            status_code=422,
            detail=f"Confidence score below threshold: {confidence:.2f}",
        )


class UnsupportedTopicError(PhinsIQException):
    """
    Raised when the user asks about a topic that PhinsIQ cannot handle
    for their role, even after Claude fallback.

    EXAMPLE: A student asking "How do I fix my computer?"
    """

    def __init__(self) -> None:
        super().__init__(
            message=(
                "I can only help with institution-related queries. "
                "Please ask about attendance, fees, exams, or similar topics."
            ),
            error_code="UNSUPPORTED_TOPIC",
            status_code=422,
        )


# =============================================================================
# ERP API Errors
# =============================================================================


class ERPAPIError(PhinsIQException):
    """
    Raised when the ERP API call fails for any reason.

    WHY WRAP ERP ERRORS IN OUR OWN EXCEPTION?
        The ERP might return any kind of error (500, 503, timeout, invalid JSON).
        By catching all of these and raising ERPAPIError, the rest of PhinsIQ
        only needs to handle one exception type — not dozens of HTTP error codes.
    """

    def __init__(
        self,
        institution_id: str,
        module: str,
        reason: str,
        status_code: int = 503,
    ) -> None:
        super().__init__(
            message="I'm having trouble fetching your information right now. Please try again in a moment.",
            error_code="ERP_API_ERROR",
            status_code=503,
            detail=f"ERP call failed for {institution_id}/{module}: {reason}",
        )


class ERPTimeoutError(ERPAPIError):
    """Raised specifically when the ERP API call exceeds the configured timeout."""

    def __init__(self, institution_id: str, module: str, timeout_seconds: int) -> None:
        super().__init__(
            institution_id=institution_id,
            module=module,
            reason=f"Timeout after {timeout_seconds}s",
        )


class ERPResponseMappingError(PhinsIQException):
    """
    Raised when the ERP returns a valid response but we cannot map it
    to our expected field names using the api_registry configuration.

    EXAMPLE: ERP returns {"attendPct": 94} but api_registry maps "attendance_percentage"
    to "attendancePercentage". PhinsIQ cannot find the expected field.

    WHY THIS IS SEPARATE FROM ERPAPIError:
        The ERP call succeeded — the institution's API is working.
        The MAPPING is wrong — the api_registry configuration needs updating.
        These two failure modes require different fixes.
    """

    def __init__(self, field: str, institution_id: str, module: str) -> None:
        super().__init__(
            message="I received a response but couldn't extract the requested information.",
            error_code="ERP_MAPPING_ERROR",
            status_code=502,
            detail=f"Cannot map field '{field}' for {institution_id}/{module}. Check api_registry configuration.",
        )


# =============================================================================
# MongoDB / Configuration Errors
# =============================================================================


class ConfigurationError(PhinsIQException):
    """
    Raised when required configuration is missing from MongoDB.

    EXAMPLE: A student asks about "library" but no api_registry entry exists
    for sags_school/student/library. The module exists but isn't configured.

    This is a DEVELOPER/ADMIN error, not a user error.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(
            message="This feature is not yet configured for your institution.",
            error_code="CONFIGURATION_ERROR",
            status_code=501,
            detail=detail,
        )


class DatabaseUnavailableError(PhinsIQException):
    """Raised when MongoDB is unreachable."""

    def __init__(self) -> None:
        super().__init__(
            message="The service is temporarily unavailable. Please try again later.",
            error_code="DATABASE_UNAVAILABLE",
            status_code=503,
        )


# =============================================================================
# Claude AI Errors
# =============================================================================


class ClaudeUnavailableError(PhinsIQException):
    """
    Raised when Claude is needed (complex request) but is unavailable —
    either because the API key is not configured or Claude's API is down.

    This is a GRACEFUL DEGRADATION case — PhinsIQ should return a helpful
    message rather than an error code.
    """

    def __init__(self) -> None:
        super().__init__(
            message=(
                "I'm having trouble processing this complex question right now. "
                "Please try a more specific question, like 'What is my attendance percentage?'"
            ),
            error_code="CLAUDE_UNAVAILABLE",
            status_code=503,
        )
