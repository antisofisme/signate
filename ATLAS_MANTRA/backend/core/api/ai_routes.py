"""
AI API Routes

Endpoints for AI chat and hints functionality.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

from core.ai.chat_service import get_chat_service
from core.ai.hints_service import get_hints_service
from core.runtime.config import get_config
from factory.container import Container


router = APIRouter(prefix="/ai", tags=["AI Assistant"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Page/decision context")


class ChatResponse(BaseModel):
    """Chat response."""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    messages: List[Dict[str, Any]]
    session_id: Optional[str] = None


class HintsRequest(BaseModel):
    """Hints request."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    field_type: str = Field(default="statement", description="Field type (statement, rationale, etc.)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class HintsResponse(BaseModel):
    """Hints response."""
    success: bool
    hints: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class ProvidersResponse(BaseModel):
    """Available providers response."""
    current_provider: str
    available_providers: List[str]


# ============================================================================
# Decision Repository (for context)
# ============================================================================


def get_decisions_for_context() -> List[Dict]:
    """
    Get all decisions for AI context.

    Uses the shared repository from Container to ensure AI endpoints
    have access to the same decisions as the main API.
    """
    try:
        repository = Container.get_decision_repository()
        # Use find_all which is the standard interface method
        stored_decisions = repository.find_all(limit=1000, offset=0)
        return [
            {
                "decision_id": sd.decision.decision_id,
                "decision_code": getattr(sd.decision, "decision_code", None),
                "domain_id": sd.decision.domain_id.value if hasattr(sd.decision.domain_id, "value") else str(sd.decision.domain_id),
                "aspect_id": sd.decision.aspect_id.value if hasattr(sd.decision.aspect_id, "value") else str(sd.decision.aspect_id),
                "statement": sd.decision.statement,
                "rationale": sd.decision.rationale,
            }
            for sd in stored_decisions
        ]
    except Exception:
        return []


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and get AI response.

    The AI assistant can help with:
    - Drafting decisions
    - Reviewing text
    - Answering questions about MANTRA
    - Comparing with existing decisions
    """
    chat_service = get_chat_service()
    decisions = get_decisions_for_context()

    result = await chat_service.chat(
        user_id=request.user_id,
        message=request.message,
        context=request.context,
        existing_decisions=decisions,
    )

    return ChatResponse(
        success=result.get("success", False),
        response=result.get("response"),
        error=result.get("error"),
        session_id=result.get("session_id"),
        provider=result.get("provider"),
        model=result.get("model"),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(user_id: str):
    """
    Get chat history for a user.

    Returns all messages from the user's current session.
    """
    cache = Container.get_cache()
    cache_key = f"mantra:chat:history:{user_id}"

    # Check cache first
    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return ChatHistoryResponse(**cached)
        except Exception:
            pass

    # Original logic - get history
    chat_service = get_chat_service()
    messages = chat_service.get_history(user_id)
    session = chat_service.get_or_create_session(user_id)

    response = ChatHistoryResponse(
        messages=messages,
        session_id=session.id,
    )

    # Cache result for 10 minutes
    if cache:
        try:
            await cache.set(cache_key, response.model_dump(), ttl=600)
        except Exception:
            pass

    return response


@router.delete("/chat/clear")
async def clear_chat_history(user_id: str):
    """
    Clear chat history for a user.

    This removes all messages from the user's current session.
    """
    chat_service = get_chat_service()
    success = chat_service.clear_history(user_id)

    # Invalidate cache
    cache = Container.get_cache()
    if cache and success:
        try:
            cache_key = f"mantra:chat:history:{user_id}"
            await cache.delete(cache_key)
        except Exception:
            pass

    return {
        "success": success,
        "message": "Chat history cleared" if success else "No history to clear",
    }


@router.post("/hints", response_model=HintsResponse)
async def get_hints(request: HintsRequest):
    """
    Get AI hints for a text field.

    Provides:
    - Grammar corrections
    - Similar decision detection
    - Improvement suggestions
    - Classification recommendations
    """
    # Build cache key from request content
    cache = Container.get_cache()
    content_hash = hashlib.sha256(
        f"{request.text}:{request.field_type}".encode()
    ).hexdigest()[:16]
    cache_key = f"mantra:hints:{content_hash}"

    # Check cache first
    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return HintsResponse(**cached)
        except Exception:
            pass

    # Original logic - call AI service
    hints_service = get_hints_service()
    decisions = get_decisions_for_context()

    result = await hints_service.get_hints(
        text=request.text,
        field_type=request.field_type,
        existing_decisions=decisions,
        context=request.context,
    )

    response = HintsResponse(
        success=result.get("success", False),
        hints=result.get("hints"),
        error=result.get("error"),
        provider=result.get("provider"),
        model=result.get("model"),
    )

    # Cache result (hints for same text are stable) - 1 hour
    if cache:
        try:
            await cache.set(cache_key, response.model_dump(), ttl=3600)
        except Exception:
            pass

    return response


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """
    Get available AI providers.

    Returns the current provider and list of all available providers.
    """
    config = get_config()

    available = []
    for provider in ["openai", "deepseek", "groq", "openrouter", "zai"]:
        if config.get_ai_api_key(provider):
            available.append(provider)

    return ProvidersResponse(
        current_provider=config.ai_provider,
        available_providers=available if available else ["openai"],
    )


@router.get("/health")
async def ai_health():
    """
    Check AI service health.

    Verifies that the AI provider is configured and accessible.
    """
    config = get_config()

    has_key = bool(config.get_ai_api_key())

    return {
        "status": "healthy" if has_key else "unconfigured",
        "provider": config.ai_provider,
        "model": config.ai_model,
        "api_key_configured": has_key,
        "timestamp": datetime.utcnow().isoformat(),
    }
