"""
Module Route Resolution Service
===============================

PURPOSE:
    Resolves client-side navigation screen routes (e.g. '/homework', '/fees', '/dashboard')
    based on the institution's configuration or standard canonical defaults.

USAGE:
    route = await route_service.get_route(institution_id="sjbhs", module="fees")
    # Returns "/fees" (or custom configured route for that institution)
"""

from typing import Optional, Any
from app.core.logging import get_logger
from app.repositories.institution import institution_repo

logger = get_logger(__name__)

# Canonical default navigation routes across ERP modules
DEFAULT_MODULE_ROUTES: dict[str, str] = {
    "profile": "/profile",
    "fees": "/fees",
    "attendance": "/attendance",
    "homework": "/homework",
    "study_materials": "/study-materials",
    "study_material": "/study-materials",
    "notification": "/notifications",
    "notice": "/notifications",
    "calendar": "/calendar",
    "holiday": "/calendar",
    "academic_overview": "/dashboard",
    "dashboard": "/dashboard",
    "exam": "/exams",
    "timetable": "/timetable",
    "library": "/library",
    "leave": "/leave",
    "greeting": "/dashboard",
}


class RouteService:
    """Resolves UI screen navigation paths per institution and module."""

    async def get_routes(
        self,
        institution_id: str,
        modules: Optional[list[str]] = None,
        is_overall_overview: bool = False,
        answer_text: Optional[str] = None,
    ) -> list[str]:
        """
        Determines the array of navigation routes for all involved modules.
        If multiple modules are involved (e.g. attendance + fees), returns routes for all.
        If overall overview or Claude advice, analyzes the answer or active modules
        and returns relevant routes (e.g. ['/attendance', '/fees', '/homework']).
        """
        routes: list[str] = []

        # Check for custom institution routes
        custom_routes: dict[str, str] = {}
        try:
            inst = await institution_repo.get_active_by_id(institution_id)
            if inst and "module_routes" in inst and isinstance(inst["module_routes"], dict):
                custom_routes = inst["module_routes"]
        except Exception as exc:
            logger.warning("custom_route_lookup_failed", institution_id=institution_id, error=str(exc))

        def resolve_single_route(mod_name: str) -> str:
            clean = mod_name.strip().lower()
            if clean in custom_routes:
                return custom_routes[clean]
            return DEFAULT_MODULE_ROUTES.get(clean, f"/{clean.replace('_', '-')}")

        # If specific modules are provided (e.g. ['attendance', 'fees'])
        if modules:
            for m in modules:
                r = resolve_single_route(m)
                if r and r not in routes:
                    routes.append(r)

        # If overall overview or Claude answer text is provided, detect mentioned/relevant modules
        if answer_text:
            text_lower = answer_text.lower()
            keyword_to_module = [
                ("attendance", "attendance"),
                ("present", "attendance"),
                ("absent", "attendance"),
                ("fee", "fees"),
                ("dues", "fees"),
                ("paid", "fees"),
                ("homework", "homework"),
                ("assignment", "homework"),
                ("study material", "study_materials"),
                ("notes", "study_materials"),
                ("portion", "study_materials"),
                ("holiday", "calendar"),
                ("vacation", "calendar"),
                ("calendar", "calendar"),
                ("notification", "notification"),
                ("notice", "notification"),
                ("profile", "profile"),
                ("admission", "profile"),
            ]
            for kw, mod in keyword_to_module:
                if kw in text_lower:
                    r = resolve_single_route(mod)
                    if r and r not in routes:
                        routes.append(r)

        if not routes:
            routes = ["/dashboard"]

        return routes

    async def get_route(
        self,
        institution_id: str,
        module: Optional[str] = None,
        is_overall_overview: bool = False,
    ) -> str:
        """
        Determines the primary navigation route for backward compatibility.
        """
        modules = [module] if module else []
        routes = await self.get_routes(
            institution_id=institution_id,
            modules=modules,
            is_overall_overview=is_overall_overview,
        )
        return routes[0] if routes else "/dashboard"


route_service = RouteService()
