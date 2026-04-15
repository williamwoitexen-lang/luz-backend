"""Service package exports.

This module re-exports functions implemented in submodules so external
imports can continue to use `from app.services import ...`.
"""

from .document_service import DocumentService, ingest_document_file, delete_document_version
from .admin_service import AdminService
from .sqlserver_documents import (
    create_document,
    create_version,
    get_document,
    get_document_versions,
    delete_document,
    get_latest_version
)

__all__ = [
    "DocumentService",
    "AdminService",
    "ingest_document_version",
    "delete_document_version",
    "create_document",
    "create_version",
    "get_document",
    "get_document_versions",
    "delete_document",
    "get_latest_version",
]



