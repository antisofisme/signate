"""
SafetyGate - Pass-through (Compliance Locked)

ENFORCEMENT: SafetyGate does NOT evaluate danger.

Reason: Jarvis is NOT a safety officer.

Pattern matching for "dangerous operations" assumes Jarvis is smart enough to:
1. Understand intent
2. Evaluate risk
3. Make judgment calls

This violates: "Jarvis is plumbing, not a brain"

Claude is the authoritative decision-maker.
If Claude warns about danger, fine.
If user insists anyway, also fine.

Jarvis just passes input through.
No evaluation. No blocking. No "protection".

Architecture Decision (COMPLIANCE LOCKED):
- SafetyGate.check() always returns ALLOW
- No pattern matching
- No confirmation dialogs
- Input goes to Claude as-is
"""

from enum import Enum
from dataclasses import dataclass


class SafetyDecision(Enum):
    """Decision from SafetyGate."""
    ALLOW = "allow"


@dataclass
class SafetyCheckResult:
    """Result of safety check (always ALLOW)."""
    decision: SafetyDecision
    reason: str


class SafetyGateError(Exception):
    """Safety gate error."""
    pass


class SafetyGate:
    """
    Pass-through - always return ALLOW.

    Contract (Compliance Locked):
    - NO pattern matching
    - NO danger evaluation
    - NO confirmation dialogs
    - Input goes to Claude unchanged
    """

    def __init__(self):
        """Initialize (stateless)."""
        pass

    def check(self, voice_input_text: str) -> SafetyCheckResult:
        """
        Always return ALLOW (pass-through).

        Args:
            voice_input_text: Transcribed voice input

        Returns:
            SafetyCheckResult with ALLOW decision

        Raises:
            SafetyGateError: If text is empty
        """
        if not voice_input_text:
            raise SafetyGateError("Empty voice input")

        # PASS-THROUGH: Always allow, no evaluation
        return SafetyCheckResult(
            decision=SafetyDecision.ALLOW,
            reason="Passed through to Claude (Jarvis does not evaluate danger)"
        )
