"""
ARSAKA TUTUR Integration Client

HTTP client for communicating with ARSAKA_TUTUR service.
MANTRA delegates all AI chat functionality to this external service.

Configuration:
- ARSAKA_TUTUR_URL: Base URL of the chat service
- ARSAKA_TUTUR_API_KEY: API key for authentication (optional)
"""

import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import os


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AtlasChatConfig:
    """Configuration for ARSAKA_TUTUR integration."""
    base_url: str
    api_key: Optional[str] = None
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "AtlasChatConfig":
        """Load config from environment variables."""
        return cls(
            base_url=os.getenv("ARSAKA_TUTUR_URL", "http://localhost:8010"),
            api_key=os.getenv("ARSAKA_TUTUR_API_KEY"),
            timeout=float(os.getenv("ARSAKA_TUTUR_TIMEOUT", "30")),
        )


# =============================================================================
# Response Models
# =============================================================================

@dataclass
class ChatResponse:
    """Response from ARSAKA_TUTUR service."""
    success: bool
    response: Optional[str] = None
    session_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class HintsResponse:
    """Hints response from ARSAKA_TUTUR service."""
    success: bool
    hints: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


# =============================================================================
# Client Implementation
# =============================================================================

class ArsakaTuturClient:
    """
    HTTP client for ARSAKA_TUTUR service.

    All AI functionality is delegated to the external service.
    MANTRA only passes context (decisions, user info) and receives responses.
    """

    def __init__(self, config: Optional[AtlasChatConfig] = None):
        self.config = config or AtlasChatConfig.from_env()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # =========================================================================
    # Chat Methods
    # =========================================================================

    async def chat(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        decisions_context: Optional[List[Dict]] = None,
        session_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Send chat message to ARSAKA_TUTUR.

        Args:
            user_id: User identifier
            message: User's message
            context: Additional context (page, current decision, etc.)
            decisions_context: MANTRA decisions for AI context
            session_id: Existing session ID (for conversation continuity)

        Returns:
            ChatResponse with AI response or error
        """
        client = await self._get_client()

        payload = {
            "user_id": user_id,
            "message": message,
            "context": context or {},
            "decisions_context": decisions_context or [],
            "session_id": session_id,
            "source": "mantra",  # Identify request source
        }

        try:
            response = await client.post("/api/v1/chat", json=payload)

            if response.status_code == 200:
                data = response.json()
                return ChatResponse(
                    success=True,
                    response=data.get("response"),
                    session_id=data.get("session_id"),
                    provider=data.get("provider"),
                    model=data.get("model"),
                    timestamp=datetime.utcnow().isoformat(),
                )
            else:
                return ChatResponse(
                    success=False,
                    error=f"Chat service returned {response.status_code}: {response.text}",
                    timestamp=datetime.utcnow().isoformat(),
                )

        except httpx.ConnectError:
            return ChatResponse(
                success=False,
                error="ARSAKA_TUTUR service unavailable. Please try again later.",
                timestamp=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            return ChatResponse(
                success=False,
                error=f"Chat service error: {str(e)}",
                timestamp=datetime.utcnow().isoformat(),
            )

    async def get_history(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get chat history from ARSAKA_TUTUR."""
        client = await self._get_client()

        params = {"user_id": user_id}
        if session_id:
            params["session_id"] = session_id

        try:
            response = await client.get("/api/v1/chat/history", params=params)
            if response.status_code == 200:
                return response.json()
            return {"messages": [], "error": f"Failed to get history: {response.status_code}"}
        except Exception as e:
            return {"messages": [], "error": str(e)}

    async def clear_history(self, user_id: str) -> bool:
        """Clear chat history in ARSAKA_TUTUR."""
        client = await self._get_client()

        try:
            response = await client.delete(
                "/api/v1/chat/clear",
                params={"user_id": user_id}
            )
            return response.status_code == 200
        except Exception:
            return False

    # =========================================================================
    # Hints Methods
    # =========================================================================

    async def get_hints(
        self,
        text: str,
        field_type: str = "statement",
        context: Optional[Dict[str, Any]] = None,
        decisions_context: Optional[List[Dict]] = None,
    ) -> HintsResponse:
        """
        Get AI hints for text input from ARSAKA_TUTUR.

        Args:
            text: Text to analyze
            field_type: Type of field (statement, rationale, etc.)
            context: Additional context
            decisions_context: Existing decisions for comparison

        Returns:
            HintsResponse with suggestions or error
        """
        client = await self._get_client()

        payload = {
            "text": text,
            "field_type": field_type,
            "context": context or {},
            "decisions_context": decisions_context or [],
            "source": "mantra",
        }

        try:
            response = await client.post("/api/v1/hints", json=payload)

            if response.status_code == 200:
                data = response.json()
                return HintsResponse(
                    success=True,
                    hints=data.get("hints"),
                    provider=data.get("provider"),
                    model=data.get("model"),
                )
            else:
                return HintsResponse(
                    success=False,
                    error=f"Hints service returned {response.status_code}",
                )

        except httpx.ConnectError:
            return HintsResponse(
                success=False,
                error="ARSAKA_TUTUR service unavailable",
            )
        except Exception as e:
            return HintsResponse(
                success=False,
                error=f"Hints service error: {str(e)}",
            )

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check ARSAKA_TUTUR service health."""
        client = await self._get_client()

        try:
            response = await client.get("/health")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "service": "arsaka_tutur",
                    "url": self.config.base_url,
                }
            return {
                "status": "unhealthy",
                "service": "arsaka_tutur",
                "error": f"Status {response.status_code}",
            }
        except Exception as e:
            return {
                "status": "unavailable",
                "service": "arsaka_tutur",
                "error": str(e),
            }


# =============================================================================
# Singleton
# =============================================================================

_client: Optional[ArsakaTuturClient] = None


def get_arsaka_tutur_client() -> ArsakaTuturClient:
    """Get ARSAKA_TUTUR client singleton."""
    global _client
    if _client is None:
        _client = ArsakaTuturClient()
    return _client


async def close_arsaka_tutur_client():
    """Close the client (call on shutdown)."""
    global _client
    if _client:
        await _client.close()
        _client = None


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AtlasChatConfig",
    "ArsakaTuturClient",
    "ChatResponse",
    "HintsResponse",
    "get_arsaka_tutur_client",
    "close_arsaka_tutur_client",
]
