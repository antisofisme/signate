"""
MICS Context Assembly Pipeline

Assembles relevant MANTRA decisions into AI context.

Pipeline Stages:
1. Task Analysis: Extract keywords, intent, domain
2. Decision Selection: Find relevant decisions
3. Relevance Ranking: Score and rank decisions
4. Token Budget Allocation: Distribute budget across decisions
5. Content Assembly: Build context with appropriate detail levels
6. Context Packaging: Format for AI consumption

Token Budget Strategy:
- Allocate 60% to high-priority decisions (detailed)
- Allocate 30% to medium-priority (standard)
- Allocate 10% to low-priority (micro/summary)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class DetailLevel(str, Enum):
    """Content detail levels for tiered delivery."""
    MICRO = "micro"        # ~100 tokens - summary only
    STANDARD = "standard"  # ~500 tokens - statement + rationale
    DETAILED = "detailed"  # ~2000+ tokens - full content
    SECTIONS = "sections"  # variable - specific sections


class Priority(str, Enum):
    """Decision priority for context assembly."""
    CRITICAL = "critical"  # Must include
    HIGH = "high"          # Include if budget allows
    MEDIUM = "medium"      # Include in standard form
    LOW = "low"            # Include as micro only


@dataclass
class ScoredDecision:
    """Decision with relevance score."""
    decision: Any  # Decision object
    score: float  # Relevance score (0-1)
    priority: Priority
    matched_keywords: List[str]
    matched_tags: List[str]
    detail_level: DetailLevel = DetailLevel.STANDARD


@dataclass
class AssembledContext:
    """Final assembled context for AI."""
    decisions: List[Dict[str, Any]]
    total_tokens: int
    token_budget: int
    context_summary: str
    task_analysis: Dict[str, Any]
    priority_breakdown: Dict[str, int]


class ContextPipeline:
    """
    MICS Context Assembly Pipeline.

    Assembles relevant decisions into AI context respecting token budgets.

    Usage:
        pipeline = ContextPipeline(repository)
        context = await pipeline.assemble(
            task="Implement user authentication",
            code="def login(user, password)...",
            budget=2000
        )
    """

    def __init__(self, repository=None):
        """
        Initialize pipeline.

        Args:
            repository: DecisionRepository instance
        """
        self.repository = repository
        self.assembler = ContextAssembler()

    async def assemble(
        self,
        task: str,
        code: Optional[str] = None,
        budget: int = 2000,
        include_groups: Optional[List[str]] = None,
        exclude_groups: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assemble context for a task.

        Pipeline:
        1. Analyze task to extract intent and keywords
        2. Select relevant decisions from repository
        3. Rank by relevance to task
        4. Allocate token budget
        5. Assemble with appropriate detail levels
        6. Package for AI consumption

        Args:
            task: Task description
            code: Optional code context
            budget: Token budget
            include_groups: Only include these groups
            exclude_groups: Exclude these groups

        Returns:
            Assembled context dict
        """
        # Stage 1: Task Analysis
        task_analysis = self._analyze_task(task, code)
        logger.debug(f"Task analysis: {task_analysis}")

        # Stage 2: Decision Selection
        if not self.repository:
            return self._empty_context(task_analysis, budget)

        all_decisions = await self._fetch_decisions(include_groups, exclude_groups)
        logger.debug(f"Fetched {len(all_decisions)} decisions")

        # Stage 3: Relevance Ranking
        scored = self._score_decisions(all_decisions, task_analysis)
        scored.sort(key=lambda x: x.score, reverse=True)
        logger.debug(f"Scored {len(scored)} decisions")

        # Stage 4: Token Budget Allocation
        allocated = self._allocate_budget(scored, budget)

        # Stage 5: Content Assembly
        assembled = self.assembler.assemble(allocated, task_analysis)

        # Stage 6: Packaging
        return self._package_context(assembled, task_analysis, budget)

    def _analyze_task(self, task: str, code: Optional[str] = None) -> Dict[str, Any]:
        """Analyze task to extract intent, keywords, domain."""
        task_lower = task.lower()
        code_lower = (code or "").lower()

        # Extract keywords
        keywords = set()

        # Technical keywords
        tech_patterns = [
            (r'\b(database|db|sql|postgresql|mongodb|redis)\b', 'DATABASE'),
            (r'\b(api|rest|graphql|endpoint|route)\b', 'API'),
            (r'\b(auth|authentication|authorization|login|jwt|oauth)\b', 'AUTH'),
            (r'\b(frontend|ui|component|react|vue|angular)\b', 'UI'),
            (r'\b(backend|server|service|fastapi|django|express)\b', 'BACKEND'),
            (r'\b(test|testing|unit|integration|e2e)\b', 'TESTING'),
            (r'\b(deploy|deployment|docker|kubernetes|ci|cd)\b', 'INFRA'),
            (r'\b(security|encryption|ssl|tls|xss|csrf)\b', 'SECURITY'),
            (r'\b(cache|caching|performance|optimization)\b', 'PERFORMANCE'),
        ]

        detected_domains = set()
        for pattern, domain in tech_patterns:
            if re.search(pattern, task_lower) or re.search(pattern, code_lower):
                detected_domains.add(domain)
                keywords.update(re.findall(pattern, task_lower))
                keywords.update(re.findall(pattern, code_lower))

        # Extract action intent
        intent = "unknown"
        intent_patterns = [
            (r'\b(implement|create|build|add)\b', 'create'),
            (r'\b(fix|debug|solve|repair)\b', 'fix'),
            (r'\b(refactor|improve|optimize|clean)\b', 'refactor'),
            (r'\b(review|check|audit|validate)\b', 'review'),
            (r'\b(understand|explain|document)\b', 'understand'),
        ]
        for pattern, detected_intent in intent_patterns:
            if re.search(pattern, task_lower):
                intent = detected_intent
                break

        # Detect file types from code
        file_hints = set()
        if code:
            if 'def ' in code or 'class ' in code:
                file_hints.add('python')
            if 'function ' in code or 'const ' in code or '=>' in code:
                file_hints.add('javascript')
            if '<template>' in code or '<div>' in code:
                file_hints.add('vue/html')
            if 'interface ' in code or ': string' in code:
                file_hints.add('typescript')

        return {
            "task": task,
            "intent": intent,
            "keywords": list(keywords),
            "domains": list(detected_domains),
            "file_hints": list(file_hints),
            "has_code": code is not None,
        }

    async def _fetch_decisions(
        self,
        include_groups: Optional[List[str]],
        exclude_groups: Optional[List[str]]
    ) -> List[Any]:
        """Fetch decisions from repository."""
        try:
            stored = await self.repository.find_all_async(limit=10000, offset=0)
            decisions = []

            for sd in stored:
                d = sd.decision
                group = d.group_id.value if hasattr(d.group_id, 'value') else d.group_id

                if include_groups and group not in include_groups:
                    continue
                if exclude_groups and group in exclude_groups:
                    continue

                decisions.append(d)

            return decisions
        except Exception as e:
            logger.error(f"Failed to fetch decisions: {e}")
            return []

    def _score_decisions(
        self,
        decisions: List[Any],
        task_analysis: Dict[str, Any]
    ) -> List[ScoredDecision]:
        """Score decisions by relevance to task."""
        scored = []
        keywords = set(k.lower() for k in task_analysis.get("keywords", []))
        domains = set(task_analysis.get("domains", []))

        for d in decisions:
            # Build searchable text
            text = f"{d.statement} {d.rationale}".lower()
            tags = set(t.lower() for t in (d.tags or []))
            tech = set(t.lower() for t in (d.tech_stack or []))

            # Score components
            keyword_matches = [k for k in keywords if k in text]
            tag_matches = [t for t in tags if t in domains or any(k in t for k in keywords)]
            tech_matches = [t for t in tech if any(k in t.lower() for k in keywords)]

            # Calculate score
            score = 0.0

            # Keyword matching (40% weight)
            if keywords:
                score += 0.4 * (len(keyword_matches) / len(keywords))

            # Tag matching (30% weight)
            if tags:
                score += 0.3 * (len(tag_matches) / max(len(tags), 1))

            # Tech stack matching (20% weight)
            if tech:
                score += 0.2 * (len(tech_matches) / max(len(tech), 1))

            # Domain alignment (10% weight)
            feature = d.feature_id.value if hasattr(d.feature_id, 'value') else d.feature_id
            if feature in domains:
                score += 0.1

            # Determine priority
            if score >= 0.6:
                priority = Priority.CRITICAL
            elif score >= 0.4:
                priority = Priority.HIGH
            elif score >= 0.2:
                priority = Priority.MEDIUM
            else:
                priority = Priority.LOW

            if score > 0.1:  # Only include if some relevance
                scored.append(ScoredDecision(
                    decision=d,
                    score=score,
                    priority=priority,
                    matched_keywords=keyword_matches,
                    matched_tags=tag_matches
                ))

        return scored

    def _allocate_budget(
        self,
        scored: List[ScoredDecision],
        budget: int
    ) -> List[ScoredDecision]:
        """Allocate token budget to decisions."""
        # Budget allocation strategy:
        # - CRITICAL: detailed (~2000 tokens each, max 60% of budget)
        # - HIGH: standard (~500 tokens each, max 30% of budget)
        # - MEDIUM: micro (~100 tokens each, max 10% of budget)
        # - LOW: excluded unless budget remains

        critical_budget = int(budget * 0.6)
        high_budget = int(budget * 0.3)
        medium_budget = int(budget * 0.1)

        allocated = []
        used = {"critical": 0, "high": 0, "medium": 0}

        for sd in scored:
            if sd.priority == Priority.CRITICAL:
                if used["critical"] + 2000 <= critical_budget:
                    sd.detail_level = DetailLevel.DETAILED
                    used["critical"] += 2000
                    allocated.append(sd)
                elif used["high"] + 500 <= high_budget:
                    sd.detail_level = DetailLevel.STANDARD
                    used["high"] += 500
                    allocated.append(sd)

            elif sd.priority == Priority.HIGH:
                if used["high"] + 500 <= high_budget:
                    sd.detail_level = DetailLevel.STANDARD
                    used["high"] += 500
                    allocated.append(sd)
                elif used["medium"] + 100 <= medium_budget:
                    sd.detail_level = DetailLevel.MICRO
                    used["medium"] += 100
                    allocated.append(sd)

            elif sd.priority == Priority.MEDIUM:
                if used["medium"] + 100 <= medium_budget:
                    sd.detail_level = DetailLevel.MICRO
                    used["medium"] += 100
                    allocated.append(sd)

        return allocated

    def _empty_context(self, task_analysis: Dict, budget: int) -> Dict[str, Any]:
        """Return empty context when no repository."""
        return {
            "decisions": [],
            "total_tokens": 0,
            "token_budget": budget,
            "context_summary": "No decisions available (repository not configured)",
            "task_analysis": task_analysis,
            "priority_breakdown": {}
        }

    def _package_context(
        self,
        assembled: List[Dict],
        task_analysis: Dict,
        budget: int
    ) -> Dict[str, Any]:
        """Package assembled context for AI."""
        # Count by priority
        breakdown = {"critical": 0, "high": 0, "medium": 0}
        total_tokens = 0

        for d in assembled:
            level = d.get("_detail_level", "standard")
            if level == "detailed":
                breakdown["critical"] += 1
                total_tokens += 2000
            elif level == "standard":
                breakdown["high"] += 1
                total_tokens += 500
            else:
                breakdown["medium"] += 1
                total_tokens += 100

        # Generate summary
        summary = self._generate_summary(assembled, task_analysis)

        return {
            "decisions": assembled,
            "total_tokens": total_tokens,
            "token_budget": budget,
            "context_summary": summary,
            "task_analysis": task_analysis,
            "priority_breakdown": breakdown
        }

    def _generate_summary(self, decisions: List[Dict], task_analysis: Dict) -> str:
        """Generate human-readable context summary."""
        if not decisions:
            return f"No relevant decisions found for task: {task_analysis.get('task', 'unknown')[:50]}"

        lines = [
            f"Found {len(decisions)} relevant decisions for: {task_analysis.get('task', '')[:50]}",
            f"Domains: {', '.join(task_analysis.get('domains', ['general']))}",
            ""
        ]

        # Group by detail level
        by_level = {"detailed": [], "standard": [], "micro": []}
        for d in decisions:
            level = d.get("_detail_level", "standard")
            by_level[level].append(d.get("decision_code", "?"))

        if by_level["detailed"]:
            lines.append(f"Full context: {', '.join(by_level['detailed'][:3])}")
        if by_level["standard"]:
            lines.append(f"Standard: {', '.join(by_level['standard'][:5])}")
        if by_level["micro"]:
            lines.append(f"Summary: {', '.join(by_level['micro'][:5])}")

        return "\n".join(lines)


