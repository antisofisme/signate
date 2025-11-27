# Security Architecture for Multi-Tenant Digital Signage System

## Executive Summary

This document outlines the comprehensive security architecture for a multi-tenant digital signage system, covering authentication, authorization, data security, device management, and API protection. The system follows defense-in-depth principles with multiple security layers.

## Current Security Assessment

### Strengths Identified
- ✅ JWT-based authentication with access/refresh token pattern
- ✅ Bcrypt password hashing (cost factor 12)
- ✅ Pydantic schemas for input validation
- ✅ SQLAlchemy ORM preventing SQL injection
- ✅ CORS properly configured with whitelisted origins
- ✅ Role-based access control (admin/editor/viewer)
- ✅ Secure device activation with time-limited codes

### Critical Security Gaps
- ❌ **No rate limiting implementation** (login brute force risk)
- ❌ **Missing multi-tenant data isolation** (no organization/tenant model)
- ❌ **No CSRF protection** for state-changing operations
- ❌ **Weak JWT secret in default config**
- ❌ **No password complexity requirements**
- ❌ **Missing security headers** (CSP, HSTS, X-Frame-Options)
- ❌ **No audit logging for security events**
- ❌ **Device activation codes using weak randomness**
- ❌ **No API versioning strategy**
- ❌ **Missing encryption for sensitive data at rest**

## 1. Authentication Security Architecture

### 1.1 JWT Implementation Improvements

```python
# backend/app/core/security/jwt_enhanced.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from secrets import token_urlsafe
import hashlib

class EnhancedJWTManager:
    """Enhanced JWT manager with security best practices"""

    def __init__(self, settings):
        self.settings = settings
        self.algorithm = "RS256"  # Use RS256 instead of HS256
        self._validate_secret_strength()

    def _validate_secret_strength(self):
        """Ensure JWT secret meets complexity requirements"""
        if len(self.settings.JWT_SECRET) < 32:
            raise ValueError("JWT secret must be at least 32 characters")

        # Check entropy
        entropy = len(set(self.settings.JWT_SECRET))
        if entropy < 16:
            raise ValueError("JWT secret has insufficient entropy")

    def create_access_token(
        self,
        user_id: int,
        username: str,
        role: str,
        organization_id: Optional[int] = None,
        permissions: List[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> str:
        """Create access token with enhanced claims"""

        # Generate unique token ID for revocation
        jti = token_urlsafe(16)

        payload = {
            # Standard claims
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "nbf": datetime.now(timezone.utc),
            "jti": jti,

            # Custom claims
            "username": username,
            "role": role,
            "org_id": organization_id,
            "permissions": permissions or [],
            "type": "access",

            # Security context
            "fingerprint": device_fingerprint,
            "iss": self.settings.JWT_ISSUER,
            "aud": self.settings.JWT_AUDIENCE
        }

        # Store JTI in Redis for revocation checking
        self._store_token_metadata(jti, user_id, "access")

        return jwt.encode(payload, self.settings.JWT_PRIVATE_KEY, algorithm=self.algorithm)

    def verify_token(self, token: str, expected_type: str = "access") -> Optional[Dict]:
        """Verify token with additional security checks"""
        try:
            # Decode with audience and issuer validation
            payload = jwt.decode(
                token,
                self.settings.JWT_PUBLIC_KEY,
                algorithms=[self.algorithm],
                audience=self.settings.JWT_AUDIENCE,
                issuer=self.settings.JWT_ISSUER,
                options={"verify_exp": True, "verify_nbf": True}
            )

            # Check token type
            if payload.get("type") != expected_type:
                return None

            # Check if token is revoked
            if self._is_token_revoked(payload.get("jti")):
                return None

            # Verify device fingerprint if present
            if not self._verify_fingerprint(payload.get("fingerprint")):
                return None

            return payload

        except JWTError:
            return None

    def _is_token_revoked(self, jti: str) -> bool:
        """Check if token is in revocation list"""
        # Implementation with Redis
        return redis_client.exists(f"revoked_token:{jti}")
```

### 1.2 Enhanced Password Security

