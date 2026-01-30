"""
MANTRA Document Generator - Base System

Single Source of Truth → Multiple Document Outputs

Filters decisions by scope, tags, domain and transforms
into audience-appropriate documentation format.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class DocumentType(str, Enum):
    """Types of documents that can be generated."""
    # Planning Phase
    PRD = "PRD"                       # Product Requirements Document
    BRD = "BRD"                       # Business Requirements Document
    FEATURE_SPEC = "FEATURE_SPEC"     # Feature Specification

    # Design Phase
    TECH_SPEC = "TECH_SPEC"           # Technical Specification
    API_SPEC = "API_SPEC"             # API Specification
    DB_SCHEMA = "DB_SCHEMA"           # Database Schema / ERD
    UI_SPEC = "UI_SPEC"               # UI/UX Specification

    # Security Phase
    SECURITY_SPEC = "SECURITY_SPEC"   # Security Specification
    THREAT_MODEL = "THREAT_MODEL"     # Threat Model
    COMPLIANCE_DOC = "COMPLIANCE_DOC" # Compliance Documentation

    # Quality Phase
    TEST_PLAN = "TEST_PLAN"           # Test Plan
    PERF_SPEC = "PERF_SPEC"           # Performance Specification

    # Operations Phase
    DEPLOY_GUIDE = "DEPLOY_GUIDE"     # Deployment Guide
    RUNBOOK = "RUNBOOK"               # Operations Runbook
    INFRA_SPEC = "INFRA_SPEC"         # Infrastructure Specification

    # User Phase
    USER_MANUAL = "USER_MANUAL"       # User Manual
    API_DOCS = "API_DOCS"             # External API Documentation
    FAQ = "FAQ"                       # Frequently Asked Questions

    # Maintenance Phase
    ADR = "ADR"                       # Architecture Decision Records
    CHANGELOG = "CHANGELOG"           # Change Log
    MIGRATION_GUIDE = "MIGRATION_GUIDE"  # Migration Guide

    # Executive
    EXEC_SUMMARY = "EXEC_SUMMARY"     # Executive Summary
    IMPACT_REPORT = "IMPACT_REPORT"   # Impact Report


class AudienceType(str, Enum):
    """Target audience for the document."""
    DEVELOPER = "DEVELOPER"         # Technical, detailed
    PM = "PM"                       # Product-focused
    DESIGNER = "DESIGNER"           # UI/UX focused
    QA = "QA"                       # Testing focused
    DEVOPS = "DEVOPS"               # Operations focused
    SECURITY = "SECURITY"           # Security focused
    EXECUTIVE = "EXECUTIVE"         # High-level summary
    CUSTOMER = "CUSTOMER"           # End user, simplified
    EXTERNAL_DEV = "EXTERNAL_DEV"   # Third-party developers
    AUDITOR = "AUDITOR"             # Compliance/audit


class OutputFormat(str, Enum):
    """Output format for generated documents."""
    MARKDOWN = "MARKDOWN"           # .md file
    HTML = "HTML"                   # .html file
    PDF = "PDF"                     # .pdf file (via markdown)
    JSON = "JSON"                   # Structured JSON
    CONFLUENCE = "CONFLUENCE"       # Confluence wiki format
    NOTION = "NOTION"               # Notion format
    DOCX = "DOCX"                   # Word document
    RST = "RST"                     # reStructuredText


# ============================================================================
# DOCUMENT TYPE METADATA
# ============================================================================

@dataclass
class DocumentTypeMeta:
    """Metadata for a document type."""
    doc_type: DocumentType
    name: str
    description: str
    phase: str
    primary_audience: AudienceType
    secondary_audiences: List[AudienceType]

    # Filters for decisions
    domains: List[str]              # Filter by domain_id
    scopes: List[str]               # Filter by scope_path patterns
    tags: List[str]                 # Filter by tags

    # Content settings
    include_rationale: bool = True
    include_constraints: bool = True
    include_examples: bool = True
    simplify_language: bool = False

    # Output
    default_format: OutputFormat = OutputFormat.MARKDOWN


# Document type registry
DOCUMENT_TYPES: Dict[DocumentType, DocumentTypeMeta] = {
    DocumentType.PRD: DocumentTypeMeta(
        doc_type=DocumentType.PRD,
        name="Product Requirements Document",
        description="What to build - features, user stories, acceptance criteria",
        phase="Planning",
        primary_audience=AudienceType.PM,
        secondary_audiences=[AudienceType.DEVELOPER, AudienceType.DESIGNER],
        domains=["*"],
        scopes=["*"],
        tags=["feature", "requirement", "user-story"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.BRD: DocumentTypeMeta(
        doc_type=DocumentType.BRD,
        name="Business Requirements Document",
        description="Business goals, ROI, constraints, stakeholders",
        phase="Planning",
        primary_audience=AudienceType.EXECUTIVE,
        secondary_audiences=[AudienceType.PM],
        domains=["INT"],
        scopes=["*"],
        tags=["business", "roi", "stakeholder", "goal"],
        include_rationale=True,
        include_constraints=True,
        include_examples=False,
    ),

    DocumentType.TECH_SPEC: DocumentTypeMeta(
        doc_type=DocumentType.TECH_SPEC,
        name="Technical Specification",
        description="How to build - architecture, patterns, technical decisions",
        phase="Design",
        primary_audience=AudienceType.DEVELOPER,
        secondary_audiences=[AudienceType.DEVOPS],
        domains=["ARCH"],
        scopes=["be.*", "fe.*", "infra.*"],
        tags=["architecture", "pattern", "technical", "design"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.API_SPEC: DocumentTypeMeta(
        doc_type=DocumentType.API_SPEC,
        name="API Specification",
        description="Endpoints, request/response formats, authentication",
        phase="Design",
        primary_audience=AudienceType.DEVELOPER,
        secondary_audiences=[AudienceType.EXTERNAL_DEV],
        domains=["ARCH", "CTL"],
        scopes=["be.api.*", "api.*"],
        tags=["api", "endpoint", "rest", "graphql", "contract"],
        include_rationale=False,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.DB_SCHEMA: DocumentTypeMeta(
        doc_type=DocumentType.DB_SCHEMA,
        name="Database Schema / ERD",
        description="Data structure, relationships, migrations",
        phase="Design",
        primary_audience=AudienceType.DEVELOPER,
        secondary_audiences=[AudienceType.DEVOPS],
        domains=["ARCH"],
        scopes=["be.db.*", "db.*", "data.*"],
        tags=["database", "schema", "erd", "migration", "table"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.UI_SPEC: DocumentTypeMeta(
        doc_type=DocumentType.UI_SPEC,
        name="UI/UX Specification",
        description="Wireframes, components, design system, user flows",
        phase="Design",
        primary_audience=AudienceType.DESIGNER,
        secondary_audiences=[AudienceType.DEVELOPER],
        domains=["ARCH"],
        scopes=["fe.*", "ui.*", "design.*"],
        tags=["ui", "ux", "component", "design", "wireframe", "flow"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.SECURITY_SPEC: DocumentTypeMeta(
        doc_type=DocumentType.SECURITY_SPEC,
        name="Security Specification",
        description="Security requirements, controls, compliance",
        phase="Security",
        primary_audience=AudienceType.SECURITY,
        secondary_audiences=[AudienceType.DEVELOPER, AudienceType.AUDITOR],
        domains=["CTL"],
        scopes=["*"],
        tags=["security", "auth", "encryption", "compliance", "access"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.THREAT_MODEL: DocumentTypeMeta(
        doc_type=DocumentType.THREAT_MODEL,
        name="Threat Model",
        description="Attack vectors, risk assessment, mitigations",
        phase="Security",
        primary_audience=AudienceType.SECURITY,
        secondary_audiences=[AudienceType.DEVELOPER],
        domains=["CTL"],
        scopes=["*"],
        tags=["threat", "risk", "attack", "vulnerability", "mitigation"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.TEST_PLAN: DocumentTypeMeta(
        doc_type=DocumentType.TEST_PLAN,
        name="Test Plan",
        description="Test strategy, test cases, coverage requirements",
        phase="Quality",
        primary_audience=AudienceType.QA,
        secondary_audiences=[AudienceType.DEVELOPER],
        domains=["CTL"],
        scopes=["*.test.*", "test.*", "qa.*"],
        tags=["test", "testing", "qa", "coverage", "automation"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.PERF_SPEC: DocumentTypeMeta(
        doc_type=DocumentType.PERF_SPEC,
        name="Performance Specification",
        description="SLA, benchmarks, limits, optimization",
        phase="Quality",
        primary_audience=AudienceType.DEVOPS,
        secondary_audiences=[AudienceType.DEVELOPER],
        domains=["CTL", "ARCH"],
        scopes=["*"],
        tags=["performance", "sla", "benchmark", "optimization", "latency"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.DEPLOY_GUIDE: DocumentTypeMeta(
        doc_type=DocumentType.DEPLOY_GUIDE,
        name="Deployment Guide",
        description="How to deploy, infrastructure, environments",
        phase="Operations",
        primary_audience=AudienceType.DEVOPS,
        secondary_audiences=[AudienceType.DEVELOPER],
        domains=["ARCH", "CTL"],
        scopes=["ops.*", "infra.*", "deploy.*"],
        tags=["deploy", "deployment", "infrastructure", "environment"],
        include_rationale=False,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.RUNBOOK: DocumentTypeMeta(
        doc_type=DocumentType.RUNBOOK,
        name="Operations Runbook",
        description="Incident response, troubleshooting, maintenance",
        phase="Operations",
        primary_audience=AudienceType.DEVOPS,
        secondary_audiences=[],
        domains=["CTL"],
        scopes=["ops.*"],
        tags=["incident", "troubleshoot", "maintenance", "alert", "runbook"],
        include_rationale=False,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.USER_MANUAL: DocumentTypeMeta(
        doc_type=DocumentType.USER_MANUAL,
        name="User Manual",
        description="How to use the product - for end users",
        phase="User",
        primary_audience=AudienceType.CUSTOMER,
        secondary_audiences=[],
        domains=["*"],
        scopes=["*"],
        tags=["user", "guide", "how-to", "tutorial"],
        include_rationale=False,
        include_constraints=False,
        include_examples=True,
        simplify_language=True,
    ),

    DocumentType.API_DOCS: DocumentTypeMeta(
        doc_type=DocumentType.API_DOCS,
        name="External API Documentation",
        description="API documentation for third-party developers",
        phase="User",
        primary_audience=AudienceType.EXTERNAL_DEV,
        secondary_audiences=[],
        domains=["ARCH"],
        scopes=["be.api.*", "api.*"],
        tags=["api", "integration", "sdk", "documentation"],
        include_rationale=False,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.ADR: DocumentTypeMeta(
        doc_type=DocumentType.ADR,
        name="Architecture Decision Records",
        description="All architecture decisions with full rationale",
        phase="Maintenance",
        primary_audience=AudienceType.DEVELOPER,
        secondary_audiences=[AudienceType.PM],
        domains=["ARCH"],
        scopes=["*"],
        tags=["*"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.CHANGELOG: DocumentTypeMeta(
        doc_type=DocumentType.CHANGELOG,
        name="Changelog",
        description="Version history, what changed, breaking changes",
        phase="Maintenance",
        primary_audience=AudienceType.DEVELOPER,
        secondary_audiences=[AudienceType.PM, AudienceType.CUSTOMER],
        domains=["EVO"],
        scopes=["*"],
        tags=["version", "change", "release", "breaking"],
        include_rationale=False,
        include_constraints=False,
        include_examples=False,
    ),

    DocumentType.MIGRATION_GUIDE: DocumentTypeMeta(
        doc_type=DocumentType.MIGRATION_GUIDE,
        name="Migration Guide",
        description="How to upgrade, breaking changes, migration steps",
        phase="Maintenance",
        primary_audience=AudienceType.DEVELOPER,
        secondary_audiences=[AudienceType.DEVOPS],
        domains=["EVO"],
        scopes=["*"],
        tags=["migration", "upgrade", "breaking", "deprecation"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.EXEC_SUMMARY: DocumentTypeMeta(
        doc_type=DocumentType.EXEC_SUMMARY,
        name="Executive Summary",
        description="High-level overview for executives and stakeholders",
        phase="Executive",
        primary_audience=AudienceType.EXECUTIVE,
        secondary_audiences=[AudienceType.PM],
        domains=["*"],
        scopes=["*"],
        tags=["*"],
        include_rationale=False,
        include_constraints=False,
        include_examples=False,
        simplify_language=True,
    ),

    # =========================================================================
    # ADDITIONAL DOCUMENT TYPES (complete coverage)
    # =========================================================================

    DocumentType.FEATURE_SPEC: DocumentTypeMeta(
        doc_type=DocumentType.FEATURE_SPEC,
        name="Feature Specification",
        description="Detailed feature requirements with acceptance criteria",
        phase="Planning",
        primary_audience=AudienceType.PM,
        secondary_audiences=[AudienceType.DEVELOPER, AudienceType.DESIGNER],
        domains=["*"],
        scopes=["*"],
        tags=["feature", "requirement", "acceptance", "user-story", "epic"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.COMPLIANCE_DOC: DocumentTypeMeta(
        doc_type=DocumentType.COMPLIANCE_DOC,
        name="Compliance Documentation",
        description="Regulatory compliance, audit requirements, certifications",
        phase="Security",
        primary_audience=AudienceType.AUDITOR,
        secondary_audiences=[AudienceType.SECURITY, AudienceType.EXECUTIVE],
        domains=["CTL"],
        scopes=["*"],
        tags=["compliance", "audit", "gdpr", "hipaa", "soc2", "iso", "regulation"],
        include_rationale=True,
        include_constraints=True,
        include_examples=False,
    ),

    DocumentType.FAQ: DocumentTypeMeta(
        doc_type=DocumentType.FAQ,
        name="Frequently Asked Questions",
        description="Common questions and answers for users",
        phase="User",
        primary_audience=AudienceType.CUSTOMER,
        secondary_audiences=[AudienceType.EXTERNAL_DEV],
        domains=["*"],
        scopes=["*"],
        tags=["faq", "question", "answer", "help", "support"],
        include_rationale=True,
        include_constraints=False,
        include_examples=True,
        simplify_language=True,
    ),

    DocumentType.INFRA_SPEC: DocumentTypeMeta(
        doc_type=DocumentType.INFRA_SPEC,
        name="Infrastructure Specification",
        description="Cloud infrastructure, networking, scaling requirements",
        phase="Operations",
        primary_audience=AudienceType.DEVOPS,
        secondary_audiences=[AudienceType.DEVELOPER],
        domains=["ARCH", "CTL"],
        scopes=["infra.*", "ops.*", "cloud.*"],
        tags=["infrastructure", "cloud", "aws", "kubernetes", "network", "scaling"],
        include_rationale=True,
        include_constraints=True,
        include_examples=True,
    ),

    DocumentType.IMPACT_REPORT: DocumentTypeMeta(
        doc_type=DocumentType.IMPACT_REPORT,
        name="Impact Report",
        description="Business and technical impact analysis of decisions",
        phase="Executive",
        primary_audience=AudienceType.EXECUTIVE,
        secondary_audiences=[AudienceType.PM, AudienceType.DEVELOPER],
        domains=["*"],
        scopes=["*"],
        tags=["impact", "analysis", "risk", "benefit", "cost"],
        include_rationale=True,
        include_constraints=False,
        include_examples=False,
        simplify_language=True,
    ),
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DocumentSection:
    """A section within a generated document."""
    id: str
    title: str
    content: str
    level: int = 1  # Heading level (1-6)
    decision_ids: List[str] = field(default_factory=list)
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedDocument:
    """A generated document."""
    doc_id: str
    doc_type: DocumentType
    title: str
    version: str

    # Content
    sections: List[DocumentSection]
    table_of_contents: List[Dict[str, Any]]

    # Metadata
    generated_at: datetime
    generated_by: str
    source_decisions: List[str]  # Decision IDs used

    # Stats
    word_count: int
    section_count: int
    decision_count: int

    # Output
    output_format: OutputFormat
    raw_content: str  # Final rendered content

    def to_markdown(self) -> str:
        """Get markdown representation."""
        return self.raw_content if self.output_format == OutputFormat.MARKDOWN else ""

    def to_html(self) -> str:
        """Get HTML representation."""
        if self.output_format == OutputFormat.HTML:
            return self.raw_content
        # Convert markdown to HTML
        import re
        html = self.raw_content
        # Basic markdown to HTML conversion
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'\n\n', r'</p><p>', html)
        return f"<html><body><p>{html}</p></body></html>"


@dataclass
class DocumentConfig:
    """Configuration for document generation."""
    doc_type: DocumentType
    title: Optional[str] = None
    version: str = "1.0.0"
    output_format: OutputFormat = OutputFormat.MARKDOWN

    # Filters (override defaults)
    scope_filter: Optional[str] = None
    tag_filter: Optional[List[str]] = None
    domain_filter: Optional[str] = None

    # Content options
    include_toc: bool = True
    include_metadata: bool = True
    include_decision_refs: bool = True
    max_decisions: Optional[int] = None

    # Styling
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    custom_header: Optional[str] = None
    custom_footer: Optional[str] = None


# ============================================================================
# BASE GENERATOR
# ============================================================================

class DocumentGenerator(ABC):
    """
    Base class for document generators.

    Subclasses implement specific document type generation.
    """

    def __init__(self, decisions: List[Dict[str, Any]]):
        """
        Initialize generator with decisions.

        Args:
            decisions: List of decision dictionaries
        """
        self.decisions = decisions
        self._filtered: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def doc_type(self) -> DocumentType:
        """Document type this generator produces."""
        pass

    @property
    def meta(self) -> DocumentTypeMeta:
        """Get metadata for this document type."""
        return DOCUMENT_TYPES[self.doc_type]

    def filter_decisions(self, config: DocumentConfig) -> List[Dict[str, Any]]:
        """
        Filter decisions based on document type and config.

        Returns decisions relevant to this document type.
        """
        meta = self.meta
        filtered = []

        for dec in self.decisions:
            # Domain filter
            if meta.domains != ["*"]:
                dec_domain = dec.get("domain_id", "")
                if dec_domain not in meta.domains:
                    continue

            # Custom domain filter from config
            if config.domain_filter:
                if dec.get("domain_id") != config.domain_filter:
                    continue

            # Scope filter
            dec_scope = dec.get("scope_path", "*")
            if meta.scopes != ["*"]:
                scope_match = False
                for pattern in meta.scopes:
                    if self._scope_matches(dec_scope, pattern):
                        scope_match = True
                        break
                if not scope_match:
                    continue

            # Custom scope filter from config
            if config.scope_filter:
                if not self._scope_matches(dec_scope, config.scope_filter):
                    continue

            # Tag filter
            dec_tags = set(t.lower() for t in dec.get("tags", []))
            if meta.tags != ["*"]:
                meta_tags = set(t.lower() for t in meta.tags)
                if not (dec_tags & meta_tags):
                    continue

            # Custom tag filter from config
            if config.tag_filter:
                filter_tags = set(t.lower() for t in config.tag_filter)
                if not (dec_tags & filter_tags):
                    continue

            filtered.append(dec)

        # Apply max limit
        if config.max_decisions:
            filtered = filtered[:config.max_decisions]

        self._filtered = filtered
        return filtered

    def _scope_matches(self, dec_scope: str, pattern: str) -> bool:
        """Check if decision scope matches pattern."""
        if pattern == "*" or dec_scope == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return dec_scope.startswith(prefix)
        return dec_scope == pattern or dec_scope.startswith(pattern + ".")

    @abstractmethod
    def generate_sections(self, decisions: List[Dict[str, Any]], config: DocumentConfig) -> List[DocumentSection]:
        """
        Generate document sections from filtered decisions.

        Override in subclasses for specific document structure.
        """
        pass

    def generate_toc(self, sections: List[DocumentSection]) -> List[Dict[str, Any]]:
        """Generate table of contents from sections."""
        toc = []
        for section in sections:
            toc.append({
                "id": section.id,
                "title": section.title,
                "level": section.level,
            })
            if section.subsections:
                for sub in section.subsections:
                    toc.append({
                        "id": sub.id,
                        "title": sub.title,
                        "level": sub.level,
                    })
        return toc

    def render_markdown(self, sections: List[DocumentSection], config: DocumentConfig) -> str:
        """Render sections to markdown."""
        lines = []

        # Header
        if config.custom_header:
            lines.append(config.custom_header)
            lines.append("")

        # Title
        title = config.title or self.meta.name
        lines.append(f"# {title}")
        lines.append("")

        # Metadata
        if config.include_metadata:
            lines.append(f"**Version:** {config.version}")
            lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
            lines.append(f"**Document Type:** {self.meta.name}")
            if config.company_name:
                lines.append(f"**Organization:** {config.company_name}")
            lines.append("")

        # Table of Contents
        if config.include_toc:
            lines.append("## Table of Contents")
            lines.append("")
            for section in sections:
                indent = "  " * (section.level - 1)
                lines.append(f"{indent}- [{section.title}](#{section.id})")
                for sub in section.subsections:
                    sub_indent = "  " * sub.level
                    lines.append(f"{sub_indent}- [{sub.title}](#{sub.id})")
            lines.append("")

        # Sections
        for section in sections:
            lines.append(self._render_section(section, config))

        # Footer
        if config.custom_footer:
            lines.append("")
            lines.append("---")
            lines.append(config.custom_footer)

        return "\n".join(lines)

    def _render_section(self, section: DocumentSection, config: DocumentConfig) -> str:
        """Render a single section to markdown."""
        lines = []

        # Heading
        heading_prefix = "#" * min(section.level + 1, 6)
        lines.append(f"{heading_prefix} {section.title}")
        lines.append("")

        # Content
        if section.content:
            lines.append(section.content)
            lines.append("")

        # Decision references
        if config.include_decision_refs and section.decision_ids:
            lines.append(f"*Based on decisions: {', '.join(section.decision_ids)}*")
            lines.append("")

        # Subsections
        for sub in section.subsections:
            lines.append(self._render_section(sub, config))

        return "\n".join(lines)

    def generate(self, config: Optional[DocumentConfig] = None) -> GeneratedDocument:
        """
        Generate the complete document.

        Args:
            config: Generation configuration (optional)

        Returns:
            GeneratedDocument with all content
        """
        if config is None:
            config = DocumentConfig(doc_type=self.doc_type)

        # Filter decisions
        filtered = self.filter_decisions(config)

        # Generate sections
        sections = self.generate_sections(filtered, config)

        # Generate TOC
        toc = self.generate_toc(sections)

        # Render to output format
        if config.output_format == OutputFormat.MARKDOWN:
            raw_content = self.render_markdown(sections, config)
        elif config.output_format == OutputFormat.HTML:
            md_content = self.render_markdown(sections, config)
            # Simple HTML conversion
            raw_content = f"<html><body>{md_content}</body></html>"
        elif config.output_format == OutputFormat.JSON:
            import json
            raw_content = json.dumps({
                "title": config.title or self.meta.name,
                "sections": [self._section_to_dict(s) for s in sections],
                "toc": toc,
            }, indent=2)
        else:
            raw_content = self.render_markdown(sections, config)

        # Calculate stats
        word_count = len(raw_content.split())
        section_count = len(sections) + sum(len(s.subsections) for s in sections)
        decision_ids = list(set(
            did for s in sections for did in s.decision_ids
        ))

        return GeneratedDocument(
            doc_id=str(uuid.uuid4()),
            doc_type=self.doc_type,
            title=config.title or self.meta.name,
            version=config.version,
            sections=sections,
            table_of_contents=toc,
            generated_at=datetime.now(timezone.utc),
            generated_by="MANTRA",
            source_decisions=decision_ids,
            word_count=word_count,
            section_count=section_count,
            decision_count=len(filtered),
            output_format=config.output_format,
            raw_content=raw_content,
        )

    def _section_to_dict(self, section: DocumentSection) -> Dict[str, Any]:
        """Convert section to dictionary for JSON output."""
        return {
            "id": section.id,
            "title": section.title,
            "content": section.content,
            "level": section.level,
            "decision_ids": section.decision_ids,
            "subsections": [self._section_to_dict(s) for s in section.subsections],
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_document_meta(doc_type: DocumentType) -> DocumentTypeMeta:
    """Get metadata for a document type."""
    return DOCUMENT_TYPES.get(doc_type)


def list_available_documents() -> List[Dict[str, Any]]:
    """List all available document types with metadata."""
    return [
        {
            "type": meta.doc_type.value,
            "name": meta.name,
            "description": meta.description,
            "phase": meta.phase,
            "audience": meta.primary_audience.value,
        }
        for meta in DOCUMENT_TYPES.values()
    ]


def generate_document(
    doc_type: DocumentType,
    decisions: List[Dict[str, Any]],
    config: Optional[DocumentConfig] = None
) -> GeneratedDocument:
    """
    Generate a document of the specified type.

    This is a convenience function that automatically selects
    the appropriate generator.
    """
    # Import specialized generators
    from .tech_spec import TechSpecGenerator
    from .api_spec import APISpecGenerator
    from .security_spec import SecuritySpecGenerator
    from .user_guide import UserGuideGenerator
    from .exec_summary import ExecSummaryGenerator

    # Generator mapping
    generators = {
        DocumentType.TECH_SPEC: TechSpecGenerator,
        DocumentType.API_SPEC: APISpecGenerator,
        DocumentType.SECURITY_SPEC: SecuritySpecGenerator,
        DocumentType.THREAT_MODEL: SecuritySpecGenerator,
        DocumentType.USER_MANUAL: UserGuideGenerator,
        DocumentType.EXEC_SUMMARY: ExecSummaryGenerator,
    }

    generator_class = generators.get(doc_type)
    if generator_class:
        generator = generator_class(decisions)
    else:
        # Use a generic generator for unimplemented types
        from .generic import GenericGenerator
        generator = GenericGenerator(decisions, doc_type)

    return generator.generate(config)


# ============================================================================
# EXPORTS
# ============================================================================

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
    # Generator
    "DocumentGenerator",
    # Functions
    "get_document_meta",
    "list_available_documents",
    "generate_document",
]
