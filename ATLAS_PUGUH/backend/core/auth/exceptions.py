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