```python
# backend/app/core/security/password_enhanced.py
import re
from typing import Tuple, List
import bcrypt
from passlib.context import CryptContext
import secrets
import hashlib

class PasswordManager:
    """Enhanced password management with security best practices"""

    # Use Argon2 for new passwords, maintain bcrypt compatibility
    pwd_context = CryptContext(
        schemes=["argon2", "bcrypt"],
        default="argon2",
        argon2__rounds=4,
        argon2__memory_cost=65536,
        argon2__parallelism=2,
        bcrypt__rounds=12,
        deprecated="auto"
    )

    # Password complexity requirements
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Common weak passwords list (load from file in production)
    COMMON_PASSWORDS = {
        "password123", "admin123", "12345678", "qwerty123",
        "password", "123456", "admin", "letmein"
    }

    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against security requirements

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")

        # Complexity checks
        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if cls.REQUIRE_NUMBERS and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")

        if cls.REQUIRE_SPECIAL and not re.search(f"[{re.escape(cls.SPECIAL_CHARS)}]", password):
            errors.append("Password must contain at least one special character")

        # Check against common passwords
        if password.lower() in cls.COMMON_PASSWORDS:
            errors.append("Password is too common")

        # Check for sequential characters
        if cls._has_sequential_chars(password):
            errors.append("Password contains sequential characters")

        # Calculate entropy
        entropy = cls._calculate_entropy(password)
        if entropy < 50:  # NIST recommends minimum 50 bits
            errors.append("Password is not complex enough")

        return len(errors) == 0, errors

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash password with Argon2"""
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify password and update hash if needed"""
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def generate_secure_password(cls, length: int = 16) -> str:
        """Generate cryptographically secure random password"""
        alphabet = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            + cls.SPECIAL_CHARS
        )
        return ''.join(secrets.choice(alphabet) for _ in range(length))
```

### 1.3 Login Rate Limiting

```python
# backend/app/core/security/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from datetime import datetime, timedelta
import hashlib

class LoginRateLimiter:
    """Advanced rate limiting for authentication endpoints"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.progressive_delay = True

    def check_rate_limit(self, identifier: str, endpoint: str = "login") -> Tuple[bool, int]:
        """
        Check if identifier (IP/username) is rate limited

        Returns:
            Tuple of (is_allowed, seconds_until_retry)
        """
        key = f"rate_limit:{endpoint}:{identifier}"
        attempts = self.redis.get(key)

        if not attempts:
            return True, 0

        attempts = int(attempts)

        # Progressive lockout
        if self.progressive_delay:
            lockout_multiplier = min(attempts // self.max_attempts, 5)
            lockout_time = self.lockout_duration * lockout_multiplier
        else:
            lockout_time = self.lockout_duration

        # Check if locked out
        lockout_key = f"{key}:lockout"
        ttl = self.redis.ttl(lockout_key)

        if ttl > 0:
            return False, ttl

        if attempts >= self.max_attempts:
            # Apply lockout
            self.redis.setex(lockout_key, lockout_time, "locked")
            # Log security event
            self._log_security_event(identifier, endpoint, "rate_limit_exceeded")
            return False, lockout_time

        return True, 0

    def record_attempt(self, identifier: str, endpoint: str = "login", success: bool = False):
        """Record login attempt"""
        key = f"rate_limit:{endpoint}:{identifier}"

        if success:
            # Reset on successful login
            self.redis.delete(key)
            self.redis.delete(f"{key}:lockout")
        else:
            # Increment failed attempts
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 3600)  # Reset after 1 hour
            pipe.execute()

    def _log_security_event(self, identifier: str, endpoint: str, event: str):
        """Log security events for monitoring"""
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "identifier": identifier,
            "endpoint": endpoint
        }
        self.redis.lpush("security_events", json.dumps(event_data))
        self.redis.ltrim("security_events", 0, 9999)  # Keep last 10000 events

# FastAPI Integration
from fastapi import Request, HTTPException, status

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri="redis://192.168.5.12:6379"
)

@router.post("/login")
@limiter.limit("5/minute")  # 5 login attempts per minute per IP
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    # Additional username-based rate limiting
    rate_limiter = LoginRateLimiter(redis_client)

    # Check IP rate limit
    ip_address = request.client.host
    ip_allowed, ip_retry = rate_limiter.check_rate_limit(ip_address, "login_ip")

    if not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts from IP. Retry after {ip_retry} seconds"
        )

    # Check username rate limit
    username_hash = hashlib.sha256(login_data.username.encode()).hexdigest()[:16]
    user_allowed, user_retry = rate_limiter.check_rate_limit(username_hash, "login_user")

    if not user_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts for this account. Retry after {user_retry} seconds"
        )

    # Perform authentication...
    success = authenticate_user(login_data)

    # Record attempt
    rate_limiter.record_attempt(ip_address, "login_ip", success)
    rate_limiter.record_attempt(username_hash, "login_user", success)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Return tokens...
```

## 2. Authorization & Multi-Tenant Security

### 2.1 Multi-Tenant Data Model

```python
# backend/app/models/organization.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Organization(Base):
    """Multi-tenant organization model"""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)

    # Security settings
    enforce_2fa = Column(Boolean, default=False)
    password_policy = Column(JSON, default={})
    ip_whitelist = Column(ARRAY(String), default=[])

    # Limits
    max_users = Column(Integer, default=10)
    max_devices = Column(Integer, default=50)
    max_content_gb = Column(Integer, default=100)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    users = relationship("User", back_populates="organization")
    devices = relationship("Device", back_populates="organization")
    content = relationship("Content", back_populates="organization")

# Update User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    # ... existing fields

    # Add organization relationship
    organization = relationship("Organization", back_populates="users")
```

### 2.2 Row-Level Security Implementation

