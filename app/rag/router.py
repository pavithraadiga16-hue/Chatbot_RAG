"""Low-cost intent boundary between private student data and policy knowledge."""

import re

POLICY_CUE_RE = re.compile(
    r"\b(policy|policies|rules?|regulations?|guidelines?|eligibility|criteria|"
    r"minimum|required|requirement|requirements|condonation|documents?|paperwork|"
    r"how to apply|application process|procedure|allowed|permitted|deadline)\b",
    re.IGNORECASE,
)
KNOWLEDGE_TOPIC_RE = re.compile(
    r"\b(attendance|absence|exam(?:ination)?s?|scholarships?|leave|fees?|payment|"
    r"academic|college|institution|calendar|holiday|holidays)\b",
    re.IGNORECASE,
)
STUDENT_DATA_RE = re.compile(
    r"\b(attendance|cgpa|gpa|sgpa|marks?|grades?|scores?|results?|balance|dues?|"
    r"fee status|timetable|homework|my exam|next exam)\b",
    re.IGNORECASE,
)
PERSONAL_CUE_RE = re.compile(r"\b(my|mine|me|our|ours|personal|current)\b", re.IGNORECASE)
DYNAMIC_CAMPUS_INFO_RE = re.compile(
    r"\b(cafeteria|canteen)\b.*\b(menu|food|today)\b|\b(menu|food|today)\b.*\b(cafeteria|canteen)\b",
    re.IGNORECASE,
)


def is_institutional_knowledge_query(question: str) -> bool:
    """Identify policy/document questions without capturing individual ERP lookups."""
    text = question.strip()
    if not text:
        return False
    # Route this common live-information question through the knowledge lookup
    # so an unrelated website fuzzy match cannot invent today's menu.
    if DYNAMIC_CAMPUS_INFO_RE.search(text):
        return True
    if not KNOWLEDGE_TOPIC_RE.search(text) or not POLICY_CUE_RE.search(text):
        return False
    # Explicit policy language is a separate intent even in a message that
    # also asks for personal ERP data (e.g. fee balance + attendance minimum).
    return True


def knowledge_topic_modules(question: str) -> set[str]:
    """Find ERP topics that are being asked about as policy/document knowledge.

    Topic and policy cue proximity scopes the RAG intent without splitting the
    user's message at conjunctions. Other detected modules remain ERP intents.
    """
    policy_spans = [m.span() for m in POLICY_CUE_RE.finditer(question)]
    if not policy_spans:
        return set()
    topic_terms = {
        "attendance": r"\b(attendance|absence|absent)\b",
        "exam": r"\b(exam|examination|test)\b",
        "fees": r"\b(fees?|payment)\b",
        "leave": r"\b(leave)\b",
        "calendar": r"\b(calendar|holiday|holidays)\b",
    }
    selected = set()
    for module, pattern in topic_terms.items():
        for match in re.finditer(pattern, question, re.IGNORECASE):
            start, end = match.span()
            if any(
                max(0, p_start - end, start - p_end) <= 24
                for p_start, p_end in policy_spans
            ):
                selected.add(module)
                break
    return selected


def build_knowledge_query(question: str, modules: set[str]) -> str:
    """Build a focused RAG query from policy cues and their nearby topic.

    Mixed questions may mention personal ERP fields far from a policy clause.
    Keeping those unrelated terms out of retrieval prevents the policy answer
    from returning fee or attendance facts for the wrong part of the message.
    """
    topic_terms = {
        "attendance": r"\b(attendance|absence|absent)\b",
        "exam": r"\b(exam|examination|test)\b",
        "fees": r"\b(fees?|payment)\b",
        "leave": r"\b(leave)\b",
        "calendar": r"\b(calendar|holiday|holidays)\b",
    }
    focused_terms: list[str] = []
    for module in sorted(modules):
        pattern = topic_terms.get(module)
        if not pattern:
            continue
        topic_match = next(re.finditer(pattern, question, re.IGNORECASE), None)
        if not topic_match:
            continue
        focused_terms.append(topic_match.group(0))
        nearby = [
            cue for cue in POLICY_CUE_RE.finditer(question)
            if max(0, cue.start() - topic_match.end(), topic_match.start() - cue.end()) <= 24
        ]
        focused_terms.extend(cue.group(0) for cue in nearby)
    return " ".join(dict.fromkeys(focused_terms)) or question


def is_dynamic_campus_information_query(question: str) -> bool:
    """True for live campus details that cannot be inferred from static policy files."""
    return bool(DYNAMIC_CAMPUS_INFO_RE.search(question.strip()))

