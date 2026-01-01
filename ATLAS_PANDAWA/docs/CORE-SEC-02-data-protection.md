# Data Protection & Privacy

> **Date**: 2025-12-23
> **Status**: Draft
> **Compliance**: GDPR-ready, SOC 2 Type II, Privacy-first

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA PROTECTION ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  SENSITIVE DATA LAYERS                                          │   │
│  │                                                                 │   │
│  │  PII (Personally Identifiable Information):                     │   │
│  │  - National ID (KTP)                                            │   │
│  │  - Passport numbers                                             │   │
│  │  - Credit card numbers                                          │   │
│  │  - Health records                                               │   │
│  │  - Biometric data                                               │   │
│  │                                                                 │   │
│  │  Financial Data:                                                │   │
│  │  - Bank account numbers                                         │   │
│  │  - Payment information                                          │   │
│  │  - Transaction details                                          │   │
│  │                                                                 │   │
│  │  Regular Data:                                                  │   │
│  │  - Names, emails (encrypted in transit)                         │   │
│  │  - Phone numbers                                                │   │
│  │  - Addresses                                                    │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PROTECTION MECHANISMS                                          │   │
│  │                                                                 │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │   │
│  │  │ Field-Level      │  │ Access Control   │  │ Audit Logging │ │   │
│  │  │ Encryption       │  │ & Masking        │  │ (Append-only) │ │   │
│  │  │ (AES-256)        │  │ (Role-based)     │  │               │ │   │
│  │  └──────────────────┘  └──────────────────┘  └───────────────┘ │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Core Principles

### 1.1 Data Classification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA CLASSIFICATION LEVELS                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LEVEL 1: CRITICAL (Highest Protection)                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Data Type              │ Examples            │ Protection       │   │
│  ├────────────────────────┼─────────────────────┼──────────────────┤   │
│  │ National ID            │ KTP, Passport       │ Field encryption │   │
│  │ Financial              │ Bank account, CC    │ Field encryption │   │
│  │ Health Records         │ Medical history     │ Field encryption │   │
│  │ Biometric              │ Fingerprint, face   │ Field encryption │   │
│  │ Authentication         │ Passwords, tokens   │ Hashing/encrypt  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LEVEL 2: SENSITIVE (High Protection)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Data Type              │ Examples            │ Protection       │   │
│  ├────────────────────────┼─────────────────────┼──────────────────┤   │
│  │ Personal Info          │ Email, phone, DOB   │ TLS in transit   │   │
│  │ Location Data          │ GPS, addresses      │ TLS in transit   │   │
│  │ Transaction History    │ Bookings, orders    │ Access control   │   │
│  │ Communication          │ Messages, calls     │ TLS + retention  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LEVEL 3: INTERNAL (Standard Protection)                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Data Type              │ Examples            │ Protection       │   │
│  ├────────────────────────┼─────────────────────┼──────────────────┤   │
│  │ Business Data          │ Revenue, occupancy  │ Access control   │   │
│  │ Operational            │ Room status, tasks  │ Access control   │   │
│  │ System Logs            │ Application logs    │ Retention policy │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LEVEL 4: PUBLIC (Minimal Protection)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Data Type              │ Examples            │ Protection       │   │
│  ├────────────────────────┼─────────────────────┼──────────────────┤   │
│  │ Public Info            │ Hotel name, address │ None required    │   │
│  │ Marketing              │ Promotions, blogs   │ None required    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Protection Requirements

**CRITICAL Data (Level 1) - MANDATORY:**
- ❌ NEVER store plaintext
- ✅ MUST use field-level encryption (AES-256)
- ✅ MUST require explicit authorization to view
- ✅ MUST log all access (append-only audit log)
- ✅ MUST support data masking for unauthorized roles
- ✅ MUST have retention & deletion policy

**SENSITIVE Data (Level 2) - REQUIRED:**
- ✅ Encryption in transit (TLS 1.3)
- ✅ Access control based on role
- ✅ Retention policy defined
- ✅ Optional encryption at rest

**INTERNAL/PUBLIC Data (Level 3-4) - STANDARD:**
- ✅ Standard access control
- ✅ Backup & recovery procedures

---

## Part 2: Field-Level Encryption

### 2.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   FIELD-LEVEL ENCRYPTION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

WRITE (Encrypt):
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│ Plaintext    │───►│ Get Key      │───►│ Encrypt      │───►│ Store DB │
│ KTP: 3201... │    │ from Env/    │    │ AES-256-GCM  │    │ Encrypted│
│              │    │ Vault        │    │              │    │          │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────┘

READ (Decrypt):
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│ Fetch from   │───►│ Check        │───►│ Decrypt in   │───►│ Return   │
│ DB (encrypted│    │ Permission   │    │ Memory       │    │ or Mask  │
│              │    │              │    │              │    │          │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ No Permission│
                    │ Return Masked│
                    │ 3201****4567 │
                    └──────────────┘
```

### 2.2 Database Schema

```sql
-- Example: guests table with encrypted PII
CREATE TABLE guests (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id VARCHAR(100) NOT NULL,

    -- Basic info (not encrypted)
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),

    -- Encrypted PII fields
    ktp_number_encrypted TEXT,  -- National ID (encrypted)
    ktp_name_encrypted TEXT,    -- Name on ID (encrypted)
    passport_number_encrypted TEXT,  -- Passport (encrypted)

    -- Encryption metadata
    encryption_key_id VARCHAR(50) NOT NULL,  -- Which key version was used
    encryption_algorithm VARCHAR(50) DEFAULT 'AES-256-GCM',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    INDEX idx_guests_tenant (tenant_id),
    INDEX idx_guests_email (email),
    INDEX idx_guests_phone (phone)
    -- NOTE: No index on encrypted fields (cannot search encrypted data directly)
);

