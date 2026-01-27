"""
MANTRA MCP Resources

Provides read-only resources for AI assistants:
- decisions:// - List/filter decisions
- decision:// - Get single decision
- groups:// - List decision groups
- features:// - List feature areas
- matrix:// - Decision matrix view

Resources return data that AI can use for context.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DecisionResource:
    """Single decision resource."""
    decision_id: str
    decision_code: str
    statement: str
    rationale: str
    group_id: str
    feature_id: str
    scope: str
    status: str
    tags: List[str]
    tech_stack: List[str]
    # Layer B content (optional)
    detailed_content: Optional[str] = None
    sections: Optional[List[Dict]] = None
    content_summary: Optional[str] = None


@dataclass
class GroupResource:
    """Decision group resource."""
    group_id: str
    name: str
    description: str
    decision_count: int


@dataclass
class FeatureResource:
    """Feature area resource."""
    feature_id: str
    group_id: str
    name: str
    description: str
    decision_count: int


class ResourceProvider:
    """
    Provides MCP resource handlers.

    MICS Integration:
    - Resources are READ-ONLY context for AI
    - Support tiered detail levels (micro, standard, detailed, sections)
    - Token budget awareness for context injection
    """

    def __init__(self, repository=None):
        """
        Initialize resource provider.

        Args:
            repository: DecisionRepository instance
        """
        self.repository = repository

    async def get_decisions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        detail_level: str = "standard",
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get list of decisions with optional filtering.

        Args:
            filters: Optional filter criteria
            detail_level: micro|standard|detailed|sections
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with decisions and metadata
        """
        if not self.repository:
            return {"decisions": [], "total": 0, "error": "Repository not configured"}

        try:
            # Fetch from repository
            stored_decisions = await self.repository.find_all_async(limit=limit, offset=offset)

            # Apply filters if provided
            decisions = []
            for sd in stored_decisions:
                d = sd.decision
                record = {
                    "decision_id": d.decision_id,
                    "decision_code": d.decision_code,
                    "group_id": d.group_id.value if hasattr(d.group_id, 'value') else d.group_id,
                    "feature_id": d.feature_id.value if hasattr(d.feature_id, 'value') else d.feature_id,
                    "status": d.status.value if hasattr(d.status, 'value') else d.status,
                }

                # Apply detail level
                if detail_level == "micro":
                    # Minimal: just ID and summary
                    record["summary"] = d.content_summary or d.statement[:100]
                elif detail_level == "standard":
                    # Standard: statement, rationale, key metadata
                    record["statement"] = d.statement
                    record["rationale"] = d.rationale
                    record["scope"] = d.scope.value if hasattr(d.scope, 'value') else d.scope
                    record["tags"] = d.tags or []
                elif detail_level == "detailed":
                    # Detailed: everything including Layer B
                    record["statement"] = d.statement
                    record["rationale"] = d.rationale
                    record["scope"] = d.scope.value if hasattr(d.scope, 'value') else d.scope
                    record["tags"] = d.tags or []
                    record["tech_stack"] = d.tech_stack or []
                    record["detailed_content"] = d.detailed_content
                    record["constraints"] = [
                        {"type": c.type.value if hasattr(c.type, 'value') else c.type, "statement": c.statement}
                        for c in (d.constraints or [])
                    ]
                elif detail_level == "sections":
                    # Sections: Layer B sections only
                    record["statement"] = d.statement
                    record["sections"] = [
                        {
                            "section_id": s.section_id,
                            "title": s.title,
                            "section_type": s.section_type.value if hasattr(s.section_type, 'value') else s.section_type,
                            "content": s.content
                        }
                        for s in (d.sections or [])
                    ]

                decisions.append(record)

            return {
                "decisions": decisions,
                "total": len(decisions),
                "detail_level": detail_level,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error fetching decisions: {e}")
            return {"decisions": [], "total": 0, "error": str(e)}

    async def get_decision(self, decision_id: str, detail_level: str = "detailed") -> Dict[str, Any]:
        """
        Get a single decision by ID or code.

        Args:
            decision_id: Decision ID or code
            detail_level: micro|standard|detailed|sections

        Returns:
            Decision data or error
        """
        if not self.repository:
            return {"error": "Repository not configured"}

        try:
            # Try by ID first, then by code
            stored = await self.repository.find_by_id_async(decision_id)
            if not stored:
                stored = await self.repository.find_by_code_async(decision_id)

            if not stored:
                return {"error": f"Decision not found: {decision_id}"}

            d = stored.decision
            record = {
                "decision_id": d.decision_id,
                "decision_code": d.decision_code,
                "group_id": d.group_id.value if hasattr(d.group_id, 'value') else d.group_id,
                "feature_id": d.feature_id.value if hasattr(d.feature_id, 'value') else d.feature_id,
                "statement": d.statement,
                "rationale": d.rationale,
                "scope": d.scope.value if hasattr(d.scope, 'value') else d.scope,
                "status": d.status.value if hasattr(d.status, 'value') else d.status,
                "tags": d.tags or [],
                "tech_stack": d.tech_stack or [],
                "blast_radius": d.blast_radius.value if hasattr(d.blast_radius, 'value') else d.blast_radius,
            }

            # Add Layer B content based on detail level
            if detail_level in ("detailed", "sections"):
                record["detailed_content"] = d.detailed_content
                record["sections"] = [
                    {
                        "section_id": s.section_id,
                        "title": s.title,
                        "section_type": s.section_type.value if hasattr(s.section_type, 'value') else s.section_type,
                        "content": s.content,
                        "order": s.order
                    }
                    for s in (d.sections or [])
                ]
                record["constraints"] = [
                    {"type": c.type.value if hasattr(c.type, 'value') else c.type, "statement": c.statement}
                    for c in (d.constraints or [])
                ]
                record["invariants"] = d.invariants or []

            return record

        except Exception as e:
            logger.error(f"Error fetching decision {decision_id}: {e}")
            return {"error": str(e)}

    async def get_groups(self) -> Dict[str, Any]:
        """
        Get list of decision groups.

        Returns:
            Dict with groups and their decision counts
        """
        # Static groups from schema
        from ..domain.schema import Group

        groups = []
        for g in Group:
            groups.append({
                "group_id": g.value,
                "name": g.name,
                "description": _get_group_description(g.value),
            })

        # Add decision counts if repository available
        if self.repository:
            try:
                for group in groups:
                    count = await self._count_decisions_in_group(group["group_id"])
                    group["decision_count"] = count
            except Exception as e:
                logger.warning(f"Could not get decision counts: {e}")

        return {"groups": groups}

    async def get_features(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of feature areas.

        Args:
            group_id: Optional filter by group

        Returns:
            Dict with features
        """
        from ..domain.schema import Feature

        features = []
        for f in Feature:
            feature_group = _get_feature_group(f.value)
            if group_id and feature_group != group_id:
                continue

            features.append({
                "feature_id": f.value,
                "group_id": feature_group,
                "name": f.name,
                "description": _get_feature_description(f.value),
            })

        return {"features": features}

    async def get_decision_matrix(self) -> Dict[str, Any]:
        """
        Get decision matrix (groups x features).

        Returns:
            Matrix with decision counts per cell
        """
        from ..domain.schema import Group, Feature

        matrix = {}
        for g in Group:
            matrix[g.value] = {}
            for f in Feature:
                # Only include relevant features for this group
                if _get_feature_group(f.value) == g.value or _get_feature_group(f.value) == "COMMON":
                    matrix[g.value][f.value] = 0

        # Fill counts if repository available
        if self.repository:
            try:
                stored_decisions = await self.repository.find_all_async(limit=10000, offset=0)
                for sd in stored_decisions:
                    g = sd.decision.group_id.value if hasattr(sd.decision.group_id, 'value') else sd.decision.group_id
                    f = sd.decision.feature_id.value if hasattr(sd.decision.feature_id, 'value') else sd.decision.feature_id
                    if g in matrix and f in matrix[g]:
                        matrix[g][f] += 1
            except Exception as e:
                logger.warning(f"Could not populate matrix: {e}")

        return {"matrix": matrix}

    async def _count_decisions_in_group(self, group_id: str) -> int:
        """Count decisions in a group."""
        if not self.repository:
            return 0
        try:
            stored = await self.repository.find_all_async(limit=10000, offset=0)
            return sum(
                1 for sd in stored
                if (sd.decision.group_id.value if hasattr(sd.decision.group_id, 'value') else sd.decision.group_id) == group_id
            )
        except:
            return 0


# =============================================================================
# Helper Functions
# =============================================================================

def _get_group_description(group_id: str) -> str:
    """Get human-readable group description."""
    descriptions = {
        "ARCH": "Architectural decisions - system structure and design patterns",
        "STD": "Standards and conventions - coding style, naming, formatting",
        "PROC": "Processes and workflows - CI/CD, deployment, development flow",
        "IMPL": "Implementation details - specific technical choices",
        "SPEC": "Specifications - detailed requirements and contracts",
    }
    return descriptions.get(group_id, f"Decision group: {group_id}")


def _get_feature_description(feature_id: str) -> str:
    """Get human-readable feature description."""
    descriptions = {
        "DATABASE": "Database design, queries, migrations",
        "API": "API design, endpoints, contracts",
        "AUTH": "Authentication and authorization",
        "UI": "User interface and components",
        "INFRA": "Infrastructure and deployment",
        "TESTING": "Testing strategy and patterns",
        "SECURITY": "Security policies and practices",
        "PERFORMANCE": "Performance optimization",
        "MONITORING": "Logging, metrics, observability",
    }
    return descriptions.get(feature_id, f"Feature area: {feature_id}")


def _get_feature_group(feature_id: str) -> str:
    """Get the primary group for a feature."""
    # Most features are COMMON (applicable to multiple groups)
    group_specific = {
        # Add group-specific features here
    }
    return group_specific.get(feature_id, "COMMON")
