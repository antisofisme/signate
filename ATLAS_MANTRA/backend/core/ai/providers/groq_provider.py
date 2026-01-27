"""
Groq Provider Implementation

Uses Groq API (OpenAI-compatible, ultra-fast inference)
"""

import httpx
from typing import List, Optional

from .base import AIProvider, ChatMessage, ChatResponse


class GroqProvider(AIProvider):
    """Groq API provider."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override default model for Groq
        if self.model.startswith("gpt"):
            self.model = "llama-3.1-70b-versatile"

    @property
    def provider_name(self) -> str:
        return "groq"

    async def chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> ChatResponse:
        """Send chat messages to Groq API."""
        prepared_messages = self._prepare_messages(messages, system_prompt)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": prepared_messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )

            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"Groq API error ({response.status_code}): {error_text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            return ChatResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                usage=usage,
            )

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> ChatResponse:
        """Simple completion using chat API."""
        messages = [ChatMessage(role="user", content=prompt)]
        return await self.chat(messages, system_prompt)
