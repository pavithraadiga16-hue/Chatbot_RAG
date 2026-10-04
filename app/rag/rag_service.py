"""
PhinsIQ Institutional Document RAG Service
==========================================

PURPOSE:
    Retrieves and generates answers strictly from institutional documents,
    policy texts, lecturer notes, and uploaded module PDFs.

CONSTRAINTS:
    - Zero Cloud LLM calls (No Gemini, OpenAI, Claude, Anthropic, or Qwen).
    - If relevant context is found in uploaded documents: returns answer extracted
      directly from the retrieved context.
    - If relevant context is NOT found: returns a clear message stating the
      information is not available in the institutional documents. Never hallucinates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.retriever import RetrievedChunk, rag_retriever
from app.rag.vector_store import normalized_terms

logger = get_logger(__name__)

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
KEY_FACT_RE = re.compile(
    r"\b\d+(?:\.\d+)?%\b|\b(eligible|eligibility|condonation|must|expected|required|"
    r"submit|not automatic|not guaranteed|subject-wise|due date|module|chapter|syllabus|definition|formula)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[str]
    confidence: float


class RAGService:
    @staticmethod
    def _extract_evidence(question: str, hits: list[RetrievedChunk]) -> str:
        """
        Synthesize/extract the most query-relevant facts from retrieved chunks
        without inventing or modifying external facts.
        """
        q_terms = normalized_terms(question)
        ranked: list[tuple[float, str]] = []
        seen: set[str] = set()

        for hit in hits:
            for raw in SENTENCE_RE.split(hit.content):
                sentence = raw.strip(" \t-*•\r\n")
                if len(sentence) < 15 or sentence.lower() in seen:
                    continue
                if "DUMMY DEVELOPMENT SAMPLE" in sentence.upper() or sentence.upper().startswith("NORTHSTAR INSTITUTE"):
                    continue
                seen.add(sentence.lower())

                terms = normalized_terms(sentence)
                lexical = len(q_terms & terms) / len(q_terms) if q_terms else 0.0
                boost = 0.25 if KEY_FACT_RE.search(sentence) else 0.0
                score = lexical + boost
                ranked.append((score, sentence))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [text for score, text in ranked[:5] if score > 0.04]

        if not selected:
            for hit in hits:
                clean = hit.content.replace("DUMMY DEVELOPMENT SAMPLE - FOR LOCAL TESTING ONLY", "").strip()
                lines = [l.strip() for l in clean.split("\n") if l.strip() and not l.startswith("===") and "DUMMY" not in l.upper()]
                if lines:
                    return "\n".join(lines[:4])
            return ""

        return "\n".join(f"• {sentence}" for sentence in selected)

    async def answer(self, question: str) -> RAGAnswer | None:
        """
        Retrieve relevant institutional/academic document content.
        Returns RAGAnswer if relevant context is found, else None.
        """
        logger.info("[RAG] Searching documents", query=question)
        print(f"[RAG] Searching documents for: {question}")

        hits = rag_retriever.retrieve(question)
        if not hits:
            logger.info("[RAG] No relevant context found in available documents")
            print(f"[RAG] No relevant context found in available documents")
            return None

        # Topic term filtering to keep results focused on intended subject/module
        generic_terms = {"required", "eligible", "document", "criteria", "minimum", "least", "explain", "what", "policy"}
        topic_terms = normalized_terms(question) - generic_terms
        topic_hits = [
            hit for hit in hits
            if topic_terms & normalized_terms(hit.document_type.replace("_", " "))
        ]
        if topic_hits:
            hits = topic_hits

        sources = list(dict.fromkeys(hit.source for hit in hits))
        confidence = round(hits[0].score, 3)

        logger.info(
            "[RAG] Relevant context found in: " + ", ".join(sources),
            sources=sources,
            confidence=confidence,
        )
        print(f"[RAG] Relevant context found in: {', '.join(sources)}")

        answer_text = self._extract_evidence(question, hits)
        if not answer_text:
            logger.info("[RAG] No extractable evidence from retrieved chunks")
            return None

        if any("DUMMY DEVELOPMENT SAMPLE" in hit.content for hit in hits):
            answer_text = "Development sample only (not an official policy):\n\n" + answer_text

        logger.info("[RAG] Response generated", confidence=confidence, sources=sources)
        print(f"[RAG] Response generated from: {', '.join(sources)}")

        return RAGAnswer(
            answer=answer_text,
            sources=sources,
            confidence=confidence,
        )


rag_service = RAGService()
