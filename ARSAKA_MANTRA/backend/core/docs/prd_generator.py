"""
MANTRA PRD (Product Requirements Document) Generator

Generates comprehensive product requirements documentation.

Features:
- User stories with acceptance criteria
- Feature breakdown by priority
- Dependencies and constraints
- Timeline considerations (if available)

OUTPUT STRUCTURE:
1. Executive Summary - High-level overview
2. Goals & Objectives - What we're trying to achieve
3. User Stories - Who, What, Why
4. Features - Detailed feature breakdown
5. Constraints - Technical and business constraints
6. Dependencies - What this depends on
7. Success Criteria - How we measure success
8. Appendix - References, glossary
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class PRDGenerator(DocumentGenerator):
    """Generates Product Requirements Documents."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.PRD

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate PRD sections from decisions."""
        sections = []

        # 1. Executive Summary
        sections.append(self._generate_executive_summary(decisions, config))

        # 2. Goals & Objectives
        sections.append(self._generate_goals(decisions))

        # 3. User Stories
        sections.append(self._generate_user_stories(decisions))

        # 4. Features
        sections.append(self._generate_features(decisions))

        # 5. Constraints
        sections.append(self._generate_constraints(decisions))

        # 6. Dependencies
        sections.append(self._generate_dependencies(decisions))

        # 7. Success Criteria
        sections.append(self._generate_success_criteria(decisions))

        # 8. Appendix
        sections.append(self._generate_appendix(decisions))

        return sections

    def _generate_executive_summary(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate executive summary."""
        # Count by priority
        critical = len([d for d in decisions if d.get("impact") == "CRITICAL"])
        important = len([d for d in decisions if d.get("impact") == "IMPORTANT"])

        content = f"""## Executive Summary

This Product Requirements Document defines **{len(decisions)} decisions** that shape the product.

**Priority Breakdown:**
- Critical Requirements: {critical}
- Important Requirements: {important}
- Reference Requirements: {len(decisions) - critical - important}

**Document Purpose:**
This PRD serves as the single source of truth for product requirements, derived from
MANTRA decisions. It defines what to build, why, and the acceptance criteria for success.

**Audience:**
- Product Managers: Feature planning and prioritization
- Developers: Implementation guidance
- Designers: UX requirements and constraints
- Stakeholders: Business alignment

"""
        return DocumentSection(
            id="executive-summary",
            title="Executive Summary",
            content=content,
            level=1,
        )

    def _generate_goals(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate goals and objectives section."""
        content_lines = ["## Goals & Objectives\n"]

        # Extract goals from INT domain decisions
        int_decisions = [d for d in decisions if d.get("domain_id") == "INT"]

        if int_decisions:
            content_lines.append("### Product Goals\n")
            for d in int_decisions[:5]:
                summary = d.get("summary", d.get("statement", "")[:100])
                code = d.get("code", "")
                content_lines.append(f"- **[{code}]** {summary}")
            content_lines.append("")

        # Extract objectives from tags
        content_lines.append("### Key Objectives\n")
        objectives = set()
        for d in decisions:
            tags = d.get("tags", [])
            for tag in tags:
                if tag.lower() in ["goal", "objective", "target", "kpi"]:
                    objectives.add(d.get("summary", "")[:80])

        if objectives:
            for obj in list(objectives)[:10]:
                content_lines.append(f"- {obj}")
        else:
            content_lines.append("- Deliver high-quality product features")
            content_lines.append("- Ensure technical excellence")
            content_lines.append("- Meet stakeholder expectations")

        return DocumentSection(
            id="goals",
            title="Goals & Objectives",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in int_decisions[:5]],
        )

    def _generate_user_stories(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate user stories section."""
        subsections = []

        # Group by scope to create user story categories
        by_scope: Dict[str, List[Dict]] = {}
        for d in decisions:
            scope = d.get("scope_path", "*")
            top_scope = scope.split(".")[0] if scope != "*" else "general"
            if top_scope not in by_scope:
                by_scope[top_scope] = []
            by_scope[top_scope].append(d)

        for scope, scope_decisions in by_scope.items():
            content_lines = []

            for d in scope_decisions[:5]:
                code = d.get("code", "")
                statement = d.get("statement", "")
                rationale = d.get("rationale", "")

                # Format as user story
                content_lines.append(f"#### {code}")
                content_lines.append(f"**As a** user of the {scope} system,")
                content_lines.append(f"**I want** {statement[:200]}")
                if rationale:
                    content_lines.append(f"**So that** {rationale[:150]}...")
                content_lines.append("")

                # Acceptance criteria from constraints
                constraints = d.get("constraints", [])
                if constraints:
                    content_lines.append("**Acceptance Criteria:**")
                    for c in constraints[:3]:
                        rule = c.get("rule", str(c)) if isinstance(c, dict) else str(c)
                        content_lines.append(f"- [ ] {rule[:100]}")
                    content_lines.append("")

            subsections.append(DocumentSection(
                id=f"stories-{scope}",
                title=f"{scope.upper()} User Stories",
                content="\n".join(content_lines),
                level=2,
                decision_ids=[d.get("code", "") for d in scope_decisions[:5]],
            ))

        return DocumentSection(
            id="user-stories",
            title="User Stories",
            content="User stories grouped by product area:",
            level=1,
            subsections=subsections,
        )

    def _generate_features(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate features breakdown."""
        content_lines = ["## Features\n"]

        # Sort by priority_rank
        sorted_decisions = sorted(
            decisions,
            key=lambda d: d.get("priority_rank", 50)
        )

        # Group by impact for priority sections
        critical = [d for d in sorted_decisions if d.get("impact") == "CRITICAL"]
        important = [d for d in sorted_decisions if d.get("impact") == "IMPORTANT"]
        reference = [d for d in sorted_decisions if d.get("impact") == "REFERENCE"]

        if critical:
            content_lines.append("### P0 - Critical Features\n")
            content_lines.append("*Must have for launch*\n")
            for d in critical[:10]:
                code = d.get("code", "")
                summary = d.get("summary", "")
                content_lines.append(f"- **{code}**: {summary}")
            content_lines.append("")

        if important:
            content_lines.append("### P1 - Important Features\n")
            content_lines.append("*Should have for launch*\n")
            for d in important[:10]:
                code = d.get("code", "")
                summary = d.get("summary", "")
                content_lines.append(f"- **{code}**: {summary}")
            content_lines.append("")

        if reference:
            content_lines.append("### P2 - Nice to Have\n")
            content_lines.append("*Can be deferred*\n")
            for d in reference[:5]:
                code = d.get("code", "")
                summary = d.get("summary", "")
                content_lines.append(f"- **{code}**: {summary}")

        return DocumentSection(
            id="features",
            title="Features",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in sorted_decisions[:20]],
        )

    def _generate_constraints(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate constraints section."""
        content_lines = ["## Constraints\n"]

        must = []
        must_not = []
        should = []

        for d in decisions:
            code = d.get("code", "")
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    rule = c.get("rule", "")
                    ctype = c.get("type", "MUST")

                    entry = f"- **[{code}]** {rule[:100]}"

                    if ctype == "MUST":
                        must.append(entry)
                    elif ctype == "MUST_NOT":
                        must_not.append(entry)
                    elif ctype == "SHOULD":
                        should.append(entry)

        if must:
            content_lines.append("### Required (MUST)")
            content_lines.extend(must[:15])
            content_lines.append("")

        if must_not:
            content_lines.append("### Prohibited (MUST NOT)")
            content_lines.extend(must_not[:10])
            content_lines.append("")

        if should:
            content_lines.append("### Recommended (SHOULD)")
            content_lines.extend(should[:10])

        if not (must or must_not or should):
            content_lines.append("No constraints documented.")

        return DocumentSection(
            id="constraints",
            title="Constraints",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_dependencies(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate dependencies section."""
        content_lines = ["## Dependencies\n"]

        # Extract depends_on relationships
        deps_map: Dict[str, List[str]] = {}
        for d in decisions:
            code = d.get("code", "")
            depends_on = d.get("depends_on", [])
            if depends_on:
                deps_map[code] = depends_on

        if deps_map:
            content_lines.append("### Decision Dependencies\n")
            content_lines.append("| Decision | Depends On |")
            content_lines.append("|----------|------------|")
            for code, deps in list(deps_map.items())[:20]:
                deps_str = ", ".join(deps[:3])
                if len(deps) > 3:
                    deps_str += f" (+{len(deps)-3} more)"
                content_lines.append(f"| {code} | {deps_str} |")
            content_lines.append("")
        else:
            content_lines.append("No explicit dependencies documented.")

        # External dependencies from tags
        content_lines.append("\n### External Dependencies\n")
        external_deps = set()
        for d in decisions:
            tags = d.get("tags", [])
            for tag in tags:
                if tag.lower() in ["react", "python", "postgres", "redis", "aws", "docker"]:
                    external_deps.add(tag)

        if external_deps:
            for dep in sorted(external_deps):
                content_lines.append(f"- {dep}")
        else:
            content_lines.append("- To be determined during implementation")

        return DocumentSection(
            id="dependencies",
            title="Dependencies",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_success_criteria(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate success criteria section."""
        content_lines = [
            "## Success Criteria\n",
            "### Acceptance Metrics\n"
        ]

        # Extract from invariants
        criteria = []
        for d in decisions:
            code = d.get("code", "")
            for inv in d.get("invariants", [])[:2]:
                criteria.append(f"- **[{code}]** {inv[:100]}")

        if criteria:
            content_lines.extend(criteria[:15])
        else:
            content_lines.append("- All CRITICAL decisions implemented")
            content_lines.append("- All MUST constraints satisfied")
            content_lines.append("- No MUST_NOT violations")

        content_lines.append("\n### Definition of Done\n")
        content_lines.append("- [ ] All P0 features implemented and tested")
        content_lines.append("- [ ] Code reviewed and approved")
        content_lines.append("- [ ] Documentation updated")
        content_lines.append("- [ ] Performance benchmarks met")
        content_lines.append("- [ ] Security review passed")

        return DocumentSection(
            id="success-criteria",
            title="Success Criteria",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_appendix(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate appendix."""
        content_lines = [
            "## Appendix\n",
            "### Decision Reference\n"
        ]

        # Quick reference table
        content_lines.append("| Code | Summary | Impact |")
        content_lines.append("|------|---------|--------|")

        for d in decisions[:30]:
            code = d.get("code", "")
            summary = d.get("summary", "")[:40]
            impact = d.get("impact", "IMPORTANT")
            content_lines.append(f"| {code} | {summary} | {impact} |")

        content_lines.append("\n### Glossary\n")
        content_lines.append("- **CRITICAL**: Must have for launch")
        content_lines.append("- **IMPORTANT**: Should have for launch")
        content_lines.append("- **REFERENCE**: Nice to have, can defer")
        content_lines.append("- **MUST**: Absolute requirement")
        content_lines.append("- **MUST_NOT**: Absolute prohibition")
        content_lines.append("- **SHOULD**: Recommendation")

        return DocumentSection(
            id="appendix",
            title="Appendix",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )


__all__ = ["PRDGenerator"]
