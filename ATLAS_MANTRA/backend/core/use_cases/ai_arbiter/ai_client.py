"""
Multi-Provider AI Client for Server-side Arbitration

Supports multiple AI providers with unified interface:
- Anthropic (Claude)
- OpenAI (GPT-4, GPT-3.5)
- DeepSeek
- Groq
- xAI (Grok)
- OpenRouter (aggregator for multiple models)

IMPORTANT: AI is NOT called for every validation!
AI arbitration is ONLY invoked when:
1. Quality score is borderline (50-80) - needs judgment
2. Near-duplicate detected (85-95%) - needs classification
3. Medium-severity conflict - needs resolution

This saves cost by avoiding unnecessary AI calls.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class AIProvider(str, Enum):
    """Supported AI providers."""
    ANTHROPIC = "anthropic"      # Claude models
    OPENAI = "openai"            # GPT models
    DEEPSEEK = "deepseek"        # DeepSeek models
    GROQ = "groq"                # Groq (fast inference)
    XAI = "xai"                  # xAI Grok models
    OPENROUTER = "openrouter"    # OpenRouter (multi-model aggregator)


# Provider configurations
PROVIDER_CONFIGS = {
    AIProvider.ANTHROPIC: {
        "base_url": None,  # Uses SDK default
        "default_model": "claude-3-haiku-20240307",
        "env_key": "ANTHROPIC_API_KEY",
        "api_style": "anthropic",
    },
    AIProvider.OPENAI: {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "api_style": "openai",
    },
    AIProvider.DEEPSEEK: {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "api_style": "openai",  # OpenAI-compatible
    },
    AIProvider.GROQ: {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.1-70b-versatile",
        "env_key": "GROQ_API_KEY",
        "api_style": "openai",  # OpenAI-compatible
    },
    AIProvider.XAI: {
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-beta",
        "env_key": "XAI_API_KEY",
        "api_style": "openai",  # OpenAI-compatible
    },
    AIProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-3-haiku",
        "env_key": "OPENROUTER_API_KEY",
        "api_style": "openai",  # OpenAI-compatible
        "extra_headers": {
            "HTTP-Referer": "https://mantra.atlas.dev",
            "X-Title": "MANTRA Validator",
        },
    },
}


@dataclass
class AIConfig:
    """Configuration for AI client."""
    provider: AIProvider = AIProvider.ANTHROPIC
    api_key: Optional[str] = None
    model: Optional[str] = None  # None = use provider default
    base_url: Optional[str] = None  # None = use provider default
    max_tokens: int = 500
    temperature: float = 0.3  # Low for consistent judgments
    timeout: int = 30  # seconds

    def __post_init__(self):
        """Set defaults based on provider."""
        provider_config = PROVIDER_CONFIGS.get(self.provider, {})

        if not self.model:
            self.model = provider_config.get("default_model", "gpt-4o-mini")

        if not self.base_url:
            self.base_url = provider_config.get("base_url")

    @classmethod
    def from_env(cls) -> 'AIConfig':
        """Load configuration from environment variables."""
        provider_str = os.getenv("AI_PROVIDER", "anthropic").lower()
        try:
            provider = AIProvider(provider_str)
        except ValueError:
            provider = AIProvider.ANTHROPIC

        provider_config = PROVIDER_CONFIGS.get(provider, {})
        env_key = provider_config.get("env_key", "AI_API_KEY")

        return cls(
            provider=provider,
            api_key=os.getenv(env_key) or os.getenv("AI_API_KEY"),
            model=os.getenv("AI_MODEL"),
            base_url=os.getenv("AI_BASE_URL"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "500")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.3")),
            timeout=int(os.getenv("AI_TIMEOUT", "30")),
        )


class AIClient:
    """
    Multi-provider AI client for MANTRA arbitration.

    Supports Anthropic, OpenAI, DeepSeek, Groq, xAI, and OpenRouter
    with a unified interface.
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialize AI client.

        Args:
            config: AI configuration. If None, loads from environment.
        """
        self.config = config or AIConfig.from_env()
        self._anthropic_client = None
        self._openai_client = None

    @property
    def is_configured(self) -> bool:
        """Check if AI client is properly configured."""
        return bool(self.config.api_key)

    @property
    def provider_name(self) -> str:
        """Get human-readable provider name."""
        return self.config.provider.value.title()

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate completion from AI.

        Args:
            prompt: The user prompt/question
            system_prompt: Optional system instructions

        Returns:
            AI response text

        Raises:
            ValueError: If not configured
            Exception: If API call fails
        """
        if not self.is_configured:
            provider_config = PROVIDER_CONFIGS.get(self.config.provider, {})
            env_key = provider_config.get("env_key", "AI_API_KEY")
            raise ValueError(
                f"AI client not configured. Set {env_key} environment variable."
            )

        api_style = PROVIDER_CONFIGS.get(self.config.provider, {}).get("api_style", "openai")

        if api_style == "anthropic":
            return await self._call_anthropic(prompt, system_prompt)
        else:
            return await self._call_openai_compatible(prompt, system_prompt)

    async def _call_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Call Anthropic Claude API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        if self._anthropic_client is None:
            self._anthropic_client = anthropic.AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout,
            )

        default_system = (
            "You are an expert software architect evaluating decision records. "
            "Respond with JSON only, no markdown."
        )

        try:
            response = await self._anthropic_client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt or default_system,
                messages=[{"role": "user", "content": prompt}],
            )

            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""

        except anthropic.APIError as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    async def _call_openai_compatible(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Call OpenAI-compatible API.

        Works with: OpenAI, DeepSeek, Groq, xAI, OpenRouter
        """
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx package not installed. Run: pip install httpx"
            )

        provider_config = PROVIDER_CONFIGS.get(self.config.provider, {})
        base_url = self.config.base_url or provider_config.get("base_url")

        if not base_url:
            raise ValueError(f"No base URL for provider: {self.config.provider}")

        # Build headers
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        # Add extra headers for specific providers (e.g., OpenRouter)
        extra_headers = provider_config.get("extra_headers", {})
        headers.update(extra_headers)

        # Build messages
        default_system = (
            "You are an expert software architect evaluating decision records. "
            "Respond with JSON only, no markdown."
        )
        messages = [
            {"role": "system", "content": system_prompt or default_system},
            {"role": "user", "content": prompt},
        ]

        # Build request
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # Extract content
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    return message.get("content", "")
                return ""

        except httpx.HTTPStatusError as e:
            raise Exception(
                f"{self.provider_name} API error ({e.response.status_code}): "
                f"{e.response.text}"
            )
        except httpx.RequestError as e:
            raise Exception(f"{self.provider_name} request error: {str(e)}")

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from AI response.

        Handles common issues like markdown code blocks.
        """
        text = response.strip()

        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object from text
            import re
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass

            # Return default structure on parse failure
            return {
                "verdict": "NEEDS_IMPROVEMENT",
                "confidence": 0.5,
                "reason": f"Failed to parse AI response",
                "suggestions": ["Please try again"],
            }


# =============================================================================
# Convenience Functions
# =============================================================================

_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create global AI client instance."""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


def set_ai_client(client: AIClient) -> None:
    """Set global AI client instance (for testing/injection)."""
    global _ai_client
    _ai_client = client


def create_client(
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> AIClient:
    """
    Create AI client with specific configuration.

    Args:
        provider: One of: anthropic, openai, deepseek, groq, xai, openrouter
        api_key: API key (or set via environment)
        model: Model name (or use provider default)

    Returns:
        Configured AIClient
    """
    try:
        provider_enum = AIProvider(provider.lower())
    except ValueError:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(p.value for p in AIProvider)}"
        )

    config = AIConfig(
        provider=provider_enum,
        api_key=api_key,
        model=model,
    )
    return AIClient(config)


# =============================================================================
# Provider Info (for UI/documentation)
# =============================================================================

def get_available_providers() -> List[Dict[str, Any]]:
    """Get list of available AI providers with their configuration."""
    providers = []
    for provider in AIProvider:
        config = PROVIDER_CONFIGS.get(provider, {})
        providers.append({
            "id": provider.value,
            "name": provider.value.title(),
            "default_model": config.get("default_model"),
            "env_key": config.get("env_key"),
            "models": _get_provider_models(provider),
        })
    return providers


def _get_provider_models(provider: AIProvider) -> List[str]:
    """Get available models for a provider."""
    models = {
        AIProvider.ANTHROPIC: [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
        ],
        AIProvider.OPENAI: [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        AIProvider.DEEPSEEK: [
            "deepseek-chat",
            "deepseek-coder",
        ],
        AIProvider.GROQ: [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
        AIProvider.XAI: [
            "grok-beta",
            "grok-2",
        ],
        AIProvider.OPENROUTER: [
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "openai/gpt-4o-mini",
            "google/gemini-pro",
            "meta-llama/llama-3.1-70b-instruct",
        ],
    }
    return models.get(provider, [])
