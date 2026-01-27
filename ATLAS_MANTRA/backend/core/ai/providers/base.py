"""
Base AI Provider Interface

All AI providers must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ChatMessage:
    """Single chat message."""
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class ChatResponse:
    """Response from AI provider."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None  # tokens used


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All providers (OpenAI, DeepSeek, Groq, etc.) must implement this interface.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> ChatResponse:
        """
        Send chat messages and get response.

        Args:
            messages: List of chat messages
            system_prompt: Optional system prompt (prepended to messages)

        Returns:
            ChatResponse with AI's response
        """
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> ChatResponse:
        """
        Simple completion (single prompt).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            ChatResponse with AI's response
        """
        pass

    def _prepare_messages(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Convert ChatMessage list to API format."""
        result = []

        if system_prompt:
            result.append({"role": "system", "content": system_prompt})

        for msg in messages:
            result.append({"role": msg.role, "content": msg.content})

        return result
