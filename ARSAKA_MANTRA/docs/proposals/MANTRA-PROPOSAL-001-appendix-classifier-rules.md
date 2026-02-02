# MANTRA-PROPOSAL-001 Appendix: AI Classifier Rules

**Companion to**: MANTRA-PROPOSAL-001-improved-taxonomy-design.md
**Purpose**: Detailed classification rules for AI assistants

---

## 1. Classification Algorithm

### 1.1 Primary Domain Selection

```python
def classify_domain(text: str) -> str:
    """
    Classify input text into one of 6 domains.
    Uses keyword matching + semantic analysis.
    """
    text_lower = text.lower()

    # Check domain indicators in priority order

    # 1. Resources & Economics (RES) - WHO/HOW MUCH
    if any(kw in text_lower for kw in [
        "team", "owner", "responsible", "accountable",
        "hire", "staff", "headcount", "skill", "competency",
        "budget", "cost", "spend", "money", "invest", "roi",
        "capacity", "resource", "memory", "cpu", "instance", "quota"
    ]):
        if not is_structure_context(text):  # Not architecture
            return "RES"

    # 2. Quality, Timing & Metrics (QTM) - HOW WELL/WHEN
    if any(kw in text_lower for kw in [
        "latency", "throughput", "response time", "performance",
        "quality", "coverage", "test", "acceptance criteria",
        "sla", "uptime", "availability", "reliability", "99.",
        "deadline", "schedule", "milestone", "timeline", "q1", "q2", "q3", "q4"
    ]):
        if not is_risk_context(text):  # Not risk assessment
            return "QTM"

    # 3. Intent & Direction (INT) - WHY/WHAT
    if any(kw in text_lower for kw in [
        "goal", "vision", "outcome", "achieve", "target",
        "problem", "issue", "pain", "challenge", "solve",
        "scope", "include", "exclude", "out of scope",
        "principle", "value", "prioritize", "trade-off"
    ]):
        return "INT"

    # 4. Architecture & Boundaries (ARCH) - HOW/WHERE
    if any(kw in text_lower for kw in [
        "domain", "bounded context", "aggregate", "entity",
        "service", "module", "component", "microservice",
        "database", "storage", "schema", "data owner",
        "api", "contract", "protocol", "interface", "rest", "grpc"
    ]):
        return "ARCH"

    # 5. Control, Policy & Risk (CTL) - CAN/MUST NOT
    if any(kw in text_lower for kw in [
        "policy", "rule", "must", "should", "must not", "forbidden",
        "approval", "authority", "permission", "sign-off",
        "security", "encrypt", "auth", "compliance", "gdpr",
        "risk", "impact", "failure", "fallback", "blast radius"
    ]):
        return "CTL"

    # 6. Execution & Evolution (EVO) - CHANGE SAFELY
    if any(kw in text_lower for kw in [
        "version", "evolve", "supersede", "lifecycle", "deprecate",
        "rollback", "exit", "revert", "migration", "undo",
        "environment", "promote", "deploy", "staging", "production",
        "drift", "consistency", "align", "enforce", "sync"
    ]):
        return "EVO"

    # Default: Requires human classification
    return "UNKNOWN"
```

### 1.2 Secondary Aspect Selection

