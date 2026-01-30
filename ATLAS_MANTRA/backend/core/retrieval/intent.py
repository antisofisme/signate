"""
Intent Detection & Adaptive Field Selection

Detects user intent from query and selects optimal fields to return.

INTENT TYPES:
- LIST:       User wants to browse/list decisions → minimal fields
- ENFORCE:    User is coding, needs rules → constraints focused
- UNDERSTAND: User wants to know WHY → rationale focused
- REVIEW:     User wants to check/validate → examples + invariants
- EXPLORE:    User exploring a topic → balanced fields
- FULL:       User explicitly wants everything → all fields

FIELD SELECTION per Intent:
┌──────────────┬─────────────────────────────────────────────────────┐
│ Intent       │ Fields Returned                                     │
├──────────────┼─────────────────────────────────────────────────────┤
│ LIST         │ code, summary, domain_id, impact (~30 tokens)       │
│ ENFORCE      │ code, statement, constraints (~150 tokens)          │
│ UNDERSTAND   │ code, statement, rationale (~300 tokens)            │
│ REVIEW       │ code, constraints, invariants, examples (~250 tok)  │
│ EXPLORE      │ code, statement, constraints, tags (~200 tokens)    │
│ FULL         │ All 18 fields (~500 tokens)                         │
└──────────────┴─────────────────────────────────────────────────────┘
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import re


class QueryIntent(str, Enum):
    """Detected intent from user query."""
    LIST = "LIST"              # Browse/list decisions
    ENFORCE = "ENFORCE"        # Apply rules during coding
    UNDERSTAND = "UNDERSTAND"  # Learn WHY a rule exists
    REVIEW = "REVIEW"          # Validate/check code
    EXPLORE = "EXPLORE"        # Explore a topic
    FULL = "FULL"              # Explicit full detail request
    PRD_EXPORT = "PRD_EXPORT"  # Export as documentation


@dataclass
class IntentResult:
    """Result of intent detection."""
    intent: QueryIntent
    confidence: float  # 0-1
    matched_signals: List[str]
    suggested_fields: List[str]
    token_estimate: int  # Per decision


# Field sets per intent
INTENT_FIELDS: Dict[QueryIntent, List[str]] = {
    QueryIntent.LIST: [
        "code", "summary", "domain_id", "impact"
    ],
    QueryIntent.ENFORCE: [
        "code", "statement", "constraints"
    ],
    QueryIntent.UNDERSTAND: [
        "code", "statement", "rationale", "tags"
    ],
    QueryIntent.REVIEW: [
        "code", "statement", "constraints", "invariants", "examples"
    ],
    QueryIntent.EXPLORE: [
        "code", "statement", "constraints", "tags", "applies_to"
    ],
    QueryIntent.FULL: None,  # None = all fields
    QueryIntent.PRD_EXPORT: [
        "code", "version", "domain_id", "aspect_id",
        "statement", "summary", "rationale",
        "constraints", "invariants",
        "examples", "tags", "applies_to",
        "depends_on", "supersedes", "priority_rank",
        "impact", "authored_by", "authored_at",
    ],
}

# Estimated tokens per intent
INTENT_TOKENS: Dict[QueryIntent, int] = {
    QueryIntent.LIST: 30,
    QueryIntent.ENFORCE: 150,
    QueryIntent.UNDERSTAND: 300,
    QueryIntent.REVIEW: 250,
    QueryIntent.EXPLORE: 200,
    QueryIntent.FULL: 500,
    QueryIntent.PRD_EXPORT: 600,
}


class IntentDetector:
    """
    Detects user intent from query to optimize field selection.

    Uses keyword matching and pattern recognition.
    """

    # Intent signals (keywords/patterns that indicate intent)
    SIGNALS: Dict[QueryIntent, List[str]] = {
        QueryIntent.LIST: [
            r"\blist\b", r"\bshow\s+all\b", r"\bapa\s+saja\b",
            r"\bdaftar\b", r"\bsebutkan\b", r"\benumerate\b",
            r"\bwhat\s+decisions\b", r"\bavailable\b",
            r"\bbrowse\b", r"\bindex\b",
        ],
        QueryIntent.ENFORCE: [
            r"\bbuat\b", r"\bcreate\b", r"\bbuild\b", r"\bimplement\b",
            r"\bwrite\b", r"\bcode\b", r"\bdevelop\b",
            r"\badd\b", r"\bgenerate\b", r"\bbikin\b",
            r"\btolong\b.*\bbuat\b", r"\bbantu\b.*\b(buat|create)\b",
        ],
        QueryIntent.UNDERSTAND: [
            r"\bwhy\b", r"\bkenapa\b", r"\bmengapa\b",
            r"\bexplain\b", r"\bjelaskan\b", r"\breason\b",
            r"\balasan\b", r"\bdasar\b", r"\bbackground\b",
            r"\bwhat\s+is\s+the\s+reason\b",
        ],
        QueryIntent.REVIEW: [
            r"\breview\b", r"\bcheck\b", r"\bvalidate\b",
            r"\baudit\b", r"\binspect\b", r"\bverify\b",
            r"\bcek\b", r"\bperiksa\b", r"\bevaluate\b",
            r"\bis\s+this\s+(correct|right|ok)\b",
        ],
        QueryIntent.EXPLORE: [
            r"\bhow\b", r"\bbagaimana\b", r"\bwhat\s+about\b",
            r"\btell\s+me\s+about\b", r"\bceritakan\b",
            r"\blearn\b", r"\bpelajari\b", r"\bunderstand\b",
        ],
        QueryIntent.FULL: [
            r"\bfull\b", r"\bdetail\b", r"\blengkap\b",
            r"\bsemua\s+field\b", r"\ball\s+fields\b",
            r"\bcomplete\b", r"\bcomprehensive\b",
            r"\bseluruhnya\b", r"\beverything\b",
        ],
        QueryIntent.PRD_EXPORT: [
            r"\bprd\b", r"\bexport\b", r"\bdocument\b",
            r"\bdocumentation\b", r"\bspec\b", r"\bspecification\b",
            r"\bgenerate\s+doc\b", r"\bcreate\s+prd\b",
            r"\bmarkdown\b", r"\breport\b",
            r"\bdokumen\b", r"\blaporan\b", r"\bspesifikasi\b",
        ],
    }

    # Task type hints (what user is trying to accomplish)
    TASK_HINTS: Dict[str, QueryIntent] = {
        # Frontend tasks → ENFORCE
        "component": QueryIntent.ENFORCE,
        "form": QueryIntent.ENFORCE,
        "page": QueryIntent.ENFORCE,
        "button": QueryIntent.ENFORCE,
        "modal": QueryIntent.ENFORCE,
        "hook": QueryIntent.ENFORCE,

        # Backend tasks → ENFORCE
        "api": QueryIntent.ENFORCE,
        "endpoint": QueryIntent.ENFORCE,
        "service": QueryIntent.ENFORCE,
        "controller": QueryIntent.ENFORCE,
        "migration": QueryIntent.ENFORCE,

        # Review/validation → REVIEW
        "pr": QueryIntent.REVIEW,
        "pull request": QueryIntent.REVIEW,
        "code review": QueryIntent.REVIEW,
        "linter": QueryIntent.REVIEW,

        # Learning → UNDERSTAND
        "best practice": QueryIntent.UNDERSTAND,
        "pattern": QueryIntent.EXPLORE,
        "architecture": QueryIntent.EXPLORE,
    }

    def detect(self, query: str) -> IntentResult:
        """
        Detect intent from user query.

        Args:
            query: User's natural language query

        Returns:
            IntentResult with detected intent and confidence
        """
        query_lower = query.lower()

        # Count signal matches per intent
        intent_scores: Dict[QueryIntent, float] = {}
        matched_signals: Dict[QueryIntent, List[str]] = {}

        for intent, patterns in self.SIGNALS.items():
            score = 0.0
            matches = []

            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1.0
                    matches.append(pattern)

            # Check task hints
            for hint, hint_intent in self.TASK_HINTS.items():
                if hint in query_lower and hint_intent == intent:
                    score += 0.5
                    matches.append(f"task:{hint}")

            if score > 0:
                intent_scores[intent] = score
                matched_signals[intent] = matches

        # Determine winning intent
        if not intent_scores:
            # Default to ENFORCE (most common: user asking AI to do something)
            winner = QueryIntent.ENFORCE
            confidence = 0.5
            matches = ["default:no_signal"]
        else:
            # Pick highest score
            winner = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[winner]

            # Confidence based on score relative to pattern count
            confidence = min(max_score / 3.0, 1.0)  # 3+ matches = 100%
            matches = matched_signals.get(winner, [])

        return IntentResult(
            intent=winner,
            confidence=confidence,
            matched_signals=matches,
            suggested_fields=INTENT_FIELDS.get(winner) or [],
            token_estimate=INTENT_TOKENS.get(winner, 500),
        )

    def get_fields_for_intent(self, intent: QueryIntent) -> Optional[List[str]]:
        """Get field list for an intent. None means all fields."""
        return INTENT_FIELDS.get(intent)


class AdaptiveFieldSelector:
    """
    Selects and filters decision fields based on detected intent.
    """

    def __init__(self):
        self.detector = IntentDetector()

    def select_fields(
        self,
        decision: Dict[str, Any],
        intent: QueryIntent,
    ) -> Dict[str, Any]:
        """
        Filter decision to only include fields for the given intent.

        Args:
            decision: Full decision dictionary
            intent: Detected or specified intent

        Returns:
            Filtered decision with only relevant fields
        """
        fields = INTENT_FIELDS.get(intent)

        if fields is None:
            # FULL intent - return everything
            return decision

        # Filter to only specified fields
        result = {}
        for field_name in fields:
            if field_name in decision:
                value = decision[field_name]
                # Skip empty values
                if value is not None and value != [] and value != "":
                    result[field_name] = value

        # Always include decision_id for reference
        if "decision_id" in decision:
            result["decision_id"] = decision["decision_id"]

        return result

    def process_query(
        self,
        query: str,
        decisions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Process a query and return optimized decision data.

        Args:
            query: User's query
            decisions: List of matched decisions (full data)

        Returns:
            {
                "intent": detected intent,
                "confidence": detection confidence,
                "decisions": filtered decisions,
                "tokens_saved": estimated tokens saved,
            }
        """
        # Detect intent
        intent_result = self.detector.detect(query)

        # Filter each decision
        filtered = [
            self.select_fields(d, intent_result.intent)
            for d in decisions
        ]

        # Calculate savings
        full_tokens = len(decisions) * INTENT_TOKENS[QueryIntent.FULL]
        actual_tokens = len(decisions) * intent_result.token_estimate
        tokens_saved = full_tokens - actual_tokens

        return {
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "matched_signals": intent_result.matched_signals,
            "fields_returned": intent_result.suggested_fields or "all",
            "decisions": filtered,
            "decision_count": len(filtered),
            "tokens_per_decision": intent_result.token_estimate,
            "tokens_saved": tokens_saved,
        }

    def to_context_text(
        self,
        decision: Dict[str, Any],
        intent: QueryIntent,
    ) -> str:
        """
        Convert filtered decision to context text for AI.

        Optimized text format per intent.
        """
        filtered = self.select_fields(decision, intent)
        code = filtered.get("code", "UNKNOWN")

        if intent == QueryIntent.LIST:
            # Ultra-compact for listing
            summary = filtered.get("summary", "")
            domain = filtered.get("domain_id", "")
            return f"[{code}] ({domain}) {summary}"

        if intent == QueryIntent.ENFORCE:
            # Focus on rules
            lines = [f"## {code}"]
            if "statement" in filtered:
                lines.append(f"**Rule**: {filtered['statement']}")
            if "constraints" in filtered:
                lines.append("**Constraints**:")
                for c in filtered["constraints"]:
                    if isinstance(c, dict):
                        lines.append(f"- {c.get('type', 'MUST')}: {c.get('rule', '')}")
                    else:
                        lines.append(f"- {c}")
            return "\n".join(lines)

        if intent == QueryIntent.UNDERSTAND:
            # Focus on WHY
            lines = [f"## {code}"]
            if "statement" in filtered:
                lines.append(f"**What**: {filtered['statement']}")
            if "rationale" in filtered:
                lines.append(f"**Why**: {filtered['rationale']}")
            return "\n".join(lines)

        if intent == QueryIntent.REVIEW:
            # Focus on validation
            lines = [f"## {code} - Review Checklist"]
            if "constraints" in filtered:
                lines.append("**Must Check**:")
                for c in filtered["constraints"]:
                    rule = c.get("rule", c) if isinstance(c, dict) else c
                    lines.append(f"- [ ] {rule}")
            if "invariants" in filtered:
                lines.append("**Invariants**:")
                for inv in filtered["invariants"]:
                    lines.append(f"- {inv}")
            if "examples" in filtered:
                lines.append("**Examples**:")
                for ex in filtered["examples"]:
                    lines.append(f"- {ex}")
            return "\n".join(lines)

        # EXPLORE or FULL - standard format
        lines = [f"## {code}"]
        for key, value in filtered.items():
            if key in ("code", "decision_id"):
                continue
            if isinstance(value, list):
                if value:
                    lines.append(f"**{key}**: {', '.join(str(v) for v in value[:5])}")
            else:
                lines.append(f"**{key}**: {value}")
        return "\n".join(lines)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "QueryIntent",
    "IntentResult",
    "IntentDetector",
    "AdaptiveFieldSelector",
    "INTENT_FIELDS",
    "INTENT_TOKENS",
]