class ContextAssembler:
    """
    Assembles decision content at appropriate detail levels.

    Responsible for formatting decisions based on allocated detail level.
    """

    def assemble(
        self,
        scored_decisions: List[ScoredDecision],
        task_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Assemble decisions into context format.

        Args:
            scored_decisions: Decisions with allocated detail levels
            task_analysis: Task analysis for context

        Returns:
            List of formatted decision dicts
        """
        assembled = []

        for sd in scored_decisions:
            d = sd.decision
            formatted = self._format_decision(d, sd.detail_level)
            formatted["_relevance_score"] = sd.score
            formatted["_detail_level"] = sd.detail_level.value
            formatted["_matched_keywords"] = sd.matched_keywords
            assembled.append(formatted)

        return assembled

    def _format_decision(self, decision: Any, level: DetailLevel) -> Dict[str, Any]:
        """Format a single decision at specified detail level."""
        base = {
            "decision_id": decision.decision_id,
            "decision_code": decision.decision_code,
            "group_id": decision.group_id.value if hasattr(decision.group_id, 'value') else decision.group_id,
            "feature_id": decision.feature_id.value if hasattr(decision.feature_id, 'value') else decision.feature_id,
        }

        if level == DetailLevel.MICRO:
            # Minimal: just ID and summary
            base["summary"] = decision.content_summary or decision.statement[:100]
            return base

        # Standard and above: include statement and rationale
        base["statement"] = decision.statement
        base["rationale"] = decision.rationale
        base["scope"] = decision.scope.value if hasattr(decision.scope, 'value') else decision.scope
        base["tags"] = decision.tags or []

        if level == DetailLevel.STANDARD:
            # Truncate rationale if too long
            if len(base["rationale"]) > 500:
                base["rationale"] = base["rationale"][:500] + "..."
            return base

        # Detailed: include everything
        base["tech_stack"] = decision.tech_stack or []
        base["blast_radius"] = decision.blast_radius.value if hasattr(decision.blast_radius, 'value') else decision.blast_radius
        base["detailed_content"] = decision.detailed_content
        base["constraints"] = [
            {"type": c.type.value if hasattr(c.type, 'value') else c.type, "statement": c.statement}
            for c in (decision.constraints or [])
        ]
        base["sections"] = [
            {
                "section_id": s.section_id,
                "title": s.title,
                "section_type": s.section_type.value if hasattr(s.section_type, 'value') else s.section_type,
                "content": s.content
            }
            for s in (decision.sections or [])
        ]

        return base
