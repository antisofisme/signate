"""
Create API Key Use Case

Creates a new API key for service account authentication.
Returns the full key only once - must be stored securely by user.

Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication
"""

from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from ..interfaces.api_key_repository import IApiKeyRepository
from ..domain.api_key import ApiKey, ApiKeyEnvironment, ApiKeyWithSecret
from ..exceptions import ApiKeyLimitExceededError, ValidationError


# Default limit per tenant
MAX_API_KEYS_PER_TENANT = 50


@dataclass
class CreateApiKeyRequest:
    """Create API key request data."""
    tenant_id: UUID
    created_by_user_id: UUID
    name: str
    description: Optional[str] = None
    environment: str = "live"  # 'live' or 'test'
    scopes: Optional[List[str]] = None
    expires_in_days: Optional[int] = None


@dataclass
class CreateApiKeyResult:
    """Create API key result.

    WARNING: secret_key is only returned once. Store it securely!
    """
    key_id: str
    tenant_id: str
    name: str
    key_prefix: str  # For display (e.g., "pk_live_a1b2")
    secret_key: str  # Full key - ONLY RETURNED ONCE
    environment: str
    scopes: List[str]
    expires_at: Optional[str]
    created_at: str


class CreateApiKeyUseCase:
    """Create a new API key for service account authentication."""

    def __init__(
        self,
        api_key_repo: IApiKeyRepository,
        max_keys_per_tenant: int = MAX_API_KEYS_PER_TENANT,
        event_bus=None,
    ):
        self._repo = api_key_repo
        self._max_keys = max_keys_per_tenant
        self._events = event_bus

    async def execute(self, request: CreateApiKeyRequest) -> CreateApiKeyResult:
        """Execute create API key.

        Args:
            request: Create API key request

        Returns:
            CreateApiKeyResult with secret key (only shown once!)

        Raises:
            ValidationError: If input is invalid
            ApiKeyLimitExceededError: If tenant has too many keys
        """
        # 1. Validate input
        self._validate_request(request)

        # 2. Check tenant key limit
        current_count = await self._repo.count_by_tenant(request.tenant_id)
        if current_count >= self._max_keys:
            raise ApiKeyLimitExceededError(self._max_keys)

        # 3. Generate key
        environment = ApiKeyEnvironment(request.environment)
        full_key = ApiKey.generate_key(environment)

        # 4. Create API key entity
        api_key = ApiKey.create(
            full_key=full_key,
            tenant_id=request.tenant_id,
            created_by_user_id=request.created_by_user_id,
            name=request.name,
            description=request.description,
            scopes=request.scopes,
            expires_in_days=request.expires_in_days,
        )

        # 5. Save to database
        saved_key = await self._repo.create(api_key)

        # 6. Return result with secret (only shown once!)
        return CreateApiKeyResult(
            key_id=str(saved_key.key_id),
            tenant_id=str(saved_key.tenant_id),
            name=saved_key.name,
            key_prefix=saved_key.key_prefix,
            secret_key=full_key,  # WARNING: Only returned once!
            environment=saved_key.environment.value,
            scopes=saved_key.scopes,
            expires_at=saved_key.expires_at.isoformat() if saved_key.expires_at else None,
            created_at=saved_key.created_at.isoformat(),
        )

    def _validate_request(self, request: CreateApiKeyRequest) -> None:
        """Validate create request."""
        if not request.name or not request.name.strip():
            raise ValidationError("Name is required", field="name")

        if len(request.name) > 100:
            raise ValidationError("Name must be 100 characters or less", field="name")

        if request.environment not in ("live", "test"):
            raise ValidationError(
                "Environment must be 'live' or 'test'",
                field="environment"
            )

        if request.expires_in_days is not None:
            if request.expires_in_days < 1:
                raise ValidationError(
                    "Expiration must be at least 1 day",
                    field="expires_in_days"
                )
            if request.expires_in_days > 365:
                raise ValidationError(
                    "Expiration cannot exceed 365 days",
                    field="expires_in_days"
                )

        # Validate scopes format
        if request.scopes:
            for scope in request.scopes:
                if not self._is_valid_scope(scope):
                    raise ValidationError(
                        f"Invalid scope format: {scope}. Expected format: action:resource",
                        field="scopes"
                    )

    def _is_valid_scope(self, scope: str) -> bool:
        """Validate scope format."""
        if scope == "*":
            return True

        parts = scope.split(":")
        if len(parts) != 2:
            return False

        action, resource = parts
        valid_actions = ("read", "write", "delete", "admin")
        if action not in valid_actions and not action.endswith("*"):
            return False

        return bool(resource.strip())
