# MANTRA Validator Enhancement Specification

**Status**: PROPOSED
**Version**: 2.0.0
**Date**: 2026-01-26

---

## 1. Problem Statement

Current validator hanya mengecek struktur (schema validation) tanpa memberikan nilai nyata:
- No duplicate detection → decisions bisa redundant
- No conflict detection → contradicting decisions bisa coexist
- No quality scoring → incomplete/vague decisions pass
- No classification guidance → users salah pilih group/feature
- No semantic validation → nonsense text passes validation

**Result**: Decision Matrix menjadi "garbage dump" bukan knowledge base.

---

## 2. Enhanced Validation Architecture

### 2.1 Five-Phase Validation Flow

```
INPUT: DecisionCreate + AuthorshipMetadata
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: SCHEMA VALIDATION                              │
│ ─────────────────────────                               │
│ Rules: S-001 to S-022 (existing)                        │
│ Purpose: Structural conformance                         │
│ Output: VALID or INVALID                                │
│ Short-circuit: Yes (stop if invalid)                    │
└─────────────────────────────────────────────────────────┘
                │ if VALID
                ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: QUALITY SCORING (NEW)                          │
│ ───────────────────────────────                         │
│ Rules: Q-001 to Q-020                                   │
│ Purpose: Measure decision quality                       │
│ Output: Score (0-100) + Grade + Suggestions             │
│ Short-circuit: Yes if score < 30 (REJECT)               │
└─────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 3: CLASSIFICATION ANALYSIS (NEW)                  │
│ ───────────────────────────────────────                 │
│ Rules: C-001 to C-006                                   │
│ Purpose: Validate/recommend group+feature               │
│ Output: Recommendations + Confidence Scores             │
│ Short-circuit: No (advisory only)                       │
└─────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 4: CONSISTENCY CHECK (NEW)                        │
│ ─────────────────────────────────                       │
│ Rules: CON-001 to CON-010                               │
│ Purpose: Detect duplicates and conflicts                │
│ Output: Duplicates + Conflicts + Coherence Score        │
│ Short-circuit: Yes if EXACT duplicate or ERROR conflict │
└─────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 5: LAW COMPLIANCE (existing, enhanced)            │
│ ────────────────────────────────────────────            │
│ Rules: L-001 to L-011                                   │
│ Purpose: Constitutional law enforcement                 │
│ Output: COMPLIANT or REJECTED                           │
│ Short-circuit: Yes if rejected                          │
└─────────────────────────────────────────────────────────┘
                │
                ▼
        OUTPUT: EnhancedValidationResponse
```

---

## 3. Phase 2: Quality Scoring System

### 3.1 Quality Dimensions (100 points total)

#### A. Statement Quality (25 points)

| Rule | Check | Points | Implementation |
|------|-------|--------|----------------|
| Q-001 | Length (10-200 words) | 5 | Word count check |
| Q-002 | Contains action verb | 5 | Verb detection (must/should/will) |
| Q-003 | Specificity | 5 | Vague word penalty (something, stuff) |
| Q-004 | Technical terminology | 5 | Domain keyword presence |
| Q-005 | No ambiguity | 5 | Ambiguous phrase detection |

#### B. Rationale Quality (25 points)

| Rule | Check | Points | Implementation |
|------|-------|--------|----------------|
| Q-006 | Length (20-500 words) | 5 | Word count check |
| Q-007 | Explains "why" | 5 | Causal keyword presence |
| Q-008 | References context | 5 | Problem/context detection |
| Q-009 | Considers alternatives | 5 | Alternative mention detection |
| Q-010 | Coherent with statement | 5 | Semantic similarity check |

#### C. Constraint Quality (25 points)

| Rule | Check | Points | Implementation |
|------|-------|--------|----------------|
| Q-011 | Has constraints | 5 | Count >= 1 |
| Q-012 | Type diversity | 5 | Multiple constraint types |
| Q-013 | Actionable | 5 | Verb presence in constraints |
| Q-014 | Verifiable | 5 | Measurable terms |
| Q-015 | Non-contradicting | 5 | Constraint conflict check |

#### D. Metadata Quality (25 points)

