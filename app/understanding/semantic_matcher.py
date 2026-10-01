"""
Semantic Intent & Pattern Matcher
=================================

PURPOSE:
    Provides ultra-fast (< 1ms) fuzzy & token-set semantic matching on user questions.
    Ensures that once a question pattern is known or answered by Claude, neither the
    same user nor ANY other user needs to hit Claude again.

FEATURES:
    1. RapidFuzz Token-Set & Levenshtein matching with sub-millisecond latency.
    2. Canonical question patterns for identity, academic overview, and all modules.
    3. Self-learning: automatically registers questions from Claude fallback into MongoDB
       and active memory cache.
    4. Evaluates intent and routes to native FastAPI pipeline with live user ERP data.
"""

import re
from typing import Optional, Any
from pydantic import BaseModel
from rapidfuzz import fuzz

from app.core.database import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)


class SemanticMatchResult(BaseModel):
    """Result of semantic question pattern matching."""
    matched: bool
    module: Optional[str] = None
    action: str = "summary"
    is_overall_overview: bool = False
    confidence: float = 0.0
    matched_pattern: Optional[str] = None
    similarity_score: float = 0.0


# Base Canonical Intent Corpus
DEFAULT_INTENT_PATTERNS: dict[str, dict[str, Any]] = {
    # 1. Identity & Profile Intent (Strict Profile only)
    "identity_profile": {
        "module": "profile",
        "action": "summary",
        "is_overall_overview": False,
        "patterns": [
            "who am i",
            "do you know me",
            "do u know me",
            "do you remember me",
            "do u remember me",
            "tell about me",
            "tell about myself",
            "about me",
            "about myself",
            "my profile",
            "my profile details",
            "personal details",
            "my personal information",
            "what is my profile",
            "student personal details",
        ],
    },
    # 2. 360-degree Academic & School Overview Dashboard / Progress Snapshot
    "academic_overview": {
        "module": "academic_overview",
        "action": "summary",
        "is_overall_overview": True,
        "patterns": [
            "my academic info",
            "my academic information",
            "academic details",
            "overall performance",
            "my overall performance",
            "overall summary",
            "my overall info",
            "everything about me",
            "complete report",
            "school dashboard",
            "how am i doing in school",
            "how am i doing",
            "all my details",
            "show everything about me",
            "full academic status",
            "360 degree overview",
            "my school report",
            "i want know my self how much i better",
            "how much i better",
            "how can i improve",
            "how to improve my performance",
            "my progress report",
            "academic progress snapshot",
            "evaluate my performance",
            "am i doing well in school",
            "areas of improvement",
        ],
    },
    # 3. Homework Intent
    "homework_summary": {
        "module": "homework",
        "action": "summary",
        "is_overall_overview": False,
        "patterns": [
            "how much homework is pending",
            "my homework assignments",
            "pending homework",
            "total homework",
            "what homework do i have",
            "homework list",
            "show all homework",
        ],
    },
    # 4. Attendance Intent
    "attendance_summary": {
        "module": "attendance",
        "action": "summary",
        "is_overall_overview": False,
        "patterns": [
            "what is my attendance percentage",
            "attendance rate",
            "how many days was i absent",
            "how many days was i present",
            "total classes attended",
            "my attendance record",
        ],
    },
    # 5. Fees Intent
    "fees_summary": {
        "module": "fees",
        "action": "summary",
        "is_overall_overview": False,
        "patterns": [
            "how much fee is pending",
            "what is my pending fee",
            "my fee payment status",
            "total fee paid",
            "how much fee do i owe",
            "fee dues",
        ],
    },
    # 6. Study Materials Intent
    "study_materials_summary": {
        "module": "study_materials",
        "action": "summary",
        "is_overall_overview": False,
        "patterns": [
            "show study materials",
            "my lesson portions",
            "class worksheets",
            "study materials list",
            "notes and portions",
            "download worksheets",
        ],
    },
    # 7. Calendar & Holiday Intent
    "calendar_summary": {
        "module": "calendar",
        "action": "summary",
        "is_overall_overview": False,
        "patterns": [
            "upcoming school holidays",
            "when is the next holiday",
            "school reopening date",
            "academic calendar events",
            "list of holidays this year",
        ],
    },
    # 8. Notification & Circular Intent
    "notification_summary": {
        "module": "notification",
        "action": "summary",
        "is_overall_overview": False,
        "patterns": [
            "recent school notifications",
            "any new circulars",
            "school announcements",
            "latest notices",
            "recent messages from school",
        ],
    },
}


