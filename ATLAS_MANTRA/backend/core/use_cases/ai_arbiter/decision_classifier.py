"""
AI Decision Classifier

Automatically classifies decisions into the correct Domain and Aspect
based on content analysis. Removes human error in categorization.

Per MANTRA-LAW-001:
- 4 Domains (INT, ARCH, CTL, EVO)
- 16 Aspects (A01-A16, 4 per domain)

This classifier analyzes statement + rationale to determine the best fit.

IMPORTANT: Response format is MINIMAL JSON only - no verbose explanations.
This minimizes token cost for both server-side and delegated AI modes.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


# ============================================================================
# Classification Taxonomy (embedded for prompt precision)
# ============================================================================

TAXONOMY_DEFINITION = """
DOMAIN-ASPECT TAXONOMY (4 Domains × 4 Aspects = 16 Categories):

INT (Intent & Direction) - Answers: WHY? WHAT?
├─ A01: Vision & Outcome - Long-term goals, desired end state, success metrics
├─ A02: Problem Statement - Pain points, current issues, motivation for change
├─ A03: Scope & Non-Goals - What's included/excluded, boundaries of concern
└─ A04: Principles & Values - Core beliefs, guiding philosophy, non-negotiables

ARCH (Architecture & Boundaries) - Answers: HOW? WHERE?
├─ A05: Domain & Bounded Context - Business domains, DDD contexts, ownership
├─ A06: Service & Module Boundary - Microservices, packages, component split
├─ A07: Data Ownership & Sovereignty - Who owns data, storage location, GDPR
└─ A08: Integration & Contract Model - APIs, protocols, inter-service contracts

CTL (Control, Policy & Risk) - Answers: CAN? MUST NOT?
├─ A09: Policy & Rules - Governance rules, coding standards, conventions
├─ A10: Approval & Authority Model - Who approves what, sign-off requirements
├─ A11: Security & Compliance Posture - Auth, encryption, audit, compliance
└─ A12: Risk & Blast Radius - Impact assessment, failure modes, mitigation

EVO (Execution & Evolution) - Answers: HOW TO CHANGE SAFELY?
├─ A13: Decision Lifecycle - How decisions evolve, versioning strategy
├─ A14: Reversibility & Exit Strategy - Rollback plans, migration paths
├─ A15: Environment & Promotion Rules - Dev/staging/prod, deployment gates
└─ A16: Anti-Drift & Consistency - Preventing deviation, enforcement methods
"""


# ============================================================================
# Classification Prompt (PRECISE, no ambiguity)
# ============================================================================

# NOTE: Using regular string (not f-string) with {placeholders} for .format()
# JSON braces must be doubled: {{ and }} to produce literal { and }
CLASSIFICATION_PROMPT = """You are a decision classifier for MANTRA (Decision Matrix System).

""" + TAXONOMY_DEFINITION + """

TASK: Classify the decision into exactly ONE domain and ONE aspect.

INPUT:
Statement: "{statement}"
Rationale: "{rationale}"
{constraints_section}

RULES:
1. Match the PRIMARY intent, not secondary aspects
2. If about "why we do this" → INT
3. If about "how/where to build" → ARCH
4. If about "what's allowed/forbidden" → CTL
5. If about "how to change safely" → EVO

