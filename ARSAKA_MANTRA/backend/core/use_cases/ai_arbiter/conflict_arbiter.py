"""
Conflict Arbiter for Medium-Severity Conflicts

Handles conflicts with ambiguous severity that need AI judgment.
- CRITICAL conflicts: Automatically block (no AI needed)
- LOW conflicts: Automatically warn (no AI needed)
- MEDIUM conflicts: AI arbitration to determine real severity

Verdicts:
- BLOCKING: Real conflict, cannot coexist
- WARNING: Potential tension, can coexist with caution
- NOT_CONFLICT: False positive, no real conflict
"""

from typing import Any, Dict, List

from .base import (
    BaseArbiter,
    ArbiterVerdict,
    ArbiterResult,
    ArbitrationType,
    ArbitrationContext,
)


class ConflictArbiter(BaseArbiter):
    """Arbitrate medium-severity conflicts."""

    @property
    def arbitration_type(self) -> ArbitrationType:
        return ArbitrationType.CONFLICT

    def should_invoke(self, context: Dict[str, Any]) -> bool:
        """
        Check if there are medium-severity conflicts.

        Args:
            context: Must contain 'conflicts' list with severity levels

        Returns:
            True if any MEDIUM severity conflict exists
        """
        conflicts = context.get('conflicts', [])
        return any(c.get('severity') == 'MEDIUM' for c in conflicts)

    def generate_context(self, context: Dict[str, Any]) -> ArbitrationContext:
        """
        Generate context for delegated conflict arbitration.

        The prompt asks the client AI to evaluate if the conflict
        is real (blocking) or a false positive.
        """
        new_statement = context.get('new_statement', '')
        new_rationale = context.get('new_rationale', '')
        conflict = context.get('conflict', {})

        keywords = ', '.join(conflict.get('keywords', []))

        prompt = f"""Evaluate potential conflict between two decisions.

NEW: "{new_statement}"
EXISTING ({conflict.get('code', '?')}): "{conflict.get('statement', '')}"

CONFLICT DETECTED:
• Type: {conflict.get('type', 'Unknown')}
• Keywords: {keywords}
• {conflict.get('description', '')}

Return JSON:
{{"verdict": "BLOCKING|WARNING|NOT_CONFLICT", "confidence": 0.0-1.0, "reason": "1-2 sentences", "resolution": "if BLOCKING/WARNING"}}

BLOCKING = Mutually exclusive (e.g., "use X" vs "use Y" for same purpose)
WARNING = Tension exists but can coexist with documentation
NOT_CONFLICT = Keyword match but semantically different contexts"""

        return ArbitrationContext(
            arbitration_type=ArbitrationType.CONFLICT,
            prompt_template=prompt,
            context_data={
                'new_statement': new_statement,
                'new_rationale': new_rationale,
                'conflict': conflict,
            },
            expected_verdicts=['BLOCKING', 'WARNING', 'NOT_CONFLICT'],
            instructions="BLOCKING→stop, WARNING→allow+caution, NOT_CONFLICT→ignore",
        )

    async def arbitrate(self, context: Dict[str, Any]) -> ArbiterResult:
        """
        Perform server-side conflict arbitration.

        Note: This requires API key and is not the recommended mode.
        Use DELEGATED mode for cost efficiency.
        """
        arb_context = self.generate_context(context)
        response = await self._call_ai(arb_context.prompt_template)
        return self._parse_response(response)

    def quick_judgment(self, context: Dict[str, Any]) -> ArbiterResult:
        """
        Quick rule-based judgment for when AI is unavailable.

        Uses heuristics based on conflict type and keywords.
        """
        conflict = context.get('conflict', {})
        conflict_type = conflict.get('type', '')
        keywords = conflict.get('keywords', [])

        # Pattern conflicts (sync vs async) are usually just style differences
        if conflict_type == 'pattern_conflict':
            if 'sync' in keywords and 'async' in keywords:
                return ArbiterResult(
                    verdict=ArbiterVerdict.WARNING,
                    confidence=0.6,
                    reason="Sync vs async is often a valid architectural choice, not a conflict",
                    suggestions=["Document when to use each pattern"],
                    metadata={'mode': 'QUICK_JUDGMENT'},
                )

        # Scope overlap in same cell is concerning
        if conflict_type == 'scope_overlap':
            return ArbiterResult(
                verdict=ArbiterVerdict.WARNING,
                confidence=0.7,
                reason="Scope overlap may indicate duplicate coverage",
                suggestions=["Consider using supersedes relationship"],
                metadata={'mode': 'QUICK_JUDGMENT'},
            )

        # Technology conflicts are often real
        if conflict_type == 'tech_conflict':
            return ArbiterResult(
                verdict=ArbiterVerdict.WARNING,
                confidence=0.7,
                reason="Technology choice conflicts may cause integration issues",
                suggestions=["Clarify which technology applies in which context"],
                metadata={'mode': 'QUICK_JUDGMENT'},
            )

        # Default: warn but allow
        return ArbiterResult(
            verdict=ArbiterVerdict.WARNING,
            confidence=0.5,
            reason="Potential conflict detected, requires manual review",
            suggestions=["Review both decisions to ensure compatibility"],
            metadata={'mode': 'QUICK_JUDGMENT'},
        )

    def arbitrate_multiple(
        self,
        context: Dict[str, Any],
        conflicts: List[Dict[str, Any]]
    ) -> List[ArbiterResult]:
        """
        Arbitrate multiple conflicts at once.

        Returns a list of results, one per conflict.
        """
        results = []
        for conflict in conflicts:
            if conflict.get('severity') == 'MEDIUM':
                ctx = {**context, 'conflict': conflict}
                results.append(self.quick_judgment(ctx))
            else:
                # Non-MEDIUM conflicts don't need arbitration
                results.append(None)
        return results