-- Encryption keys registry
CREATE TABLE encryption_keys (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    key_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "pii-key-v1"

    -- Key is NOT stored here, only metadata
    algorithm VARCHAR(50) NOT NULL,
    purpose VARCHAR(100) NOT NULL,  -- e.g., "pii_encryption", "financial_data"

    -- Key rotation
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rotated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_encryption_keys_active (is_active) WHERE is_active = TRUE
);

-- Audit log for PII access (APPEND-ONLY)
CREATE TABLE pii_access_audit (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id VARCHAR(100) NOT NULL,

    -- Who accessed
    user_id INTEGER NOT NULL REFERENCES users(id),
    user_email VARCHAR(255) NOT NULL,
    user_role VARCHAR(100) NOT NULL,

    -- What was accessed
    resource_type VARCHAR(100) NOT NULL,  -- e.g., "guest", "payment"
    resource_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,  -- e.g., "ktp_number"

    -- How
    action VARCHAR(50) NOT NULL,  -- "view", "decrypt", "download", "export"
    access_granted BOOLEAN NOT NULL,
    reason TEXT,  -- Why access was needed (optional)

    -- Context
    ip_address INET,
    user_agent TEXT,
    correlation_id VARCHAR(100),

    -- When
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Indexes
    INDEX idx_pii_audit_tenant (tenant_id),
    INDEX idx_pii_audit_user (user_id),
    INDEX idx_pii_audit_resource (resource_type, resource_id),
    INDEX idx_pii_audit_accessed_at (accessed_at)
);

-- Prevent updates/deletes on audit log
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log is append-only. Modifications are not allowed.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_pii_audit_update
    BEFORE UPDATE OR DELETE ON pii_access_audit
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
```

### 2.3 Encryption Service

```python
# shared/security/encryption.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os
import base64
from typing import Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EncryptedValue:
    """Encrypted value with metadata"""
    ciphertext: str  # Base64 encoded
    key_id: str
    algorithm: str = "AES-256-GCM"
    nonce: str = None  # Base64 encoded nonce/IV