```python
# backend/app/core/security/rls.py
from typing import Optional, List, Type
from sqlalchemy.orm import Query, Session
from fastapi import HTTPException, status
from app.models.user import User

class RowLevelSecurity:
    """Implement row-level security for multi-tenant access"""

    @staticmethod
    def apply_tenant_filter(
        query: Query,
        user: User,
        model: Type,
        allow_superuser_bypass: bool = True
    ) -> Query:
        """
        Apply tenant filtering to query

        Args:
            query: SQLAlchemy query
            user: Current user
            model: Model being queried
            allow_superuser_bypass: Allow superusers to see all data

        Returns:
            Filtered query
        """
        # Superuser bypass (for system administration)
        if allow_superuser_bypass and user.is_superuser:
            return query

        # Check if model has organization_id
        if not hasattr(model, 'organization_id'):
            raise ValueError(f"Model {model.__name__} does not support multi-tenancy")

        # Apply tenant filter
        return query.filter(model.organization_id == user.organization_id)

    @staticmethod
    def check_resource_access(
        resource: Any,
        user: User,
        permission: str = "read",
        raise_on_failure: bool = True
    ) -> bool:
        """
        Check if user can access a specific resource

        Args:
            resource: Resource to check
            user: Current user
            permission: Required permission
            raise_on_failure: Raise exception if access denied

        Returns:
            Boolean indicating access permission
        """
        # Superuser bypass
        if user.is_superuser:
            return True

        # Check organization match
        if hasattr(resource, 'organization_id'):
            if resource.organization_id != user.organization_id:
                if raise_on_failure:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to resource from another organization"
                    )
                return False

        # Check specific permissions
        if not PermissionChecker.has_permission(user, resource, permission):
            if raise_on_failure:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {permission} operation"
                )
            return False

        return True

# Usage in API endpoints
@router.get("/devices")
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Apply RLS automatically
    query = db.query(Device)
    query = RowLevelSecurity.apply_tenant_filter(query, current_user, Device)

    devices = query.all()
    return devices

@router.put("/devices/{device_id}")
def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check access permission
    RowLevelSecurity.check_resource_access(device, current_user, "write")

    # Update device...
```

### 2.3 Advanced RBAC Implementation

```python
# backend/app/core/security/rbac.py
from enum import Enum
from typing import List, Dict, Set

class Permission(str, Enum):
    """System permissions"""
    # Device permissions
    DEVICE_VIEW = "device:view"
    DEVICE_CREATE = "device:create"
    DEVICE_UPDATE = "device:update"
    DEVICE_DELETE = "device:delete"
    DEVICE_ASSIGN_CONTENT = "device:assign_content"

    # Content permissions
    CONTENT_VIEW = "content:view"
    CONTENT_UPLOAD = "content:upload"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    CONTENT_PUBLISH = "content:publish"

    # User permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Admin permissions
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_BILLING = "admin:billing"
    ADMIN_AUDIT = "admin:audit"

class Role:
    """Role definitions with permissions"""

    ROLES = {
        "admin": {
            "name": "Administrator",
            "permissions": set(Permission),  # All permissions
            "inherits": []
        },
        "manager": {
            "name": "Manager",
            "permissions": {
                Permission.DEVICE_VIEW,
                Permission.DEVICE_CREATE,
                Permission.DEVICE_UPDATE,
                Permission.DEVICE_ASSIGN_CONTENT,
                Permission.CONTENT_VIEW,
                Permission.CONTENT_UPLOAD,
                Permission.CONTENT_UPDATE,
                Permission.CONTENT_PUBLISH,
                Permission.USER_VIEW,
            },
            "inherits": ["editor"]
        },
        "editor": {
            "name": "Editor",
            "permissions": {
                Permission.DEVICE_VIEW,
                Permission.DEVICE_ASSIGN_CONTENT,
                Permission.CONTENT_VIEW,
                Permission.CONTENT_UPLOAD,
                Permission.CONTENT_UPDATE,
            },
            "inherits": ["viewer"]
        },
        "viewer": {
            "name": "Viewer",
            "permissions": {
                Permission.DEVICE_VIEW,
                Permission.CONTENT_VIEW,
            },
            "inherits": []
        }
    }

    @classmethod
    def get_permissions(cls, role: str) -> Set[Permission]:
        """Get all permissions for a role including inherited"""
        if role not in cls.ROLES:
            return set()

        role_def = cls.ROLES[role]
        permissions = role_def["permissions"].copy()

        # Add inherited permissions
        for inherited_role in role_def.get("inherits", []):
            permissions.update(cls.get_permissions(inherited_role))

        return permissions

class PermissionChecker:
    """Check user permissions"""

    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_permissions = Role.get_permissions(user.role)
        return permission in user_permissions

    @staticmethod
    def require_permission(permission: Permission):
        """Decorator to require permission for endpoint"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user from kwargs
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                if not PermissionChecker.has_permission(current_user, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission}' required"
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator

# Usage
@router.post("/devices")
@PermissionChecker.require_permission(Permission.DEVICE_CREATE)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_active_user)
):
    # Create device...
```

