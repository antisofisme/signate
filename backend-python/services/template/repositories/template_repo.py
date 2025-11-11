"""
Template Repository
Data access layer for template operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from services.template.repositories.models import Template
from services.template.dtos import CreateTemplateRequest, UpdateTemplateRequest


class TemplateRepository:
    """Repository for template data access"""

    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        organization_id: int,
        user_id: int,
        request: CreateTemplateRequest
    ) -> Template:
        """Create a new template"""
        template = Template(
            organization_id=organization_id,
            name=request.name,
            description=request.description,
            template_type=request.template_type,
            content=request.content,
            variables=request.variables,
            preview_data=request.preview_data,
            is_active=request.is_active,
            created_by=user_id
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template_by_id(
        self,
        template_id: int,
        organization_id: int
    ) -> Optional[Template]:
        """Get template by ID (scoped to organization)"""
        return self.db.query(Template).filter(
            and_(
                Template.id == template_id,
                Template.organization_id == organization_id
            )
        ).first()

    def get_templates(
        self,
        organization_id: int,
        template_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Template], int]:
        """Get templates with optional filters"""
        query = self.db.query(Template).filter(
            Template.organization_id == organization_id
        )

        if template_type:
            query = query.filter(Template.template_type == template_type)
        if is_active is not None:
            query = query.filter(Template.is_active == is_active)

        total = query.count()
        templates = query.order_by(Template.created_at.desc()).offset(skip).limit(limit).all()

        return templates, total

    def update_template(
        self,
        template_id: int,
        organization_id: int,
        request: UpdateTemplateRequest
    ) -> Optional[Template]:
        """Update template"""
        template = self.get_template_by_id(template_id, organization_id)
        if not template:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(
        self,
        template_id: int,
        organization_id: int
    ) -> bool:
        """Delete template"""
        template = self.get_template_by_id(template_id, organization_id)
        if not template:
            return False

        self.db.delete(template)
        self.db.commit()
        return True

    def check_template_name_exists(
        self,
        organization_id: int,
        name: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """Check if template name already exists in organization"""
        query = self.db.query(Template).filter(
            and_(
                Template.organization_id == organization_id,
                Template.name == name
            )
        )

        if exclude_id:
            query = query.filter(Template.id != exclude_id)

        return query.first() is not None

    def get_template_by_name(
        self,
        organization_id: int,
        name: str
    ) -> Optional[Template]:
        """Get template by name"""
        return self.db.query(Template).filter(
            and_(
                Template.organization_id == organization_id,
                Template.name == name
            )
        ).first()
