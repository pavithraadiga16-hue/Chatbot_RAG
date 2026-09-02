"""
ERP API Router
===============

PURPOSE:
    The HTTP client that calls external ERP APIs.
    This is the only component that makes actual network calls to institutions' ERPs.

    Given an api_registry entry and a user_id, it:
    1. Builds the complete URL from institution base_url + registry path
    2. Substitutes {user_id} placeholders in the request body template
    3. Makes the HTTP call (GET/POST with appropriate headers and body)
    4. Returns the raw JSON response

WHY THIS IS GENERIC (NOT INSTITUTION-SPECIFIC):
    This router knows NOTHING about SJBHS, SAGS School, or any institution.
    It only knows:
        method + url + headers + body = response

    All institution-specific knowledge lives in the api_registry document in MongoDB.
    Adding a new institution requires ZERO changes to this file.

HTTPX vs REQUESTS:
    requests.post() is synchronous — it blocks the entire server thread while waiting.
    httpx.AsyncClient.post() is async — other requests are handled while waiting.

    For PhinsIQ, this matters:
    - 1000 students ask questions simultaneously
    - Each question triggers an ERP API call (~500ms typical)
    - With requests: server is blocked for 500ms × 1000 calls
    - With httpx async: server handles all 1000 concurrently, responds in ~500ms total

TIMEOUT HANDLING:
    We set explicit timeouts. If the ERP doesn't respond in time:
    - ERPTimeoutError is raised
    - A user-friendly message is returned ("Please try again")
    - The error is logged with institution_id and module for debugging

RETRY STRATEGY (V1):
    V1: No automatic retries. If ERP fails, we return an error immediately.
    Future: Add exponential backoff retry for transient failures.
    Why not retry now? Retrying a slow ERP makes the user wait even longer.
    Better to fail fast and let them try again.
"""

