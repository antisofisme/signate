"""
Hints Service

Provides AI-powered hints for decision text fields.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .providers import get_ai_provider
from .providers.base import ChatMessage


HINTS_PROMPT_TEMPLATE = """Analyze the following text for a MANTRA decision field and provide hints.

Field Type: {field_type}
Text to analyze:
---
{text}
---

{context_info}

Provide hints in this exact format:

📝 GRAMMAR:
[Provide a more formal/professional version of the text. Keep the meaning exactly the same.]

⚠️ SIMILAR:
[Check if this is similar to any existing decision. If yes, mention it. If no, say "No similar decisions found."]

💡 SUGGESTION:
[Provide 1-3 specific suggestions to improve clarity, completeness, or professionalism.]

🏷️ CLASSIFICATION:
[If this is a statement, suggest the appropriate Domain (INT/ARCH/CTL/EVO) and Aspect (A01-A16). Explain briefly why.]

Keep responses concise and actionable. Use the same language as the input text (Indonesian or English)."""


@dataclass
class HintResult:
    """Result from hints analysis."""
    grammar: str
    similar: str
    suggestions: List[str]
    classification: Optional[str]
    raw_response: str
    provider: str
    model: str


class HintsService:
    """
    Service for providing AI hints on decision text.

    Analyzes text and provides:
    - Grammar corrections
    - Similar decision detection
    - Improvement suggestions
    - Classification recommendations
    """

    async def get_hints(
        self,
        text: str,
        field_type: str = "statement",
        existing_decisions: List[Dict] = None,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Get AI hints for a text field.

        Args:
            text: Text to analyze
            field_type: Type of field (statement, rationale, constraint, etc.)
            existing_decisions: List of existing decisions for comparison
            context: Additional context (current group, feature, etc.)

        Returns:
            Dict with hints and metadata
        """
        if not text or not text.strip():
            return {
                "success": False,
                "error": "No text provided for analysis",
            }

        # Build context info
        context_parts = []

        if existing_decisions:
            context_parts.append("Existing decisions for comparison:")
            for d in existing_decisions[:20]:  # Limit for prompt size
                code = d.get("decision_code") or d.get("decision_id", "")[:12]
                statement = d.get("statement", "")[:80]
                context_parts.append(f"- {code}: {statement}")

        if context:
            if context.get("domain_id"):
                context_parts.append(f"Current domain: {context['domain_id']}")
            if context.get("aspect_id"):
                context_parts.append(f"Current aspect: {context['aspect_id']}")

        context_info = "\n".join(context_parts) if context_parts else "No additional context."

        # Build prompt
        prompt = HINTS_PROMPT_TEMPLATE.format(
            field_type=field_type,
            text=text,
            context_info=context_info,
        )

        try:
            provider = get_ai_provider()
            response = await provider.complete(prompt)

            # Parse response into structured hints
            hints = self._parse_hints_response(response.content)

            return {
                "success": True,
                "hints": {
                    "grammar": hints.grammar,
                    "similar": hints.similar,
                    "suggestions": hints.suggestions,
                    "classification": hints.classification,
                },
                "raw_response": response.content,
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"AI service error: {str(e)}",
            }

    def _parse_hints_response(self, response: str) -> HintResult:
        """Parse AI response into structured hints."""
        grammar = ""
        similar = ""
        suggestions = []
        classification = None

        current_section = None
        current_content = []

        for line in response.split("\n"):
            line = line.strip()

            if line.startswith("📝 GRAMMAR:"):
                if current_section and current_content:
                    self._save_section(current_section, current_content, locals())
                current_section = "grammar"
                current_content = [line.replace("📝 GRAMMAR:", "").strip()]
            elif line.startswith("⚠️ SIMILAR:"):
                if current_section and current_content:
                    self._save_section(current_section, current_content, locals())
                current_section = "similar"
                current_content = [line.replace("⚠️ SIMILAR:", "").strip()]
            elif line.startswith("💡 SUGGESTION:"):
                if current_section and current_content:
                    self._save_section(current_section, current_content, locals())
                current_section = "suggestions"
                current_content = [line.replace("💡 SUGGESTION:", "").strip()]
            elif line.startswith("🏷️ CLASSIFICATION:"):
                if current_section and current_content:
                    self._save_section(current_section, current_content, locals())
                current_section = "classification"
                current_content = [line.replace("🏷️ CLASSIFICATION:", "").strip()]
            elif line and current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            content = "\n".join(current_content).strip()
            if current_section == "grammar":
                grammar = content
            elif current_section == "similar":
                similar = content
            elif current_section == "suggestions":
                # Split suggestions by numbered list or bullet points
                suggestions = [s.strip() for s in content.split("\n") if s.strip()]
                suggestions = [s.lstrip("0123456789.-) ") for s in suggestions if s]
            elif current_section == "classification":
                classification = content

        return HintResult(
            grammar=grammar or response[:200],  # Fallback to start of response
            similar=similar or "Unable to determine similarity.",
            suggestions=suggestions or ["Review the text for clarity."],
            classification=classification,
            raw_response=response,
            provider="",
            model="",
        )

    def _save_section(self, section: str, content: List[str], local_vars: dict):
        """Helper to save parsed section."""
        text = "\n".join(content).strip()
        if section == "grammar":
            local_vars["grammar"] = text
        elif section == "similar":
            local_vars["similar"] = text
        elif section == "suggestions":
            local_vars["suggestions"] = [s.strip() for s in text.split("\n") if s.strip()]
        elif section == "classification":
            local_vars["classification"] = text


# Singleton instance
_hints_service: Optional[HintsService] = None


def get_hints_service() -> HintsService:
    """Get hints service singleton."""
    global _hints_service
    if _hints_service is None:
        _hints_service = HintsService()
    return _hints_service
