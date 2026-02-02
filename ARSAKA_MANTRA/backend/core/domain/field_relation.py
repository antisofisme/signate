"""
MANTRA Field-Level Relationships

Models relationships between individual fields across different decisions.

FIELD PATH ADDRESSING:
- "statement" - direct field
- "constraints[0]" - array element
- "constraints[0].rule" - nested property
- "tags[*]" - all array elements (wildcard)

RELATION TYPES:
- CONFLICTS_WITH: Contradicting rules (MUST vs MUST_NOT)
- STRENGTHENS: Makes a rule stricter (SHOULD → MUST)
- WEAKENS: Makes a rule looser (MUST → SHOULD)
- IMPLEMENTS: Specific implementation of abstract principle
- ENFORCES: Invariant that guarantees a constraint
- REFERENCES: Non-dependency reference for context

USE CASES:
1. Conflict Detection: Find MUST vs MUST_NOT on same topic
2. Impact Analysis: What breaks if I change constraint X?
3. Consistency Check: Do invariants still support constraints?
4. Documentation: Show implementation chains in PRD
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import uuid


class RelationType(str, Enum):
    """Types of field-level relationships."""

    # Conflict-related
    CONFLICTS_WITH = "CONFLICTS_WITH"  # Directly contradicts
    STRENGTHENS = "STRENGTHENS"        # Makes stricter
    WEAKENS = "WEAKENS"                # Makes looser

    # Implementation-related
    IMPLEMENTS = "IMPLEMENTS"          # Specific impl of abstract
    ENFORCES = "ENFORCES"              # Invariant → Constraint

    # Reference
    REFERENCES = "REFERENCES"          # Non-binding reference


class RelationConfidence(str, Enum):
    """Confidence level for detected relationships."""
    CERTAIN = "CERTAIN"        # Human verified or exact match
    HIGH = "HIGH"              # Strong signal (>80% sure)
    MEDIUM = "MEDIUM"          # Moderate signal (50-80%)
    LOW = "LOW"                # Weak signal (<50%), needs review


class RelationSource(str, Enum):
    """How the relation was created."""
    HUMAN = "HUMAN"            # Manually created by human
    AI_DETECTED = "AI_DETECTED"  # Automatically detected by AI
    RULE_BASED = "RULE_BASED"  # Detected by rule-based heuristics


@dataclass
class FieldPath:
    """
    Parsed field path for addressing fields in decisions.

    Examples:
    - "statement" → field="statement", index=None, subfield=None
    - "constraints[0]" → field="constraints", index=0, subfield=None
    - "constraints[0].rule" → field="constraints", index=0, subfield="rule"
    - "tags[*]" → field="tags", index="*" (wildcard), subfield=None
    """
    field: str
    index: Optional[int | str] = None  # int for specific, "*" for wildcard
    subfield: Optional[str] = None

    # Pattern for parsing field paths
    PATH_PATTERN = re.compile(
        r'^(\w+)'                    # field name
        r'(?:\[(\d+|\*)\])?'         # optional [index] or [*]
        r'(?:\.(\w+))?$'             # optional .subfield
    )

    @classmethod
    def parse(cls, path: str) -> 'FieldPath':
        """Parse a field path string."""
        match = cls.PATH_PATTERN.match(path)
        if not match:
            raise ValueError(f"Invalid field path: {path}")

        field_name = match.group(1)
        index_str = match.group(2)
        subfield = match.group(3)

        index = None
        if index_str is not None:
            index = "*" if index_str == "*" else int(index_str)

        return cls(field=field_name, index=index, subfield=subfield)

    def to_string(self) -> str:
        """Convert back to string representation."""
        result = self.field
        if self.index is not None:
            result += f"[{self.index}]"
        if self.subfield:
            result += f".{self.subfield}"
        return result

    def get_value(self, decision: Dict[str, Any]) -> Any:
        """Extract value from decision at this path."""
        value = decision.get(self.field)

        if value is None:
            return None

        if self.index is not None:
            if self.index == "*":
                # Wildcard - return all elements
                if isinstance(value, list):
                    if self.subfield:
                        return [
                            item.get(self.subfield) if isinstance(item, dict) else item
                            for item in value
                        ]
                    return value
                return [value]
            else:
                # Specific index
                if isinstance(value, list) and 0 <= self.index < len(value):
                    value = value[self.index]
                else:
                    return None

        if self.subfield and isinstance(value, dict):
            return value.get(self.subfield)

        return value

    def exists_in(self, decision: Dict[str, Any]) -> bool:
        """Check if this path exists in the decision."""
        try:
            value = self.get_value(decision)
            return value is not None
        except (IndexError, KeyError, TypeError):
            return False


@dataclass
class FieldRelation:
    """
    A relationship between fields in two decisions.

    This is the core model for field-level relationships.
    Immutable once created (for audit trail).
    """
    relation_id: str

    # Source field
    source_decision_id: str
    source_field_path: str  # e.g., "constraints[0].rule"

    # Target field
    target_decision_id: str
    target_field_path: str

    # Relationship
    relation_type: RelationType
    confidence: RelationConfidence
    source: RelationSource

    # Metadata
    description: Optional[str] = None
    rationale: Optional[str] = None  # Why this relation exists

    # Audit
    created_by: str = ""  # Human who created/verified
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None

    # Optional scoring for AI-detected relations
    similarity_score: Optional[float] = None  # 0-1 for semantic similarity

    def __post_init__(self):
        """Validate and generate ID if needed."""
        if not self.relation_id:
            self.relation_id = str(uuid.uuid4())

        # Validate paths
        try:
            FieldPath.parse(self.source_field_path)
            FieldPath.parse(self.target_field_path)
        except ValueError as e:
            raise ValueError(f"Invalid field path in relation: {e}")

        # Prevent self-reference (same decision AND same field)
        if (self.source_decision_id == self.target_decision_id and
            self.source_field_path == self.target_field_path):
            raise ValueError("Field cannot have relation to itself")

    @property
    def is_verified(self) -> bool:
        """Check if relation has been human-verified."""
        return self.verified_at is not None

    @property
    def is_conflict(self) -> bool:
        """Check if this is a conflict relation."""
        return self.relation_type == RelationType.CONFLICTS_WITH

    @property
    def source_path(self) -> FieldPath:
        """Get parsed source path."""
        return FieldPath.parse(self.source_field_path)

    @property
    def target_path(self) -> FieldPath:
        """Get parsed target path."""
        return FieldPath.parse(self.target_field_path)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        return {
            "relation_id": self.relation_id,
            "source_decision_id": self.source_decision_id,
            "source_field_path": self.source_field_path,
            "target_decision_id": self.target_decision_id,
            "target_field_path": self.target_field_path,
            "relation_type": self.relation_type.value,
            "confidence": self.confidence.value,
            "source": self.source.value,
            "description": self.description,
            "rationale": self.rationale,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": self.verified_by,
            "similarity_score": self.similarity_score,
            "is_verified": self.is_verified,
            "is_conflict": self.is_conflict,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldRelation':
        """Create from dictionary."""
        return cls(
            relation_id=data.get("relation_id", ""),
            source_decision_id=data["source_decision_id"],
            source_field_path=data["source_field_path"],
            target_decision_id=data["target_decision_id"],
            target_field_path=data["target_field_path"],
            relation_type=RelationType(data["relation_type"]),
            confidence=RelationConfidence(data.get("confidence", "MEDIUM")),
            source=RelationSource(data.get("source", "RULE_BASED")),
            description=data.get("description"),
            rationale=data.get("rationale"),
            created_by=data.get("created_by", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now(timezone.utc)),
            verified_at=datetime.fromisoformat(data["verified_at"]) if data.get("verified_at") else None,
            verified_by=data.get("verified_by"),
            similarity_score=data.get("similarity_score"),
        )


@dataclass
class RelationGraph:
    """
    Graph of field-level relationships.

    Provides graph operations for impact analysis.
    """
    relations: List[FieldRelation] = field(default_factory=list)

    # Indexes for fast lookup
    _by_source: Dict[str, List[FieldRelation]] = field(default_factory=dict, init=False)
    _by_target: Dict[str, List[FieldRelation]] = field(default_factory=dict, init=False)
    _by_type: Dict[RelationType, List[FieldRelation]] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Build indexes."""
        self._rebuild_indexes()

    def _rebuild_indexes(self):
        """Rebuild lookup indexes."""
        self._by_source = {}
        self._by_target = {}
        self._by_type = {}

        for rel in self.relations:
            # By source decision
            key = f"{rel.source_decision_id}:{rel.source_field_path}"
            if key not in self._by_source:
                self._by_source[key] = []
            self._by_source[key].append(rel)

            # By target decision
            key = f"{rel.target_decision_id}:{rel.target_field_path}"
            if key not in self._by_target:
                self._by_target[key] = []
            self._by_target[key].append(rel)

            # By type
            if rel.relation_type not in self._by_type:
                self._by_type[rel.relation_type] = []
            self._by_type[rel.relation_type].append(rel)

    def add_relation(self, relation: FieldRelation):
        """Add a relation to the graph."""
        self.relations.append(relation)
        self._rebuild_indexes()  # Simple approach; optimize if needed

    def get_relations_from(
        self,
        decision_id: str,
        field_path: Optional[str] = None,
    ) -> List[FieldRelation]:
        """Get relations where decision/field is the source."""
        if field_path:
            key = f"{decision_id}:{field_path}"
            return self._by_source.get(key, [])

        # All relations from this decision
        return [
            rel for rel in self.relations
            if rel.source_decision_id == decision_id
        ]

    def get_relations_to(
        self,
        decision_id: str,
        field_path: Optional[str] = None,
    ) -> List[FieldRelation]:
        """Get relations where decision/field is the target."""
        if field_path:
            key = f"{decision_id}:{field_path}"
            return self._by_target.get(key, [])

        return [
            rel for rel in self.relations
            if rel.target_decision_id == decision_id
        ]

    def get_conflicts(self) -> List[FieldRelation]:
        """Get all conflict relations."""
        return self._by_type.get(RelationType.CONFLICTS_WITH, [])

    def get_by_type(self, relation_type: RelationType) -> List[FieldRelation]:
        """Get relations of a specific type."""
        return self._by_type.get(relation_type, [])

    def get_impact_chain(
        self,
        decision_id: str,
        field_path: str,
        max_depth: int = 10,
    ) -> List[Tuple[int, FieldRelation]]:
        """
        Get all relations impacted by changing a field.

        Returns list of (depth, relation) tuples.
        """
        result = []
        visited = set()
        queue = [(0, decision_id, field_path)]

        while queue and len(result) < 100:  # Safety limit
            depth, dec_id, f_path = queue.pop(0)

            if depth > max_depth:
                continue

            key = f"{dec_id}:{f_path}"
            if key in visited:
                continue
            visited.add(key)

            # Find relations where this is the source
            relations = self.get_relations_from(dec_id, f_path)

            for rel in relations:
                result.append((depth, rel))

                # Follow the chain to target
                if rel.relation_type in [RelationType.IMPLEMENTS, RelationType.ENFORCES]:
                    queue.append((depth + 1, rel.target_decision_id, rel.target_field_path))

            # Also find relations where this is the target (reverse impact)
            reverse_relations = self.get_relations_to(dec_id, f_path)

            for rel in reverse_relations:
                if rel.relation_type in [RelationType.STRENGTHENS, RelationType.WEAKENS]:
                    result.append((depth, rel))

        return result

    def find_conflicts_for_decision(
        self,
        decision_id: str,
    ) -> List[FieldRelation]:
        """Find all conflicts involving a decision."""
        conflicts = []
        for rel in self.get_conflicts():
            if rel.source_decision_id == decision_id or rel.target_decision_id == decision_id:
                conflicts.append(rel)
        return conflicts

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        decisions = set()
        for rel in self.relations:
            decisions.add(rel.source_decision_id)
            decisions.add(rel.target_decision_id)

        type_counts = {t.value: len(rels) for t, rels in self._by_type.items()}

        verified_count = sum(1 for r in self.relations if r.is_verified)

        return {
            "total_relations": len(self.relations),
            "unique_decisions": len(decisions),
            "relations_by_type": type_counts,
            "conflicts_count": len(self.get_conflicts()),
            "verified_count": verified_count,
            "unverified_count": len(self.relations) - verified_count,
        }


