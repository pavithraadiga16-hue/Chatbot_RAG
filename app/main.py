"""
PhinsIQ - Application Entry Point
====================================

PURPOSE:
    Creates and configures the FastAPI application.
    This is the file uvicorn runs when starting the server.

    Command: uvicorn app.main:app --reload

    'app.main' → the module path (app/main.py)
    ':app'     → the FastAPI instance named 'app' inside that module

HOW FASTAPI WORKS:
    FastAPI is a web framework built on top of Starlette (an ASGI toolkit).
    ASGI (Asynchronous Server Gateway Interface) is the standard interface
    between Python async web frameworks and async servers like uvicorn.

    The flow for every request:
        Client → uvicorn → ASGI middleware stack → FastAPI router → your code

WHAT THIS FILE DOES:
    1. Configures structured logging (before anything else)
    2. Creates the FastAPI instance with metadata for the /docs page
    3. Registers the lifespan (startup + shutdown handlers)
    4. Adds CORS middleware (allows the browser demo UI to call the API)
    5. Registers exception handlers (converts our custom exceptions to JSON)
    6. Mounts the API v1 router

WHY STRUCTURED AS AN APPLICATION FACTORY?
    The `create_application()` function is an "application factory".
    Instead of creating `app = FastAPI()` at module level directly, we wrap it
    in a function. This is because:
    1. Tests can call create_application() to get a fresh app instance
    2. Module-level code runs at import time — factory functions run on demand
    3. It's easier to configure different apps for different environments
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.config import settings
from app.core.database import lifespan as db_lifespan
from app.core.exceptions import PhinsIQException
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import router as v1_router

# Configure logging FIRST — before any other imports that might log.
# If we configure logging after creating the FastAPI app, early startup
# messages (like uvicorn's "Application startup complete") use plain text.
configure_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Orchestrates startup and shutdown across all components.
    Currently delegates to the database lifespan.
    As we add more components (e.g., HTTP client pool, cache), we'll add
    their startup/shutdown code here.

    TEACHING MOMENT — What is a context manager?
        Think of it like a try/finally block:

        try:
            startup_code()   ← runs before yield
            yield            ← application runs here
        finally:
            shutdown_code()  ← runs after yield (even if an exception occurred)

        The @asynccontextmanager decorator converts a generator function
        with a 'yield' into a proper context manager object.
    """
    logger.info(
        "phinsiq_starting",
        environment=settings.app_env,
        port=settings.app_port,
    )

    # Run the database connection lifecycle
    async with db_lifespan(app):
        # Load learned semantic patterns from MongoDB
        from app.understanding.semantic_matcher import semantic_matcher
        await semantic_matcher.load_learned_patterns_from_db()

        # Warm up MeloTTS in the background so a missing torch/melotts install
        # is logged at startup instead of only surfacing as a browser fallback.
        import asyncio
        from app.tts.service import tts_service

        async def _warmup_tts() -> None:
            await asyncio.to_thread(lambda: tts_service.is_available)
            if tts_service.is_available:
                logger.info("tts_warmup_ready", sample_rate=tts_service.sample_rate)
            else:
                logger.warning("tts_warmup_unavailable", error=tts_service.init_error)

        asyncio.create_task(_warmup_tts())

        logger.info("phinsiq_ready", message="PhinsIQ is ready to receive requests.")
        yield

    logger.info("phinsiq_stopped")


