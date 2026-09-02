"""
PhinsIQ Repositories
====================
"""

from app.repositories.institution import institution_repo, role_repo
from app.repositories.module_repo import module_repo
from app.repositories.registry import fields_repo, registry_repo, templates_repo

__all__ = [
    "institution_repo",
    "role_repo",
    "module_repo",
    "registry_repo",
    "fields_repo",
    "templates_repo",
]
