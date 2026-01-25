"""
Extraction interfaces for fact extraction and summarization.
"""

from abc import ABC, abstractmethod
from typing import List

from ..entities import ChatMessage, UserFact, ExtractedFact


class FactExtractor(ABC):
    """
    Interface for extracting facts from conversations.

    Implementations: LLMFactExtractor
    """

    @abstractmethod
    async def extract(
        self,
        messages: List[ChatMessage],
        existing_facts: List[UserFact]
    ) -> List[ExtractedFact]:
        """
        Extract new facts from conversation.

        Args:
            messages: Recent conversation messages
            existing_facts: User's existing facts (to avoid duplicates)

        Returns:
            List of ExtractedFact for storage
        """
        pass

    @abstractmethod
    async def check_contradiction(
        self,
        new_fact: str,
        existing_facts: List[UserFact]
    ) -> List[str]:
        """
        Check if new fact contradicts existing facts.

        Args:
            new_fact: New fact content
            existing_facts: User's existing facts

        Returns:
            List of contradicted fact IDs
        """
        pass


class Summarizer(ABC):
    """
    Interface for conversation summarization.

    Implementations: LLMSummarizer
    """

    @abstractmethod
    async def summarize(
        self,
        messages: List[ChatMessage],
        max_length: int = 500
    ) -> str:
        """
        Create summary of conversation.

        Args:
            messages: Conversation messages
            max_length: Max summary length in tokens

        Returns:
            Summary text
        """
        pass

    @abstractmethod
    async def summarize_incremental(
        self,
        previous_summary: str,
        new_messages: List[ChatMessage],
        max_length: int = 500
    ) -> str:
        """
        Update existing summary with new messages.

        More efficient than re-summarizing entire conversation.

        Args:
            previous_summary: Existing summary
            new_messages: New messages since last summary
            max_length: Max summary length

        Returns:
            Updated summary
        """
        pass

    @abstractmethod
    async def extract_topics(
        self,
        messages: List[ChatMessage],
        max_topics: int = 5
    ) -> List[str]:
        """
        Extract main topics from conversation.

        Args:
            messages: Conversation messages
            max_topics: Max topics to extract

        Returns:
            List of topic strings
        """
        pass
