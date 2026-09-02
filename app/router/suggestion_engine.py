"""
Follow-Up Question Suggestion Engine
====================================

PURPOSE:
    Generates 3 contextual, highly relevant, and guaranteed answerable
    follow-up suggestion questions tailored to the active module or Claude AI fallback.

USAGE:
    suggestions = suggestion_engine.get_suggestions(module="fees")
    # Returns [
    #   "What is my pending fee balance?",
    #   "What is my attendance percentage?",
    #   "Show my pending homework"
    # ]
"""

from typing import Optional

# Standard 3-question suggestion maps per module
MODULE_SUGGESTIONS: dict[str, list[str]] = {
    "fees": [
        "What is my pending fee balance?",
        "What is my attendance percentage?",
        "Show my pending homework",
    ],
    "attendance": [
        "What is my pending fee balance?",
        "Show my pending homework",
        "When is my next school holiday?",
    ],
    "homework": [
        "What study materials are available?",
        "What is my attendance percentage?",
        "When is the next school holiday?",
    ],
    "study_materials": [
        "Show my pending homework",
        "What is my attendance percentage?",
        "What is my pending fee balance?",
    ],
    "notification": [
        "Show my pending homework",
        "When is my next school holiday?",
        "What is my pending fee balance?",
    ],
    "calendar": [
        "When does school reopen?",
        "What is my pending homework?",
        "What is my attendance percentage?",
    ],
    "profile": [
        "What is my academic progress?",
        "What is my pending fee balance?",
        "Show my pending homework",
    ],
    "academic_overview": [
        "What is my pending fee balance?",
        "Show my pending homework",
        "When is the next school holiday?",
    ],
    "claude_fallback": [
        "What is my attendance percentage?",
        "What is my pending fee balance?",
        "Show my pending homework",
    ],
}

DEFAULT_SUGGESTIONS: list[str] = [
    "What is my pending fee balance?",
    "What is my attendance percentage?",
    "Show my pending homework",
]


class SuggestionEngine:
    """Provides 3 interactive follow-up question suggestions for every response."""

    def get_suggestions(
        self,
        module: Optional[str] = None,
        is_overall_overview: bool = False,
        claude_used: bool = False,
    ) -> list[str]:
        """
        Returns exactly 3 contextual suggestion questions based on the module/context.
        """
        if is_overall_overview:
            return list(MODULE_SUGGESTIONS["academic_overview"])

        if claude_used:
            return list(MODULE_SUGGESTIONS["claude_fallback"])

        if not module:
            return list(DEFAULT_SUGGESTIONS)

        normalized_mod = module.strip().lower()

        # Handle aliases
        if normalized_mod in ("notice",):
            normalized_mod = "notification"
        elif normalized_mod in ("holiday",):
            normalized_mod = "calendar"
        elif normalized_mod in ("study_material",):
            normalized_mod = "study_materials"

        suggestions = MODULE_SUGGESTIONS.get(normalized_mod, DEFAULT_SUGGESTIONS)
        return list(suggestions[:3])


suggestion_engine = SuggestionEngine()
