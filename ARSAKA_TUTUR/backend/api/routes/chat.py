"""
Chat endpoints.

Integrates with ChatOrchestrator for RAG-enabled responses.
"""

from typing import Optional, List
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import StreamingResponse
import json

from ..schemas import ChatRequest, ChatResponse, ChatResponseData
from ..schemas.common import TokenUsage
from ..dependencies import get_context
from ...core.entities import RequestContext, ChatSession, ChatMessage, Role, GenerationResult
from ...container import get_container
from ...shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
@router.post("/sync", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    ctx: RequestContext = Depends(get_context),
):
    """
    Send a message and receive AI response (non-streaming).

    Supports two modes:
    - with_retrieval (default): TUTUR does RAG retrieval
    - with_context: Caller provides context documents (e.g., MANTRA with its own retrieval)
    """
    container = await get_container()

    # Determine mode and prepare parameters
    use_rag = request.mode == "with_retrieval"
    context_documents = None
    if request.mode == "with_context" and request.context_documents:
        context_documents = [doc.model_dump() for doc in request.context_documents]

    # Use ChatOrchestrator for the full flow
    session, user_message, result = await container.chat_orchestrator.chat(
        ctx=ctx,
        message=request.message,
        session_id=request.session_id,
        page_context=request.page_context,
        use_rag=use_rag,
        context_documents=context_documents,
    )

    # Get retrieved doc IDs from the last assistant message
    retrieved_docs: List[str] = []
    messages = await container.session_repository.get_messages(
        session_id=str(session.id),
        tenant_id=ctx.tenant_id,
        limit=1,
    )
    if messages and messages[-1].retrieved_doc_ids:
        retrieved_docs = messages[-1].retrieved_doc_ids

    return ChatResponse(
        data=ChatResponseData(
            session_id=str(session.id),
            message_id=str(user_message.id),  # User message ID
            content=result.content,
            retrieved_docs=retrieved_docs,
            token_usage=TokenUsage(
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
            ),
        )
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    ctx: RequestContext = Depends(get_context),
):
    """
    Send a message and receive AI response (Server-Sent Events streaming).

    Supports two modes:
    - with_retrieval (default): TUTUR does RAG retrieval
    - with_context: Caller provides context documents

    Response is streamed as SSE events:
    - event: message, data: {"content": "..."}
    - event: done, data: {"session_id": "...", "message_id": "...", "retrieved_docs": [...]}
    """
    # Determine mode outside the generator
    use_rag = request.mode == "with_retrieval"
    context_documents = None
    if request.mode == "with_context" and request.context_documents:
        context_documents = [doc.model_dump() for doc in request.context_documents]

    async def generate():
        container = await get_container()
        session = None
        result = None

        try:
            # Use streaming chat orchestrator
            async for chunk, final_session, final_result in container.chat_orchestrator.chat_stream(
                ctx=ctx,
                message=request.message,
                session_id=request.session_id,
                page_context=request.page_context,
                use_rag=use_rag,
                context_documents=context_documents,
            ):
                if chunk:
                    # Stream content chunks
                    yield f"event: message\ndata: {json.dumps({'content': chunk})}\n\n"

                if final_session:
                    session = final_session
                if final_result:
                    result = final_result

            # Get retrieved docs from the session
            retrieved_docs: List[str] = []
            if session:
                messages = await container.session_repository.get_messages(
                    session_id=str(session.id),
                    tenant_id=ctx.tenant_id,
                    limit=1,
                )
                if messages and messages[-1].retrieved_doc_ids:
                    retrieved_docs = messages[-1].retrieved_doc_ids

            # Final event with metadata
            done_data = {
                "session_id": str(session.id) if session else None,
                "message_id": str(uuid4()),  # Placeholder
                "retrieved_docs": retrieved_docs,
                "token_usage": {
                    "prompt_tokens": result.prompt_tokens if result else 0,
                    "completion_tokens": result.completion_tokens if result else 0,
                } if result else {},
            }
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# Helper functions moved to ChatOrchestrator