| Rule | Check | Points | Implementation |
|------|-------|--------|----------------|
| Q-016 | Scope matches content | 5 | Scope keyword alignment |
| Q-017 | Blast radius justified | 5 | Impact keyword alignment |
| Q-018 | Tags relevant | 5 | Tag-content alignment |
| Q-019 | Relations defined | 5 | Relations count > 0 |
| Q-020 | Tech stack specified | 5 | Tech stack count > 0 |

### 3.2 Grading Thresholds

| Score | Grade | Action |
|-------|-------|--------|
| 90-100 | EXCELLENT | Ready for production |
| 70-89 | GOOD | Acceptable, minor suggestions |
| 50-69 | FAIR | Warning, needs improvement |
| 30-49 | POOR | Should not be stored |
| 0-29 | REJECT | Block storage |

### 3.3 Example Scoring

```
INPUT:
  Statement: "Use PostgreSQL for all persistent data storage"
  Rationale: "PostgreSQL provides ACID compliance, strong consistency..."
  Constraints: [REQUIREMENT: "All services must use PostgreSQL"]

SCORING:
  Statement:
    Q-001: 7 words (too short) → 3/5
    Q-002: "Use" is action verb → 5/5
    Q-003: Specific (PostgreSQL, persistent) → 5/5
    Q-004: Technical (PostgreSQL, data storage) → 5/5
    Q-005: No ambiguity → 5/5
    Subtotal: 23/25

  Rationale:
    Q-006: Appropriate length → 5/5
    Q-007: "provides" explains why → 5/5
    ... (continued)
    Subtotal: 22/25

  Overall: 85/100 → GOOD
```

---

## 4. Phase 3: Classification Analysis

### 4.1 Group Classification Keywords

```python
GROUP_KEYWORDS = {
    "INT": {
        "primary": ["goal", "objective", "vision", "mission", "purpose", "why"],
        "secondary": ["want", "aim", "target", "outcome", "intent"],
        "question_pattern": "WHY / WHAT"
    },
    "ARCH": {
        "primary": ["architecture", "service", "database", "api", "module", "component"],
        "secondary": ["layer", "boundary", "integration", "contract", "schema"],
        "question_pattern": "HOW / WHERE"
    },
    "CTL": {
        "primary": ["policy", "rule", "security", "compliance", "approval", "authority"],
        "secondary": ["must", "cannot", "forbidden", "required", "mandatory"],
        "question_pattern": "CAN / MUST NOT"
    },
    "EVO": {
        "primary": ["deploy", "release", "migrate", "upgrade", "rollback", "version"],
        "secondary": ["environment", "promotion", "lifecycle", "change", "evolution"],
        "question_pattern": "CHANGE SAFELY"
    }
}
```

### 4.2 Feature Classification Keywords

```python
FEATURE_KEYWORDS = {
    # INT Group
    "F01": ["vision", "outcome", "success", "measure", "kpi"],
    "F02": ["problem", "pain point", "challenge", "issue", "gap"],
    "F03": ["scope", "boundary", "in-scope", "out-of-scope", "non-goal"],
    "F04": ["principle", "value", "guideline", "philosophy", "standard"],

    # ARCH Group
    "F05": ["domain", "bounded context", "aggregate", "entity", "ddd"],
    "F06": ["service", "module", "microservice", "component", "layer"],
    "F07": ["data", "database", "storage", "ownership", "schema", "table"],
    "F08": ["integration", "api", "contract", "interface", "protocol"],

    # CTL Group
    "F09": ["policy", "rule", "regulation", "guideline", "procedure"],
    "F10": ["approval", "authority", "permission", "access", "rbac"],
    "F11": ["security", "compliance", "audit", "encryption", "authentication"],
    "F12": ["risk", "blast radius", "impact", "mitigation", "fallback"],

    # EVO Group
    "F13": ["lifecycle", "status", "phase", "stage", "maturity"],
    "F14": ["reversibility", "rollback", "exit", "undo", "recovery"],
    "F15": ["environment", "promotion", "staging", "production", "dev"],
    "F16": ["drift", "consistency", "sync", "reconciliation", "alignment"]
}
```

### 4.3 Classification Algorithm

