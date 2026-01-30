"""
MANTRA Executive Summary Generator

Generates high-level summaries for executives and stakeholders.

Features:
- Concise, no technical jargon
- Focus on impact and business value
- Key metrics and statistics
- Risk highlights

OUTPUT STRUCTURE:
1. Executive Overview - One paragraph summary
2. Key Decisions - Most important decisions
3. Impact Summary - What this means for business
4. Risks & Considerations - Key concerns
5. Recommendations - Next steps
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class ExecSummaryGenerator(DocumentGenerator):
    """Generates Executive Summary documents."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.EXEC_SUMMARY

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate executive summary sections."""
        sections = []

        # 1. Executive Overview (one paragraph)
        sections.append(self._generate_overview(decisions, config))

        # 2. Key Decisions (top 5-10)
        sections.append(self._generate_key_decisions(decisions))

        # 3. Impact Summary
        sections.append(self._generate_impact(decisions))

        # 4. Risks & Considerations
        sections.append(self._generate_risks(decisions))

        # 5. Statistics Dashboard
        sections.append(self._generate_statistics(decisions))

        return sections

    def _generate_overview(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate one-paragraph executive overview."""
        # Count by domain
        domain_counts = {}
        for d in decisions:
            domain = d.get("domain_id", "Other")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Count critical
        critical = len([d for d in decisions if d.get("impact") == "CRITICAL"])

        content = f"""## Executive Overview

This summary covers **{len(decisions)} architectural decisions** that define how the system is built and operates.

**{critical} critical decisions** require immediate attention and compliance. The decisions span across {len(domain_counts)} domains including {', '.join(domain_counts.keys())}.

These decisions ensure consistency, security, and quality across the organization's technology infrastructure.
"""
        return DocumentSection(
            id="overview",
            title="Executive Overview",
            content=content,
            level=1,
        )

    def _generate_key_decisions(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate key decisions section."""
        # Sort by impact (CRITICAL first)
        sorted_decisions = sorted(
            decisions,
            key=lambda d: {"CRITICAL": 0, "IMPORTANT": 1, "REFERENCE": 2}.get(
                d.get("impact", "REFERENCE"), 2
            )
        )

        content_lines = [
            "## Key Decisions\n",
            "The most important decisions affecting the organization:\n"
        ]

        for d in sorted_decisions[:7]:  # Top 7
            code = d.get("code", "")
            summary = d.get("summary", d.get("statement", "")[:80])
            impact = d.get("impact", "IMPORTANT")

            impact_emoji = {"CRITICAL": "🔴", "IMPORTANT": "🟡", "REFERENCE": "🟢"}.get(impact, "⚪")

            content_lines.append(f"### {impact_emoji} {code}")
            content_lines.append(f"{summary}")
            content_lines.append("")

        return DocumentSection(
            id="key-decisions",
            title="Key Decisions",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in sorted_decisions[:7]],
        )

    def _generate_impact(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate business impact section."""
        # Categorize impacts
        security_impact = []
        efficiency_impact = []
        quality_impact = []

        for d in decisions:
            tags = set(t.lower() for t in d.get("tags", []))
            summary = d.get("summary", "")

            if tags & {"security", "auth", "compliance"}:
                security_impact.append(summary)
            elif tags & {"performance", "optimization", "efficiency"}:
                efficiency_impact.append(summary)
            else:
                quality_impact.append(summary)

        content_lines = ["## Business Impact\n"]

        if security_impact:
            content_lines.append("### Security & Compliance")
            content_lines.append(f"- {len(security_impact)} decisions protect the organization from security risks")
            content_lines.append("")

        if efficiency_impact:
            content_lines.append("### Efficiency & Performance")
            content_lines.append(f"- {len(efficiency_impact)} decisions improve system performance and efficiency")
            content_lines.append("")

        content_lines.append("### Quality & Consistency")
        content_lines.append(f"- {len(quality_impact)} decisions ensure consistent quality across teams")

        return DocumentSection(
            id="impact",
            title="Business Impact",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_risks(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate risks and considerations section."""
        content_lines = [
            "## Risks & Considerations\n"
        ]

        # Extract MUST_NOT constraints as risks
        risks = []
        for d in decisions:
            code = d.get("code", "")
            for c in d.get("constraints", []):
                if isinstance(c, dict) and c.get("type") == "MUST_NOT":
                    rule = c.get("rule", "")
                    risks.append(f"- **[{code}]** Violation risk: {rule[:60]}...")

        if risks:
            content_lines.append("### Compliance Risks")
            content_lines.append("Violating these rules could impact the organization:\n")
            content_lines.extend(risks[:5])
        else:
            content_lines.append("### No Critical Risks Identified")
            content_lines.append("All major risks are addressed by current decisions.")

        content_lines.append("")
        content_lines.append("### Recommendations")
        content_lines.append("- Review critical decisions quarterly")
        content_lines.append("- Ensure team awareness of key constraints")
        content_lines.append("- Monitor compliance through automated checks")

        return DocumentSection(
            id="risks",
            title="Risks & Considerations",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_statistics(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate statistics dashboard."""
        # Count by various dimensions
        by_domain = {}
        by_impact = {"CRITICAL": 0, "IMPORTANT": 0, "REFERENCE": 0}
        by_scope = {}
        total_constraints = 0

        for d in decisions:
            # Domain
            domain = d.get("domain_id", "OTHER")
            by_domain[domain] = by_domain.get(domain, 0) + 1

            # Impact
            impact = d.get("impact", "REFERENCE")
            by_impact[impact] = by_impact.get(impact, 0) + 1

            # Scope (top level)
            scope = d.get("scope_path", "*")
            top_scope = scope.split(".")[0] if scope != "*" else "Global"
            by_scope[top_scope] = by_scope.get(top_scope, 0) + 1

            # Constraints
            total_constraints += len(d.get("constraints", []))

        content_lines = [
            "## Decision Statistics\n",
            "### Overview",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total Decisions | {len(decisions)} |",
            f"| Total Constraints | {total_constraints} |",
            f"| Critical Decisions | {by_impact['CRITICAL']} |",
            f"| Important Decisions | {by_impact['IMPORTANT']} |",
            "",
            "### By Domain",
        ]

        for domain, count in sorted(by_domain.items(), key=lambda x: -x[1]):
            content_lines.append(f"- **{domain}**: {count}")

        content_lines.append("")
        content_lines.append("### By Scope")

        for scope, count in sorted(by_scope.items(), key=lambda x: -x[1])[:5]:
            content_lines.append(f"- **{scope}**: {count}")

        return DocumentSection(
            id="statistics",
            title="Statistics",
            content="\n".join(content_lines),
            level=1,
        )


__all__ = ["ExecSummaryGenerator"]
