"""
MANTRA SDK Client

Main client class for interacting with ARSAKA_MANTRA Decision System.

Per MANTRA-LAW-006: This SDK provides read-only access and proposal capabilities.
All modifications require human approval through the dashboard.
"""

import httpx
from typing import Any, Optional
from datetime import datetime

from .models import (
    Decision,
    DecisionCreate,
    ValidationResult,
    FullValidationResult,
    RetrievalResult,
    TriggerCheckResult,
    DocumentType,
    DocumentGenerateRequest,
    GeneratedDocument,
    AnalyticsSummary,
    HealthDistribution,
    DecisionStats,
    DomainId,
    AspectId,
)
from .exceptions import (
    MantraError,
    ValidationError,
    AuthorizationError,
    NotFoundError,
    ConnectionError,
    RateLimitError,
)


class MantraClient:
    """
    Client for ARSAKA_MANTRA Decision System.

    Example:
        client = MantraClient("http://localhost:8000")
        decisions = client.list_decisions(domain="INT")

        # Propose a new decision (requires human approval)
        result = client.propose_decision(DecisionCreate(...))
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the MANTRA client.

        Args:
            base_url: Base URL of the MANTRA API (e.g., "http://localhost:8000")
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make an HTTP request."""
        client = self._get_client()
        try:
            response = client.request(method, path, params=params, json=json)

            if response.status_code == 404:
                data = response.json() if response.content else {}
                raise NotFoundError(
                    data.get("resource", "Resource"),
                    data.get("identifier", "unknown"),
                )
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(int(retry_after) if retry_after else None)
            elif response.status_code == 403:
                raise AuthorizationError()
            elif response.status_code >= 400:
                data = response.json() if response.content else {}
                raise MantraError(
                    data.get("message", f"Request failed with status {response.status_code}"),
                    code=data.get("code"),
                    details=data.get("details", {}),
                )

            return response.json()
        except httpx.ConnectError as e:
            raise ConnectionError(str(e))

    def close(self):
        """Close the client connection."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ========================================================================
    # Decision Operations
    # ========================================================================

    def get_decision(self, decision_id: str) -> Decision:
        """
        Get a decision by ID.

        Args:
            decision_id: The decision ID

        Returns:
            Decision object
        """
        data = self._request("GET", f"/api/v1/decisions/{decision_id}")
        return Decision(**data)

    def list_decisions(
        self,
        domain: Optional[str] = None,
        aspect: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[list[str]] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Decision]:
        """
        List decisions with optional filters.

        Args:
            domain: Filter by domain ID (INT, ARCH, CTL, EVO)
            aspect: Filter by aspect ID (A01-A16)
            status: Filter by status
            tags: Filter by tags
            search: Search query
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of decisions
        """
        params = {"limit": limit, "offset": offset}
        if domain:
            params["domain_id"] = domain
        if aspect:
            params["aspect_id"] = aspect
        if status:
            params["status"] = status
        if tags:
            params["tags"] = ",".join(tags)
        if search:
            params["search"] = search

        data = self._request("GET", "/api/v1/decisions", params=params)
        return [Decision(**d) for d in data.get("decisions", [])]

    def get_decision_matrix(self) -> dict[str, dict[str, list[Decision]]]:
        """
        Get the 4x4 decision matrix (domain x aspect).

        Returns:
            Nested dict: matrix[domain_id][aspect_id] = list of decisions
        """
        data = self._request("GET", "/api/v1/decisions/matrix")
        matrix = {}
        for domain, aspects in data.get("matrix", {}).items():
            matrix[domain] = {}
            for aspect, decisions in aspects.items():
                matrix[domain][aspect] = [Decision(**d) for d in decisions]
        return matrix

    def propose_decision(self, decision: DecisionCreate) -> dict[str, Any]:
        """
        Propose a new decision.

        Per MANTRA-LAW-006: This creates a PROPOSAL that requires human approval.
        The SDK cannot directly create approved decisions.

        Args:
            decision: The decision to propose

        Returns:
            Proposal result with decision_id and status
        """
        data = self._request(
            "POST",
            "/api/v1/decisions/propose",
            json=decision.model_dump(mode="json"),
        )
        return data

    # ========================================================================
    # Validation Operations
    # ========================================================================

    def validate_decision(self, decision: DecisionCreate) -> ValidationResult:
        """
        Validate a decision against MANTRA rules.

        Args:
            decision: The decision to validate

        Returns:
            Validation result with status and violations
        """
        data = self._request(
            "POST",
            "/api/v1/validate",
            json={"record": decision.model_dump(mode="json")},
        )
        return ValidationResult(**data)

    def validate_full(
        self,
        decision: DecisionCreate,
        include_ai: bool = True,
    ) -> FullValidationResult:
        """
        Run full 3-gate validation pipeline.

        Args:
            decision: The decision to validate
            include_ai: Whether to include Gate 2 (AI) validation

        Returns:
            Full validation result with all 3 gates
        """
        data = self._request(
            "POST",
            "/api/v1/validation/pipeline",
            json={
                "record": decision.model_dump(mode="json"),
                "include_ai": include_ai,
            },
        )
        return FullValidationResult(**data)

    def get_pending_approvals(self) -> list[dict[str, Any]]:
        """
        Get decisions pending human approval (Gate 3).

        Returns:
            List of pending decisions with their validation status
        """
        data = self._request("GET", "/api/v1/validation/pending")
        return data.get("pending", [])

    # ========================================================================
    # Retrieval Operations
    # ========================================================================

    def retrieve(
        self,
        query: str,
        file_path: Optional[str] = None,
        file_content: Optional[str] = None,
        scope_path: Optional[str] = None,
        max_results: int = 10,
        token_budget: int = 2000,
        use_cache: bool = True,
    ) -> RetrievalResult:
        """
        Context-aware decision retrieval.

        Args:
            query: Natural language query or keywords
            file_path: Current file path for trigger matching
            file_content: File content preview (first 2000 chars)
            scope_path: Filter by scope
            max_results: Maximum results
            token_budget: Token budget for context
            use_cache: Whether to use cache

        Returns:
            Retrieval result with matched decisions
        """
        data = self._request(
            "POST",
            "/api/v1/retrieval/retrieve",
            json={
                "query": query,
                "file_path": file_path,
                "file_content": file_content,
                "scope_path": scope_path,
                "max_results": max_results,
                "token_budget": token_budget,
                "use_cache": use_cache,
            },
        )
        return RetrievalResult(**data)

    def check_triggers(
        self,
        file_path: Optional[str] = None,
        file_content: Optional[str] = None,
        scope_path: Optional[str] = None,
        keywords: Optional[list[str]] = None,
    ) -> TriggerCheckResult:
        """
        Check which triggers match the given context.

        Args:
            file_path: File path for pattern matching
            file_content: File content for keyword matching
            scope_path: Scope for filtering
            keywords: Additional keywords

        Returns:
            Trigger check result
        """
        data = self._request(
            "POST",
            "/api/v1/retrieval/check-triggers",
            json={
                "file_path": file_path,
                "file_content": file_content,
                "scope_path": scope_path,
                "keywords": keywords,
            },
        )
        return TriggerCheckResult(**data)

    def get_hot_decisions(self, limit: int = 10) -> list[str]:
        """
        Get frequently accessed decisions.

        Args:
            limit: Maximum number of decisions

        Returns:
            List of decision IDs
        """
        data = self._request(
            "GET",
            "/api/v1/retrieval/hot-decisions",
            params={"limit": limit},
        )
        return data.get("decisions", [])

    # ========================================================================
    # Document Generation
    # ========================================================================

    def list_document_types(self) -> list[DocumentType]:
        """
        List available document types.

        Returns:
            List of document type info
        """
        data = self._request("GET", "/api/v1/docs/types")
        return [DocumentType(**t) for t in data]

    def generate_document(self, request: DocumentGenerateRequest) -> GeneratedDocument:
        """
        Generate a document from decisions.

        Args:
            request: Document generation request

        Returns:
            Generated document
        """
        data = self._request(
            "POST",
            "/api/v1/docs/generate",
            json=request.model_dump(mode="json"),
        )
        return GeneratedDocument(**data)

    # ========================================================================
    # Analytics Operations
    # ========================================================================

    def get_analytics_summary(self) -> AnalyticsSummary:
        """
        Get usage analytics summary.

        Returns:
            Analytics summary
        """
        data = self._request("GET", "/api/v1/analytics/summary")
        return AnalyticsSummary(**data)

    def get_health_distribution(self) -> HealthDistribution:
        """
        Get decision health distribution.

        Returns:
            Health distribution
        """
        data = self._request("GET", "/api/v1/analytics/health-distribution")
        return HealthDistribution(**data)

    def get_decision_stats(self, decision_id: str) -> DecisionStats:
        """
        Get statistics for a specific decision.

        Args:
            decision_id: The decision ID

        Returns:
            Decision statistics
        """
        data = self._request("GET", f"/api/v1/analytics/decisions/{decision_id}/stats")
        return DecisionStats(**data)

    def track_event(
        self,
        decision_id: str,
        event_type: str,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Track a usage event.

        Args:
            decision_id: The decision ID
            event_type: Event type (view, apply, copy, etc.)
            context: Optional event context

        Returns:
            Tracking result
        """
        return self._request(
            "POST",
            "/api/v1/analytics/track",
            json={
                "decision_id": decision_id,
                "event_type": event_type,
                "context": context or {},
            },
        )

    def submit_feedback(
        self,
        decision_id: str,
        is_helpful: bool,
        comment: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Submit feedback for a decision.

        Args:
            decision_id: The decision ID
            is_helpful: Whether the decision was helpful
            comment: Optional comment

        Returns:
            Feedback result
        """
        return self._request(
            "POST",
            "/api/v1/analytics/feedback",
            json={
                "decision_id": decision_id,
                "is_helpful": is_helpful,
                "comment": comment,
            },
        )

    # ========================================================================
    # Search Operations
    # ========================================================================

    def semantic_search(
        self,
        query: str,
        domain: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Semantic search for decisions.

        Args:
            query: Natural language query
            domain: Optional domain filter
            limit: Maximum results

        Returns:
            Search results with scores
        """
        params = {"q": query, "limit": limit}
        if domain:
            params["domain"] = domain
        return self._request("GET", "/api/v1/search", params=params)

    # ========================================================================
    # Comparison Operations
    # ========================================================================

    def compare_decisions(
        self,
        decision_id_1: str,
        decision_id_2: str,
    ) -> dict[str, Any]:
        """
        Compare two decisions side by side.

        Args:
            decision_id_1: First decision ID
            decision_id_2: Second decision ID

        Returns:
            Comparison result
        """
        return self._request(
            "GET",
            "/api/v1/decisions/compare",
            params={"id1": decision_id_1, "id2": decision_id_2},
        )

    def get_decision_history(self, decision_id: str) -> list[dict[str, Any]]:
        """
        Get version history for a decision.

        Args:
            decision_id: The decision ID

        Returns:
            Version history
        """
        return self._request("GET", f"/api/v1/decisions/{decision_id}/history")
