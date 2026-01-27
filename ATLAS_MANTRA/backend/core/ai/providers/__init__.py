"""
AI Provider Factory

Supports multiple AI providers:
- OpenAI (default)
- DeepSeek
- Groq
- OpenRouter
- z.ai
"""

from .base import AIProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .groq_provider import GroqProvider
from .openrouter_provider import OpenRouterProvider

from core.runtime.config import get_config


def get_ai_provider(provider_name: str = None) -> AIProvider:
    """
    Factory function to get AI provider instance.

    Args:
        provider_name: Provider name (openai, deepseek, groq, openrouter, zai)
                      If None, uses default from config.

    Returns:
        AIProvider instance
    """
    config = get_config()
    name = provider_name or config.ai_provider

    providers = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "groq": GroqProvider,
        "openrouter": OpenRouterProvider,
        "zai": OpenRouterProvider,  # z.ai uses OpenRouter-compatible API
    }

    provider_class = providers.get(name)
    if not provider_class:
        raise ValueError(f"Unknown AI provider: {name}. Available: {list(providers.keys())}")

    api_key = config.get_ai_api_key(name)
    if not api_key:
        raise ValueError(f"API key not configured for provider: {name}")

    return provider_class(
        api_key=api_key,
        model=config.ai_model,
        max_tokens=config.ai_max_tokens,
        temperature=config.ai_temperature,
    )


__all__ = [
    "AIProvider",
    "get_ai_provider",
    "OpenAIProvider",
    "DeepSeekProvider",
    "GroqProvider",
    "OpenRouterProvider",
]