## 3. Data Security

### 3.1 Input Validation & Sanitization

```python
# backend/app/core/security/validation.py
import re
import html
import bleach
from typing import Any, Dict, List
from pydantic import BaseModel, validator, Field

class SecurityValidator:
    """Enhanced input validation and sanitization"""

    # SQL injection patterns
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)",
        r"(--|\||;|\/\*|\*\/)",
        r"(\bOR\b\s*\d+\s*=\s*\d+)",
        r"(\bAND\b\s*\d+\s*=\s*\d+)"
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>"
    ]

    @classmethod
    def validate_sql_safe(cls, value: str) -> str:
        """Validate input doesn't contain SQL injection attempts"""
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError("Potential SQL injection detected")
        return value

    @classmethod
    def sanitize_html(cls, value: str, allowed_tags: List[str] = None) -> str:
        """Sanitize HTML input to prevent XSS"""
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a']

        # Use bleach for HTML sanitization
        cleaned = bleach.clean(
            value,
            tags=allowed_tags,
            attributes={'a': ['href', 'title']},
            protocols=['http', 'https'],
            strip=True
        )

        return cleaned

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate and sanitize filenames"""
        # Remove path traversal attempts
        filename = filename.replace("../", "").replace("..\\", "")

        # Allow only safe characters
        safe_chars = re.compile(r'^[\w\-. ]+$')
        if not safe_chars.match(filename):
            raise ValueError("Invalid filename characters")

        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.pdf'}
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            raise ValueError(f"File type {ext} not allowed")

        return filename

# Enhanced Pydantic models with validation
class DeviceCreateSecure(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=100)
    ip_address: Optional[str] = None

    @validator('device_name')
    def validate_device_name(cls, v):
        # Prevent XSS in device names
        return html.escape(v.strip())

    @validator('ip_address')
    def validate_ip_address(cls, v):
        if v:
            # Validate IP format
            import ipaddress
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError("Invalid IP address format")
        return v

class ContentUploadSecure(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('title', 'description')
    def sanitize_text(cls, v):
        if v:
            # Remove any HTML/script tags
            return SecurityValidator.sanitize_html(v, allowed_tags=[])
        return v
```

### 3.2 Encryption for Sensitive Data

```python
# backend/app/core/security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class EncryptionManager:
    """Manage encryption for sensitive data at rest"""

    def __init__(self, master_key: str):
        # Derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt',  # Use proper salt management in production
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a field value"""
        if not plaintext:
            return plaintext

        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_field(self, ciphertext: str) -> str:
        """Decrypt a field value"""
        if not ciphertext:
            return ciphertext

        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # Log decryption failure
            return None

# SQLAlchemy encrypted field
from sqlalchemy.types import TypeDecorator, String

class EncryptedField(TypeDecorator):
    """SQLAlchemy type for encrypted fields"""

    impl = String
    cache_ok = True

    def __init__(self, encryption_manager: EncryptionManager, *args, **kwargs):
        self.encryption_manager = encryption_manager
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        """Encrypt on save"""
        if value is not None:
            return self.encryption_manager.encrypt_field(value)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt on load"""
        if value is not None:
            return self.encryption_manager.decrypt_field(value)
        return value

# Usage in models
class SensitiveData(Base):
    __tablename__ = "sensitive_data"

    id = Column(Integer, primary_key=True)
    # Encrypted fields
    api_key = Column(EncryptedField(encryption_manager), nullable=True)
    password_backup = Column(EncryptedField(encryption_manager), nullable=True)
    personal_data = Column(EncryptedField(encryption_manager), nullable=True)
```

## 4. Device Security

### 4.1 Secure Device Activation

