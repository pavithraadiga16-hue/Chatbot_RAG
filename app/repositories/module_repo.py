"""
Module Repository
=================

PURPOSE:
    Data access layer for the 'modules' collection in MongoDB.
    Allows listing, creating, updating, and deleting module definitions.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)

_module_cache: dict[str, dict] = {}


class ModuleRepository:
    """Data access layer for system modules."""

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return get_database()

    async def list_all(self) -> list[dict]:
        """Fetch all modules."""
        cursor = self.db.modules.find({})
        return await cursor.to_list(length=200)

    async def get_by_id(self, module_id: str) -> Optional[dict]:
        """Fetch a single module by ID."""
        if module_id in _module_cache:
            return _module_cache[module_id]
        doc = await self.db.modules.find_one({"_id": module_id})
        if doc:
            _module_cache[module_id] = doc
        return doc

    async def save(self, module_data: dict) -> dict:
        """Upsert a module definition."""
        mod_id = module_data.get("_id") or module_data.get("id")
        module_data["_id"] = mod_id
        if "id" in module_data and module_data["id"] == mod_id:
            del module_data["id"]

        await self.db.modules.replace_one({"_id": mod_id}, module_data, upsert=True)
        _module_cache[mod_id] = module_data
        logger.info("module_saved", module_id=mod_id)
        return module_data

    async def delete(self, module_id: str) -> bool:
        """Delete a module by ID."""
        res = await self.db.modules.delete_one({"_id": module_id})
        _module_cache.pop(module_id, None)
        logger.info("module_deleted", module_id=module_id)
        return res.deleted_count > 0

    def invalidate_all(self) -> None:
        """Clear cache."""
        _module_cache.clear()


module_repo = ModuleRepository()