def create_application() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI instance.

    Returns:
        FastAPI: Fully configured application ready to serve requests
    """

    # -------------------------------------------------------------------------
    # 1. Create the FastAPI instance
    # -------------------------------------------------------------------------
    # These parameters populate the automatic API documentation at /docs
    application = FastAPI(
        title="PhinsIQ",
        description=(
            "Enterprise AI Middleware Platform for Parrophins Private Limited. "
            "Intelligently routes institution-specific queries to ERP APIs "
            "and returns natural language responses."
        ),
        version="1.0.0",
        # OpenAPI docs are available at /docs (Swagger UI) and /redoc
        # In production, consider disabling /docs for security.
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        # Link the lifespan function for startup/shutdown
        lifespan=lifespan,
    )

    # -------------------------------------------------------------------------
    # 2. CORS Middleware
    # -------------------------------------------------------------------------
    # CORS (Cross-Origin Resource Sharing) is a browser security mechanism.
    # By default, a browser blocks JavaScript on http://localhost:5500 from
    # calling an API at http://localhost:8000 (different port = different origin).
    #
    # We add CORS middleware to explicitly allow our demo index.html to call
    # the PhinsIQ API during development.
    #
    # WHY NOT allow_origins=["*"] in production?
    #   "*" allows ANY website to call your API from a user's browser.
    #   A malicious website could make requests as if it were your own frontend.
    #   In production, list only your actual frontend domains.
    if settings.is_development:
        allowed_origins = ["*"]
    else:
        # In production, read from CORS_ORIGINS in .env.
        # If your frontend domain changes, just update CORS_ORIGINS in .env without changing code.
        configured = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
        allowed_origins = configured if configured else ["*"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------------------
    # 3. Exception Handlers
    # -------------------------------------------------------------------------
    # FastAPI's exception handler converts exceptions into HTTP responses.
    # Without this, unhandled exceptions return a 500 with a Python traceback
    # (which may expose internal implementation details to clients).

    @application.exception_handler(PhinsIQException)
    async def phinsiq_exception_handler(
        request: Request, exc: PhinsIQException
    ) -> JSONResponse:
        """
        Converts PhinsIQ custom exceptions into clean JSON error responses.

        Every exception in our hierarchy (InstitutionNotFoundError, ERPTimeoutError, etc.)
        inherits from PhinsIQException, so this single handler covers all of them.

        DEVELOPMENT vs PRODUCTION:
            Development: Include the technical 'detail' field for debugging
            Production: Only include the user-safe 'message' field

        This is how we ensure "Never expose internal stack traces to clients."
        """
        response_body: dict = {
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
        }

        # Include debug detail only in development mode
        if settings.is_development and exc.detail:
            response_body["detail"] = exc.detail

        logger.warning(
            "phinsiq_exception",
            error_code=exc.error_code,
            status_code=exc.status_code,
            detail=exc.detail,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=response_body,
        )

    @application.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catches any unhandled exception and converts it to a safe 500 response.

        WHY THIS IS IMPORTANT:
            Without this handler, if unexpected code raises a ValueError or any
            other Python exception, FastAPI would return a 500 with the full
            Python traceback in the response — exposing file paths, function names,
            and internal logic to the outside world.

            This handler ensures clients always get a clean, safe error message.
        """
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error_code": "INTERNAL_ERROR",
            },
        )

    # -------------------------------------------------------------------------
    # 4. Mount the API Router
    # -------------------------------------------------------------------------
    # All v1 routes are at /api/v1/...
    # The prefix here combines with the route paths defined in each endpoint file.
    application.include_router(
        v1_router,
        prefix="/api/v1",
    )

    @application.get("/", include_in_schema=False)
    async def serve_index():
        """Serve the PhinsIQ Web Console & Admin Studio."""
        import os
        index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as index_file:
                html = index_file.read().replace(
                    "__PHINSIQ_PUBLIC_API_BASE_URL__",
                    settings.public_api_base_url.rstrip("/"),
                )
            return HTMLResponse(content=html)
        return JSONResponse({"message": "PhinsIQ API running. Please open index.html."})

    @application.get("/guide", include_in_schema=False)
    @application.get("/guide.html", include_in_schema=False)
    async def serve_guide():
        """Serve the PhinsIQ Technical Code & Architecture Guide."""
        import os
        from fastapi.responses import FileResponse
        guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "guide.html")
        if os.path.exists(guide_path):
            return FileResponse(guide_path)
        return JSONResponse({"message": "PhinsIQ Guide not found."})

    @application.get("/documentation", include_in_schema=False)
    @application.get("/documentation.html", include_in_schema=False)
    async def serve_documentation():
        """Serve the PhinsIQ Complete Master Technical Handbook."""
        import os
        from fastapi.responses import FileResponse
        doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documentation.html")
        if os.path.exists(doc_path):
            return FileResponse(doc_path)
        return JSONResponse({"message": "documentation.html not found."})

    @application.get("/questions", tags=["Questions"])
    @application.get("/api/v1/questions", tags=["Questions"])
    @application.get("/api/v1/phinsiq/questions", tags=["Questions"])
    async def get_questions(
        institution_id: Optional[str] = Query(None, description="Filter by client institution ID (e.g. sjbhs, sags_school)"),
        role: Optional[str] = Query(None, description="Filter by user role (e.g. student, staff)"),
        module: Optional[str] = Query(None, description="Filter by specific module (e.g. fees, attendance)"),
    ):
        """
        Get dynamic catalog of sample natural language questions supported by PhinsIQ,
        persisted in MongoDB and filtered by institution_id, role, and module.
        """
        from app.router.question_catalog import get_catalog_for_institution
        catalog = await get_catalog_for_institution(
            institution_id=institution_id,
            role=role,
            module=module,
        )
        return JSONResponse(catalog)

    # -------------------------------------------------------------------------
    # 5. Legacy Mobile TTS Route Compatibility
    # -------------------------------------------------------------------------
    # Allows legacy mobile clients (e.g. Gonzaga School Flutter app) to call
    # /batch/synthesize and /batch/result/{job_id} directly at root.
    from fastapi import status as http_status
    from app.api.v1.tts import batch_synthesize, get_batch_result
    application.post(
        "/batch/synthesize",
        tags=["Text-to-Speech (Legacy)"],
        status_code=http_status.HTTP_201_CREATED,
        include_in_schema=False,
    )(batch_synthesize)
    application.get(
        "/batch/result/{job_id}",
        tags=["Text-to-Speech (Legacy)"],
        include_in_schema=False,
    )(get_batch_result)

    logger.info(
        "application_configured",
        routes=[str(route.path) for route in application.routes if hasattr(route, "path")],
    )

    return application


# Create the application instance.
# This is what uvicorn imports when you run: uvicorn app.main:app
app = create_application()
