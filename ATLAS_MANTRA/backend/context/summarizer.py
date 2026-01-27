"""
MICS Content Summarizer

Generates token-efficient summaries for decisions.
Used for:
- Auto-generating content_summary field
- Micro-level context injection
- Quick reference in AI prompts

Summary Strategy:
- Extract key decision intent
- Preserve technical terminology
- Compress to ~50-100 words
- Maintain actionable clarity
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContentSummary:
    """Generated content summary."""
    summary: str
    word_count: int
    estimated_tokens: int
    key_terms: List[str]
    compression_ratio: float


class ContentSummarizer:
    """
    Generates token-efficient summaries for MANTRA decisions.

    Used to populate content_summary field for Layer A.
    Enables micro-level context injection (~100 tokens).
    """

    # Important technical terms to preserve
    PRESERVE_TERMS = {
        # Patterns
        'repository', 'factory', 'singleton', 'strategy', 'observer',
        'microservice', 'monolith', 'event-driven', 'cqrs', 'saga',
        # Technologies
        'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes',
        'react', 'vue', 'angular', 'fastapi', 'django', 'express',
        'jwt', 'oauth', 'rbac', 'acl', 'ssl', 'tls',
        # Actions
        'must', 'shall', 'should', 'cannot', 'prohibited', 'required',
        # Scopes
        'organization', 'domain', 'application', 'service', 'component',
    }

    # Words to remove for compression
    FILLER_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'can', 'this',
        'that', 'these', 'those', 'it', 'its', 'which', 'who', 'whom',
        'very', 'really', 'just', 'quite', 'rather', 'somewhat',
        'however', 'therefore', 'moreover', 'furthermore', 'additionally',
    }

    def __init__(self, max_words: int = 75, max_tokens: int = 100):
        """
        Initialize summarizer.

        Args:
            max_words: Maximum words in summary
            max_tokens: Maximum estimated tokens
        """
        self.max_words = max_words
        self.max_tokens = max_tokens

    def summarize(self, decision: Dict[str, Any]) -> ContentSummary:
        """
        Generate summary for a decision.

        Args:
            decision: Decision record dict

        Returns:
            ContentSummary with summary text and metadata
        """
        statement = decision.get('statement', '')
        rationale = decision.get('rationale', '')
        constraints = decision.get('constraints', [])

        # Extract key components
        key_terms = self._extract_key_terms(statement, rationale)
        core_statement = self._compress_statement(statement)
        core_rationale = self._compress_rationale(rationale)
        core_constraints = self._compress_constraints(constraints)

        # Build summary
        parts = [core_statement]
        if core_rationale:
            parts.append(core_rationale)
        if core_constraints:
            parts.append(core_constraints)

        summary = ' '.join(parts)

        # Ensure within limits
        summary = self._enforce_limits(summary)

        # Calculate metrics
        word_count = len(summary.split())
        estimated_tokens = self._estimate_tokens(summary)
        original_words = len(f"{statement} {rationale}".split())
        compression_ratio = word_count / original_words if original_words > 0 else 1.0

        return ContentSummary(
            summary=summary,
            word_count=word_count,
            estimated_tokens=estimated_tokens,
            key_terms=key_terms,
            compression_ratio=compression_ratio
        )

    def _extract_key_terms(self, statement: str, rationale: str) -> List[str]:
        """Extract important technical terms."""
        text = f"{statement} {rationale}".lower()
        words = set(re.findall(r'\b\w+\b', text))
        key_terms = [w for w in words if w in self.PRESERVE_TERMS]
        return key_terms[:10]  # Limit to top 10

    def _compress_statement(self, statement: str) -> str:
        """Compress statement to core message."""
        if not statement:
            return ""

        # Remove filler words but preserve structure
        words = statement.split()
        compressed = []

        for word in words:
            word_lower = word.lower().strip('.,;:')
            if word_lower in self.PRESERVE_TERMS:
                compressed.append(word)
            elif word_lower not in self.FILLER_WORDS:
                compressed.append(word)
            elif len(compressed) == 0:
                # Keep first word even if filler
                compressed.append(word)

        result = ' '.join(compressed)

        # Limit to ~30 words
        words = result.split()
        if len(words) > 30:
            result = ' '.join(words[:30]) + '...'

        return result

    def _compress_rationale(self, rationale: str) -> str:
        """Compress rationale to key justification."""
        if not rationale:
            return ""

        # Find key explanation patterns
        patterns = [
            r'because\s+(.{20,100}?)(?:\.|$)',
            r'enables?\s+(.{20,80}?)(?:\.|$)',
            r'provides?\s+(.{20,80}?)(?:\.|$)',
            r'ensures?\s+(.{20,80}?)(?:\.|$)',
            r'prevents?\s+(.{20,80}?)(?:\.|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, rationale, re.IGNORECASE)
            if match:
                key_reason = match.group(1).strip()
                return f"({key_reason})"

        # Fallback: first sentence, truncated
        first_sentence = rationale.split('.')[0]
        if len(first_sentence) > 80:
            first_sentence = first_sentence[:80] + '...'
        return f"({first_sentence})"

    def _compress_constraints(self, constraints: List[Any]) -> str:
        """Compress constraints to brief list."""
        if not constraints:
            return ""

        # Extract first 2 constraint statements
        stmts = []
        for c in constraints[:2]:
            if isinstance(c, dict):
                stmt = c.get('statement', '')
            else:
                stmt = getattr(c, 'statement', str(c))

            # Compress constraint statement
            words = stmt.split()
            if len(words) > 10:
                stmt = ' '.join(words[:10]) + '...'
            stmts.append(stmt)

        if stmts:
            return f"Constraints: {'; '.join(stmts)}"
        return ""

    def _enforce_limits(self, summary: str) -> str:
        """Ensure summary is within word/token limits."""
        words = summary.split()

        if len(words) > self.max_words:
            # Truncate while preserving sentence structure
            truncated = words[:self.max_words]
            summary = ' '.join(truncated)
            if not summary.endswith(('.', '...', '?', '!')):
                summary += '...'

        return summary

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (~4 chars per token)."""
        return len(text) // 4


def generate_content_summary(decision: Dict[str, Any]) -> str:
    """
    Generate content summary for a decision.

    Convenience function for direct use.

    Args:
        decision: Decision record dict

    Returns:
        Summary string
    """
    summarizer = ContentSummarizer()
    result = summarizer.summarize(decision)
    return result.summary


def batch_generate_summaries(decisions: List[Dict[str, Any]]) -> List[ContentSummary]:
    """
    Generate summaries for multiple decisions.

    Args:
        decisions: List of decision records

    Returns:
        List of ContentSummary objects
    """
    summarizer = ContentSummarizer()
    return [summarizer.summarize(d) for d in decisions]


def update_decision_summary(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update decision with auto-generated summary.

    Modifies decision in place and returns it.

    Args:
        decision: Decision record dict

    Returns:
        Updated decision dict with content_summary
    """
    if not decision.get('content_summary'):
        decision['content_summary'] = generate_content_summary(decision)
    return decision
