"""
SafetyGate - Protect dangerous voice input before execution

Architecture: JARVIS-DEC-003 (command grammar & safety)
Pattern: Deterministic rule-based decision (never executes, only decides)

No execution inside SafetyGate.
No async, no background checks, no persistence, no "smart defaults".
Explicit rules only. No heuristics. No learning.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List


class SafetyDecision(Enum):
    """Decision from SafetyGate."""
    ALLOW = "allow"
    REQUIRE_CONFIRMATION = "require_confirmation"
    DENY = "deny"


@dataclass
class SafetyCheckResult:
    """Result of safety check."""
    decision: SafetyDecision
    reason: str
    matched_pattern: str = None


class SafetyGateError(Exception):
    """Safety gate error (user-facing message)."""
    pass


class SafetyGate:
    """
    Protect against dangerous patterns in voice input.

    Input: VoiceInput (transcribed text)
    Output: SafetyDecision (ALLOW, REQUIRE_CONFIRMATION, DENY)

    Decision rules (explicit, deterministic):
    1. Check against dangerous patterns
    2. Return REQUIRE_CONFIRMATION if dangerous
    3. Return ALLOW if safe
    4. Never returns DENY (user always decides)

    Dangerous patterns (from JARVIS-DEC-003):
    - File operations: rm -rf, rm -r, rmdir, del, format
    - Git operations: git reset, git rebase, git force, git push -f
    - Database operations: drop table, delete from, truncate
    - System operations: killall, shutdown, reboot

    Pattern:
        gate = SafetyGate()
        result = gate.check(VoiceInput("rm -rf /home"))
        # Returns: SafetyCheckResult(REQUIRE_CONFIRMATION, reason, pattern)
    """

    DANGEROUS_PATTERNS = {
        "file_ops": [
            "rm -rf",
            "rm -r",
            "rmdir",
            "del ",
            "format ",
        ],
        "git_ops": [
            "git reset",
            "git rebase",
            "git force",
            "git push -f",
        ],
        "db_ops": [
            "drop table",
            "delete from",
            "truncate ",
        ],
        "system_ops": [
            "killall",
            "shutdown",
            "reboot",
        ],
    }

    def __init__(self):
        """Initialize gate (stateless, deterministic)."""
        pass

    def check(self, voice_input_text: str) -> SafetyCheckResult:
        """
        Check if voice input is safe.

        Args:
            voice_input_text: Transcribed voice input text

        Returns:
            SafetyCheckResult with decision and reason

        Raises:
            SafetyGateError: If check fails
        """
        if not voice_input_text:
            raise SafetyGateError("Empty voice input")

        text_lower = voice_input_text.lower()

        matched = self._find_dangerous_pattern(text_lower)

        if matched:
            return SafetyCheckResult(
                decision=SafetyDecision.REQUIRE_CONFIRMATION,
                reason=f"Dangerous pattern detected: {matched}",
                matched_pattern=matched
            )

        return SafetyCheckResult(
            decision=SafetyDecision.ALLOW,
            reason="Voice input is safe"
        )

    def _find_dangerous_pattern(self, text: str) -> str:
        """
        Find dangerous pattern in text (case-insensitive substring match).

        Args:
            text: Lowercase text to check

        Returns:
            Matched pattern string, or None if no match
        """
        for category, patterns in self.DANGEROUS_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return pattern

        return None

    def get_dangerous_patterns(self) -> dict:
        """Get list of dangerous patterns (read-only)."""
        return self.DANGEROUS_PATTERNS

    def is_safe(self, voice_input_text: str) -> bool:
        """
        Quick check: is input safe?

        Args:
            voice_input_text: Transcribed text

        Returns:
            bool: True if safe, False if requires confirmation
        """
        try:
            result = self.check(voice_input_text)
            return result.decision == SafetyDecision.ALLOW
        except SafetyGateError:
            return False
