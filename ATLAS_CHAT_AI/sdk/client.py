"""
ATLAS_CHAT_AI SDK Client

Synchronous and asynchronous clients for the ATLAS_CHAT_AI API.
"""

from typing import Optional, List, Iterator, AsyncIterator, Any
import json

from .models import (
    ChatResponse,
    SearchResponse,
    SearchResult,
    Session,
    Message,
    UserFact,
    APIError,
)


class ChatClient:
    """
    Synchronous client for ATLAS_CHAT_AI.

    Example:
        client = ChatClient(
            base_url="http://localhost:8003",
            tenant_id="my-tenant",
            api_key="sk_my_api_key",
        )

        # Chat
        response = client.chat("Hello!")
        print(response.content)

        # Stream
        for chunk in client.chat_stream("Tell me a story"):
            print(chunk, end="")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8003",
        tenant_id: str = "default",
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """
        Initialize the client.

        Args:
            base_url: API base URL
            tenant_id: Tenant identifier
            api_key: API key for authentication
            jwt_token: JWT token for authentication (alternative to api_key)
            user_id: User ID for requests (optional, may be in JWT)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.user_id = user_id
        self.timeout = timeout

        self._session: Any = None

    def _get_session(self):
        """Get or create requests session."""
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session

    def _headers(self) -> dict:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-ID": self.tenant_id,
        }

        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        if self.user_id:
            headers["X-User-ID"] = self.user_id

        return headers

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make an API request."""
        url = f"{self.base_url}/api/v1{path}"
        session = self._get_session()

        response = session.request(
            method=method,
            url=url,
            headers=self._headers(),
            json=data,
            params=params,
            timeout=self.timeout,
        )

        result = response.json()

        if not result.get("success", False):
            raise APIError.from_response(result, response.status_code)

        return result.get("data", result)

    # =========================================================================
    # Chat Methods
    # =========================================================================

    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        page_context: Optional[str] = None,
        use_rag: bool = True,
    ) -> ChatResponse:
        """
        Send a chat message and get a response.

        Args:
            message: User message
            session_id: Optional session ID (creates new if not provided)
            page_context: Optional page context for RAG
            use_rag: Whether to use RAG for context retrieval

        Returns:
            ChatResponse with content and metadata
        """
        data = self._request(
            "POST",
            "/chat",
            data={
                "message": message,
                "session_id": session_id,
                "page_context": page_context,
            },
            params={"use_rag": str(use_rag).lower()},
        )

        return ChatResponse.from_dict(data)

    def chat_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        page_context: Optional[str] = None,
        use_rag: bool = True,
    ) -> Iterator[str]:
        """
        Send a chat message and stream the response.

        Args:
            message: User message
            session_id: Optional session ID
            page_context: Optional page context
            use_rag: Whether to use RAG

        Yields:
            Content chunks as they arrive
        """
        url = f"{self.base_url}/api/v1/chat/stream"
        session = self._get_session()

        response = session.post(
            url,
            headers=self._headers(),
            json={
                "message": message,
                "session_id": session_id,
                "page_context": page_context,
            },
            params={"use_rag": str(use_rag).lower()},
            stream=True,
            timeout=self.timeout,
        )

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode("utf-8")

            if line.startswith("event:"):
                event_type = line[6:].strip()
                continue

            if line.startswith("data:"):
                data = json.loads(line[5:].strip())

                if "content" in data:
                    yield data["content"]
                elif "error" in data:
                    raise APIError(
                        code="STREAM_ERROR",
                        message=data["error"],
                    )

    # =========================================================================
    # Session Methods
    # =========================================================================

    def list_sessions(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Session]:
        """List user's chat sessions."""
        data = self._request(
            "GET",
            "/sessions",
            params={"limit": limit, "offset": offset},
        )

        if isinstance(data, list):
            return [Session.from_dict(s) for s in data]
        return [Session.from_dict(s) for s in data.get("sessions", [])]

    def get_session(self, session_id: str) -> Session:
        """Get a session by ID."""
        data = self._request("GET", f"/sessions/{session_id}")
        return Session.from_dict(data)

    def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Message]:
        """Get messages for a session."""
        data = self._request(
            "GET",
            f"/sessions/{session_id}/messages",
            params={"limit": limit},
        )

        if isinstance(data, list):
            return [Message.from_dict(m) for m in data]
        return [Message.from_dict(m) for m in data.get("messages", [])]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        self._request("DELETE", f"/sessions/{session_id}")
        return True

    # =========================================================================
    # Search Methods
    # =========================================================================

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> SearchResponse:
        """
        Search knowledge base.

        Args:
            query: Search query
            top_k: Number of results
            score_threshold: Minimum relevance score

        Returns:
            SearchResponse with results
        """
        data = self._request(
            "POST",
            "/search",
            data={
                "query": query,
                "top_k": top_k,
                "score_threshold": score_threshold,
            },
        )

        return SearchResponse.from_dict(data)

    # =========================================================================
    # Memory Methods
    # =========================================================================

    def list_facts(
        self,
        fact_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[UserFact]:
        """List user facts from memory."""
        params = {"active_only": str(active_only).lower()}
        if fact_type:
            params["fact_type"] = fact_type

        data = self._request("GET", "/memory/facts", params=params)

        if isinstance(data, list):
            return [UserFact.from_dict(f) for f in data]
        return [UserFact.from_dict(f) for f in data.get("facts", data)]

    def create_fact(
        self,
        content: str,
        fact_type: str = "GENERAL",
        confidence: float = 1.0,
    ) -> str:
        """
        Create a user fact.

        Returns the fact ID.
        """
        data = self._request(
            "POST",
            "/memory/facts",
            data={
                "fact_type": fact_type,
                "content": content,
                "confidence": confidence,
            },
        )

        return data.get("fact_id", "")

    def delete_fact(self, fact_id: str) -> bool:
        """Delete (deactivate) a fact."""
        self._request("DELETE", f"/memory/facts/{fact_id}")
        return True

    def search_past_sessions(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Session]:
        """Search past sessions by semantic similarity."""
        data = self._request(
            "GET",
            "/memory/sessions/search",
            params={"query": query, "top_k": top_k},
        )

        if isinstance(data, list):
            return [Session.from_dict(s) for s in data]
        return [Session.from_dict(s) for s in data.get("sessions", data)]

    # =========================================================================
    # Cleanup
    # =========================================================================

    def close(self) -> None:
        """Close the client session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncChatClient:
    """
    Asynchronous client for ATLAS_CHAT_AI.

    Example:
        async with AsyncChatClient(
            base_url="http://localhost:8003",
            tenant_id="my-tenant",
            api_key="sk_my_api_key",
        ) as client:
            response = await client.chat("Hello!")
            print(response.content)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8003",
        tenant_id: str = "default",
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """Initialize the async client."""
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.user_id = user_id
        self.timeout = timeout

        self._session: Any = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    def _headers(self) -> dict:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-ID": self.tenant_id,
        }

        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        if self.user_id:
            headers["X-User-ID"] = self.user_id

        return headers

    async def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make an async API request."""
        url = f"{self.base_url}/api/v1{path}"
        session = await self._get_session()

        async with session.request(
            method=method,
            url=url,
            headers=self._headers(),
            json=data,
            params=params,
        ) as response:
            result = await response.json()

            if not result.get("success", False):
                raise APIError.from_response(result, response.status)

            return result.get("data", result)

    # =========================================================================
    # Chat Methods
    # =========================================================================

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        page_context: Optional[str] = None,
        use_rag: bool = True,
    ) -> ChatResponse:
        """Send a chat message and get a response."""
        data = await self._request(
            "POST",
            "/chat",
            data={
                "message": message,
                "session_id": session_id,
                "page_context": page_context,
            },
            params={"use_rag": str(use_rag).lower()},
        )

        return ChatResponse.from_dict(data)

    async def chat_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        page_context: Optional[str] = None,
        use_rag: bool = True,
    ) -> AsyncIterator[str]:
        """Stream a chat response."""
        url = f"{self.base_url}/api/v1/chat/stream"
        session = await self._get_session()

        async with session.post(
            url,
            headers=self._headers(),
            json={
                "message": message,
                "session_id": session_id,
                "page_context": page_context,
            },
            params={"use_rag": str(use_rag).lower()},
        ) as response:
            async for line in response.content:
                line = line.decode("utf-8").strip()

                if not line or line.startswith("event:"):
                    continue

                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())

                    if "content" in data:
                        yield data["content"]
                    elif "error" in data:
                        raise APIError(
                            code="STREAM_ERROR",
                            message=data["error"],
                        )

    # =========================================================================
    # Session Methods
    # =========================================================================

    async def list_sessions(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Session]:
        """List user's chat sessions."""
        data = await self._request(
            "GET",
            "/sessions",
            params={"limit": limit, "offset": offset},
        )

        if isinstance(data, list):
            return [Session.from_dict(s) for s in data]
        return [Session.from_dict(s) for s in data.get("sessions", [])]

    async def get_session(self, session_id: str) -> Session:
        """Get a session by ID."""
        data = await self._request("GET", f"/sessions/{session_id}")
        return Session.from_dict(data)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        await self._request("DELETE", f"/sessions/{session_id}")
        return True

    # =========================================================================
    # Search Methods
    # =========================================================================

    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> SearchResponse:
        """Search knowledge base."""
        data = await self._request(
            "POST",
            "/search",
            data={
                "query": query,
                "top_k": top_k,
                "score_threshold": score_threshold,
            },
        )

        return SearchResponse.from_dict(data)

    # =========================================================================
    # Memory Methods
    # =========================================================================

    async def list_facts(
        self,
        fact_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[UserFact]:
        """List user facts from memory."""
        params = {"active_only": str(active_only).lower()}
        if fact_type:
            params["fact_type"] = fact_type

        data = await self._request("GET", "/memory/facts", params=params)

        if isinstance(data, list):
            return [UserFact.from_dict(f) for f in data]
        return [UserFact.from_dict(f) for f in data.get("facts", data)]

    async def create_fact(
        self,
        content: str,
        fact_type: str = "GENERAL",
        confidence: float = 1.0,
    ) -> str:
        """Create a user fact."""
        data = await self._request(
            "POST",
            "/memory/facts",
            data={
                "fact_type": fact_type,
                "content": content,
                "confidence": confidence,
            },
        )

        return data.get("fact_id", "")

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def close(self) -> None:
        """Close the client session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