OUTPUT FORMAT (JSON only, no explanation):
{{"domain_id": "INT|ARCH|CTL|EVO", "aspect_id": "A01-A16", "confidence": 0.0-1.0}}
"""


# ============================================================================
# Classification Result
# ============================================================================

@dataclass
class ClassificationResult:
    """Result of AI classification."""
    domain_id: str  # INT, ARCH, CTL, EVO
    aspect_id: str  # A01-A16
    confidence: float  # 0.0-1.0

    # For delegated mode: context needed by client AI
    delegated_prompt: Optional[str] = None
    requires_ai: bool = False


@dataclass
class ClassificationContext:
    """Context for delegated AI classification."""
    classification_type: str = "DECISION_CLASSIFICATION"
    prompt_template: str = ""
    statement: str = ""
    rationale: str = ""
    constraints_summary: str = ""
    taxonomy: str = TAXONOMY_DEFINITION


# ============================================================================
# Decision Classifier
# ============================================================================

class DecisionClassifier:
    """
    AI-powered decision classifier.

    Supports two modes:
    1. SERVER: MANTRA calls AI directly (costs MANTRA)
    2. DELEGATED: Returns context for client AI (costs user)
    """

    # Valid domains and their aspects
    VALID_DOMAINS = {"INT", "ARCH", "CTL", "EVO"}
    DOMAIN_ASPECTS = {
        "INT": ["A01", "A02", "A03", "A04"],
        "ARCH": ["A05", "A06", "A07", "A08"],
        "CTL": ["A09", "A10", "A11", "A12"],
        "EVO": ["A13", "A14", "A15", "A16"],
    }

    def __init__(self, ai_client=None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize classifier.

        Args:
            ai_client: Optional AI client for server-side classification
            model: Model to use (Haiku recommended for cost efficiency)
        """
        self.ai_client = ai_client
        self.model = model

    def build_prompt(
        self,
        statement: str,
        rationale: str,
        constraints: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build classification prompt with decision content."""

        # Format constraints if provided
        constraints_section = ""
        if constraints:
            constraint_texts = []
            for c in constraints[:3]:  # Limit to 3 for token efficiency
                c_type = c.get('type', 'REQUIREMENT')
                c_stmt = c.get('statement', '')[:100]  # Truncate long statements
                constraint_texts.append(f"- [{c_type}] {c_stmt}")
            if constraint_texts:
                constraints_section = f"Constraints:\n" + "\n".join(constraint_texts)

        return CLASSIFICATION_PROMPT.format(
            statement=statement[:500],  # Truncate for token efficiency
            rationale=rationale[:500],
            constraints_section=constraints_section
        )

    def get_delegated_context(
        self,
        statement: str,
        rationale: str,
        constraints: Optional[List[Dict[str, Any]]] = None
    ) -> ClassificationContext:
        """
        Get context for delegated AI classification.

        Use this when the client has their own AI (e.g., Claude Code via MCP).
        This returns all context needed for the client AI to perform classification.
        """
        constraints_summary = ""
        if constraints:
            constraints_summary = "; ".join([
                f"[{c.get('type', 'REQ')}] {c.get('statement', '')[:50]}"
                for c in constraints[:3]
            ])

        return ClassificationContext(
            classification_type="DECISION_CLASSIFICATION",
            prompt_template=self.build_prompt(statement, rationale, constraints),
            statement=statement,
            rationale=rationale,
            constraints_summary=constraints_summary,
            taxonomy=TAXONOMY_DEFINITION,
        )

    async def classify_server_side(
        self,
        statement: str,
        rationale: str,
        constraints: Optional[List[Dict[str, Any]]] = None
    ) -> ClassificationResult:
        """
        Classify decision using server-side AI.

        COST: MANTRA pays for this API call.
        Use only when client has no AI (e.g., web UI).
        """
        if not self.ai_client:
            # Fallback: Return requires_ai=True for manual classification
            return ClassificationResult(
                domain_id="",
                aspect_id="",
                confidence=0.0,
                requires_ai=True,
                delegated_prompt=self.build_prompt(statement, rationale, constraints)
            )

        prompt = self.build_prompt(statement, rationale, constraints)

        try:
            # Call AI (implementation depends on client)
            response = await self._call_ai(prompt)
            return self._parse_response(response)
        except Exception as e:
            # On error, return for manual/delegated classification
            return ClassificationResult(
                domain_id="",
                aspect_id="",
                confidence=0.0,
                requires_ai=True,
                delegated_prompt=prompt
            )

    async def _call_ai(self, prompt: str) -> str:
        """Call AI client. Override for specific client implementation."""
        if not self.ai_client:
            raise ValueError("No AI client configured")

        # Generic implementation - subclass for specific clients
        # This supports both OpenAI and Anthropic style clients
        if hasattr(self.ai_client, 'messages'):
            # Anthropic style
            response = await self.ai_client.messages.create(
                model=self.model,
                max_tokens=100,  # Minimal - just need JSON
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        elif hasattr(self.ai_client, 'chat'):
            # OpenAI style
            response = await self.ai_client.chat.completions.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        else:
            raise ValueError("Unsupported AI client type")

    def _parse_response(self, response: str) -> ClassificationResult:
        """Parse AI response into ClassificationResult."""
        import json
        import re

        # Try to extract JSON from response
        try:
            # Clean response - find JSON object
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            domain_id = data.get('domain_id', '').upper()
            aspect_id = data.get('aspect_id', '').upper()
            confidence = float(data.get('confidence', 0.5))

            # Validate
            if domain_id not in self.VALID_DOMAINS:
                return self._fallback_result()

            if aspect_id not in self.DOMAIN_ASPECTS.get(domain_id, []):
                return self._fallback_result()

            return ClassificationResult(
                domain_id=domain_id,
                aspect_id=aspect_id,
                confidence=confidence
            )

        except (json.JSONDecodeError, KeyError, ValueError):
            return self._fallback_result()

    def _fallback_result(self) -> ClassificationResult:
        """Return fallback when parsing fails."""
        return ClassificationResult(
            domain_id="",
            aspect_id="",
            confidence=0.0,
            requires_ai=True
        )

    def validate_classification(
        self,
        domain_id: str,
        aspect_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a classification (from delegated AI or user).

        Returns: (is_valid, error_message)
        """
        if domain_id not in self.VALID_DOMAINS:
            return False, f"Invalid domain_id: {domain_id}. Must be one of: {self.VALID_DOMAINS}"

        valid_aspects = self.DOMAIN_ASPECTS.get(domain_id, [])
        if aspect_id not in valid_aspects:
            return False, f"Aspect {aspect_id} not compatible with domain {domain_id}. Valid aspects: {valid_aspects}"

        return True, None


# ============================================================================
# Convenience Functions
# ============================================================================

def get_classification_context(
    statement: str,
    rationale: str,
    constraints: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Get classification context for delegated AI mode.

    Returns dict ready for API response.
    """
    classifier = DecisionClassifier()
    ctx = classifier.get_delegated_context(statement, rationale, constraints)

    return {
        "classification_required": True,
        "classification_type": ctx.classification_type,
        "prompt": ctx.prompt_template,
        "taxonomy": ctx.taxonomy,
        "expected_response": {
            "format": "JSON",
            "schema": {
                "domain_id": "INT|ARCH|CTL|EVO",
                "aspect_id": "A01-A16",
                "confidence": "0.0-1.0"
            }
        }
    }


def validate_classification_result(
    domain_id: str,
    aspect_id: str
) -> tuple[bool, Optional[str]]:
    """Validate classification result from any source."""
    classifier = DecisionClassifier()
    return classifier.validate_classification(domain_id, aspect_id)
