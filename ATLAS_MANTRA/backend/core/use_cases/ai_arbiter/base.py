"""
Base Arbiter Interface for MANTRA AI Arbitration

Defines the common interface for all arbiters and supports
both SERVER and DELEGATED arbitration modes.

DELEGATED mode is the recommended approach for MCP/CLI users:
- User's AI (Claude Code, Cursor, etc.) performs arbitration
- MANTRA returns arbitration_context instead of calling AI
- User's AI decides and submits verdict back
- Cost: $0 for MANTRA (user pays via existing AI subscription)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ArbiterVerdict(str, Enum):
    """Possible verdicts from AI arbitration."""
    # Quality verdicts
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT"

    # Duplicate verdicts
    DUPLICATE = "DUPLICATE"
    EVOLUTION = "EVOLUTION"
    DIFFERENT = "DIFFERENT"

    # Conflict verdicts
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"
    NOT_CONFLICT = "NOT_CONFLICT"


class ArbitrationMode(str, Enum):
    """Arbitration execution mode."""
    SERVER = "SERVER"       # MANTRA's AI does arbitration (costs $)
    DELEGATED = "DELEGATED" # Client AI does arbitration (user's existing AI)
    SKIP = "SKIP"           # No AI arbitration (accept uncertainty)


class ArbitrationType(str, Enum):
    """Type of arbitration needed."""
    QUALITY = "QUALITY"           # Borderline quality score
    DUPLICATE = "DUPLICATE"       # Near-duplicate classification
    CONFLICT = "CONFLICT"         # Medium-severity conflict


@dataclass
class ArbiterResult:
    """Result from AI arbitration (either mode)."""
    verdict: ArbiterVerdict
    confidence: float  # 0-1
    reason: str
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArbitrationContext:
    """
    Context for delegated arbitration.

    When MANTRA detects an ambiguous case and mode is DELEGATED,
    this context is returned to the client AI for arbitration.
    """
    arbitration_type: ArbitrationType
    prompt_template: str  # Ready-to-use prompt for client AI
    context_data: Dict[str, Any]  # All data needed for decision
    expected_verdicts: List[str]  # Valid verdict options
    instructions: str  # How to interpret and respond

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for API response."""
        return {
            'arbitration_type': self.arbitration_type.value,
            'prompt_template': self.prompt_template,
            'context_data': self.context_data,
            'expected_verdicts': self.expected_verdicts,
            'instructions': self.instructions,
        }


@dataclass
class ArbitrationVerdict:
    """Verdict submitted by client AI (for delegated mode)."""
    arbitration_type: ArbitrationType
    verdict: ArbiterVerdict
    confidence: float
    reason: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArbitrationVerdict':
        """Create from dict (API request)."""
        return cls(
            arbitration_type=ArbitrationType(data['arbitration_type']),
            verdict=ArbiterVerdict(data['verdict']),
            confidence=float(data.get('confidence', 0.8)),
            reason=data.get('reason', 'No reason provided'),
        )


class BaseArbiter(ABC):
    """
    Abstract base for AI arbiters.

    Each arbiter:
    1. Determines if arbitration is needed (should_invoke)
    2. Generates context for delegated mode (generate_context)
    3. Performs server-side arbitration if enabled (arbitrate)
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize arbiter.

        Args:
            api_key: API key for server-side AI (optional for delegated mode)
            model: Model to use for server-side arbitration
        """
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def arbitration_type(self) -> ArbitrationType:
        """The type of arbitration this arbiter handles."""
        pass

    @abstractmethod
    def should_invoke(self, context: Dict[str, Any]) -> bool:
        """
        Determine if AI arbitration is needed.

        Args:
            context: Validation context (scores, matches, conflicts, etc.)

        Returns:
            True if this case needs AI arbitration
        """
        pass

    @abstractmethod
    def generate_context(self, context: Dict[str, Any]) -> ArbitrationContext:
        """
        Generate context for delegated arbitration.

        This is called when mode is DELEGATED. The returned context
        is sent to the client AI for arbitration.

        Args:
            context: Validation context

        Returns:
            ArbitrationContext with prompt and data for client AI
        """
        pass

    @abstractmethod
    async def arbitrate(self, context: Dict[str, Any]) -> ArbiterResult:
        """
        Perform server-side AI arbitration.

        This is called when mode is SERVER. Requires api_key.

        Args:
            context: Validation context

        Returns:
            ArbiterResult with verdict
        """
        pass

    def accept_verdict(
        self,
        verdict: ArbitrationVerdict,
        original_context: Dict[str, Any]
    ) -> ArbiterResult:
        """
        Accept verdict from client AI (delegated mode).

        Converts client verdict into ArbiterResult.

        Args:
            verdict: Verdict submitted by client AI
            original_context: Original validation context

        Returns:
            ArbiterResult
        """
        return ArbiterResult(
            verdict=verdict.verdict,
            confidence=verdict.confidence,
            reason=verdict.reason,
            suggestions=[],
            metadata={
                'mode': 'DELEGATED',
                'arbitration_type': verdict.arbitration_type.value,
            }
        )

    async def _call_ai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Call AI API for server-side arbitration.

        Uses the multi-provider AI client.
        """
        from .ai_client import get_ai_client, AIClient

        client = get_ai_client()

        if not client.is_configured:
            raise ValueError(
                "AI client not configured. Set AI_API_KEY or provider-specific key "
                "(ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)"
            )

        return await client.complete(prompt, system_prompt)

    def _parse_response(self, response: str) -> ArbiterResult:
        """
        Parse AI response into ArbiterResult.

        Expected format: JSON with verdict, confidence, reason, suggestions
        """
        import json
        try:
            data = json.loads(response)
            return ArbiterResult(
                verdict=ArbiterVerdict(data['verdict']),
                confidence=float(data.get('confidence', 0.8)),
                reason=data.get('reason', 'No reason provided'),
                suggestions=data.get('suggestions', []),
                metadata=data.get('metadata', {}),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return ArbiterResult(
                verdict=ArbiterVerdict.NEEDS_IMPROVEMENT,
                confidence=0.5,
                reason=f"Failed to parse AI response: {str(e)}",
                suggestions=[],
                metadata={'parse_error': str(e)},
            )
