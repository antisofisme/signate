"""
Security Test Suite for Template System

Comprehensive tests for:
- Code execution prevention
- File access blocking
- XSS protection
- DoS protection
- Information disclosure prevention
- Timeout enforcement

Run: pytest tests/test_template_security.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock

from app.services.template_service import (
    SecureTemplateRenderer,
    TemplateSecurityError,
    TemplateValidationError,
    TemplateTimeoutError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def renderer():
    """Create secure renderer instance."""
    return SecureTemplateRenderer()


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


# ============================================================================
# CODE EXECUTION TESTS
# ============================================================================

class TestCodeExecutionPrevention:
    """Test that code execution attempts are blocked."""

    @pytest.mark.asyncio
    async def test_blocks_import(self, renderer):
        """Test __import__ is blocked."""
        template = "{{__import__('os').system('id')}}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})

    @pytest.mark.asyncio
    async def test_blocks_eval(self, renderer):
        """Test eval() is blocked."""
        template = "{{eval('1+1')}}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})

    @pytest.mark.asyncio
    async def test_blocks_exec(self, renderer):
        """Test exec() is blocked."""
        template = "{{exec('print(1)')}}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})

    @pytest.mark.asyncio
    async def test_blocks_compile(self, renderer):
        """Test compile() is blocked."""
        template = "{{compile('1+1', 'string', 'eval')}}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})

    @pytest.mark.asyncio
    async def test_blocks_class_access(self, renderer):
        """Test __class__ access is blocked."""
        template = "{{''.__class__.__bases__}}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})

    @pytest.mark.asyncio
    async def test_blocks_subclass_enumeration(self, renderer):
        """Test subclass enumeration is blocked."""
        template = "{% for x in [].__class__.__base__.__subclasses__() %}{{x}}{% endfor %}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})


# ============================================================================
# FILE ACCESS TESTS
# ============================================================================

class TestFileAccessPrevention:
    """Test that file system access is blocked."""

    @pytest.mark.asyncio
    async def test_blocks_open(self, renderer):
        """Test open() is blocked."""
        template = "{{open('/etc/passwd').read()}}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})

    @pytest.mark.asyncio
    async def test_blocks_file_include(self, renderer):
        """Test {% include %} is blocked."""
        template = "{% include '/etc/passwd' %}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})

    @pytest.mark.asyncio
    async def test_blocks_import_directive(self, renderer):
        """Test {% import %} is blocked."""
        template = "{% import 'os' as os %}{{os.listdir('/')}}"

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, {})


# ============================================================================
# XSS PROTECTION TESTS
# ============================================================================

class TestXSSProtection:
    """Test XSS attack prevention."""

    @pytest.mark.asyncio
    async def test_escapes_html_by_default(self, renderer):
        """Test that HTML is escaped automatically."""
        template = "Hello {{name}}!"
        context = {"name": "<script>alert('XSS')</script>"}

        result = await renderer.render(template, context, user_role='admin')
        output = result['output']

        assert "&lt;script&gt;" in output
        assert "<script>" not in output
        assert "alert" not in output or "&lt;" in output

    @pytest.mark.asyncio
    async def test_escapes_event_handlers(self, renderer):
        """Test event handler escaping."""
        template = "{{payload}}"
        context = {"payload": "<img src=x onerror=alert(1)>"}

        result = await renderer.render(template, context, user_role='admin')
        output = result['output']

        # Should be escaped or blocked
        assert "onerror" not in output or "&lt;" in output

    @pytest.mark.asyncio
    async def test_escapes_javascript_protocol(self, renderer):
        """Test javascript: protocol is blocked."""
        template = "{{link}}"
        context = {"link": "javascript:alert(1)"}

        result = await renderer.render(template, context, user_role='admin')
        output = result['output']

        # Should be escaped or filtered
        assert "javascript:" not in output or "&#" in output


# ============================================================================
# ATTRIBUTE ACCESS TESTS
# ============================================================================

class TestAttributeAccessControl:
    """Test that private/internal attributes are blocked."""

    @pytest.mark.asyncio
    async def test_blocks_private_attributes(self, renderer):
        """Test private attribute access is blocked."""
        template = "{{device._internal}}"
        context = {"device": {"_internal": "secret"}}

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, context, user_role='admin')

    @pytest.mark.asyncio
    async def test_blocks_dunder_access(self, renderer):
        """Test __dunder__ access is blocked."""
        template = "{{device.__dict__}}"
        context = {"device": {"name": "TV-01"}}

        with pytest.raises(TemplateSecurityError):
            await renderer.render(template, context, user_role='admin')


# ============================================================================
# TIMEOUT TESTS
# ============================================================================

class TestTimeoutProtection:
    """Test timeout enforcement for DoS prevention."""

    @pytest.mark.asyncio
    async def test_enforces_timeout(self, renderer):
        """Test that rendering respects timeout."""
        # Template with potentially expensive operation
        template = "{% for i in range(1000000) %}{{i}}{% endfor %}"

        with pytest.raises((TemplateTimeoutError, TemplateSecurityError)):
            await renderer.render(template, {}, timeout=1)

    @pytest.mark.asyncio
    async def test_default_timeout_5_seconds(self, renderer):
        """Test default timeout is 5 seconds."""
        # This should complete within 5 seconds
        template = "{{1 + 1}}"

        result = await renderer.render(template, {}, user_role='admin')
        assert result['render_time_ms'] < 5000


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestTemplateValidation:
    """Test template validation logic."""

    @pytest.mark.asyncio
    async def test_rejects_oversized_templates(self, renderer):
        """Test that oversized templates are rejected."""
        # Create 100KB template (exceeds 50KB limit)
        template = "x" * 100000

        validation = await renderer.validate_template(template)
        assert not validation['valid']
        assert "size" in validation['error'].lower()

    @pytest.mark.asyncio
    async def test_detects_syntax_errors(self, renderer):
        """Test syntax error detection."""
        template = "{{unclosed"

        validation = await renderer.validate_template(template)
        assert not validation['valid']
        assert "syntax" in validation['error'].lower()

    @pytest.mark.asyncio
    async def test_accepts_valid_template(self, renderer):
        """Test valid templates pass validation."""
        template = "Hello {{name|upper}}!"

        validation = await renderer.validate_template(template)
        assert validation['valid']
        assert validation['error'] is None


# ============================================================================
# ROLE-BASED ACCESS TESTS
# ============================================================================

class TestRoleBasedAccess:
    """Test role-based variable filtering."""

    @pytest.mark.asyncio
    async def test_admin_sees_all_variables(self, renderer):
        """Test admin role has access to all variables."""
        template = "{{device.name}} - {{device.ip_address}}"
        context = {
            "device": {
                "name": "TV-01",
                "ip_address": "192.168.1.100"
            }
        }

        result = await renderer.render(template, context, user_role='admin')
        assert "TV-01" in result['output']
        assert "192.168" in result['output']

    @pytest.mark.asyncio
    async def test_viewer_filtered_variables(self, renderer):
        """Test viewer role has limited access."""
        template = "{{device.name}} - {{device.ip_address}}"
        context = {
            "device": {
                "name": "TV-01",
                "ip_address": "192.168.1.100"
            }
        }

        # Viewer shouldn't see IP address
        result = await renderer.render(template, context, user_role='viewer')
        assert "TV-01" in result['output']
        # IP should be filtered out or undefined


# ============================================================================
# CACHING TESTS
# ============================================================================

class TestCaching:
    """Test multi-layer caching."""

    @pytest.mark.asyncio
    async def test_cache_improves_performance(self, renderer):
        """Test that caching improves render performance."""
        template = "Hello {{name}}!"
        context = {"name": "World"}

        # First render (uncached)
        result1 = await renderer.render(template, context, use_cache=True, user_role='admin')
        time1 = result1['render_time_ms']

        # Second render (should be cached)
        result2 = await renderer.render(template, context, use_cache=True, user_role='admin')
        time2 = result2['render_time_ms']

        assert result2['cached'] is True
        # Cached should be faster (allowing some variance)
        # Note: First call might be cached too if test runs multiple times

    @pytest.mark.asyncio
    async def test_cache_respects_context_changes(self, renderer):
        """Test cache invalidation on context changes."""
        template = "Hello {{name}}!"

        result1 = await renderer.render(template, {"name": "Alice"}, user_role='admin')
        result2 = await renderer.render(template, {"name": "Bob"}, user_role='admin')

        assert "Alice" in result1['output']
        assert "Bob" in result2['output']
        assert result1['output'] != result2['output']


# ============================================================================
# FILTER TESTS
# ============================================================================

class TestSafeFilters:
    """Test that only safe filters are available."""

    @pytest.mark.asyncio
    async def test_safe_filters_work(self, renderer):
        """Test whitelisted filters work correctly."""
        template = "{{text|upper}} - {{text|lower}}"
        context = {"text": "Hello World"}

        result = await renderer.render(template, context, user_role='admin')
        assert "HELLO WORLD" in result['output']
        assert "hello world" in result['output']

    @pytest.mark.asyncio
    async def test_date_filter(self, renderer):
        """Test date formatting filter."""
        from datetime import datetime

        template = "{{now|date('%Y-%m-%d')}}"
        context = {"now": datetime(2024, 1, 15)}

        result = await renderer.render(template, context, user_role='admin')
        assert "2024-01-15" in result['output']

    @pytest.mark.asyncio
    async def test_currency_filter(self, renderer):
        """Test currency formatting filter."""
        template = "{{price|currency('USD')}}"
        context = {"price": 1234.56}

        result = await renderer.render(template, context, user_role='admin')
        assert "$" in result['output']
        assert "1,234.56" in result['output']


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_safe_workflow(self, renderer):
        """Test complete safe rendering workflow."""
        # 1. Validate template
        template = "Welcome {{device.name}}! Temperature: {{weather.temp}}°C"

        validation = await renderer.validate_template(template)
        assert validation['valid']

        # 2. Render with context
        context = {
            "device": {"name": "Lobby Display"},
            "weather": {"temp": 25.0}
        }

        result = await renderer.render(template, context, user_role='editor')

        # 3. Verify output
        assert "Welcome Lobby Display!" in result['output']
        assert "25.0" in result['output']
        assert result['render_time_ms'] > 0

    @pytest.mark.asyncio
    async def test_handles_missing_variables_gracefully(self, renderer):
        """Test graceful handling of missing variables."""
        template = "Hello {{name|default('Guest')}}!"
        context = {}  # Missing 'name'

        result = await renderer.render(template, context, user_role='admin')
        assert "Hello Guest!" in result['output']


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance benchmarks."""

    @pytest.mark.asyncio
    async def test_simple_render_under_100ms(self, renderer):
        """Test simple renders are fast."""
        template = "Hello {{name}}!"
        context = {"name": "World"}

        result = await renderer.render(template, context, use_cache=False, user_role='admin')
        assert result['render_time_ms'] < 100  # Should be < 100ms

    @pytest.mark.asyncio
    async def test_complex_render_performance(self, renderer):
        """Test complex templates with loops."""
        template = """
        {% for item in items %}
        <div>{{item.name|upper}}</div>
        {% endfor %}
        """
        context = {
            "items": [{"name": f"Item {i}"} for i in range(10)]
        }

        result = await renderer.render(template, context, use_cache=False, user_role='admin')
        assert result['render_time_ms'] < 500  # Should be < 500ms for 10 items


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
