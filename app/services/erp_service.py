"""
ERP Service Interface
=====================
Connects query requests to institution ERP APIs and mapped student data.
"""

from app.router.api_router import erp_router, ERPAPIRouter
from app.router.response_mapper import response_mapper
from app.router.array_aggregator import array_aggregator

__all__ = ["erp_router", "ERPAPIRouter", "response_mapper", "array_aggregator"]
