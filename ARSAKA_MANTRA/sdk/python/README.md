# MANTRA SDK for Python

Python client library for ARSAKA_MANTRA Decision System.

## Installation

```bash
pip install mantra-sdk
```

Or from source:

```bash
cd ARSAKA_MANTRA/sdk/python
pip install -e .
```

## Quick Start

```python
from mantra_sdk import MantraClient, DecisionCreate, AuthorshipMetadata

# Initialize client
client = MantraClient("http://localhost:8000")

# List decisions
decisions = client.list_decisions(domain="INT", limit=10)
for d in decisions:
    print(f"{d.code}: {d.statement}")

# Get a specific decision
decision = client.get_decision("uuid-here")

# Context-aware retrieval
result = client.retrieve(
    query="authentication patterns",
    file_path="src/auth/login.ts",
    max_results=5,
)
for match in result.results:
    print(f"{match.decision_code} ({match.confidence:.0%}): {match.statement}")
```

## Proposing Decisions

Per MANTRA-LAW-006, the SDK can only **propose** decisions. All proposals require human approval.

```python
from mantra_sdk import DecisionCreate, AuthorshipMetadata
from datetime import datetime

# Create a proposal
proposal = DecisionCreate(
    code="MANTRA-ARCH-042",
    domain_id="ARCH",
    aspect_id="A05",
    statement="Use Repository pattern for data access",
    rationale="Provides abstraction and testability",
    scope=["backend/*"],
    tags=["pattern", "data-access"],
    authorship=AuthorshipMetadata(
        authored_by="john.doe@example.com",
        organization="Engineering",
    ),
)

# Submit proposal (requires human approval via dashboard)
result = client.propose_decision(proposal)
print(f"Proposal ID: {result['decision_id']}")
print(f"Status: {result['status']}")  # "pending_approval"
```

## Validation

```python
# Validate a decision before proposing
validation = client.validate_decision(proposal)
print(f"Status: {validation.status}")
for v in validation.violations:
    print(f"  [{v.severity}] {v.rule_id}: {v.message}")

# Full 3-gate validation
full_result = client.validate_full(proposal, include_ai=True)
print(f"Gate 1 (Deterministic): {'PASS' if full_result.gate1.passed else 'FAIL'}")
print(f"Gate 2 (AI): Confidence {full_result.gate2.confidence:.0%}")
print(f"Gate 3 (Human): {'Approved' if not full_result.gate3.pending else 'Pending'}")
```

## Document Generation

```python
from mantra_sdk import DocumentGenerateRequest

# List available document types
types = client.list_document_types()
for t in types:
    print(f"{t.type}: {t.name} ({t.phase})")

# Generate a PRD
doc = client.generate_document(DocumentGenerateRequest(
    doc_type="prd",
    title="My Project PRD",
    company_name="Acme Corp",
    domain_filter="INT",
    max_decisions=50,
))
print(f"Generated: {doc.title} ({doc.word_count} words)")
print(doc.content)
```

## Analytics

```python
# Get usage summary
summary = client.get_analytics_summary()
print(f"Tracked: {summary.total_decisions_tracked}")
print(f"Hot: {summary.hot_decisions_count}")
print(f"Stale: {summary.stale_decisions_count}")

# Track usage
client.track_event("decision-id", "view", {"source": "sdk"})

# Submit feedback
client.submit_feedback("decision-id", is_helpful=True, comment="Very clear")
```

## Error Handling

```python
from mantra_sdk import (
    MantraError,
    ValidationError,
    AuthorizationError,
    NotFoundError,
)

try:
    decision = client.get_decision("invalid-id")
except NotFoundError as e:
    print(f"Not found: {e.identifier}")
except AuthorizationError:
    print("Human authorization required")
except MantraError as e:
    print(f"Error [{e.code}]: {e.message}")
```

## Context Manager

```python
with MantraClient("http://localhost:8000") as client:
    decisions = client.list_decisions()
    # Connection automatically closed
```

## MANTRA Laws

This SDK enforces MANTRA constitutional laws:

- **LAW-001**: All decisions must be human-authored
- **LAW-006**: AI has ZERO authority for approval/creation/modification

The SDK can:
- Read decisions
- Validate decisions
- Propose decisions (requires human approval)
- Retrieve context-aware results
- Generate documentation
- Track usage analytics

The SDK cannot:
- Directly create approved decisions
- Modify existing decisions
- Approve proposals
