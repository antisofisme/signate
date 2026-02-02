"""
PromptShaper - Pass-through for voice input (Compliance Locked)

ENFORCEMENT: PromptShaper is a NO-OP.

Reason: Mode prefixes like "[CODING]" are SILENT SEMANTIC MODIFICATIONS.

This violates: "Jarvis never interprets, evaluates, or rewrites Claude's answers"
Extended to: "Jarvis never modifies user input without explicit user action"

If user wants mode-specific behavior:
- User speaks it explicitly: "mode coding" → Jarvis acknowledges
- User speaks their input: "write a function"
- Both are visible in CLI
- Claude sees ONLY the input, not hidden prefixes

Architecture Decision (COMPLIANCE LOCKED):
- PromptShaper.shape() returns text AS-IS
- mode parameter ignored
- No prefix injection
- No silent modifications
"""

from dataclasses import dataclass


class PromptShaperError(Exception):
    """Prompt shaping error."""
    pass


@dataclass
class WrappedPrompt:
    """Result of prompt shaping (pass-through)."""
    wrapped_text: str  # Original text, unchanged


class PromptShaper:
    """
    Pass-through - return text unchanged.

    Contract (Compliance Locked):
    - NO prefix injection
    - NO silent modifications
    - User input goes to Claude AS-IS
    """

    def __init__(self):
        """Initialize (stateless)."""
        pass

    def shape(self, text: str, mode: str = None) -> WrappedPrompt:
        """
        Return text unchanged.

        Args:
            text: Voice input text
            mode: Ignored (for compatibility only)

        Returns:
            WrappedPrompt with original text

        Raises:
            PromptShaperError: If text is empty
        """
        if not text:
            raise PromptShaperError("Cannot shape empty text")

        # PASS-THROUGH: Return text unchanged, no mode prefix
        return WrappedPrompt(wrapped_text=text)
