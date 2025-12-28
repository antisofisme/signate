"""
PromptShaper - Transform voice input into Claude prompts

Architecture: JARVIS-L1-DEC-003 (Prompt Shaping Contract)
Pattern: Deterministic template-based transformation (mechanical, transparent)

No inference. No creativity. No context-aware logic.
Explicit templates only. Same input → same output.
"""

from dataclasses import dataclass


class PromptShaperError(Exception):
    """Prompt shaping error (user-facing message)."""
    pass


@dataclass
class WrappedPrompt:
    """Result of prompt shaping."""
    prefix: str  # Mode prefix (or empty for default)
    wrapped_text: str  # prefix + original text
    mode_applied: str  # Which mode was used


class PromptShaper:
    """
    Transform voice input into Claude prompts with deterministic mode prefix.

    Input: text + mode
    Output: Shaped prompt (prefix + text)

    Contract (JARVIS-L1-DEC-003):
    - MECHANICAL: Lookup table + string concat only
    - DETERMINISTIC: Same input → same output
    - TRANSPARENT: Prefix visible to user and Claude
    - HINTS ONLY: Prefixes are suggestions, not instructions
    - NO INFERENCE: No context-aware logic

    Mode-to-prefix mapping (fixed, deterministic):
    - default: "" (no prefix)
    - coding: "[CODING] "
    - debug: "[DEBUG] "
    - explain: "[EXPLAIN] "

    Pattern:
        shaper = PromptShaper()
        prompt = shaper.shape(text="write a function", mode="coding")
        # Returns: "[CODING] write a function"
    """

    MODE_PREFIXES = {
        "default": "",
        "coding": "[CODING] ",
        "debug": "[DEBUG] ",
        "explain": "[EXPLAIN] ",
    }

    def __init__(self):
        """Initialize shaper (stateless, deterministic)."""
        pass

    def shape(self, text: str, mode: str) -> WrappedPrompt:
        """
        Shape prompt deterministically from text and mode.

        Contract (JARVIS-L1-DEC-003):
        - MECHANICAL: Lookup mode prefix + concatenate
        - DETERMINISTIC: Same (text, mode) → same wrapped output
        - PURE: No state mutation
        - TRANSPARENT: Visible wrapping

        Args:
            text: Voice input text (clean, from safety gate)
            mode: Current interaction mode (default, coding, debug, explain)

        Returns:
            WrappedPrompt with prefix, wrapped text, and mode applied

        Raises:
            PromptShaperError: If mode is invalid
        """
        if not text:
            raise PromptShaperError("Cannot shape empty text")

        if mode not in self.MODE_PREFIXES:
            raise PromptShaperError(
                f"Invalid mode: {mode}. "
                f"Valid modes: {', '.join(self.MODE_PREFIXES.keys())}"
            )

        # Lookup prefix (deterministic)
        prefix = self.MODE_PREFIXES[mode]

        # Concatenate (mechanical)
        wrapped_text = prefix + text

        return WrappedPrompt(
            prefix=prefix,
            wrapped_text=wrapped_text,
            mode_applied=mode
        )

    def get_modes(self) -> list:
        """Get list of valid interaction modes (read-only)."""
        return list(self.MODE_PREFIXES.keys())
