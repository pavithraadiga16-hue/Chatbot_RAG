"""
Module Detector
================

PURPOSE:
    Determines which ERP module a user's question is about.
    This is the first major "understanding" step in the pipeline.

    User: "What is my pending fee?"
    Module Detector → "fees"

    User: "How many classes did I miss?"
    Module Detector → "attendance"

HOW IT WORKS — Keyword Matching:
    We define keyword groups for each module. If the message contains
    words from a group, that module gets a confidence score.

    WHY KEYWORD MATCHING FIRST (not ML)?
        1. It's fast — no model inference time
        2. It's predictable — always gives the same result
        3. It's debuggable — you can see exactly why a module was chosen
        4. It handles 90%+ of real student/staff questions
        5. ML can be added LATER to replace or augment this

    For the remaining ~10% that keyword matching gets wrong or is unsure
    about, we fall back to Claude.

CONFIDENCE SCORING:
    Each matched keyword adds to the confidence score.
    - More matches = higher confidence
    - Matches in multiple modules = ambiguous question

    Example:
        "What is my fee attendance deduction?" → fees AND attendance both match
        System picks the higher score or flags for Claude review.

DESIGN FOR EXTENSIBILITY:
    Adding a new module requires ONLY adding its keywords to the dict below.
    No other Python code changes. The keywords could even be stored in
    MongoDB in the future (making it fully configuration-driven).
"""

