"""Small persistent vector store backed by SQLite and deterministic hashed vectors."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

VECTOR_DIMENSIONS = 512
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
SYNONYMS = {
    "minimum": "required", "requirement": "required", "requirements": "required", "requires": "required",
    "threshold": "required", "least": "required", "attendance": "attendance",
    "absent": "absence", "absence": "absence", "condonation": "condonation",
    "eligibility": "eligible", "qualify": "eligible", "qualified": "eligible",
    "criteria": "eligible", "documents": "document", "papers": "document",
    "scholarships": "scholarship", "exams": "examination", "exam": "examination",
    "tests": "examination", "rules": "rule", "regulations": "rule",
    "holidays": "holiday", "leave": "leave", "payment": "fee", "payments": "fee",
    "tuition": "fee", "fees": "fee", "calendar": "calendar",
    "submit": "document", "application": "document", "applications": "document", "form": "document",
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is", "it",
    "me", "my", "of", "on", "or", "our", "the", "to", "what", "when", "where", "which", "who",
    "with", "you", "your", "explain", "tell", "about", "please", "can",
    "policy", "policies", "rule", "rules", "regulation", "regulations", "guideline", "guidelines",
}


def normalized_terms(text: str) -> set[str]:
    return {
        SYNONYMS.get(token, token)
        for token in TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS
    }


def _feature_index(feature: str) -> tuple[int, float]:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "little")
    return value % VECTOR_DIMENSIONS, (1.0 if value & (1 << 63) else -1.0)


def embed_text(text: str) -> list[float]:
    """Create a normalized feature-hashing embedding without model downloads."""
    tokens = [SYNONYMS.get(token, token) for token in TOKEN_RE.findall(text.lower())]
    vector = [0.0] * VECTOR_DIMENSIONS
    for token in tokens:
        idx, sign = _feature_index("w:" + token)
        vector[idx] += sign
        # Character trigrams make spelling variants and inflections less brittle.
        padded = f"^{token}$"
        for i in range(max(0, len(padded) - 2)):
            idx, sign = _feature_index("c:" + padded[i:i + 3])
            vector[idx] += sign * 0.15
    for left, right in zip(tokens, tokens[1:]):
        idx, sign = _feature_index("b:" + left + "_" + right)
        vector[idx] += sign * 0.6

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude:
        vector = [value / magnitude for value in vector]
    return vector


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


@dataclass(frozen=True)
class VectorRecord:
    source: str
    document_type: str
    chunk_id: str
    content: str
    embedding: list[float]


class SQLiteVectorStore:
    """SQLite-backed local vector index; similarity is computed with cosine distance."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute(
            """CREATE TABLE IF NOT EXISTS rag_chunks (
                source TEXT NOT NULL,
                document_type TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                PRIMARY KEY (source, chunk_id)
            )"""
        )
        return connection

    def rebuild(self, records: Iterable[VectorRecord]) -> int:
        rows = [
            (r.source, r.document_type, r.chunk_id, r.content, json.dumps(r.embedding))
            for r in records
        ]
        with self._connect() as connection:
            connection.execute("DELETE FROM rag_chunks")
            connection.executemany(
                "INSERT INTO rag_chunks(source, document_type, chunk_id, content, embedding) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    def search(self, query: str, top_k: int = 3) -> list[tuple[VectorRecord, float]]:
        query_vector = embed_text(query)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT source, document_type, chunk_id, content, embedding FROM rag_chunks"
            ).fetchall()
        scored: list[tuple[VectorRecord, float]] = []
        query_terms = normalized_terms(query)
        for source, document_type, chunk_id, content, encoded in rows:
            vector = json.loads(encoded)
            vector_score = cosine_similarity(query_vector, vector)
            content_terms = normalized_terms(content)
            lexical_score = (
                len(query_terms & content_terms) / len(query_terms)
                if query_terms else 0.0
            )
            document_terms = normalized_terms(document_type.replace("_", " "))
            metadata_score = (
                len(query_terms & document_terms) / len(query_terms)
                if query_terms else 0.0
            )
            # Exact corpus-topic and term coverage keeps relevant policy facts
            # ahead of unrelated chunks that happen to collide in a compact vector.
            score = (0.60 * lexical_score) + (0.25 * metadata_score) + (0.15 * max(0.0, vector_score))
            scored.append((VectorRecord(source, document_type, chunk_id, content, vector), score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:max(0, top_k)]

    def count(self) -> int:
        if not self.path.exists():
            return 0
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0])

