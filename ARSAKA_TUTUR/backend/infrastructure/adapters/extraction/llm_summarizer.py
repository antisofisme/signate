"""
LLM-based Summarizer

Uses LLM to summarize conversations and extract topics.
"""

from typing import List, Optional
import json

from ....core.interfaces.extraction import Summarizer
from ....core.interfaces.ai_providers import LLMProvider
from ....core.entities import ChatMessage, Message
from ....shared.logging import get_logger

logger = get_logger(__name__)


SUMMARIZE_PROMPT = """You are a conversation summarizer. Create a concise summary of the conversation.

Guidelines:
1. Focus on key topics, decisions, and outcomes
2. Include any tasks or action items discussed
3. Preserve important context that would be useful for future reference
4. Write in third person (e.g., "The user discussed..." not "You discussed...")
5. Keep the summary concise but informative

Format: Plain text summary, no bullet points or headers unless necessary."""


INCREMENTAL_SUMMARIZE_PROMPT = """You are a conversation summarizer. Update the existing summary with new information.

Guidelines:
1. Incorporate new information into the existing summary
2. Remove outdated information if superseded
3. Keep the summary concise - aim for the same length as the original
4. Maintain important context from the original summary
5. Write in third person

Existing Summary:
{previous_summary}

New Messages:
{new_messages}

Provide an updated summary that incorporates the new information."""


TOPIC_EXTRACTION_PROMPT = """Extract the main topics from this conversation.

Guidelines:
1. Identify 1-5 main topics discussed
2. Use short, descriptive phrases (2-4 words)
3. Focus on substantive topics, not small talk
4. Order by importance/relevance

Respond in JSON: {"topics": ["topic1", "topic2", ...]}"""


class LLMSummarizer(Summarizer):
    """
    LLM-based implementation of conversation summarization.

    Features:
    - Full conversation summarization
    - Incremental summary updates
    - Topic extraction
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ):
        self.llm_provider = llm_provider
        self.model = model
        self.temperature = temperature

    async def summarize(
        self,
        messages: List[ChatMessage],
        max_length: int = 500
    ) -> str:
        """Create summary of conversation."""
        if not messages:
            return ""

        # Format conversation
        conversation_text = self._format_conversation(messages)

        prompt = f"""{SUMMARIZE_PROMPT}

