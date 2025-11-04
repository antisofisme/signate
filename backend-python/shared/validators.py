"""
Shared Validators
Common validation functions and rules
"""

import re
from typing import Optional, Any
from datetime import datetime


# =============================================================================
# STRING VALIDATORS
# =============================================================================

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