```python
# backend/app/core/security/device_activation.py
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Tuple

class SecureDeviceActivation:
    """Enhanced device activation with security measures"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.code_length = 6
        self.expiry_minutes = 10

    def generate_activation_code(self, device_id: Optional[int] = None) -> Tuple[str, str]:
        """
        Generate secure activation code with HMAC verification

        Returns:
            Tuple of (activation_code, verification_token)
        """
        # Generate cryptographically secure random code
        code = ''.join([str(secrets.randbelow(10)) for _ in range(self.code_length)])

        # Create HMAC for verification
        timestamp = int(datetime.utcnow().timestamp())
        data = f"{code}:{timestamp}:{device_id or 'new'}"

        verification_token = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        return code, verification_token

    def verify_activation_code(
        self,
        code: str,
        verification_token: str,
        device_id: Optional[int] = None
    ) -> bool:
        """Verify activation code with HMAC"""
        # Recreate HMAC and compare
        for time_offset in range(0, self.expiry_minutes * 60, 30):
            timestamp = int((datetime.utcnow() - timedelta(seconds=time_offset)).timestamp())
            data = f"{code}:{timestamp}:{device_id or 'new'}"

            expected_token = hmac.new(
                self.secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(verification_token, expected_token):
                return True

        return False

    def generate_device_token(self, device_id: int, organization_id: int) -> str:
        """Generate long-lived device authentication token"""
        # Create JWT specifically for devices
        payload = {
            "device_id": device_id,
            "org_id": organization_id,
            "type": "device",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=365),  # Long-lived
            "jti": secrets.token_urlsafe(16)
        }

        # Sign with device-specific key
        device_key = f"{self.secret_key}:device:{device_id}"
        token = jwt.encode(payload, device_key, algorithm="HS256")

        return token

# Enhanced device registration endpoint
@router.post("/devices/activate")
def activate_device(
    activation_data: DeviceActivation,
    request: Request,
    db: Session = Depends(get_db)
):
    # Rate limit activation attempts
    rate_limiter = LoginRateLimiter(redis_client)
    ip_address = request.client.host

    allowed, retry = rate_limiter.check_rate_limit(
        f"{ip_address}:{activation_data.code}",
        "device_activation"
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many activation attempts. Retry after {retry} seconds"
        )

    # Find pending device by code
    device = db.query(Device).filter(
        Device.unique_code == activation_data.code,
        Device.status == "pending"
    ).first()

    if not device:
        rate_limiter.record_attempt(f"{ip_address}:{activation_data.code}", "device_activation", False)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired activation code"
        )

    # Verify code hasn't expired
    if device.code_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Activation code has expired"
        )

    # Verify HMAC if using enhanced security
    activator = SecureDeviceActivation(settings.DEVICE_SECRET)
    if not activator.verify_activation_code(
        activation_data.code,
        activation_data.verification_token,
        device.id
    ):
        rate_limiter.record_attempt(f"{ip_address}:{activation_data.code}", "device_activation", False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification token"
        )

    # Bind device to IP
    device.ip_address = ip_address
    device.status = "active"
    device.activated_at = datetime.utcnow()

    # Generate device token
    device_token = activator.generate_device_token(device.id, device.organization_id)
    device.auth_token_hash = hashlib.sha256(device_token.encode()).hexdigest()

    db.commit()

    # Log activation event
    log_security_event("device_activated", {
        "device_id": device.id,
        "ip_address": ip_address,
        "activation_method": "code"
    })

    return {
        "device_id": device.id,
        "device_token": device_token,
        "status": "active"
    }
```

### 4.2 Device Authentication & Heartbeat Security

```python
# backend/app/core/security/device_auth.py
from typing import Optional
import hashlib
from fastapi import Header, HTTPException, status

class DeviceAuthenticator:
    """Authenticate and authorize device requests"""

    @staticmethod
    def verify_device_token(
        authorization: str = Header(None),
        x_device_id: int = Header(None),
        db: Session = Depends(get_db)
    ) -> Device:
        """Verify device authentication token"""

        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Device token required"
            )

        token = authorization.replace("Bearer ", "")

        # Verify token format and signature
        try:
            # Decode without verification first to get device_id
            unverified = jwt.decode(token, options={"verify_signature": False})
            device_id = unverified.get("device_id")

            if device_id != x_device_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Device ID mismatch"
                )

            # Now verify with device-specific key
            device_key = f"{settings.DEVICE_SECRET}:device:{device_id}"
            payload = jwt.decode(token, device_key, algorithms=["HS256"])

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid device token"
            )

        # Get device from database
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        # Verify token hash matches
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if device.auth_token_hash != token_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        # Check device status
        if device.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device is {device.status}"
            )

        return device

# Secure heartbeat endpoint
@router.post("/devices/{device_id}/heartbeat")
def device_heartbeat(
    device_id: int,
    heartbeat_data: HeartbeatData,
    device: Device = Depends(DeviceAuthenticator.verify_device_token),
    db: Session = Depends(get_db)
):
    # Verify device ID matches token
    if device.id != device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID mismatch"
        )

    # Validate heartbeat data
    if heartbeat_data.timestamp:
        # Check timestamp is recent (prevent replay attacks)
        time_diff = abs((datetime.utcnow() - heartbeat_data.timestamp).total_seconds())
        if time_diff > 60:  # More than 1 minute difference
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Heartbeat timestamp is stale"
            )

    # Update device status
    device.last_seen = datetime.utcnow()
    device.connection_status = "online"

    # Store metrics if provided
    if heartbeat_data.metrics:
        store_device_metrics(device_id, heartbeat_data.metrics)

    db.commit()

    return {"status": "ok", "timestamp": datetime.utcnow()}
```

## 5. API Security

### 5.1 Security Headers

```python
# backend/app/core/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # HSTS - Enforce HTTPS
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Adjust for your needs
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self';"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )

        return response

# Add to FastAPI app
app.add_middleware(SecurityHeadersMiddleware)
```

### 5.2 CSRF Protection

