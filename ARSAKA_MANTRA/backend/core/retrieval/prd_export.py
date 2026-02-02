"""
MANTRA PRD Export Module

Exports decisions as Product Requirements Documents (PRD).

FEATURES:
1. Hierarchical markdown output (Domain → Aspect → Decisions)
2. Dependency tree rendering
3. Conflict/supersedes annotations
4. Table of contents generation
5. Filtering by domain/aspect/tags

OUTPUT FORMATS:
- Markdown (default)
- JSON (structured)
- HTML (styled)

Per MANTRA-LAW-001: Decisions ARE the PRD - this just formats them.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json


class ExportFormat(str, Enum):
    """Supported export formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class SectionStyle(str, Enum):
    """PRD section styling options."""
    HIERARCHICAL = "hierarchical"  # Domain → Aspect → Decision
    FLAT = "flat"                  # Just decisions
    PRIORITY = "priority"          # Sorted by priority_rank


@dataclass
class ExportConfig:
    """Configuration for PRD export."""
    format: ExportFormat = ExportFormat.MARKDOWN
    style: SectionStyle = SectionStyle.HIERARCHICAL
    include_toc: bool = True
    include_metadata: bool = True
    include_dependencies: bool = True
    include_conflicts: bool = True
    include_examples: bool = True
    max_constraint_count: int = 10
    max_example_count: int = 5
    # Filters
    domains: Optional[List[str]] = None
    aspects: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    min_priority: Optional[int] = None


@dataclass
class PRDSection:
    """A section in the PRD."""
    title: str
    level: int  # 1 = h1, 2 = h2, etc.
    content: str
    anchor: str  # For TOC links


@dataclass
class PRDDocument:
    """Complete PRD document."""
    title: str
    generated_at: datetime
    sections: List[PRDSection]
    toc: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    decision_count: int
    word_count: int

    def to_markdown(self) -> str:
        """Render as markdown."""
        lines = []

        # Title
        lines.append(f"# {self.title}")
        lines.append("")

        # Metadata
        lines.append(f"*Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}*")
        lines.append(f"*Decisions: {self.decision_count}*")
        lines.append("")

        # TOC
        if self.toc:
            lines.append("## Table of Contents")
            lines.append("")
            for item in self.toc:
                indent = "  " * (item["level"] - 1)
                lines.append(f"{indent}- [{item['title']}](#{item['anchor']})")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Sections
        for section in self.sections:
            prefix = "#" * section.level
            lines.append(f"{prefix} {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Render as JSON."""
        return json.dumps({
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
            "decision_count": self.decision_count,
            "word_count": self.word_count,
            "toc": self.toc,
            "sections": [
                {
                    "title": s.title,
                    "level": s.level,
                    "content": s.content,
                    "anchor": s.anchor,
                }
                for s in self.sections
            ],
        }, indent=2)

    def to_html(self) -> str:
        """Render as HTML."""
        # Simple HTML conversion
        md = self.to_markdown()

        # Basic markdown to HTML
        html_lines = ["<!DOCTYPE html>", "<html>", "<head>",
                      f"<title>{self.title}</title>",
                      "<style>",
                      "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; }",
                      "h1 { border-bottom: 2px solid #333; }",
                      "h2 { border-bottom: 1px solid #ccc; margin-top: 2rem; }",
                      "h3 { color: #2563eb; }",
                      "code { background: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 3px; }",
                      "pre { background: #f3f4f6; padding: 1rem; border-radius: 5px; overflow-x: auto; }",
                      ".constraint { margin: 0.5rem 0; padding-left: 1.5rem; }",
                      ".must { border-left: 3px solid #dc2626; }",
                      ".should { border-left: 3px solid #f59e0b; }",
                      ".may { border-left: 3px solid #10b981; }",
                      "</style>",
                      "</head>", "<body>"]

        # Convert markdown sections to HTML
        for section in self.sections:
            tag = f"h{section.level}"
            html_lines.append(f"<{tag} id=\"{section.anchor}\">{section.title}</{tag}>")

            # Convert content (basic)
            content_html = section.content
            # Convert bold
            import re
            content_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content_html)
            # Convert lists
            content_html = re.sub(r'^- (.+)$', r'<li>\1</li>', content_html, flags=re.MULTILINE)
            # Convert paragraphs
            paragraphs = content_html.split('\n\n')
            content_html = ''.join(f'<p>{p}</p>' if not p.startswith('<li>') else f'<ul>{p}</ul>' for p in paragraphs if p.strip())

            html_lines.append(f"<div class=\"section-content\">{content_html}</div>")

        html_lines.extend(["</body>", "</html>"])
        return "\n".join(html_lines)