Target length: approximately {max_length // 4} words.

Conversation:
{conversation_text}"""

        try:
            result = await self.llm_provider.generate(
                messages=[
                    Message(role="system", content="You are a helpful summarizer."),
                    Message(role="user", content=prompt),
                ],
                temperature=self.temperature,
                max_tokens=max_length,
            )

            summary = result.content.strip()
            logger.debug(f"Generated summary of {len(summary)} chars from {len(messages)} messages")
            return summary

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return self._fallback_summary(messages)

    async def summarize_incremental(
        self,
        previous_summary: str,
        new_messages: List[ChatMessage],
        max_length: int = 500
    ) -> str:
        """Update existing summary with new messages."""
        if not new_messages:
            return previous_summary

        if not previous_summary:
            return await self.summarize(new_messages, max_length)

        # Format new messages
        new_messages_text = self._format_conversation(new_messages)

        prompt = INCREMENTAL_SUMMARIZE_PROMPT.format(
            previous_summary=previous_summary,
            new_messages=new_messages_text,
        )

        prompt += f"\n\nTarget length: approximately {max_length // 4} words."

        try:
            result = await self.llm_provider.generate(
                messages=[
                    Message(role="system", content="You are a helpful summarizer."),
                    Message(role="user", content=prompt),
                ],
                temperature=self.temperature,
                max_tokens=max_length,
            )

            summary = result.content.strip()
            logger.debug(f"Updated summary with {len(new_messages)} new messages")
            return summary

        except Exception as e:
            logger.error(f"Incremental summarization failed: {e}")
            # Fallback: append simple summary of new messages
            new_summary = self._fallback_summary(new_messages)
            return f"{previous_summary}\n\nUpdate: {new_summary}"

    async def extract_topics(
        self,
        messages: List[ChatMessage],
        max_topics: int = 5
    ) -> List[str]:
        """Extract main topics from conversation."""
        if not messages:
            return []

        conversation_text = self._format_conversation(messages)

        prompt = f"""{TOPIC_EXTRACTION_PROMPT}

Maximum topics: {max_topics}

Conversation:
{conversation_text}"""

        try:
            result = await self.llm_provider.generate(
                messages=[
                    Message(role="system", content="You extract topics from conversations."),
                    Message(role="user", content=prompt),
                ],
                temperature=0.1,
                max_tokens=200,
            )

            # Parse response
            topics = self._parse_topics(result.content)
            logger.debug(f"Extracted {len(topics)} topics from {len(messages)} messages")
            return topics[:max_topics]

        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return []

    def _format_conversation(self, messages: List[ChatMessage]) -> str:
        """Format messages for the prompt."""
        lines = []
        for msg in messages[-50:]:  # Limit to recent messages
            role = "User" if msg.role.value == "user" else "Assistant"
            content = msg.content[:1000]  # Truncate long messages
            if len(msg.content) > 1000:
                content += "..."
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _parse_topics(self, response: str) -> List[str]:
        """Parse topics from LLM response."""
        try:
            # Extract JSON
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            data = json.loads(response_text)
            topics = data.get("topics", [])

            # Clean up topics
            cleaned = []
            for topic in topics:
                if isinstance(topic, str) and topic.strip():
                    cleaned.append(topic.strip())

            return cleaned

        except json.JSONDecodeError:
            # Fallback: try to extract topics from plain text
            logger.warning("Failed to parse JSON topics, using fallback")
            return self._extract_topics_fallback(response)

    def _extract_topics_fallback(self, response: str) -> List[str]:
        """Fallback topic extraction from plain text."""
        topics = []

        # Try to find bulleted or numbered items
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Remove bullets/numbers
            for prefix in ["- ", "* ", "• "]:
                if line.startswith(prefix):
                    line = line[len(prefix):]
                    break

            # Remove numbered prefixes
            if line[0].isdigit() and (line[1] == "." or line[1] == ")"):
                line = line[2:].strip()
            elif len(line) > 2 and line[0].isdigit() and line[1].isdigit() and (line[2] == "." or line[2] == ")"):
                line = line[3:].strip()

            if line and len(line) < 50:  # Reasonable topic length
                topics.append(line)

        return topics[:5]

    def _fallback_summary(self, messages: List[ChatMessage]) -> str:
        """Simple fallback summary when LLM fails."""
        if not messages:
            return ""

        user_messages = [m for m in messages if m.role.value == "user"]

        if not user_messages:
            return "Conversation with assistant."

        # Take first and last user messages
        summary_parts = []

        if user_messages:
            first_msg = user_messages[0].content[:100]
            summary_parts.append(f"Started with: {first_msg}")

        if len(user_messages) > 1:
            last_msg = user_messages[-1].content[:100]
            summary_parts.append(f"Ended with: {last_msg}")

        summary_parts.append(f"Total messages: {len(messages)}")

        return " | ".join(summary_parts)


class SessionSummarizer:
    """
    High-level session summarization helper.

    Combines summarization with topic extraction.
    """

    def __init__(self, summarizer: LLMSummarizer):
        self.summarizer = summarizer

    async def summarize_session(
        self,
        messages: List[ChatMessage],
        existing_summary: Optional[str] = None,
        max_length: int = 500,
    ) -> dict:
        """
        Generate complete session summary with topics.

        Returns:
            {
                "summary": str,
                "topics": List[str],
                "message_count": int,
            }
        """
        if existing_summary:
            summary = await self.summarizer.summarize_incremental(
                previous_summary=existing_summary,
                new_messages=messages,
                max_length=max_length,
            )
        else:
            summary = await self.summarizer.summarize(
                messages=messages,
                max_length=max_length,
            )

        topics = await self.summarizer.extract_topics(messages)

        return {
            "summary": summary,
            "topics": topics,
            "message_count": len(messages),
        }
