"""
API Registry Repository
========================

PURPOSE:
    Fetches ERP API configurations from MongoDB's 'api_registry' collection.
    Every institution+role+module+action combination has one registry entry
    that tells PhinsIQ exactly how to call that ERP endpoint.

WHY THIS IS THE MOST IMPORTANT REPOSITORY:
    This is what makes 150 institutions possible with ZERO institution-specific
    Python code. The registry entry contains:
      - Which URL to call
      - Which HTTP method
      - What request body to send
      - How to map the response fields

    Python code uses this config. Python code never has institution names in it.

CACHING STRATEGY:
    API registry entries are cached per (institution_id, role, module, action).
    TTL: 10 minutes — reasonable since API configs change infrequently.
    Cache key: "sjbhs:student:fees:summary"

FIELDS COLLECTION:
    The 'fields' collection stores field definitions with aliases for each module.
    These are used by the field_detector to map user intent to field names.
    Cached for 10 minutes since field/alias definitions rarely change.
"""

import time
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)

_registry_cache: dict[str, tuple[dict, float]] = {}
_fields_cache: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 600  # 10 minutes


class RegistryRepository:
    """
    Data access layer for the 'api_registry' collection.

    The api_registry maps a specific (institution, role, module, action)
    combination to the exact ERP API endpoint and field mapping.
    """

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return get_database()

    def _cache_key(self, institution_id: str, role: str, module: str, action: str) -> str:
        """
        Build a deterministic cache key from the query parameters.

        Using ':' as separator — since institution_ids use '_' (e.g., "sags_school"),
        ':' ensures there's no key collision between "a:b:c:d" and "a_b:c:d".
        """
        return f"{institution_id}:{role}:{module}:{action}"

    async def get_registry(
        self,
        institution_id: str,
        role: str,
        module: str,
        action: str = "summary",
    ) -> Optional[dict]:
        """
        Fetch the API registry entry for a specific institution/role/module/action.

        This is the most critical lookup in the entire PhinsIQ system.
        It answers: "How do I call the ERP for this institution's fees module?"

        Args:
            institution_id: e.g., "sjbhs"
            role:           e.g., "student"
            module:         e.g., "fees"
            action:         e.g., "summary" (default: "summary")

        Returns:
            Registry document with 'request' config and 'response_mapping',
            or None if no registry entry exists for this combination.
        """
        cache_key = self._cache_key(institution_id, role, module, action)

        # Check cache
        cached = _registry_cache.get(cache_key)
        if cached:
            doc, expiry = cached
            if time.time() < expiry:
                return doc
            del _registry_cache[cache_key]

        # Query MongoDB
        doc = await self.db.api_registry.find_one({
            "institution_id": institution_id,
            "role":           role,
            "module":         module,
            "action":         action,
        })

        # Fallback: if exact action not found, find any entry for this module
        if not doc:
            doc = await self.db.api_registry.find_one({
                "institution_id": institution_id,
                "role":           role,
                "module":         module,
            })

        if doc:
            _registry_cache[cache_key] = (doc, time.time() + _CACHE_TTL)
            logger.debug(
                "registry_loaded",
                institution_id=institution_id,
                role=role,
                module=module,
                action=doc.get("action", action),
            )
        else:
            logger.warning(
                "registry_not_found",
                institution_id=institution_id,
                role=role,
                module=module,
                action=action,
            )

        return doc

    async def list_all(self, institution_id: Optional[str] = None, module: Optional[str] = None) -> list[dict]:
        """List all registry entries, optionally filtered."""
        query = {}
        if institution_id:
            query["institution_id"] = institution_id
        if module:
            query["module"] = module
        cursor = self.db.api_registry.find(query)
        return await cursor.to_list(length=1000)

    async def save(self, data: dict) -> dict:
        """Upsert an api_registry entry and invalidate cache."""
        query = {
            "institution_id": data["institution_id"],
            "role": data.get("role", "student"),
            "module": data["module"],
            "action": data.get("action", "summary"),
        }
        await self.db.api_registry.replace_one(query, data, upsert=True)
        cache_key = self._cache_key(
            data["institution_id"],
            data.get("role", "student"),
            data["module"],
            data.get("action", "summary"),
        )
        _registry_cache.pop(cache_key, None)
        logger.info("registry_saved", **query)
        return data

    async def delete(self, institution_id: str, role: str, module: str, action: str) -> bool:
        """Delete an api_registry entry and invalidate cache."""
        query = {
            "institution_id": institution_id,
            "role": role,
            "module": module,
            "action": action,
        }
        res = await self.db.api_registry.delete_one(query)
        cache_key = self._cache_key(institution_id, role, module, action)
        _registry_cache.pop(cache_key, None)
        return res.deleted_count > 0

    def invalidate_all(self) -> None:
        """Clear registry cache."""
        _registry_cache.clear()