```python
def classify_decision(statement: str, rationale: str) -> ClassificationResult:
    text = f"{statement} {rationale}".lower()
    words = extract_keywords(text)

    # Step 1: Calculate group probabilities
    group_scores = {}
    for group, keywords in GROUP_KEYWORDS.items():
        primary_hits = count_matches(words, keywords["primary"])
        secondary_hits = count_matches(words, keywords["secondary"])
        group_scores[group] = primary_hits * 2 + secondary_hits

    total = sum(group_scores.values()) or 1
    group_probs = {g: s/total for g, s in group_scores.items()}
    recommended_group = max(group_probs, key=group_probs.get)

    # Step 2: Calculate feature probabilities (within recommended group)
    feature_scores = {}
    valid_features = GROUP_FEATURE_MATRIX[recommended_group]
    for feature in valid_features:
        hits = count_matches(words, FEATURE_KEYWORDS[feature])
        feature_scores[feature] = hits

    total = sum(feature_scores.values()) or 1
    feature_probs = {f: s/total for f, s in feature_scores.items()}
    recommended_feature = max(feature_probs, key=feature_probs.get)

    return ClassificationResult(
        recommended_group=recommended_group,
        group_confidence=group_probs[recommended_group],
        recommended_feature=recommended_feature,
        feature_confidence=feature_probs[recommended_feature],
        all_group_probs=group_probs,
        all_feature_probs=feature_probs
    )
```

### 4.4 Metadata Inference

```python
def infer_metadata(statement: str, group: str, feature: str) -> MetadataInference:
    text = statement.lower()

    # Scope inference
    if any(w in text for w in ["all", "every", "company", "enterprise", "organization"]):
        suggested_scope = "ORGANIZATION"
    elif any(w in text for w in ["domain", "bounded", "service", "team"]):
        suggested_scope = "DOMAIN"
    else:
        suggested_scope = "APPLICATION"

    # Blast radius inference
    if any(w in text for w in ["database", "auth", "security", "all services"]):
        suggested_blast_radius = "CRITICAL"
    elif any(w in text for w in ["api", "integration", "core"]):
        suggested_blast_radius = "HIGH"
    elif any(w in text for w in ["module", "component", "feature"]):
        suggested_blast_radius = "MEDIUM"
    else:
        suggested_blast_radius = "LOW"

    # Tags inference
    suggested_tags = []
    TAG_KEYWORDS = {
        "FE": ["frontend", "ui", "react", "vue", "css"],
        "BE": ["backend", "api", "server", "fastapi", "django"],
        "DB": ["database", "postgresql", "mongodb", "sql"],
        "INFRA": ["infrastructure", "docker", "kubernetes", "cloud"],
        "SECURITY": ["security", "auth", "encryption", "compliance"],
        # ... more
    }
    for tag, keywords in TAG_KEYWORDS.items():
        if any(k in text for k in keywords):
            suggested_tags.append(tag)

    return MetadataInference(
        suggested_scope=suggested_scope,
        suggested_blast_radius=suggested_blast_radius,
        suggested_tags=suggested_tags
    )
```

---

## 5. Phase 4: Consistency Check

### 5.1 Duplicate Detection

#### Similarity Levels

| Level | Similarity | Action |
|-------|------------|--------|
| EXACT | 100% | BLOCK storage |
| NEAR | 85-99% | REQUIRE acknowledgment |
| SEMANTIC | 70-84% | SHOW warning |
| RELATED | 50-69% | SUGGEST relation |

#### Algorithm

```python
def detect_duplicates(decision: Decision, existing: List[Decision]) -> List[DuplicateMatch]:
    matches = []

    for existing_dec in existing:
        # Level 1: Exact match
        if (decision.group_id == existing_dec.group_id and
            decision.feature_id == existing_dec.feature_id and
            normalize(decision.statement) == normalize(existing_dec.statement)):
            matches.append(DuplicateMatch(
                decision_id=existing_dec.decision_id,
                decision_code=existing_dec.decision_code,
                similarity=1.0,
                level="EXACT"
            ))
            continue

        # Level 2-4: Semantic similarity
        similarity = calculate_similarity(
            decision.statement,
            existing_dec.statement
        )

        if similarity >= 0.85:
            level = "NEAR"
        elif similarity >= 0.70:
            level = "SEMANTIC"
        elif similarity >= 0.50:
            level = "RELATED"
        else:
            continue

        matches.append(DuplicateMatch(
            decision_id=existing_dec.decision_id,
            decision_code=existing_dec.decision_code,
            similarity=similarity,
            level=level
        ))

    return sorted(matches, key=lambda m: m.similarity, reverse=True)
```

### 5.2 Conflict Detection

#### Conflict Types

