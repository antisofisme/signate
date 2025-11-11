"""
Render Template Use Case
Business logic for rendering templates with Jinja2
"""

import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jinja2 import Template as Jinja2Template, TemplateSyntaxError, UndefinedError

from services.template.dtos import (
    RenderTemplateRequest,
    RenderTemplateResponse,
    ValidateTemplateRequest,
    ValidateTemplateResponse,
    ExtractVariablesRequest,
    ExtractVariablesResponse
)
from services.template.repositories.template_repo import TemplateRepository


def render_template_use_case(
    template_id: int,
    organization_id: int,
    request: RenderTemplateRequest,
    db: Session
) -> RenderTemplateResponse:
    """
    Render template with data using Jinja2

    Business Rules:
    - Template must exist and belong to organization
    - All required variables must be provided
    """
    repo = TemplateRepository(db)

    # Get template
    template_obj = repo.get_template_by_id(template_id, organization_id)
    if not template_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )

    # Render using Jinja2
    try:
        template = Jinja2Template(template_obj.content)
        rendered = template.render(**request.data)

        return RenderTemplateResponse(
            rendered_content=rendered,
            template_id=template_obj.id,
            template_name=template_obj.name
        )
    except UndefinedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required variable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render template: {str(e)}"
        )


def validate_template_use_case(
    request: ValidateTemplateRequest,
    db: Session
) -> ValidateTemplateResponse:
    """
    Validate template syntax and render with sample data

    Returns validation result with extracted variables
    """
    try:
        # Parse template
        template = Jinja2Template(request.content)

        # Extract variables
        variables = extract_variables_from_content(request.content)

        # Try to render with provided data (if any)
        rendered_preview = None
        if request.variables:
            try:
                rendered_preview = template.render(**request.variables)
            except Exception as e:
                return ValidateTemplateResponse(
                    valid=False,
                    message=f"Template syntax is valid but rendering failed: {str(e)}",
                    extracted_variables=variables
                )

        return ValidateTemplateResponse(
            valid=True,
            message="Template is valid",
            extracted_variables=variables,
            rendered_preview=rendered_preview
        )

    except TemplateSyntaxError as e:
        return ValidateTemplateResponse(
            valid=False,
            message=f"Template syntax error: {str(e)}",
            extracted_variables=None
        )
    except Exception as e:
        return ValidateTemplateResponse(
            valid=False,
            message=f"Validation error: {str(e)}",
            extracted_variables=None
        )


def extract_variables_use_case(
    request: ExtractVariablesRequest,
    db: Session
) -> ExtractVariablesResponse:
    """
    Extract variable names from template content

    Returns list of unique variable names found in template
    """
    variables = extract_variables_from_content(request.content)

    return ExtractVariablesResponse(
        variables=variables,
        variable_count=len(variables)
    )


def extract_variables_from_content(content: str) -> List[str]:
    """
    Extract variable names from template content

    Finds all {{variable}} and {{ variable }} patterns
    """
    # Find all {{variable}} patterns (with optional spaces)
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    variables = re.findall(pattern, content)

    # Return unique variables
    return list(set(variables))
