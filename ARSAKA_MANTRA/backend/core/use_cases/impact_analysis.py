"""
Impact Analysis Module for MANTRA Validator

Analyzes potential impact of a decision on the system:
1. Dependency Chain Analysis - Who depends on this/superseded decisions?
2. Reverse Dependencies - What does this decision depend on?
3. Tag/Area Impact - What technical areas are affected?
4. Blast Radius Assessment - Overall risk level
5. Breaking Change Detection - What might break when superseding?
6. Temporal Decay (Phase 8) - Weight recent decisions higher

Risk Levels:
- MINIMAL: Low blast_radius, APPLICATION scope, no dependencies
- LOW: Low blast_radius or few dependents
- MODERATE: Medium blast_radius with some dependents
- HIGH: High blast_radius or many dependents
- CRITICAL: Critical blast_radius or breaks important dependencies

Temporal Decay:
Old decisions contribute less to risk score:
- < 30 days: 100% weight (recent, active)
- 30-90 days: 80% weight
- 90-180 days: 60% weight
- 180-365 days: 40% weight
- > 365 days: 20% weight (potentially obsolete)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum


class ImpactLevel(str, Enum):
    """Overall impact/risk level of the decision."""
    MINIMAL = "MINIMAL"    # Safe to proceed
    LOW = "LOW"            # Low risk
    MODERATE = "MODERATE"  # Review recommended
    HIGH = "HIGH"          # Careful review required
    CRITICAL = "CRITICAL"  # High risk, extensive review required


class ImpactType(str, Enum):
    """Type of impact relationship."""
    DEPENDENCY = "dependency"              # Decision depends on this
    REVERSE_DEPENDENCY = "reverse_dependency"  # This depends on decision
    SUPERSEDES = "supersedes"              # This decision supersedes target
    SUPERSEDED_BY = "superseded_by"        # Target supersedes this
    SAME_ASPECT = "same_aspect"            # Same domain+aspect (potential override)
    SAME_TAG = "same_tag"                  # Shares technical area
    SAME_TECH_STACK = "same_tech_stack"    # Shares technology


@dataclass
class AffectedDecision:
    """A decision affected by the proposed change."""
    decision_id: str
    decision_code: Optional[str]
    domain_id: str
    aspect_id: str
    statement_preview: str
    impact_type: ImpactType
    impact_reason: str
    blast_radius: str  # Of the affected decision
    scope: str         # Of the affected decision
    created_at: Optional[datetime] = None  # For temporal decay weighting


@dataclass
class DependencyChain:
    """Represents a chain of dependencies."""
    root_decision_id: str
    chain: List[str]  # List of decision IDs in the chain
    depth: int
    is_circular: bool = False


@dataclass
class BreakingChange:
    """Represents a potential breaking change."""
    superseded_id: str
    superseded_code: Optional[str]
    dependent_decisions: List[AffectedDecision]
    risk_level: ImpactLevel
    description: str
    mitigation: str


@dataclass
class ImpactAnalysisResult:
    """Complete impact analysis result."""
    # Overall assessment
    overall_risk: ImpactLevel
    risk_score: int  # 0-100

    # Affected decisions
    affected_decisions: List[AffectedDecision]
    affected_count: int

    # Dependency analysis
    dependency_chains: List[DependencyChain]
    reverse_dependencies: List[AffectedDecision]
    max_dependency_depth: int

    # Breaking changes (if superseding)
    breaking_changes: List[BreakingChange]
    has_breaking_changes: bool

    # Area/Tech impact
    affected_areas: List[str]  # Tags
    affected_tech_stack: List[str]

    # blast_radius validation (declared vs calculated)
    blast_radius_accurate: bool = True
    blast_radius_warning: Optional[str] = None

    # Risk factors
    risk_factors: List[str] = None

    # Recommendations
    recommendations: List[str] = None

    # Summary
    summary: str = ""


# =============================================================================
# Risk Scoring Weights
# =============================================================================

BLAST_RADIUS_WEIGHTS = {
    "LOW": 10,
    "MEDIUM": 25,
    "HIGH": 50,
    "CRITICAL": 80
}

SCOPE_WEIGHTS = {
    "APPLICATION": 10,
    "DOMAIN": 30,
    "ORGANIZATION": 50
}

# Points per affected decision by type
IMPACT_TYPE_WEIGHTS = {
    ImpactType.DEPENDENCY: 15,          # Something depends on this
    ImpactType.REVERSE_DEPENDENCY: 5,   # This depends on something
    ImpactType.SUPERSEDES: 20,          # Superseding another decision
    ImpactType.SUPERSEDED_BY: 0,        # Info only
    ImpactType.SAME_ASPECT: 10,         # Potential conflict
    ImpactType.SAME_TAG: 3,             # Related area
    ImpactType.SAME_TECH_STACK: 2,      # Related tech
}


# =============================================================================
# Temporal Decay (Phase 8)
# =============================================================================

def calculate_temporal_weight(created_at: Optional[datetime]) -> float:
    """
    Calculate temporal weight for a decision based on age.

    Recent decisions matter more than old ones because:
    - Old decisions may be obsolete but not formally superseded
    - Recent decisions reflect current architectural thinking
    - Stale dependencies indicate technical debt

    Weight scale:
    - < 30 days: 1.0 (full weight)
    - 30-90 days: 0.8
    - 90-180 days: 0.6
    - 180-365 days: 0.4
    - > 365 days: 0.2

    Args:
        created_at: Decision creation timestamp (None = unknown age)

    Returns:
        Weight multiplier between 0.2 and 1.0
    """
    if created_at is None:
        return 0.5  # Unknown age gets middle weight

    now = datetime.utcnow()

    # Handle timezone-aware datetimes
    if created_at.tzinfo is not None:
        # Make now timezone-aware to match
        from datetime import timezone
        now = datetime.now(timezone.utc)

    try:
        age = now - created_at
        age_days = age.days
    except TypeError:
        # If datetime comparison fails, use default
        return 0.5

    if age_days < 0:
        # Future date (data issue), treat as new
        return 1.0
    elif age_days < 30:
        return 1.0
    elif age_days < 90:
        return 0.8
    elif age_days < 180:
        return 0.6
    elif age_days < 365:
        return 0.4
    else:
        return 0.2


# =============================================================================
# Analysis Functions
# =============================================================================

def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try basic format
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
    return None


def find_dependents(
    decision_id: str,
    existing_decisions: List[Dict[str, Any]]
) -> List[AffectedDecision]:
    """Find decisions that depend on the given decision."""
    dependents = []

    for existing in existing_decisions:
        created_at = _parse_datetime(existing.get('created_at'))

        # Check related_decisions (deprecated but still used)
        related = existing.get('related_decisions', [])
        if decision_id in related:
            dependents.append(AffectedDecision(
                decision_id=existing.get('decision_id', ''),
                decision_code=existing.get('decision_code'),
                domain_id=existing.get('domain_id', ''),
                aspect_id=existing.get('aspect_id', ''),
                statement_preview=(existing.get('statement') or '')[:100],
                impact_type=ImpactType.DEPENDENCY,
                impact_reason="Listed in related_decisions",
                blast_radius=existing.get('blast_radius', 'UNKNOWN'),
                scope=existing.get('scope', 'UNKNOWN'),
                created_at=created_at
            ))
            continue

        # Check typed relations
        relations = existing.get('relations', [])
        for relation in relations:
            if isinstance(relation, dict):
                if relation.get('target_id') == decision_id:
                    rel_type = relation.get('type', '')
                    dependents.append(AffectedDecision(
                        decision_id=existing.get('decision_id', ''),
                        decision_code=existing.get('decision_code'),
                        domain_id=existing.get('domain_id', ''),
                        aspect_id=existing.get('aspect_id', ''),
                        statement_preview=(existing.get('statement') or '')[:100],
                        impact_type=ImpactType.DEPENDENCY,
                        impact_reason=f"Has '{rel_type}' relation",
                        blast_radius=existing.get('blast_radius', 'UNKNOWN'),
                        scope=existing.get('scope', 'UNKNOWN'),
                        created_at=created_at
                    ))
                    break

    return dependents


def find_reverse_dependencies(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> List[AffectedDecision]:
    """Find decisions that the record depends on."""
    reverse_deps = []

    # Check related_decisions
    related_ids = record.get('related_decisions', [])

    # Check typed relations
    relations = record.get('relations', [])
    for relation in relations:
        if isinstance(relation, dict):
            target_id = relation.get('target_id')
            if target_id and target_id not in related_ids:
                related_ids.append(target_id)

    # Find the actual decisions
    for existing in existing_decisions:
        existing_id = existing.get('decision_id', '')
        if existing_id in related_ids:
            created_at = _parse_datetime(existing.get('created_at'))
            reverse_deps.append(AffectedDecision(
                decision_id=existing_id,
                decision_code=existing.get('decision_code'),
                domain_id=existing.get('domain_id', ''),
                aspect_id=existing.get('aspect_id', ''),
                statement_preview=(existing.get('statement') or '')[:100],
                impact_type=ImpactType.REVERSE_DEPENDENCY,
                impact_reason="Referenced by this decision",
                blast_radius=existing.get('blast_radius', 'UNKNOWN'),
                scope=existing.get('scope', 'UNKNOWN'),
                created_at=created_at
            ))

    return reverse_deps


def find_supersession_impact(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> Tuple[List[AffectedDecision], List[BreakingChange]]:
    """
    Analyze impact of supersession.

    Returns:
        (affected_decisions, breaking_changes)
    """
    affected = []
    breaking_changes = []

    supersedes_id = record.get('supersedes')
    if not supersedes_id:
        return affected, breaking_changes

    # Find the superseded decision
    superseded = None
    for existing in existing_decisions:
        if existing.get('decision_id') == supersedes_id:
            superseded = existing
            break

    if not superseded:
        return affected, breaking_changes

    # Add superseded decision as affected
    created_at = _parse_datetime(superseded.get('created_at'))
    affected.append(AffectedDecision(
        decision_id=supersedes_id,
        decision_code=superseded.get('decision_code'),
        domain_id=superseded.get('domain_id', ''),
        aspect_id=superseded.get('aspect_id', ''),
        statement_preview=(superseded.get('statement') or '')[:100],
        impact_type=ImpactType.SUPERSEDES,
        impact_reason="Being superseded by this decision",
        blast_radius=superseded.get('blast_radius', 'UNKNOWN'),
        scope=superseded.get('scope', 'UNKNOWN'),
        created_at=created_at
    ))

    # Find who depends on the superseded decision
    dependents = find_dependents(supersedes_id, existing_decisions)

    if dependents:
        # This is a potential breaking change
        risk = ImpactLevel.HIGH if len(dependents) > 3 else ImpactLevel.MODERATE

        breaking_changes.append(BreakingChange(
            superseded_id=supersedes_id,
            superseded_code=superseded.get('decision_code'),
            dependent_decisions=dependents,
            risk_level=risk,
            description=f"{len(dependents)} decision(s) depend on the superseded decision",
            mitigation="Update dependent decisions to reference the new version"
        ))

        affected.extend(dependents)

    return affected, breaking_changes


def find_same_aspect_decisions(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> List[AffectedDecision]:
    """Find decisions in the same domain+aspect."""
    same_aspect = []

    record_domain = record.get('domain_id')
    record_aspect = record.get('aspect_id')
    record_id = record.get('decision_id', '')
    supersedes_id = record.get('supersedes')

    for existing in existing_decisions:
        existing_id = existing.get('decision_id', '')

        # Skip self and superseded (already handled)
        if existing_id == record_id or existing_id == supersedes_id:
            continue

        if (existing.get('domain_id') == record_domain and
            existing.get('aspect_id') == record_aspect):
            created_at = _parse_datetime(existing.get('created_at'))
            same_aspect.append(AffectedDecision(
                decision_id=existing_id,
                decision_code=existing.get('decision_code'),
                domain_id=existing.get('domain_id', ''),
                aspect_id=existing.get('aspect_id', ''),
                statement_preview=(existing.get('statement') or '')[:100],
                impact_type=ImpactType.SAME_ASPECT,
                impact_reason="Same domain and aspect - potential overlap",
                blast_radius=existing.get('blast_radius', 'UNKNOWN'),
                scope=existing.get('scope', 'UNKNOWN'),
                created_at=created_at
            ))

    return same_aspect


def find_tag_overlap(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> Tuple[List[AffectedDecision], Set[str]]:
    """Find decisions with overlapping tags."""
    overlapping = []
    all_affected_tags: Set[str] = set()

    record_tags = set(record.get('tags', []))
    record_id = record.get('decision_id', '')

    if not record_tags:
        return overlapping, all_affected_tags

    all_affected_tags.update(record_tags)

    for existing in existing_decisions:
        existing_id = existing.get('decision_id', '')
        if existing_id == record_id:
            continue

        existing_tags = set(existing.get('tags', []))
        common_tags = record_tags & existing_tags

        if common_tags:
            created_at = _parse_datetime(existing.get('created_at'))
            overlapping.append(AffectedDecision(
                decision_id=existing_id,
                decision_code=existing.get('decision_code'),
                domain_id=existing.get('domain_id', ''),
                aspect_id=existing.get('aspect_id', ''),
                statement_preview=(existing.get('statement') or '')[:100],
                impact_type=ImpactType.SAME_TAG,
                impact_reason=f"Shares tags: {', '.join(common_tags)}",
                blast_radius=existing.get('blast_radius', 'UNKNOWN'),
                scope=existing.get('scope', 'UNKNOWN'),
                created_at=created_at
            ))
            all_affected_tags.update(existing_tags)

    return overlapping, all_affected_tags


def find_tech_stack_overlap(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> Tuple[List[AffectedDecision], Set[str]]:
    """Find decisions with overlapping tech stack."""
    overlapping = []
    all_tech: Set[str] = set()

    record_tech = set(t.lower() for t in record.get('tech_stack', []))
    record_id = record.get('decision_id', '')

    if not record_tech:
        return overlapping, all_tech

    all_tech.update(record_tech)

    for existing in existing_decisions:
        existing_id = existing.get('decision_id', '')
        if existing_id == record_id:
            continue

        existing_tech = set(t.lower() for t in existing.get('tech_stack', []))
        common_tech = record_tech & existing_tech

        if common_tech:
            created_at = _parse_datetime(existing.get('created_at'))
            overlapping.append(AffectedDecision(
                decision_id=existing_id,
                decision_code=existing.get('decision_code'),
                domain_id=existing.get('domain_id', ''),
                aspect_id=existing.get('aspect_id', ''),
                statement_preview=(existing.get('statement') or '')[:100],
                impact_type=ImpactType.SAME_TECH_STACK,
                impact_reason=f"Shares tech: {', '.join(common_tech)}",
                blast_radius=existing.get('blast_radius', 'UNKNOWN'),
                scope=existing.get('scope', 'UNKNOWN'),
                created_at=created_at
            ))
            all_tech.update(existing_tech)

    return overlapping, all_tech


def build_dependency_chains(
    decision_id: str,
    existing_decisions: List[Dict[str, Any]],
    max_depth: int = 5
) -> List[DependencyChain]:
    """
    Build dependency chains starting from a decision.

    Finds decisions that depend on this, and recursively their dependents.
    """
    chains: List[DependencyChain] = []
    visited: Set[str] = set()

    def trace_chain(current_id: str, chain: List[str], depth: int) -> None:
        if depth > max_depth:
            return

        if current_id in visited:
            # Circular dependency detected
            chains.append(DependencyChain(
                root_decision_id=chain[0] if chain else current_id,
                chain=chain + [current_id],
                depth=depth,
                is_circular=True
            ))
            return

        visited.add(current_id)
        dependents = find_dependents(current_id, existing_decisions)

        if not dependents:
            if len(chain) > 1:  # Only add meaningful chains
                chains.append(DependencyChain(
                    root_decision_id=chain[0],
                    chain=chain,
                    depth=depth,
                    is_circular=False
                ))
            return

        for dependent in dependents:
            trace_chain(
                dependent.decision_id,
                chain + [dependent.decision_id],
                depth + 1
            )

    trace_chain(decision_id, [decision_id], 0)

    return chains


def calculate_risk_score(
    record: Dict[str, Any],
    affected_decisions: List[AffectedDecision],
    breaking_changes: List[BreakingChange],
    max_depth: int
) -> int:
    """
    Calculate overall risk score (0-100).

    REBALANCED (Phase 5): Uses logarithmic scaling to prevent saturation.
    Previously, HIGH blast_radius + ORGANIZATION scope = 100 before
    counting any dependencies. Now uses:
    - Reduced base weights (max ~50 from declared metadata)
    - Logarithmic scaling for many dependents
    - Dependency depth limited contribution

    TEMPORAL DECAY (Phase 8): Weights recent decisions higher.
    Old decisions (> 1 year) contribute only 20% of their base weight.
    This reflects that old, potentially obsolete decisions shouldn't
    inflate impact scores as much as recent, active decisions.
    """
    import math

    score = 0

    # Base score from blast_radius and scope (REBALANCED - max ~50 combined)
    # Reduced to leave room for calculated impact factors
    blast_radius = record.get('blast_radius', 'LOW')
    scope = record.get('scope', 'APPLICATION')

    # REBALANCED: Reduced weights (old: 10/25/50/80 and 10/30/50)
    blast_weights_rebalanced = {
        "LOW": 5,
        "MEDIUM": 15,
        "HIGH": 30,
        "CRITICAL": 45
    }
    scope_weights_rebalanced = {
        "APPLICATION": 5,
        "DOMAIN": 15,
        "ORGANIZATION": 25
    }

    score += blast_weights_rebalanced.get(blast_radius, 5)
    score += scope_weights_rebalanced.get(scope, 5)

    # Points for affected decisions with LOGARITHMIC scaling + TEMPORAL DECAY
    # 1 affected = ~10 pts, 10 affected = ~23 pts, 100 affected = ~46 pts
    # But old decisions (> 1 year) contribute only ~20% of their weight
    dependency_score = 0
    for affected in affected_decisions:
        base_weight = IMPACT_TYPE_WEIGHTS.get(affected.impact_type, 1)
        # Apply temporal decay (Phase 8)
        temporal_weight = calculate_temporal_weight(affected.created_at)
        dependency_score += base_weight * temporal_weight

    if dependency_score > 0:
        # Logarithmic scaling: 10 * log10(score + 1) * 2.3
        # This grows slowly: 1->~7, 10->~23, 50->~39, 100->~46
        scaled_dependency = int(10 * math.log10(dependency_score + 1) * 2.3)
        score += scaled_dependency

    # Breaking changes penalty with logarithmic scaling + temporal decay
    breaking_score = 0
    for bc in breaking_changes:
        for dep in bc.dependent_decisions:
            temporal_weight = calculate_temporal_weight(dep.created_at)
            breaking_score += temporal_weight  # Count each dependent with decay

    if breaking_score > 0:
        # Similar logarithmic scaling
        breaking_penalty = int(10 * math.log10(breaking_score + 1) * 2)
        score += breaking_penalty

    # Dependency depth (capped at 15 points)
    depth_penalty = min(max_depth * 3, 15)
    score += depth_penalty

    # Cap at 100
    return min(100, score)


def determine_risk_level(score: int) -> ImpactLevel:
    """Determine risk level from score."""
    if score >= 80:
        return ImpactLevel.CRITICAL
    elif score >= 60:
        return ImpactLevel.HIGH
    elif score >= 40:
        return ImpactLevel.MODERATE
    elif score >= 20:
        return ImpactLevel.LOW
    else:
        return ImpactLevel.MINIMAL


def validate_blast_radius(
    declared_radius: str,
    calculated_risk: ImpactLevel,
    affected_count: int
) -> Tuple[bool, Optional[str]]:
    """
    Validate if declared blast_radius matches calculated impact.

    This helps catch cases where users understate or overstate
    the impact of their decisions.

    Returns:
        (is_accurate, warning_message)
    """
    # Map calculated risk to expected radius
    risk_to_radius = {
        ImpactLevel.MINIMAL: "LOW",
        ImpactLevel.LOW: "LOW",
        ImpactLevel.MODERATE: "MEDIUM",
        ImpactLevel.HIGH: "HIGH",
        ImpactLevel.CRITICAL: "CRITICAL"
    }
    expected_radius = risk_to_radius.get(calculated_risk, "LOW")

    # Define radius ordering
    radius_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Get indices
    try:
        declared_idx = radius_order.index(declared_radius.upper())
    except ValueError:
        declared_idx = 0  # Default to LOW if unknown

    try:
        expected_idx = radius_order.index(expected_radius)
    except ValueError:
        expected_idx = 0

    # Allow 1 level difference as acceptable
    if abs(declared_idx - expected_idx) <= 1:
        return True, None

    # Mismatch detected
    if declared_idx < expected_idx:
        return False, (
            f"Declared blast_radius ({declared_radius}) is LOWER than "
            f"calculated ({expected_radius}). {affected_count} decisions affected. "
            f"Consider updating to {expected_radius}."
        )
    else:
        return False, (
            f"Declared blast_radius ({declared_radius}) may be overstated. "
            f"Calculated risk is {expected_radius} based on {affected_count} affected decisions."
        )


def generate_risk_factors(
    record: Dict[str, Any],
    affected_decisions: List[AffectedDecision],
    breaking_changes: List[BreakingChange],
    dependency_chains: List[DependencyChain]
) -> List[str]:
    """Generate list of risk factors."""
    factors = []

    blast_radius = record.get('blast_radius', 'LOW')
    scope = record.get('scope', 'APPLICATION')

    if blast_radius in ('HIGH', 'CRITICAL'):
        factors.append(f"High blast radius: {blast_radius}")

    if scope == 'ORGANIZATION':
        factors.append("Organization-wide scope affects entire system")

    if breaking_changes:
        total_deps = sum(len(bc.dependent_decisions) for bc in breaking_changes)
        factors.append(f"Breaking change: {total_deps} decision(s) depend on superseded")

    dep_count = sum(1 for a in affected_decisions if a.impact_type == ImpactType.DEPENDENCY)
    if dep_count > 5:
        factors.append(f"High dependency count: {dep_count} decisions depend on this")

    circular = [c for c in dependency_chains if c.is_circular]
    if circular:
        factors.append(f"Circular dependency detected in {len(circular)} chain(s)")

    max_depth = max((c.depth for c in dependency_chains), default=0)
    if max_depth > 3:
        factors.append(f"Deep dependency chain: {max_depth} levels")

    same_aspect = sum(1 for a in affected_decisions if a.impact_type == ImpactType.SAME_ASPECT)
    if same_aspect > 2:
        factors.append(f"{same_aspect} existing decisions in same aspect - potential conflicts")

    return factors


def generate_recommendations(
    record: Dict[str, Any],
    affected_decisions: List[AffectedDecision],
    breaking_changes: List[BreakingChange],
    risk_level: ImpactLevel
) -> List[str]:
    """Generate recommendations based on analysis."""
    recommendations = []

    if risk_level in (ImpactLevel.HIGH, ImpactLevel.CRITICAL):
        recommendations.append("Consider peer review before finalizing this decision")

    if breaking_changes:
        for bc in breaking_changes:
            recommendations.append(
                f"Update {len(bc.dependent_decisions)} dependent decision(s) "
                f"to reference this version instead of {bc.superseded_code or bc.superseded_id[:8]}"
            )

    same_aspect = [a for a in affected_decisions if a.impact_type == ImpactType.SAME_ASPECT]
    if same_aspect and not record.get('supersedes'):
        recommendations.append(
            f"Consider if this should supersede existing decision(s) in the same aspect: "
            f"{', '.join(a.decision_code or a.decision_id[:8] for a in same_aspect[:3])}"
        )

    if not record.get('tags'):
        recommendations.append("Add tags (FE, BE, DB, etc.) to improve impact visibility")

    if not record.get('tech_stack'):
        recommendations.append("Add tech_stack to improve dependency tracking")

    deps = [a for a in affected_decisions if a.impact_type == ImpactType.DEPENDENCY]
    if deps:
        critical_deps = [a for a in deps if a.blast_radius in ('HIGH', 'CRITICAL')]
        if critical_deps:
            recommendations.append(
                f"Review {len(critical_deps)} high-impact dependent decision(s): "
                f"{', '.join(a.decision_code or a.decision_id[:8] for a in critical_deps[:3])}"
            )

    return recommendations[:7]  # Limit to 7


def generate_summary(
    risk_level: ImpactLevel,
    risk_score: int,
    affected_count: int,
    breaking_changes: List[BreakingChange],
    affected_areas: List[str]
) -> str:
    """Generate human-readable summary."""
    parts = [f"Impact Level: {risk_level.value} (Score: {risk_score}/100)"]

    if affected_count > 0:
        parts.append(f"{affected_count} decision(s) may be affected")
    else:
        parts.append("No directly affected decisions found")

    if breaking_changes:
        total = sum(len(bc.dependent_decisions) for bc in breaking_changes)
        parts.append(f"BREAKING CHANGE: {total} dependent decision(s) need update")

    if affected_areas:
        parts.append(f"Affected areas: {', '.join(affected_areas[:5])}")

    return ". ".join(parts) + "."


# =============================================================================
# Main Analysis Function
# =============================================================================

def analyze_impact(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> ImpactAnalysisResult:
    """
    Perform comprehensive impact analysis.

    Args:
        record: New/proposed decision record
        existing_decisions: List of existing decision dicts

    Returns:
        ImpactAnalysisResult with full analysis
    """
    all_affected: List[AffectedDecision] = []

    # 1. Supersession impact (most important)
    supersession_affected, breaking_changes = find_supersession_impact(
        record, existing_decisions
    )
    all_affected.extend(supersession_affected)

    # 2. Same aspect decisions
    same_aspect = find_same_aspect_decisions(record, existing_decisions)
    all_affected.extend(same_aspect)

    # 3. Reverse dependencies (what this decision depends on)
    reverse_deps = find_reverse_dependencies(record, existing_decisions)
    all_affected.extend(reverse_deps)

    # 4. Tag overlap
    tag_overlap, affected_tags = find_tag_overlap(record, existing_decisions)
    # Don't add to all_affected (too noisy) but track tags

    # 5. Tech stack overlap
    tech_overlap, affected_tech = find_tech_stack_overlap(record, existing_decisions)
    # Don't add to all_affected (too noisy) but track tech

    # 6. Build dependency chains
    decision_id = record.get('decision_id', '')
    dependency_chains = build_dependency_chains(
        decision_id, existing_decisions, max_depth=5
    )

    # Calculate max depth
    max_depth = max((c.depth for c in dependency_chains), default=0)

    # Remove duplicates from affected
    seen_ids = set()
    unique_affected = []
    for affected in all_affected:
        if affected.decision_id not in seen_ids:
            seen_ids.add(affected.decision_id)
            unique_affected.append(affected)

    # Calculate risk
    risk_score = calculate_risk_score(
        record, unique_affected, breaking_changes, max_depth
    )
    risk_level = determine_risk_level(risk_score)

    # Validate blast_radius declared vs calculated
    declared_radius = record.get('blast_radius', 'LOW')
    radius_accurate, radius_warning = validate_blast_radius(
        declared_radius, risk_level, len(unique_affected)
    )

    # Generate feedback
    risk_factors = generate_risk_factors(
        record, unique_affected, breaking_changes, dependency_chains
    )

    # Add blast_radius warning to risk factors if mismatch
    if radius_warning:
        risk_factors.append(f"Blast radius mismatch: {radius_warning}")

    recommendations = generate_recommendations(
        record, unique_affected, breaking_changes, risk_level
    )

    # Generate summary
    summary = generate_summary(
        risk_level, risk_score, len(unique_affected),
        breaking_changes, list(affected_tags)
    )

    return ImpactAnalysisResult(
        overall_risk=risk_level,
        risk_score=risk_score,
        affected_decisions=unique_affected[:20],  # Limit to 20
        affected_count=len(unique_affected),
        dependency_chains=dependency_chains[:10],  # Limit to 10
        reverse_dependencies=reverse_deps,
        max_dependency_depth=max_depth,
        breaking_changes=breaking_changes,
        has_breaking_changes=len(breaking_changes) > 0,
        affected_areas=list(affected_tags)[:10],
        affected_tech_stack=list(affected_tech)[:10],
        blast_radius_accurate=radius_accurate,
        blast_radius_warning=radius_warning,
        risk_factors=risk_factors,
        recommendations=recommendations,
        summary=summary
    )


# =============================================================================
# Async Helper
# =============================================================================

async def analyze_impact_async(
    record: Dict[str, Any],
    repository
) -> ImpactAnalysisResult:
    """
    Async version that fetches existing decisions from repository.

    Args:
        record: Decision record to analyze
        repository: DecisionRepository instance

    Returns:
        ImpactAnalysisResult
    """
    stored_decisions = await repository.find_all_async(limit=10000, offset=0)

    existing_decisions = [
        {
            'decision_id': sd.decision.decision_id,
            'decision_code': sd.decision.decision_code,
            'domain_id': sd.decision.domain_id.value,
            'aspect_id': sd.decision.aspect_id.value,
            'statement': sd.decision.statement,
            'scope': sd.decision.scope.value,
            'blast_radius': sd.decision.blast_radius.value,
            'supersedes': sd.decision.supersedes,
            'related_decisions': sd.decision.related_decisions,
            'relations': [
                {'target_id': r.target_id, 'type': r.type.value}
                for r in sd.decision.relations
            ] if hasattr(sd.decision, 'relations') else [],
            'tags': sd.decision.tags if hasattr(sd.decision, 'tags') else [],
            'tech_stack': sd.decision.tech_stack if hasattr(sd.decision, 'tech_stack') else [],
        }
        for sd in stored_decisions
    ]

    return analyze_impact(record, existing_decisions)


# =============================================================================
# Serialization Helper
# =============================================================================

def serialize_impact_result(result: ImpactAnalysisResult) -> Dict[str, Any]:
    """Serialize ImpactAnalysisResult to dict for API response."""
    return {
        'overall_risk': result.overall_risk.value,
        'risk_score': result.risk_score,
        'affected_decisions': [
            {
                'decision_id': a.decision_id,
                'decision_code': a.decision_code,
                'domain_id': a.domain_id,
                'aspect_id': a.aspect_id,
                'statement_preview': a.statement_preview,
                'impact_type': a.impact_type.value,
                'impact_reason': a.impact_reason,
                'blast_radius': a.blast_radius,
                'scope': a.scope,
            }
            for a in result.affected_decisions
        ],
        'affected_count': result.affected_count,
        'dependency_chains': [
            {
                'root_decision_id': c.root_decision_id,
                'chain': c.chain,
                'depth': c.depth,
                'is_circular': c.is_circular,
            }
            for c in result.dependency_chains
        ],
        'reverse_dependencies': [
            {
                'decision_id': r.decision_id,
                'decision_code': r.decision_code,
                'statement_preview': r.statement_preview,
            }
            for r in result.reverse_dependencies
        ],
        'max_dependency_depth': result.max_dependency_depth,
        'breaking_changes': [
            {
                'superseded_id': bc.superseded_id,
                'superseded_code': bc.superseded_code,
                'dependent_count': len(bc.dependent_decisions),
                'risk_level': bc.risk_level.value,
                'description': bc.description,
                'mitigation': bc.mitigation,
            }
            for bc in result.breaking_changes
        ],
        'has_breaking_changes': result.has_breaking_changes,
        'affected_areas': result.affected_areas,
        'affected_tech_stack': result.affected_tech_stack,
        'blast_radius_accurate': result.blast_radius_accurate,
        'blast_radius_warning': result.blast_radius_warning,
        'risk_factors': result.risk_factors or [],
        'recommendations': result.recommendations or [],
        'summary': result.summary,
    }
