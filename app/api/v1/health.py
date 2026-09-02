"""
Health Check Endpoint
=======================

PURPOSE:
    A simple endpoint that confirms the server is running.
    Used by load balancers, monitoring systems, and deployment pipelines.

WHY A HEALTH ENDPOINT?
    In production deployments (Docker, Kubernetes, cloud platforms):
    1. The load balancer pings /health every 30 seconds
    2. If it gets a 200 response, traffic is routed to this server
    3. If it gets an error, this server is taken out of the pool

    Without this, the load balancer has no way to know if the app is healthy.

PHASES OF HEALTH:
    Phase 1 (current): Simple "is the server running?" check
    Phase 2 (future): Check MongoDB connection
    Phase 3 (future): Check Claude availability
    Phase 4 (future): Check ERP connectivity for active institutions

WHY NOT BUILD FULL HEALTH CHECKS NOW?
    We don't want /health to fail just because MongoDB is down during startup.
    The database connection might temporarily drop and recover — the server is
    still "healthy" in the sense that it can process requests once the DB recovers.
    We'll add nuanced health checks in Phase 11 (Observability).
"""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    summary="Health Check",
    description=(
        "Returns the operational status of the PhinsIQ service. "
        "Used by load balancers and monitoring systems."
    ),
    response_description="Service health status",
    tags=["Health"],
)
async def health_check() -> dict:
    """
    Basic liveness probe.

    Returns HTTP 200 if the server is running.
    An exception here means the server is in a broken state.

    TEACHING MOMENT — Why is this async?
        This specific function doesn't do any async work (no await calls).
        However, we declare it async because:
        1. FastAPI runs all route handlers in its async event loop
        2. Consistency — all route handlers should be async so we can add
           async operations later without changing the signature
        3. Uvicorn (the ASGI server) expects async handlers

    Returns:
        dict: Simple status object
    """
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
    }
