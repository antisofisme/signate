"""
MANTRA MCP Resources

Provides read-only resources for AI assistants:
- decisions:// - List/filter decisions
- decision:// - Get single decision
- domains:// - List decision domains
- aspects:// - List aspect areas
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
    domain_id: str
    aspect_id: str
    scope: str
    status: str
    tags: List[str]
    tech_stack: List[str]
    # Layer B content (optional)
    detailed_content: Optional[str] = None
    sections: Optional[List[Dict]] = None
    content_summary: Optional[str] = None


@dataclass
class DomainResource:
    """Decision domain resource."""
    domain_id: str
    name: str
    description: str
    decision_count: int


@dataclass
class AspectResource:
    """Aspect area resource."""
    aspect_id: str
    domain_id: str
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
                    "domain_id": d.domain_id.value if hasattr(d.domain_id, 'value') else d.domain_id,
                    "aspect_id": d.aspect_id.value if hasattr(d.aspect_id, 'value') else d.aspect_id,
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
                "domain_id": d.domain_id.value if hasattr(d.domain_id, 'value') else d.domain_id,
                "aspect_id": d.aspect_id.value if hasattr(d.aspect_id, 'value') else d.aspect_id,
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

    async def get_domains(self) -> Dict[str, Any]:
        """
        Get list of decision domains.

        Returns:
            Dict with domains and their decision counts
        """
        # Static domains from schema
        from ..domain.schema import Domain

        domains = []
        for d in Domain:
            domains.append({
                "domain_id": d.value,
                "name": d.name,
                "description": _get_domain_description(d.value),
            })

        # Add decision counts if repository available
        if self.repository:
            try:
                for domain in domains:
                    count = await self._count_decisions_in_domain(domain["domain_id"])
                    domain["decision_count"] = count
            except Exception as e:
                logger.warning(f"Could not get decision counts: {e}")

        return {"domains": domains}

    async def get_aspects(self, domain_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of aspect areas.

        Args:
            domain_id: Optional filter by domain

        Returns:
            Dict with aspects
        """
        from ..domain.schema import Aspect

        aspects = []
        for a in Aspect:
            aspect_domain = _get_aspect_domain(a.value)
            if domain_id and aspect_domain != domain_id:
                continue

            aspects.append({
                "aspect_id": a.value,
                "domain_id": aspect_domain,
                "name": a.name,
                "description": _get_aspect_description(a.value),
            })

        return {"aspects": aspects}

    async def get_decision_matrix(self) -> Dict[str, Any]:
        """
        Get decision matrix (domains x aspects).

        Returns:
            Matrix with decision counts per cell
        """
        from ..domain.schema import Domain, Aspect

        matrix = {}
        for d in Domain:
            matrix[d.value] = {}
            for a in Aspect:
                # Only include relevant aspects for this domain
                if _get_aspect_domain(a.value) == d.value or _get_aspect_domain(a.value) == "COMMON":
                    matrix[d.value][a.value] = 0

        # Fill counts if repository available
        if self.repository:
            try:
                stored_decisions = await self.repository.find_all_async(limit=10000, offset=0)
                for sd in stored_decisions:
                    d = sd.decision.domain_id.value if hasattr(sd.decision.domain_id, 'value') else sd.decision.domain_id
                    a = sd.decision.aspect_id.value if hasattr(sd.decision.aspect_id, 'value') else sd.decision.aspect_id
                    if d in matrix and a in matrix[d]:
                        matrix[d][a] += 1
            except Exception as e:
                logger.warning(f"Could not populate matrix: {e}")

        return {"matrix": matrix}

    async def _count_decisions_in_domain(self, domain_id: str) -> int:
        """Count decisions in a domain."""
        if not self.repository:
            return 0
        try:
            stored = await self.repository.find_all_async(limit=10000, offset=0)
            return sum(
                1 for sd in stored
                if (sd.decision.domain_id.value if hasattr(sd.decision.domain_id, 'value') else sd.decision.domain_id) == domain_id
            )
        except:
            return 0


# =============================================================================
# Helper Functions
# =============================================================================

def _get_domain_description(domain_id: str) -> str:
    """Get human-readable domain description."""
    descriptions = {
        "ARCH": "Architectural decisions - system structure and design patterns",
        "STD": "Standards and conventions - coding style, naming, formatting",
        "PROC": "Processes and workflows - CI/CD, deployment, development flow",
        "IMPL": "Implementation details - specific technical choices",
        "SPEC": "Specifications - detailed requirements and contracts",
    }
    return descriptions.get(domain_id, f"Decision domain: {domain_id}")


def _get_aspect_description(aspect_id: str) -> str:
    """Get human-readable aspect description."""
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
    return descriptions.get(aspect_id, f"Aspect area: {aspect_id}")


def _get_aspect_domain(aspect_id: str) -> str:
    """Get the primary domain for an aspect."""
    # Most aspects are COMMON (applicable to multiple domains)
    domain_specific = {
        # Add domain-specific aspects here
    }
    return domain_specific.get(aspect_id, "COMMON")
