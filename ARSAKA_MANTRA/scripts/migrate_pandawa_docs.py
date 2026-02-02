#!/usr/bin/env python3
"""
Migrate ARSAKA_PANDAWA docs to MANTRA decisions with Layer B content.

This script:
1. Reads all markdown files from PANDAWA/docs
2. Parses content and extracts metadata
3. Creates decisions via MANTRA API with full Layer B content
"""

import os
import re
import json
import requests
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# MANTRA API endpoint
API_BASE = "http://31.97.111.175:8002/api/v1"

# Domain mapping based on doc prefix
DOMAIN_MAPPING = {
    "CORE-ARCH": "ARCH",
    "CORE-SEC": "CTL",
    "CORE-STD": "CTL",
    "CORE-SPEC": "ARCH",
    "CORE-REF": "INT",
    "CORE-GUIDE": "EVO",
    "CORE-UI": "ARCH",
    "CORE-TEST": "CTL",
    "CORE-DECISION": "INT",
    "ACC-BIZ": "CTL",
    "ACC-REF": "ARCH",
    "ACC-SPEC": "ARCH",
    "PMS-REF": "ARCH",
    "PMS-SPEC": "ARCH",
    "INV-REF": "ARCH",
    "MULTI-SPEC": "ARCH",
    "EXTENSION-ARCH": "ARCH",
}

# Aspect mapping based on doc category
ASPECT_MAPPING = {
    # INT domain aspects
    "CORE-REF": "A01",      # Vision & Outcome
    "CORE-DECISION": "A02", # Principles & Beliefs

    # ARCH domain aspects
    "CORE-ARCH": "A05",     # Technical Architecture
    "CORE-SPEC": "A06",     # Domain Boundaries
    "CORE-UI": "A07",       # Integration Contracts
    "ACC-REF": "A05",
    "ACC-SPEC": "A06",
    "PMS-REF": "A05",
    "PMS-SPEC": "A06",
    "INV-REF": "A05",
    "MULTI-SPEC": "A08",    # Data & State Ownership
    "EXTENSION-ARCH": "A05",

    # CTL domain aspects
    "CORE-SEC": "A09",      # Security & Access
    "CORE-STD": "A10",      # Compliance & Audit
    "CORE-TEST": "A12",     # Quality Gates
    "ACC-BIZ": "A11",       # Risk Boundaries

    # EVO domain aspects
    "CORE-GUIDE": "A13",    # Change Protocols
}

@dataclass
class ParsedDoc:
    """Parsed document structure"""
    filename: str
    title: str
    doc_code: str
    category: str
    statement: str
    rationale: str
    detailed_content: str
    content_summary: str
    sections: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    tech_stack: list = field(default_factory=list)

def extract_doc_code(filename: str) -> tuple[str, str]:
    """Extract doc code and category from filename"""
    # e.g., CORE-ARCH-01-platform-vision.md -> (CORE-ARCH, CORE-ARCH-01)
    name = filename.replace(".md", "")
    parts = name.split("-")

    if len(parts) >= 3:
        # Find where the number starts
        for i, part in enumerate(parts):
            if part.isdigit():
                category = "-".join(parts[:i])
                doc_code = "-".join(parts[:i+1])
                return category, doc_code

    return name, name

def extract_title(content: str) -> str:
    """Extract title from first H1 heading"""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Untitled"

def extract_summary(content: str, max_words: int = 100) -> str:
    """Extract summary from first paragraph after title"""
    # Remove title
    content = re.sub(r'^#\s+.+\n', '', content, count=1)

    # Find first non-empty paragraph
    paragraphs = re.split(r'\n\n+', content.strip())
    for para in paragraphs:
        para = para.strip()
        # Skip headings and code blocks
        if para and not para.startswith('#') and not para.startswith('```'):
            # Clean markdown
            clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', para)  # links
            clean = re.sub(r'[*_`]', '', clean)  # formatting
            clean = re.sub(r'\s+', ' ', clean)  # whitespace

            words = clean.split()
            if len(words) > max_words:
                return ' '.join(words[:max_words]) + '...'
            return clean

    return "No summary available"

def extract_sections(content: str) -> list[dict]:
    """Extract sections from markdown headings"""
    sections = []
    current_section = None
    section_content = []
    order = 0

    lines = content.split('\n')

    for line in lines:
        # Check for H2 or H3 heading
        h2_match = re.match(r'^##\s+(.+)$', line)
        h3_match = re.match(r'^###\s+(.+)$', line)

        if h2_match or h3_match:
            # Save previous section
            if current_section:
                sections.append({
                    "section_id": f"sec-{order:02d}",
                    "title": current_section,
                    "section_type": categorize_section(current_section),
                    "content": '\n'.join(section_content).strip(),
                    "order": order
                })

            order += 1
            current_section = (h2_match or h3_match).group(1).strip()
            section_content = []
        else:
            section_content.append(line)

    # Save last section
    if current_section:
        sections.append({
            "section_id": f"sec-{order:02d}",
            "title": current_section,
            "section_type": categorize_section(current_section),
            "content": '\n'.join(section_content).strip(),
            "order": order
        })

    # Filter out empty sections
    sections = [s for s in sections if s['content'].strip()]

    return sections

def categorize_section(title: str) -> str:
    """Categorize section by title keywords"""
    title_lower = title.lower()

    if any(kw in title_lower for kw in ['overview', 'introduction', 'summary', 'about']):
        return 'OVERVIEW'
    elif any(kw in title_lower for kw in ['rule', 'requirement', 'must', 'constraint', 'policy']):
        return 'RULES'
    elif any(kw in title_lower for kw in ['example', 'sample', 'usage', 'demo']):
        return 'EXAMPLES'
    elif any(kw in title_lower for kw in ['structure', 'schema', 'model', 'format', 'field']):
        return 'STRUCTURE'
    elif any(kw in title_lower for kw in ['diagram', 'flow', 'sequence', 'architecture']):
        return 'DIAGRAM'
    elif any(kw in title_lower for kw in ['reference', 'link', 'resource', 'see also']):
        return 'REFERENCE'
    else:
        return 'OVERVIEW'