class SemanticMatcher:
    """Fast semantic intent matcher using RapidFuzz and persistent learned patterns."""

    def __init__(self, match_threshold: float = 78.0) -> None:
        self.match_threshold = match_threshold
        self._learned_cache: list[dict[str, Any]] = []
        self._init_base_corpus()

    def _init_base_corpus(self) -> None:
        """Initialize the in-memory pattern corpus."""
        self._learned_cache.clear()
        for intent_key, conf in DEFAULT_INTENT_PATTERNS.items():
            for p in conf["patterns"]:
                self._learned_cache.append({
                    "pattern": p.strip().lower(),
                    "module": conf["module"],
                    "action": conf.get("action", "summary"),
                    "is_overall_overview": conf.get("is_overall_overview", False),
                    "intent": intent_key,
                })

    def _normalize_text(self, text: str) -> str:
        """Normalize query text for clean comparison."""
        t = text.lower().strip()
        # Replace common slang/shortcuts
        t = re.sub(r"\bu\b", "you", t)
        t = re.sub(r"\br\b", "are", t)
        t = re.sub(r"\bur\b", "your", t)
        # Remove punctuation
        t = re.sub(r"[^\w\s]", " ", t)
        return " ".join(t.split())

    def match(self, message: str) -> SemanticMatchResult:
        """
        Match a user query against known intent patterns.

        Returns:
            SemanticMatchResult with matched module and similarity score.
        """
        normalized = self._normalize_text(message)
        if not normalized:
            return SemanticMatchResult(matched=False)

        best_score = 0.0
        best_entry: Optional[dict[str, Any]] = None

        for entry in self._learned_cache:
            pat = entry["pattern"]
            norm_pat = self._normalize_text(pat)

            # 1. Exact match after normalization
            if normalized == norm_pat:
                return SemanticMatchResult(
                    matched=True,
                    module=entry["module"],
                    action=entry.get("action", "summary"),
                    is_overall_overview=entry.get("is_overall_overview", False),
                    confidence=1.0,
                    matched_pattern=pat,
                    similarity_score=100.0,
                )

            # Subject / academic questions guardrail for self-identity intents
            words_norm = normalized.split()
            words_pat = norm_pat.split()
            if entry.get("intent") == "identity_profile":
                academic_terms = {
                    "math", "maths", "mathematics", "science", "physics", "chemistry", "biology",
                    "history", "geography", "algebra", "geometry", "calculus", "question", "questions",
                    "solve", "equation", "formula", "concept", "theorem", "syllabus", "subject", "study"
                }
                if any(term in words_norm for term in academic_terms):
                    continue
                self_terms = {"me", "myself", "my", "i"}
                if not any(st in words_norm for st in self_terms):
                    continue

            # Length penalty ratio so a short 3-word pattern doesn't falsely match a long question
            len_ratio = min(len(words_norm), len(words_pat)) / max(len(words_norm), len(words_pat)) if words_norm and words_pat else 1.0

            score_sort = fuzz.token_sort_ratio(normalized, norm_pat)
            score_ratio = fuzz.ratio(normalized, norm_pat)
            score_token = fuzz.token_set_ratio(normalized, norm_pat) * (len_ratio ** 0.5)

            score = max(score_sort, score_ratio, score_token)

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score >= self.match_threshold:
            conf = round(best_score / 100.0, 2)
            logger.info(
                "semantic_intent_matched",
                query=message,
                matched_pattern=best_entry["pattern"],
                module=best_entry["module"],
                score=best_score,
            )
            return SemanticMatchResult(
                matched=True,
                module=best_entry["module"],
                action=best_entry.get("action", "summary"),
                is_overall_overview=best_entry.get("is_overall_overview", False),
                confidence=conf,
                matched_pattern=best_entry["pattern"],
                similarity_score=best_score,
            )

        return SemanticMatchResult(matched=False, similarity_score=best_score)

    async def learn_pattern(
        self,
        question: str,
        module: str,
        action: str = "summary",
        is_overall_overview: bool = False,
    ) -> None:
        """
        Register a new question pattern into active memory and MongoDB
        so future queries match locally without hitting Claude.
        """
        clean_q = question.strip().lower()
        if not clean_q or len(clean_q) < 3:
            return

        # Check if already exists in active cache
        if any(e["pattern"] == clean_q for e in self._learned_cache):
            return

        entry = {
            "pattern": clean_q,
            "module": module,
            "action": action,
            "is_overall_overview": is_overall_overview,
        }
        self._learned_cache.append(entry)

        # Save to MongoDB asynchronously
        try:
            db = get_database()
            await db.learned_patterns.replace_one(
                {"pattern": clean_q},
                entry,
                upsert=True,
            )
            logger.info("pattern_learned_and_saved", pattern=clean_q, module=module)
        except Exception as exc:
            logger.warning("pattern_save_db_error", error=str(exc))

    async def load_learned_patterns_from_db(self) -> int:
        """Load previously learned patterns from MongoDB on startup."""
        try:
            db = get_database()
            cursor = db.learned_patterns.find({})
            docs = await cursor.to_list(length=1000)
            count = 0
            for doc in docs:
                pat = doc.get("pattern")
                if pat and not any(e["pattern"] == pat for e in self._learned_cache):
                    self._learned_cache.append({
                        "pattern": pat,
                        "module": doc.get("module"),
                        "action": doc.get("action", "summary"),
                        "is_overall_overview": doc.get("is_overall_overview", False),
                    })
                    count += 1
            logger.info("learned_patterns_loaded_from_db", count=count)
            return count
        except Exception as exc:
            logger.warning("load_learned_patterns_failed", error=str(exc))
            return 0


semantic_matcher = SemanticMatcher()