```python
CONFLICT_PAIRS = {
    # Exclusive technologies
    ("postgresql", "mongodb"): ("exclusive_technology", "Database technology conflict"),
    ("mysql", "postgresql"): ("exclusive_technology", "Database technology conflict"),
    ("react", "vue"): ("exclusive_framework", "Frontend framework conflict"),
    ("react", "angular"): ("exclusive_framework", "Frontend framework conflict"),

    # Architecture conflicts
    ("microservice", "monolith"): ("architecture_conflict", "Architecture style conflict"),
    ("serverless", "kubernetes"): ("deployment_conflict", "Deployment model conflict"),

    # Communication conflicts
    ("rest", "graphql"): ("api_conflict", "API style conflict"),
    ("sync", "async"): ("pattern_conflict", "Communication pattern conflict"),
}

CONTRADICTION_PATTERNS = [
    (r"must use (\w+)", r"must not use \1"),
    (r"always (\w+)", r"never \1"),
    (r"require (\w+)", r"prohibit \1"),
]
```

#### Algorithm

```python
def detect_conflicts(decision: Decision, existing: List[Decision]) -> List[ConflictMatch]:
    conflicts = []
    decision_keywords = extract_keywords(decision.statement)

    for existing_dec in existing:
        existing_keywords = extract_keywords(existing_dec.statement)

        # Check conflict pairs
        for (kw1, kw2), (conflict_type, description) in CONFLICT_PAIRS.items():
            if ((kw1 in decision_keywords and kw2 in existing_keywords) or
                (kw2 in decision_keywords and kw1 in existing_keywords)):

                # Same feature = ERROR, different feature = WARNING
                severity = "ERROR" if decision.feature_id == existing_dec.feature_id else "WARNING"

                conflicts.append(ConflictMatch(
                    decision_id=existing_dec.decision_id,
                    decision_code=existing_dec.decision_code,
                    conflict_type=conflict_type,
                    description=description,
                    severity=severity
                ))

        # Check contradiction patterns
        for pos_pattern, neg_pattern in CONTRADICTION_PATTERNS:
            pos_match = re.search(pos_pattern, decision.statement.lower())
            neg_match = re.search(neg_pattern, existing_dec.statement.lower())
            if pos_match and neg_match and pos_match.group(1) == neg_match.group(1):
                conflicts.append(ConflictMatch(
                    decision_id=existing_dec.decision_id,
                    decision_code=existing_dec.decision_code,
                    conflict_type="direct_contradiction",
                    description=f"Direct contradiction detected",
                    severity="ERROR"
                ))

    return conflicts
```

---

## 6. Enhanced Response Structure

```python
@dataclass
class EnhancedValidationResponse:
    # Basic result
    result: Literal["READY", "INVALID", "BLOCKED"]
    proposal_id: str
    decision_id: str

    # Quality assessment (NEW)
    quality: QualityAssessment

    # Classification assessment (NEW)
    classification: ClassificationAssessment

    # Consistency assessment (NEW)
    consistency: ConsistencyAssessment

    # Existing fields
    violations: List[Violation]
    warnings: List[str]
    advisory_notes: List[str]
    skipped_rules: List[str]
    validated_at: datetime

@dataclass
class QualityAssessment:
    overall_score: int  # 0-100
    statement_score: int  # 0-25
    rationale_score: int  # 0-25
    constraint_score: int  # 0-25
    metadata_score: int  # 0-25
    grade: Literal["EXCELLENT", "GOOD", "FAIR", "POOR", "REJECT"]
    improvement_suggestions: List[str]

@dataclass
class ClassificationAssessment:
    recommended_group: str
    group_confidence: float  # 0-1
    recommended_feature: str
    feature_confidence: float  # 0-1
    user_group: str
    user_feature: str
    mismatch_warning: bool
    suggested_scope: str
    suggested_blast_radius: str
    suggested_tags: List[str]
    suggested_tech_stack: List[str]

@dataclass
class ConsistencyAssessment:
    duplicates: List[DuplicateMatch]
    conflicts: List[ConflictMatch]
    missing_relations: List[str]
    coherence_score: int  # 0-100
```

---

## 7. Blocking Rules

### 7.1 BLOCKED (cannot store)

