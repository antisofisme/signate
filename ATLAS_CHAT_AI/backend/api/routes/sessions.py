"""
Session endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..schemas import (
    CreateSessionRequest,
    SessionResponse,
    SessionListResponse,
    SessionDeleteResponse,
    SessionData,
    MessageData,
    SessionWithMessagesResponse,
    SessionWithMessagesData,
)
from ..schemas.common import PaginationMeta
from ..dependencies import get_context
from ...core.entities import RequestContext
from ...container import get_container
from ...shared.logging import get_logger
from ...shared.exceptions import SessionNotFoundError

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    ctx: RequestContext = Depends(get_context),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List user's chat sessions.

    Returns sessions ordered by last message time (most recent first).
    """
    container = await get_container()

    sessions = await container.session_repository.list_by_user(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        limit=limit,
        offset=offset,
    )

    total = await container.session_repository.count_by_user(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
    )

    return SessionListResponse(
        data=[
            SessionData(
                id=str(s.id),
                title=s.title,
                started_at=s.started_at,
                last_message_at=s.last_message_at,
                message_count=s.message_count,
                summary=s.summary,
            )
            for s in sessions
        ],
        meta=PaginationMeta(total=total, limit=limit, offset=offset),
    )


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    ctx: RequestContext = Depends(get_context),
):
    """
    Create a new chat session.
    """
    from ...core.entities import ChatSession

    container = await get_container()

    session = ChatSession(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        title=request.title,
    )

    await container.session_repository.create(session)
    logger.info(f"Created session {session.id} for user {ctx.user_id}")

    return SessionResponse(
        data=SessionData(
            id=str(session.id),
            title=session.title,
            started_at=session.started_at,
            last_message_at=session.last_message_at,
            message_count=session.message_count,
        )
    )


@router.get("/{session_id}", response_model=SessionWithMessagesResponse)
async def get_session(
    session_id: str,
    ctx: RequestContext = Depends(get_context),
    messages: bool = Query(True, description="Include messages"),
    limit: int = Query(50, ge=1, le=200, description="Message limit"),
):
    """
    Get a session by ID.

    Optionally includes messages (default: true).
    """
    container = await get_container()

    session = await container.session_repository.get_active(
        session_id=session_id,
        tenant_id=ctx.tenant_id,
    )

    if not session or session.user_id != ctx.user_id:
        raise SessionNotFoundError(session_id)

    # Get messages if requested
    message_list = []
    if messages:
        msgs = await container.message_repository.get_by_session(
            session_id=session_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
        )
        message_list = [
            MessageData(
                id=str(m.id),
                role=m.role.value,
                content=m.content,
                created_at=m.created_at,
                retrieved_doc_ids=m.retrieved_doc_ids,
                is_redacted=m.is_redacted,
            )
            for m in msgs
        ]

    return SessionWithMessagesResponse(
        data=SessionWithMessagesData(
            id=str(session.id),
            title=session.title,
            started_at=session.started_at,
            last_message_at=session.last_message_at,
            message_count=session.message_count,
            messages=message_list,
        )
    )


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(
    session_id: str,
    ctx: RequestContext = Depends(get_context),
):
    """
    Soft-delete a session.

    The session and its messages are marked as deleted but not removed.
    """
    container = await get_container()

    # Verify session exists and belongs to user
    session = await container.session_repository.get_active(
        session_id=session_id,
        tenant_id=ctx.tenant_id,
    )

    if not session or session.user_id != ctx.user_id:
        raise SessionNotFoundError(session_id)

    # Soft delete
    deleted = await container.session_repository.soft_delete(
        session_id=session_id,
        tenant_id=ctx.tenant_id,
        deleted_by=ctx.user_id,
    )

    if deleted:
        logger.info(f"Deleted session {session_id} by user {ctx.user_id}")

    return SessionDeleteResponse(
        data={"id": session_id, "deleted": deleted}
    )
