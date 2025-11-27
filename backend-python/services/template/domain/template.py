"""
Template Domain Entity
Pure business logic for template management
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import re


class Template:
    """Template entity - pure Python domain object"""

    VALID_TYPES = ["text", "image", "video", "html", "greeting"]
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    def __init__(
        self,
        name: str,
        template_type: str,
        content: str,
        organization_id: int,
        id: Optional[int] = None,
        description: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        preview_data: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_by_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.template_type = template_type
        self.content = content
        self.variables = variables or {}
        self.preview_data = preview_data or {}
        self.is_active = is_active
        self.organization_id = organization_id
        self.created_by_id = created_by_id
        self.created_at = created_at
        self.updated_at = updated_at

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Template name cannot be empty")

        if len(self.name) > 255:
            raise ValueError("Template name too long (max 255 characters)")

        if self.template_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid template type. Must be one of: {', '.join(self.VALID_TYPES)}")

        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Template content cannot be empty")

        if not self.organization_id:
            raise ValueError("Organization ID is required")

    def extract_variables(self) -> List[str]:
        """Extract variable names from template content"""
        matches = self.VARIABLE_PATTERN.findall(self.content)
        return list(set(matches))  # Return unique variable names

    def validate_syntax(self) -> tuple[bool, str]:
        """Validate template syntax"""
        try:
            # Check for unmatched braces
            open_braces = self.content.count('{{')
            close_braces = self.content.count('}}')

            if open_braces != close_braces:
                return False, "Unmatched template braces"

            # Check for valid variable names
            variables = self.extract_variables()
            for var in variables:
                if not var.isidentifier():
                    return False, f"Invalid variable name: {var}"

            return True, "Valid template syntax"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def render(self, data: Dict[str, Any]) -> str:
        """Render template with provided data"""
        rendered = self.content
        variables = self.extract_variables()

        # Check for missing variables
        missing_vars = [v for v in variables if v not in data]
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

        # Replace all variables
        for var_name, var_value in data.items():
            pattern = f'{{{{{var_name}}}}}'
            rendered = rendered.replace(pattern, str(var_value))

        return rendered

    def render_preview(self) -> Optional[str]:
        """Render template with preview data if available"""
        if not self.preview_data:
            return None

        try:
            return self.render(self.preview_data)
        except ValueError:
            return None

    def update_content(
        self,
        content: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        preview_data: Optional[Dict[str, Any]] = None,
    ):
        """Update template content with validation"""
        if content is not None:
            if not content or len(content.strip()) == 0:
                raise ValueError("Template content cannot be empty")
            self.content = content

        if variables is not None:
            self.variables = variables

        if preview_data is not None:
            self.preview_data = preview_data

        self.updated_at = datetime.now(timezone.utc)

    def activate(self):
        """Activate template"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate template"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def is_greeting_template(self) -> bool:
        """Check if this is a greeting template"""
        return self.template_type == "greeting"

    def is_text_template(self) -> bool:
        """Check if this is a text template"""
        return self.template_type == "text"

    def is_html_template(self) -> bool:
        """Check if this is an HTML template"""
        return self.template_type == "html"

    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}', type={self.template_type}, active={self.is_active})>"