from dataclasses import dataclass
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# Module Keyword Map
# =============================================================================
# Each module has a list of keywords. If any keyword appears in the message,
# that module gets a score boost.
#
# IMPORTANT: These keywords should be UNIQUE to their module where possible.
# Generic words like "how much" or "what is" don't help detection.
# Words like "pending", "fee", "installment" are strong fee signals.
#
# Weights: some keywords are stronger signals than others.
# "installment" → almost certainly fees (weight: 2.0)
# "amount" → could be fees or payroll (weight: 0.5)
#
MODULE_KEYWORDS: dict[str, list[tuple[str, float]]] = {
    "fees": [
        ("fee", 2.0),
        ("fees", 2.0),
        ("payment", 1.5),
        ("paid", 1.5),
        ("pay", 1.5),
        ("pending fee", 2.0),
        ("pending fees", 2.0),
        ("pending amount", 2.0),
        ("fee pending", 2.0),
        ("pending", 0.6),
        ("installment", 2.0),
        ("instalment", 2.0),
        ("challan", 2.0),
        ("concession", 2.0),
        ("balance", 1.0),
        ("dues", 1.5),
        ("outstanding", 1.5),
        ("amount", 0.5),
        ("rupee", 1.5),
        ("money", 0.8),
        ("exam fee", 2.0),
        ("tuition", 1.5),
        ("scholarship", 1.5),
    ],
    "attendance": [
        ("attendance", 2.0),
        ("attend", 2.0),
        ("present", 1.5),
        ("absent", 1.5),
        ("bunk", 2.0),
        ("bunked", 2.0),
        ("percentage", 1.0),  # lower weight — also used in other modules
        ("class", 0.5),
        ("miss", 1.0),
        ("proxy", 1.5),
        ("shortage", 1.5),
    ],
    "exam": [
        ("exam", 2.0),
        ("test", 1.5),
        ("result", 1.5),
        ("marks", 2.0),
        ("grade", 1.5),
        ("score", 1.5),
        ("assessment", 1.5),
        ("internal", 1.0),
        ("external", 1.0),
        ("semester exam", 2.0),
        ("hall ticket", 2.0),
    ],
    "calendar": [
        ("calendar", 2.0),
        ("calender", 2.0),
        ("academic calendar", 2.0),
        ("holiday", 2.0),
        ("holidays", 2.0),
        ("vacation", 2.0),
        ("reopen", 2.0),
        ("reopens", 2.0),
        ("reopening", 2.0),
        ("event", 1.5),
        ("events", 1.5),
        ("fest", 2.0),
        ("annual day", 2.0),
        ("sports day", 2.0),
        ("orientation", 1.5),
        ("tournament", 1.5),
        ("tourament", 1.5),
        ("assessment", 2.0),
        ("unit assessment", 2.0),
        ("final assessment", 2.0),
        ("mid-term", 2.0),
        ("ceremony", 2.0),
        ("investiture", 2.0),
        ("valedictory", 2.0),
        ("graduation", 2.0),
        ("ptm", 2.0),
        ("pta", 1.5),
        ("parenting", 1.5),
        ("bakrid", 2.0),
        ("muharram", 2.0),
        ("yoga day", 2.0),
        ("dasara", 2.0),
        ("christmas", 2.0),
        ("sankranthi", 2.0),
        ("good friday", 2.0),
        ("easter", 2.0),
        ("independence day", 2.0),
        ("republic day", 2.0),
        ("gandhi jayanti", 2.0),
        ("meraki", 2.0),
        ("mun", 2.0),
        ("aurum", 2.0),
        ("bifrost", 2.0),
        ("eucranium", 2.0),
        ("inigo", 2.0),
        ("dynamix", 2.0),
        ("cadence", 2.0),
        ("phenomenon", 2.0),
        ("infinity", 2.0),
        ("chilgala", 2.0),
        ("bala mela", 2.0),
        ("heats", 1.5),
        ("athletic", 1.5),
        ("aquatic", 1.5),
        ("public holiday", 2.0),
        ("festival", 1.5),
        ("what is there on", 2.5),
        ("what is on", 2.0),
        ("anything on", 2.0),
        ("events on", 2.0),
        ("event on", 2.0),
        ("holiday on", 2.0),
        ("is there on", 2.0),
        ("there on", 1.5),
        ("january", 1.0),
        ("february", 1.0),
        ("march", 1.0),
        ("april", 1.0),
        ("june", 1.0),
        ("july", 1.0),
        ("august", 1.0),
        ("september", 1.0),
        ("october", 1.0),
        ("november", 1.0),
        ("december", 1.0),
        ("oct", 1.0),
        ("nov", 1.0),
        ("dec", 1.0),
        ("sep", 1.0),
        ("aug", 1.0),
        ("jul", 1.0),
        ("jun", 1.0),
        ("jan", 1.0),
        ("feb", 1.0),
        ("mar", 1.0),
        ("apr", 1.0),
    ],
    "timetable": [
        ("timetable", 2.0),
        ("time table", 2.0),
        ("schedule", 1.5),
        ("class time", 2.0),
        ("period", 1.5),
        ("timing", 1.5),
        ("when is my class", 2.0),
    ],
    "library": [
        ("library", 2.0),
        ("book", 1.5),
        ("return", 1.0),
        ("issue", 1.0),
        ("borrow", 1.5),
        ("due date", 1.5),  # library book due date
        ("fine", 1.5),      # library fine
    ],
    "leave": [
        ("leave", 2.0),
        ("leave balance", 2.0),
        ("leave remaining", 2.0),
        ("leave days", 2.0),
        ("casual leave", 2.0),
        ("sick leave", 2.0),
        ("earned leave", 2.0),
        ("leave quota", 2.0),
    ],
    "payroll": [
        ("salary", 2.0),
        ("payroll", 2.0),
        ("payslip", 2.0),
        ("pay slip", 2.0),
        ("deduction", 1.5),
        ("increment", 1.5),
        ("ctc", 2.0),
        ("take home", 1.5),
        ("net pay", 1.5),
    ],
    "homework": [
        ("homework", 2.0),
        ("home work", 2.0),
        ("hw", 2.0),
        ("assignment", 2.0),
        ("assignments", 2.0),
        ("submission date", 2.0),
        ("submission", 1.5),
        ("submit", 1.5),
        ("homeworks", 2.0),
        ("pending homework", 2.0),
        ("completed homework", 2.0),
        ("homework pending", 2.0),
        ("homework completed", 2.0),
        ("homework status", 2.0),
    ],
    "notification": [
        ("notification", 2.0),
        ("notifications", 2.0),
        ("notice", 2.0),
        ("notices", 2.0),
        ("circular", 2.0),
        ("circulars", 2.0),
        ("announcement", 2.0),
        ("announcements", 2.0),
        ("recent notification", 2.0),
        ("latest notification", 2.0),
        ("recent notifications", 2.0),
        ("latest notifications", 2.0),
        ("latest circular", 2.0),
        ("recent circular", 2.0),
        ("recent notice", 2.0),
        ("latest notice", 2.0),
        ("notice board", 2.0),
    ],
    "notice": [
        ("notice", 2.0),
        ("notices", 2.0),
        ("notice board", 2.0),
        ("circular", 2.0),
        ("circulars", 2.0),
        ("announcement", 2.0),
        ("announcements", 2.0),
        ("notification", 2.0),
        ("notifications", 2.0),
    ],
    "profile": [
        ("profile", 2.0),
        ("my profile", 2.5),
        ("about me", 2.5),
        ("tell about me", 2.5),
        ("tell me about me", 2.5),
        ("about myself", 2.5),
        ("tell me about myself", 2.5),
        ("who am i", 2.5),
        ("my info", 2.0),
        ("my details", 2.0),
        ("personal information", 2.5),
        ("personal details", 2.5),
        ("personal info", 2.5),
        ("what is my name", 2.5),
        ("my name", 2.5),
        ("tell my name", 2.5),
        ("student name", 2.0),
        ("mother tongue", 2.0),
        ("father profession", 2.0),
        ("mother profession", 2.0),
        ("father occupation", 2.0),
        ("mother occupation", 2.0),
        ("father name", 2.0),
        ("father's name", 2.0),
        ("father", 1.5),
        ("mother name", 2.0),
        ("mother's name", 2.0),
        ("mother", 1.5),
        ("guardian name", 2.0),
        ("guardian's name", 2.0),
        ("guardian", 1.5),
        ("parents", 2.0),
        ("parent name", 2.0),
        ("date of birth", 2.0),
        ("dob", 2.0),
        ("birthday", 1.5),
        ("blood group", 2.0),
        ("blood type", 2.0),
        ("class teacher", 2.0),
        ("class teacher name", 2.0),
        ("house color", 2.0),
        ("house name", 2.0),
        ("which house", 2.0),
        ("admission number", 2.0),
        ("admission no", 2.0),
        ("application number", 2.0),
        ("student id", 2.0),
        ("roll number", 2.0),
        ("aadhaar", 2.0),
        ("aadhar", 2.0),
        ("aadhaar number", 2.0),
        ("apaar", 2.0),
        ("apaar id", 2.0),
        ("pen number", 2.0),
        ("pen no", 2.0),
        ("sts number", 2.0),
        ("sts no", 2.0),
        ("sat number", 2.0),
        ("sat no", 2.0),
        ("my address", 2.0),
        ("present address", 2.0),
        ("permanent address", 2.0),
        ("registered mobile", 2.0),
        ("father mobile", 2.0),
        ("mother mobile", 2.0),
        ("registered email", 2.0),
        ("second language", 2.0),
        ("third language", 2.0),
        ("caste", 1.5),
        ("religion", 1.5),
        ("nationality", 1.5),
        ("gender", 1.5),
    ],
    "study_materials": [
        ("study materials", 2.5),
        ("study material", 2.5),
        ("materials", 1.5),
        ("material", 1.5),
        ("portion", 2.0),
        ("portions", 2.0),
        ("worksheet", 2.0),
        ("worksheets", 2.0),
        ("notes", 2.0),
        ("lesson notes", 2.5),
        ("class notes", 2.0),
        ("revision notes", 2.5),
        ("learning material", 2.5),
        ("question bank", 2.0),
        ("question paper", 2.0),
        ("study note", 2.0),
        ("study notes", 2.0),
        ("latest study material", 2.5),
        ("recent study material", 2.5),
        ("new study material", 2.5),
        ("latest notes", 2.5),
        ("recent notes", 2.5),
    ],
}

