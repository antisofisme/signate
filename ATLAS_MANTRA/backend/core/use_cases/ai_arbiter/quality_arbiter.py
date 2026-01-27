"""
Quality Arbiter for Borderline Quality Scores

Handles decisions with quality scores in the "gray zone" (50-80).
- Below 50: Automatically rejected (no AI needed)
- Above 80: Automatically approved (no AI needed)
- 50-80: AI arbitration to decide if quality is sufficient

DELEGATED mode provides the context to the user's AI for judgment.
"""

from typing import Any, Dict, List

from .base import (
    BaseArbiter,
    ArbiterVerdict,
    ArbiterResult,
    ArbitrationType,
    ArbitrationContext,
)


class QualityArbiter(BaseArbiter):
    """Arbitrate borderline quality scores (50-80)."""

    # Score thresholds
    BORDERLINE_MIN = 50
    BORDERLINE_MAX = 80

    @property
    def arbitration_type(self) -> ArbitrationType:
        return ArbitrationType.QUALITY

    def should_invoke(self, context: Dict[str, Any]) -> bool:
        """
        Check if quality score is in borderline range.

        Args:
            context: Must contain 'quality_score' (0-100)

        Returns:
            True if score is 50-80 (needs arbitration)
        """
        score = context.get('quality_score', 0)
        return self.BORDERLINE_MIN <= score <= self.BORDERLINE_MAX

    def generate_context(self, context: Dict[str, Any]) -> ArbitrationContext:
        """
        Generate context for delegated quality arbitration.

        The prompt asks the client AI to evaluate if the decision
        provides enough clarity and justification for implementation.
        """
        statement = context.get('statement', '')
        rationale = context.get('rationale', '')
        quality_score = context.get('quality_score', 0)
        statement_score = context.get('statement_score', 0)
        rationale_score = context.get('rationale_score', 0)
        suggestions = context.get('suggestions', [])
        coherence_score = context.get('coherence_score', 0)
        readability = context.get('readability', {})

        # Build issues list compactly
        issues_text = "\n".join(f"• {s}" for s in suggestions[:5]) if suggestions else "None"

        prompt = f"""Evaluate this architectural decision record (ADR).

DECISION:
"{statement}"

RATIONALE:
"{rationale}"

METRICS:
• Quality: {quality_score}/100 (borderline 50-80 range)
• Statement: {statement_score}/25, Rationale: {rationale_score}/25
• Coherence: {coherence_score:.1%}

ISSUES:
{issues_text}

QUESTION: Can a developer implement this decision with the information provided?

Return JSON:
{{"verdict": "APPROVE|REJECT|NEEDS_IMPROVEMENT", "confidence": 0.0-1.0, "reason": "1-2 sentences", "suggestions": ["if NEEDS_IMPROVEMENT"]}}

APPROVE = Clear enough to implement
REJECT = Missing critical information (what/why unclear)
NEEDS_IMPROVEMENT = Specific clarifications needed"""

        return ArbitrationContext(
            arbitration_type=ArbitrationType.QUALITY,
            prompt_template=prompt,
            context_data={
                'statement': statement,
                'rationale': rationale,
                'quality_score': quality_score,
                'statement_score': statement_score,
                'rationale_score': rationale_score,
                'suggestions': suggestions,
                'coherence_score': coherence_score,
            },
            expected_verdicts=['APPROVE', 'REJECT', 'NEEDS_IMPROVEMENT'],
            instructions="APPROVE→store, REJECT→block, NEEDS_IMPROVEMENT→suggestions",
        )

    async def arbitrate(self, context: Dict[str, Any]) -> ArbiterResult:
        """
        Perform server-side quality arbitration.

        Note: This requires API key and is not the recommended mode.
        Use DELEGATED mode for cost efficiency.
        """
        arb_context = self.generate_context(context)
        response = await self._call_ai(arb_context.prompt_template)
        return self._parse_response(response)

    def quick_judgment(self, context: Dict[str, Any]) -> ArbiterResult:
        """
        Quick rule-based judgment for when AI is unavailable.

        This provides a reasonable default based on sub-scores
        when neither SERVER nor DELEGATED mode is used.
        """
        statement_score = context.get('statement_score', 0)
        rationale_score = context.get('rationale_score', 0)
        coherence_score = context.get('coherence_score', 0)

        # If any critical component is very low, reject
        if statement_score < 10:
            return ArbiterResult(
                verdict=ArbiterVerdict.REJECT,
                confidence=0.7,
                reason="Statement quality too low for meaningful decision",
                suggestions=["Expand the statement with more technical detail"],
                metadata={'mode': 'QUICK_JUDGMENT'},
            )

        if rationale_score < 8:
            return ArbiterResult(
                verdict=ArbiterVerdict.REJECT,
                confidence=0.7,
                reason="Rationale insufficient to justify the decision",
                suggestions=["Explain WHY this decision was made"],
                metadata={'mode': 'QUICK_JUDGMENT'},
            )

        # If coherence is very low, the statement and rationale don't match
        if coherence_score < 0.4:
            return ArbiterResult(
                verdict=ArbiterVerdict.NEEDS_IMPROVEMENT,
                confidence=0.6,
                reason="Statement and rationale appear disconnected",
                suggestions=["Ensure rationale directly supports the statement"],
                metadata={'mode': 'QUICK_JUDGMENT'},
            )

        # Otherwise, tentatively approve with warning
        return ArbiterResult(
            verdict=ArbiterVerdict.APPROVE,
            confidence=0.6,
            reason="Quality is borderline but acceptable",
            suggestions=["Consider improving quality for better documentation"],
            metadata={'mode': 'QUICK_JUDGMENT'},
        )
