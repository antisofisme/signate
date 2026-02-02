"""
Auth Module Exceptions

Custom exceptions for authentication operations.
"""


class AuthError(Exception):
    """Base class for auth errors."""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


class EmailExistsError(AuthError):
    """Raised when email already exists."""
    def __init__(self, email: str):
        super().__init__(
            message="An account with this email already exists",
            code="EMAIL_EXISTS"
        )
        self.email = email


class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS"
        )


class AccountNotVerifiedError(AuthError):
    """Raised when account email is not verified."""
    def __init__(self):
        super().__init__(
            message="Please verify your email before logging in",
            code="ACCOUNT_NOT_VERIFIED"
        )


class AccountSuspendedError(AuthError):
    """Raised when account is suspended."""
    def __init__(self):
        super().__init__(
            message="Your account has been suspended",
            code="ACCOUNT_SUSPENDED"
        )


class AccountLockedError(AuthError):
    """Raised when account is locked due to too many attempts."""
    def __init__(self, unlock_at: str = None):
        super().__init__(
            message="Account temporarily locked due to too many failed attempts",
            code="ACCOUNT_LOCKED"
        )
        self.unlock_at = unlock_at


class TokenExpiredError(AuthError):
    """Raised when token is expired."""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message, code="TOKEN_EXPIRED")


class TokenInvalidError(AuthError):
    """Raised when token is invalid."""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message, code="TOKEN_INVALID")


class TokenRevokedError(AuthError):
    """Raised when token has been revoked."""
    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message=message, code="TOKEN_REVOKED")


class OAuthError(AuthError):
    """Raised when OAuth operation fails."""
    def __init__(self, message: str):
        super().__init__(message=message, code="OAUTH_ERROR")


class OAuthAlreadyLinkedError(AuthError):
    """Raised when OAuth account is already linked to another user."""
    def __init__(self, provider: str):
        super().__init__(
            message=f"This {provider} account is already linked to another user",
            code="OAUTH_ALREADY_LINKED"
        )
        self.provider = provider


class CannotUnlinkError(AuthError):
    """Raised when cannot unlink the only auth method."""
    def __init__(self, provider: str):
        super().__init__(
            message="Cannot unlink the only authentication method",
            code="CANNOT_UNLINK"
        )
        self.provider = provider


class RateLimitError(AuthError):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: int):
        super().__init__(
            message="Too many requests. Please try again later.",
            code="RATE_LIMIT_EXCEEDED"
        )
        self.retry_after = retry_after


class ValidationError(AuthError):
    """Raised when input validation fails."""
    def __init__(self, message: str, field: str = None):
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.field = field


# API Key Exceptions

class ApiKeyError(AuthError):
    """Base class for API key errors."""
    pass


class ApiKeyNotFoundError(ApiKeyError):
    """Raised when API key is not found."""
    def __init__(self, key_id: str = None):
        super().__init__(
            message="API key not found",
            code="API_KEY_NOT_FOUND"
        )
        self.key_id = key_id


class ApiKeyRevokedError(ApiKeyError):
    """Raised when API key has been revoked."""
    def __init__(self):
        super().__init__(
            message="This API key has been revoked",
            code="API_KEY_REVOKED"
        )


class ApiKeyExpiredError(ApiKeyError):
    """Raised when API key has expired."""
    def __init__(self):
        super().__init__(
            message="This API key has expired",
            code="API_KEY_EXPIRED"
        )


class ApiKeyInvalidError(ApiKeyError):
    """Raised when API key is invalid."""
    def __init__(self):
        super().__init__(
            message="Invalid API key",
            code="API_KEY_INVALID"
        )


class ApiKeyLimitExceededError(ApiKeyError):
    """Raised when API key limit is exceeded for a tenant."""
    def __init__(self, limit: int):
        super().__init__(
            message=f"API key limit ({limit}) exceeded for this tenant",
            code="API_KEY_LIMIT_EXCEEDED"
        )
        self.limit = limit


class InsufficientScopeError(ApiKeyError):
    """Raised when API key lacks required scope."""
    def __init__(self, required_scope: str):
        super().__init__(
            message=f"API key lacks required scope: {required_scope}",
            code="INSUFFICIENT_SCOPE"
        )
        self.required_scope = required_scope