```python
# backend/app/core/security/csrf.py
import secrets
import hmac
import hashlib
from fastapi import Request, HTTPException, status
from typing import Optional

class CSRFProtection:
    """CSRF protection for state-changing operations"""

    def __init__(self, secret: str):
        self.secret = secret
        self.token_length = 32
        self.header_name = "X-CSRF-Token"
        self.cookie_name = "csrf_token"

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token tied to session"""
        random_token = secrets.token_urlsafe(self.token_length)

        # Create HMAC of token with session
        mac = hmac.new(
            self.secret.encode(),
            f"{random_token}:{session_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{random_token}.{mac}"

    def verify_token(self, token: str, session_id: str) -> bool:
        """Verify CSRF token"""
        try:
            random_token, mac = token.rsplit(".", 1)

            expected_mac = hmac.new(
                self.secret.encode(),
                f"{random_token}:{session_id}".encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(mac, expected_mac)
        except (ValueError, AttributeError):
            return False

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF middleware for FastAPI"""

    def __init__(self, app, secret: str):
        super().__init__(app)
        self.csrf = CSRFProtection(secret)
        self.safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods
        if request.method in self.safe_methods:
            return await call_next(request)

        # Skip for API endpoints with Bearer token auth
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # Get session ID (from cookie or header)
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session required for this operation"
            )

        # Get CSRF token from header
        csrf_token = request.headers.get(self.csrf.header_name)
        if not csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required"
            )

        # Verify token
        if not self.csrf.verify_token(csrf_token, session_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )

        return await call_next(request)
```

## 6. Security Monitoring & Audit

### 6.1 Comprehensive Audit Logging

```python
# backend/app/core/security/audit.py
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
import json

class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    PASSWORD_CHANGE = "auth.password.change"

    # Authorization events
    PERMISSION_DENIED = "authz.permission.denied"
    ROLE_CHANGE = "authz.role.change"

    # Data events
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Security events
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    CSRF_VIOLATION = "security.csrf"

    # Device events
    DEVICE_REGISTERED = "device.registered"
    DEVICE_ACTIVATED = "device.activated"
    DEVICE_DEACTIVATED = "device.deactivated"

class AuditLogger:
    """Comprehensive audit logging system"""

    def __init__(self, db_session: Session, redis_client):
        self.db = db_session
        self.redis = redis_client

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ):
        """Log an audit event"""

        audit_entry = AuditLog(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=json.dumps(metadata or {}),
            severity=severity
        )

        self.db.add(audit_entry)
        self.db.commit()

        # Also send to real-time monitoring
        self._send_to_monitoring(audit_entry)

        # Check for suspicious patterns
        self._check_suspicious_patterns(audit_entry)

    def _send_to_monitoring(self, audit_entry: AuditLog):
        """Send audit event to real-time monitoring system"""
        event_data = {
            "timestamp": audit_entry.timestamp.isoformat(),
            "event_type": audit_entry.event_type,
            "user_id": audit_entry.user_id,
            "organization_id": audit_entry.organization_id,
            "severity": audit_entry.severity
        }

        # Publish to Redis for real-time monitoring
        self.redis.publish("audit_events", json.dumps(event_data))

        # Store in time-series for analytics
        key = f"audit_ts:{audit_entry.event_type}:{datetime.utcnow().strftime('%Y%m%d')}"
        self.redis.hincrby(key, audit_entry.timestamp.hour, 1)
        self.redis.expire(key, 86400 * 30)  # Keep for 30 days

    def _check_suspicious_patterns(self, audit_entry: AuditLog):
        """Detect suspicious activity patterns"""

        # Check for multiple failed logins
        if audit_entry.event_type == AuditEventType.LOGIN_FAILED:
            key = f"failed_logins:{audit_entry.ip_address}"
            count = self.redis.incr(key)
            self.redis.expire(key, 3600)  # Reset after 1 hour

            if count >= 10:
                self.log_event(
                    AuditEventType.SUSPICIOUS_ACTIVITY,
                    metadata={
                        "reason": "Multiple failed login attempts",
                        "ip_address": audit_entry.ip_address,
                        "count": count
                    },
                    severity="warning"
                )

        # Check for rapid API calls (potential DoS)
        if audit_entry.user_id:
            key = f"api_calls:{audit_entry.user_id}"
            count = self.redis.incr(key)
            self.redis.expire(key, 60)  # Reset after 1 minute

            if count >= 100:
                self.log_event(
                    AuditEventType.SUSPICIOUS_ACTIVITY,
                    user_id=audit_entry.user_id,
                    metadata={
                        "reason": "Excessive API calls",
                        "count": count
                    },
                    severity="warning"
                )

# Audit middleware
class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to audit all API requests"""

    async def dispatch(self, request: Request, call_next):
        # Extract request details
        user_id = getattr(request.state, "user_id", None)
        organization_id = getattr(request.state, "organization_id", None)

        # Log request
        audit_logger.log_event(
            AuditEventType.DATA_READ if request.method == "GET" else AuditEventType.DATA_UPDATE,
            user_id=user_id,
            organization_id=organization_id,
            resource_type="api",
            metadata={
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.query_params)
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent")
        )

        response = await call_next(request)

        return response
```

