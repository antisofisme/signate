"""
Storage interfaces for vector and memory storage.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from ..entities import ChatSession, ChatMessage, SearchResult


class VectorStore(ABC):
    """
    Interface for vector database operations.

    Implementations: QdrantAdapter
    """

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            collection: Collection/index name
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            score_threshold: Minimum similarity score

        Returns:
            List of SearchResult ordered by similarity
        """
        pass

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """
        Insert or update a vector.

        Args:
            collection: Collection/index name
            id: Unique vector ID
            vector: Embedding vector
            payload: Metadata payload

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def upsert_batch(
        self,
        collection: str,
        items: List[Dict[str, Any]]
    ) -> int:
        """
        Batch insert/update vectors.

        Args:
            collection: Collection/index name
            items: List of {id, vector, payload}

        Returns:
            Number of vectors upserted
        """
        pass

    @abstractmethod
    async def delete(self, collection: str, id: str) -> bool:
        """
        Delete a vector by ID.

        Args:
            collection: Collection/index name
            id: Vector ID to delete

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    async def delete_by_filter(
        self,
        collection: str,
        filters: Dict[str, Any]
    ) -> int:
        """
        Delete vectors matching filter.

        Args:
            collection: Collection/index name
            filters: Metadata filters

        Returns:
            Number of vectors deleted
        """
        pass

    @abstractmethod
    async def ensure_collection(
        self,
        collection: str,
        vector_size: int
    ) -> bool:
        """
        Ensure collection exists with correct configuration.

        Args:
            collection: Collection/index name
            vector_size: Dimension of vectors

        Returns:
            True if collection exists/created
        """
        pass


class MemoryStore(ABC):
    """
    Interface for persistent chat storage.

    Implementations: PostgresMemoryStore (via repositories)
    """

    @abstractmethod
    async def create_session(
        self,
        session: ChatSession
    ) -> str:
        """
        Create a new chat session.

        Args:
            session: ChatSession entity

        Returns:
            Session ID
        """
        pass

    @abstractmethod
    async def get_session(
        self,
        session_id: str,
        tenant_id: str
    ) -> Optional[ChatSession]:
        """
        Get session by ID.

        Args:
            session_id: Session UUID
            tenant_id: Tenant ID (for isolation)

        Returns:
            ChatSession or None if not found
        """
        pass

    @abstractmethod
    async def update_session(self, session: ChatSession) -> bool:
        """
        Update session metadata.

        Args:
            session: ChatSession with updates

        Returns:
            True if updated
        """
        pass

    @abstractmethod
    async def list_sessions(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[ChatSession]:
        """
        List user's chat sessions.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            limit: Max results
            offset: Pagination offset
            include_deleted: Include soft-deleted sessions

        Returns:
            List of ChatSession
        """
        pass

    @abstractmethod
    async def delete_session(
        self,
        session_id: str,
        tenant_id: str,
        deleted_by: str
    ) -> bool:
        """
        Soft-delete a session.

        Args:
            session_id: Session UUID
            tenant_id: Tenant ID
            deleted_by: User performing deletion

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    async def save_message(self, message: ChatMessage) -> str:
        """
        Save a chat message (APPEND-ONLY).

        Args:
            message: ChatMessage entity

        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List[ChatMessage]:
        """
        Get messages for a session.

        Args:
            session_id: Session UUID
            tenant_id: Tenant ID
            limit: Max messages
            before_id: Pagination cursor (messages before this ID)

        Returns:
            List of ChatMessage ordered by created_at
        """
        pass

    @abstractmethod
    async def count_sessions(
        self,
        tenant_id: str,
        user_id: str
    ) -> int:
        """
        Count user's active sessions.

        Args:
            tenant_id: Tenant ID
            user_id: User ID

        Returns:
            Session count
        """
        pass
