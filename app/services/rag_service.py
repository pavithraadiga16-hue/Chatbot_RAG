"""
RAG Service Interface
=====================
Exports the document RAG service from the app.rag package.
"""

from app.rag.rag_service import rag_service, RAGService, RAGAnswer

__all__ = ["rag_service", "RAGService", "RAGAnswer"]
