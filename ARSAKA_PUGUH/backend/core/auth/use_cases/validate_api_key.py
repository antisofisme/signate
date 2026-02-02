"""
Validate API Key Use Case

Validates an API key and returns the associated context.
Used by middleware for service account authentication.

Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication
"""

from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from ..interfaces.api_key_repository import IApiKeyRepository
from ..domain.api_key import ApiKey
from ..exceptions import (
    ApiKeyInvalidError,
    ApiKeyRevokedError,
    ApiKeyExpiredError,
    InsufficientScopeError,
)


@dataclass
class ApiKeyContext:
    """Context extracted from validated API key."""
    key_id: UUID
    tenant_id: UUID
    created_by_user_id: UUID
    environment: str  # 'live' or 'test'
    scopes: List[str]
    name: str


@dataclass
class ValidateApiKeyResult:
    """Result of API key validation."""
    valid: bool
    context: Optional[ApiKeyContext]
    error: Optional[str]


class ValidateApiKeyUseCase:
    """Validate API key for service account authentication."""

    def __init__(
        self,
        api_key_repo: IApiKeyRepository,
        event_bus=None,
    ):
        self._repo = api_key_repo
        self._events = event_bus

    async def execute(
        self,
        full_key: str,
        required_scope: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> ValidateApiKeyResult:
        """Validate API key.

        Args:
            full_key: Full API key string (pk_live_xxx or pk_test_xxx)
            required_scope: Optional scope that must be present
            ip_address: Client IP address for logging

        Returns:
            ValidateApiKeyResult with context if valid

        Note:
            Updates usage statistics on successful validation.
        """
        # 1. Basic format check
        if not self._is_valid_format(full_key):
            return ValidateApiKeyResult(
                valid=False,
                context=None,
                error="Invalid API key format"
            )

        # 2. Hash the key and lookup
        key_hash = ApiKey.hash_key(full_key)
        api_key = await self._repo.get_by_hash(key_hash)

        if not api_key:
            return ValidateApiKeyResult(
                valid=False,
                context=None,
                error="API key not found"
            )

        # 3. Check if valid (not revoked, not expired)
        if not api_key.is_valid():
            if api_key.status.value == "revoked":
                return ValidateApiKeyResult(
                    valid=False,
                    context=None,
                    error="API key has been revoked"
                )
            else:
                return ValidateApiKeyResult(
                    valid=False,
                    context=None,
                    error="API key has expired"
                )

        # 4. Check required scope
        if required_scope and not api_key.has_scope(required_scope):
            return ValidateApiKeyResult(
                valid=False,
                context=None,
                error=f"API key lacks required scope: {required_scope}"
            )

        # 5. Update usage statistics
        await self._repo.update_usage(api_key.key_id, ip_address)

        # 6. Return success with context
        return ValidateApiKeyResult(
            valid=True,
            context=ApiKeyContext(
                key_id=api_key.key_id,
                tenant_id=api_key.tenant_id,
                created_by_user_id=api_key.created_by_user_id,
                environment=api_key.environment.value,
                scopes=api_key.scopes,
                name=api_key.name,
            ),
            error=None
        )

    async def execute_strict(
        self,
        full_key: str,
        required_scope: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> ApiKeyContext:
        """Validate API key with strict error handling.

        Same as execute() but raises exceptions instead of returning errors.

        Args:
            full_key: Full API key string
            required_scope: Optional scope that must be present
            ip_address: Client IP address for logging

        Returns:
            ApiKeyContext if valid

        Raises:
            ApiKeyInvalidError: If key format is wrong or not found
            ApiKeyRevokedError: If key has been revoked
            ApiKeyExpiredError: If key has expired
            InsufficientScopeError: If key lacks required scope
        """
        result = await self.execute(full_key, required_scope, ip_address)

        if not result.valid:
            error = result.error or "Invalid API key"

            if "revoked" in error.lower():
                raise ApiKeyRevokedError()
            elif "expired" in error.lower():
                raise ApiKeyExpiredError()
            elif "scope" in error.lower():
                raise InsufficientScopeError(required_scope or "unknown")
            else:
                raise ApiKeyInvalidError()

        return result.context

    def _is_valid_format(self, key: str) -> bool:
        """Check if key has valid format."""
        if not key:
            return False

        # Must start with pk_live_ or pk_test_
        if not (key.startswith("pk_live_") or key.startswith("pk_test_")):
            return False

        # Must have sufficient length (prefix + 32 hex chars)
        # pk_live_ = 8, pk_test_ = 8, hex = 32 -> total = 40
        if len(key) < 40:
            return False

        return True