class EncryptionService:
    """Service for field-level encryption of sensitive data"""

    def __init__(self, encryption_key: bytes, key_id: str = "pii-key-v1"):
        """
        Initialize encryption service

        Args:
            encryption_key: 32-byte encryption key (for AES-256)
            key_id: Identifier for key version (for rotation)
        """
        if len(encryption_key) != 32:
            raise ValueError("Encryption key must be 32 bytes for AES-256")

        self.key = encryption_key
        self.key_id = key_id
        self.aesgcm = AESGCM(encryption_key)

    @classmethod
    def from_secret_manager(cls, secrets_manager, key_id: str = "pii-key-v1"):
        """Create encryption service from secrets manager"""
        key_b64 = secrets_manager.get(f"encryption_keys/{key_id}")
        if not key_b64:
            raise ValueError(f"Encryption key not found: {key_id}")

        encryption_key = base64.b64decode(key_b64)
        return cls(encryption_key, key_id)

    @classmethod
    def from_env(cls, env_var: str = "ENCRYPTION_KEY", key_id: str = "pii-key-v1"):
        """Create encryption service from environment variable"""
        key_b64 = os.getenv(env_var)
        if not key_b64:
            raise ValueError(f"Encryption key not found in env: {env_var}")

        encryption_key = base64.b64decode(key_b64)
        return cls(encryption_key, key_id)

    def encrypt(self, plaintext: str) -> EncryptedValue:
        """
        Encrypt plaintext value

        Args:
            plaintext: The value to encrypt

        Returns:
            EncryptedValue with ciphertext and metadata
        """
        if not plaintext:
            return None

        # Generate random nonce (12 bytes for GCM)
        nonce = os.urandom(12)

        # Encrypt
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext_bytes = self.aesgcm.encrypt(nonce, plaintext_bytes, None)

        # Encode to base64 for storage
        ciphertext_b64 = base64.b64encode(ciphertext_bytes).decode('ascii')
        nonce_b64 = base64.b64encode(nonce).decode('ascii')

        return EncryptedValue(
            ciphertext=ciphertext_b64,
            key_id=self.key_id,
            algorithm="AES-256-GCM",
            nonce=nonce_b64
        )

    def decrypt(self, encrypted_value: EncryptedValue) -> str:
        """
        Decrypt encrypted value

        Args:
            encrypted_value: EncryptedValue to decrypt

        Returns:
            Decrypted plaintext
        """
        if not encrypted_value or not encrypted_value.ciphertext:
            return None

        # Check key version
        if encrypted_value.key_id != self.key_id:
            logger.warning(
                f"Decrypting with different key version: "
                f"data={encrypted_value.key_id}, current={self.key_id}"
            )
            # In production, fetch the correct key version
            # For now, proceed with current key (may fail)

        # Decode from base64
        ciphertext_bytes = base64.b64decode(encrypted_value.ciphertext)
        nonce_bytes = base64.b64decode(encrypted_value.nonce)

        # Decrypt
        try:
            plaintext_bytes = self.aesgcm.decrypt(nonce_bytes, ciphertext_bytes, None)
            return plaintext_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data. Key mismatch or corrupted data.")

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Encrypt specific fields in a dictionary

        Args:
            data: Dictionary containing fields to encrypt
            fields: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields (field_name_encrypted)
        """
        result = data.copy()

        for field in fields:
            if field in data and data[field]:
                encrypted = self.encrypt(data[field])

                # Store encrypted value
                result[f"{field}_encrypted"] = encrypted.ciphertext
                result[f"{field}_nonce"] = encrypted.nonce

                # Remove plaintext
                del result[field]

        # Add encryption metadata
        result["encryption_key_id"] = self.key_id
        result["encryption_algorithm"] = "AES-256-GCM"

        return result

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Decrypt specific fields in a dictionary

        Args:
            data: Dictionary containing encrypted fields
            fields: List of original field names (without _encrypted suffix)

        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()

        for field in fields:
            encrypted_field = f"{field}_encrypted"
            nonce_field = f"{field}_nonce"

            if encrypted_field in data and data[encrypted_field]:
                encrypted_value = EncryptedValue(
                    ciphertext=data[encrypted_field],
                    nonce=data[nonce_field],
                    key_id=data.get("encryption_key_id", self.key_id),
                    algorithm=data.get("encryption_algorithm", "AES-256-GCM")
                )

                # Decrypt
                result[field] = self.decrypt(encrypted_value)

        return result

    @staticmethod
    def mask_value(value: str, visible_start: int = 4, visible_end: int = 4) -> str:
        """
        Mask sensitive value for display

        Args:
            value: Value to mask
            visible_start: Number of characters visible at start
            visible_end: Number of characters visible at end

        Returns:
            Masked value (e.g., "3201****4567")
        """
        if not value:
            return None

        if len(value) <= visible_start + visible_end:
            return "*" * len(value)

        mask_length = len(value) - visible_start - visible_end
        return value[:visible_start] + ("*" * mask_length) + value[-visible_end:]


# Key generation utility
def generate_encryption_key() -> str:
    """Generate a new 256-bit encryption key (Base64 encoded)"""
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode('ascii')


# Usage example
if __name__ == "__main__":
    # Generate new key
    key_b64 = generate_encryption_key()
    print(f"New encryption key (store in secrets manager):\n{key_b64}\n")

    # Example encryption
    service = EncryptionService(base64.b64decode(key_b64))

    # Encrypt KTP number
    ktp_plain = "3201234567891234"
    encrypted = service.encrypt(ktp_plain)
    print(f"Plaintext: {ktp_plain}")
    print(f"Encrypted: {encrypted.ciphertext}")
    print(f"Nonce: {encrypted.nonce}")

    # Decrypt
    decrypted = service.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")

    # Mask
    masked = service.mask_value(ktp_plain)
    print(f"Masked: {masked}")
```

### 2.4 Repository Integration

```python
# services/guests/repository.py
from typing import Optional, List
from sqlalchemy import select
from shared.database import Base
from shared.security.encryption import EncryptionService
from .models import Guest
import logging

logger = logging.getLogger(__name__)


class GuestRepository:
    """Repository for guest data with automatic encryption/decryption"""

    def __init__(self, db, encryption_service: EncryptionService):
        self.db = db
        self.encryption = encryption_service

        # Fields that should be encrypted
        self.encrypted_fields = ['ktp_number', 'ktp_name', 'passport_number']

    async def create(self, guest_data: dict) -> Guest:
        """Create guest with automatic encryption of PII fields"""

        # Encrypt sensitive fields
        encrypted_data = self.encryption.encrypt_dict(
            guest_data,
            self.encrypted_fields
        )

        # Create model
        guest = Guest(**encrypted_data)
        self.db.add(guest)
        await self.db.commit()
        await self.db.refresh(guest)

        logger.info(f"Created guest with encrypted PII: {guest.id}")
        return guest

    async def get_by_id(
        self,
        guest_id: int,
        decrypt: bool = False,
        user_id: Optional[int] = None,
        audit_reason: Optional[str] = None
    ) -> Optional[Guest]:
        """
        Get guest by ID with optional decryption

        Args:
            guest_id: Guest ID
            decrypt: Whether to decrypt PII fields
            user_id: User requesting access (for audit)
            audit_reason: Reason for access (for audit)
        """
        result = await self.db.execute(
            select(Guest).where(Guest.id == guest_id)
        )
        guest = result.scalar_one_or_none()

        if not guest:
            return None

        # If decryption requested, decrypt and audit
        if decrypt:
            # Audit log (should check permission first in actual implementation)
            await self._audit_pii_access(
                user_id=user_id,
                resource_type="guest",
                resource_id=guest.id,
                fields=self.encrypted_fields,
                action="decrypt",
                granted=True,  # Would be based on actual permission check
                reason=audit_reason
            )

            # Decrypt
            guest_dict = guest.__dict__
            decrypted_dict = self.encryption.decrypt_dict(
                guest_dict,
                self.encrypted_fields
            )

            # Update guest object with decrypted values
            for field in self.encrypted_fields:
                if field in decrypted_dict:
                    setattr(guest, field, decrypted_dict[field])

        return guest

    async def get_by_id_masked(
        self,
        guest_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Guest]:
        """Get guest with PII fields masked (for unauthorized users)"""

        guest = await self.get_by_id(guest_id, decrypt=True, user_id=user_id)

        if not guest:
            return None

        # Mask PII fields
        for field in self.encrypted_fields:
            value = getattr(guest, field, None)
            if value:
                masked = self.encryption.mask_value(value)
                setattr(guest, field, masked)

        # Audit masked access
        await self._audit_pii_access(
            user_id=user_id,
            resource_type="guest",
            resource_id=guest.id,
            fields=self.encrypted_fields,
            action="view_masked",
            granted=True
        )

        return guest

    async def update(
        self,
        guest_id: int,
        updates: dict,
        user_id: Optional[int] = None
    ) -> Guest:
        """Update guest with automatic encryption"""

        guest = await self.get_by_id(guest_id)
        if not guest:
            raise ValueError(f"Guest not found: {guest_id}")

        # Encrypt any PII fields in updates
        encrypted_updates = self.encryption.encrypt_dict(
            updates,
            [f for f in self.encrypted_fields if f in updates]
        )

        # Apply updates
        for key, value in encrypted_updates.items():
            setattr(guest, key, value)

        await self.db.commit()
        await self.db.refresh(guest)

        logger.info(f"Updated guest {guest.id} with encrypted PII")
        return guest

    async def _audit_pii_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        fields: List[str],
        action: str,
        granted: bool,
        reason: Optional[str] = None
    ):
        """Create audit log entry for PII access"""
        from .models import PIIAccessAudit
        from shared.observability.context import get_correlation_id

        # Get user details
        from services.auth.models import User
        user = await self.db.get(User, user_id)

        for field in fields:
            audit = PIIAccessAudit(
                tenant_id=user.tenant_id if hasattr(user, 'tenant_id') else None,
                user_id=user_id,
                user_email=user.email if user else "unknown",
                user_role=user.role if user else "unknown",
                resource_type=resource_type,
                resource_id=resource_id,
                field_name=field,
                action=action,
                access_granted=granted,
                reason=reason,
                correlation_id=get_correlation_id()
            )

            self.db.add(audit)

        await self.db.commit()
```

---

## Part 3: File Storage Security

### 3.1 KTP File Storage (Cloudflare R2)

```python
# shared/storage/secure_storage.py
import boto3
from botocore.client import Config
from datetime import datetime, timedelta
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class SecureFileStorage:
    """Secure file storage for sensitive documents (KTP, passports, etc.)"""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "auto"
    ):
        self.bucket = bucket
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version='s3v4')
        )

    @classmethod
    def from_config(cls, config):
        """Create from application config"""
        return cls(
            endpoint_url=config.storage.endpoint_url,
            access_key=config.storage.access_key.get_secret_value(),
            secret_key=config.storage.secret_key.get_secret_value(),
            bucket=config.storage.bucket
        )

    def upload_ktp(
        self,
        file_content: bytes,
        guest_id: int,
        tenant_id: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload KTP file to private storage

        Args:
            file_content: File bytes
            guest_id: Guest ID
            tenant_id: Tenant ID
            content_type: MIME type

        Returns:
            Object key (path) in storage
        """
        # Generate secure path: tenants/{tenant_id}/ktp/{guest_id}/{timestamp}.jpg
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = self._get_extension(content_type)
        object_key = f"tenants/{tenant_id}/ktp/{guest_id}/{timestamp}{extension}"

        # Upload with metadata
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=file_content,
            ContentType=content_type,
            Metadata={
                "tenant_id": tenant_id,
                "guest_id": str(guest_id),
                "uploaded_at": datetime.utcnow().isoformat(),
                "classification": "pii"
            },
            # CRITICAL: Private ACL
            ACL='private'
        )

        logger.info(f"Uploaded KTP for guest {guest_id} to {object_key}")
        return object_key

    def generate_signed_url(
        self,
        object_key: str,
        expires_in: int = 300,  # 5 minutes
        user_id: Optional[int] = None
    ) -> str:
        """
        Generate temporary signed URL for accessing KTP file

        Args:
            object_key: Object key in storage
            expires_in: Expiration time in seconds (default: 5 minutes)
            user_id: User requesting access (for audit)

        Returns:
            Signed URL
        """
        # Audit access
        logger.info(
            f"Generated signed URL for {object_key}",
            extra={
                "user_id": user_id,
                "expires_in": expires_in,
                "object_key": object_key
            }
        )

        # Generate presigned URL
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': object_key
            },
            ExpiresIn=expires_in
        )

        return url

    def delete_ktp(self, object_key: str) -> bool:
        """Delete KTP file (for GDPR compliance / data deletion requests)"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=object_key
            )
            logger.info(f"Deleted KTP file: {object_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete KTP file {object_key}: {e}")
            return False

    def list_ktp_files(self, guest_id: int, tenant_id: str) -> list[dict]:
        """List all KTP files for a guest"""
        prefix = f"tenants/{tenant_id}/ktp/{guest_id}/"

        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix
        )

        files = []
        for obj in response.get('Contents', []):
            files.append({
                "key": obj['Key'],
                "size": obj['Size'],
                "last_modified": obj['LastModified'],
                "etag": obj['ETag']
            })

        return files

    @staticmethod
    def _get_extension(content_type: str) -> str:
        """Get file extension from content type"""
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "application/pdf": ".pdf"
        }
        return mapping.get(content_type, ".bin")
```

### 3.2 File Upload API

```python
# services/guests/routes.py (excerpt)
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from shared.auth.dependencies import get_current_user, require_permission
from shared.storage.secure_storage import SecureFileStorage
from .service import GuestService

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.post("/{guest_id}/ktp/upload")
async def upload_ktp(
    guest_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("guests.ktp.upload")),
    guest_service: GuestService = Depends(),
    storage: SecureFileStorage = Depends()
):
    """Upload KTP file for guest"""

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Invalid file type. Allowed: {allowed_types}")

    # Validate file size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File size exceeds 10MB limit")

    # Get guest to verify tenant
    guest = await guest_service.get_by_id(guest_id)
    if not guest:
        raise HTTPException(404, "Guest not found")

    # Upload to secure storage
    object_key = storage.upload_ktp(
        file_content=content,
        guest_id=guest_id,
        tenant_id=guest.tenant_id,
        content_type=file.content_type
    )

    # Update guest record with file reference
    await guest_service.update(guest_id, {
        "ktp_file_key": object_key
    })

    return {
        "success": True,
        "object_key": object_key,
        "message": "KTP file uploaded successfully"
    }


@router.get("/{guest_id}/ktp/view")
async def view_ktp(
    guest_id: int,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("guests.ktp.view")),
    guest_service: GuestService = Depends(),
    storage: SecureFileStorage = Depends()
):
    """Get signed URL to view KTP file"""

    guest = await guest_service.get_by_id(guest_id)
    if not guest or not guest.ktp_file_key:
        raise HTTPException(404, "KTP file not found")

    # Generate signed URL (expires in 5 minutes)
    signed_url = storage.generate_signed_url(
        object_key=guest.ktp_file_key,
        expires_in=300,
        user_id=current_user.id
    )

    return {
        "url": signed_url,
        "expires_in": 300,
        "warning": "This URL expires in 5 minutes. Do not share."
    }
```

---

## Part 4: Access Control & Data Masking

### 4.1 Permission-Based Access

```python
# shared/auth/permissions.py
from enum import Enum
from typing import Optional

class PIIPermission(str, Enum):
    """Permissions for PII data access"""

    # KTP/ID Documents
    KTP_VIEW_FULL = "pii.ktp.view_full"  # View unmasked KTP number
    KTP_VIEW_MASKED = "pii.ktp.view_masked"  # View masked KTP
    KTP_UPLOAD = "pii.ktp.upload"  # Upload KTP files
    KTP_DELETE = "pii.ktp.delete"  # Delete KTP data

    # Financial Data
    PAYMENT_VIEW_FULL = "pii.payment.view_full"
    PAYMENT_VIEW_MASKED = "pii.payment.view_masked"

    # Audit Access
    AUDIT_VIEW = "pii.audit.view"  # View PII access logs

    # Data Export
    EXPORT_PII = "pii.export"  # Export PII data (GDPR requests)


# Role-based permission mapping
ROLE_PII_PERMISSIONS = {
    "owner": [
        PIIPermission.KTP_VIEW_FULL,
        PIIPermission.KTP_UPLOAD,
        PIIPermission.KTP_DELETE,
        PIIPermission.PAYMENT_VIEW_FULL,
        PIIPermission.AUDIT_VIEW,
        PIIPermission.EXPORT_PII
    ],
    "manager": [
        PIIPermission.KTP_VIEW_FULL,
        PIIPermission.KTP_UPLOAD,
        PIIPermission.PAYMENT_VIEW_FULL,
        PIIPermission.AUDIT_VIEW
    ],
    "audit": [
        PIIPermission.KTP_VIEW_FULL,
        PIIPermission.PAYMENT_VIEW_FULL,
        PIIPermission.AUDIT_VIEW
    ],
    "front_desk": [
        PIIPermission.KTP_VIEW_MASKED,
        PIIPermission.KTP_UPLOAD,
        PIIPermission.PAYMENT_VIEW_MASKED
    ],
    "housekeeping": [],  # No PII access
    "viewer": [
        PIIPermission.KTP_VIEW_MASKED,
        PIIPermission.PAYMENT_VIEW_MASKED
    ]
}
```

### 4.2 Service Layer with Permission Checks

```python
# services/guests/service.py
from typing import Optional
from shared.auth.permissions import PIIPermission, ROLE_PII_PERMISSIONS
from shared.security.encryption import EncryptionService
from .repository import GuestRepository
from .models import Guest
import logging

logger = logging.getLogger(__name__)


class GuestService:
    """Guest service with PII protection"""

    def __init__(
        self,
        repository: GuestRepository,
        encryption: EncryptionService
    ):
        self.repo = repository
        self.encryption = encryption

    async def get_guest(
        self,
        guest_id: int,
        user_id: int,
        user_role: str,
        reason: Optional[str] = None
    ) -> Optional[Guest]:
        """
        Get guest with automatic PII masking based on user permissions

        Args:
            guest_id: Guest ID
            user_id: User requesting access
            user_role: User's role
            reason: Reason for access (for audit)

        Returns:
            Guest with appropriate PII visibility
        """
        # Check if user can view full PII
        can_view_full = PIIPermission.KTP_VIEW_FULL in ROLE_PII_PERMISSIONS.get(user_role, [])

        if can_view_full:
            # Decrypt and return full data
            guest = await self.repo.get_by_id(
                guest_id,
                decrypt=True,
                user_id=user_id,
                audit_reason=reason
            )
        else:
            # Return masked data
            guest = await self.repo.get_by_id_masked(
                guest_id,
                user_id=user_id
            )

        return guest

    async def export_guest_data(
        self,
        guest_id: int,
        user_id: int,
        user_role: str,
        reason: str
    ) -> dict:
        """
        Export guest data (for GDPR data portability requests)

        Requires EXPORT_PII permission
        """
        # Check permission
        if PIIPermission.EXPORT_PII not in ROLE_PII_PERMISSIONS.get(user_role, []):
            raise PermissionError("User does not have permission to export PII")

        # Get full decrypted data
        guest = await self.repo.get_by_id(
            guest_id,
            decrypt=True,
            user_id=user_id,
            audit_reason=f"GDPR Export: {reason}"
        )

        if not guest:
            return None

        # Return all data (for GDPR compliance)
        return {
            "personal_info": {
                "name": guest.name,
                "email": guest.email,
                "phone": guest.phone
            },
            "identification": {
                "ktp_number": guest.ktp_number,
                "ktp_name": guest.ktp_name,
                "passport_number": guest.passport_number
            },
            "metadata": {
                "created_at": guest.created_at.isoformat(),
                "updated_at": guest.updated_at.isoformat() if guest.updated_at else None
            }
        }

    async def delete_guest_pii(
        self,
        guest_id: int,
        user_id: int,
        user_role: str,
        reason: str
    ) -> bool:
        """
        Delete guest PII data (for GDPR right to erasure)

        Requires KTP_DELETE permission
        """
        # Check permission
        if PIIPermission.KTP_DELETE not in ROLE_PII_PERMISSIONS.get(user_role, []):
            raise PermissionError("User does not have permission to delete PII")

        # Soft delete PII fields (set to null)
        await self.repo.update(guest_id, {
            "ktp_number_encrypted": None,
            "ktp_name_encrypted": None,
            "passport_number_encrypted": None,
            "ktp_file_key": None
        }, user_id=user_id)

        logger.info(
            f"Deleted PII for guest {guest_id}",
            extra={
                "user_id": user_id,
                "reason": reason,
                "action": "gdpr_erasure"
            }
        )

        return True
```

---

## Part 5: Secret Management for Development

### 5.1 Bitwarden Workflow (Solo Dev / AI-Assisted)

For solo developers or small teams, **Bitwarden + CLI** provides a practical alternative to HashiCorp Vault:

**Why Bitwarden:**
- Online & accessible across devices
- Murah (gratis / ~$10/year for premium)
- Open-source & trusted
- CLI available (`bw`)
- Perfect for solo dev + AI-assisted development

**Setup:**

```bash
# Install Bitwarden CLI
npm install -g @bitwarden/cli

# Login
bw login

# Unlock (returns session key)
export BW_SESSION=$(bw unlock --raw)

# Create item for project secrets
bw create item \
  --name "SUHO-PROD" \
  --username "production" \
  --notes '{"DATABASE_URL":"postgresql://...","JWT_SECRET":"...","ENCRYPTION_KEY":"..."}'

# Or via JSON file
cat > secrets.json <<EOF
{
  "organizationId": null,
  "type": 2,
  "name": "SUHO-DEV",
  "notes": "",
  "fields": [
    {"name": "DATABASE_URL", "value": "postgresql://localhost/suho_dev", "type": 0},
    {"name": "REDIS_URL", "value": "redis://localhost:6379", "type": 0},
    {"name": "JWT_SECRET", "value": "dev-secret-key-change-in-prod", "type": 1},
    {"name": "ENCRYPTION_KEY", "value": "$(python -c 'import secrets; print(secrets.token_urlsafe(32))')", "type": 1}
  ]
}
EOF

bw create item --file secrets.json
```

**Daily Workflow:**

```bash
# On new device / terminal session
bw login
export BW_SESSION=$(bw unlock --raw)

# Get secrets
bw get item "SUHO-DEV" | jq -r '.fields[] | "\(.name)=\(.value)"' > .env.local

# Or set directly to environment
export $(bw get item "SUHO-DEV" | jq -r '.fields[] | "\(.name)=\(.value)"')

# Run application
python main.py
```

**Deployment to VPS/Nomad:**

```bash
# On server
bw login --apikey  # Use API key for non-interactive

# Fetch secrets and inject to Nomad
bw get item "SUHO-PROD" | jq -r '.fields[]' | while read -r field; do
  name=$(echo $field | jq -r '.name')
  value=$(echo $field | jq -r '.value')

  # Set in Nomad job template
  nomad job dispatch -meta "$name=$value" suho-backend
done
```

**Best Practices:**
1. ✅ One Bitwarden item per environment (DEV, STAGING, PROD)
2. ✅ Use `type: 1` (hidden) for sensitive fields
3. ✅ Rotate secrets regularly (update in Bitwarden, redeploy)
4. ✅ Never commit `.env` files
5. ✅ Use `.env.example` as template (no real values)

### 5.2 Production: HashiCorp Vault

For production at scale, use Vault (as defined in STD-11):

```python
# shared/config/secrets.py (excerpt from STD-11)
from shared.config.secrets import create_secrets_manager

# In production, this uses Vault
# In development, uses environment variables
secrets = create_secrets_manager()

# Get encryption key
encryption_key_b64 = await secrets.get_required("encryption_keys/pii-key-v1")
encryption_key = base64.b64decode(encryption_key_b64)

# Create encryption service
encryption_service = EncryptionService(encryption_key, key_id="pii-key-v1")
```

---

## Part 6: Compliance & Best Practices

### 6.1 GDPR Compliance

**Right to Access (Article 15):**
```python
@router.get("/guests/{guest_id}/gdpr/export")
async def export_guest_data_gdpr(
    guest_id: int,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("pii.export")),
    service: GuestService = Depends()
):
    """Export all personal data for GDPR data portability request"""

    data = await service.export_guest_data(
        guest_id=guest_id,
        user_id=current_user.id,
        user_role=current_user.role,
        reason="GDPR Article 15 - Right to Access"
    )

    return {
        "request_type": "data_export",
        "requested_at": datetime.utcnow().isoformat(),
        "data": data
    }
```

**Right to Erasure (Article 17):**
```python
@router.delete("/guests/{guest_id}/gdpr/erase")
async def erase_guest_pii_gdpr(
    guest_id: int,
    reason: str,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("pii.ktp.delete")),
    service: GuestService = Depends()
):
    """Erase personal data for GDPR right to erasure request"""

    success = await service.delete_guest_pii(
        guest_id=guest_id,
        user_id=current_user.id,
        user_role=current_user.role,
        reason=f"GDPR Article 17 - Right to Erasure: {reason}"
    )

    return {
        "request_type": "data_erasure",
        "processed_at": datetime.utcnow().isoformat(),
        "success": success
    }
```

**Data Breach Notification (Article 33):**
- Audit logs provide evidence of who accessed what and when
- In case of breach, query `pii_access_audit` table for affected users

### 6.2 Data Retention Policy

```python
# Database retention policies
DATA_RETENTION_POLICIES = {
    "pii_access_audit": {
        "retention_days": 2555,  # 7 years (legal requirement)
        "archive_after_days": 365,  # Archive after 1 year
        "deletion_allowed": False  # Never delete (legal hold)
    },
    "guests_pii": {
        "retention_days": 1825,  # 5 years after last activity
        "archive_after_days": 730,  # Archive after 2 years
        "deletion_allowed": True,  # Can be deleted on request (GDPR)
        "soft_delete": True  # Soft delete first, hard delete after 90 days
    },
    "ktp_files": {
        "retention_days": 1825,  # 5 years
        "deletion_allowed": True,
        "notify_before_deletion": True
    }
}


# Scheduled task for retention enforcement
@shared_task(name="scheduled.enforce_data_retention")
def enforce_data_retention():
    """Enforce data retention policies"""
    from services.compliance.service import ComplianceService

    with get_db_sync() as db:
        service = ComplianceService(db)

        # Archive old audit logs
        archived_audits = service.archive_old_audit_logs(
            older_than_days=DATA_RETENTION_POLICIES["pii_access_audit"]["archive_after_days"]
        )

        # Soft delete old guest PII (if no legal hold)
        deleted_guests = service.soft_delete_old_guest_pii(
            older_than_days=DATA_RETENTION_POLICIES["guests_pii"]["retention_days"]
        )

        # Hard delete soft-deleted PII after grace period
        purged_guests = service.purge_soft_deleted_pii(
            soft_deleted_before_days=90
        )

    return {
        "archived_audits": archived_audits,
        "deleted_guests": deleted_guests,
        "purged_guests": purged_guests
    }
```

### 6.3 Security Best Practices Checklist

**Field-Level Encryption:**
- [ ] Use AES-256-GCM for PII encryption
- [ ] Store encryption keys in secrets manager (Vault/Bitwarden)
- [ ] Never store keys in database or code
- [ ] Implement key rotation strategy (annual minimum)
- [ ] Use unique key_id for each key version
- [ ] Include nonce/IV for each encrypted value

**Access Control:**
- [ ] Implement role-based permissions for PII access
- [ ] Default to masked/hidden for non-authorized roles
- [ ] Require explicit reason for PII decryption
- [ ] Implement principle of least privilege

**Audit Logging:**
- [ ] Log all PII access (view, decrypt, export, delete)
- [ ] Use append-only audit tables (prevent tampering)
- [ ] Include: who, what, when, why, granted/denied
- [ ] Retain audit logs per legal requirements (7+ years)

**File Storage:**
- [ ] Use private buckets (never public)
- [ ] Generate signed URLs with short expiration (5-15 min)
- [ ] Encrypt files at rest (server-side encryption)
- [ ] Scan uploaded files for malware

**Secrets Management:**
- [ ] Never commit secrets to git
- [ ] Use `.gitignore` for `.env*` files
- [ ] Production: Use Vault or cloud secrets manager
- [ ] Development: Use Bitwarden CLI or environment variables
- [ ] Rotate secrets regularly (quarterly minimum)

**Compliance:**
- [ ] Implement GDPR right to access (data export)
- [ ] Implement GDPR right to erasure (data deletion)
- [ ] Define data retention policies
- [ ] Maintain audit trail for compliance
- [ ] Document data processing activities

**Monitoring:**
- [ ] Alert on unauthorized PII access attempts
- [ ] Monitor encryption/decryption failures
- [ ] Track unusual audit patterns (mass exports)
- [ ] Set up breach detection workflows

---

## Part 7: Testing & Validation

### 7.1 Encryption Tests

```python
# tests/security/test_encryption.py
import pytest
from shared.security.encryption import EncryptionService, generate_encryption_key
import base64


class TestEncryption:

    @pytest.fixture
    def encryption_service(self):
        key_b64 = generate_encryption_key()
        key = base64.b64decode(key_b64)
        return EncryptionService(key, key_id="test-key-v1")

    def test_encrypt_decrypt(self, encryption_service):
        """Test basic encryption and decryption"""
        plaintext = "3201234567891234"

        # Encrypt
        encrypted = encryption_service.encrypt(plaintext)
        assert encrypted.ciphertext != plaintext
        assert encrypted.key_id == "test-key-v1"
        assert encrypted.nonce is not None

        # Decrypt
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self, encryption_service):
        """Test encryption of empty string"""
        result = encryption_service.encrypt("")
        assert result is None

    def test_encrypt_dict(self, encryption_service):
        """Test encrypting dictionary fields"""
        data = {
            "name": "John Doe",
            "ktp_number": "3201234567891234",
            "email": "john@example.com"
        }

        encrypted = encryption_service.encrypt_dict(data, ["ktp_number"])

        assert "ktp_number" not in encrypted
        assert "ktp_number_encrypted" in encrypted
        assert "ktp_number_nonce" in encrypted
        assert encrypted["name"] == "John Doe"
        assert encrypted["encryption_key_id"] == "test-key-v1"

    def test_decrypt_dict(self, encryption_service):
        """Test decrypting dictionary fields"""
        data = {
            "name": "John Doe",
            "ktp_number": "3201234567891234"
        }

        encrypted = encryption_service.encrypt_dict(data, ["ktp_number"])
        decrypted = encryption_service.decrypt_dict(encrypted, ["ktp_number"])

        assert decrypted["ktp_number"] == "3201234567891234"
        assert decrypted["name"] == "John Doe"

    def test_masking(self, encryption_service):
        """Test value masking"""
        value = "3201234567891234"
        masked = encryption_service.mask_value(value)

        assert masked == "3201********1234"
        assert len(masked) == len(value)

    def test_masking_short_value(self, encryption_service):
        """Test masking of short values"""
        value = "1234"
        masked = encryption_service.mask_value(value, visible_start=2, visible_end=2)

        assert masked == "****"
```

### 7.2 Permission Tests

```python
# tests/services/test_guest_service.py
import pytest
from services.guests.service import GuestService
from shared.auth.permissions import PIIPermission, ROLE_PII_PERMISSIONS


@pytest.mark.asyncio
class TestGuestServicePermissions:

    async def test_owner_can_view_full_pii(self, guest_service, test_guest):
        """Test that owner can view unmasked PII"""
        guest = await guest_service.get_guest(
            guest_id=test_guest.id,
            user_id=1,
            user_role="owner",
            reason="Testing owner access"
        )

        # Should have full KTP number (not masked)
        assert guest.ktp_number == "3201234567891234"
        assert "*" not in guest.ktp_number

    async def test_front_desk_sees_masked_pii(self, guest_service, test_guest):
        """Test that front desk sees masked PII"""
        guest = await guest_service.get_guest(
            guest_id=test_guest.id,
            user_id=2,
            user_role="front_desk",
            reason="Check-in process"
        )

        # Should have masked KTP number
        assert "*" in guest.ktp_number
        assert guest.ktp_number.startswith("3201")
        assert guest.ktp_number.endswith("1234")

    async def test_housekeeping_no_pii_access(self, guest_service, test_guest):
        """Test that housekeeping has no PII access"""
        # This should either return masked data or raise PermissionError
        # depending on implementation
        guest = await guest_service.get_guest(
            guest_id=test_guest.id,
            user_id=3,
            user_role="housekeeping"
        )

        # Should be completely masked or null
        assert guest.ktp_number is None or "*****" in guest.ktp_number
```

---

## Summary

**One-liner:**
> **Encrypt critical data, control access by role, audit everything, comply with privacy laws.**

**Key Principles:**
1. **Field-level encryption (AES-256)** for PII data
2. **Role-based access** with masking for unauthorized users
3. **Append-only audit logs** for all PII access
4. **Private file storage** with signed URLs
5. **Secrets in vault**, never in code
6. **GDPR compliance** built-in (export, erasure)
7. **Retention policies** enforced automatically

**Protection Layers:**
```
Layer 1: Encryption at Rest (field-level AES-256)
Layer 2: Access Control (role-based permissions)
Layer 3: Audit Logging (who accessed what, when, why)
Layer 4: Encryption in Transit (TLS 1.3)
Layer 5: File Security (private storage, signed URLs)
Layer 6: Secrets Management (Vault/Bitwarden)
```

**For Solo Dev / Small Teams:**
- Use **Bitwarden + CLI** for secret management
- Use **Cloudflare R2** for file storage (free tier available)
- Implement **basic encryption** from day one
- Add **audit logging** early (append-only table)

**For Production / Enterprise:**
- Use **HashiCorp Vault** for secrets (see STD-11)
- Implement **comprehensive audit logging**
- Regular **security audits** & **penetration testing**
- **Data breach response** plan documented
- **GDPR compliance** officer assigned

---

**Related Documents:**
- SEC-01: Security & Authentication (authentication flows, JWT)
- STD-11: Secrets & Configuration Management (Vault integration)
- STD-17: Logging & Observability (structured logging for audit)
- ARCH-05: Frontend Architecture (permission guards in UI)
