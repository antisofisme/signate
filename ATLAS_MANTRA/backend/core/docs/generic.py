"""
MANTRA Generic Document Generator

Fallback generator for document types without specialized implementation.
Uses document type metadata to generate appropriate content.
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig,
    DOCUMENT_TYPES
)


class GenericGenerator(DocumentGenerator):
    """
    Generic document generator.

    Uses document type metadata to generate appropriate structure.
    """

    def __init__(self, decisions: List[Dict[str, Any]], doc_type: DocumentType):
        super().__init__(decisions)
        self._doc_type = doc_type

    @property
    def doc_type(self) -> DocumentType:
        return self._doc_type

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate generic sections based on document type metadata."""
        meta = self.meta
        sections = []

        # 1. Overview Section
        sections.append(self._generate_overview(decisions, meta, config))

        # 2. Decisions by Category
        sections.append(self._generate_decisions_by_category(decisions, meta))

        # 3. Constraints Section
        if meta.include_constraints:
            sections.append(self._generate_constraints(decisions))

        # 4. Examples Section
        if meta.include_examples:
            examples_section = self._generate_examples(decisions)
            if examples_section.content.strip():
                sections.append(examples_section)

        # 5. References Section
        sections.append(self._generate_references(decisions))

        return sections

    def _generate_overview(
        self,
        decisions: List[Dict[str, Any]],
        meta,
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate overview section."""
        content = f"""## {meta.name}

{meta.description}

**Phase:** {meta.phase}
**Primary Audience:** {meta.primary_audience.value}
**Decisions Covered:** {len(decisions)}

This document is auto-generated from MANTRA decisions filtered by:
- Domains: {', '.join(meta.domains) if meta.domains != ['*'] else 'All'}
- Scopes: {', '.join(meta.scopes) if meta.scopes != ['*'] else 'All'}
- Tags: {', '.join(meta.tags) if meta.tags != ['*'] else 'All'}
"""
        return DocumentSection(
            id="overview",
            title="Overview",
            content=content,
            level=1,
        )

    def _generate_decisions_by_category(
        self,
        decisions: List[Dict[str, Any]],
        meta
    ) -> DocumentSection:
        """Generate decisions grouped by scope or domain."""
        subsections = []

        # Group by scope
        by_scope: Dict[str, List[Dict]] = {}
        for d in decisions:
            scope = d.get("scope_path", "*")
            top = scope.split(".")[0] if scope != "*" else "general"
            if top not in by_scope:
                by_scope[top] = []
            by_scope[top].append(d)

        for scope, scope_decisions in by_scope.items():
            content_lines = []

            for d in scope_decisions:
                code = d.get("code", d.get("decision_id", ""))
                statement = d.get("statement", "")
                summary = d.get("summary", "")

                content_lines.append(f"### {code}")
                content_lines.append(f"**Summary:** {summary or statement[:100]}")

                if meta.include_rationale and d.get("rationale"):
                    content_lines.append(f"\n**Rationale:** {d['rationale'][:200]}...")

                content_lines.append("")

            subsections.append(DocumentSection(
                id=f"section-{scope}",
                title=f"{scope.upper()} Decisions",
                content="\n".join(content_lines),
                level=2,
                decision_ids=[d.get("code", "") for d in scope_decisions],
            ))

        return DocumentSection(
            id="decisions",
            title="Decisions",
            content=f"Grouped decisions ({len(decisions)} total):",
            level=1,
            subsections=subsections,
        )

    def _generate_constraints(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate constraints section."""
        must = []
        must_not = []
        should = []

        for d in decisions:
            code = d.get("code", "")
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    rule = c.get("rule", "")
                    ctype = c.get("type", "MUST")
                    entry = f"- **[{code}]** {rule}"

                    if ctype == "MUST":
                        must.append(entry)
                    elif ctype == "MUST_NOT":
                        must_not.append(entry)
                    else:
                        should.append(entry)

        content_lines = ["## Constraints\n"]

        if must:
            content_lines.append("### Required (MUST)")
            content_lines.extend(must[:20])
            content_lines.append("")

        if must_not:
            content_lines.append("### Prohibited (MUST NOT)")
            content_lines.extend(must_not[:20])
            content_lines.append("")

        if should:
            content_lines.append("### Recommended (SHOULD)")
            content_lines.extend(should[:20])

        if not (must or must_not or should):
            content_lines.append("No constraints documented.")

        return DocumentSection(
            id="constraints",
            title="Constraints",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_examples(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate examples section."""
        content_lines = ["## Examples\n"]

        for d in decisions:
            examples = d.get("examples", [])
            if examples:
                code = d.get("code", "")
                content_lines.append(f"### {code}")
                for ex in examples[:3]:
                    content_lines.append(f"- {ex}")
                content_lines.append("")

        return DocumentSection(
            id="examples",
            title="Examples",
            content="\n".join(content_lines) if len(content_lines) > 1 else "",
            level=1,
        )

    def _generate_references(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate references section."""
        content_lines = [
            "## References\n",
            "### Decision Codes\n"
        ]

        for d in decisions:
            code = d.get("code", d.get("decision_id", ""))
            summary = d.get("summary", "")[:50]
            content_lines.append(f"- `{code}` - {summary}")

        content_lines.append("")
        content_lines.append("### Related Resources")
        content_lines.append("- MANTRA Decision System")
        content_lines.append("- Architecture Documentation")

        return DocumentSection(
            id="references",
            title="References",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )


__all__ = ["GenericGenerator"]
