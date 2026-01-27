"""
Duplicate Classifier for Near-Duplicates

Handles decisions with similarity in the "ambiguous zone" (85-95%).
- Below 85%: Not a duplicate (different enough)
- Above 95%: Exact duplicate (block storage)
- 85-95%: AI classification needed

Classifications:
- DUPLICATE: Same decision, should be blocked
- EVOLUTION: Updated version, should supersede existing
- DIFFERENT: Different enough to coexist (suggest relation)
"""

from typing import Any, Dict

from .base import (
    BaseArbiter,
    ArbiterVerdict,
    ArbiterResult,
    ArbitrationType,
    ArbitrationContext,
)


class DuplicateClassifier(BaseArbiter):
    """Classify near-duplicates (85-95% similarity)."""

    # Similarity thresholds
    NEAR_DUP_MIN = 0.85
    NEAR_DUP_MAX = 0.95

    @property
    def arbitration_type(self) -> ArbitrationType:
        return ArbitrationType.DUPLICATE

    def should_invoke(self, context: Dict[str, Any]) -> bool:
        """
        Check if there's a near-duplicate in the ambiguous range.

        Args:
            context: Must contain 'max_similarity' (0-1)

        Returns:
            True if similarity is 85-95% (needs classification)
        """
        max_sim = context.get('max_similarity', 0)
        return self.NEAR_DUP_MIN <= max_sim <= self.NEAR_DUP_MAX

    def generate_context(self, context: Dict[str, Any]) -> ArbitrationContext:
        """
        Generate context for delegated duplicate classification.

        The prompt asks the client AI to determine if this is:
        - A true duplicate (same decision)
        - An evolution (updated version)
        - A different decision (just happens to be similar)
        """
        new_statement = context.get('new_statement', '')
        new_group = context.get('group_id', '')
        new_feature = context.get('feature_id', '')

        existing_code = context.get('existing_code', '')
        existing_statement = context.get('existing_statement', '')
        existing_created_at = context.get('existing_created_at', 'Unknown')
        similarity = context.get('similarity', 0)
        same_cell = context.get('same_cell', False)

        cell_info = "SAME cell (likely evolution)" if same_cell else "DIFFERENT cell"

        prompt = f"""Classify relationship between two decisions ({similarity:.0%} similar).

NEW: "{new_statement}"
     [{new_group}/{new_feature}]

EXISTING ({existing_code}): "{existing_statement}"
     [{cell_info}] Created: {existing_created_at}

Return JSON:
{{"verdict": "DUPLICATE|EVOLUTION|DIFFERENT", "confidence": 0.0-1.0, "reason": "1-2 sentences", "action": "BLOCK|SUPERSEDE|RELATE"}}

DUPLICATE = Same intent, different words → BLOCK new
EVOLUTION = New improves/updates existing → SUPERSEDE existing
DIFFERENT = Similar wording, different intent → RELATE as informed_by"""

        return ArbitrationContext(
            arbitration_type=ArbitrationType.DUPLICATE,
            prompt_template=prompt,
            context_data={
                'new_statement': new_statement,
                'group_id': new_group,
                'feature_id': new_feature,
                'existing_id': context.get('existing_id', ''),
                'existing_code': existing_code,
                'existing_statement': existing_statement,
                'existing_created_at': existing_created_at,
                'similarity': similarity,
                'same_cell': same_cell,
            },
            expected_verdicts=['DUPLICATE', 'EVOLUTION', 'DIFFERENT'],
            instructions="DUPLICATE→BLOCK, EVOLUTION→SUPERSEDE, DIFFERENT→RELATE",
        )

    async def arbitrate(self, context: Dict[str, Any]) -> ArbiterResult:
        """
        Perform server-side duplicate classification.

        Note: This requires API key and is not the recommended mode.
        Use DELEGATED mode for cost efficiency.
        """
        arb_context = self.generate_context(context)
        response = await self._call_ai(arb_context.prompt_template)
        return self._parse_response(response)

    def quick_judgment(self, context: Dict[str, Any]) -> ArbiterResult:
        """
        Quick rule-based judgment for when AI is unavailable.

        Uses heuristics based on similarity and cell location.
        """
        similarity = context.get('similarity', 0)
        same_cell = context.get('same_cell', False)

        # Very high similarity in same cell = likely evolution
        if similarity >= 0.92 and same_cell:
            return ArbiterResult(
                verdict=ArbiterVerdict.EVOLUTION,
                confidence=0.7,
                reason="Very high similarity in same group/feature suggests evolution",
                suggestions=["Add supersedes relationship to the existing decision"],
                metadata={
                    'mode': 'QUICK_JUDGMENT',
                    'suggested_action': 'SUPERSEDE',
                },
            )

        # High similarity in same cell = probably evolution
        if similarity >= 0.88 and same_cell:
            return ArbiterResult(
                verdict=ArbiterVerdict.EVOLUTION,
                confidence=0.6,
                reason="High similarity in same cell likely indicates an update",
                suggestions=["Consider if this supersedes the existing decision"],
                metadata={
                    'mode': 'QUICK_JUDGMENT',
                    'suggested_action': 'SUPERSEDE',
                },
            )

        # High similarity but different cell = likely related but different
        if not same_cell:
            return ArbiterResult(
                verdict=ArbiterVerdict.DIFFERENT,
                confidence=0.7,
                reason="Similar content in different group/feature suggests related decisions",
                suggestions=["Consider adding as informed_by relation"],
                metadata={
                    'mode': 'QUICK_JUDGMENT',
                    'suggested_action': 'RELATE',
                },
            )

        # Default: uncertain, lean toward evolution in same cell
        return ArbiterResult(
            verdict=ArbiterVerdict.EVOLUTION,
            confidence=0.5,
            reason="Moderate similarity in same cell, defaulting to evolution",
            suggestions=["Review manually to confirm relationship"],
            metadata={
                'mode': 'QUICK_JUDGMENT',
                'suggested_action': 'SUPERSEDE',
            },
        )
