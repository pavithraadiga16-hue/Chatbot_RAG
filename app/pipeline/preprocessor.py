"""
Text Normalizer & Pre-processor
=================================

PURPOSE:
    The first stage of the pipeline. Runs before intent detection.
    Handles messages that don't need ERP calls or Claude.

STAGES:
    1. Text normalization (lowercase, strip, remove extra spaces)
    2. Greeting detection ("hi", "hello", "good morning")
    3. Thank-you detection ("thanks", "thank you")
    4. Goodbye detection ("bye", "goodbye")
    5. Profanity detection (returns safe response)
    6. Very short/unclear input detection

WHY THESE DON'T USE CLAUDE:
    Greetings, thanks, goodbyes are 100% deterministic.
    A "hi" message should NEVER trigger an ERP call or Claude.
    These are handled with simple keyword lists — fast and free.

RETURN VALUES:
    If pre-processing handles the message → returns a PreprocessResult with handled=True
    If pre-processing doesn't handle it → returns handled=False, pipeline continues
"""

import re
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# Keyword Lists
# =============================================================================

GREETING_PATTERNS = [
    "hi", "hello", "hey", "hii", "helo", "heyy",
    "good morning", "good afternoon", "good evening", "good night",
    "howdy", "what's up", "whats up", "sup", "yo", "greetings",
    "namaste", "vanakkam", "assalamualaikum", "jai hind"
]

THANK_YOU_PATTERNS = [
    "thanks", "thank you", "thank u", "thx", "ty", "tq",
    "many thanks", "thanks a lot", "thank you so much", "thankful",
    "appreciated", "great thanks", "cheers"
]

GOODBYE_PATTERNS = [
    "bye", "goodbye", "good bye", "see you", "see ya", "later",
    "take care", "cya", "ttyl", "ok bye", "okay bye"
]

# PROFANITY_PATTERNS: We keep this minimal and non-specific.
# In a real system, use a dedicated profanity filter library.
# This is a placeholder for the architecture.
PROFANITY_MARKERS = [
    "fuck", "shit", "ass", "bitch", "bastard", "damn",
    "idiot", "stupid", "crap"
]

# Messages too short or too vague to process
VAGUE_INPUTS = [
    "?", "...", "ok", "okay", "yes", "no", "maybe", "hmm", "hm"
]

# =============================================================================
# Response Templates (No ERP needed)
# =============================================================================

GREETING_RESPONSES = [
    "👋 Hello! I'm PhinsIQ, your academic assistant. How can I help you today?\n\nYou can ask me about your fees, attendance, exams, timetable, and more!",
    "👋 Hi there! I'm PhinsIQ. Ask me anything about your fees, attendance, or exams!",
]

THANK_YOU_RESPONSES = [
    "😊 You're welcome! Feel free to ask if you need anything else.",
    "😊 Happy to help! Let me know if you have more questions.",
]

GOODBYE_RESPONSES = [
    "👋 Goodbye! Have a great day!",
    "👋 Take care! Come back anytime you need help.",
]

PROFANITY_RESPONSE = (
    "I'm here to help with your academic queries. "
    "Please keep the conversation respectful so I can assist you better. 😊"
)

VAGUE_RESPONSE = (
    "I'm here to help! You can ask me about:\n\n"
    "📋 **Fees** — pending amount, paid amount, installments\n"
    "📊 **Attendance** — your attendance percentage\n"
    "📝 **Exams** — upcoming exams, results\n"
    "📅 **Holidays** — academic calendar\n"
    "🕐 **Timetable** — class schedule\n\n"
    "What would you like to know?"
)


@dataclass
class PreprocessResult:
    """
    Result from the pre-processor stage.

    Attributes:
        handled:        True if this stage produced a final response
        response:       The response to return (if handled=True)
        normalized_msg: The cleaned message text (always set)
        response_type:  What type of pre-processing result this is
    """
    handled: bool
    normalized_msg: str
    response: Optional[str] = None
    response_type: Optional[str] = None  # "greeting", "thanks", "goodbye", "profanity", "vague"