```python
def should_block(response: EnhancedValidationResponse) -> bool:
    # Quality too low
    if response.quality.overall_score < 30:
        return True
    if response.quality.grade == "REJECT":
        return True

    # Exact duplicate exists
    if any(d.level == "EXACT" for d in response.consistency.duplicates):
        return True

    # Critical conflict exists
    if any(c.severity == "ERROR" for c in response.consistency.conflicts):
        return True

    # Schema/law violations
    if len(response.violations) > 0:
        return True

    return False
```

### 7.2 INVALID (can store with acknowledgment)

```python
def is_invalid(response: EnhancedValidationResponse) -> bool:
    # Quality below good
    if 30 <= response.quality.overall_score < 50:
        return True

    # Near duplicate unacknowledged
    if any(d.level == "NEAR" for d in response.consistency.duplicates):
        return True

    # Warning-level conflict
    if any(c.severity == "WARNING" for c in response.consistency.conflicts):
        return True

    # Low classification confidence
    if response.classification.group_confidence < 0.5:
        return True

    return False
```

---

## 8. Implementation Phases

### Phase A: Quality Scoring (P0)
- [ ] Implement Q-001 to Q-020 rules
- [ ] Add quality scoring to validation response
- [ ] Update frontend Validator page
- [ ] Add minimum quality threshold (30)

### Phase B: Duplicate Detection (P0)
- [ ] Implement similarity calculation
- [ ] Add duplicate detection to validation
- [ ] Create duplicate match response structure
- [ ] Block exact duplicates

### Phase C: Conflict Detection (P0)
- [ ] Build conflict keyword database
- [ ] Implement conflict detection algorithm
- [ ] Add conflict to validation response
- [ ] Block ERROR-level conflicts

### Phase D: Classification Guidance (P1)
- [ ] Build keyword databases
- [ ] Implement classification algorithm
- [ ] Add metadata inference
- [ ] Update frontend with recommendations

### Phase E: Enhanced UI (P1)
- [ ] Redesign Validator page
- [ ] Add quality score visualization
- [ ] Add classification recommendations panel
- [ ] Add duplicate/conflict warnings

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| False Positive Rate | < 5% | Valid decisions wrongly blocked |
| False Negative Rate | < 10% | Bad decisions that passed |
| Classification Accuracy | > 80% | Recommendations accepted |
| User Override Rate | < 20% | User changes recommendation |
| Quality Score Correlation | > 0.7 | Quality vs usefulness rating |

---

## 10. Appendix: Test Cases

### Test Case 1: Low Quality Decision
```json
{
  "statement": "Use X",
  "rationale": "Good",
  "constraints": []
}
```
Expected: BLOCKED (quality < 30)

### Test Case 2: Duplicate Decision
```json
{
  "statement": "Use PostgreSQL for all data storage",
  "group_id": "ARCH",
  "feature_id": "F07"
}
```
(When identical decision exists)
Expected: BLOCKED (exact duplicate)

### Test Case 3: Conflict Decision
```json
{
  "statement": "Use MongoDB for all persistent data",
  "group_id": "ARCH",
  "feature_id": "F07"
}
```
(When PostgreSQL decision exists)
Expected: BLOCKED or INVALID (conflict)

### Test Case 4: Misclassified Decision
```json
{
  "statement": "All API endpoints must require authentication",
  "group_id": "ARCH",
  "feature_id": "F08"
}
```
Expected: VALID with WARNING (CTL-F11 recommended)

### Test Case 5: Good Decision
```json
{
  "statement": "Use PostgreSQL 15+ for all relational data storage with read replicas for high availability",
  "rationale": "PostgreSQL provides ACID compliance, strong consistency guarantees, and excellent support for complex queries. Version 15+ offers improved performance and security features. Read replicas ensure high availability for read-heavy workloads.",
  "constraints": [
    {"constraint_id": "C-001", "type": "REQUIREMENT", "statement": "All services must use PostgreSQL client library v3+"},
    {"constraint_id": "C-002", "type": "PROHIBITION", "statement": "Direct database access from frontend is prohibited"}
  ],
  "invariants": ["Database schema changes must be backwards compatible"],
  "group_id": "ARCH",
  "feature_id": "F07",
  "scope": "ORGANIZATION",
  "blast_radius": "CRITICAL",
  "tags": ["DB", "INFRA"],
  "tech_stack": ["PostgreSQL", "Docker"]
}
```
Expected: READY (quality 85+, no conflicts)