def extract_tech_stack(content: str) -> list[str]:
    """Extract technology mentions from content"""
    tech_keywords = [
        'Python', 'FastAPI', 'React', 'TypeScript', 'PostgreSQL', 'TimescaleDB',
        'Redis', 'RabbitMQ', 'Celery', 'Meilisearch', 'Centrifugo', 'Docker',
        'Kubernetes', 'Nomad', 'Consul', 'Traefik', 'Nginx', 'Cloudflare',
        'JWT', 'OAuth', 'REST', 'GraphQL', 'WebSocket', 'gRPC'
    ]

    found = []
    content_lower = content.lower()
    for tech in tech_keywords:
        if tech.lower() in content_lower:
            found.append(tech)

    return found[:5]  # Limit to 5

def extract_tags(filename: str, content: str) -> list[str]:
    """Extract tags based on filename and content"""
    tags = []

    # From filename prefix
    if 'ARCH' in filename:
        tags.append('architecture')
    if 'SEC' in filename:
        tags.append('security')
    if 'STD' in filename:
        tags.append('standard')
    if 'SPEC' in filename:
        tags.append('specification')
    if 'REF' in filename:
        tags.append('reference')
    if 'GUIDE' in filename:
        tags.append('guide')
    if 'UI' in filename:
        tags.append('ui-ux')
    if 'TEST' in filename:
        tags.append('testing')
    if 'ACC' in filename:
        tags.append('accounting')
    if 'PMS' in filename:
        tags.append('pms')
    if 'INV' in filename:
        tags.append('inventory')

    return tags[:4]  # Limit to 4

def parse_document(filepath: Path) -> ParsedDoc:
    """Parse a markdown document into structured data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = filepath.name
    category, doc_code = extract_doc_code(filename)
    title = extract_title(content)

    # Create statement from title
    statement = f"{title} - Architectural decision for ARSAKA_PANDAWA enterprise platform"
    if len(statement) > 200:
        statement = statement[:197] + "..."

    # Extract rationale from first section
    rationale = extract_summary(content, max_words=150)

    # Content summary (shorter)
    content_summary = extract_summary(content, max_words=50)

    # Sections
    sections = extract_sections(content)

    return ParsedDoc(
        filename=filename,
        title=title,
        doc_code=doc_code,
        category=category,
        statement=statement,
        rationale=rationale,
        detailed_content=content,
        content_summary=content_summary,
        sections=sections,
        tags=extract_tags(filename, content),
        tech_stack=extract_tech_stack(content),
    )

def create_decision(doc: ParsedDoc, seq: int) -> dict:
    """Create a decision via API"""

    # Determine domain and aspect
    domain_id = DOMAIN_MAPPING.get(doc.category, "ARCH")
    aspect_id = ASPECT_MAPPING.get(doc.category, "A05")

    # Create decision payload (wrapped per API requirements)
    payload = {
        "decision": {
            "domain_id": domain_id,
            "aspect_id": aspect_id,
            "statement": doc.statement,
            "rationale": doc.rationale,
            "constraints": [],
            "invariants": [
                f"Based on {doc.doc_code} specification",
                "Must be reviewed when underlying requirements change"
            ],
            "scope": "ORGANIZATION",
            "blast_radius": "HIGH" if "CORE" in doc.filename else "MEDIUM",
            "version": "1.0.0",
            "created_by": "pandawa-migration",
            "tags": doc.tags,
            "tech_stack": doc.tech_stack,
            # Layer B content
            "detailed_content": doc.detailed_content,
            "sections": doc.sections,
            "content_summary": doc.content_summary,
        },
        "stored_by": "pandawa-migration-script"
    }

    try:
        response = requests.post(f"{API_BASE}/decisions", json=payload, timeout=30)
        if response.status_code != 200 and response.status_code != 201:
            print(f"✗ Failed: {doc.filename}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            return None
        result = response.json()
        decision_id = result.get('decision_id', 'unknown')[:8]
        print(f"✓ [{seq:02d}] Created: {decision_id}... - {doc.title[:40]}")
        return result
    except Exception as e:
        print(f"✗ Failed: {doc.filename} - {e}")
        return None

def main():
    """Main migration function"""
    # Path to PANDAWA docs
    docs_path = Path("/mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PANDAWA/docs")

    if not docs_path.exists():
        # Try relative path for VPS
        docs_path = Path("../ARSAKA_PANDAWA/docs")

    if not docs_path.exists():
        print(f"Error: Docs path not found: {docs_path}")
        return

    # Get all markdown files
    md_files = sorted(docs_path.glob("*.md"))
    print(f"Found {len(md_files)} markdown files")

    # Parse all documents
    docs = []
    for filepath in md_files:
        try:
            doc = parse_document(filepath)
            docs.append(doc)
            print(f"Parsed: {doc.doc_code} - {doc.title[:40]}...")
        except Exception as e:
            print(f"Error parsing {filepath.name}: {e}")

    print(f"\nCreating {len(docs)} decisions...")

    # Create decisions via API
    success_count = 0
    for i, doc in enumerate(docs, 1):
        result = create_decision(doc, i)
        if result:
            success_count += 1
        time.sleep(0.1)  # Rate limiting

    print(f"\nSuccessfully created {success_count}/{len(docs)} decisions")

    print("\nMigration complete!")

if __name__ == "__main__":
    main()
