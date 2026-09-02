"""
Institution Repository
========================

PURPOSE:
    All MongoDB queries related to institutions and their configurations.
    This is the ONLY place that reads from the 'institutions' collection.

WHY A REPOSITORY PATTERN?
    Without it, MongoDB queries get scattered everywhere:
        # In chat.py:
        db.institutions.find_one(...)
        # In pipeline.py:
        db.institutions.find_one(...)
        # In permission_engine.py:
        db.institutions.find_one(...)

    That's the same query in 3 places. If we need to add caching or
    change the query, we change 3 files.

    With a repository, the query lives in ONE place. Everything else
    calls get_institution() and doesn't care how it works internally.

IN-PROCESS CACHING:
    We cache institution documents for 5 minutes after first load.
    WHY? Institution config changes rarely (maybe once when onboarding).
    Caching means MongoDB is only hit ONCE per institution per 5 minutes,
    regardless of how many requests come in.

    This is important for 150+ institutions — if every request hit MongoDB
    for institution config, that's a lot of unnecessary database reads.
"""

import time
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)

# Simple in-process cache: {institution_id: (document, expiry_timestamp)}
# WHY NOT USE REDIS YET?
#   A Python dict is sufficient for V1. Redis adds operational complexity
#   (another service to run, another failure point). We'll switch to Redis
#   when the cache needs to be shared across multiple server instances.
_institution_cache: dict[str, tuple[dict, float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes


class InstitutionRepository:
    """
    Data access layer for the 'institutions' collection in MongoDB.

    All methods are async because MongoDB queries involve network I/O.
    Making them async lets the server handle other requests while waiting.
    """

    def __init__(self) -> None:
        # We don't accept the database in __init__ because this repository
        # may be instantiated at module load time (before the DB is connected).
        # get_database() is called lazily inside each method, at query time.
        pass

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Returns the active database. Called only when a query is needed."""
        return get_database()

    async def get_by_id(self, institution_id: str) -> Optional[dict]:
        """
        Fetch an institution by its ID.

        Checks the in-process cache first. If the cache entry is expired
        or missing, queries MongoDB and caches the result.

        Args:
            institution_id: The institution's unique slug (e.g., "sjbhs")

        Returns:
            Institution document dict, or None if not found
        """
        # Check cache
        cached = _institution_cache.get(institution_id)
        if cached:
            doc, expiry = cached
            if time.time() < expiry:
                logger.debug("institution_cache_hit", institution_id=institution_id)
                return doc
            # Cache expired — remove it
            del _institution_cache[institution_id]

        # Cache miss — query MongoDB
        logger.debug("institution_cache_miss", institution_id=institution_id)
        doc = await self.db.institutions.find_one({"_id": institution_id})

        if doc:
            # Store in cache with expiry
            _institution_cache[institution_id] = (doc, time.time() + _CACHE_TTL_SECONDS)
            logger.debug(
                "institution_loaded",
                institution_id=institution_id,
                name=doc.get("name"),
            )

        return doc

    async def get_active_by_id(self, institution_id: str) -> Optional[dict]:
        """
        Fetch an institution only if it's active.

        Returns None for both missing and inactive institutions.
        The caller should check for None and raise InstitutionNotFoundError.
        """
        doc = await self.get_by_id(institution_id)
        if doc and doc.get("status") == "active":
            return doc
        return None

    async def list_all(self) -> list[dict]:
        """Fetch all institutions from MongoDB."""
        cursor = self.db.institutions.find({})
        return await cursor.to_list(length=500)

    async def save(self, institution_data: dict) -> dict:
        """
        Upsert an institution into MongoDB.
        Invalidates in-process cache immediately.
        """
        inst_id = institution_data.get("_id") or institution_data.get("id")
        institution_data["_id"] = inst_id
        if "id" in institution_data and institution_data["id"] == inst_id:
            del institution_data["id"]

        await self.db.institutions.replace_one(
            {"_id": inst_id},
            institution_data,
            upsert=True,
        )
        self.invalidate_cache(inst_id)
        return institution_data

    async def delete(self, institution_id: str) -> bool:
        """Delete an institution by ID and invalidate cache."""
        result = await self.db.institutions.delete_one({"_id": institution_id})
        self.invalidate_cache(institution_id)
        return result.deleted_count > 0

    def invalidate_cache(self, institution_id: str) -> None:
        """
        Remove an institution from the cache.

        Call this after updating an institution's config in MongoDB so
        the next request loads the fresh configuration.
        """
        _institution_cache.pop(institution_id, None)
        logger.info("institution_cache_invalidated", institution_id=institution_id)

    def invalidate_all(self) -> None:
        """Clear the entire institution cache."""
        _institution_cache.clear()
        logger.info("institution_cache_cleared_all")


class RoleRepository:
    """
    Data access layer for the 'roles' collection.

    Roles define which modules are accessible for each role type.
    These change very rarely, so we cache aggressively.
    """

    _role_cache: dict[str, tuple[dict, float]] = {}
    _CACHE_TTL = 600  # 10 minutes — roles change even less often than institutions

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return get_database()

    async def get_by_id(self, role_id: str) -> Optional[dict]:
        """
        Fetch a role definition by ID (e.g., "student", "staff").

        Args:
            role_id: Role identifier

        Returns:
            Role document with 'modules' list, or None
        """
        cached = self._role_cache.get(role_id)
        if cached:
            doc, expiry = cached
            if time.time() < expiry:
                return doc
            del self._role_cache[role_id]

        doc = await self.db.roles.find_one({"_id": role_id})
        if doc:
            self._role_cache[role_id] = (doc, time.time() + self._CACHE_TTL)
        return doc

    async def get_allowed_modules(self, role_id: str) -> list[str]:
        """
        Returns the list of module IDs this role can access.

        Used by the permission engine to check if a detected module
        is accessible for the user's role.

        Returns:
            List of module ID strings, empty list if role not found
        """
        role = await self.get_by_id(role_id)
        return role.get("modules", []) if role else []


# Module-level singletons.
# WHY SINGLETONS?
#   Creating a new InstitutionRepository() on every request would work,
#   but the cache (_institution_cache) is on the class, not the instance,
#   so the cache is shared regardless. Using singletons makes this explicit.
institution_repo = InstitutionRepository()
role_repo = RoleRepository()