# ============================================================================
# FIELD PATH UTILITIES
# ============================================================================

def validate_field_path(path: str, decision_schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate a field path is syntactically correct.

    If decision_schema is provided, also validates the path exists in schema.
    """
    try:
        parsed = FieldPath.parse(path)

        # Known MANTRA decision fields
        valid_fields = {
            "decision_id", "code", "version",
            "domain_id", "aspect_id", "validity_state",
            "statement", "rationale", "constraints", "invariants",
            "applies_to", "examples", "tags",
            "authored_by", "authored_at", "content_by",
            "impact", "summary",
            "depends_on", "supersedes", "priority_rank",
        }

        if parsed.field not in valid_fields:
            return False

        # Validate index makes sense for array fields
        array_fields = {"constraints", "invariants", "applies_to", "examples", "tags", "depends_on"}
        if parsed.index is not None and parsed.field not in array_fields:
            return False

        # Validate subfields
        constraint_subfields = {"id", "type", "rule", "enforcement_level", "is_automated"}
        if parsed.field == "constraints" and parsed.subfield:
            if parsed.subfield not in constraint_subfields:
                return False

        return True

    except ValueError:
        return False


def extract_constraint_paths(decision: Dict[str, Any]) -> List[str]:
    """Extract all constraint field paths from a decision."""
    paths = []
    constraints = decision.get("constraints", [])

    for i, c in enumerate(constraints):
        paths.append(f"constraints[{i}]")
        if isinstance(c, dict):
            for key in c.keys():
                paths.append(f"constraints[{i}].{key}")

    return paths


def extract_all_field_paths(decision: Dict[str, Any]) -> List[str]:
    """Extract all addressable field paths from a decision."""
    paths = []

    # Simple fields
    simple_fields = [
        "decision_id", "code", "version",
        "domain_id", "aspect_id",
        "statement", "rationale",
        "impact", "summary",
        "authored_by", "content_by",
        "supersedes", "priority_rank",
    ]

    for field in simple_fields:
        if field in decision:
            paths.append(field)

    # Array fields
    array_fields = ["constraints", "invariants", "applies_to", "examples", "tags", "depends_on"]

    for field in array_fields:
        items = decision.get(field, [])
        if items:
            paths.append(field)
            paths.append(f"{field}[*]")  # Wildcard

            for i, item in enumerate(items):
                paths.append(f"{field}[{i}]")

                # Nested fields for constraints
                if field == "constraints" and isinstance(item, dict):
                    for key in item.keys():
                        paths.append(f"{field}[{i}].{key}")

    return paths


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "RelationType",
    "RelationConfidence",
    "RelationSource",
    # Models
    "FieldPath",
    "FieldRelation",
    "RelationGraph",
    # Utilities
    "validate_field_path",
    "extract_constraint_paths",
    "extract_all_field_paths",
]
