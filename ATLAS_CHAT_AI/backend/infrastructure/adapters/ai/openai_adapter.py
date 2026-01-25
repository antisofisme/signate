"""
OpenAI Adapter

Implements LLMProvider and EmbeddingProvider interfaces for OpenAI.
"""

from typing import Optional, List, AsyncIterator

from openai import AsyncOpenAI

from ....core.interfaces import LLMProvider, EmbeddingProvider
from ....core.entities import Message, GenerationResult
from ....config import OpenAIConfig, get_settings
from ....shared.logging import get_logger
from ....shared.exceptions import ExternalServiceError

logger = get_logger(__name__)


class OpenAIEmbeddingAdapter(EmbeddingProvider):
    """
    OpenAI implementation of EmbeddingProvider.

    Supports text-embedding-3-small and text-embedding-3-large.
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        self.config = config or get_settings().openai
        self._client: Optional[AsyncOpenAI] = None
        self._model = self.config.embedding_model
        self._dimensions = self.config.embedding_dimensions

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                organization=self.config.organization,
            )
        return self._client

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> List[float]:
        """
        Embed single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        client = self._get_client()

        try:
            response = await client.embeddings.create(
                model=self._model,
                input=text,
                dimensions=self._dimensions,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise ExternalServiceError(
                service="openai",
                message="Failed to generate embedding",
                original_error=str(e),
            )

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Embed multiple texts.

        Args:
            texts: List of texts
            batch_size: Batch size for API calls

        Returns:
            List of embedding vectors
        """
        client = self._get_client()
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                response = await client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                )

                # Sort by index to maintain order
                batch_embeddings = sorted(response.data, key=lambda x: x.index)
                embeddings.extend([e.embedding for e in batch_embeddings])

            except Exception as e:
                logger.error(f"OpenAI batch embedding error: {e}")
                raise ExternalServiceError(
                    service="openai",
                    message="Failed to generate batch embeddings",
                    original_error=str(e),
                )

        return embeddings


class OpenAILLMAdapter(LLMProvider):
    """
    OpenAI implementation of LLMProvider.

    Supports GPT-4, GPT-4o, GPT-4o-mini, etc.
    """

    def __init__(
        self,
        config: Optional[OpenAIConfig] = None,
        model: Optional[str] = None
    ):
        self.config = config or get_settings().openai
        self._client: Optional[AsyncOpenAI] = None
        self._model = model or self.config.default_model

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                organization=self.config.organization,
            )
        return self._client

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stop: Optional[List[str]] = None
    ) -> GenerationResult:
        """
        Generate completion.

        Args:
            messages: List of Message (role, content)
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            stop: Stop sequences

        Returns:
            GenerationResult with content and token counts
        """
        client = self._get_client()

        # Convert to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
            )

            choice = response.choices[0]
            usage = response.usage

            return GenerationResult(
                content=choice.message.content or "",
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                model=response.model,
                finish_reason=choice.finish_reason or "stop",
                metadata={
                    "id": response.id,
                    "created": response.created,
                },
            )

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise ExternalServiceError(
                service="openai",
                message="Failed to generate completion",
                original_error=str(e),
            )

    async def stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        """
        Stream completion token by token.

        Args:
            messages: List of Message
            temperature: Sampling temperature
            max_tokens: Max tokens

        Yields:
            Token strings as they're generated
        """
        client = self._get_client()

        # Convert to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        try:
            stream = await client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise ExternalServiceError(
                service="openai",
                message="Failed to stream completion",
                original_error=str(e),
            )
