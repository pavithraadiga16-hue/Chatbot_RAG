"""
PhinsIQ Structured Logging
============================

PURPOSE:
    Configures structured logging for the entire application.
    Every log entry contains machine-readable fields instead of plain text.

WHY STRUCTURED LOGGING?
    Plain logging:
        "ERROR: Failed to call ERP for sags_school attendance"

    Structured logging (JSON):
        {
            "event": "erp_call_failed",
            "institution_id": "sags_school",
            "module": "attendance",
            "error": "Connection timeout",
            "request_id": "req_abc123",
            "duration_ms": 10043
        }

    In production with 150+ institutions, you need to filter logs by institution,
    module, or time. Structured logs make this possible with log aggregation
    tools like Datadog, CloudWatch, or ELK Stack.

USAGE:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("attendance_fetched", institution_id="sags_school", module="attendance")
    logger.error("erp_timeout", institution_id="sags_school", error=str(e))
"""

import logging
import structlog
from app.core.config import settings


def configure_logging() -> None:
    """
    Configure structlog and the standard Python logging system.

    WHY CALL THIS ONCE AT STARTUP?
        Logging configuration is global state. If we configure it in every
        module, there would be conflicts. We configure it once in main.py
        during application startup.

    HOW IT WORKS:
        structlog wraps Python's standard logging library. This means:
        1. Our code uses structlog's clean API
        2. Third-party libraries that use standard logging (FastAPI, httpx, motor)
           still produce logs — they flow through the standard logging system
        3. All logs go through structlog's processors (filtering, formatting)
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure the standard Python logging (for third-party libraries)
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )
    # Suppress overly verbose logs from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)

    # Choose renderers based on environment
    if settings.is_development:
        # In development: colored, human-readable console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # In production: machine-readable JSON for log aggregation tools
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            # Add log level (INFO, ERROR, etc.) to every event
            structlog.stdlib.add_log_level,
            # Add timestamp to every event
            structlog.processors.TimeStamper(fmt="iso"),
            # Format exception tracebacks if present
            structlog.processors.format_exc_info,
            # The actual renderer (console or JSON)
            renderer,
        ],
        # Use a wrapper class compatible with Python's standard logging
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        # Cache the logger after first creation for performance
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a named logger instance for a module.

    The name parameter should always be __name__ — Python's built-in that
    gives the current module's dotted path (e.g., "app.pipeline.pipeline").
    This lets you trace exactly which module produced each log entry.

    EXAMPLE:
        logger = get_logger(__name__)
        logger.info("request_received", user_id="ST123", module="attendance")

    Args:
        name: Module name, typically __name__

    Returns:
        A structlog bound logger instance
    """
    return structlog.get_logger(name)
