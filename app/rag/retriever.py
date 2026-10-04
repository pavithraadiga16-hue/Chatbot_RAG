"""Policy document retrieval for the PhinsIQ chat pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.ingestion import PROJECT_ROOT
from app.rag.vector_store import SQLiteVectorStore

logger = get_logger(__name__)
MIN_RELEVANCE = 0.10


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    document_type: str
    chunk_id: str
    content: str
    score: float


class RAGRetriever:
    def _store(self) -> SQLiteVectorStore:
        path = Path(settings.rag_vector_db_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            legacy_path = PROJECT_ROOT / "data" / "vector_db" / "rag.sqlite3"
            if legacy_path.exists():
                path = legacy_path
        return SQLiteVectorStore(path)

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Return top relevant chunks; missing/corrupt indexes fail closed."""
        store = self._store()
        try:
            ranked = store.search(query, top_k=top_k or settings.rag_top_k)
        except Exception as exc:
            logger.warning("rag_retrieval_failed", error=str(exc))
            return []
        hits = [
            RetrievedChunk(r.source, r.document_type, r.chunk_id, r.content, score)
            for r, score in ranked if score >= MIN_RELEVANCE
        ]
        logger.info(
            "rag_retrieval_complete",
            top_k=top_k or settings.rag_top_k,
            retrieved_documents=[hit.source for hit in hits],
            scores=[round(hit.score, 3) for hit in hits],
        )
        return hits


rag_retriever = RAGRetriever()