# Words that STRONGLY suggest the user wants a summary/all data
SUMMARY_KEYWORDS = [
    "all", "complete", "everything", "full", "details", "show me",
    "tell me", "give me", "summary", "overview", "detail"
]

OVERALL_OVERVIEW_PATTERNS = [
    r"\b(?:my\s+)?academic\s+(?:info|information|details|overview|performance|report|summary|record|status|data)\b",
    r"\bmy\s+academic\b",
    r"\boverall\s+(?:performance|summary|details|report|status|overview|info|record|dashboard)\b",
    r"\boverall\b",
    r"\bcomplete\s+(?:dashboard|summary|report|overview|details|academic|profile and performance)\b",
    r"\bschool\s+(?:overview|dashboard|performance|summary|report|status)\b",
    r"\beverything\s+about\s+me\b",
    r"\bmy\s+entire\s+(?:details|info|record|status|performance|summary)\b",
    r"\bhow\s+am\s+i\s+doing\s+(?:in|at)\s+school\b",
    r"\bstudent\s+dashboard\b",
    r"\b360(?:\s+degree)?\s+(?:view|summary|overview|report|dashboard)\b",
    r"\bmy\s+school\s+summary\b",
    r"\ball\s+my\s+information\b",
]


from dataclasses import dataclass, field
from typing import Optional
import re
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModuleDetectionResult:
    """
    Result from module detection.

    Attributes:
        module:              Primary detected module ID, or None if unknown
        confidence:          Score from 0.0 to 1.0 (1.0 = very confident)
        method:              How the detection was made ('keyword', 'fallback', 'overall_overview')
        all_scores:          Raw scores for all modules (for debugging)
        modules:             List of all qualifying detected modules (for multi-module cross-queries)
        is_overall_overview: Whether the query requests an overall 360-degree academic dashboard
    """
    module: Optional[str]
    confidence: float
    method: str
    all_scores: dict[str, float]
    modules: list[str] = field(default_factory=list)
    is_overall_overview: bool = False


