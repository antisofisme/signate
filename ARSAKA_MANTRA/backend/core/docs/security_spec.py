"""
MANTRA Security Specification Generator

Generates security specification and threat model documents.

OUTPUT STRUCTURE:
1. Security Overview - Scope, objectives
2. Authentication & Authorization - Access control
3. Data Protection - Encryption, privacy
4. Threat Mitigations - Security controls
5. Compliance Requirements - Standards, regulations
6. Security Constraints - MUST/MUST_NOT rules
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class SecuritySpecGenerator(DocumentGenerator):
    """Generates Security Specification documents."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.SECURITY_SPEC

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate security spec sections from decisions."""
        sections = []

        # 1. Security Overview
        sections.append(self._generate_overview(decisions, config))

        # 2. Authentication & Authorization
        auth_decisions = [d for d in decisions if self._is_auth_related(d)]
        if auth_decisions:
            sections.append(self._generate_auth_section(auth_decisions))

        # 3. Data Protection
        data_decisions = [d for d in decisions if self._is_data_protection(d)]
        if data_decisions:
            sections.append(self._generate_data_protection(data_decisions))

        # 4. Threat Mitigations
        sections.append(self._generate_threat_mitigations(decisions))

        # 5. Security Constraints (MUST/MUST_NOT)
        sections.append(self._generate_security_constraints(decisions))

        # 6. Compliance
        compliance_decisions = [d for d in decisions if self._is_compliance(d)]
        if compliance_decisions:
            sections.append(self._generate_compliance(compliance_decisions))

        return sections

    def _generate_overview(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate security overview."""
        # Count by category
        auth_count = len([d for d in decisions if self._is_auth_related(d)])
        data_count = len([d for d in decisions if self._is_data_protection(d)])

        content = f"""## Security Specification Overview

This document outlines the security requirements and controls for the system.

**Security Decisions Analyzed:** {len(decisions)}
- Authentication & Authorization: {auth_count}
- Data Protection: {data_count}

**Security Objectives:**
- Protect user data and privacy
- Prevent unauthorized access
- Ensure system integrity
- Maintain audit trail
"""
        return DocumentSection(
            id="overview",
            title="Security Overview",
            content=content,
            level=1,
        )

    def _generate_auth_section(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate authentication & authorization section."""
        content_lines = [
            "## Authentication & Authorization\n"
        ]

        for d in decisions:
            code = d.get("code", "")
            statement = d.get("statement", "")
            content_lines.append(f"### {code}")
            content_lines.append(statement)
            content_lines.append("")

            rationale = d.get("rationale", "")
            if rationale:
                content_lines.append(f"**Rationale:** {rationale[:200]}...")
                content_lines.append("")

            # Constraints
            constraints = d.get("constraints", [])
            if constraints:
                content_lines.append("**Security Controls:**")
                for c in constraints:
                    if isinstance(c, dict):
                        content_lines.append(f"- {c.get('type', 'MUST')}: {c.get('rule', '')}")
                content_lines.append("")

        return DocumentSection(
            id="authentication",
            title="Authentication & Authorization",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _generate_data_protection(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate data protection section."""
        content_lines = [
            "## Data Protection\n",
            "Controls for protecting data at rest and in transit:\n"
        ]

        for d in decisions:
            code = d.get("code", "")
            statement = d.get("statement", "")
            content_lines.append(f"### {code}")
            content_lines.append(statement)
            content_lines.append("")

            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    content_lines.append(f"- {c.get('type')}: {c.get('rule', '')}")
            content_lines.append("")

        return DocumentSection(
            id="data-protection",
            title="Data Protection",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _generate_threat_mitigations(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate threat mitigations section."""
        # Extract MUST_NOT constraints as threats to prevent
        threats = []
        mitigations = []

        for d in decisions:
            code = d.get("code", "")
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    rule = c.get("rule", "")
                    ctype = c.get("type", "")
                    if ctype == "MUST_NOT":
                        threats.append(f"- **[{code}]** {rule}")
                    elif ctype == "MUST" and self._is_security_control(rule):
                        mitigations.append(f"- **[{code}]** {rule}")

        content_lines = [
            "## Threat Mitigations\n",
            "### Prohibited Actions (Threats Prevented)\n"
        ]
        content_lines.extend(threats[:15] if threats else ["- No explicit prohibitions documented"])
        content_lines.append("")
        content_lines.append("### Required Security Controls\n")
        content_lines.extend(mitigations[:15] if mitigations else ["- No explicit controls documented"])

        return DocumentSection(
            id="threats",
            title="Threat Mitigations",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_security_constraints(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate all security constraints."""
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
                    elif ctype == "SHOULD":
                        should.append(entry)

        content_lines = ["## Security Constraints\n"]

        if must:
            content_lines.append("### MUST (Required)")
            content_lines.extend(must)
            content_lines.append("")

        if must_not:
            content_lines.append("### MUST NOT (Prohibited)")
            content_lines.extend(must_not)
            content_lines.append("")

        if should:
            content_lines.append("### SHOULD (Recommended)")
            content_lines.extend(should)

        return DocumentSection(
            id="constraints",
            title="Security Constraints",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_compliance(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate compliance section."""
        content_lines = [
            "## Compliance Requirements\n",
            "Regulatory and standards compliance:\n"
        ]

        for d in decisions:
            code = d.get("code", "")
            statement = d.get("statement", "")
            tags = d.get("tags", [])
            content_lines.append(f"### {code}")
            content_lines.append(statement)
            if tags:
                content_lines.append(f"*Tags: {', '.join(tags)}*")
            content_lines.append("")

        return DocumentSection(
            id="compliance",
            title="Compliance Requirements",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _is_auth_related(self, decision: Dict[str, Any]) -> bool:
        tags = set(t.lower() for t in decision.get("tags", []))
        auth_tags = {"auth", "authentication", "authorization", "access", "permission", "rbac"}
        return bool(tags & auth_tags)

    def _is_data_protection(self, decision: Dict[str, Any]) -> bool:
        tags = set(t.lower() for t in decision.get("tags", []))
        data_tags = {"encryption", "privacy", "data", "pii", "sensitive", "protection"}
        return bool(tags & data_tags)

    def _is_compliance(self, decision: Dict[str, Any]) -> bool:
        tags = set(t.lower() for t in decision.get("tags", []))
        compliance_tags = {"compliance", "gdpr", "hipaa", "pci", "sox", "iso", "regulation"}
        return bool(tags & compliance_tags)

    def _is_security_control(self, rule: str) -> bool:
        keywords = ["encrypt", "validate", "sanitize", "authenticate", "authorize",
                   "log", "audit", "hash", "secure", "protect"]
        rule_lower = rule.lower()
        return any(kw in rule_lower for kw in keywords)


__all__ = ["SecuritySpecGenerator"]
