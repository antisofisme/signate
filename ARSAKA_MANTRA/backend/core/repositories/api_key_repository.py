"""
API Key Repository

Provides data access abstraction for API Key management.
Supports both in-memory and PostgreSQL backends.
"""

import os
import hashlib
import secrets
import string
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..domain.api_key_schema import ApiKey


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Format: mk_<32 random alphanumeric characters>
    Example: mk_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6
    """
    chars = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(32))
    return f"mk_{random_part}"


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        key: The full API key

    Returns:
        SHA-256 hash as hex string
    """
    return hashlib.sha256(key.encode()).hexdigest()


def mask_api_key(key: str) -> str:
    """
    Create a masked display version of the key.

    Example: mk_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6
          -> mk_A1b2...O5p6
    """
    if len(key) < 12:
        return key[:4] + "..." + key[-4:]
    return key[:7] + "..." + key[-4:]


class ApiKeyRepository(ABC):
    """
    Abstract repository interface for API Key management.
    """

    @abstractmethod
    def save(self, api_key: ApiKey) -> None:
        """Save a new API key."""
        pass

    @abstractmethod
    def find_by_id(self, key_id: str) -> Optional[ApiKey]:
        """Find an API key by its ID."""
        pass

    @abstractmethod
    def find_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        """Find an API key by its hash (for validation)."""
        pass

    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[ApiKey]:
        """Find all API keys with pagination."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Count total API keys."""
        pass

    @abstractmethod
    def update(self, api_key: ApiKey) -> None:
        """Update an API key (name, description only)."""
        pass

    @abstractmethod
    def update_last_used(self, key_id: str) -> None:
        """Update the last_used_at timestamp."""
        pass

    @abstractmethod
    def revoke(self, key_id: str) -> bool:
        """
        Revoke an API key.
        Sets is_active=False and revoked_at=now.
        Returns True if key was found and revoked.
        """
        pass

    @abstractmethod
    def delete(self, key_id: str) -> bool:
        """
        Delete an API key permanently.
        Returns True if key was found and deleted.
        """
        pass


class InMemoryApiKeyRepository(ApiKeyRepository):
    """
    In-memory implementation for development/testing.
    """

    def __init__(self):
        self._keys: dict[str, ApiKey] = {}
        self._hash_index: dict[str, str] = {}  # hash -> key_id

    def save(self, api_key: ApiKey) -> None:
        if api_key.id in self._keys:
            raise ValueError(f"API key with id {api_key.id} already exists")
        if api_key.key_hash in self._hash_index:
            raise ValueError("API key with this hash already exists")

        self._keys[api_key.id] = api_key
        self._hash_index[api_key.key_hash] = api_key.id

    def find_by_id(self, key_id: str) -> Optional[ApiKey]:
        return self._keys.get(key_id)

    def find_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        key_id = self._hash_index.get(key_hash)
        if key_id:
            return self._keys.get(key_id)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[ApiKey]:
        all_keys = list(self._keys.values())
        # Sort by created_at descending
        all_keys.sort(key=lambda k: k.created_at, reverse=True)
        return all_keys[offset:offset + limit]

    def count(self) -> int:
        return len(self._keys)

    def update(self, api_key: ApiKey) -> None:
        if api_key.id not in self._keys:
            raise ValueError(f"API key with id {api_key.id} not found")
        self._keys[api_key.id] = api_key

    def update_last_used(self, key_id: str) -> None:
        if key_id in self._keys:
            key = self._keys[key_id]
            # Create updated key with new last_used_at
            updated = ApiKey(
                id=key.id,
                name=key.name,
                description=key.description,
                key_prefix=key.key_prefix,
                key_hash=key.key_hash,
                permissions=key.permissions,
                is_active=key.is_active,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=datetime.utcnow(),
                revoked_at=key.revoked_at,
                created_by=key.created_by,
            )
            self._keys[key_id] = updated

    def revoke(self, key_id: str) -> bool:
        if key_id not in self._keys:
            return False

        key = self._keys[key_id]
        updated = ApiKey(
            id=key.id,
            name=key.name,
            description=key.description,
            key_prefix=key.key_prefix,
            key_hash=key.key_hash,
            permissions=key.permissions,
            is_active=False,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            revoked_at=datetime.utcnow(),
            created_by=key.created_by,
        )
        self._keys[key_id] = updated
        return True

    def delete(self, key_id: str) -> bool:
        if key_id not in self._keys:
            return False

        key = self._keys[key_id]
        del self._hash_index[key.key_hash]
        del self._keys[key_id]
        return True


