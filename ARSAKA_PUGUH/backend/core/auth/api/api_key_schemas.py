"""
API Key Schemas

Pydantic models for API key HTTP transport.
Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Create API Key
# ============================================================================

class CreateApiKeyRequest(BaseModel):
    """POST /api-keys request."""
    name: str = Field(..., min_length=1, max_length=100, description="Display name for the key")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    environment: str = Field("live", description="Environment: 'live' or 'test'")
    scopes: Optional[List[str]] = Field(None, description="Permission scopes (empty = full access)")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiration")


class CreateApiKeyData(BaseModel):
    """Create API key response data."""
    key_id: str
    name: str
    key_prefix: str = Field(..., description="Display prefix (e.g., pk_live_a1b2)")
    secret_key: str = Field(..., description="Full key - STORE THIS! Only shown once.")
    environment: str
    scopes: List[str]
    expires_at: Optional[str]
    created_at: str
    warning: str = "Store the secret_key securely. It will not be shown again."


class CreateApiKeyResponse(BaseModel):
    """POST /api-keys response."""
    success: bool = True
    data: CreateApiKeyData


# ============================================================================
# Get API Key
# ============================================================================

class ApiKeyInfo(BaseModel):
    """API key info (without secret)."""
    key_id: str
    name: str
    description: Optional[str]
    key_prefix: str = Field(..., description="Display prefix (e.g., pk_live_a1b2)")
    environment: str
    scopes: List[str]
    status: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    usage_count: int
    created_at: str
    created_by_user_id: str


class GetApiKeyResponse(BaseModel):
    """GET /api-keys/{key_id} response."""
    success: bool = True
    data: ApiKeyInfo


# ============================================================================
# List API Keys
# ============================================================================

class ListApiKeysData(BaseModel):
    """List API keys response data."""
    api_keys: List[ApiKeyInfo]
    total: int
    limit: int
    offset: int
    has_more: bool


class ListApiKeysResponse(BaseModel):
    """GET /api-keys response."""
    success: bool = True
    data: ListApiKeysData


# ============================================================================
# Update API Key
# ============================================================================

class UpdateApiKeyRequest(BaseModel):
    """PATCH /api-keys/{key_id} request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    scopes: Optional[List[str]] = None


class UpdateApiKeyResponse(BaseModel):
    """PATCH /api-keys/{key_id} response."""
    success: bool = True
    data: ApiKeyInfo


# ============================================================================
# Revoke API Key
# ============================================================================

class RevokeApiKeyData(BaseModel):
    """Revoke API key response data."""
    key_id: str
    name: str
    revoked: bool
    message: str


class RevokeApiKeyResponse(BaseModel):
    """POST /api-keys/{key_id}/revoke response."""
    success: bool = True
    data: RevokeApiKeyData


# ============================================================================
# Delete API Key
# ============================================================================

class DeleteApiKeyData(BaseModel):
    """Delete API key response data."""
    key_id: str
    deleted: bool


class DeleteApiKeyResponse(BaseModel):
    """DELETE /api-keys/{key_id} response."""
    success: bool = True
    data: DeleteApiKeyData


# ============================================================================
# Error Response
# ============================================================================

class ApiKeyErrorDetail(BaseModel):
    """Error detail for API key operations."""
    code: str
    message: str
    field: Optional[str] = None


class ApiKeyErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: ApiKeyErrorDetail
