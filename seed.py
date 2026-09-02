"""
PhinsIQ MongoDB Universal Seed Script
=======================================

PURPOSE:
    Populates MongoDB with complete multi-tenant configurations including:
    - Client Institutions (SJBHS, SJBHS Student, SAGS School)
    - Roles & Concepts/Modules
    - Field Definitions & NLP Aliases
    - ERP API Registries & Response Mappers
    - Response Templates
    - Dedicated 'questions' collection (Multi-tenant sample questions by institution_id & role)

USAGE:
    ./venv/bin/python seed.py
    ./venv/bin/python seed.py --questions-only
    ./venv/bin/python seed.py --institution sjbhs
"""

import asyncio
import argparse
import certifi
import sys
import os
from datetime import datetime, timezone
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient

# Ensure workspace root is on sys.path
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from app.core.config import settings
from app.router.question_catalog import get_default_seed_questions
from scripts.seed_sjbhs import (
    INSTITUTIONS,
    ROLES,
    MODULES,
    ACTIONS,
    FIELDS,
    API_REGISTRIES,
    TEMPLATES,
)


async def seed_questions_collection(db, institution_filter: str = None) -> int:
    """
    Seed the 'questions' collection in MongoDB.

    NEW SCHEMA: One consolidated document per (institution_id, role).
    Structure:
        {
          "_id": "sjbhs_student",
          "institution_id": "sjbhs",
          "role": "student",
          "modules": {
            "fees":       { "category_label": "...", "questions": [...] },
            "attendance": { "category_label": "...", "questions": [...] },
            ...
          },
          "updated_at": "..."
        }

    WHY? 4 documents total instead of 136. Easier to maintain, update, and query.
    """
    print("\n🎯 Seeding 'questions' collection in MongoDB...")

    # Ensure index for fast role-based queries
    await db.questions.create_index(
        [("institution_id", 1), ("role", 1)],
        name="idx_questions_inst_role",
        unique=True,
    )

    targets = [
        ("sjbhs", "student"),
        ("sjbhs", "staff"),
        ("sjbhs_student", "student"),
        ("sags_school", "student"),
    ]

    if institution_filter:
        targets = [t for t in targets if t[0] == institution_filter]

    total_questions = 0

    for inst_id, role in targets:
        flat_docs = get_default_seed_questions(institution_id=inst_id, role=role)

        # Convert flat list → modules sub-document map
        modules_map: dict[str, Any] = {}
        for q in flat_docs:
            mod = q.get("module", "general")
            if mod not in modules_map:
                modules_map[mod] = {
                    "category_label": q.get("category_label", mod.replace("_", " ").title()),
                    "questions": [],
                }
            modules_map[mod]["questions"].append({
                "question": q["question"],
                "field": q.get("field", ""),
                "description": q.get("description", ""),
                "route": q.get("route", "/dashboard"),
            })

        doc_id = f"{inst_id}_{role}"
        consolidated_doc = {
            "_id": doc_id,
            "institution_id": inst_id,
            "role": role,
            "modules": modules_map,
            "updated_at": datetime.now(timezone.utc),
        }

        await db.questions.replace_one({"_id": doc_id}, consolidated_doc, upsert=True)
        total_questions += len(flat_docs)
        print(f"  ✓ 1 doc saved for '{inst_id}' ({role}) → {len(flat_docs)} questions across {len(modules_map)} modules")

    total_docs = len(targets)
    print(f"  ✨ {total_docs} documents (previously {total_questions} individual docs) saved in 'questions' collection.")
    return total_questions


async def seed_all(questions_only: bool = False, institution_filter: str = None):
    print("=" * 65)
    print("🚀 PhinsIQ Database Seeder")
    print(f"   Database: {settings.mongodb_database}")
    print(f"   Mode: {'Questions Only' if questions_only else 'Full System Seed'}")
    print("=" * 65)

    client = AsyncIOMotorClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=10000,
        tlsCAFile=certifi.where(),
    )
    db = client[settings.mongodb_database]

    try:
        await client.admin.command("ping")
        print(f"✅ Connected to MongoDB successfully!\n")

        if not questions_only:
            # 1. Institutions
            print("🏢 Seeding Institutions...")
            for inst in INSTITUTIONS:
                if not institution_filter or inst["_id"] == institution_filter:
                    await db.institutions.replace_one({"_id": inst["_id"]}, inst, upsert=True)
                    print(f"  ✓ Institution: {inst['_id']} ({inst['name']})")

            # 2. Roles
            print("\n👥 Seeding Roles...")
            for role in ROLES:
                await db.roles.replace_one({"_id": role["_id"]}, role, upsert=True)
                print(f"  ✓ Role: {role['_id']}")

            # 3. Modules
            print("\n🧩 Seeding Modules...")
            for mod in MODULES:
                await db.modules.replace_one({"_id": mod["_id"]}, mod, upsert=True)
                print(f"  ✓ Module: {mod['_id']}")

            # 4. Actions
            print("\n⚡ Seeding Actions...")
            for act in ACTIONS:
                await db.actions.replace_one({"_id": act["_id"]}, act, upsert=True)
                print(f"  ✓ Action: {act['_id']}")

            # 5. Fields
            print("\n🏷️ Seeding Fields & NLP Aliases...")
            for f in FIELDS:
                await db.fields.replace_one({"module": f["module"]}, f, upsert=True)
                print(f"  ✓ Fields: {f['module']} ({len(f['fields'])} fields)")

            # 6. API Registry
            print("\n🗺️ Seeding ERP API Registries...")
            for reg in API_REGISTRIES:
                if not institution_filter or reg["institution_id"] == institution_filter:
                    await db.api_registry.replace_one(
                        {
                            "institution_id": reg["institution_id"],
                            "role": reg["role"],
                            "module": reg["module"],
                            "action": reg["action"],
                        },
                        reg,
                        upsert=True
                    )
                    print(f"  ✓ API Registry: {reg['institution_id']}/{reg['role']}/{reg['module']}/{reg['action']}")

            # 7. Templates
            print("\n📝 Seeding Response Templates...")
            for t in TEMPLATES:
                await db.templates.replace_one(
                    {"module": t["module"], "action": t["action"]},
                    t,
                    upsert=True
                )
                print(f"  ✓ Templates: {t['module']}/{t['action']}")

        # 8. Questions Table
        await seed_questions_collection(db, institution_filter=institution_filter)

        print("\n" + "=" * 65)
        print("🎉 Database seeding completed successfully!")
        print("=" * 65)

    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description="Seed PhinsIQ MongoDB configuration and questions")
    parser.add_argument("--questions-only", action="store_true", help="Only seed the questions table")
    parser.add_argument("--institution", type=str, default=None, help="Filter seed by specific institution_id (e.g. sjbhs)")
    args = parser.parse_args()

    asyncio.run(seed_all(questions_only=args.questions_only, institution_filter=args.institution))


if __name__ == "__main__":
    main()
