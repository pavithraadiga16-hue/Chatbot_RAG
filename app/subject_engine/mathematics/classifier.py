"""
Mathematics Intent and Concept Classifier
=========================================

PURPOSE:
    Layered mathematical intent classifier, concept detector, and expression extractor.
    Computes a confidence score to determine if a question can be reliably answered
    locally without consulting an LLM.
"""

import re
from typing import Optional, Any
from pydantic import BaseModel, Field

from app.subject_engine.base import QuestionIntent
from app.subject_engine.mathematics.concepts import concept_kb, MathConcept
from app.subject_engine.mathematics.normalizer import math_normalizer


class MathClassificationResult(BaseModel):
    """Result of mathematics classification and intent detection."""
    is_mathematics: bool = False
    intent: QuestionIntent = QuestionIntent.UNKNOWN
    concept: Optional[MathConcept] = None
    topic: Optional[str] = None
    confidence: float = 0.0
    extracted_expression: str = ""
    clean_query: str = ""
    variables: list[str] = Field(default_factory=list)


class MathClassifier:
    """Classifies mathematical questions into intents, topics, and concepts."""

    # Intent Trigger Keywords & Regexes
    INTENT_TRIGGERS = [
        (re.compile(r'\b(differentiate|derivative|diff|d\/dx)\b', re.IGNORECASE), QuestionIntent.DIFFERENTIATE),
        (re.compile(r'\b(integrate|integration|antiderivative|integral)\b', re.IGNORECASE), QuestionIntent.INTEGRATE),
        (re.compile(r'\b(factorise|factorize|factor|factors)\b', re.IGNORECASE), QuestionIntent.FACTOR),
        (re.compile(r'\b(expand|expansion)\b', re.IGNORECASE), QuestionIntent.EXPAND),
        (re.compile(r'\b(simplify|simplification)\b', re.IGNORECASE), QuestionIntent.SIMPLIFY),
        (re.compile(r'\b(solve|roots\s+of|find\s+[a-zA-Z]\b)', re.IGNORECASE), QuestionIntent.SOLVE),
        (re.compile(r'\b(prove|proof\s+of|show\s+that|prameya)\b', re.IGNORECASE), QuestionIntent.PROVE),
        (re.compile(r'\b(formula\s+for|formula\s+of|what\s+is\s+the\s+formula)\b', re.IGNORECASE), QuestionIntent.FIND_FORMULA),
        (re.compile(r'\b(define|definition\s+of|what\s+is\s+a\b|what\s+is\s+an\b|explain\s+concept)\b', re.IGNORECASE), QuestionIntent.DEFINE),
        (re.compile(r'\b(convert|conversion|in\s+meters|in\s+cm|in\s+kg|to\s+radians|to\s+degrees)\b', re.IGNORECASE), QuestionIntent.UNIT_CONVERSION),
        (re.compile(r'\b(calculate|evaluate|find|value\s+of|compute)\b', re.IGNORECASE), QuestionIntent.CALCULATE),
    ]

    # Explicit Math Indicators (Characters / Symbols)
    MATH_SYMBOLS = {'+', '-', '*', '/', '^', '=', '<', '>', '√', 'π', '²', '³', '∫', '∑', 'θ', '!', '%'}

    # Core Mathematical Terms
    CORE_MATH_KEYWORDS = {
        "hcf", "gcd", "lcm", "prime", "fraction", "decimal", "percentage", "percent",
        "ratio", "proportion", "profit", "loss", "discount", "interest", "principal",
        "algebra", "equation", "quadratic", "polynomial", "discriminant", "remainder",
        "triangle", "rectangle", "square", "circle", "cylinder", "sphere", "cone",
        "area", "perimeter", "volume", "surface area", "radius", "diameter", "hypotenuse",
        "pythagoras", "distance", "midpoint", "slope", "coordinate", "vector",
        "matrix", "matrices", "determinant", "sin", "cos", "tan", "sec", "cosec", "cot",
        "limit", "derivative", "differentiate", "integral", "integrate", "ap", "gp",
        "progression", "permutation", "combination", "factorial", "mean", "median",
        "mode", "variance", "standard deviation", "probability", "subset", "union",
        "intersection", "set", "degrees", "radians"
    }

    # ERP-specific words that should NOT be classified as pure subject math problem solving
    ERP_EXCLUSIONS = {
        "attendance", "fees", "fee", "homework", "exam timetable", "hall ticket",
        "my marks", "marks card", "due date", "teacher", "admission", "profile",
        "circular", "notice", "holiday", "study material", "study materials"
    }

    def classify(self, query: str) -> MathClassificationResult:
        """
        Main classification pipeline.
        """
        raw_text = query.strip()
        normalized = math_normalizer.normalize(raw_text)
        lower_query = raw_text.lower()
        lower_norm = normalized.lower()

        # Step 1: Check for school ERP exclusions
        for word in self.ERP_EXCLUSIONS:
            if re.search(r'\b' + re.escape(word) + r'\b', lower_query):
                # Contains strong ERP signal, return not pure math
                return MathClassificationResult(is_mathematics=False, confidence=0.0)

        # Step 2: Detect Intent
        intent = QuestionIntent.UNKNOWN
        for pattern, matched_intent in self.INTENT_TRIGGERS:
            if pattern.search(lower_query):
                intent = matched_intent
                break

        # Step 3: Find Matching Concepts
        matched_concepts = concept_kb.find_by_query(lower_query)
        top_concept = matched_concepts[0][0] if matched_concepts else None
        topic = top_concept.topic if top_concept else None

        # Step 4: Calculate Confidence Score
        confidence = 0.0
        has_math_symbol = any(c in normalized for c in self.MATH_SYMBOLS)
        has_math_kw = any(re.search(r'\b' + re.escape(kw) + r'\b', lower_query) for kw in self.CORE_MATH_KEYWORDS)
        has_numbers = bool(re.search(r'\d+', normalized))

        if has_math_symbol:
            confidence += 0.4
        if has_math_kw:
            confidence += 0.4
        if has_numbers:
            confidence += 0.15
        if top_concept:
            confidence += 0.25
        if intent != QuestionIntent.UNKNOWN:
            confidence += 0.2

        # Cap confidence at 1.0
        confidence = min(1.0, confidence)

        # Step 5: If question has pure arithmetic (e.g. "25 * 48", "12 + 15", "x^2 + 5x + 6 = 0")
        is_math = confidence >= 0.35 or has_math_symbol

        # Step 6: Extract pure mathematical expression candidate
        extracted_expr = self._extract_expression(raw_text, normalized)

        # If intent is still unknown and expression has equation/operators, assign intent
        if intent == QuestionIntent.UNKNOWN:
            if "=" in extracted_expr:
                intent = QuestionIntent.SOLVE
            elif any(sym in extracted_expr for sym in ("+", "-", "*", "/", "^", "**")):
                intent = QuestionIntent.CALCULATE
            elif "factor" in lower_query:
                intent = QuestionIntent.FACTOR

        return MathClassificationResult(
            is_mathematics=is_math,
            intent=intent,
            concept=top_concept,
            topic=topic,
            confidence=confidence,
            extracted_expression=extracted_expr,
            clean_query=raw_text,
        )

    def _extract_expression(self, raw_text: str, normalized: str) -> str:
        """
        Extracts clean math expression by stripping lead-in phrases like
        'solve', 'calculate', 'find value of', 'what is', 'differentiate', etc.
        """
        prefixes = [
            r'^(?:solve|calculate|compute|evaluate|find|simplify|expand|factorize|factor)\s+(?:for\s+[a-zA-Z]\s+in\s+)?(?:the\s+value\s+of\s+)?',
            r'^(?:what\s+is\s+the\s+(?:value\s+of\s+|derivative\s+of\s+|integral\s+of\s+|solution\s+to\s+|area\s+of\s+|sum\s+of\s+)?)',
            r'^(?:what\s+is\s+)',
            r'^(?:differentiate|integrate|diff)\s+',
            r'^(?:find\s+the\s+)',
        ]
        text = normalized
        for p in prefixes:
            text = re.sub(p, '', text, flags=re.IGNORECASE).strip()

        # Remove trailing question marks or punctuation
        text = text.rstrip('?.,;!')
        return text.strip()


# Global classifier
math_classifier = MathClassifier()
