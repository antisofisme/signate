"""
Unit Tests for shared/validators.py
Tests all validation functions for correctness and security
"""

import pytest
from shared.validators import (
    sanitize_string,
    sanitize_html,
    contains_html_tags,
    contains_script_tags,
    validate_safe_string,
    validate_email,
    validate_username,
    validate_password,
    validate_phone,
    validate_activation_code,
    validate_pin,
    validate_range,
    validate_positive,
    validate_date_format,
    validate_file_extension,
    validate_file_size,
    validate_url,
    validate_path_safe,
    validate_no_sql_injection,
    validate_alphanumeric,
)


# =============================================================================
# STRING SANITIZATION TESTS
# =============================================================================

class TestSanitizeString:
    """Tests for sanitize_string function"""

    def test_strips_whitespace(self):
        assert sanitize_string("  hello  ") == "hello"

    def test_empty_string(self):
        assert sanitize_string("") == ""

    def test_none_returns_empty(self):
        assert sanitize_string(None) == ""

    def test_preserves_internal_spaces(self):
        assert sanitize_string("  hello world  ") == "hello world"


class TestSanitizeHtml:
    """Tests for sanitize_html function - XSS prevention"""

    def test_escapes_script_tag(self):
        result = sanitize_html("<script>alert('XSS')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escapes_html_entities(self):
        result = sanitize_html("<b>Bold</b>")
        assert "<b>" not in result
        assert "&lt;b&gt;" in result

    def test_normal_text_unchanged(self):
        assert sanitize_html("Normal text") == "Normal text"

    def test_empty_string(self):
        assert sanitize_html("") == ""

    def test_none_returns_empty(self):
        assert sanitize_html(None) == ""


class TestContainsHtmlTags:
    """Tests for contains_html_tags function"""

    def test_detects_html_tag(self):
        assert contains_html_tags("<b>Bold</b>") is True

    def test_detects_self_closing_tag(self):
        assert contains_html_tags("<br/>") is True

    def test_no_html_returns_false(self):
        assert contains_html_tags("Plain text") is False

    def test_empty_string(self):
        assert contains_html_tags("") is False


class TestContainsScriptTags:
    """Tests for contains_script_tags function - security critical"""

    def test_detects_script_tag(self):
        assert contains_script_tags("<script>alert('XSS')</script>") is True

    def test_detects_iframe(self):
        assert contains_script_tags("<iframe src='evil.com'>") is True

    def test_detects_javascript_protocol(self):
        assert contains_script_tags("javascript:alert('XSS')") is True

    def test_detects_event_handlers(self):
        assert contains_script_tags("<img onerror='alert(1)'>") is True
        assert contains_script_tags("<div onclick='evil()'>") is True

    def test_case_insensitive(self):
        assert contains_script_tags("<SCRIPT>alert('XSS')</SCRIPT>") is True

    def test_normal_text_safe(self):
        assert contains_script_tags("Normal text") is False


# =============================================================================
# INPUT VALIDATION TESTS
# =============================================================================

class TestValidateSafeString:
    """Tests for validate_safe_string function"""

    def test_normal_text_valid(self):
        is_valid, error = validate_safe_string("Normal text")
        assert is_valid is True
        assert error is None

    def test_script_tag_invalid(self):
        is_valid, error = validate_safe_string("<script>alert('XSS')</script>")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_max_length_exceeded(self):
        is_valid, error = validate_safe_string("a" * 1001)
        assert is_valid is False
        assert "1000" in error

    def test_custom_max_length(self):
        is_valid, error = validate_safe_string("a" * 51, max_length=50)
        assert is_valid is False
        assert "50" in error


class TestValidateEmail:
    """Tests for validate_email function"""

    def test_valid_email(self):
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True

    def test_valid_email_with_subdomain(self):
        is_valid, error = validate_email("user@mail.example.com")
        assert is_valid is True

    def test_invalid_email_no_at(self):
        is_valid, error = validate_email("userexample.com")
        assert is_valid is False

    def test_invalid_email_no_domain(self):
        is_valid, error = validate_email("user@")
        assert is_valid is False


class TestValidateUsername:
    """Tests for validate_username function"""

    def test_valid_username(self):
        is_valid, error = validate_username("john_doe")
        assert is_valid is True

    def test_valid_with_numbers(self):
        is_valid, error = validate_username("user123")
        assert is_valid is True

    def test_too_short(self):
        is_valid, error = validate_username("ab")
        assert is_valid is False
        assert "3" in error

    def test_invalid_characters(self):
        is_valid, error = validate_username("user@name")
        assert is_valid is False


class TestValidatePassword:
    """Tests for validate_password function"""

    def test_valid_strong_password(self):
        is_valid, error = validate_password("SecurePass123")
        assert is_valid is True

    def test_too_short(self):
        is_valid, error = validate_password("Short1")
        assert is_valid is False
        assert "8" in error

    def test_missing_uppercase(self):
        is_valid, error = validate_password("lowercase123")
        assert is_valid is False
        assert "uppercase" in error.lower()

    def test_missing_lowercase(self):
        is_valid, error = validate_password("UPPERCASE123")
        assert is_valid is False
        assert "lowercase" in error.lower()

    def test_missing_digit(self):
        is_valid, error = validate_password("NoDigitsHere")
        assert is_valid is False
        assert "digit" in error.lower()


class TestValidatePhone:
    """Tests for validate_phone function"""

    def test_valid_international(self):
        assert validate_phone("+62812345678") is True

    def test_valid_local(self):
        assert validate_phone("081234567890") is True

    def test_valid_with_dashes(self):
        assert validate_phone("0812-345-678") is True

    def test_invalid_short(self):
        assert validate_phone("123") is False


# =============================================================================
# CODE VALIDATION TESTS
# =============================================================================

class TestValidateActivationCode:
    """Tests for validate_activation_code function"""

    def test_valid_code(self):
        is_valid, error = validate_activation_code("ABC123")
        assert is_valid is True

    def test_wrong_length(self):
        is_valid, error = validate_activation_code("ABC")
        assert is_valid is False
        assert "6" in error

    def test_non_alphanumeric(self):
        is_valid, error = validate_activation_code("ABC-12")
        assert is_valid is False


class TestValidatePin:
    """Tests for validate_pin function"""

    def test_valid_pin(self):
        is_valid, error = validate_pin("123456")
        assert is_valid is True

    def test_wrong_length(self):
        is_valid, error = validate_pin("12345")
        assert is_valid is False

    def test_non_numeric(self):
        is_valid, error = validate_pin("12345a")
        assert is_valid is False


# =============================================================================
# NUMERIC VALIDATION TESTS
# =============================================================================

class TestValidateRange:
    """Tests for validate_range function"""

    def test_within_range(self):
        is_valid, error = validate_range(50, min_value=0, max_value=100)
        assert is_valid is True

    def test_below_min(self):
        is_valid, error = validate_range(-5, min_value=0, max_value=100)
        assert is_valid is False

    def test_above_max(self):
        is_valid, error = validate_range(150, min_value=0, max_value=100)
        assert is_valid is False

    def test_invalid_type(self):
        is_valid, error = validate_range("not a number", min_value=0)
        assert is_valid is False


class TestValidatePositive:
    """Tests for validate_positive function"""

    def test_positive_valid(self):
        is_valid, error = validate_positive(10)
        assert is_valid is True

    def test_zero_invalid(self):
        is_valid, error = validate_positive(0)
        assert is_valid is False

    def test_negative_invalid(self):
        is_valid, error = validate_positive(-5)
        assert is_valid is False


# =============================================================================
# DATE VALIDATION TESTS
# =============================================================================

class TestValidateDateFormat:
    """Tests for validate_date_format function"""

    def test_valid_date(self):
        is_valid, error = validate_date_format("2025-01-04")
        assert is_valid is True

    def test_invalid_format(self):
        is_valid, error = validate_date_format("04-01-2025")
        assert is_valid is False

    def test_invalid_date(self):
        is_valid, error = validate_date_format("2025-13-45")
        assert is_valid is False


# =============================================================================
# FILE VALIDATION TESTS
# =============================================================================

class TestValidateFileExtension:
    """Tests for validate_file_extension function"""

    def test_allowed_extension(self):
        is_valid, error = validate_file_extension("image.jpg", [".jpg", ".png"])
        assert is_valid is True

    def test_disallowed_extension(self):
        is_valid, error = validate_file_extension("document.pdf", [".jpg", ".png"])
        assert is_valid is False

    def test_case_insensitive(self):
        is_valid, error = validate_file_extension("IMAGE.JPG", [".jpg", ".png"])
        assert is_valid is True


class TestValidateFileSize:
    """Tests for validate_file_size function"""

    def test_within_limit(self):
        is_valid, error = validate_file_size(5 * 1024 * 1024, max_size_mb=10)
        assert is_valid is True

    def test_exceeds_limit(self):
        is_valid, error = validate_file_size(15 * 1024 * 1024, max_size_mb=10)
        assert is_valid is False


# =============================================================================
# SECURITY VALIDATION TESTS
# =============================================================================

class TestValidateUrl:
    """Tests for validate_url function - security critical"""

    def test_valid_https(self):
        is_valid, error = validate_url("https://example.com")
        assert is_valid is True

    def test_valid_http(self):
        is_valid, error = validate_url("http://example.com")
        assert is_valid is True

    def test_javascript_protocol_blocked(self):
        is_valid, error = validate_url("javascript:alert('XSS')")
        assert is_valid is False

    def test_ftp_blocked_by_default(self):
        is_valid, error = validate_url("ftp://example.com")
        assert is_valid is False

    def test_custom_allowed_schemes(self):
        is_valid, error = validate_url("ftp://example.com", allowed_schemes=["ftp"])
        assert is_valid is True


class TestValidatePathSafe:
    """Tests for validate_path_safe function - directory traversal prevention"""

    def test_valid_path(self):
        is_valid, error = validate_path_safe("uploads/image.jpg")
        assert is_valid is True

    def test_directory_traversal_blocked(self):
        is_valid, error = validate_path_safe("../../etc/passwd")
        assert is_valid is False
        assert "traversal" in error.lower()

    def test_absolute_path_blocked(self):
        is_valid, error = validate_path_safe("/etc/passwd")
        assert is_valid is False
        assert "absolute" in error.lower()

    def test_null_byte_blocked(self):
        is_valid, error = validate_path_safe("file.txt\0.jpg")
        assert is_valid is False


class TestValidateNoSqlInjection:
    """Tests for validate_no_sql_injection function - SQL injection prevention"""

    def test_normal_text_valid(self):
        is_valid, error = validate_no_sql_injection("Normal text")
        assert is_valid is True

    def test_select_statement_blocked(self):
        is_valid, error = validate_no_sql_injection("SELECT * FROM users")
        assert is_valid is False

    def test_drop_statement_blocked(self):
        is_valid, error = validate_no_sql_injection("'; DROP TABLE users--")
        assert is_valid is False

    def test_union_select_blocked(self):
        is_valid, error = validate_no_sql_injection("' UNION SELECT password FROM users")
        assert is_valid is False


class TestValidateAlphanumeric:
    """Tests for validate_alphanumeric function"""

    def test_valid_alphanumeric(self):
        is_valid, error = validate_alphanumeric("Test123")
        assert is_valid is True

    def test_with_spaces(self):
        is_valid, error = validate_alphanumeric("Test 123", allow_spaces=True)
        assert is_valid is True

    def test_with_special_chars(self):
        is_valid, error = validate_alphanumeric("Test-123", allow_special="-")
        assert is_valid is True

    def test_invalid_chars_blocked(self):
        is_valid, error = validate_alphanumeric("Test<script>")
        assert is_valid is False
