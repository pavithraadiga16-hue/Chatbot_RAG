"""
Field Detector
================

PURPOSE:
    After the module is detected, the field detector determines WHICH
    specific data fields the user is asking for within that module.

    Module detected: "fees"
    User: "What is my pending fee?"
    Field Detector → ["pending_amount"]

    User: "What is my total and paid amount?"
    Field Detector → ["total_fee", "paid_amount"]

    User: "Show all my fee details"
    Field Detector → [] (empty = show summary)

HOW IT WORKS:
    Uses the 'aliases' from the MongoDB 'fields' collection.
    For each field, we check if any of its aliases appear in the message.

    WHY USE DB ALIASES INSTEAD OF HARDCODED KEYWORDS?
        Hardcoded: You'd need to update Python code to add a new alias
        DB-driven: Add an alias in MongoDB → works immediately for all institutions

    EXAMPLE ALIASES for "pending_amount":
        ["pending", "pending fee", "due", "balance", "outstanding", "remaining"]

    If "remaining" is in the user's message → detected field: "pending_amount"

MULTI-FIELD DETECTION:
    The detector can return multiple fields from a single message.
    "What is my total and paid amount?" → ["total_fee", "paid_amount"]

    This powers multi-field responses without requiring Claude.
"""

from dataclasses import dataclass, field
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

# Keywords that indicate the user wants everything, not a specific field
FULL_SUMMARY_TRIGGERS = [
    # Generic
    "all", "complete", "everything", "full details", "all details",
    "show all", "complete details", "show everything", "all info",
    # Fees
    "fee details", "fee summary", "entire fee", "fee information", "fee info",
    # Attendance
    "attendance details", "attendance summary", "attendance report",
    "full attendance", "complete attendance", "all attendance",
    "full attendance report", "overall attendance",
    # Holiday & Calendar
    "holiday details", "holiday summary", "calendar details",
    "academic calendar", "school calendar", "full calendar", "all events", "event calendar",
]


@dataclass
class FieldDetectionResult:
    """
    Result from field detection.

    Attributes:
        fields:         List of detected field names (e.g., ["pending_amount"])
        wants_summary:  True if user asked for all/complete data
        confidence:     Detection confidence (0.0–1.0)
    """
    fields: list[str] = field(default_factory=list)
    wants_summary: bool = False
    confidence: float = 0.0


class FieldDetector:
    """
    Detects which specific fields within a module the user is asking about.

    Requires the fields configuration from MongoDB (loaded by the pipeline
    from the 'fields' collection for the detected module).

    WHY LOAD FIELDS FROM DB?
        Different modules have different fields.
        "fees" has: pending_amount, total_fee, paid_amount, installment...
        "attendance" has: percentage, absent_dates, total_classes...

        By loading from DB, we don't need to hardcode field names per module.
        Adding a new field to a module is just a MongoDB update.
    """

    def detect(
        self,
        message: str,
        field_definitions: list[dict],
    ) -> FieldDetectionResult:
        """
        Detect which fields are requested in the user's message.

        Algorithm:
            1. Check if user wants everything (summary keywords)
            2. For each field definition, check if any alias appears in message
            3. Return all matched fields

        Args:
            message:          The user's normalized message
            field_definitions: List of field dicts from MongoDB 'fields' collection.
                               Each dict has: name, aliases, erp_key, format.

        Returns:
            FieldDetectionResult with detected field names
        """
        normalized = message.lower().strip()

        # Check if user wants a complete summary
        if self._wants_full_summary(normalized):
            logger.debug("field_detection_summary_requested", message_preview=normalized[:50])
            return FieldDetectionResult(
                fields=[],
                wants_summary=True,
                confidence=0.9,
            )

        import re

        # Flatten all (alias, field_name) pairs and sort by length descending (longest alias first)
        alias_pairs = []
        for field_def in field_definitions:
            fname = field_def.get("name", "")
            for a in field_def.get("aliases", []):
                if a and a.strip():
                    alias_pairs.append((a.lower().strip(), fname))

        alias_pairs.sort(key=lambda x: len(x[0]), reverse=True)

        detected_fields: list[str] = []
        matched_spans: list[tuple[int, int]] = []

        for alias, fname in alias_pairs:
            pattern = r'\b' + re.escape(alias) + r'\b'
            for match in re.finditer(pattern, normalized):
                start, end = match.span()
                # Check if this span overlaps with any previously consumed span (from a longer alias)
                overlap = any(
                    max(start, m_start) < min(end, m_end)
                    for m_start, m_end in matched_spans
                )
                if not overlap:
                    matched_spans.append((start, end))
                    if fname not in detected_fields:
                        detected_fields.append(fname)
                        logger.debug("field_matched", field=fname, alias=alias, span=(start, end))

        if detected_fields:
            confidence = min(0.6 + (len(detected_fields) * 0.2), 0.98)
        else:
            confidence = 0.5

        logger.debug(
            "fields_detected",
            fields=detected_fields,
            wants_summary=not detected_fields,
            confidence=confidence,
        )

        return FieldDetectionResult(
            fields=detected_fields,
            # If no specific fields detected, default to summary
            wants_summary=not detected_fields,
            confidence=confidence,
        )

    def _wants_full_summary(self, message: str) -> bool:
        """
        Check if the message contains keywords indicating a full summary is wanted.

        Uses word-boundary regex to prevent false positives like 'all' matching inside 'installment'.
        """
        import re
        for trigger in FULL_SUMMARY_TRIGGERS:
            # Check whole phrase / words
            pattern = r'\b' + re.escape(trigger) + r'\b'
            if re.search(pattern, message):
                return True
        return False


# Singleton
field_detector = FieldDetector()
