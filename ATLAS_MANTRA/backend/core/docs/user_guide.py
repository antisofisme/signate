"""
MANTRA User Guide Generator

Generates user-friendly documentation for end users/customers.

Features:
- Simplified language (no technical jargon)
- How-to focused
- Examples and screenshots placeholders
- FAQ generation

OUTPUT STRUCTURE:
1. Getting Started - Quick start guide
2. Features - What you can do
3. How-To Guides - Step-by-step instructions
4. FAQ - Common questions
5. Troubleshooting - Common issues
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class UserGuideGenerator(DocumentGenerator):
    """Generates User Guide documents for end users."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.USER_MANUAL

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate user guide sections."""
        sections = []

        # 1. Getting Started
        sections.append(self._generate_getting_started(decisions, config))

        # 2. Features Overview
        sections.append(self._generate_features(decisions))

        # 3. How-To Guides
        sections.append(self._generate_how_to(decisions))

        # 4. FAQ
        sections.append(self._generate_faq(decisions))

        # 5. Troubleshooting
        sections.append(self._generate_troubleshooting(decisions))

        return sections

    def _simplify_text(self, text: str) -> str:
        """Simplify technical text for end users."""
        # Replace technical terms with simpler alternatives
        replacements = {
            "authenticate": "log in",
            "authorization": "permission",
            "API": "system",
            "endpoint": "feature",
            "parameter": "option",
            "configuration": "settings",
            "implement": "set up",
            "invoke": "use",
            "instantiate": "create",
            "execute": "run",
            "MUST": "need to",
            "MUST NOT": "should not",
            "SHOULD": "it's best to",
        }
        result = text
        for tech, simple in replacements.items():
            result = result.replace(tech, simple)
            result = result.replace(tech.lower(), simple)
        return result

    def _generate_getting_started(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate getting started section."""
        content = """## Getting Started

Welcome! This guide will help you get started quickly.

### What You'll Need

Before you begin, make sure you have:
- An active account
- Access to the system
- A modern web browser

### Quick Start Steps

1. **Log in** to your account
2. **Explore** the main features
3. **Try** the basic functions
4. **Check** the How-To guides for specific tasks

### Need Help?

If you run into any issues, check the FAQ section or contact support.
"""
        return DocumentSection(
            id="getting-started",
            title="Getting Started",
            content=content,
            level=1,
        )

    def _generate_features(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate features overview section."""
        content_lines = [
            "## Features Overview\n",
            "Here's what you can do:\n"
        ]

        # Extract user-facing features from decisions
        for d in decisions[:10]:  # Limit to top 10
            statement = d.get("statement", "")
            summary = d.get("summary", "")

            # Simplify and extract feature description
            text = self._simplify_text(summary or statement[:100])
            if text:
                content_lines.append(f"- **{text[:50]}**")

        if len(content_lines) == 2:
            content_lines.append("- Features are being documented")

        return DocumentSection(
            id="features",
            title="Features Overview",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_how_to(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate how-to guides section."""
        subsections = []

        # Group decisions that have examples
        with_examples = [d for d in decisions if d.get("examples")]

        for d in with_examples[:5]:  # Top 5 with examples
            code = d.get("code", "")
            summary = self._simplify_text(d.get("summary", "How to use this feature"))
            examples = d.get("examples", [])

            content_lines = [f"Here's how to do this:\n"]

            # Convert examples to steps
            for i, ex in enumerate(examples[:5], 1):
                simplified = self._simplify_text(str(ex))
                content_lines.append(f"{i}. {simplified}")

            content_lines.append("")
            content_lines.append("> **Tip:** Take it step by step!")

            subsections.append(DocumentSection(
                id=f"howto-{code}",
                title=f"How to: {summary[:40]}",
                content="\n".join(content_lines),
                level=2,
                decision_ids=[code],
            ))

        if not subsections:
            subsections.append(DocumentSection(
                id="howto-placeholder",
                title="How-To Guides Coming Soon",
                content="Detailed how-to guides are being prepared.",
                level=2,
            ))

        return DocumentSection(
            id="how-to",
            title="How-To Guides",
            content="Step-by-step guides for common tasks:",
            level=1,
            subsections=subsections,
        )

    def _generate_faq(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate FAQ section."""
        content_lines = [
            "## Frequently Asked Questions\n"
        ]

        # Generate FAQs from decisions with rationale
        faq_count = 0
        for d in decisions:
            rationale = d.get("rationale", "")
            summary = d.get("summary", "")

            if rationale and faq_count < 10:
                question = f"Why does the system {self._simplify_text(summary[:50])}?"
                answer = self._simplify_text(rationale[:150])
                content_lines.append(f"### Q: {question}")
                content_lines.append(f"**A:** {answer}...")
                content_lines.append("")
                faq_count += 1

        if faq_count == 0:
            content_lines.append("### Q: How do I get started?")
            content_lines.append("**A:** Check the Getting Started section above!")
            content_lines.append("")
            content_lines.append("### Q: Who can I contact for help?")
            content_lines.append("**A:** Contact our support team for assistance.")

        return DocumentSection(
            id="faq",
            title="Frequently Asked Questions",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_troubleshooting(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate troubleshooting section."""
        content_lines = [
            "## Troubleshooting\n",
            "### Common Issues and Solutions\n"
        ]

        # Extract MUST_NOT constraints as things to avoid
        issues = []
        for d in decisions:
            for c in d.get("constraints", []):
                if isinstance(c, dict) and c.get("type") == "MUST_NOT":
                    rule = self._simplify_text(c.get("rule", ""))
                    if rule:
                        issues.append(f"**Issue:** {rule[:60]}\n**Solution:** Avoid doing this.")

        if issues:
            content_lines.extend(issues[:5])
        else:
            content_lines.append("**Issue:** Something isn't working")
            content_lines.append("**Solution:** Try refreshing the page or logging out and back in.")
            content_lines.append("")
            content_lines.append("**Issue:** I can't access a feature")
            content_lines.append("**Solution:** Make sure you have the right permissions. Contact your admin if needed.")

        content_lines.append("")
        content_lines.append("### Still Need Help?")
        content_lines.append("Contact support if the issue persists.")

        return DocumentSection(
            id="troubleshooting",
            title="Troubleshooting",
            content="\n".join(content_lines),
            level=1,
        )


__all__ = ["UserGuideGenerator"]
