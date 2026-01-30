"""
MANTRA Context Triggers

Dynamic rules for auto-injecting decisions based on context conditions.

TRIGGER TYPES:
1. FILE_PATTERN - Match file paths (*.tsx, src/api/*)
2. CONTENT_MATCH - Match content patterns (regex)
3. KEYWORD - Match keywords in query/context
4. SCOPE - Match scope paths
5. COMPOSITE - Combine triggers with AND/OR

EXAMPLES:
- IF file.endsWith('.tsx') AND contains('useState') → React Hooks decisions
- IF scope='be.api' AND keyword='auth' → API Auth decisions
- IF file.matches('**/test/**') → Testing decisions

EXECUTION ORDER:
1. Evaluate all triggers against context
2. Collect all triggered decision IDs
3. De-duplicate and return
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Set, Callable, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from dataclasses import dataclass
import uuid
import re
import fnmatch


# ============================================================================
# ENUMS
# ============================================================================

class TriggerType(str, Enum):
    """Type of context trigger."""
    FILE_PATTERN = "FILE_PATTERN"     # Glob pattern on file path
    CONTENT_MATCH = "CONTENT_MATCH"   # Regex on file content
    KEYWORD = "KEYWORD"               # Keyword in query/context
    SCOPE = "SCOPE"                   # Scope path match
    TAG = "TAG"                       # Tag match
    COMPOSITE = "COMPOSITE"           # Combination of triggers


class CompositeOperator(str, Enum):
    """Operator for composite triggers."""
    AND = "AND"  # All conditions must match
    OR = "OR"    # Any condition must match
    NOT = "NOT"  # Negation (single child)


class TriggerPriority(str, Enum):
    """Priority level for trigger evaluation."""
    CRITICAL = "CRITICAL"  # Always evaluate first
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


# ============================================================================
# CONTEXT MODEL
# ============================================================================

@dataclass
class RetrievalContext:
    """
    Context information for trigger evaluation.

    This is what triggers are evaluated against.
    """
    # File context (optional)
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    file_extension: Optional[str] = None

    # Query context
    query: Optional[str] = None
    keywords: Optional[List[str]] = None

    # Scope context
    scope_path: Optional[str] = None
    scope_tags: Optional[List[str]] = None

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # Auto-extract extension from file_path
        if self.file_path and not self.file_extension:
            if '.' in self.file_path:
                self.file_extension = self.file_path.rsplit('.', 1)[-1]

        # Auto-extract keywords from query
        if self.query and not self.keywords:
            # Simple keyword extraction (can be enhanced)
            self.keywords = [
                w.lower() for w in re.findall(r'\b\w{3,}\b', self.query)
            ]


# ============================================================================
# TRIGGER CONDITION MODELS
# ============================================================================

class TriggerCondition(BaseModel):
    """Base class for trigger conditions."""
    trigger_type: TriggerType

    def evaluate(self, context: RetrievalContext) -> bool:
        """Evaluate this condition against context. Override in subclasses."""
        raise NotImplementedError


class FilePatternCondition(TriggerCondition):
    """Match file path against glob pattern."""
    trigger_type: TriggerType = TriggerType.FILE_PATTERN
    pattern: str = Field(..., description="Glob pattern (e.g., '*.tsx', 'src/api/**')")

    def evaluate(self, context: RetrievalContext) -> bool:
        if not context.file_path:
            return False
        return fnmatch.fnmatch(context.file_path, self.pattern)


class ContentMatchCondition(TriggerCondition):
    """Match file content against regex pattern."""
    trigger_type: TriggerType = TriggerType.CONTENT_MATCH
    pattern: str = Field(..., description="Regex pattern")
    case_sensitive: bool = Field(default=False)

    def evaluate(self, context: RetrievalContext) -> bool:
        if not context.file_content:
            return False
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return bool(re.search(self.pattern, context.file_content, flags))


class KeywordCondition(TriggerCondition):
    """Match keywords in query/context."""
    trigger_type: TriggerType = TriggerType.KEYWORD
    keywords: List[str] = Field(..., description="Keywords to match (any)")
    match_all: bool = Field(default=False, description="If True, ALL keywords must match")

    def evaluate(self, context: RetrievalContext) -> bool:
        ctx_keywords = set(k.lower() for k in (context.keywords or []))
        if not ctx_keywords:
            # Also check query directly
            if context.query:
                query_lower = context.query.lower()
                if self.match_all:
                    return all(kw.lower() in query_lower for kw in self.keywords)
                return any(kw.lower() in query_lower for kw in self.keywords)
            return False

        trigger_keywords = set(k.lower() for k in self.keywords)
        if self.match_all:
            return trigger_keywords <= ctx_keywords
        return bool(trigger_keywords & ctx_keywords)


class ScopeCondition(TriggerCondition):
    """Match scope path."""
    trigger_type: TriggerType = TriggerType.SCOPE
    scope_path: str = Field(..., description="Scope path to match")
    include_children: bool = Field(default=True, description="Match child scopes too")

    def evaluate(self, context: RetrievalContext) -> bool:
        if not context.scope_path:
            return False

        if self.scope_path == "*":
            return True

        if context.scope_path == self.scope_path:
            return True

        if self.include_children and context.scope_path.startswith(self.scope_path + "."):
            return True

        return False


class TagCondition(TriggerCondition):
    """Match scope tags."""
    trigger_type: TriggerType = TriggerType.TAG
    tags: List[str] = Field(..., description="Tags to match (any)")
    match_all: bool = Field(default=False)

    def evaluate(self, context: RetrievalContext) -> bool:
        if not context.scope_tags:
            return False

        ctx_tags = set(t.lower() for t in context.scope_tags)
        trigger_tags = set(t.lower() for t in self.tags)

        if self.match_all:
            return trigger_tags <= ctx_tags
        return bool(trigger_tags & ctx_tags)


class CompositeCondition(TriggerCondition):
    """Combine multiple conditions with AND/OR/NOT."""
    trigger_type: TriggerType = TriggerType.COMPOSITE
    operator: CompositeOperator = Field(default=CompositeOperator.AND)
    conditions: List[Dict[str, Any]] = Field(
        ...,
        description="Child conditions (will be parsed into TriggerCondition objects)"
    )

    def evaluate(self, context: RetrievalContext) -> bool:
        parsed_conditions = [
            parse_condition(c) for c in self.conditions
        ]

        if self.operator == CompositeOperator.AND:
            return all(c.evaluate(context) for c in parsed_conditions)
        elif self.operator == CompositeOperator.OR:
            return any(c.evaluate(context) for c in parsed_conditions)
        elif self.operator == CompositeOperator.NOT:
            if len(parsed_conditions) != 1:
                raise ValueError("NOT operator requires exactly one child condition")
            return not parsed_conditions[0].evaluate(context)

        return False


def parse_condition(data: Dict[str, Any]) -> TriggerCondition:
    """Parse a condition dictionary into the appropriate TriggerCondition type."""
    trigger_type = data.get("trigger_type", "")

    if trigger_type == TriggerType.FILE_PATTERN:
        return FilePatternCondition(**data)
    elif trigger_type == TriggerType.CONTENT_MATCH:
        return ContentMatchCondition(**data)
    elif trigger_type == TriggerType.KEYWORD:
        return KeywordCondition(**data)
    elif trigger_type == TriggerType.SCOPE:
        return ScopeCondition(**data)
    elif trigger_type == TriggerType.TAG:
        return TagCondition(**data)
    elif trigger_type == TriggerType.COMPOSITE:
        return CompositeCondition(**data)
    else:
        raise ValueError(f"Unknown trigger type: {trigger_type}")


# ============================================================================
# CONTEXT TRIGGER MODEL
# ============================================================================

class ContextTrigger(BaseModel):
    """
    A rule that triggers decision injection based on context.

    When the condition evaluates to True, the associated decisions
    (or bundles) are automatically included in retrieval.
    """

    # Identity
    trigger_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID primary key"
    )

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Human-readable trigger name"
    )

    description: str = Field(
        default="",
        max_length=500,
        description="What this trigger does"
    )

    # Condition (stored as dict, parsed on evaluation)
    condition: Dict[str, Any] = Field(
        ...,
        description="Trigger condition (TriggerCondition as dict)"
    )

    # What to inject
    decision_ids: List[str] = Field(
        default_factory=list,
        description="Decision IDs to inject when triggered"
    )

    bundle_ids: List[str] = Field(
        default_factory=list,
        description="Bundle IDs to inject when triggered"
    )

    # Configuration
    priority: TriggerPriority = Field(
        default=TriggerPriority.NORMAL,
        description="Evaluation priority"
    )

    enabled: bool = Field(
        default=True,
        description="Whether this trigger is active"
    )

    # Limits
    max_tokens: Optional[int] = Field(
        default=None,
        description="Max tokens this trigger can inject (None = no limit)"
    )

    # Metadata
    created_by: str = Field(..., description="Human who created the trigger")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)

    # Stats
    trigger_count: int = Field(default=0, description="How many times triggered")
    last_triggered_at: Optional[datetime] = Field(default=None)

    # =========================================================================
    # Methods
    # =========================================================================

    def evaluate(self, context: RetrievalContext) -> bool:
        """Evaluate this trigger against context."""
        if not self.enabled:
            return False

        try:
            condition = parse_condition(self.condition)
            return condition.evaluate(context)
        except Exception:
            return False

    def get_injections(self) -> tuple[List[str], List[str]]:
        """Get decision IDs and bundle IDs to inject."""
        return self.decision_ids.copy(), self.bundle_ids.copy()

    def record_trigger(self) -> None:
        """Record that this trigger was activated."""
        self.trigger_count += 1
        self.last_triggered_at = datetime.now(timezone.utc)


# ============================================================================
# TRIGGER ENGINE
# ============================================================================

class TriggerEngine:
    """
    Evaluates all triggers against a context and collects injections.
    """

    def __init__(self, triggers: Optional[List[ContextTrigger]] = None):
        self.triggers: Dict[str, ContextTrigger] = {}
        if triggers:
            for trigger in triggers:
                self.add_trigger(trigger)

    def add_trigger(self, trigger: ContextTrigger) -> None:
        """Add or update a trigger."""
        self.triggers[trigger.trigger_id] = trigger

    def remove_trigger(self, trigger_id: str) -> bool:
        """Remove a trigger."""
        return self.triggers.pop(trigger_id, None) is not None

    def get_trigger(self, trigger_id: str) -> Optional[ContextTrigger]:
        """Get a trigger by ID."""
        return self.triggers.get(trigger_id)

    def evaluate(
        self,
        context: RetrievalContext,
        record_triggers: bool = True
    ) -> "TriggerResult":
        """
        Evaluate all triggers against context.

        Returns:
            TriggerResult with all triggered decision/bundle IDs
        """
        # Sort by priority
        priority_order = {
            TriggerPriority.CRITICAL: 0,
            TriggerPriority.HIGH: 1,
            TriggerPriority.NORMAL: 2,
            TriggerPriority.LOW: 3,
        }

        sorted_triggers = sorted(
            self.triggers.values(),
            key=lambda t: priority_order.get(t.priority, 2)
        )

        triggered: List[ContextTrigger] = []
        decision_ids: Set[str] = set()
        bundle_ids: Set[str] = set()

        for trigger in sorted_triggers:
            if trigger.evaluate(context):
                triggered.append(trigger)
                dec_ids, bnd_ids = trigger.get_injections()
                decision_ids.update(dec_ids)
                bundle_ids.update(bnd_ids)

                if record_triggers:
                    trigger.record_trigger()

        return TriggerResult(
            context=context,
            triggered=triggered,
            decision_ids=list(decision_ids),
            bundle_ids=list(bundle_ids)
        )

    def get_all_enabled(self) -> List[ContextTrigger]:
        """Get all enabled triggers."""
        return [t for t in self.triggers.values() if t.enabled]


@dataclass
class TriggerResult:
    """Result of trigger evaluation."""
    context: RetrievalContext
    triggered: List[ContextTrigger]
    decision_ids: List[str]
    bundle_ids: List[str]

    @property
    def has_triggers(self) -> bool:
        return len(self.triggered) > 0

    @property
    def trigger_names(self) -> List[str]:
        return [t.name for t in self.triggered]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_file_trigger(
    name: str,
    pattern: str,
    decision_ids: List[str],
    created_by: str,
    description: str = ""
) -> ContextTrigger:
    """Create a simple file pattern trigger."""
    return ContextTrigger(
        name=name,
        description=description or f"Triggers on files matching {pattern}",
        condition={
            "trigger_type": "FILE_PATTERN",
            "pattern": pattern
        },
        decision_ids=decision_ids,
        created_by=created_by
    )


def create_keyword_trigger(
    name: str,
    keywords: List[str],
    decision_ids: List[str],
    created_by: str,
    match_all: bool = False,
    description: str = ""
) -> ContextTrigger:
    """Create a keyword-based trigger."""
    return ContextTrigger(
        name=name,
        description=description or f"Triggers on keywords: {', '.join(keywords)}",
        condition={
            "trigger_type": "KEYWORD",
            "keywords": keywords,
            "match_all": match_all
        },
        decision_ids=decision_ids,
        created_by=created_by
    )


def create_scope_trigger(
    name: str,
    scope_path: str,
    decision_ids: List[str],
    created_by: str,
    include_children: bool = True,
    description: str = ""
) -> ContextTrigger:
    """Create a scope-based trigger."""
    return ContextTrigger(
        name=name,
        description=description or f"Triggers for scope: {scope_path}",
        condition={
            "trigger_type": "SCOPE",
            "scope_path": scope_path,
            "include_children": include_children
        },
        decision_ids=decision_ids,
        created_by=created_by
    )


def create_composite_trigger(
    name: str,
    operator: CompositeOperator,
    conditions: List[Dict[str, Any]],
    decision_ids: List[str],
    created_by: str,
    description: str = ""
) -> ContextTrigger:
    """Create a composite trigger with multiple conditions."""
    return ContextTrigger(
        name=name,
        description=description,
        condition={
            "trigger_type": "COMPOSITE",
            "operator": operator.value,
            "conditions": conditions
        },
        decision_ids=decision_ids,
        created_by=created_by
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "TriggerType",
    "CompositeOperator",
    "TriggerPriority",
    # Context
    "RetrievalContext",
    # Conditions
    "TriggerCondition",
    "FilePatternCondition",
    "ContentMatchCondition",
    "KeywordCondition",
    "ScopeCondition",
    "TagCondition",
    "CompositeCondition",
    "parse_condition",
    # Trigger
    "ContextTrigger",
    "TriggerEngine",
    "TriggerResult",
    # Convenience
    "create_file_trigger",
    "create_keyword_trigger",
    "create_scope_trigger",
    "create_composite_trigger",
]
