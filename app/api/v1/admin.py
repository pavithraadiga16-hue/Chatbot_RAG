"""
Admin Configuration API Router
==============================

PURPOSE:
    Provides full CRUD endpoints for the Web Admin Studio:
    - Institutions (Clients)
    - Modules (Concepts)
    - API Registry (ERP Endpoints & Field Mappings)
    - Fields & Aliases (Standard Fields & NLP Keywords)
    - Response Templates (Single field & Summary formatting)
    - Live ERP Tester & Auto-Key Extractor
    - 1-Click Starter Seed & Cache Flush
"""

from datetime import datetime, timezone
from typing import Any, Optional
import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import get_logger
from app.models.admin import (
    ApiRegistryModel,
    FieldsDocModel,
    InstitutionModel,
    ModuleModel,
    QuestionModel,
    TemplateModel,
    TestErpRequest,
    TestErpResponse,
)
from app.repositories.institution import institution_repo, role_repo
from app.repositories.module_repo import module_repo
from app.repositories.question_repo import question_repo
from app.repositories.registry import fields_repo, registry_repo, templates_repo

logger = get_logger(__name__)

router = APIRouter(tags=["Admin Management"])


# =============================================================================
# Helper function: Extract all dot-notation keys from nested dict/list
# =============================================================================

def serialize_doc(doc: Any) -> Any:
    """Recursively convert ObjectIds and non-JSON native types for safe serialization."""
    if isinstance(doc, dict):
        res = {}
        for k, v in doc.items():
            if k == "_id":
                res[k] = str(v)
            elif isinstance(v, (dict, list)):
                res[k] = serialize_doc(v)
            elif isinstance(v, datetime):
                res[k] = v.isoformat()
            else:
                res[k] = v
        return res
    elif isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    return doc


def extract_json_keys(data: Any, prefix: str = "") -> list[str]:
    """Recursively extract dot-separated keys from a nested JSON object."""
    keys: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{prefix}.{k}" if prefix else k
            keys.append(current_path)
            if isinstance(v, (dict, list)):
                keys.extend(extract_json_keys(v, current_path))
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], (dict, list)):
        keys.extend(extract_json_keys(data[0], prefix))
    return sorted(list(set(keys)))


# =============================================================================
# 1. Institutions (Clients) Endpoints
# =============================================================================

@router.get("/institutions", response_model=list[dict])
async def list_institutions():
    """List all registered institutions/clients."""
    docs = await institution_repo.list_all()
    return serialize_doc(docs)


@router.post("/institutions", status_code=status.HTTP_200_OK)
async def create_or_update_institution(payload: InstitutionModel):
    """Create or update an institution configuration."""
    data = payload.model_dump(by_alias=True)
    data["updated_at"] = datetime.now(timezone.utc)
    if "created_at" not in data:
        data["created_at"] = datetime.now(timezone.utc)
    saved = await institution_repo.save(data)
    return {"success": True, "institution": serialize_doc(saved)}


