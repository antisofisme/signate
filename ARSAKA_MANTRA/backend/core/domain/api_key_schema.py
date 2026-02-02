"""
API Key Schema

Pydantic models for API Key management.
Used for MCP Server authentication.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ============================================================================
# Enumerations
# ============================================================================

class ApiKeyPermission(str, Enum):
    """Available permissions for API keys"""
    READ = "read"
    WRITE = "write"
    PROPOSE = "propose"
    ADMIN = "admin"


# ============================================================================
# Domain Models
# ============================================================================

class ApiKey(BaseModel):
    """API Key domain model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    key_prefix: str  # Masked for display: mk_A1b2...O5p6
    key_hash: str  # SHA-256 hash
    permissions: List[str] = Field(default_factory=lambda: ["read"])
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_by: str


class ApiKeyWithFullKey(BaseModel):
    """
    API Key with the full key included.
    ONLY returned on creation - key is shown ONCE.
    """
    id: str
    name: str
    description: Optional[str] = None
    key_prefix: str
    full_key: str  # ONLY on creation
    permissions: List[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    created_by: str


# ============================================================================
# Request/Response DTOs
# ============================================================================

class ApiKeyCreateRequest(BaseModel):
    """Request to create a new API key"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    permissions: List[str] = Field(default_factory=lambda: ["read"])
    expires_at: Optional[datetime] = None


class ApiKeyUpdateRequest(BaseModel):
    """Request to update an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class ApiKeyResponse(BaseModel):
    """API key response (without hash or full key)"""
    id: str
    name: str
    description: Optional[str] = None
    key_prefix: str
    permissions: List[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_by: str


class ApiKeyCreatedResponse(BaseModel):
    """
    Response when creating a new API key.
    IMPORTANT: full_key is only shown ONCE!
    """
    id: str
    name: str
    description: Optional[str] = None
    key_prefix: str
    full_key: str  # SHOWN ONCE - user must save this!
    permissions: List[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    created_by: str
    warning: str = "Save this key now! It will not be shown again."


class ApiKeyListResponse(BaseModel):
    """Response for listing API keys"""
    keys: List[ApiKeyResponse]
    total_count: int


class ApiKeyValidateRequest(BaseModel):
    """Request to validate an API key"""
    key: str


class ApiKeyValidateResponse(BaseModel):
    """Response for API key validation"""
    valid: bool
    key_id: Optional[str] = None
    key_name: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    error: Optional[str] = None