```python
ASPECT_KEYWORDS = {
    # INT Domain
    "A01": ["vision", "goal", "outcome", "achieve", "success", "future", "long-term"],
    "A02": ["problem", "issue", "pain", "challenge", "struggle", "solve", "current"],
    "A03": ["scope", "include", "exclude", "boundary", "limit", "non-goal", "out of scope"],
    "A04": ["principle", "value", "belief", "trade-off", "prioritize", "philosophy"],

    # ARCH Domain
    "A05": ["domain", "bounded context", "aggregate", "entity", "business", "ubiquitous"],
    "A06": ["service", "module", "component", "microservice", "package", "layer"],
    "A07": ["data", "database", "storage", "schema", "ownership", "sovereignty", "gdpr"],
    "A08": ["api", "contract", "protocol", "interface", "integration", "communication"],

    # CTL Domain
    "A09": ["policy", "rule", "standard", "convention", "guideline", "must", "should"],
    "A10": ["approval", "authority", "permission", "role", "sign-off", "escalation"],
    "A11": ["security", "encrypt", "auth", "compliance", "audit", "regulation", "access"],
    "A12": ["risk", "impact", "failure", "fallback", "mitigation", "blast radius", "resilience"],

    # EVO Domain
    "A13": ["version", "evolve", "supersede", "lifecycle", "deprecate", "iteration"],
    "A14": ["rollback", "exit", "revert", "migration", "undo", "reversible"],
    "A15": ["environment", "promote", "deploy", "staging", "production", "gate", "release"],
    "A16": ["drift", "consistency", "align", "enforce", "sync", "diverge"],

    # RES Domain (NEW)
    "A17": ["team", "owner", "responsible", "accountable", "structure", "organization"],
    "A18": ["skill", "competency", "hire", "staff", "headcount", "expertise", "training"],
    "A19": ["budget", "cost", "spend", "money", "roi", "investment", "funding"],
    "A20": ["capacity", "resource", "memory", "cpu", "instance", "quota", "infrastructure"],

    # QTM Domain (NEW)
    "A21": ["latency", "throughput", "response", "speed", "performance", "benchmark"],
    "A22": ["quality", "coverage", "test", "acceptance", "criteria", "standard"],
    "A23": ["sla", "uptime", "availability", "reliability", "downtime", "mttr"],
    "A24": ["deadline", "schedule", "milestone", "timeline", "roadmap", "date", "quarter"],
}

def classify_aspect(text: str, domain: str) -> str:
    """Select aspect within domain based on keywords."""
    text_lower = text.lower()

    # Get valid aspects for domain
    domain_aspects = {
        "INT": ["A01", "A02", "A03", "A04"],
        "ARCH": ["A05", "A06", "A07", "A08"],
        "CTL": ["A09", "A10", "A11", "A12"],
        "EVO": ["A13", "A14", "A15", "A16"],
        "RES": ["A17", "A18", "A19", "A20"],
        "QTM": ["A21", "A22", "A23", "A24"],
    }

    valid_aspects = domain_aspects.get(domain, [])

    # Score each aspect
    scores = {}
    for aspect in valid_aspects:
        keywords = ASPECT_KEYWORDS.get(aspect, [])
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[aspect] = score

    # Return highest scoring aspect
    best_aspect = max(scores, key=scores.get)
    return best_aspect if scores[best_aspect] > 0 else valid_aspects[0]
```

---

## 2. Disambiguation Rules

### 2.1 RES vs ARCH Disambiguation

**Scenario**: "Team Alpha owns the Auth service"

| Signal | Points to |
|--------|-----------|
| Focus on team structure | RES/A17 |
| Focus on service responsibility | ARCH/A05 |

**Rule**: If the decision is about WHO (people/team), use RES. If about WHAT (service structure), use ARCH.

### 2.2 QTM vs CTL Disambiguation

**Scenario**: "API latency must be under 200ms"

| Signal | Points to |
|--------|-----------|
| Defines target metric | QTM/A21 |
| Defines rule/policy | CTL/A09 |
| Defines risk tolerance | CTL/A12 |

**Rule**: If there's a specific numeric target, use QTM. If it's a general rule without target, use CTL.

### 2.3 QTM vs INT Disambiguation

**Scenario**: "We launch Q3 2025"

| Signal | Points to |
|--------|-----------|
| Specific date/deadline | QTM/A24 |
| Long-term vision | INT/A01 |

**Rule**: Specific dates/quarters are QTM/A24. General future state without dates is INT/A01.

### 2.4 RES vs CTL Disambiguation

**Scenario**: "Budget approval requires CFO sign-off"

| Signal | Points to |
|--------|-----------|
| About budget amount | RES/A19 |
| About approval process | CTL/A10 |

**Rule**: The budget constraint is RES. The approval process is CTL. May need two decisions.

---

## 3. Compound Decision Splitting

### 3.1 Detection Rules

