"""
MANTRA Document Generation System

Single Source of Truth → Multiple Document Outputs

Write decisions once, generate documentation for any audience:
- Developers → Technical Spec, API Spec, ADR
- Product Managers → PRD, Feature Spec
- Executives → Summary, Impact Report
- Security Team → Security Spec, Compliance Doc
- QA Team → Test Plan
- Customers → User Guide, FAQ
- Auditors → Audit Trail, Decision Log

SUPPORTED DOCUMENT TYPES (22 total):
- Planning: PRD, BRD, Feature Spec
- Design: Tech Spec, API Spec, DB Schema, UI Spec
- Security: Security Spec, Threat Model, Compliance Doc
- Quality: Test Plan, Performance Spec
- Operations: Deployment Guide, Runbook, Infra Spec
- User: User Manual, API Docs, FAQ
- Maintenance: ADR, Changelog, Migration Guide
- Executive: Exec Summary, Impact Report

USAGE:
    from core.docs import generate_document, DocumentType, DocumentConfig

    # Generate PRD
    prd = generate_document(
        DocumentType.PRD,
        decisions=my_decisions,
        config=DocumentConfig(
            doc_type=DocumentType.PRD,
            title="My Product PRD",
            company_name="Acme Corp"
        )
    )

    print(prd.raw_content)  # Markdown output
"""

from .doc_generator import (
    # Enums
    DocumentType,
    AudienceType,
    OutputFormat,
    # Metadata
    DocumentTypeMeta,
    DOCUMENT_TYPES,
    # Models
    DocumentSection,
    GeneratedDocument,
    DocumentConfig,
    # Generator
    DocumentGenerator,
    # Convenience
    get_document_meta,
    list_available_documents,
)

# Specialized Generators
from .tech_spec import TechSpecGenerator
from .api_spec import APISpecGenerator
from .security_spec import SecuritySpecGenerator
from .user_guide import UserGuideGenerator
from .exec_summary import ExecSummaryGenerator
from .generic import GenericGenerator

# New Specialized Generators
from .prd_generator import PRDGenerator
from .test_plan_generator import TestPlanGenerator
from .adr_generator import ADRGenerator


# ============================================================================
# ENHANCED generate_document FUNCTION
# ============================================================================

def generate_document(
    doc_type: DocumentType,
    decisions: list,
    config: DocumentConfig = None
) -> GeneratedDocument:
    """
    Generate a document of the specified type.

    This function automatically selects the appropriate generator
    based on document type.

    Args:
        doc_type: Type of document to generate
        decisions: List of decision dictionaries
        config: Optional configuration

    Returns:
        GeneratedDocument with rendered content
    """
    # Generator mapping - specialized generators for each type
    GENERATORS = {
        # Planning Phase
        DocumentType.PRD: PRDGenerator,
        DocumentType.FEATURE_SPEC: PRDGenerator,  # Similar structure

        # Design Phase
        DocumentType.TECH_SPEC: TechSpecGenerator,
        DocumentType.API_SPEC: APISpecGenerator,

        # Security Phase
        DocumentType.SECURITY_SPEC: SecuritySpecGenerator,
        DocumentType.THREAT_MODEL: SecuritySpecGenerator,

        # Quality Phase
        DocumentType.TEST_PLAN: TestPlanGenerator,

        # User Phase
        DocumentType.USER_MANUAL: UserGuideGenerator,

        # Maintenance Phase
        DocumentType.ADR: ADRGenerator,

        # Executive Phase
        DocumentType.EXEC_SUMMARY: ExecSummaryGenerator,
    }

    generator_class = GENERATORS.get(doc_type)

    if generator_class:
        generator = generator_class(decisions)
    else:
        # Use generic generator for types without specialized implementation
        generator = GenericGenerator(decisions, doc_type)

    return generator.generate(config)


__all__ = [
    # Enums
    "DocumentType",
    "AudienceType",
    "OutputFormat",

    # Metadata
    "DocumentTypeMeta",
    "DOCUMENT_TYPES",

    # Models
    "DocumentSection",
    "GeneratedDocument",
    "DocumentConfig",

    # Base Generator
    "DocumentGenerator",

    # Specialized Generators
    "TechSpecGenerator",
    "APISpecGenerator",
    "SecuritySpecGenerator",
    "UserGuideGenerator",
    "ExecSummaryGenerator",
    "GenericGenerator",

    # New Specialized Generators
    "PRDGenerator",
    "TestPlanGenerator",
    "ADRGenerator",

    # Convenience Functions
    "get_document_meta",
    "generate_document",
    "list_available_documents",
]
