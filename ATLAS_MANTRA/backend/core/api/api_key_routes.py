"""
API Key Routes

FastAPI routes for API Key management.
Used for MCP Server authentication key management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime

from ..domain.api_key_schema import (
    ApiKey,
    ApiKeyCreateRequest,
    ApiKeyUpdateRequest,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyValidateRequest,
    ApiKeyValidateResponse,
)
from ..repositories.api_key_repository import (
    ApiKeyRepository,
    get_api_key_repository,
    generate_api_key,
    hash_api_key,
    mask_api_key,
)


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


# ============================================================================
# Helper Functions
# ============================================================================

def api_key_to_response(api_key: ApiKey) -> ApiKeyResponse:
    """Convert ApiKey domain model to response DTO."""
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        permissions=api_key.permissions,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        revoked_at=api_key.revoked_at,
        created_by=api_key.created_by,
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "",
    response_model=ApiKeyListResponse,
    summary="List all API keys",
    description="Returns all API keys with masked prefixes. Does not return full keys."
)
async def list_api_keys(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repository: ApiKeyRepository = Depends(get_api_key_repository)
) -> ApiKeyListResponse:
    """List all API keys."""
    keys = repository.find_all(limit=limit, offset=offset)
    total = repository.count()

    return ApiKeyListResponse(
        keys=[api_key_to_response(k) for k in keys],
        total_count=total,
    )


@router.post(
    "",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    description="""
    Creates a new API key and returns it.

    **IMPORTANT**: The full key is only returned ONCE at creation time.
    Make sure to save it immediately - it cannot be retrieved later.
    """
)
async def create_api_key(
    request: ApiKeyCreateRequest,
    created_by: str = Query(..., description="User creating the key"),
    repository: ApiKeyRepository = Depends(get_api_key_repository)
) -> ApiKeyCreatedResponse:
    """Create a new API key."""
    # Generate the key
    full_key = generate_api_key()
    key_hash = hash_api_key(full_key)
    key_prefix = mask_api_key(full_key)

    # Create the domain model
    api_key = ApiKey(
        name=request.name,
        description=request.description,
        key_prefix=key_prefix,
        key_hash=key_hash,
        permissions=request.permissions,
        is_active=True,
        created_at=datetime.utcnow(),
        expires_at=request.expires_at,
        created_by=created_by,
    )

    # Save to repository
    try:
        repository.save(api_key)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        full_key=full_key,  # ONLY returned here!
        permissions=api_key.permissions,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        created_by=api_key.created_by,
    )


@router.get(
    "/{key_id}",
    response_model=ApiKeyResponse,
    summary="Get API key details",
    description="Returns API key details without the full key."
)
async def get_api_key(
    key_id: str,
    repository: ApiKeyRepository = Depends(get_api_key_repository)
) -> ApiKeyResponse:
    """Get API key by ID."""
    api_key = repository.find_by_id(key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found"
        )

    return api_key_to_response(api_key)


@router.put(
    "/{key_id}",
    response_model=ApiKeyResponse,
    summary="Update API key",
    description="Updates the name and/or description of an API key."
)
async def update_api_key(
    key_id: str,
    request: ApiKeyUpdateRequest,
    repository: ApiKeyRepository = Depends(get_api_key_repository)
) -> ApiKeyResponse:
    """Update API key name/description."""
    api_key = repository.find_by_id(key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found"
        )

    # Update fields
    updated = ApiKey(
        id=api_key.id,
        name=request.name if request.name is not None else api_key.name,
        description=request.description if request.description is not None else api_key.description,
        key_prefix=api_key.key_prefix,
        key_hash=api_key.key_hash,
        permissions=api_key.permissions,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        revoked_at=api_key.revoked_at,
        created_by=api_key.created_by,
    )

    repository.update(updated)
    return api_key_to_response(updated)


@router.post(
    "/{key_id}/revoke",
    response_model=ApiKeyResponse,
    summary="Revoke API key",
    description="Revokes an API key. The key will no longer be valid for authentication."
)
async def revoke_api_key(
    key_id: str,
    repository: ApiKeyRepository = Depends(get_api_key_repository)
) -> ApiKeyResponse:
    """Revoke an API key."""
    success = repository.revoke(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found"
        )

    # Return updated key
    api_key = repository.find_by_id(key_id)
    return api_key_to_response(api_key)


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API key",
    description="Permanently deletes an API key."
)
async def delete_api_key(
    key_id: str,
    repository: ApiKeyRepository = Depends(get_api_key_repository)
):
    """Delete an API key permanently."""
    success = repository.delete(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found"
        )

    return None


@router.post(
    "/validate",
    response_model=ApiKeyValidateResponse,
    summary="Validate API key",
    description="""
    Validates an API key and returns its details if valid.

    This endpoint is used by the MCP Server to validate incoming requests.
    It also updates the last_used_at timestamp for the key.
    """
)
async def validate_api_key(
    request: ApiKeyValidateRequest,
    repository: ApiKeyRepository = Depends(get_api_key_repository)
) -> ApiKeyValidateResponse:
    """Validate an API key."""
    # Hash the provided key
    key_hash = hash_api_key(request.key)

    # Look up by hash
    api_key = repository.find_by_hash(key_hash)

    if not api_key:
        return ApiKeyValidateResponse(
            valid=False,
            error="Invalid API key"
        )

    # Check if active
    if not api_key.is_active:
        return ApiKeyValidateResponse(
            valid=False,
            error="API key has been revoked"
        )

    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return ApiKeyValidateResponse(
            valid=False,
            error="API key has expired"
        )

    # Update last_used_at
    repository.update_last_used(api_key.id)

    return ApiKeyValidateResponse(
        valid=True,
        key_id=api_key.id,
        key_name=api_key.name,
        permissions=api_key.permissions,
    )
