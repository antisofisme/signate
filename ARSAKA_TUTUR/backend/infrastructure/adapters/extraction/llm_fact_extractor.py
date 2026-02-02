"""
LLM-based Fact Extractor

Uses LLM to extract user facts from conversations.
"""

from typing import List, Optional
import json

from ....core.interfaces.extraction import FactExtractor
from ....core.interfaces.ai_providers import LLMProvider
from ....core.entities import ChatMessage, UserFact, ExtractedFact, FactType, Message
from ....shared.logging import get_logger

logger = get_logger(__name__)


FACT_EXTRACTION_PROMPT = """You are a fact extraction system. Analyze the conversation and extract factual information about the user.

Extract facts in these categories:
- PREFERENCE: User preferences, likes, dislikes (e.g., "prefers dark mode", "likes coffee")
- BEHAVIOR: User habits, patterns, workflows (e.g., "works late at night", "uses vim")
- CONTEXT: Background info, roles, projects (e.g., "works at TechCorp", "building an AI app")
- RELATIONSHIP: People, teams, organizations mentioned (e.g., "manager is Sarah", "on DevOps team")
- GENERAL: Other relevant facts

Rules:
1. Only extract facts explicitly stated or strongly implied
2. Use third person ("The user prefers..." not "I prefer...")
3. Be specific and concise
4. Assign confidence (0.0-1.0) based on how certain the fact is
5. Skip facts that are temporary or session-specific
6. Skip facts already in the existing facts list

Respond in JSON format:
{
  "facts": [
    {
      "fact_type": "PREFERENCE",
      "content": "The user prefers Python over JavaScript for backend development",
      "confidence": 0.9,
      "source_quote": "I always use Python for my APIs"
    }
  ]
}

If no new facts found, respond: {"facts": []}
"""


class LLMFactExtractor(FactExtractor):
    """
    LLM-based implementation of fact extraction.

    Uses a smaller, faster model for efficient extraction.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ):
        self.llm_provider = llm_provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def extract(
        self,
        messages: List[ChatMessage],
        existing_facts: List[UserFact]
    ) -> List[ExtractedFact]:
        """Extract new facts from conversation."""
        if not messages:
            return []

        # Format messages for the prompt
        conversation_text = self._format_conversation(messages)

        # Format existing facts
        existing_facts_text = self._format_existing_facts(existing_facts)

        # Build the prompt
        user_prompt = f"""## Existing Facts About This User
{existing_facts_text if existing_facts_text else "No existing facts."}

## Recent Conversation
{conversation_text}

## Task
Extract new facts from the conversation above. Do not duplicate existing facts."""

        # Call LLM
        try:
            result = await self.llm_provider.generate(
                messages=[
                    Message(role="system", content=FACT_EXTRACTION_PROMPT),
                    Message(role="user", content=user_prompt),
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            # Parse response
            facts = self._parse_response(result.content, messages)

            logger.debug(f"Extracted {len(facts)} facts from {len(messages)} messages")
            return facts

        except Exception as e:
            logger.error(f"Fact extraction failed: {e}")
            return []

    async def check_contradiction(
        self,
        new_fact: str,
        existing_facts: List[UserFact]
    ) -> List[str]:
        """Check if new fact contradicts existing facts."""
        if not existing_facts:
            return []

        existing_facts_text = self._format_existing_facts(existing_facts)

        prompt = f"""Determine if this new fact contradicts any existing facts.

## Existing Facts
{existing_facts_text}

## New Fact
{new_fact}

## Task
List the IDs of any facts that are contradicted by the new fact.
Only include facts that are directly contradicted, not just different.

Respond in JSON: {{"contradicted_ids": ["id1", "id2"]}}
If no contradictions: {{"contradicted_ids": []}}"""

        try:
            result = await self.llm_provider.generate(
                messages=[
                    Message(role="system", content="You are a fact verification system."),
                    Message(role="user", content=prompt),
                ],
                temperature=0.0,
                max_tokens=500,
            )

            # Parse response
            response_text = result.content.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            data = json.loads(response_text)
            return data.get("contradicted_ids", [])

        except Exception as e:
            logger.warning(f"Contradiction check failed: {e}")
            return []

    def _format_conversation(self, messages: List[ChatMessage]) -> str:
        """Format messages for the prompt."""
        lines = []
        for msg in messages[-20:]:  # Limit to recent messages
            role = "User" if msg.role.value == "user" else "Assistant"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def _format_existing_facts(self, facts: List[UserFact]) -> str:
        """Format existing facts for the prompt."""
        if not facts:
            return ""

        lines = []
        for fact in facts[:20]:  # Limit
            lines.append(f"- [{fact.id}] ({fact.fact_type.value}): {fact.content}")
        return "\n".join(lines)

    def _parse_response(
        self,
        response: str,
        source_messages: List[ChatMessage]
    ) -> List[ExtractedFact]:
        """Parse LLM response into ExtractedFact objects."""
        try:
            # Extract JSON from response
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            data = json.loads(response_text)
            facts_data = data.get("facts", [])

            facts = []
            for item in facts_data:
                try:
                    fact_type = FactType(item.get("fact_type", "GENERAL").upper())
                except ValueError:
                    fact_type = FactType.GENERAL

                # Find source message if quote provided
                source_message_id = None
                source_quote = item.get("source_quote", "")
                if source_quote:
                    for msg in source_messages:
                        if source_quote.lower() in msg.content.lower():
                            source_message_id = str(msg.id)
                            break

                facts.append(ExtractedFact(
                    fact_type=fact_type,
                    content=item.get("content", ""),
                    confidence=float(item.get("confidence", 0.8)),
                    source_message_id=source_message_id,
                    source_quote=source_quote,
                ))

            return facts

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse fact extraction response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing fact extraction response: {e}")
            return []


class BatchFactExtractor:
    """
    Batch processing wrapper for fact extraction.

    Handles multiple conversations efficiently.
    """

    def __init__(self, extractor: LLMFactExtractor):
        self.extractor = extractor

    async def extract_batch(
        self,
        conversations: List[tuple[List[ChatMessage], List[UserFact]]],
    ) -> List[List[ExtractedFact]]:
        """
        Extract facts from multiple conversations.

        Args:
            conversations: List of (messages, existing_facts) tuples

        Returns:
            List of extracted facts for each conversation
        """
        results = []
        for messages, existing_facts in conversations:
            facts = await self.extractor.extract(messages, existing_facts)
            results.append(facts)
        return results