class PostgresApiKeyRepository(ApiKeyRepository):
    """
    PostgreSQL implementation for production.
    Uses environment variable for database connection.
    """

    def __init__(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

    def _get_connection(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def _row_to_api_key(self, row: dict) -> ApiKey:
        return ApiKey(
            id=str(row["id"]),
            name=row["name"],
            description=row.get("description"),
            key_prefix=row["key_prefix"],
            key_hash=row["key_hash"],
            permissions=row.get("permissions", ["read"]),
            is_active=row["is_active"],
            created_at=row["created_at"],
            expires_at=row.get("expires_at"),
            last_used_at=row.get("last_used_at"),
            revoked_at=row.get("revoked_at"),
            created_by=row["created_by"],
        )

    def save(self, api_key: ApiKey) -> None:
        import json
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO api_keys (
                        id, name, description, key_prefix, key_hash,
                        permissions, is_active, created_at, expires_at, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        api_key.id,
                        api_key.name,
                        api_key.description,
                        api_key.key_prefix,
                        api_key.key_hash,
                        json.dumps(api_key.permissions),
                        api_key.is_active,
                        api_key.created_at,
                        api_key.expires_at,
                        api_key.created_by,
                    )
                )
            conn.commit()

    def find_by_id(self, key_id: str) -> Optional[ApiKey]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM api_keys WHERE id = %s", (key_id,))
                row = cur.fetchone()
                return self._row_to_api_key(row) if row else None

    def find_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM api_keys WHERE key_hash = %s", (key_hash,))
                row = cur.fetchone()
                return self._row_to_api_key(row) if row else None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[ApiKey]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM api_keys ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
                rows = cur.fetchall()
                return [self._row_to_api_key(row) for row in rows]

    def count(self) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM api_keys")
                row = cur.fetchone()
                return row["count"] if row else 0

    def update(self, api_key: ApiKey) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE api_keys
                    SET name = %s, description = %s
                    WHERE id = %s
                    """,
                    (api_key.name, api_key.description, api_key.id)
                )
            conn.commit()

    def update_last_used(self, key_id: str) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE api_keys SET last_used_at = NOW() WHERE id = %s",
                    (key_id,)
                )
            conn.commit()

    def revoke(self, key_id: str) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE api_keys
                    SET is_active = FALSE, revoked_at = NOW()
                    WHERE id = %s
                    RETURNING id
                    """,
                    (key_id,)
                )
                row = cur.fetchone()
            conn.commit()
            return row is not None

    def delete(self, key_id: str) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM api_keys WHERE id = %s RETURNING id",
                    (key_id,)
                )
                row = cur.fetchone()
            conn.commit()
            return row is not None


# ============================================================================
# Factory function
# ============================================================================

_repository: Optional[ApiKeyRepository] = None


def get_api_key_repository() -> ApiKeyRepository:
    """
    Get the API key repository instance.

    Uses PostgreSQL if DATABASE_URL is set, otherwise in-memory.
    """
    global _repository

    if _repository is None:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            try:
                _repository = PostgresApiKeyRepository()
            except Exception as e:
                print(f"Warning: Failed to connect to PostgreSQL: {e}")
                print("Falling back to in-memory repository")
                _repository = InMemoryApiKeyRepository()
        else:
            _repository = InMemoryApiKeyRepository()

    return _repository


def set_api_key_repository(repo: ApiKeyRepository) -> None:
    """Set the API key repository (for testing)."""
    global _repository
    _repository = repo