## 7. Security Testing Strategy

### 7.1 Automated Security Testing

```python
# tests/security/test_authentication.py
import pytest
from fastapi.testclient import TestClient
import time

class TestAuthenticationSecurity:
    """Test authentication security measures"""

    def test_jwt_algorithm_not_none(self, client: TestClient):
        """Test that 'none' algorithm is rejected"""
        # Create token with 'none' algorithm
        token = jwt.encode(
            {"user_id": 1, "exp": time.time() + 3600},
            "",
            algorithm="none"
        )

        response = client.get(
            "/api/devices",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401

    def test_jwt_signature_validation(self, client: TestClient):
        """Test that modified JWT signature is rejected"""
        # Create valid token
        valid_token = create_access_token({"user_id": 1})

        # Modify signature
        parts = valid_token.split(".")
        parts[2] = parts[2][:-4] + "hack"
        invalid_token = ".".join(parts)

        response = client.get(
            "/api/devices",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )

        assert response.status_code == 401

    def test_password_complexity_requirements(self, client: TestClient):
        """Test password complexity validation"""
        weak_passwords = [
            "password",
            "12345678",
            "admin123",
            "Password",  # No special char
            "Pass@123",  # Too short
        ]

        for password in weak_passwords:
            response = client.post("/api/auth/register", json={
                "username": "testuser",
                "password": password,
                "email": "test@example.com"
            })

            assert response.status_code == 400
            assert "password" in response.json()["detail"].lower()

    def test_rate_limiting(self, client: TestClient):
        """Test login rate limiting"""
        # Attempt multiple failed logins
        for i in range(10):
            response = client.post("/api/auth/login", json={
                "username": "testuser",
                "password": "wrongpassword"
            })

        # Next attempt should be rate limited
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })

        assert response.status_code == 429
        assert "too many" in response.json()["detail"].lower()

class TestMultiTenantSecurity:
    """Test multi-tenant isolation"""

    def test_cross_tenant_data_access_denied(self, client: TestClient, db):
        """Test that users cannot access other organization's data"""
        # Create two organizations with users
        org1 = create_organization("Org1")
        org2 = create_organization("Org2")

        user1 = create_user("user1", org1.id)
        user2 = create_user("user2", org2.id)

        # Create device for org1
        device = create_device("Device1", org1.id)

        # Try to access org1's device as org2 user
        token = create_access_token({"user_id": user2.id})

        response = client.get(
            f"/api/devices/{device.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    def test_sql_injection_prevention(self, client: TestClient):
        """Test SQL injection prevention"""
        injection_attempts = [
            "'; DROP TABLE devices; --",
            "1' OR '1'='1",
            "1; UPDATE users SET role='admin'",
            "1 UNION SELECT * FROM users"
        ]

        for payload in injection_attempts:
            response = client.get(
                f"/api/devices?name={payload}",
                headers=get_auth_headers()
            )

            # Should return normal response, not SQL error
            assert response.status_code in [200, 400]
            # Check no SQL error messages leaked
            assert "sql" not in response.text.lower()
            assert "syntax" not in response.text.lower()

class TestDeviceSecurity:
    """Test device authentication and security"""

    def test_device_activation_code_entropy(self):
        """Test activation code has sufficient entropy"""
        codes = set()

        # Generate 1000 codes
        for _ in range(1000):
            code = generate_activation_code()
            codes.add(code)

        # All should be unique
        assert len(codes) == 1000

        # Check entropy (at least 6 digits = 10^6 possibilities)
        assert all(len(code) == 6 for code in codes)
        assert all(c.isdigit() for code in codes for c in code)

    def test_device_token_replay_prevention(self, client: TestClient):
        """Test that old device tokens cannot be replayed"""
        device = create_and_activate_device()

        # Get current token
        old_token = device.auth_token

        # Rotate token
        new_token = rotate_device_token(device)

        # Try to use old token
        response = client.post(
            f"/api/devices/{device.id}/heartbeat",
            headers={"Authorization": f"Bearer {old_token}"},
            json={"timestamp": datetime.utcnow().isoformat()}
        )

        assert response.status_code == 401
```

### 7.2 Security Testing Checklist

