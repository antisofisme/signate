"""
API Key Routes

FastAPI router for API key management endpoints.
Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication

SECURITY: API key operations require "api_access" feature in subscription plan.
This is enforced at the route level using require_feature dependency.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..use_cases import (
    CreateApiKeyUseCase,
    CreateApiKeyRequest as CreateKeyInput,
    ValidateApiKeyUseCase,
    ListApiKeysUseCase,
    ListApiKeysRequest as ListKeysInput,
    GetApiKeyUseCase,
    RevokeApiKeyUseCase,
    RevokeApiKeyRequest as RevokeKeyInput,
    DeleteApiKeyUseCase,
)
from ..exceptions import (
    ValidationError,
    ApiKeyNotFoundError,
    ApiKeyLimitExceededError,
    ApiKeyInvalidError,
    ApiKeyRevokedError,
    ApiKeyExpiredError,
    InsufficientScopeError,
)
from .api_key_schemas import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    CreateApiKeyData,
    GetApiKeyResponse,
    ListApiKeysResponse,
    ListApiKeysData,
    UpdateApiKeyRequest,
    UpdateApiKeyResponse,
    RevokeApiKeyResponse,
    RevokeApiKeyData,
    DeleteApiKeyResponse,
    DeleteApiKeyData,
    ApiKeyInfo,
    ApiKeyErrorResponse,
)
from .dependencies import (
    get_current_user,
    get_client_ip,
    get_create_api_key_use_case,
    get_list_api_keys_use_case,
    get_api_key_use_case,
    get_revoke_api_key_use_case,
    get_delete_api_key_use_case,
)
from ..interfaces.token_service import TokenPayload

# SECURITY: Import feature enforcement for billing limit checks
from ...billing.api.dependencies import require_feature


router = APIRouter(prefix="/api-keys", tags=["api-keys"])


# ============================================================================
# Create API Key
# ============================================================================

@router.post(
    "",
    response_model=CreateApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ApiKeyErrorResponse, "description": "Validation error"},
        402: {"model": ApiKeyErrorResponse, "description": "Feature not available in plan"},
        403: {"model": ApiKeyErrorResponse, "description": "API key limit exceeded"},
    },
    summary="Create API Key",
    description="""
    Create a new API key for service account authentication.

    **WARNING**: The `secret_key` in the response is only shown once.
    Store it securely - it cannot be retrieved again.

    Scopes format: `{action}:{resource}` (e.g., `read:decisions`, `write:*`)
    Empty scopes = full access.

    **SECURITY**: Requires `api_access` feature in your subscription plan.
    Free plan users must upgrade to create API keys.
    """,
)
async def create_api_key(
    request: CreateApiKeyRequest,
    _: None = Depends(require_feature("api_access")),  # SECURITY: Check plan feature
    current_user: TokenPayload = Depends(get_current_user),
    use_case: CreateApiKeyUseCase = Depends(get_create_api_key_use_case),
):
    """Create a new API key.

    SECURITY: Requires api_access feature in subscription plan.
    """
    try:
        # Use active tenant from user context
        if not current_user.active_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "NO_TENANT_CONTEXT",
                    "message": "No active tenant. Please select a tenant first.",
                }
            )

        input_dto = CreateKeyInput(
            tenant_id=UUID(current_user.active_tenant_id),
            created_by_user_id=UUID(current_user.sub),
            name=request.name,
            description=request.description,
            environment=request.environment,
            scopes=request.scopes,
            expires_in_days=request.expires_in_days,
        )
        result = await use_case.execute(input_dto)

        return CreateApiKeyResponse(
            data=CreateApiKeyData(
                key_id=result.key_id,
                name=result.name,
                key_prefix=result.key_prefix,
                secret_key=result.secret_key,
                environment=result.environment,
                scopes=result.scopes,
                expires_at=result.expires_at,
                created_at=result.created_at,
            )
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": e.message,
                "field": e.field,
            }
        )
    except ApiKeyLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "API_KEY_LIMIT_EXCEEDED",
                "message": e.message,
            }
        )


# ============================================================================
# List API Keys
# ============================================================================

@router.get(
    "",
    response_model=ListApiKeysResponse,
    summary="List API Keys",
    description="List API keys for the current tenant.",
)
async def list_api_keys(
    include_revoked: bool = Query(False, description="Include revoked keys"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: TokenPayload = Depends(get_current_user),
    use_case: ListApiKeysUseCase = Depends(get_list_api_keys_use_case),
):
    """List API keys for the tenant."""
    if not current_user.active_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT_CONTEXT",
                "message": "No active tenant. Please select a tenant first.",
            }
        )

    input_dto = ListKeysInput(
        tenant_id=UUID(current_user.active_tenant_id),
        include_revoked=include_revoked,
        limit=limit,
        offset=offset,
    )
    result = await use_case.execute(input_dto)

    return ListApiKeysResponse(
        data=ListApiKeysData(
            api_keys=[
                ApiKeyInfo(
                    key_id=k.key_id,
                    name=k.name,
                    description=k.description,
                    key_prefix=k.key_prefix,
                    environment=k.environment,
                    scopes=k.scopes,
                    status=k.status,
                    expires_at=k.expires_at,
                    last_used_at=k.last_used_at,
                    usage_count=k.usage_count,
                    created_at=k.created_at,
                    created_by_user_id=k.created_by_user_id,
                )
                for k in result.api_keys
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            has_more=result.has_more,
        )
    )


# ============================================================================
# Get API Key
# ============================================================================

@router.get(
    "/{key_id}",
    response_model=GetApiKeyResponse,
    responses={
        404: {"model": ApiKeyErrorResponse, "description": "API key not found"},
    },
    summary="Get API Key",
    description="Get details of a specific API key.",
)
async def get_api_key(
    key_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    use_case: GetApiKeyUseCase = Depends(get_api_key_use_case),
):
    """Get API key by ID."""
    if not current_user.active_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT_CONTEXT",
                "message": "No active tenant. Please select a tenant first.",
            }
        )

    result = await use_case.execute(
        key_id=key_id,
        tenant_id=UUID(current_user.active_tenant_id),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "API_KEY_NOT_FOUND",
                "message": "API key not found",
            }
        )

    return GetApiKeyResponse(
        data=ApiKeyInfo(
            key_id=result.key_id,
            name=result.name,
            description=result.description,
            key_prefix=result.key_prefix,
            environment=result.environment,
            scopes=result.scopes,
            status=result.status,
            expires_at=result.expires_at,
            last_used_at=result.last_used_at,
            usage_count=result.usage_count,
            created_at=result.created_at,
            created_by_user_id=result.created_by_user_id,
        )
    )


# ============================================================================
# Revoke API Key
# ============================================================================

@router.post(
    "/{key_id}/revoke",
    response_model=RevokeApiKeyResponse,
    responses={
        404: {"model": ApiKeyErrorResponse, "description": "API key not found"},
    },
    summary="Revoke API Key",
    description="Revoke an API key. This action cannot be undone.",
)
async def revoke_api_key(
    key_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    use_case: RevokeApiKeyUseCase = Depends(get_revoke_api_key_use_case),
):
    """Revoke an API key."""
    if not current_user.active_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT_CONTEXT",
                "message": "No active tenant. Please select a tenant first.",
            }
        )

    try:
        input_dto = RevokeKeyInput(
            key_id=key_id,
            tenant_id=UUID(current_user.active_tenant_id),
            revoked_by_user_id=UUID(current_user.sub),
        )
        result = await use_case.execute(input_dto)

        return RevokeApiKeyResponse(
            data=RevokeApiKeyData(
                key_id=result.key_id,
                name=result.name,
                revoked=result.revoked,
                message=result.message,
            )
        )
    except ApiKeyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "API_KEY_NOT_FOUND",
                "message": "API key not found",
            }
        )


# ============================================================================
# Delete API Key
# ============================================================================

@router.delete(
    "/{key_id}",
    response_model=DeleteApiKeyResponse,
    responses={
        404: {"model": ApiKeyErrorResponse, "description": "API key not found"},
    },
    summary="Delete API Key",
    description="""
    Permanently delete an API key.

    **WARNING**: This removes the key from the database.
    Consider using revoke instead for audit trail.
    """,
)
async def delete_api_key(
    key_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    use_case: DeleteApiKeyUseCase = Depends(get_delete_api_key_use_case),
):
    """Delete an API key permanently."""
    if not current_user.active_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "NO_TENANT_CONTEXT",
                "message": "No active tenant. Please select a tenant first.",
            }
        )

    try:
        await use_case.execute(
            key_id=key_id,
            tenant_id=UUID(current_user.active_tenant_id),
        )

        return DeleteApiKeyResponse(
            data=DeleteApiKeyData(
                key_id=str(key_id),
                deleted=True,
            )
        )
    except ApiKeyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "API_KEY_NOT_FOUND",
                "message": "API key not found",
            }
        )
