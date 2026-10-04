"""
PhinsIQ RAG Document Ingestion & Indexing Engine
=================================================

PURPOSE:
    Ingests institutional policy documents, lecturer notes, module materials,
    and PDF uploads. Chunks text, computes deterministic vector embeddings,
    and indexes them into the local SQLite vector database.

SUPPORTED FORMATS:
    - PDF (.pdf) via pypdf text extraction
    - Plain text (.txt)
    - Markdown (.md)

DOCUMENT STRUCTURE:
    data/
    └── rag/
        ├── documents/
        │   ├── module_1/
        │   ├── module_2/
        │   ├── module_3/
        │   ├── module_4/
        │   └── module_5/
        └── index/
            └── rag.sqlite3

HOW TO INDEX A NEW PDF / LECTURER NOTE:
    1. Place the new PDF or text file in data/rag/documents/<module_or_subject>/
    2. Run from the repository root:
       python -m app.rag.ingestion
    3. The new content is automatically chunked, embedded, and indexed.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterator, Sequence

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.vector_store import SQLiteVectorStore, VectorRecord, embed_text

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_DOCS_DIR = PROJECT_ROOT / "data" / "rag" / "documents"
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge_base"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract clean text content from all pages of a PDF document."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        pages_text: list[str] = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            stripped = text.strip()
            if stripped:
                pages_text.append(stripped)
        return "\n\n".join(pages_text)
    except Exception as exc:
        logger.warning("pdf_extraction_failed", path=str(pdf_path), error=str(exc))
        return ""


def chunk_text(text: str, chunk_size: int = 750, overlap: int = 100) -> list[str]:
    """Split text into overlapping, word-aligned chunks."""
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        extra = len(word) + (1 if current else 0)
        if current and current_len + extra > chunk_size:
            chunks.append(" ".join(current))
            carry: list[str] = []
            carry_len = 0
            for prior in reversed(current):
                n = len(prior) + (1 if carry else 0)
                if carry and carry_len + n > overlap:
                    break
                carry.insert(0, prior)
                carry_len += n
            current = carry
            current_len = carry_len
        current.append(word)
        current_len += len(word) + (1 if len(current) > 1 else 0)
    if current:
        chunks.append(" ".join(current))
    return chunks


def iter_records(
    directories: Path | Sequence[Path] | None = None,
) -> Iterator[VectorRecord]:
    """
    Scan provided directory or standard RAG and knowledge directories for
    .pdf, .txt, and .md documents, producing chunked VectorRecords.
    """
    if directories is None:
        target_dirs = [RAG_DOCS_DIR, KNOWLEDGE_DIR]
    elif isinstance(directories, Path):
        target_dirs = [directories]
    else:
        target_dirs = list(directories)

    seen_sources: set[str] = set()

    for base_dir in target_dirs:
        if not base_dir.exists():
            continue

        # Recursively discover all supported files
        files = sorted(
            [p for p in base_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".pdf", ".md"}]
        )

        for path in files:
            # Determine readable source name and document type
            try:
                rel_path = path.relative_to(base_dir).as_posix()
            except ValueError:
                rel_path = path.name

            source_name = f"{base_dir.name}/{rel_path}" if len(target_dirs) > 1 else rel_path
            if source_name in seen_sources:
                continue
            seen_sources.add(source_name)

            if path.suffix.lower() == ".pdf":
                text = extract_text_from_pdf(path).strip()
            else:
                text = path.read_text(encoding="utf-8", errors="replace").strip()

            if not text:
                continue

            # Identify document type (e.g. module_3, attendance_policy)
            doc_type = path.parent.name if path.parent.name.startswith("module_") else path.stem

            for index, chunk in enumerate(chunk_text(text)):
                yield VectorRecord(
                    source=path.name,
                    document_type=doc_type,
                    chunk_id=f"{path.stem}:{index:04d}",
                    content=chunk,
                    embedding=embed_text(chunk),
                )


def build_index(
    directory: Path | Sequence[Path] | None = None,
    db_path: Path | None = None,
) -> int:
    """Rebuild the SQLite vector index; return indexed chunk count."""
    path = db_path or Path(settings.rag_vector_db_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    records = list(iter_records(directory))
    count = SQLiteVectorStore(path).rebuild(records)

    # Also sync to legacy vector_db path if distinct, to keep existing tests aligned
    legacy_path = PROJECT_ROOT / "data" / "vector_db" / "rag.sqlite3"
    if legacy_path.resolve() != path.resolve():
        try:
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            SQLiteVectorStore(legacy_path).rebuild(records)
        except Exception:
            pass

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/rebuild the PhinsIQ document RAG index")
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Optional directory to index (defaults to data/rag/documents and data/knowledge_base)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Optional SQLite index path override",
    )
    args = parser.parse_args()

    count = build_index(args.source, args.db)
    target_db = str(args.db or settings.rag_vector_db_path)
    logger.info("rag_index_rebuilt", chunk_count=count, database=target_db)
    print(f"RAG index successfully rebuilt: {count} chunks indexed to {target_db}")


if __name__ == "__main__":
    main()