```markdown
## Security Testing Checklist

### Authentication & Authorization
- [ ] JWT tokens use strong algorithms (RS256/HS256 with 256-bit key)
- [ ] JWT secret key is at least 32 characters with high entropy
- [ ] Tokens expire appropriately (15 min access, 7 day refresh)
- [ ] Refresh token rotation is implemented
- [ ] Password complexity requirements enforced (12+ chars, mixed case, numbers, special)
- [ ] Passwords hashed with Argon2 or bcrypt (cost factor 12+)
- [ ] Login rate limiting prevents brute force (5 attempts/minute)
- [ ] Account lockout after repeated failures
- [ ] 2FA/MFA support for sensitive operations
- [ ] Session invalidation on logout
- [ ] Concurrent session limiting

### Multi-Tenant Security
- [ ] Row-level security enforced on all queries
- [ ] Cross-tenant data access blocked
- [ ] Organization context validated on every request
- [ ] Superuser access logged and monitored
- [ ] Tenant resource limits enforced

### Input Validation & Sanitization
- [ ] All inputs validated with Pydantic schemas
- [ ] SQL injection prevention via parameterized queries
- [ ] XSS prevention via output encoding
- [ ] Path traversal prevention in file operations
- [ ] Command injection prevention
- [ ] XML/XXE attack prevention
- [ ] File upload validation (type, size, content)

### API Security
- [ ] CORS properly configured with specific origins
- [ ] CSRF protection on state-changing operations
- [ ] Rate limiting on all endpoints
- [ ] Request size limits enforced
- [ ] API versioning strategy implemented
- [ ] Proper error handling without information leakage
- [ ] Security headers (HSTS, CSP, X-Frame-Options, etc.)

### Device Security
- [ ] Activation codes have sufficient entropy
- [ ] Codes expire after reasonable time (10 minutes)
- [ ] Device binding to IP/fingerprint
- [ ] Device token rotation capability
- [ ] Heartbeat authentication required
- [ ] Replay attack prevention

### Data Security
- [ ] Sensitive data encrypted at rest
- [ ] Encryption keys properly managed
- [ ] PII data minimized and protected
- [ ] Secure data deletion/sanitization
- [ ] Backup encryption
- [ ] Data retention policies enforced

### Network Security
- [ ] TLS 1.2+ enforced
- [ ] Certificate validation
- [ ] Perfect forward secrecy
- [ ] Secure cookie flags (HttpOnly, Secure, SameSite)
- [ ] DNS security (DNSSEC)

### Monitoring & Audit
- [ ] All authentication events logged
- [ ] Failed access attempts logged
- [ ] Data access/modification logged
- [ ] Security events monitored in real-time
- [ ] Anomaly detection implemented
- [ ] Log retention per compliance requirements
- [ ] Log integrity protection

### Compliance & Governance
- [ ] GDPR compliance (if applicable)
- [ ] PCI DSS compliance (if processing payments)
- [ ] HIPAA compliance (if healthcare data)
- [ ] Data residency requirements met
- [ ] Privacy policy implemented
- [ ] Terms of service updated
- [ ] Security incident response plan
```

## 8. Implementation Roadmap

### Phase 1: Critical Security Fixes (Week 1)
1. **Implement rate limiting** on authentication endpoints
2. **Strengthen JWT configuration** (use RS256, strong secrets)
3. **Add password complexity requirements**
4. **Implement CSRF protection**
5. **Add security headers middleware**

### Phase 2: Multi-Tenant Security (Week 2)
1. **Create organization model** and migrations
2. **Implement row-level security**
3. **Add tenant context to all queries**
4. **Update user model** with organization relationship
5. **Test cross-tenant isolation**

### Phase 3: Enhanced Authentication (Week 3)
1. **Upgrade to Argon2** password hashing
2. **Implement token rotation**
3. **Add account lockout mechanism**
4. **Implement session management**
5. **Add 2FA support** (TOTP)

### Phase 4: Device Security (Week 4)
1. **Enhance activation code generation**
2. **Implement device token authentication**
3. **Add device fingerprinting**
4. **Secure heartbeat mechanism**
5. **Implement device revocation**

### Phase 5: Monitoring & Compliance (Week 5)
1. **Implement comprehensive audit logging**
2. **Add real-time security monitoring**
3. **Create security dashboard**
4. **Document security procedures**
5. **Conduct penetration testing**

## 9. Security Best Practices

### Development Practices
1. **Security-first mindset** - Consider security implications in every feature
2. **Principle of least privilege** - Grant minimum required permissions
3. **Defense in depth** - Multiple security layers
4. **Fail securely** - Errors should not compromise security
5. **Security by design** - Build security in, don't bolt it on

### Operational Practices
1. **Regular security updates** - Keep dependencies updated
2. **Security scanning** - Automated vulnerability scanning
3. **Penetration testing** - Annual professional testing
4. **Security training** - Regular team training
5. **Incident response plan** - Documented and tested

### Code Review Checklist
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] Output encoding for user-generated content
- [ ] Proper error handling without info leakage
- [ ] Authentication/authorization checks
- [ ] Rate limiting where appropriate
- [ ] Audit logging for sensitive operations
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] Dependencies up to date

## Conclusion

This security architecture provides comprehensive protection for your multi-tenant digital signage system. Implementation should be prioritized based on risk assessment, with critical vulnerabilities addressed first. Regular security audits and updates are essential to maintain security posture as the system evolves.

Remember: **Security is not a one-time implementation but an ongoing process** that requires continuous monitoring, updating, and improvement.