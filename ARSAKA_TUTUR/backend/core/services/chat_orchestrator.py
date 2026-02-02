"""
Chat Orchestrator - Main chat flow coordinator.

Integrates RAG retrieval for knowledge-augmented responses.
"""

from typing import Optional, List, AsyncIterator, TYPE_CHECKING
from dataclasses import dataclass
from uuid import uuid4
from datetime import datetime

from ..entities import (
    ChatMessage, ChatSession, Role, Message,
    RequestContext, GenerationResult, RetrievalResult
)
from ..interfaces import LLMProvider, MemoryStore
from ...shared.logging import get_logger
from ...shared.exceptions import SessionNotFoundError, SessionLimitExceededError

if TYPE_CHECKING:
    from .rag_orchestrator import RAGOrchestrator

logger = get_logger(__name__)


# Default configuration values when tenant_config is not available
@dataclass
class DefaultRAGConfig:
    enabled: bool = False
    top_k: int = 5
    score_threshold: float = 0.3


@dataclass
class DefaultLLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000


DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."
DEFAULT_MAX_SESSIONS = 50


class ChatOrchestrator:
    """
    Orchestrates the chat flow.

    Responsibilities:
    - Session management (create, get, validate limits)
    - Message persistence
    - Context assembly (including RAG retrieval)
    - LLM generation coordination

    This is the main entry point for chat operations.
    """

    def __init__(
        self,
        memory_store: MemoryStore,
        llm_provider: Optional[LLMProvider] = None,
        rag_orchestrator: Optional["RAGOrchestrator"] = None,
    ):
        self.memory_store = memory_store
        self.llm_provider = llm_provider
        self.rag_orchestrator = rag_orchestrator

    def _get_rag_config(self, ctx: RequestContext):
        """Get RAG config with safe defaults."""
        if ctx.tenant_config and hasattr(ctx.tenant_config, 'rag_config') and ctx.tenant_config.rag_config:
            return ctx.tenant_config.rag_config
        return DefaultRAGConfig()

    def _get_llm_config(self, ctx: RequestContext):
        """Get LLM config with safe defaults."""
        if ctx.tenant_config and hasattr(ctx.tenant_config, 'llm_config') and ctx.tenant_config.llm_config:
            return ctx.tenant_config.llm_config
        return DefaultLLMConfig()

    def _get_system_prompt(self, ctx: RequestContext) -> str:
        """Get system prompt with safe default."""
        if ctx.tenant_config and hasattr(ctx.tenant_config, 'system_prompt') and ctx.tenant_config.system_prompt:
            return ctx.tenant_config.system_prompt
        return DEFAULT_SYSTEM_PROMPT

    async def chat(
        self,
        ctx: RequestContext,
        message: str,
        session_id: Optional[str] = None,
        page_context: Optional[str] = None,
        use_rag: bool = True,
        context_documents: Optional[List[dict]] = None,
    ) -> tuple[ChatSession, ChatMessage, GenerationResult]:
        """
        Process a chat message and generate response.

        Supports two modes:
        - with_retrieval: TUTUR does RAG retrieval (use_rag=True, context_documents=None)
        - with_context: Caller provides context (use_rag=False, context_documents=[...])

        Args:
            ctx: Request context with tenant and user info
            message: User message
            session_id: Optional existing session ID
            page_context: Optional page context
            use_rag: Whether to use RAG for context retrieval
            context_documents: Pre-fetched context from caller (for mode=with_context)

        Returns:
            Tuple of (session, user_message, generation_result)
        """
        # Get or create session
        session = await self._get_or_create_session(ctx, session_id)

        # Save user message
        user_message = await self._save_user_message(
            ctx, session, message, page_context
        )

        # Get conversation history
        history = await self.memory_store.get_messages(
            session_id=str(session.id),
            tenant_id=ctx.tenant_id,
            limit=20  # Recent messages for context
        )

        # Context handling based on mode
        rag_context: Optional[RetrievalResult] = None
        retrieved_doc_ids: List[str] = []
        caller_context: Optional[str] = None

        if context_documents:
            # Mode: with_context - use caller-provided context
            caller_context = self._format_caller_context(context_documents)
            logger.debug(f"Using {len(context_documents)} caller-provided context documents")
        elif use_rag:
            # Mode: with_retrieval - use RAG
            rag_config = self._get_rag_config(ctx)
            if self.rag_orchestrator and rag_config.enabled:
                try:
                    rag_context = await self.rag_orchestrator.search(
                        ctx=ctx,
                        query=message,
                        top_k=rag_config.top_k,
                        score_threshold=rag_config.score_threshold,
                    )
                    retrieved_doc_ids = [r.document_id for r in rag_context.results if r.document_id]
                    logger.debug(f"RAG retrieved {len(rag_context.results)} documents")
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without context: {e}")

        # Build messages for LLM
        messages = self._build_messages(
            ctx, history, message,
            rag_context=rag_context,
            caller_context=caller_context
        )

        # Generate response
        llm_config = self._get_llm_config(ctx)
        if self.llm_provider:
            result = await self.llm_provider.generate(
                messages=messages,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )
        else:
            # Placeholder response for testing
            result = GenerationResult(
                content=f"Echo: {message}",
                prompt_tokens=len(message) // 4,
                completion_tokens=len(message) // 4,
                model="placeholder",
            )

        # Save assistant message with retrieved doc IDs
        await self._save_assistant_message(ctx, session, result, retrieved_doc_ids)

        return session, user_message, result

    async def chat_stream(
        self,
        ctx: RequestContext,
        message: str,
        session_id: Optional[str] = None,
        page_context: Optional[str] = None,
        use_rag: bool = True,
        context_documents: Optional[List[dict]] = None,
    ) -> AsyncIterator[tuple[str, Optional[ChatSession], Optional[GenerationResult]]]:
        """
        Process a chat message with streaming response.

        Supports two modes:
        - with_retrieval: TUTUR does RAG retrieval
        - with_context: Caller provides context

        Yields:
            Tuples of (chunk, session, final_result)
            - During streaming: (chunk, None, None)
            - Final yield: ("", session, result)
        """
        # Get or create session
        session = await self._get_or_create_session(ctx, session_id)

        # Save user message
        await self._save_user_message(ctx, session, message, page_context)

        # Get conversation history
        history = await self.memory_store.get_messages(
            session_id=str(session.id),
            tenant_id=ctx.tenant_id,
            limit=20
        )

        # Context handling based on mode
        rag_context: Optional[RetrievalResult] = None
        retrieved_doc_ids: List[str] = []
        caller_context: Optional[str] = None
        llm_config = self._get_llm_config(ctx)

        if context_documents:
            # Mode: with_context
            caller_context = self._format_caller_context(context_documents)
        elif use_rag:
            # Mode: with_retrieval
            rag_config = self._get_rag_config(ctx)
            if self.rag_orchestrator and rag_config.enabled:
                try:
                    rag_context = await self.rag_orchestrator.search(
                        ctx=ctx,
                        query=message,
                        top_k=rag_config.top_k,
                        score_threshold=rag_config.score_threshold,
                    )
                    retrieved_doc_ids = [r.document_id for r in rag_context.results if r.document_id]
                except Exception as e:
                    logger.warning(f"RAG retrieval failed during streaming: {e}")

        # Build messages
        messages = self._build_messages(
            ctx, history, message,
            rag_context=rag_context,
            caller_context=caller_context
        )

        # Stream response
        full_content = ""
        if self.llm_provider:
            async for chunk in self.llm_provider.stream(
                messages=messages,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            ):
                full_content += chunk
                yield chunk, None, None
        else:
            # Placeholder for testing
            full_content = f"Echo: {message}"
            yield full_content, None, None

        # Create result
        result = GenerationResult(
            content=full_content,
            prompt_tokens=len(message) // 4,
            completion_tokens=len(full_content) // 4,
            model=llm_config.model,
        )

        # Save assistant message with retrieved doc IDs
        await self._save_assistant_message(ctx, session, result, retrieved_doc_ids)

        # Final yield with session and result
        yield "", session, result

    async def get_session(
        self,
        ctx: RequestContext,
        session_id: str,
    ) -> ChatSession:
        """Get a session by ID."""
        session = await self.memory_store.get_session(session_id, ctx.tenant_id)
        if not session:
            raise SessionNotFoundError(session_id)
        return session

    async def get_session_messages(
        self,
        ctx: RequestContext,
        session_id: str,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Get messages for a session."""
        # Verify session exists and belongs to user
        session = await self.get_session(ctx, session_id)
        if session.user_id != ctx.user_id:
            raise SessionNotFoundError(session_id)

        return await self.memory_store.get_messages(
            session_id=session_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
        )

    async def create_session(
        self,
        ctx: RequestContext,
        title: Optional[str] = None,
    ) -> ChatSession:
        """Create a new session."""
        # Check session limit
        await self._check_session_limit(ctx)

        session = ChatSession(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            title=title,
        )

        await self.memory_store.create_session(session)
        logger.info(f"Created session {session.id} for user {ctx.user_id}")

        return session

    async def delete_session(
        self,
        ctx: RequestContext,
        session_id: str,
    ) -> bool:
        """Soft-delete a session."""
        session = await self.get_session(ctx, session_id)
        if session.user_id != ctx.user_id:
            raise SessionNotFoundError(session_id)

        return await self.memory_store.delete_session(
            session_id=session_id,
            tenant_id=ctx.tenant_id,
            deleted_by=ctx.user_id,
        )

    async def list_sessions(
        self,
        ctx: RequestContext,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ChatSession]:
        """List user's sessions."""
        return await self.memory_store.list_sessions(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            limit=limit,
            offset=offset,
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_or_create_session(
        self,
        ctx: RequestContext,
        session_id: Optional[str],
    ) -> ChatSession:
        """Get existing session or create new one."""
        if session_id:
            session = await self.memory_store.get_session(session_id, ctx.tenant_id)
            if session and session.user_id == ctx.user_id:
                return session
            # Session not found or doesn't belong to user - create new

        return await self.create_session(ctx)

    async def _check_session_limit(self, ctx: RequestContext) -> None:
        """Check if user has reached session limit."""
        count = await self.memory_store.count_sessions(ctx.tenant_id, ctx.user_id)
        # Use default if tenant_config is not loaded
        max_sessions = 50  # Default limit
        if ctx.tenant_config and hasattr(ctx.tenant_config, 'max_sessions_per_user'):
            max_sessions = ctx.tenant_config.max_sessions_per_user or max_sessions

        if count >= max_sessions:
            raise SessionLimitExceededError(count, max_sessions)

    async def _save_user_message(
        self,
        ctx: RequestContext,
        session: ChatSession,
        content: str,
        page_context: Optional[str],
    ) -> ChatMessage:
        """Save user message to storage."""
        message = ChatMessage(
            session_id=session.id,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            role=Role.USER,
            content=content,
            page_context=page_context,
        )

        await self.memory_store.save_message(message)
        return message

    async def _save_assistant_message(
        self,
        ctx: RequestContext,
        session: ChatSession,
        result: GenerationResult,
        retrieved_doc_ids: Optional[List[str]] = None,
    ) -> ChatMessage:
        """Save assistant message to storage."""
        llm_config = self._get_llm_config(ctx)
        message = ChatMessage(
            session_id=session.id,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            role=Role.ASSISTANT,
            content=result.content,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            provider=llm_config.provider,
            model=result.model,
            temperature=llm_config.temperature,
            retrieved_doc_ids=retrieved_doc_ids,
        )

        await self.memory_store.save_message(message)
        return message

    def _build_messages(
        self,
        ctx: RequestContext,
        history: List[ChatMessage],
        current_message: str,
        rag_context: Optional[RetrievalResult] = None,
        caller_context: Optional[str] = None,
    ) -> List[Message]:
        """
        Build message list for LLM.

        Args:
            ctx: Request context
            history: Conversation history
            current_message: Current user message
            rag_context: Optional RAG retrieval results (mode=with_retrieval)
            caller_context: Optional caller-provided context (mode=with_context)

        Returns:
            List of messages for LLM
        """
        messages = []

        # System prompt (possibly augmented with context)
        system_content = self._get_system_prompt(ctx)

        # Add context to system prompt (either from RAG or caller)
        if caller_context:
            # Mode: with_context - use caller's pre-formatted context
            system_content = f"{system_content}\n\n{caller_context}"
        elif rag_context and rag_context.results:
            # Mode: with_retrieval - use RAG context
            context_text = self._format_rag_context(rag_context)
            system_content = f"{system_content}\n\n{context_text}"

        messages.append(Message(
            role="system",
            content=system_content,
        ))

        # Conversation history
        for msg in history:
            messages.append(msg.to_message())

        # Current message (if not already in history)
        if not history or history[-1].content != current_message:
            messages.append(Message(role="user", content=current_message))

        return messages

    def _format_rag_context(self, rag_context: RetrievalResult) -> str:
        """
        Format RAG retrieval results for inclusion in system prompt.

        Args:
            rag_context: RAG retrieval results

        Returns:
            Formatted context string
        """
        if not rag_context.results:
            return ""

        context_parts = [
            "## Relevant Context",
            "",
            "The following information may be relevant to answer the user's question:",
            "",
        ]

        for i, result in enumerate(rag_context.results, 1):
            source = result.metadata.get("source", "unknown")
            context_parts.append(f"### Source {i} (relevance: {result.score:.2f})")
            context_parts.append(f"Source: {source}")
            context_parts.append("")
            context_parts.append(result.content)
            context_parts.append("")

        context_parts.append("---")
        context_parts.append("")
        context_parts.append(
            "Use the above context to inform your response when relevant. "
            "If the context doesn't help answer the question, you may ignore it."
        )

        return "\n".join(context_parts)

    def _format_caller_context(self, context_documents: List[dict]) -> str:
        """
        Format caller-provided context documents for inclusion in system prompt.

        Used for mode=with_context where the caller (e.g., MANTRA) provides
        pre-fetched context with domain-specific retrieval.

        Args:
            context_documents: List of context documents from caller
                Each document should have: content, type (optional), metadata (optional)

        Returns:
            Formatted context string
        """
        if not context_documents:
            return ""

        context_parts = [
            "## Relevant Context",
            "",
            "The following information has been provided to help answer the user's question:",
            "",
        ]

        for i, doc in enumerate(context_documents, 1):
            doc_type = doc.get("type", "document")
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Build header with type and metadata
            header = f"### {doc_type.title()} {i}"
            if metadata:
                # Add relevant metadata to header
                if "decision_code" in metadata:
                    header += f" ({metadata['decision_code']})"
                elif "source" in metadata:
                    header += f" (Source: {metadata['source']})"

            context_parts.append(header)
            context_parts.append("")
            context_parts.append(content)
            context_parts.append("")

        context_parts.append("---")
        context_parts.append("")
        context_parts.append(
            "Use the above context to inform your response when relevant. "
            "If the context doesn't help answer the question, you may ignore it."
        )

        return "\n".join(context_parts)