import httpx
from typing import Any, Optional
from app.core.config import settings
from app.core.exceptions import ERPAPIError, ERPTimeoutError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ERPAPIRouter:
    """
    Generic HTTP client for calling external ERP APIs.

    Uses httpx for async HTTP calls. The client is created fresh per request
    in V1 (not pooled) for simplicity. In V2, we can use a shared AsyncClient
    with connection pooling for better performance under load.
    """

    def _substitute_placeholders(
        self,
        template: dict | str,
        user_id: str,
    ) -> dict | str:
        """
        Replace {user_id} placeholders in request body templates.

        WHY PLACEHOLDER SUBSTITUTION?
            The api_registry stores a body TEMPLATE like:
                {"row_id": "{user_id}"}

            At runtime, for user ST123:
                {"row_id": "ST123"}

            This pattern is used for ALL institutions — the template is
            in MongoDB, the actual value comes from the live request.

        Args:
            template: Dict or string containing {user_id} placeholders
            user_id:  The actual user ID from the chat request

        Returns:
            Template with {user_id} replaced by the actual user_id
        """
        if isinstance(template, dict):
            return {
                key: self._substitute_placeholders(value, user_id)
                for key, value in template.items()
            }
        elif isinstance(template, str):
            return template.replace("{user_id}", user_id)
        else:
            return template

    async def call(
        self,
        institution_config: dict,
        registry_entry: dict,
        user_id: str,
        extra_params: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Execute an ERP API call based on the registry configuration.

        This is the core function that actually hits the external ERP.

        Args:
            institution_config: The institution document from MongoDB.
                                Contains base_url, auth_type, headers.
            registry_entry:     The api_registry document for this module.
                                Contains method, path, body_template, etc.
            user_id:            The user's ID (used to fill {user_id} placeholders).
            extra_params:       Additional query parameters (future use).

        Returns:
            Raw JSON response from the ERP as a dict.

        Raises:
            ERPTimeoutError:    If the ERP API doesn't respond in time.
            ERPAPIError:        If the ERP returns an error status or invalid JSON.
        """
        institution_id = institution_config.get("_id", "unknown")
        api_cfg = institution_config.get("api_config", {})
        base_url = api_cfg.get("base_url", "").rstrip("/")

        request_cfg = registry_entry.get("request", {})
        method = request_cfg.get("method", "GET").upper()
        path = request_cfg.get("path", "").lstrip("/")
        module = registry_entry.get("module", "unknown")
        action = registry_entry.get("action", "summary")

        full_url = f"{base_url}/{path}"

        # Build headers: start with institution defaults, then add content type
        headers = dict(api_cfg.get("headers", {}))
        if not headers.get("Content-Type"):
            headers["Content-Type"] = "application/json"

        # Build the request body by substituting {user_id} in the template
        body_template = request_cfg.get("body_template", {})
        request_body = self._substitute_placeholders(body_template, user_id)

        logger.info(
            "erp_api_calling",
            institution_id=institution_id,
            module=module,
            action=action,
            method=method,
            url=full_url,
            user_id=user_id,
        )

        try:
            async with httpx.AsyncClient(
                timeout=settings.erp_timeout,
                # Follow redirects in case the ERP server redirects
                follow_redirects=True,
            ) as client:

                if method == "GET":
                    response = await client.get(
                        full_url,
                        headers=headers,
                        params=request_body if request_body else None,
                    )
                elif method == "POST":
                    response = await client.post(
                        full_url,
                        headers=headers,
                        json=request_body,
                    )
                elif method == "PUT":
                    response = await client.put(
                        full_url,
                        headers=headers,
                        json=request_body,
                    )
                else:
                    raise ERPAPIError(
                        institution_id=institution_id,
                        module=module,
                        reason=f"Unsupported HTTP method: {method}",
                    )

            # Check for HTTP errors (4xx, 5xx)
            if response.status_code >= 400:
                logger.error(
                    "erp_api_http_error",
                    institution_id=institution_id,
                    module=module,
                    status_code=response.status_code,
                    url=full_url,
                )
                # In development mode, if live ERP fails, fall back to mock data
                if settings.is_development:
                    from mock_erp.mock_provider import MockERPProvider
                    mock_data = MockERPProvider.get_mock_data(institution_id, registry_entry.get("role", "student"), module)
                    if mock_data:
                        logger.warning(
                            "erp_fallback_to_mock_used",
                            institution_id=institution_id,
                            module=module,
                            reason=f"Live ERP returned HTTP {response.status_code}",
                        )
                        return mock_data

                raise ERPAPIError(
                    institution_id=institution_id,
                    module=module,
                    reason=f"HTTP {response.status_code}",
                )

            # Parse JSON response
            try:
                data = response.json()
            except Exception:
                if settings.is_development:
                    from mock_erp.mock_provider import MockERPProvider
                    mock_data = MockERPProvider.get_mock_data(institution_id, registry_entry.get("role", "student"), module)
                    if mock_data:
                        logger.warning(
                            "erp_fallback_to_mock_used",
                            institution_id=institution_id,
                            module=module,
                            reason="Live ERP returned non-JSON",
                        )
                        return mock_data

                raise ERPAPIError(
                    institution_id=institution_id,
                    module=module,
                    reason="ERP returned non-JSON response",
                )

            logger.info(
                "erp_api_success",
                institution_id=institution_id,
                module=module,
                status_code=response.status_code,
            )

            return data

        except httpx.TimeoutException:
            logger.error(
                "erp_api_timeout",
                institution_id=institution_id,
                module=module,
                timeout_seconds=settings.erp_timeout,
                url=full_url,
            )
            if settings.is_development:
                from mock_erp.mock_provider import MockERPProvider
                mock_data = MockERPProvider.get_mock_data(institution_id, registry_entry.get("role", "student"), module)
                if mock_data:
                    logger.warning("erp_fallback_to_mock_used", reason="Timeout")
                    return mock_data

            raise ERPTimeoutError(
                institution_id=institution_id,
                module=module,
                timeout_seconds=settings.erp_timeout,
            )

        except (ERPAPIError, ERPTimeoutError):
            raise

        except Exception as e:
            logger.error(
                "erp_api_unexpected_error",
                institution_id=institution_id,
                module=module,
                error=str(e),
            )
            if settings.is_development:
                from mock_erp.mock_provider import MockERPProvider
                mock_data = MockERPProvider.get_mock_data(institution_id, registry_entry.get("role", "student"), module)
                if mock_data:
                    logger.warning("erp_fallback_to_mock_used", reason=str(e))
                    return mock_data

            raise ERPAPIError(
                institution_id=institution_id,
                module=module,
                reason=str(e),
            )


# Singleton
erp_router = ERPAPIRouter()
