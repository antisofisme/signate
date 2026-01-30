"""
MANTRA API Specification Generator

Generates API specification documents from API-related decisions.

OUTPUT STRUCTURE:
1. API Overview - Purpose, versioning, base URL
2. Authentication - Auth methods, tokens
3. Endpoints - Grouped by resource
4. Error Handling - Error codes, formats
5. Rate Limiting - Limits, quotas
6. Examples - Request/response examples
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class APISpecGenerator(DocumentGenerator):
    """Generates API Specification documents."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.API_SPEC

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate API spec sections from decisions."""
        sections = []

        # 1. API Overview
        sections.append(self._generate_overview(decisions, config))

        # 2. Authentication Section
        auth_decisions = [d for d in decisions if self._is_auth_related(d)]
        if auth_decisions:
            sections.append(self._generate_auth(auth_decisions))

        # 3. Endpoints Section
        endpoint_decisions = [d for d in decisions if self._is_endpoint_related(d)]
        if endpoint_decisions:
            sections.append(self._generate_endpoints(endpoint_decisions))

        # 4. Error Handling Section
        error_decisions = [d for d in decisions if self._is_error_related(d)]
        sections.append(self._generate_errors(error_decisions or decisions))

        # 5. Constraints & Rules
        sections.append(self._generate_api_constraints(decisions))

        return sections

    def _generate_overview(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate API overview section."""
        content = f"""## API Overview

This document describes the API specification based on {len(decisions)} architectural decisions.

**Base URL:** `https://api.example.com/v1`

**Versioning:** API version is included in the URL path.

**Content Type:** `application/json`

**Decisions Covered:** {len(decisions)}
"""
        return DocumentSection(
            id="overview",
            title="API Overview",
            content=content,
            level=1,
        )

    def _generate_auth(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate authentication section."""
        content_lines = [
            "## Authentication\n",
            "The following authentication methods and rules apply:\n"
        ]

        for d in decisions:
            code = d.get("code", "")
            statement = d.get("statement", "")
            content_lines.append(f"### {code}")
            content_lines.append(statement)
            content_lines.append("")

            # Extract auth-related constraints
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    rule = c.get("rule", "")
                    ctype = c.get("type", "MUST")
                    content_lines.append(f"- **{ctype}:** {rule}")
            content_lines.append("")

        return DocumentSection(
            id="authentication",
            title="Authentication",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _generate_endpoints(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate endpoints section."""
        subsections = []

        # Group by scope (resource)
        by_resource: Dict[str, List[Dict]] = {}
        for d in decisions:
            scope = d.get("scope_path", "api")
            # Extract resource from scope: be.api.users -> users
            parts = scope.split(".")
            resource = parts[-1] if len(parts) > 2 else parts[-1] if parts else "general"
            if resource not in by_resource:
                by_resource[resource] = []
            by_resource[resource].append(d)

        for resource, res_decisions in by_resource.items():
            content_lines = []
            for d in res_decisions:
                code = d.get("code", "")
                statement = d.get("statement", "")
                content_lines.append(f"**{code}**: {statement}")
                content_lines.append("")

                # Add constraints as API rules
                for c in d.get("constraints", []):
                    if isinstance(c, dict):
                        content_lines.append(f"  - {c.get('type', 'MUST')}: {c.get('rule', '')}")
                content_lines.append("")

            subsections.append(DocumentSection(
                id=f"endpoint-{resource}",
                title=f"{resource.title()} Endpoints",
                content="\n".join(content_lines),
                level=2,
                decision_ids=[d.get("code", "") for d in res_decisions],
            ))

        return DocumentSection(
            id="endpoints",
            title="Endpoints",
            content="API endpoints grouped by resource:",
            level=1,
            subsections=subsections,
        )

    def _generate_errors(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate error handling section."""
        content = """## Error Handling

### Standard Error Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

"""
        # Add error-related decisions
        error_rules = []
        for d in decisions:
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    rule = c.get("rule", "").lower()
                    if "error" in rule or "exception" in rule or "response" in rule:
                        error_rules.append(f"- {c.get('rule', '')}")

        if error_rules:
            content += "\n### Error Handling Rules\n\n"
            content += "\n".join(error_rules[:10])

        return DocumentSection(
            id="errors",
            title="Error Handling",
            content=content,
            level=1,
        )

    def _generate_api_constraints(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate API constraints section."""
        content_lines = [
            "## API Constraints & Rules\n",
            "The following rules apply to all API interactions:\n"
        ]

        must_rules = []
        rate_limits = []
        other_rules = []

        for d in decisions:
            code = d.get("code", "")
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    rule = c.get("rule", "")
                    ctype = c.get("type", "MUST")
                    entry = f"- **[{code}]** {rule}"

                    if "rate" in rule.lower() or "limit" in rule.lower():
                        rate_limits.append(entry)
                    elif ctype in ["MUST", "MUST_NOT"]:
                        must_rules.append(entry)
                    else:
                        other_rules.append(entry)

        if must_rules:
            content_lines.append("### Required Rules")
            content_lines.extend(must_rules[:15])
            content_lines.append("")

        if rate_limits:
            content_lines.append("### Rate Limiting")
            content_lines.extend(rate_limits)
            content_lines.append("")

        if other_rules:
            content_lines.append("### Recommendations")
            content_lines.extend(other_rules[:10])

        return DocumentSection(
            id="constraints",
            title="API Constraints",
            content="\n".join(content_lines),
            level=1,
            decision_ids=[d.get("code", "") for d in decisions],
        )

    def _is_auth_related(self, decision: Dict[str, Any]) -> bool:
        """Check if decision is auth-related."""
        tags = set(t.lower() for t in decision.get("tags", []))
        auth_tags = {"auth", "authentication", "authorization", "token", "jwt", "oauth"}
        text = (decision.get("statement", "") + decision.get("summary", "")).lower()
        return bool(tags & auth_tags) or "auth" in text

    def _is_endpoint_related(self, decision: Dict[str, Any]) -> bool:
        """Check if decision is endpoint-related."""
        tags = set(t.lower() for t in decision.get("tags", []))
        endpoint_tags = {"endpoint", "api", "rest", "route", "controller"}
        scope = decision.get("scope_path", "")
        return bool(tags & endpoint_tags) or "api" in scope.lower()

    def _is_error_related(self, decision: Dict[str, Any]) -> bool:
        """Check if decision is error-related."""
        tags = set(t.lower() for t in decision.get("tags", []))
        error_tags = {"error", "exception", "handling", "response"}
        return bool(tags & error_tags)


__all__ = ["APISpecGenerator"]
