"""
MANTRA ADR (Architecture Decision Records) Generator

Generates Architecture Decision Records following standard ADR format.

Features:
- Standard ADR structure per MADR template
- Full rationale preservation
- Relationship tracking (supersedes, depends_on)
- Chronological ordering

ADR STRUCTURE (per decision):
1. Title - Decision identifier and summary
2. Status - Current validity state
3. Context - Why this decision was needed
4. Decision - What was decided
5. Consequences - Impact of this decision
6. Constraints - MUST/MUST_NOT rules
7. Related - Dependencies and supersedes
"""

from typing import List, Dict, Any
from datetime import datetime
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class ADRGenerator(DocumentGenerator):
    """Generates Architecture Decision Records."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.ADR

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate ADR sections."""
        sections = []

        # 1. Index/TOC
        sections.append(self._generate_index(decisions))

        # 2. Individual ADRs
        # Sort by code for consistent ordering
        sorted_decisions = sorted(
            decisions,
            key=lambda d: d.get("code", d.get("decision_code", "ZZZ"))
        )

        for decision in sorted_decisions:
            sections.append(self._generate_adr(decision))

        # 3. Summary Statistics
        sections.append(self._generate_summary(decisions))

        return sections

    def _generate_index(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate ADR index."""
        content_lines = [
            "## Architecture Decision Records Index\n",
            "This document contains all architecture decisions tracked in MANTRA.\n",
            "### Quick Reference\n",
            "| ADR | Title | Status | Domain |",
            "|-----|-------|--------|--------|",
        ]

        # Sort by code
        sorted_decisions = sorted(
            decisions,
            key=lambda d: d.get("code", "")
        )

        for d in sorted_decisions:
            code = d.get("code", d.get("decision_code", ""))
            summary = d.get("summary", "")[:40]
            validity = d.get("validity_state", "CURRENT")
            if hasattr(validity, 'value'):
                validity = validity.value
            domain = d.get("domain_id", "")
            if hasattr(domain, 'value'):
                domain = domain.value

            status_emoji = {
                "CURRENT": "✅",
                "SUPERSEDED": "🔄",
                "EXPIRED": "⚠️",
            }.get(validity, "❓")

            content_lines.append(f"| [{code}](#{code.lower()}) | {summary} | {status_emoji} {validity} | {domain} |")

        content_lines.append("")
        content_lines.append("### Legend")
        content_lines.append("- ✅ CURRENT: Active decision")
        content_lines.append("- 🔄 SUPERSEDED: Replaced by newer decision")
        content_lines.append("- ⚠️ EXPIRED: Past sunset date")

        return DocumentSection(
            id="adr-index",
            title="ADR Index",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_adr(
        self,
        decision: Dict[str, Any]
    ) -> DocumentSection:
        """Generate a single ADR."""
        code = decision.get("code", decision.get("decision_code", ""))
        summary = decision.get("summary", "")
        statement = decision.get("statement", "")
        rationale = decision.get("rationale", "")
        validity = decision.get("validity_state", "CURRENT")
        if hasattr(validity, 'value'):
            validity = validity.value

        domain = decision.get("domain_id", "")
        if hasattr(domain, 'value'):
            domain = domain.value

        aspect = decision.get("aspect_id", "")
        if hasattr(aspect, 'value'):
            aspect = aspect.value

        version = decision.get("version", "1.0.0")
        authored_by = decision.get("authored_by", "Unknown")
        authored_at = decision.get("authored_at")
        if isinstance(authored_at, datetime):
            authored_at = authored_at.strftime("%Y-%m-%d")
        elif not authored_at:
            authored_at = "Unknown"

        content_lines = [
            f"## ADR: {code}\n",
            f"### {summary}\n",
            "---\n",
            "#### Metadata",
            f"- **ID**: {code}",
            f"- **Version**: {version}",
            f"- **Status**: {validity}",
            f"- **Domain**: {domain}",
            f"- **Aspect**: {aspect}",
            f"- **Author**: {authored_by}",
            f"- **Date**: {authored_at}",
            "",
            "---\n",
            "#### Context",
            "*Why was this decision needed?*\n",
        ]

        # Extract context from rationale (first paragraph)
        if rationale:
            context_text = rationale.split("\n\n")[0] if "\n\n" in rationale else rationale[:500]
            content_lines.append(context_text)
        else:
            content_lines.append("Context not documented.")

        content_lines.append("")
        content_lines.append("---\n")
        content_lines.append("#### Decision")
        content_lines.append("*What was decided?*\n")
        content_lines.append(statement if statement else "Decision not documented.")

        # Constraints
        constraints = decision.get("constraints", [])
        if constraints:
            content_lines.append("")
            content_lines.append("---\n")
            content_lines.append("#### Constraints")
            content_lines.append("*Rules that must be followed:*\n")

            for c in constraints:
                if isinstance(c, dict):
                    ctype = c.get("type", "MUST")
                    rule = c.get("rule", "")
                    cid = c.get("id", "")
                    content_lines.append(f"- **{ctype}** [{cid}]: {rule}")
                else:
                    content_lines.append(f"- {c}")

        # Invariants
        invariants = decision.get("invariants", [])
        if invariants:
            content_lines.append("")
            content_lines.append("---\n")
            content_lines.append("#### Invariants")
            content_lines.append("*These must always be true:*\n")

            for inv in invariants:
                content_lines.append(f"- {inv}")

        # Consequences
        content_lines.append("")
        content_lines.append("---\n")
        content_lines.append("#### Consequences")
        content_lines.append("*Impact of this decision:*\n")

        # Extract consequences from rationale (remaining paragraphs)
        if rationale and "\n\n" in rationale:
            consequence_text = "\n\n".join(rationale.split("\n\n")[1:])
            if consequence_text:
                content_lines.append(consequence_text[:500])
            else:
                content_lines.append("See rationale above.")
        else:
            impact = decision.get("impact", "IMPORTANT")
            if hasattr(impact, 'value'):
                impact = impact.value
            content_lines.append(f"- Impact Level: {impact}")
            content_lines.append("- Detailed consequences to be documented")

        # Related decisions
        depends_on = decision.get("depends_on", [])
        supersedes = decision.get("supersedes")

        if depends_on or supersedes:
            content_lines.append("")
            content_lines.append("---\n")
            content_lines.append("#### Related Decisions\n")

            if depends_on:
                content_lines.append("**Depends On:**")
                for dep in depends_on:
                    content_lines.append(f"- {dep}")

            if supersedes:
                content_lines.append(f"\n**Supersedes:** {supersedes}")

        # Examples
        examples = decision.get("examples", [])
        if examples:
            content_lines.append("")
            content_lines.append("---\n")
            content_lines.append("#### Examples\n")
            for ex in examples[:5]:
                content_lines.append(f"- {ex}")

        # Tags
        tags = decision.get("tags", [])
        if tags:
            content_lines.append("")
            content_lines.append(f"**Tags:** {', '.join(tags)}")

        content_lines.append("\n---\n")

        return DocumentSection(
            id=code.lower(),
            title=f"ADR: {code}",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[code],
            metadata={
                "status": validity,
                "domain": domain,
                "version": version,
            }
        )

    def _generate_summary(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate ADR summary statistics."""
        # Count by status
        by_status = {}
        for d in decisions:
            status = d.get("validity_state", "CURRENT")
            if hasattr(status, 'value'):
                status = status.value
            by_status[status] = by_status.get(status, 0) + 1

        # Count by domain
        by_domain = {}
        for d in decisions:
            domain = d.get("domain_id", "OTHER")
            if hasattr(domain, 'value'):
                domain = domain.value
            by_domain[domain] = by_domain.get(domain, 0) + 1

        # Count constraints
        total_constraints = sum(len(d.get("constraints", [])) for d in decisions)
        must_constraints = sum(
            len([c for c in d.get("constraints", [])
                 if isinstance(c, dict) and c.get("type") == "MUST"])
            for d in decisions
        )

        content_lines = [
            "## ADR Summary\n",
            "### Statistics\n",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total ADRs | {len(decisions)} |",
            f"| Active (CURRENT) | {by_status.get('CURRENT', 0)} |",
            f"| Superseded | {by_status.get('SUPERSEDED', 0)} |",
            f"| Total Constraints | {total_constraints} |",
            f"| MUST Constraints | {must_constraints} |",
            "",
            "### By Domain\n",
            "| Domain | Count |",
            "|--------|-------|",
        ]

        for domain, count in sorted(by_domain.items(), key=lambda x: -x[1]):
            content_lines.append(f"| {domain} | {count} |")

        content_lines.append("")
        content_lines.append("### Supersession Chain\n")
        content_lines.append("*Decisions that have been superseded:*\n")

        superseded_chain = []
        for d in decisions:
            supersedes = d.get("supersedes")
            if supersedes:
                code = d.get("code", "")
                superseded_chain.append(f"- {code} supersedes {supersedes}")

        if superseded_chain:
            content_lines.extend(superseded_chain)
        else:
            content_lines.append("No supersessions documented.")

        return DocumentSection(
            id="adr-summary",
            title="ADR Summary",
            content="\n".join(content_lines),
            level=1,
        )


__all__ = ["ADRGenerator"]
