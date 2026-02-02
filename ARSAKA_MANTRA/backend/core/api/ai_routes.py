"""
AI API Routes

Endpoints for AI chat and hints functionality.
Delegates to ARSAKA_TUTUR external service.

MANTRA does NOT have its own AI - all AI functionality is provided
by the ARSAKA_TUTUR service. This ensures:
1. Centralized AI management
2. Consistent behavior across ARSAKA projects
3. Easier model/provider updates
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

from core.ai.arsaka_tutur_client import get_arsaka_tutur_client
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
    session_id: Optional[str] = Field(default=None, description="Existing session ID")


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
    error: Optional[str] = None


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


class ServiceStatusResponse(BaseModel):
    """AI service status response."""
    status: str
    service: str
    url: Optional[str] = None
    error: Optional[str] = None
    timestamp: str


# ============================================================================
# Decision Context Helper
# ============================================================================

def get_decisions_for_context() -> List[Dict]:
    """
    Get decisions for AI context.

    Passes MANTRA decisions to ARSAKA_TUTUR so it can:
    - Compare with existing decisions
    - Detect duplicates/conflicts
    - Provide relevant suggestions
    """
    try:
        repository = Container.get_decision_repository()
        stored_decisions = repository.find_all(limit=100, offset=0)
        return [
            {
                "decision_id": sd.decision.decision_id,
                "decision_code": getattr(sd.decision, "decision_code", None),
                "domain_id": sd.decision.domain_id.value if hasattr(sd.decision.domain_id, "value") else str(sd.decision.domain_id),
                "aspect_id": sd.decision.aspect_id.value if hasattr(sd.decision.aspect_id, "value") else str(sd.decision.aspect_id),
                "statement": sd.decision.statement,
                "rationale": sd.decision.rationale[:500] if sd.decision.rationale else None,
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

    Delegates to ARSAKA_TUTUR service with MANTRA context.

    The AI assistant can help with:
    - Drafting decisions
    - Reviewing text
    - Answering questions about MANTRA
    - Comparing with existing decisions
    """
    client = get_arsaka_tutur_client()
    decisions = get_decisions_for_context()

    result = await client.chat(
        user_id=request.user_id,
        message=request.message,
        context=request.context,
        decisions_context=decisions,
        session_id=request.session_id,
    )

    return ChatResponse(
        success=result.success,
        response=result.response,
        error=result.error,
        session_id=result.session_id,
        provider=result.provider,
        model=result.model,
        timestamp=result.timestamp or datetime.utcnow().isoformat(),
    )


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(user_id: str, session_id: Optional[str] = None):
    """
    Get chat history for a user.

    Retrieves history from ARSAKA_TUTUR service.
    """
    # Check cache first
    cache = Container.get_cache()
    cache_key = f"mantra:chat:history:{user_id}"

    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return ChatHistoryResponse(**cached)
        except Exception:
            pass

    # Get from ARSAKA_TUTUR
    client = get_arsaka_tutur_client()
    result = await client.get_history(user_id, session_id)

    response = ChatHistoryResponse(
        messages=result.get("messages", []),
        session_id=result.get("session_id"),
        error=result.get("error"),
    )

    # Cache for 10 minutes
    if cache and not result.get("error"):
        try:
            await cache.set(cache_key, response.model_dump(), ttl=600)
        except Exception:
            pass

    return response


@router.delete("/chat/clear")
async def clear_chat_history(user_id: str):
    """
    Clear chat history for a user.

    Clears history in ARSAKA_TUTUR service.
    """
    client = get_arsaka_tutur_client()
    success = await client.clear_history(user_id)

    # Invalidate cache
    cache = Container.get_cache()
    if cache and success:
        try:
            await cache.delete(f"mantra:chat:history:{user_id}")
        except Exception:
            pass

    return {
        "success": success,
        "message": "Chat history cleared" if success else "Failed to clear history",
    }


@router.post("/hints", response_model=HintsResponse)
async def get_hints(request: HintsRequest):
    """
    Get AI hints for a text field.

    Delegates to ARSAKA_TUTUR for analysis.

    Provides:
    - Grammar corrections
    - Similar decision detection
    - Improvement suggestions
    - Classification recommendations
    """
    # Check cache first
    cache = Container.get_cache()
    content_hash = hashlib.sha256(
        f"{request.text}:{request.field_type}".encode()
    ).hexdigest()[:16]
    cache_key = f"mantra:hints:{content_hash}"

    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return HintsResponse(**cached)
        except Exception:
            pass

    # Get from ARSAKA_TUTUR
    client = get_arsaka_tutur_client()
    decisions = get_decisions_for_context()

    result = await client.get_hints(
        text=request.text,
        field_type=request.field_type,
        context=request.context,
        decisions_context=decisions,
    )

    response = HintsResponse(
        success=result.success,
        hints=result.hints,
        error=result.error,
        provider=result.provider,
        model=result.model,
    )

    # Cache for 1 hour (hints are stable for same text)
    if cache and result.success:
        try:
            await cache.set(cache_key, response.model_dump(), ttl=3600)
        except Exception:
            pass

    return response


@router.get("/health", response_model=ServiceStatusResponse)
async def ai_health():
    """
    Check AI service health.

    Verifies connection to ARSAKA_TUTUR service.
    """
    client = get_arsaka_tutur_client()
    result = await client.health_check()

    return ServiceStatusResponse(
        status=result.get("status", "unknown"),
        service="arsaka_tutur",
        url=result.get("url"),
        error=result.get("error"),
        timestamp=datetime.utcnow().isoformat(),
    )
