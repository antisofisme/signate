"""
Token counting utilities using tiktoken.
"""

from functools import lru_cache
from typing import List, Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


@lru_cache(maxsize=10)
def _get_encoding(model: str = "gpt-4o-mini"):
    """
    Get tiktoken encoding for model.

    Args:
        model: Model name

    Returns:
        Encoding or None if tiktoken not available
    """
    if not TIKTOKEN_AVAILABLE:
        return None

    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in text.

    Args:
        text: Text to count
        model: Model name for tokenizer

    Returns:
        Token count (estimated if tiktoken not available)
    """
    encoding = _get_encoding(model)

    if encoding is not None:
        return len(encoding.encode(text))

    # Fallback: estimate ~4 characters per token
    return len(text) // 4


def count_tokens_messages(
    messages: List[dict],
    model: str = "gpt-4o-mini"
) -> int:
    """
    Count tokens in chat messages.

    Args:
        messages: List of {"role": ..., "content": ...}
        model: Model name

    Returns:
        Token count
    """
    encoding = _get_encoding(model)

    if encoding is None:
        # Fallback estimate
        total = 0
        for msg in messages:
            total += count_tokens(msg.get("content", ""), model)
            total += 4  # Overhead for role, separators
        return total + 3  # Assistant reply priming

    # Token counting based on OpenAI's methodology
    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    tokens_per_message = 3  # <|start|>role<|sep|>content<|end|>

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if value:
                num_tokens += len(encoding.encode(str(value)))

    num_tokens += 3  # Priming for assistant reply
    return num_tokens


def truncate_to_tokens(
    text: str,
    max_tokens: int,
    model: str = "gpt-4o-mini",
    suffix: str = "..."
) -> str:
    """
    Truncate text to fit within token limit.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens
        model: Model name
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    encoding = _get_encoding(model)

    if encoding is None:
        # Fallback: estimate characters
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars - len(suffix)] + suffix

    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text

    # Reserve tokens for suffix
    suffix_tokens = len(encoding.encode(suffix))
    target_tokens = max_tokens - suffix_tokens

    truncated_tokens = tokens[:target_tokens]
    return encoding.decode(truncated_tokens) + suffix


def split_into_chunks(
    text: str,
    chunk_size: int,
    chunk_overlap: int = 0,
    model: str = "gpt-4o-mini"
) -> List[str]:
    """
    Split text into chunks by token count.

    Args:
        text: Text to split
        chunk_size: Target tokens per chunk
        chunk_overlap: Overlapping tokens between chunks
        model: Model name

    Returns:
        List of text chunks
    """
    encoding = _get_encoding(model)

    if encoding is None:
        # Fallback: split by character estimate
        char_size = chunk_size * 4
        char_overlap = chunk_overlap * 4

        chunks = []
        start = 0
        while start < len(text):
            end = start + char_size
            chunks.append(text[start:end])
            start = end - char_overlap
        return chunks

    tokens = encoding.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end - chunk_overlap

    return chunks


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gpt-4o-mini"
) -> float:
    """
    Estimate API cost in USD.

    Args:
        prompt_tokens: Input tokens
        completion_tokens: Output tokens
        model: Model name

    Returns:
        Estimated cost in USD
    """
    # Pricing as of 2024 (per 1M tokens)
    PRICING = {
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "text-embedding-3-small": {"input": 0.02, "output": 0.0},
        "text-embedding-3-large": {"input": 0.13, "output": 0.0},
    }

    pricing = PRICING.get(model, {"input": 1.0, "output": 3.0})

    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost
