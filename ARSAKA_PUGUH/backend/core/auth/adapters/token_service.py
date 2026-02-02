"""
JWT Token Service

Implementation of ITokenService for JWT operations.
Handles access tokens, refresh tokens, and verification tokens.

Source: INFRA-DEC-008-auth-flow.md
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.token_service import (
    ITokenService,
    TokenPayload,
    TokenPair,
    TenantContext,
)
from ..exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
)


class JWTTokenService(ITokenService):
    """JWT token service implementation.

    SECURITY: This implementation includes protections against:
    - Algorithm confusion attacks (strict algorithm verification)
    - Weak secrets (minimum length validation)
    - Known default secrets (blocklist check)
    """

    # SECURITY: Allowed algorithms (prevent algorithm confusion attacks)
    ALLOWED_ALGORITHMS = {"HS256", "HS384", "HS512"}

    # SECURITY: Blocked default/weak secrets
    BLOCKED_SECRETS = {
        "CHANGE_THIS_SECRET_KEY",
        "secret",
        "password",
        "jwt_secret",
        "changeme",
        "your-secret-key",
        "your_secret_key",
        "supersecret",
    }

    # SECURITY: Minimum secret length for HS256
    MIN_SECRET_LENGTH = 32

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
        refresh_token_remember_days: int = 30,
        verification_token_expire_hours: int = 24,
        reset_token_expire_hours: int = 1,
        session_factory=None,  # For database operations
        skip_secret_validation: bool = False,  # For testing only
    ):
        """Initialize JWT token service.

        Args:
            secret_key: JWT signing secret (min 32 chars for HS256)
            algorithm: JWT algorithm (HS256, HS384, HS512 only)
            access_token_expire_minutes: Access token expiry
            refresh_token_expire_days: Refresh token expiry
            refresh_token_remember_days: Extended refresh token expiry
            verification_token_expire_hours: Email verification token expiry
            reset_token_expire_hours: Password reset token expiry
            session_factory: Database session factory
            skip_secret_validation: Skip validation (ONLY for testing)

        Raises:
            ValueError: If algorithm or secret is insecure
        """
        # SECURITY: Validate algorithm
        if algorithm not in self.ALLOWED_ALGORITHMS:
            raise ValueError(
                f"Algorithm '{algorithm}' not allowed. "
                f"Use one of: {', '.join(sorted(self.ALLOWED_ALGORITHMS))}"
            )

        # SECURITY: Validate secret (unless testing)
        if not skip_secret_validation:
            self._validate_secret(secret_key, algorithm)

        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expire = timedelta(minutes=access_token_expire_minutes)
        self._refresh_expire = timedelta(days=refresh_token_expire_days)
        self._refresh_remember_expire = timedelta(days=refresh_token_remember_days)
        self._verification_expire = timedelta(hours=verification_token_expire_hours)
        self._reset_expire = timedelta(hours=reset_token_expire_hours)
        self._session_factory = session_factory

    def _validate_secret(self, secret: str, algorithm: str) -> None:
        """Validate JWT secret meets security requirements.

        SECURITY: Prevents weak secrets that could be brute-forced.

        Args:
            secret: The JWT secret key
            algorithm: The algorithm being used

        Raises:
            ValueError: If secret is too weak
        """
        # Check for blocked secrets
        if secret.lower() in {s.lower() for s in self.BLOCKED_SECRETS}:
            raise ValueError(
                "SECURITY ERROR: Default/weak JWT secret detected. "
                "Set JWT_SECRET_KEY environment variable to a secure random value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

        # Check minimum length based on algorithm
        min_lengths = {
            "HS256": 32,  # 256 bits
            "HS384": 48,  # 384 bits
            "HS512": 64,  # 512 bits
        }
        min_len = min_lengths.get(algorithm, 32)

        if len(secret) < min_len:
            raise ValueError(
                f"SECURITY ERROR: JWT secret too short for {algorithm}. "
                f"Minimum length: {min_len} characters. Current: {len(secret)}. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

    async def create_access_token(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str],
        tenants: List[TenantContext],
        active_tenant_id: Optional[str] = None,
        active_project_id: Optional[str] = None,
    ) -> str:
        """Create JWT access token."""
        now = datetime.utcnow()
        expire = now + self._access_expire

        payload = {
            "sub": user_id,
            "email": email,
            "display_name": display_name,
            "tenants": [
                {
                    "tenant_id": t.tenant_id,
                    "slug": t.slug,
                    "role": t.role,
                    "projects": t.projects,
                }
                for t in tenants
            ],
            "active_tenant_id": active_tenant_id,
            "active_project_id": active_project_id,
            "iat": now,
            "exp": expire,
            "jti": str(uuid4()),
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    async def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token."""
        now = datetime.utcnow()
        expire = now + self._refresh_expire

        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": expire,
            "jti": str(uuid4()),
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    async def create_token_pair(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str],
        tenants: List[TenantContext],
        active_tenant_id: Optional[str] = None,
        active_project_id: Optional[str] = None,
        remember_me: bool = False,
    ) -> TokenPair:
        """Create access and refresh token pair."""
        access_token = await self.create_access_token(
            user_id=user_id,
            email=email,
            display_name=display_name,
            tenants=tenants,
            active_tenant_id=active_tenant_id,
            active_project_id=active_project_id,
        )

        # Create refresh token with extended expiry if remember_me
        now = datetime.utcnow()
        expire = now + (self._refresh_remember_expire if remember_me else self._refresh_expire)

        refresh_payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": expire,
            "jti": str(uuid4()),
        }
        refresh_token = jwt.encode(refresh_payload, self._secret_key, algorithm=self._algorithm)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(self._access_expire.total_seconds()),
        )

    async def verify_access_token(self, token: str) -> TokenPayload:
        """Verify and decode access token.

        SECURITY: Strict algorithm verification to prevent confusion attacks.
        Only the configured algorithm is accepted.
        """
        try:
            # SECURITY: Decode with strict algorithm verification
            # Only accept the exact algorithm we configured
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],  # STRICT: Only configured algorithm
                options={
                    "require": ["exp", "iat", "sub"],  # Required claims
                    "verify_exp": True,
                    "verify_iat": True,
                }
            )

            # Check if revoked
            jti = payload.get("jti")
            if jti and await self.is_revoked(jti):
                raise TokenRevokedError("Token has been revoked")

            # Parse tenants
            tenants = [
                TenantContext(
                    tenant_id=t["tenant_id"],
                    slug=t["slug"],
                    role=t["role"],
                    projects=t.get("projects", []),
                )
                for t in payload.get("tenants", [])
            ]

            return TokenPayload(
                user_id=payload["sub"],
                email=payload["email"],
                display_name=payload.get("display_name"),
                tenants=tenants,
                active_tenant_id=payload.get("active_tenant_id"),
                active_project_id=payload.get("active_project_id"),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=payload.get("jti", ""),
            )

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Access token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid access token: {e}")

    async def verify_refresh_token(self, token: str) -> str:
        """Verify refresh token and return user_id.

        SECURITY: Strict algorithm verification to prevent confusion attacks.
        """
        try:
            # SECURITY: Decode with strict algorithm verification
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],  # STRICT: Only configured algorithm
                options={
                    "require": ["exp", "iat", "sub", "type"],  # Required claims
                    "verify_exp": True,
                    "verify_iat": True,
                }
            )

            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise TokenInvalidError("Not a refresh token")

            # Check if revoked
            jti = payload.get("jti")
            if jti and await self.is_revoked(jti):
                raise TokenRevokedError("Refresh token has been revoked")

            return payload["sub"]

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid refresh token: {e}")

    async def revoke_token(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist."""
        if not self._session_factory:
            return

        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO token_blacklist (jti, expires_at)
                    VALUES (:jti, :expires_at)
                    ON CONFLICT (jti) DO NOTHING
                """),
                {"jti": jti, "expires_at": expires_at}
            )
            await session.commit()

    async def is_revoked(self, jti: str) -> bool:
        """Check if token is revoked."""
        if not self._session_factory:
            return False

        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM token_blacklist WHERE jti = :jti"),
                {"jti": jti}
            )
            return result.scalar() is not None

    async def create_verification_token(self, user_id: str) -> str:
        """Create email verification token."""
        token = secrets.token_hex(32)  # 64 char hex string
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.utcnow() + self._verification_expire

        if self._session_factory:
            async with self._session_factory() as session:
                await session.execute(
                    text("""
                        INSERT INTO auth_tokens (user_id, token_hash, token_type, expires_at)
                        VALUES (:user_id, :token_hash, 'email_verification', :expires_at)
                    """),
                    {
                        "user_id": user_id,
                        "token_hash": token_hash,
                        "expires_at": expires_at,
                    }
                )
                await session.commit()

        return token

    async def verify_verification_token(self, token: str) -> str:
        """Verify email verification token and return user_id."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        if not self._session_factory:
            raise TokenInvalidError("Token service not configured")

        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT user_id, expires_at, used_at
                    FROM auth_tokens
                    WHERE token_hash = :token_hash
                      AND token_type = 'email_verification'
                """),
                {"token_hash": token_hash}
            )
            row = result.fetchone()

            if not row:
                raise TokenInvalidError("Invalid verification token")

            user_id, expires_at, used_at = row

            if used_at:
                raise TokenInvalidError("Token has already been used")

            if expires_at < datetime.utcnow():
                raise TokenExpiredError("Verification token has expired")

            return str(user_id)

    async def create_password_reset_token(self, user_id: str) -> str:
        """Create password reset token."""
        token = secrets.token_hex(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.utcnow() + self._reset_expire

        if self._session_factory:
            async with self._session_factory() as session:
                await session.execute(
                    text("""
                        INSERT INTO auth_tokens (user_id, token_hash, token_type, expires_at)
                        VALUES (:user_id, :token_hash, 'password_reset', :expires_at)
                    """),
                    {
                        "user_id": user_id,
                        "token_hash": token_hash,
                        "expires_at": expires_at,
                    }
                )
                await session.commit()

        return token

    async def verify_password_reset_token(self, token: str) -> str:
        """Verify password reset token and return user_id."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        if not self._session_factory:
            raise TokenInvalidError("Token service not configured")

        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT user_id, expires_at, used_at
                    FROM auth_tokens
                    WHERE token_hash = :token_hash
                      AND token_type = 'password_reset'
                """),
                {"token_hash": token_hash}
            )
            row = result.fetchone()

            if not row:
                raise TokenInvalidError("Invalid reset token")

            user_id, expires_at, used_at = row

            if used_at:
                raise TokenInvalidError("Reset token has already been used")

            if expires_at < datetime.utcnow():
                raise TokenExpiredError("Reset token has expired")

            return str(user_id)

    async def mark_token_used(self, token: str) -> None:
        """Mark a one-time token as used."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        if self._session_factory:
            async with self._session_factory() as session:
                await session.execute(
                    text("""
                        UPDATE auth_tokens
                        SET used_at = NOW()
                        WHERE token_hash = :token_hash
                    """),
                    {"token_hash": token_hash}
                )
                await session.commit()