@router.delete("/institutions/{institution_id}")
async def delete_institution(institution_id: str):
    """Delete an institution by ID."""
    deleted = await institution_repo.delete(institution_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Institution not found")
    return {"success": True, "deleted_id": institution_id}


# =============================================================================
# 2. Modules (Concepts) Endpoints
# =============================================================================

@router.get("/modules", response_model=list[dict])
async def list_modules():
    """List all system modules."""
    docs = await module_repo.list_all()
    return serialize_doc(docs)


@router.post("/modules", status_code=status.HTTP_200_OK)
async def create_or_update_module(payload: ModuleModel):
    """Create or update a module."""
    data = payload.model_dump(by_alias=True)
    data["updated_at"] = datetime.now(timezone.utc)
    saved = await module_repo.save(data)
    return {"success": True, "module": serialize_doc(saved)}


@router.delete("/modules/{module_id}")
async def delete_module(module_id: str):
    """Delete a module."""
    deleted = await module_repo.delete(module_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"success": True, "deleted_id": module_id}


# =============================================================================
# 3. API Registry & Field Mappings Endpoints
# =============================================================================

@router.get("/registry", response_model=list[dict])
async def list_registries(
    institution_id: Optional[str] = Query(None, description="Filter by institution"),
    module: Optional[str] = Query(None, description="Filter by module"),
):
    """List all API registry endpoint mappings."""
    docs = await registry_repo.list_all(institution_id=institution_id, module=module)
    return serialize_doc(docs)


@router.post("/registry", status_code=status.HTTP_200_OK)
async def create_or_update_registry(payload: ApiRegistryModel):
    """Create or update an API registry entry (ERP endpoint & dynamic mapping)."""
    data = payload.model_dump()
    data["updated_at"] = datetime.now(timezone.utc)
    saved = await registry_repo.save(data)
    return {"success": True, "registry": serialize_doc(saved)}


@router.delete("/registry")
async def delete_registry(
    institution_id: str = Query(...),
    role: str = Query("student"),
    module: str = Query(...),
    action: str = Query("summary"),
):
    """Delete a specific API registry entry."""
    deleted = await registry_repo.delete(
        institution_id=institution_id,
        role=role,
        module=module,
        action=action,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Registry entry not found")
    return {"success": True, "deleted": {"institution_id": institution_id, "module": module, "action": action}}


# =============================================================================
# 4. Fields & NLP Aliases Endpoints
# =============================================================================

@router.get("/fields", response_model=list[dict])
async def list_all_fields():
    """List all field definitions across all modules."""
    docs = await fields_repo.list_all()
    return serialize_doc(docs)


@router.get("/fields/{module}")
async def get_module_fields(module: str):
    """Get field definitions for a specific module."""
    doc = await fields_repo.get_fields(module)
    if not doc:
        return {"module": module, "fields": []}
    return serialize_doc(doc)


@router.post("/fields", status_code=status.HTTP_200_OK)
async def create_or_update_fields(payload: FieldsDocModel):
    """Create or update field definitions and NLP aliases for a module."""
    data = payload.model_dump()
    data["updated_at"] = datetime.now(timezone.utc)
    saved = await fields_repo.save(data)
    return {"success": True, "fields_doc": serialize_doc(saved)}


@router.delete("/fields/{module}")
async def delete_module_fields(module: str):
    """Delete all field definitions for a module."""
    deleted = await fields_repo.delete(module)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fields not found for module")
    return {"success": True, "deleted_module": module}


# =============================================================================
# 5. Response Templates Endpoints
# =============================================================================

@router.get("/templates", response_model=list[dict])
async def list_all_templates():
    """List all response templates."""
    docs = await templates_repo.list_all()
    return serialize_doc(docs)


@router.get("/templates/{module}/{action}")
async def get_template(module: str, action: str = "summary"):
    """Get a specific template."""
    doc = await templates_repo.get_templates(module, action)
    if not doc:
        raise HTTPException(status_code=404, detail="Template not found")
    return serialize_doc(doc)


@router.post("/templates", status_code=status.HTTP_200_OK)
async def create_or_update_template(payload: TemplateModel):
    """Create or update a response template."""
    data = payload.model_dump()
    data["updated_at"] = datetime.now(timezone.utc)
    saved = await templates_repo.save(data)
    return {"success": True, "template": serialize_doc(saved)}


@router.delete("/templates/{module}/{action}")
async def delete_template(module: str, action: str = "summary"):
    """Delete a response template."""
    deleted = await templates_repo.delete(module, action)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "deleted": {"module": module, "action": action}}


# =============================================================================
# 6. Live ERP Tester & Auto-Key Extractor
# =============================================================================

@router.post("/test-erp", response_model=TestErpResponse)
async def test_erp_endpoint(payload: TestErpRequest):
    """
    Calls a live ERP API endpoint directly and returns the response JSON along
    with all discovered dot-notation keys.
    """
    url = payload.base_url.rstrip("/") + "/" + payload.path.lstrip("/")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if payload.headers:
        headers.update(payload.headers)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            if payload.method.upper() == "GET":
                resp = await client.get(url, headers=headers, params=payload.body)
            else:
                resp = await client.post(url, headers=headers, json=payload.body or {})

            try:
                data = resp.json()
            except Exception:
                data = {"raw_text": resp.text}

            extracted_keys = extract_json_keys(data) if isinstance(data, (dict, list)) else []

            return TestErpResponse(
                status_code=resp.status_code,
                success=resp.is_success,
                data=data,
                extracted_keys=extracted_keys,
            )
    except Exception as e:
        logger.warning("test_erp_failed", url=url, error=str(e))
        return TestErpResponse(
            status_code=500,
            success=False,
            error=str(e),
            extracted_keys=[],
        )


# =============================================================================
# 7. Sample Questions Management
# =============================================================================

@router.get("/questions")
async def list_sample_questions(
    institution_id: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
):
    """
    List sample questions as a flat list (for Admin Studio table view).
    Reads from consolidated (institution_id, role) document and expands
    the modules sub-array into individual rows.
    """
    questions = await question_repo.get_questions(
        institution_id=institution_id,
        role=role,
        module=module,
    )
    return serialize_doc(questions)


@router.post("/questions")
async def save_sample_question(data: QuestionModel):
    """
    Add or update a single question entry.
    The question is pushed into the modules.{module}.questions array
    inside the consolidated (institution_id, role) document.
    """
    doc = data.model_dump(by_alias=True, exclude_none=True)
    qid = await question_repo.upsert_question(doc)
    return {"success": True, "_id": qid, "message": "Sample question saved successfully."}


@router.delete("/questions/{institution_id}")
async def delete_sample_question(
    institution_id: str,
    role: str = Query(..., description="Role (e.g. student, staff)"),
    module: str = Query(..., description="Module name (e.g. fees, attendance)"),
    question_text: str = Query(..., description="Exact question text to remove"),
):
    """
    Remove a specific question entry from the consolidated questions document.
    Targets the exact question text within the specified module sub-array.
    """
    success = await question_repo.delete_question(
        institution_id=institution_id,
        role=role,
        module=module,
        question_text=question_text,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Question not found or nothing was removed")
    return {"success": True, "message": "Question removed from module array."}


@router.post("/questions/seed")
async def seed_institution_questions(
    institution_id: str = Query("sjbhs"),
    role: str = Query("student"),
):
    """Seed or re-seed the consolidated questions document for an institution+role."""
    from app.router.question_catalog import get_default_seed_questions
    seed_docs = get_default_seed_questions(institution_id=institution_id, role=role)
    count = await question_repo.seed_questions_if_empty(seed_docs)
    return {"success": True, "count": count, "message": f"Seeded {count} sample questions for {institution_id} ({role})"}


# =============================================================================
# 8. Cache Invalidation & 1-Click Starter Seed
# =============================================================================

@router.post("/cache/flush")
async def flush_all_caches():
    """Flush all in-memory caches across all repositories."""
    institution_repo.invalidate_all()
    module_repo.invalidate_all()
    registry_repo.invalidate_all()
    fields_repo.invalidate_all()
    templates_repo.invalidate_all()
    question_repo.flush_cache()
    return {"success": True, "message": "All repository caches cleared successfully."}


@router.post("/seed-defaults")
async def seed_starter_defaults():
    """
    1-Click seed for initial standard datasets (SJBHS, SAGS, standard modules,
    fees/attendance fields, templates, and sample questions).
    """
    from scripts.seed_sjbhs import seed as run_seed_script
    try:
        await run_seed_script()
        # Seed questions for standard clients
        from app.router.question_catalog import get_default_seed_questions
        for inst, r in [("sjbhs", "student"), ("sjbhs_student", "student"), ("sags_school", "student")]:
            await question_repo.seed_questions_if_empty(get_default_seed_questions(institution_id=inst, role=r))

        # Flush all in-memory caches so fresh data is loaded
        institution_repo.invalidate_all()
        module_repo.invalidate_all()
        registry_repo.invalidate_all()
        fields_repo.invalidate_all()
        templates_repo.invalidate_all()
        question_repo.flush_cache()
        return {"success": True, "message": "Standard configurations and sample questions seeded and loaded into MongoDB!"}
    except Exception as e:
        logger.error("seed_defaults_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Seed failed: {str(e)}")