class FieldsRepository:
    """
    Data access layer for the 'fields' collection.

    Provides field definitions with their aliases for a given module.
    Used by field_detector to understand what the user is asking for.
    """

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return get_database()

    async def get_fields(self, module: str) -> Optional[dict]:
        """
        Fetch all field definitions (with aliases) for a module.

        Args:
            module: Module ID, e.g., "fees", "attendance"

        Returns:
            Fields document containing a 'fields' list with 'name',
            'aliases', 'erp_key', and 'format' for each field.
            None if the module has no field definitions.
        """
        cached = _fields_cache.get(module)
        if cached:
            doc, expiry = cached
            if time.time() < expiry:
                return doc
            del _fields_cache[module]

        doc = await self.db.fields.find_one({"module": module})
        if doc:
            _fields_cache[module] = (doc, time.time() + _CACHE_TTL)

        return doc

    async def get_field_list(self, module: str) -> list[dict]:
        """
        Returns just the list of field definitions for a module.

        Convenience method — most callers only need the list, not the wrapper doc.

        Returns:
            List of field dicts, each with 'name', 'aliases', 'erp_key', 'format'.
            Empty list if module not found.
        """
        doc = await self.get_fields(module)
        return doc.get("fields", []) if doc else []

    async def list_all(self) -> list[dict]:
        """List all fields documents across all modules."""
        cursor = self.db.fields.find({})
        return await cursor.to_list(length=200)

    async def save(self, data: dict) -> dict:
        """Upsert field definitions for a module and invalidate cache."""
        module = data["module"]
        await self.db.fields.replace_one({"module": module}, data, upsert=True)
        _fields_cache.pop(module, None)
        logger.info("fields_saved", module=module, count=len(data.get("fields", [])))
        return data

    async def delete(self, module: str) -> bool:
        """Delete field definitions for a module."""
        res = await self.db.fields.delete_one({"module": module})
        _fields_cache.pop(module, None)
        return res.deleted_count > 0

    def invalidate_all(self) -> None:
        """Clear fields cache."""
        _fields_cache.clear()


class TemplatesRepository:
    """
    Data access layer for the 'templates' collection.

    Templates are pre-written response strings with {placeholder} variables.
    Using templates means we never need Claude for straightforward questions.
    """

    _templates_cache: dict[str, tuple[dict, float]] = {}
    _CACHE_TTL = 600

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return get_database()

    async def get_templates(self, module: str, action: str = "summary") -> Optional[dict]:
        """
        Fetch template definitions for a module+action combination.

        Args:
            module: e.g., "fees"
            action: e.g., "summary"

        Returns:
            Templates document with 'field_templates' dict,
            'summary_template' string, etc.
        """
        cache_key = f"{module}:{action}"
        cached = self._templates_cache.get(cache_key)
        if cached:
            doc, expiry = cached
            if time.time() < expiry:
                return doc
            del self._templates_cache[cache_key]

        doc = await self.db.templates.find_one({"module": module, "action": action})
        if doc:
            self._templates_cache[cache_key] = (doc, time.time() + self._CACHE_TTL)
        return doc

    async def list_all(self) -> list[dict]:
        """List all templates."""
        cursor = self.db.templates.find({})
        return await cursor.to_list(length=200)

    async def save(self, data: dict) -> dict:
        """Upsert template for module+action and invalidate cache."""
        module = data["module"]
        action = data.get("action", "summary")
        query = {"module": module, "action": action}
        await self.db.templates.replace_one(query, data, upsert=True)
        cache_key = f"{module}:{action}"
        self._templates_cache.pop(cache_key, None)
        logger.info("template_saved", module=module, action=action)
        return data

    async def delete(self, module: str, action: str) -> bool:
        """Delete template for module+action."""
        res = await self.db.templates.delete_one({"module": module, "action": action})
        cache_key = f"{module}:{action}"
        self._templates_cache.pop(cache_key, None)
        return res.deleted_count > 0

    def invalidate_all(self) -> None:
        """Clear templates cache."""
        self._templates_cache.clear()


# Singletons
registry_repo = RegistryRepository()
fields_repo = FieldsRepository()
templates_repo = TemplatesRepository()
