"""
Shared Validators
Common validation functions and rules

Enhanced with security validators:
- XSS prevention (HTML sanitization)
- Path traversal prevention
- URL validation
- SQL injection prevention (via parameterized queries)
"""

import re
import html
from typing import Optional, Any
from datetime import datetime
from urllib.parse import urlparse


# =============================================================================
# STRING VALIDATORS
# =============================================================================

def sanitize_string(text: str) -> str:
    """
    Sanitize string by stripping whitespace

    Args:
        text: String to sanitize

    Returns:
        Sanitized string
    """
    if not text:
        return ""
    return text.strip()


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks

    Escapes HTML special characters to prevent script injection

    Args:
        text: String that may contain HTML

    Returns:
        HTML-escaped string safe for display

    Example:
        >>> sanitize_html("<script>alert('XSS')</script>")
        "&lt;script&gt;alert('XSS')&lt;/script&gt;"
        >>> sanitize_html("Normal text")
        "Normal text"
    """
    if not text:
        return ""
    return html.escape(text)


def contains_html_tags(text: str) -> bool:
    """
    Check if string contains HTML tags

    Args:
        text: String to check

    Returns:
        True if HTML tags detected

    Example:
        >>> contains_html_tags("<b>Bold</b>")
        True
        >>> contains_html_tags("Plain text")
        False
    """
    if not text:
        return False
    # Match HTML tags like <tag>, </tag>, <tag/>
    html_pattern = r'<[^>]+>'
    return bool(re.search(html_pattern, text))


def contains_script_tags(text: str) -> bool:
    """
    Check if string contains potentially dangerous script tags

    Args:
        text: String to check

    Returns:
        True if script tags detected (case-insensitive)

    Example:
        >>> contains_script_tags("<script>alert('XSS')</script>")
        True
        >>> contains_script_tags("Normal text")
        False
    """
    if not text:
        return False
    dangerous_tags = [
        r'<script[^>]*>',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers like onclick=, onerror=
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in dangerous_tags)


def validate_safe_string(text: str, max_length: int = 1000) -> tuple[bool, Optional[str]]:
    """
    Validate string is safe (no HTML/script injection)

    Args:
        text: String to validate
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_safe_string("Normal text")
        (True, None)
        >>> validate_safe_string("<script>alert('XSS')</script>")
        (False, "Input contains potentially dangerous content")
    """
    if not text:
        return True, None

    if len(text) > max_length:
        return False, f"Input must not exceed {max_length} characters"

    if contains_script_tags(text):
        return False, "Input contains potentially dangerous content"

    return True, None


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        True if valid email format

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str, min_length: int = 3, max_length: int = 50) -> tuple[bool, Optional[str]]:
    """
    Validate username format

    Args:
        username: Username to validate
        min_length: Minimum length (default: 3)
        max_length: Maximum length (default: 50)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_username("john_doe")
        (True, None)
        >>> validate_username("ab")
        (False, "Username must be between 3 and 50 characters")
    """
    if len(username) < min_length or len(username) > max_length:
        return False, f"Username must be between {min_length} and {max_length} characters"

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, None


def validate_password(password: str, min_length: int = 8) -> tuple[bool, Optional[str]]:
    """
    Validate password strength

    Args:
        password: Password to validate
        min_length: Minimum length (default: 8)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_password("SecurePass123!")
        (True, None)
        >>> validate_password("weak")
        (False, "Password must be at least 8 characters long")
    """
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    return True, None


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format

    Args:
        phone: Phone number to validate

    Returns:
        True if valid phone format

    Example:
        >>> validate_phone("+62812345678")
        True
        >>> validate_phone("081234567890")
        True
    """
    # Remove spaces and dashes
    cleaned = re.sub(r'[\s-]', '', phone)

    # Check if it's a valid format
    patterns = [
        r'^\+?\d{10,15}$',  # International format
        r'^0\d{9,14}$',     # Local format starting with 0
    ]

    return any(re.match(pattern, cleaned) for pattern in patterns)


# =============================================================================
# CODE VALIDATORS
# =============================================================================

