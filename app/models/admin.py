"""
Admin Management Models
=======================

PURPOSE:
    Pydantic schemas for the Admin Configuration API.
    Enables full CRUD operations for institutions, modules, api_registry,
    fields, and response templates through the web UI.
"""

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Institution Models
# =============================================================================

class ApiConfig(BaseModel):
    base_url: str = Field(..., description="Base URL of the institution's ERP API")
    auth_type: str = Field("none", description="Auth type: none, bearer, basic, header, or custom")
    auth_token: Optional[str] = Field(None, description="Optional bearer token or API key")
    headers: dict[str, str] = Field(
        default_factory=lambda: {"Content-Type": "application/json", "Accept": "application/json"}
    )


class InstitutionModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique institution slug, e.g., sjbhs, sags_school")
    name: str = Field(..., description="Full display name of the institution")
    short_name: str = Field(..., description="Short acronym or code")
    status: str = Field("active", description="Status: active or inactive")
    api_config: ApiConfig
    roles: list[str] = Field(default_factory=lambda: ["student", "staff"])


# =============================================================================
# Module Models
# =============================================================================

class ModuleModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique module slug, e.g. fees, attendance, hostel")
    name: str = Field(..., description="Display name, e.g. Fees, Attendance, Hostel")
    status: str = Field("active", description="Status: active or inactive")
    description: str = Field("", description="Module description")


# =============================================================================
# API Registry Models
# =============================================================================

class RequestConfig(BaseModel):
    method: str = Field("POST", description="HTTP method: GET, POST, PUT")
    path: str = Field(..., description="Relative API endpoint path, e.g., /student/apiviewFeePaymentInfo")
    body_template: Optional[dict[str, Any]] = Field(
        default_factory=lambda: {"row_id": "{user_id}"},
        description="JSON body template with placeholders like {user_id}",
    )
    content_type: str = Field("application/json", description="Request Content-Type")
    headers: Optional[dict[str, str]] = Field(default=None, description="Optional custom headers")


class ApiRegistryModel(BaseModel):
    institution_id: str = Field(..., description="Institution ID, e.g. sjbhs")
    role: str = Field("student", description="Role, e.g. student or staff")
    module: str = Field(..., description="Module slug, e.g. fees")
    action: str = Field("summary", description="Action slug, e.g. summary or percentage")
    request: RequestConfig
    response_root: Optional[str] = Field(None, description="Top-level response JSON key (if nested)")
    response_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value mapping: {phinsiq_standard_field: erp_response_path}",
    )


# =============================================================================
# Fields & Aliases Models
# =============================================================================

class FieldItem(BaseModel):
    name: str = Field(..., description="Standard PhinsIQ field name, e.g. total_fee, pending_amount")
    label: str = Field(..., description="User-friendly display label, e.g. Total Fee")
    erp_key: Optional[str] = Field(None, description="Default ERP key fallback")
    format: str = Field("currency", description="Format type: currency, percentage, boolean, text")
    aliases: list[str] = Field(default_factory=list, description="NLP keywords/phrases to match this field")


class FieldsDocModel(BaseModel):
    module: str = Field(..., description="Module slug, e.g. fees, attendance")
    fields: list[FieldItem] = Field(default_factory=list, description="List of field definitions")


# =============================================================================
# Response Template Models
# =============================================================================

class TemplateModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    module: str = Field(..., description="Target module slug")
    action: str = Field("summary", description="Target action, usually 'summary'")
    summary_template: str = Field(..., description="Jinja2 summary template string")
    field_templates: dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping single field names to Jinja2 template strings",
    )


# =============================================================================
# Sample Question Models
# =============================================================================

class QuestionModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id", description="Optional unique identifier")
    institution_id: str = Field("sjbhs", description="Target institution ID, e.g., sjbhs, sags_school, or 'all'")
    role: str = Field("student", description="Target user role, e.g., student, staff, parent, or 'all'")
    module: str = Field("fees", description="Target module, e.g., fees, attendance, homework")
    category_label: Optional[str] = Field(None, description="Display label for optgroup, e.g. 💰 Fees & Payments")
    question: str = Field(..., description="Natural language question string")
    field: Optional[str] = Field("", description="Target mapped field, e.g., pending_fee, attendance_percentage")
    description: Optional[str] = Field("", description="Helpful description of what this query answers")
    route: Optional[str] = Field("/dashboard", description="Client screen route, e.g. /fees, /attendance")
    display_order: int = Field(0, description="Sorting order in dropdowns")
    is_active: bool = Field(True, description="Whether this prompt is visible to users")


# =============================================================================
# ERP Live Tester Models
# =============================================================================

class TestErpRequest(BaseModel):
    base_url: str = Field(..., description="Institution ERP base URL")
    method: str = Field("POST", description="HTTP method")
    path: str = Field(..., description="Endpoint path")
    body: Optional[dict[str, Any]] = Field(default=None, description="Request JSON payload")
    headers: Optional[dict[str, str]] = Field(default=None, description="Request headers")


class TestErpResponse(BaseModel):
    status_code: int
    success: bool
    data: Optional[Any] = None
    extracted_keys: list[str] = Field(default_factory=list, description="List of all dot-notation keys found in response")
    error: Optional[str] = None
