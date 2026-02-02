"""
ARSAKA_TUTUR Python SDK

A Python client for interacting with the ARSAKA_TUTUR service.

Usage:
    from arsaka_tutur import ChatClient

    client = ChatClient(
        base_url="http://localhost:8003",
        tenant_id="my-tenant",
        api_key="sk_my_api_key",
    )

    # Send a message
    response = client.chat("Hello!")
    print(response.content)

    # Stream a response
    for chunk in client.chat_stream("Tell me a story"):
        print(chunk, end="", flush=True)
"""

from .client import ChatClient, AsyncChatClient
from .models import (
    ChatResponse,
    SearchResult,
    Session,
    Message,
    UserFact,
    APIError,
)

__version__ = "1.0.0"

__all__ = [
    "ChatClient",
    "AsyncChatClient",
    "ChatResponse",
    "SearchResult",
    "Session",
    "Message",
    "UserFact",
    "APIError",
]