A decision should be split if it contains:
1. Multiple distinct concerns (different domains)
2. AND/OR conjunctions between independent statements
3. Multiple targets or metrics

### 3.2 Split Examples

**Input**: "Team Alpha owns Auth service and must maintain 99.9% uptime"

**Split**:
1. RES/A17: "Team Alpha is accountable for the Auth service"
2. QTM/A23: "Auth service must maintain 99.9% uptime"

**Input**: "API must be REST with JSON and latency under 100ms"

**Split**:
1. ARCH/A08: "API must use REST protocol with JSON format"
2. QTM/A21: "API latency must be under 100ms"

**Input**: "Hire 2 senior engineers by Q2 for the migration project"

**Split**:
1. RES/A18: "Migration project requires 2 senior engineers"
2. QTM/A24: "Hiring must complete by Q2"

---

## 4. Confidence Scoring

### 4.1 Confidence Levels

| Score | Meaning | Action |
|-------|---------|--------|
| 0.9+ | Very confident | Auto-classify |
| 0.7-0.9 | Confident | Auto-classify with review option |
| 0.5-0.7 | Borderline | Request confirmation |
| < 0.5 | Low confidence | Human classification required |

### 4.2 Confidence Factors

```python
def calculate_confidence(text: str, domain: str, aspect: str) -> float:
    """Calculate classification confidence."""
    base_score = 0.5

    # Factor 1: Keyword match strength (+0.3 max)
    keyword_score = count_matching_keywords(text, domain, aspect) / 10
    base_score += min(0.3, keyword_score)

    # Factor 2: Single domain indicator (+0.2)
    if has_only_one_domain_signal(text):
        base_score += 0.2

    # Factor 3: No ambiguous signals (+0.1)
    if not has_cross_domain_keywords(text):
        base_score += 0.1

    # Factor 4: Clear aspect match (+0.1)
    if has_clear_aspect_signal(text, aspect):
        base_score += 0.1

    return min(1.0, base_score)
```

---

## 5. Training Examples

### 5.1 RES Domain Examples (NEW)

| Input | Classification | Confidence |
|-------|----------------|------------|
| "Platform team handles infrastructure" | RES/A17 | 0.95 |
| "Need 3 more developers for Q2" | RES/A18 | 0.90 |
| "Cloud budget capped at $100K/month" | RES/A19 | 0.95 |
| "Database needs 64GB RAM minimum" | RES/A20 | 0.85 |
| "DevOps team owns CI/CD pipeline" | RES/A17 | 0.90 |
| "Require AWS Solutions Architect certified" | RES/A18 | 0.85 |
| "No new hires until Series B" | RES/A19 | 0.75 |
| "Reserve 100 ECS tasks for peak" | RES/A20 | 0.85 |

### 5.2 QTM Domain Examples (NEW)

| Input | Classification | Confidence |
|-------|----------------|------------|
| "P95 latency under 50ms" | QTM/A21 | 0.95 |
| "80% code coverage required" | QTM/A22 | 0.90 |
| "99.95% availability SLA" | QTM/A23 | 0.95 |
| "MVP by September 30" | QTM/A24 | 0.90 |
| "Throughput minimum 10K RPS" | QTM/A21 | 0.90 |
| "All code must pass SonarQube gates" | QTM/A22 | 0.85 |
| "MTTR under 4 hours" | QTM/A23 | 0.85 |
| "Feature freeze July 15" | QTM/A24 | 0.90 |

### 5.3 Disambiguation Examples

| Input | Correct | Why Not Alternative |
|-------|---------|---------------------|
| "Team X maintains 99.9% uptime" | SPLIT: RES/A17 + QTM/A23 | Compound decision |
| "Performance must not regress" | CTL/A09 | No specific metric (rule) |
| "Latency budget: 200ms" | QTM/A21 | Has specific metric |
| "Junior devs cannot deploy to prod" | CTL/A10 | About authority, not skills |
| "Hiring freeze until profit" | RES/A19 | About budget constraint |
| "Q2 roadmap includes auth" | QTM/A24 | Timeline decision |
| "Vision: best auth by 2026" | INT/A01 | Future state, no specific date |

