"""
MANTRA Technical Specification Generator

Generates technical specification documents from ARCH domain decisions.

OUTPUT STRUCTURE:
1. Overview - Project/feature summary
2. Architecture - System design, components
3. Technical Decisions - ADRs, patterns chosen
4. Constraints - Technical limitations, requirements
5. Dependencies - External dependencies, integrations
6. Implementation Notes - Developer guidance
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class TechSpecGenerator(DocumentGenerator):
    """Generates Technical Specification documents."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.TECH_SPEC

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate tech spec sections from decisions."""
        sections = []

        # 1. Overview Section
        overview = self._generate_overview(decisions, config)
        if overview:
            sections.append(overview)

        # 2. Architecture Section
        arch_decisions = [d for d in decisions if self._is_architecture(d)]
        if arch_decisions:
            sections.append(self._generate_architecture(arch_decisions))

        # 3. Patterns & Practices Section
        pattern_decisions = [d for d in decisions if self._is_pattern(d)]
        if pattern_decisions:
            sections.append(self._generate_patterns(pattern_decisions))

        # 4. Technical Constraints Section
        sections.append(self._generate_constraints(decisions))

        # 5. Dependencies Section
        dep_decisions = [d for d in decisions if self._has_dependencies(d)]
        if dep_decisions:
            sections.append(self._generate_dependencies(dep_decisions))

        # 6. Implementation Notes Section
        sections.append(self._generate_implementation_notes(decisions))

        return sections

    def _generate_overview(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate overview section."""
        # Collect summaries from high-impact decisions
        summaries = []
        for d in decisions[:5]:  # Top 5 decisions
            summary = d.get("summary", d.get("statement", "")[:100])
            if summary:
                summaries.append(f"- {summary}")

        content = f"""This technical specification document describes the architecture and
technical decisions for the system.

**Key Technical Decisions:**
{chr(10).join(summaries) if summaries else "- No decisions documented yet"}

**Scope:** {config.scope_filter or "All technical components"}
**Total Decisions:** {len(decisions)}
"""
        return DocumentSection(
            id="overview",
            title="Overview",
            content=content,
            level=1,
            decision_ids=[d.get("code", d.get("decision_id", "")) for d in decisions[:5]],
        )

    def _generate_architecture(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate architecture section."""
        subsections = []

        # Group by scope
        by_scope: Dict[str, List[Dict]] = {}
        for d in decisions:
            scope = d.get("scope_path", "general")
            # Get top-level scope
            top_scope = scope.split(".")[0] if scope != "*" else "general"
            if top_scope not in by_scope:
                by_scope[top_scope] = []
            by_scope[top_scope].append(d)

        for scope, scope_decisions in by_scope.items():
            scope_content = []
            for d in scope_decisions:
                statement = d.get("statement", "")
                code = d.get("code", d.get("decision_id", ""))
                scope_content.append(f"**[{code}]** {statement[:200]}")

                # Add rationale if available
                rationale = d.get("rationale", "")
                if rationale:
                    scope_content.append(f"> *Rationale:* {rationale[:150]}...")
                scope_content.append("")

            subsections.append(DocumentSection(
                id=f"arch-{scope}",
                title=f"{scope.upper()} Architecture",
                content="\n".join(scope_content),
                level=2,
                decision_ids=[d.get("code", "") for d in scope_decisions],
            ))

        return DocumentSection(
            id="architecture",
            title="Architecture",
            content="This section describes the system architecture and component design.",
            level=1,
            subsections=subsections,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _generate_patterns(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate patterns and practices section."""
        content_lines = [
            "The following design patterns and practices are mandated:\n"
        ]

        for d in decisions:
            code = d.get("code", "")
            statement = d.get("statement", "")
            content_lines.append(f"### {code}")
            content_lines.append(f"{statement}")
            content_lines.append("")

            # Add examples if available
            examples = d.get("examples", [])
            if examples:
                content_lines.append("**Examples:**")
                for ex in examples[:3]:
                    content_lines.append(f"- {ex}")
                content_lines.append("")

        return DocumentSection(
            id="patterns",
            title="Patterns & Practices",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _generate_constraints(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate technical constraints section."""
        must_rules = []
        must_not_rules = []
        should_rules = []

        for d in decisions:
            code = d.get("code", "")
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    rule = c.get("rule", "")
                    ctype = c.get("type", "MUST")
                else:
                    rule = str(c)
                    ctype = "MUST"

                entry = f"- **[{code}]** {rule}"
                if ctype == "MUST":
                    must_rules.append(entry)
                elif ctype == "MUST_NOT":
                    must_not_rules.append(entry)
                elif ctype == "SHOULD":
                    should_rules.append(entry)

        content_lines = []

        if must_rules:
            content_lines.append("### MUST (Required)")
            content_lines.extend(must_rules)
            content_lines.append("")

        if must_not_rules:
            content_lines.append("### MUST NOT (Prohibited)")
            content_lines.extend(must_not_rules)
            content_lines.append("")

        if should_rules:
            content_lines.append("### SHOULD (Recommended)")
            content_lines.extend(should_rules)
            content_lines.append("")

        if not content_lines:
            content_lines.append("No explicit constraints defined.")

        return DocumentSection(
            id="constraints",
            title="Technical Constraints",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions if d.get("constraints")],
        )

    def _generate_dependencies(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate dependencies section."""
        content_lines = ["External dependencies and integrations:\n"]

        for d in decisions:
            deps = d.get("depends_on", [])
            if deps:
                code = d.get("code", "")
                content_lines.append(f"**{code}** depends on:")
                for dep in deps:
                    content_lines.append(f"  - {dep}")
                content_lines.append("")

        return DocumentSection(
            id="dependencies",
            title="Dependencies",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _generate_implementation_notes(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate implementation notes section."""
        content_lines = [
            "Implementation guidance for developers:\n"
        ]

        # Group by scope for relevant implementation context
        by_scope: Dict[str, List[str]] = {}
        for d in decisions:
            scope = d.get("scope_path", "*")
            top = scope.split(".")[0] if scope != "*" else "general"
            if top not in by_scope:
                by_scope[top] = []

            # Extract implementation hints from tags and applies_to
            applies = d.get("applies_to", [])
            if applies:
                by_scope[top].append(f"- Applies to: {', '.join(applies[:5])}")

        for scope, notes in by_scope.items():
            if notes:
                content_lines.append(f"### {scope.upper()}")
                content_lines.extend(notes[:10])
                content_lines.append("")

        return DocumentSection(
            id="implementation",
            title="Implementation Notes",
            content="\n".join(content_lines),
            level=1,
        )

    def _is_architecture(self, decision: Dict[str, Any]) -> bool:
        """Check if decision is architecture-related."""
        tags = set(t.lower() for t in decision.get("tags", []))
        arch_tags = {"architecture", "design", "structure", "component", "system"}
        return bool(tags & arch_tags) or decision.get("domain_id") == "ARCH"

    def _is_pattern(self, decision: Dict[str, Any]) -> bool:
        """Check if decision is about patterns/practices."""
        tags = set(t.lower() for t in decision.get("tags", []))
        pattern_tags = {"pattern", "practice", "convention", "standard"}
        return bool(tags & pattern_tags)

    def _has_dependencies(self, decision: Dict[str, Any]) -> bool:
        """Check if decision has dependencies."""
        return bool(decision.get("depends_on"))


__all__ = ["TechSpecGenerator"]