def validate_activation_code(code: str) -> tuple[bool, Optional[str]]:
    """
    Validate activation code format (6 characters, alphanumeric)

    Args:
        code: Activation code to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_activation_code("ABC123")
        (True, None)
        >>> validate_activation_code("abc")
        (False, "Activation code must be exactly 6 characters")
    """
    if len(code) != 6:
        return False, "Activation code must be exactly 6 characters"

    if not code.isalnum():
        return False, "Activation code must contain only letters and numbers"

    return True, None


def validate_pin(pin: str, length: int = 6) -> tuple[bool, Optional[str]]:
    """
    Validate PIN format

    Args:
        pin: PIN to validate
        length: Expected PIN length (default: 6)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_pin("123456")
        (True, None)
        >>> validate_pin("12345")
        (False, "PIN must be exactly 6 digits")
    """
    if len(pin) != length:
        return False, f"PIN must be exactly {length} digits"

    if not pin.isdigit():
        return False, "PIN must contain only digits"

    return True, None


# =============================================================================
# NUMERIC VALIDATORS
# =============================================================================

def validate_range(
    value: Any,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> tuple[bool, Optional[str]]:
    """
    Validate if value is within range

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_range(50, min_value=0, max_value=100)
        (True, None)
        >>> validate_range(150, min_value=0, max_value=100)
        (False, "Value must be at most 100")
    """
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return False, "Value must be a number"

    if min_value is not None and numeric_value < min_value:
        return False, f"Value must be at least {min_value}"

    if max_value is not None and numeric_value > max_value:
        return False, f"Value must be at most {max_value}"

    return True, None


def validate_positive(value: Any) -> tuple[bool, Optional[str]]:
    """
    Validate if value is positive

    Args:
        value: Value to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_positive(10)
        (True, None)
        >>> validate_positive(-5)
        (False, "Value must be positive")
    """
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return False, "Value must be a number"

    if numeric_value <= 0:
        return False, "Value must be positive"

    return True, None


# =============================================================================
# DATE VALIDATORS
# =============================================================================

def validate_date_format(date_string: str, format: str = "%Y-%m-%d") -> tuple[bool, Optional[str]]:
    """
    Validate date string format

    Args:
        date_string: Date string to validate
        format: Expected date format (default: YYYY-MM-DD)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_date_format("2025-01-04")
        (True, None)
        >>> validate_date_format("04-01-2025")
        (False, "Invalid date format, expected YYYY-MM-DD")
    """
    try:
        datetime.strptime(date_string, format)
        return True, None
    except ValueError:
        return False, f"Invalid date format, expected {format}"


def validate_future_date(date_string: str, format: str = "%Y-%m-%d") -> tuple[bool, Optional[str]]:
    """
    Validate if date is in the future

    Args:
        date_string: Date string to validate
        format: Date format (default: YYYY-MM-DD)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_future_date("2030-01-01")
        (True, None)
        >>> validate_future_date("2020-01-01")
        (False, "Date must be in the future")
    """
    try:
        date = datetime.strptime(date_string, format)
        if date <= datetime.now():
            return False, "Date must be in the future"
        return True, None
    except ValueError:
        return False, f"Invalid date format, expected {format}"


# =============================================================================
# FILE VALIDATORS
# =============================================================================

def validate_file_extension(filename: str, allowed_extensions: list[str]) -> tuple[bool, Optional[str]]:
    """
    Validate file extension

    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png'])

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_file_extension("image.jpg", ['.jpg', '.png'])
        (True, None)
        >>> validate_file_extension("document.pdf", ['.jpg', '.png'])
        (False, "File type not allowed. Allowed: .jpg, .png")
    """
    import os

    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in [e.lower() for e in allowed_extensions]:
        return False, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"

    return True, None


def validate_file_size(size_bytes: int, max_size_mb: int = 10) -> tuple[bool, Optional[str]]:
    """
    Validate file size

    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in MB (default: 10)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_file_size(5 * 1024 * 1024, max_size_mb=10)  # 5 MB
        (True, None)
        >>> validate_file_size(15 * 1024 * 1024, max_size_mb=10)  # 15 MB
        (False, "File size must not exceed 10 MB")
    """
    max_bytes = max_size_mb * 1024 * 1024

    if size_bytes > max_bytes:
        return False, f"File size must not exceed {max_size_mb} MB"

    return True, None


# =============================================================================
# SECURITY VALIDATORS
# =============================================================================

def validate_url(url: str, allowed_schemes: list[str] = None) -> tuple[bool, Optional[str]]:
    """
    Validate URL format and scheme

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_url("https://example.com")
        (True, None)
        >>> validate_url("javascript:alert('XSS')")
        (False, "URL scheme not allowed")
        >>> validate_url("ftp://example.com", allowed_schemes=['http', 'https'])
        (False, "URL scheme not allowed. Allowed: http, https")
    """
    if not url:
        return False, "URL cannot be empty"

    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    try:
        parsed = urlparse(url)

        # Check if scheme is present
        if not parsed.scheme:
            return False, "Invalid URL format"

        # Check if scheme is allowed
        if parsed.scheme.lower() not in [s.lower() for s in allowed_schemes]:
            return False, f"URL scheme not allowed. Allowed: {', '.join(allowed_schemes)}"

        # Check if netloc (domain) is present
        if not parsed.netloc:
            return False, "Invalid URL format - missing domain"

        return True, None
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_path_safe(path: str) -> tuple[bool, Optional[str]]:
    """
    Validate path is safe (no directory traversal)

    Prevents path traversal attacks like ../../etc/passwd

    Args:
        path: File path to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_path_safe("uploads/image.jpg")
        (True, None)
        >>> validate_path_safe("../../etc/passwd")
        (False, "Path contains directory traversal")
        >>> validate_path_safe("/etc/passwd")
        (False, "Absolute paths not allowed")
    """
    if not path:
        return False, "Path cannot be empty"

    # Check for directory traversal patterns
    dangerous_patterns = [
        r'\.\.',      # Parent directory reference
        r'\/\/+',     # Multiple slashes
        r'^/',        # Absolute path
        r'^\\',       # Windows absolute path
        r'[A-Z]:',    # Windows drive letter
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, path):
            if pattern == r'\.\':
                return False, "Path contains directory traversal"
            elif pattern in [r'^/', r'^\\', r'[A-Z]:']:
                return False, "Absolute paths not allowed"
            else:
                return False, "Invalid path format"

    # Check for null bytes (path truncation attack)
    if '\0' in path:
        return False, "Path contains invalid characters"

    return True, None


def validate_no_sql_injection(text: str) -> tuple[bool, Optional[str]]:
    """
    Validate input doesn't contain SQL injection patterns

    Note: This is a secondary defense. Primary defense is using
    parameterized queries (which SQLAlchemy ORM does automatically).

    Args:
        text: Input text to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_no_sql_injection("Normal text")
        (True, None)
        >>> validate_no_sql_injection("'; DROP TABLE users--")
        (False, "Input contains potentially dangerous SQL patterns")
    """
    if not text:
        return True, None

    # Common SQL injection patterns
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(--|#|\/\*|\*\/)',  # SQL comments
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bOR\b.*=.*)',
        r'(\'.*--)',
        r'(;.*\b(DROP|DELETE|UPDATE)\b)',
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Input contains potentially dangerous SQL patterns"

    return True, None


def validate_alphanumeric(text: str, allow_spaces: bool = False, allow_special: str = "") -> tuple[bool, Optional[str]]:
    """
    Validate text contains only alphanumeric characters

    Args:
        text: Text to validate
        allow_spaces: Allow spaces (default: False)
        allow_special: String of additional allowed special characters (default: "")

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_alphanumeric("Test123")
        (True, None)
        >>> validate_alphanumeric("Test 123", allow_spaces=True)
        (True, None)
        >>> validate_alphanumeric("Test-123", allow_special="-")
        (True, None)
        >>> validate_alphanumeric("Test<script>")
        (False, "Input contains invalid characters")
    """
    if not text:
        return True, None

    # Build allowed pattern
    pattern = r'^[a-zA-Z0-9'
    if allow_spaces:
        pattern += r'\s'
    if allow_special:
        # Escape special regex characters
        escaped_special = re.escape(allow_special)
        pattern += escaped_special
    pattern += r']+$'

    if not re.match(pattern, text):
        return False, "Input contains invalid characters"

    return True, None