---

## 6. Implementation Prompt Template

```
You are a decision classifier for MANTRA (Decision Matrix System).

TAXONOMY (6 Domains × 4 Aspects = 24 Categories):

INT (Intent & Direction) - WHY/WHAT
├─ A01: Vision & Outcome - Long-term goals, success criteria
├─ A02: Problem Statement - Pain points, challenges
├─ A03: Scope & Non-Goals - Boundaries, exclusions
└─ A04: Principles & Values - Trade-offs, guiding beliefs

ARCH (Architecture & Boundaries) - HOW/WHERE
├─ A05: Domain & Bounded Context - Business domains, DDD
├─ A06: Service & Module Boundary - Components, microservices
├─ A07: Data Ownership & Sovereignty - Storage, GDPR
└─ A08: Integration & Contract Model - APIs, protocols

CTL (Control, Policy & Risk) - CAN/MUST NOT
├─ A09: Policy & Rules - Standards, conventions
├─ A10: Approval & Authority Model - Permissions, sign-off
├─ A11: Security & Compliance Posture - Auth, encryption
└─ A12: Risk & Blast Radius - Impact, failure handling

EVO (Execution & Evolution) - CHANGE SAFELY
├─ A13: Decision Lifecycle - Versioning, supersedes
├─ A14: Reversibility & Exit Strategy - Rollback, migration
├─ A15: Environment & Promotion Rules - Deploy gates
└─ A16: Anti-Drift & Consistency - Enforcement, sync

RES (Resources & Economics) - WHO/HOW MUCH
├─ A17: Team & Ownership - Team structure, responsibility
├─ A18: Skills & Capacity - Competencies, staffing
├─ A19: Budget & Cost - Financial constraints, ROI
└─ A20: Infrastructure Quota - Hardware, cloud resources

QTM (Quality, Timing & Metrics) - HOW WELL/WHEN
├─ A21: Performance Targets - Latency, throughput
├─ A22: Quality Standards - Coverage, acceptance criteria
├─ A23: SLA & Availability - Uptime, reliability
└─ A24: Schedule & Milestones - Deadlines, timelines

TASK: Classify the decision into exactly ONE domain and ONE aspect.

INPUT:
Statement: "{statement}"
Rationale: "{rationale}"

RULES:
1. Match PRIMARY intent, not secondary aspects
2. If compound (multiple concerns), respond with "SPLIT_REQUIRED"
3. Confidence < 0.5 → respond with "HUMAN_REQUIRED"

OUTPUT FORMAT (JSON only):
{"domain_id": "INT|ARCH|CTL|EVO|RES|QTM", "aspect_id": "A01-A24", "confidence": 0.0-1.0}
```

---

## 7. Validation Rules

### 7.1 Domain-Aspect Compatibility

```python
VALID_COMBINATIONS = {
    "INT": {"A01", "A02", "A03", "A04"},
    "ARCH": {"A05", "A06", "A07", "A08"},
    "CTL": {"A09", "A10", "A11", "A12"},
    "EVO": {"A13", "A14", "A15", "A16"},
    "RES": {"A17", "A18", "A19", "A20"},
    "QTM": {"A21", "A22", "A23", "A24"},
}

def validate_classification(domain: str, aspect: str) -> tuple[bool, str]:
    """Validate domain-aspect combination."""
    if domain not in VALID_COMBINATIONS:
        return False, f"Invalid domain: {domain}"

    if aspect not in VALID_COMBINATIONS[domain]:
        return False, f"Aspect {aspect} invalid for domain {domain}"

    return True, None
```

### 7.2 Decision Code Format

```
Format: {DOMAIN}-{ASPECT}-{SEQ:03d}-v{VERSION}

Examples:
- INT-A01-001-v1.0.0  (First vision decision)
- RES-A17-003-v1.0.0  (Third team ownership decision)
- QTM-A24-001-v2.0.0  (First schedule decision, version 2)
```

---

**END OF APPENDIX**