class PRDExporter:
    """
    Exports decisions as PRD documents.

    Usage:
        exporter = PRDExporter()
        doc = exporter.export(
            decisions=decisions_list,
            config=ExportConfig(format=ExportFormat.MARKDOWN)
        )
        markdown = doc.to_markdown()
    """

    DOMAIN_NAMES = {
        "INT": "Intent & Direction",
        "ARCH": "Architecture & Boundaries",
        "CTL": "Control & Policy",
        "EVO": "Execution & Evolution",
    }

    ASPECT_NAMES = {
        "A01": "Core Purpose",
        "A02": "Guiding Principles",
        "A03": "Key Capabilities",
        "A04": "Strategic Constraints",
        "A05": "System Boundaries",
        "A06": "Component Structure",
        "A07": "Integration Points",
        "A08": "Technology Choices",
        "A09": "Security Policies",
        "A10": "Quality Standards",
        "A11": "Operational Limits",
        "A12": "Compliance Requirements",
        "A13": "Delivery Process",
        "A14": "Monitoring & Feedback",
        "A15": "Change Management",
        "A16": "Scaling Strategy",
    }

    def __init__(self):
        self._dependency_graph: Dict[str, List[str]] = {}

    def export(
        self,
        decisions: List[Dict[str, Any]],
        config: Optional[ExportConfig] = None,
        title: str = "Product Requirements Document",
    ) -> PRDDocument:
        """
        Export decisions as PRD document.

        Args:
            decisions: List of decision dictionaries
            config: Export configuration
            title: Document title

        Returns:
            PRDDocument ready for rendering
        """
        config = config or ExportConfig()

        # Filter decisions
        filtered = self._filter_decisions(decisions, config)

        # Sort decisions
        filtered = self._sort_decisions(filtered, config.style)

        # Build dependency graph
        self._dependency_graph = {
            d.get("decision_id", ""): d.get("depends_on", [])
            for d in filtered
        }

        # Generate sections based on style
        if config.style == SectionStyle.HIERARCHICAL:
            sections = self._generate_hierarchical(filtered, config)
        elif config.style == SectionStyle.PRIORITY:
            sections = self._generate_priority(filtered, config)
        else:
            sections = self._generate_flat(filtered, config)

        # Generate TOC
        toc = []
        if config.include_toc:
            toc = [
                {"title": s.title, "level": s.level, "anchor": s.anchor}
                for s in sections
                if s.level <= 3  # Only include up to h3 in TOC
            ]

        # Calculate stats
        all_content = " ".join(s.content for s in sections)
        word_count = len(all_content.split())

        # Metadata
        metadata = {
            "total_decisions": len(filtered),
            "domains": list(set(d.get("domain_id", "") for d in filtered)),
            "config": {
                "style": config.style.value,
                "include_dependencies": config.include_dependencies,
                "include_examples": config.include_examples,
            },
        }

        return PRDDocument(
            title=title,
            generated_at=datetime.now(timezone.utc),
            sections=sections,
            toc=toc,
            metadata=metadata,
            decision_count=len(filtered),
            word_count=word_count,
        )

    def _filter_decisions(
        self,
        decisions: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> List[Dict[str, Any]]:
        """Filter decisions based on config."""
        result = decisions

        # Filter by domains
        if config.domains:
            result = [d for d in result if d.get("domain_id") in config.domains]

        # Filter by aspects
        if config.aspects:
            result = [d for d in result if d.get("aspect_id") in config.aspects]

        # Filter by tags
        if config.tags:
            result = [
                d for d in result
                if any(t in d.get("tags", []) for t in config.tags)
            ]

        # Filter by priority
        if config.min_priority is not None:
            result = [
                d for d in result
                if d.get("priority_rank", 100) <= config.min_priority
            ]

        return result

    def _sort_decisions(
        self,
        decisions: List[Dict[str, Any]],
        style: SectionStyle,
    ) -> List[Dict[str, Any]]:
        """Sort decisions based on style."""
        if style == SectionStyle.PRIORITY:
            return sorted(decisions, key=lambda d: d.get("priority_rank", 100))
        elif style == SectionStyle.HIERARCHICAL:
            return sorted(decisions, key=lambda d: (
                d.get("domain_id", "ZZZ"),
                d.get("aspect_id", "ZZZ"),
                d.get("priority_rank", 100),
            ))
        return decisions

    def _generate_hierarchical(
        self,
        decisions: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> List[PRDSection]:
        """Generate hierarchical sections (Domain → Aspect → Decision)."""
        sections = []

        # Group by domain
        by_domain: Dict[str, List[Dict[str, Any]]] = {}
        for d in decisions:
            domain = d.get("domain_id", "OTHER")
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(d)

        # Process each domain
        for domain_id in ["INT", "ARCH", "CTL", "EVO", "OTHER"]:
            if domain_id not in by_domain:
                continue

            domain_name = self.DOMAIN_NAMES.get(domain_id, domain_id)
            domain_decisions = by_domain[domain_id]

            # Domain section
            sections.append(PRDSection(
                title=f"{domain_id}: {domain_name}",
                level=2,
                content=self._domain_intro(domain_id, domain_decisions),
                anchor=f"domain-{domain_id.lower()}",
            ))

            # Group by aspect within domain
            by_aspect: Dict[str, List[Dict[str, Any]]] = {}
            for d in domain_decisions:
                aspect = d.get("aspect_id", "OTHER")
                if aspect not in by_aspect:
                    by_aspect[aspect] = []
                by_aspect[aspect].append(d)

            # Process each aspect
            for aspect_id in sorted(by_aspect.keys()):
                aspect_name = self.ASPECT_NAMES.get(aspect_id, aspect_id)
                aspect_decisions = by_aspect[aspect_id]

                # Aspect section
                sections.append(PRDSection(
                    title=f"{aspect_id}: {aspect_name}",
                    level=3,
                    content="",
                    anchor=f"aspect-{aspect_id.lower()}",
                ))

                # Decision sections
                for decision in aspect_decisions:
                    sections.append(self._decision_section(decision, config, level=4))

        return sections

    def _generate_priority(
        self,
        decisions: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> List[PRDSection]:
        """Generate sections sorted by priority."""
        sections = []

        # Priority bands
        critical = [d for d in decisions if d.get("priority_rank", 100) <= 25]
        high = [d for d in decisions if 25 < d.get("priority_rank", 100) <= 50]
        medium = [d for d in decisions if 50 < d.get("priority_rank", 100) <= 75]
        low = [d for d in decisions if d.get("priority_rank", 100) > 75]

        bands = [
            ("Critical Priority (1-25)", critical),
            ("High Priority (26-50)", high),
            ("Medium Priority (51-75)", medium),
            ("Low Priority (76-100)", low),
        ]

        for band_name, band_decisions in bands:
            if not band_decisions:
                continue

            sections.append(PRDSection(
                title=band_name,
                level=2,
                content=f"*{len(band_decisions)} decision(s)*",
                anchor=f"priority-{band_name.split()[0].lower()}",
            ))

            for decision in band_decisions:
                sections.append(self._decision_section(decision, config, level=3))

        return sections

    def _generate_flat(
        self,
        decisions: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> List[PRDSection]:
        """Generate flat list of decisions."""
        sections = []

        sections.append(PRDSection(
            title="Decisions",
            level=2,
            content=f"*{len(decisions)} decision(s)*",
            anchor="decisions",
        ))

        for decision in decisions:
            sections.append(self._decision_section(decision, config, level=3))

        return sections

    def _domain_intro(
        self,
        domain_id: str,
        decisions: List[Dict[str, Any]],
    ) -> str:
        """Generate domain introduction."""
        intros = {
            "INT": "Decisions about core purpose, guiding principles, and strategic direction.",
            "ARCH": "Decisions about system boundaries, component structure, and technology choices.",
            "CTL": "Decisions about security, quality, operational limits, and compliance.",
            "EVO": "Decisions about delivery process, monitoring, change management, and scaling.",
        }

        intro = intros.get(domain_id, "")
        return f"{intro}\n\n*{len(decisions)} decision(s) in this domain*"

    def _decision_section(
        self,
        decision: Dict[str, Any],
        config: ExportConfig,
        level: int = 3,
    ) -> PRDSection:
        """Generate a section for a single decision."""
        code = decision.get("code", "UNKNOWN")
        summary = decision.get("summary", "")

        lines = []

        # Statement
        statement = decision.get("statement", "")
        if statement:
            lines.append(f"**Statement**: {statement}")
            lines.append("")

        # Priority
        priority = decision.get("priority_rank", 50)
        impact = decision.get("impact", "IMPORTANT")
        lines.append(f"**Priority**: {priority}/100 | **Impact**: {impact}")
        lines.append("")

        # Rationale
        rationale = decision.get("rationale", "")
        if rationale:
            lines.append(f"**Rationale**: {rationale}")
            lines.append("")

        # Constraints
        constraints = decision.get("constraints", [])[:config.max_constraint_count]
        if constraints:
            lines.append("**Constraints**:")
            for c in constraints:
                if isinstance(c, dict):
                    ctype = c.get("type", "MUST")
                    rule = c.get("rule", "")
                    automated = " *(automated)*" if c.get("is_automated") else ""
                    lines.append(f"- **{ctype}**: {rule}{automated}")
                else:
                    lines.append(f"- {c}")
            lines.append("")

        # Invariants
        invariants = decision.get("invariants", [])
        if invariants:
            lines.append("**Invariants**:")
            for inv in invariants:
                lines.append(f"- {inv}")
            lines.append("")

        # Dependencies
        if config.include_dependencies:
            depends_on = decision.get("depends_on", [])
            if depends_on:
                lines.append(f"**Depends On**: {', '.join(depends_on)}")
                lines.append("")

            supersedes = decision.get("supersedes")
            if supersedes:
                lines.append(f"**Supersedes**: {supersedes}")
                lines.append("")

        # Examples
        if config.include_examples:
            examples = decision.get("examples", [])[:config.max_example_count]
            if examples:
                lines.append("**Examples**:")
                for ex in examples:
                    lines.append(f"- {ex}")
                lines.append("")

        # Tags
        tags = decision.get("tags", [])
        if tags:
            lines.append(f"**Tags**: {', '.join(tags)}")
            lines.append("")

        # Applies to
        applies_to = decision.get("applies_to", [])
        if applies_to:
            lines.append(f"**Applies To**: `{', '.join(applies_to[:5])}`")

        return PRDSection(
            title=f"{code}: {summary}",
            level=level,
            content="\n".join(lines),
            anchor=f"decision-{code.lower().replace('-', '')}",
        )

    def export_markdown(
        self,
        decisions: List[Dict[str, Any]],
        **kwargs,
    ) -> str:
        """Convenience: Export directly to markdown string."""
        doc = self.export(decisions, **kwargs)
        return doc.to_markdown()

    def export_json(
        self,
        decisions: List[Dict[str, Any]],
        **kwargs,
    ) -> str:
        """Convenience: Export directly to JSON string."""
        doc = self.export(decisions, **kwargs)
        return doc.to_json()


# ============================================================================
# INTENT INTEGRATION
# ============================================================================

# PRD_EXPORT fields - all content + relationships
PRD_EXPORT_FIELDS = [
    "code", "version", "domain_id", "aspect_id",
    "statement", "summary", "rationale",
    "constraints", "invariants",
    "examples", "tags", "applies_to",
    "depends_on", "supersedes", "priority_rank",
    "impact", "authored_by", "authored_at",
]

PRD_EXPORT_TOKEN_ESTIMATE = 600  # Per decision


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ExportFormat",
    "SectionStyle",
    "ExportConfig",
    "PRDSection",
    "PRDDocument",
    "PRDExporter",
    "PRD_EXPORT_FIELDS",
    "PRD_EXPORT_TOKEN_ESTIMATE",
]