class TextNormalizer:
    """Normalizes raw text before processing."""

    def normalize(self, text: str) -> str:
        """
        Normalize text for consistent processing.

        Steps:
        1. Strip leading/trailing whitespace
        2. Lowercase
        3. Collapse multiple spaces into one
        4. Remove excessive punctuation (but keep ? and !)

        WHY LOWERCASE?
            "PENDING FEE" and "pending fee" should both detect the fees module.
            Lowercase normalization ensures consistent matching.
        """
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)       # Multiple spaces → one space
        text = re.sub(r'[^\w\s?!.,₹%/\-]', '', text)  # Keep slashes and hyphens for dates
        return text


class Preprocessor:
    """
    Pre-processes messages before they enter the intent detection pipeline.

    Handles messages that don't require ERP calls or Claude.
    Returns immediately for greetings, thanks, goodbyes, and profanity.
    """

    def __init__(self) -> None:
        self.normalizer = TextNormalizer()

    def process(self, raw_message: str) -> PreprocessResult:
        """
        Pre-process a raw message from the user.

        Checks each category in order — the first match wins.
        Order matters: check profanity before greetings to avoid
        "hi asshole" being treated as a friendly greeting.

        Args:
            raw_message: Raw message string from the chat request

        Returns:
            PreprocessResult — either handled with a response,
            or not handled (pipeline continues to intent detection)
        """
        normalized = self.normalizer.normalize(raw_message)

        # 1. Profanity check (first — highest priority)
        if self._is_profanity(normalized):
            return PreprocessResult(
                handled=True,
                normalized_msg=normalized,
                response=PROFANITY_RESPONSE,
                response_type="profanity",
            )

        # 2. Greeting
        if self._is_greeting(normalized):
            return PreprocessResult(
                handled=True,
                normalized_msg=normalized,
                response=GREETING_RESPONSES[0],
                response_type="greeting",
            )

        # 3. Thank you
        if self._is_thank_you(normalized):
            return PreprocessResult(
                handled=True,
                normalized_msg=normalized,
                response=THANK_YOU_RESPONSES[0],
                response_type="thanks",
            )

        # 4. Goodbye
        if self._is_goodbye(normalized):
            return PreprocessResult(
                handled=True,
                normalized_msg=normalized,
                response=GOODBYE_RESPONSES[0],
                response_type="goodbye",
            )

        # 5. Vague/unclear input
        if self._is_vague(normalized):
            return PreprocessResult(
                handled=True,
                normalized_msg=normalized,
                response=VAGUE_RESPONSE,
                response_type="vague",
            )

        # Not handled — continue to intent detection
        return PreprocessResult(
            handled=False,
            normalized_msg=normalized,
        )

    def _is_greeting(self, msg: str) -> bool:
        """Check if message is a greeting."""
        # Exact match for very short greetings
        if msg in GREETING_PATTERNS:
            return True
        # Starts-with check for "good morning" etc.
        return any(msg.startswith(pattern) for pattern in GREETING_PATTERNS if len(pattern) > 3)

    def _is_thank_you(self, msg: str) -> bool:
        for pattern in THANK_YOU_PATTERNS:
            if re.search(r'\b' + re.escape(pattern) + r'\b', msg):
                return True
        return False

    def _is_goodbye(self, msg: str) -> bool:
        return any(msg == pattern or msg.startswith(pattern) for pattern in GOODBYE_PATTERNS)

    def _is_profanity(self, msg: str) -> bool:
        for marker in PROFANITY_MARKERS:
            if re.search(r'\b' + re.escape(marker) + r'\b', msg):
                return True
        return False

    def _is_vague(self, msg: str) -> bool:
        """
        Detect vague inputs that are too short or unclear to process.
        Only triggers if the message has no module keywords at all.
        """
        if msg in VAGUE_INPUTS:
            return True
        # Single word with no useful content
        if len(msg.split()) == 1 and len(msg) < 4:
            return True
        return False


# Singletons
preprocessor = Preprocessor()
normalizer = TextNormalizer()