class ModuleDetector:
    """
    Detects which ERP module a user question is about.

    This class is stateless — it does not access MongoDB or any external service.
    All detection logic uses the keyword map defined at module level.
    """

    # Below this confidence, we're not sure about the module
    # and should consider Claude fallback
    CONFIDENCE_THRESHOLD = 0.40

    def detect(self, message: str) -> ModuleDetectionResult:
        """
        Detect the module(s) from a natural language message.

        Algorithm:
            1. Normalize the message (lowercase, strip)
            2. Check if the user is requesting an overall 360-degree academic overview/dashboard
            3. For each module, sum the weights of word-boundary matching keywords
            4. The module with the highest total score is primary
            5. Modules scoring above threshold are included in `modules` for cross-query support
            6. Normalize the winning score to 0.0–1.0

        Args:
            message: The user's normalized message text

        Returns:
            ModuleDetectionResult with primary module, all qualifying modules, and confidence
        """
        normalized = message.lower().strip()

        # Check for overall 360 overview / academic dashboard
        if not any(ex in normalized for ex in ("academic id", "academic calendar", "academic year", "academic session", "academic term")):
            for pat in OVERALL_OVERVIEW_PATTERNS:
                if re.search(pat, normalized):
                    logger.debug("module_detected_academic_overview", message_preview=normalized[:50])
                    return ModuleDetectionResult(
                        module="academic_overview",
                        confidence=1.0,
                        method="overall_overview",
                        all_scores={"academic_overview": 5.0},
                        modules=["academic_overview"],
                        is_overall_overview=True,
                    )

        scores: dict[str, float] = {}

        for module, keywords in MODULE_KEYWORDS.items():
            score = 0.0
            for keyword, weight in keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, normalized):
                    score += weight
            if score > 0:
                scores[module] = score

        if not scores:
            from app.understanding.semantic_matcher import semantic_matcher
            semantic_res = semantic_matcher.match(normalized)
            if semantic_res.matched and semantic_res.confidence >= 0.70:
                logger.info(
                    "module_detected_via_semantic_match",
                    module=semantic_res.module,
                    pattern=semantic_res.matched_pattern,
                    confidence=semantic_res.confidence,
                )
                return ModuleDetectionResult(
                    module=semantic_res.module,
                    confidence=semantic_res.confidence,
                    method="semantic_match",
                    all_scores={semantic_res.module or "unknown": 5.0},
                    modules=[semantic_res.module] if semantic_res.module else [],
                    is_overall_overview=semantic_res.is_overall_overview,
                )

            logger.debug("module_detection_no_match", message_preview=normalized[:50])
            return ModuleDetectionResult(
                module=None,
                confidence=0.0,
                method="keyword",
                all_scores={},
                modules=[],
            )

        # Find the winner
        best_module = max(scores, key=lambda m: scores[m])
        best_score = scores[best_module]

        # Gather all qualifying modules (for cross-module questions e.g. fees + attendance)
        qualifying_modules = [best_module]
        for m, s in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if m != best_module and s >= 2.0 and s >= (best_score * 0.5):
                qualifying_modules.append(m)

        # Normalize confidence to 0.0–1.0
        confidence = min(best_score / 4.0, 1.0)

        # If keyword confidence is low, verify with semantic matcher
        if confidence < self.CONFIDENCE_THRESHOLD:
            from app.understanding.semantic_matcher import semantic_matcher
            semantic_res = semantic_matcher.match(normalized)
            if semantic_res.matched and semantic_res.confidence > confidence:
                logger.info(
                    "module_boosted_via_semantic_match",
                    module=semantic_res.module,
                    pattern=semantic_res.matched_pattern,
                    confidence=semantic_res.confidence,
                )
                return ModuleDetectionResult(
                    module=semantic_res.module,
                    confidence=semantic_res.confidence,
                    method="semantic_match",
                    all_scores=scores,
                    modules=[semantic_res.module] if semantic_res.module else qualifying_modules,
                    is_overall_overview=semantic_res.is_overall_overview,
                )

        # Single module penalty check if ambiguous and only 1 module wanted
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(qualifying_modules) == 1 and len(sorted_scores) >= 2 and sorted_scores[1] > sorted_scores[0] * 0.5:
            confidence *= 0.75

        logger.debug(
            "module_detected",
            primary_module=best_module,
            all_modules=qualifying_modules,
            confidence=round(confidence, 3),
            scores=scores,
        )

        return ModuleDetectionResult(
            module=best_module,
            confidence=round(confidence, 3),
            method="keyword",
            all_scores=scores,
            modules=qualifying_modules,
        )

    def wants_summary(self, message: str) -> bool:
        """
        Returns True if the user's message suggests they want all details,
        not a specific single field.

        Example:
            "What is my pending fee?" → False (specific field)
            "Show me my complete fee details" → True (summary)
            "What is my fee?" → True (vague — show summary)
        """
        normalized = message.lower()
        return any(kw in normalized for kw in SUMMARY_KEYWORDS)


# Module-level singleton — the detector is stateless so one instance is enough
module_detector = ModuleDetector()
