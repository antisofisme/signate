"""
Device utility functions
"""

import random
import string
from datetime import datetime, timedelta


def generate_activation_code(length: int = 6) -> str:
    """
    Generate a unique activation code for monitor devices (alphanumeric)

    Args:
        length: Length of activation code (default 6)

    Returns:
        str: Random alphanumeric code (uppercase)
    """
    # Use uppercase letters and numbers only (exclude confusing chars: 0, O, I, 1)
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    code = ''.join(random.choice(chars) for _ in range(length))
    return code


def generate_numeric_code(length: int = 6) -> str:
    """
    Generate a unique numeric activation code for browser viewers

    Args:
        length: Length of numeric code (default 6)

    Returns:
        str: Random 6-digit numeric code
    """
    # Generate random 6-digit number
    code = ''.join(random.choice(string.digits) for _ in range(length))
    return code


def get_code_expiry(minutes: int = 10) -> datetime:
    """
    Get expiry datetime for activation code

    Args:
        minutes: Minutes until expiry (default 10)

    Returns:
        datetime: Expiry timestamp
    """
    return datetime.utcnow() + timedelta(minutes=minutes)


def is_code_expired(expires_at: datetime) -> bool:
    """
    Check if activation code is expired

    Args:
        expires_at: Expiry timestamp

    Returns:
        bool: True if expired, False otherwise
    """
    return datetime.utcnow() > expires_at
