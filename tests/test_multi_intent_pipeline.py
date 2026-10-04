"""Pipeline-level proof that multi-module queries call and combine both APIs."""

import asyncio
from types import SimpleNamespace

from app.models.chat import ChatRequest
from app.pipeline import pipeline as pipeline_module


def test_fee_balance_and_absence_execute_both_erp_handlers(monkeypatch):
    calls = []

    async def get_active_institution(_institution_id):
        return {"_id": "test_school"}

    async def get_allowed_modules(_role):
        return ["fees", "attendance"]

    async def get_fields(module):
        if module == "fees":
            return [{"name": "pending_amount", "aliases": ["fee balance", "balance"]}]
        return [{"name": "absent_count", "aliases": ["absent", "days absent"]}]

    async def get_registry(**kwargs):
        return {"module": kwargs["module"]}

    async def erp_call(*, registry_entry, **_kwargs):
        module = registry_entry["module"]
        calls.append(module)
        return {
            "fees": {"pending_amount": "₹12,500"},
            "attendance": {"absent_count": 6},
        }[module]

    def render(*, requested_fields, mapped_data, **_kwargs):
        return ". ".join(f"{field}={mapped_data[field]}" for field in requested_fields)

    monkeypatch.setattr(pipeline_module.institution_repo, "get_active_by_id", get_active_institution)
    monkeypatch.setattr(pipeline_module.role_repo, "get_allowed_modules", get_allowed_modules)
    monkeypatch.setattr(pipeline_module.fields_repo, "get_field_list", get_fields)
    monkeypatch.setattr(pipeline_module.registry_repo, "get_registry", get_registry)
    monkeypatch.setattr(pipeline_module.templates_repo, "get_templates", lambda _module: asyncio.sleep(0, result={}))
    monkeypatch.setattr(pipeline_module.erp_router, "call", erp_call)
    monkeypatch.setattr(pipeline_module.response_mapper, "map", lambda *, raw_response, **_kwargs: raw_response)
    monkeypatch.setattr(pipeline_module.array_aggregator, "aggregate", lambda **_kwargs: {})
    monkeypatch.setattr(pipeline_module.template_engine, "render", render)
    monkeypatch.setattr(pipeline_module.route_service, "get_routes", lambda **_kwargs: asyncio.sleep(0, result=[]))
    monkeypatch.setattr(pipeline_module.suggestion_engine, "get_suggestions", lambda **_kwargs: [])

    request = ChatRequest(
        institution_id="test_school",
        role="student",
        user_id="student_1",
        message="What is my fee balance and how many days was I absent?",
        claude=False,
    )
    response = asyncio.run(pipeline_module.pipeline._execute(request, "test-request"))

    assert sorted(calls) == ["attendance", "fees"]
    assert "₹12,500" in response.message
    assert "6" in response.message
