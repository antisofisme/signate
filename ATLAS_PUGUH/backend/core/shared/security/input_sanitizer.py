"""
Input Sanitizer

Sanitizes user input to prevent XSS and injection attacks.
"""

import re
import html
from typing import Any, Dict, List, Optional, Union


# HTML tags that are allowed in sanitized HTML content
ALLOWED_TAGS = {
    "p", "br", "strong", "em", "b", "i", "u",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a", "code", "pre", "blockquote",
}

# Attributes allowed on specific tags
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target"},
}

# Patterns to detect potential injection attempts
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # Script tags
    r"javascript:",  # JavaScript URLs
    r"on\w+\s*=",  # Event handlers (onclick, onload, etc.)
    r"data:",  # Data URLs
    r"vbscript:",  # VBScript
    r"expression\s*\(",  # CSS expressions
]


def sanitize_input(value: Any, max_length: Optional[int] = None) -> Any:
    """
    Sanitize user input to prevent injection attacks.

    Handles strings, lists, and dictionaries recursively.

    Args:
        value: Input value to sanitize
        max_length: Optional maximum length for strings

    Returns:
        Sanitized value
    """
    if value is None:
        return None

    if isinstance(value, str):
        return _sanitize_string(value, max_length)

    if isinstance(value, list):
        return [sanitize_input(item, max_length) for item in value]

    if isinstance(value, dict):
        return {
            sanitize_input(k): sanitize_input(v, max_length)
            for k, v in value.items()
        }

    # Numbers, booleans, etc. - return as-is
    return value


def _sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize a string value"""
    # Remove null bytes
    value = value.replace("\x00", "")

    # Escape HTML entities
    value = html.escape(value, quote=True)

    # Truncate if needed
    if max_length and len(value) > max_length:
        value = value[:max_length]

    return value


def sanitize_html(
    html_content: str,
    allowed_tags: Optional[set] = None,
    allowed_attributes: Optional[Dict[str, set]] = None,
) -> str:
    """
    Sanitize HTML content while preserving safe tags.

    Args:
        html_content: HTML string to sanitize
        allowed_tags: Set of allowed tag names (default: ALLOWED_TAGS)
        allowed_attributes: Dict of tag -> allowed attributes (default: ALLOWED_ATTRIBUTES)

    Returns:
        Sanitized HTML string
    """
    if allowed_tags is None:
        allowed_tags = ALLOWED_TAGS
    if allowed_attributes is None:
        allowed_attributes = ALLOWED_ATTRIBUTES

    # Remove dangerous patterns first
    for pattern in DANGEROUS_PATTERNS:
        html_content = re.sub(pattern, "", html_content, flags=re.IGNORECASE | re.DOTALL)

    # Simple tag-based sanitization
    # For production, use a library like bleach or html-sanitizer
    def replace_tag(match):
        full_tag = match.group(0)
        tag_name = match.group(1).lower()

        # Check if tag is allowed
        if tag_name not in allowed_tags:
            return html.escape(full_tag)

        # For allowed tags, strip dangerous attributes
        if tag_name in allowed_attributes:
            # Keep only allowed attributes
            attrs = allowed_attributes[tag_name]
            # Simple attribute filtering (for production, use proper HTML parser)
            for attr in ["onclick", "onerror", "onload", "onmouseover", "onfocus", "onblur"]:
                full_tag = re.sub(
                    rf'\s+{attr}\s*=\s*["\'][^"\']*["\']',
                    "",
                    full_tag,
                    flags=re.IGNORECASE,
                )

        return full_tag

    # Match opening tags
    html_content = re.sub(
        r"<(\w+)([^>]*)>",
        replace_tag,
        html_content,
    )

    # Match closing tags
    def replace_closing_tag(match):
        tag_name = match.group(1).lower()
        if tag_name not in allowed_tags:
            return html.escape(match.group(0))
        return match.group(0)

    html_content = re.sub(
        r"</(\w+)>",
        replace_closing_tag,
        html_content,
    )

    return html_content


def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe (not javascript:, data:, etc.)

    Args:
        url: URL to check

    Returns:
        True if URL is safe
    """
    if not url:
        return True

    url_lower = url.lower().strip()

    # Dangerous schemes
    dangerous_schemes = [
        "javascript:",
        "vbscript:",
        "data:",
        "file:",
    ]

    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            return False

    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Remove directory components
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Replace multiple underscores with single
    filename = re.sub(r"_+", "_", filename)

    # Limit length
    if len(filename) > 255:
        # Keep extension if present
        parts = filename.rsplit(".", 1)
        if len(parts) == 2 and len(parts[1]) <= 10:
            name, ext = parts
            filename = f"{name[:255-len(ext)-1]}.{ext}"
        else:
            filename = filename[:255]

    return filename or "unnamed"


def detect_injection_attempt(value: str) -> bool:
    """
    Detect potential injection attempts in input.

    Args:
        value: Input string to check

    Returns:
        True if potential injection detected
    """
    value_lower = value.lower()

    # SQL injection patterns
    sql_patterns = [
        r"'\s*or\s+",
        r"'\s*and\s+",
        r"union\s+select",
        r";\s*drop\s+",
        r";\s*delete\s+",
        r";\s*insert\s+",
        r";\s*update\s+",
        r"--\s*$",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, value_lower):
            return True

    # XSS patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, value_lower):
            return True

    return False
