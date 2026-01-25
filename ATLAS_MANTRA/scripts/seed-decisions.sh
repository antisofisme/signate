#!/bin/bash
# ATLAS_MANTRA Seed Decisions Script
# Loads the 5 self-validation MANTRA decisions into the database
#
# Usage: ./seed-decisions.sh [--api-url=http://31.97.111.175:8002]

set -e

API_URL="${1:-http://31.97.111.175:8002}"
STORED_BY="ATLAS_MANTRA Core Team"

echo "================================================"
echo "  ATLAS_MANTRA Seed Decisions"
echo "  API: $API_URL"
echo "================================================"
echo ""

# Function to create decision
create_decision() {
    local json="$1"
    local name="$2"

    echo -n "Creating $name... "

    response=$(curl -s -X POST "$API_URL/api/v1/decisions" \
        -H "Content-Type: application/json" \
        -d "$json" 2>/dev/null)

    if echo "$response" | grep -q '"result":"STORED"'; then
        echo "✅ Created"
    elif echo "$response" | grep -q '"detail"'; then
        echo "❌ Failed: $(echo $response | grep -o '"msg":"[^"]*"' | head -1)"
    else
        echo "⚠️  Unknown: $response"
    fi
}

# MANTRA-DECISION-001: Immutability Principle
create_decision '{
    "decision": {
        "group_id": "CTL",
        "feature_id": "F-09",
        "statement": "Stored decisions MUST NOT be modified or deleted. All modifications are INVALID.",
        "rationale": "Immutability is the foundation of decision governance: (1) Audit trail integrity - cannot prove what was decided if records change, (2) Accountability - creators remain responsible, (3) Trust - stakeholders know records cannot be tampered, (4) Compliance - SOX/GDPR require proof at specific times, (5) Evolution clarity - changes are explicit via supersedes chain.",
        "constraints": [
            {"constraint_id": "P-001", "type": "PROHIBITION", "statement": "Decision records MUST NOT have UPDATE operations"},
            {"constraint_id": "P-002", "type": "PROHIBITION", "statement": "Decision records MUST NOT have DELETE operations"},
            {"constraint_id": "P-003", "type": "PROHIBITION", "statement": "Database triggers MUST prevent modification attempts"},
            {"constraint_id": "R-001", "type": "REQUIREMENT", "statement": "All changes MUST create new decision with supersedes link"},
            {"constraint_id": "R-002", "type": "REQUIREMENT", "statement": "Original decision MUST remain accessible forever"}
        ],
        "invariants": [
            "decision.created_at never changes after creation",
            "decision.statement never changes after creation",
            "decision.rationale never changes after creation",
            "Decision count only increases, never decreases"
        ],
        "scope": "ORGANIZATION",
        "blast_radius": "CRITICAL",
        "version": "1.0.0",
        "created_by": "ATLAS_MANTRA Core Team",
        "related_decisions": ["MANTRA-DECISION-003", "MANTRA-DECISION-004"]
    },
    "stored_by": "'"$STORED_BY"'"
}' "MANTRA-DECISION-001 (Immutability)"

# MANTRA-DECISION-002: AI Authority Zero
create_decision '{
    "decision": {
        "group_id": "CTL",
        "feature_id": "F-10",
        "statement": "AI authority in decision-making is ZERO. AI cannot create, approve, modify, or finalize decisions. Only humans have decision authority.",
        "rationale": "Human authority is non-negotiable: (1) Accountability - humans can be held responsible, AI cannot, (2) Legal standing - decisions affecting people must have human accountability, (3) Judgment - decisions require contextual understanding AI lacks, (4) Override capability - humans must always be able to override, (5) Trust - stakeholders trust identifiable humans, not algorithms.",
        "constraints": [
            {"constraint_id": "P-001", "type": "PROHIBITION", "statement": "API endpoints for create/approve MUST require human authentication"},
            {"constraint_id": "P-002", "type": "PROHIBITION", "statement": "created_by and approved_by fields MUST be human identifiers"},
            {"constraint_id": "P-003", "type": "PROHIBITION", "statement": "Automated systems MUST NOT call decision creation endpoints"},
            {"constraint_id": "R-001", "type": "REQUIREMENT", "statement": "Every decision MUST have identifiable human creator"},
            {"constraint_id": "R-002", "type": "REQUIREMENT", "statement": "Audit trail MUST distinguish human vs AI actions"},
            {"constraint_id": "L-001", "type": "LIMITATION", "statement": "AI-assisted decisions are valid IF human approves final version"}
        ],
        "invariants": [
            "Every stored decision has a human created_by",
            "Every stored decision has a human approver",
            "AI cannot directly write to decision store",
            "actor_type: ai never appears in decision creation audit logs"
        ],
        "scope": "ORGANIZATION",
        "blast_radius": "CRITICAL",
        "version": "1.0.0",
        "created_by": "ATLAS_MANTRA Core Team",
        "related_decisions": ["MANTRA-DECISION-001", "MANTRA-DECISION-003"]
    },
    "stored_by": "'"$STORED_BY"'"
}' "MANTRA-DECISION-002 (AI Authority Zero)"

# MANTRA-DECISION-003: No Status Field
create_decision '{
    "decision": {
        "group_id": "EVO",
        "feature_id": "F-13",
        "statement": "Decision records SHALL NOT have a status field. Lifecycle is expressed through existence + supersedes chain only.",
        "rationale": "Status fields violate immutability: (1) Status changes require UPDATE operations which violate immutability, (2) Lifecycle is already expressed via existence + supersedes chain, (3) What status would mean is unclear - DRAFT/APPROVED implies mutable workflow, (4) Simpler model - decision exists or does not exist, (5) Evolution via new versions, not status transitions.",
        "constraints": [
            {"constraint_id": "P-001", "type": "PROHIBITION", "statement": "No status column in decisions table"},
            {"constraint_id": "P-002", "type": "PROHIBITION", "statement": "No status field in Decision domain object"},
            {"constraint_id": "P-003", "type": "PROHIBITION", "statement": "No DRAFT/APPROVED/REJECTED workflow"},
            {"constraint_id": "R-001", "type": "REQUIREMENT", "statement": "Lifecycle expressed via version + supersedes only"},
            {"constraint_id": "R-002", "type": "REQUIREMENT", "statement": "Challenge creates new decision, not status change"}
        ],
        "invariants": [
            "decisions table has no status column",
            "Decision object has no status attribute",
            "All decisions are equally valid once stored",
            "Supersedes is the only evolution mechanism"
        ],
        "scope": "APPLICATION",
        "blast_radius": "HIGH",
        "version": "1.0.0",
        "created_by": "ATLAS_MANTRA Core Team",
        "related_decisions": ["MANTRA-DECISION-001", "MANTRA-DECISION-004"]
    },
    "stored_by": "'"$STORED_BY"'"
}' "MANTRA-DECISION-003 (No Status Field)"

# MANTRA-DECISION-004: Supersedes Chain
create_decision '{
    "decision": {
        "group_id": "EVO",
        "feature_id": "F-13",
        "statement": "Decision evolution MUST occur via supersedes links creating an append-only chain. The newest decision in a chain is current.",
        "rationale": "Supersedes chains enable evolution while preserving immutability: (1) Append-only - old decisions stay, new ones link back, (2) Full history - can trace evolution of any decision, (3) Clear currency - newest in chain is current, (4) Accountability preserved - each version has its creator, (5) Rollback possible - can supersede back to earlier version.",
        "constraints": [
            {"constraint_id": "R-001", "type": "REQUIREMENT", "statement": "supersedes field references valid decision_id or null"},
            {"constraint_id": "R-002", "type": "REQUIREMENT", "statement": "Version increment when superseding"},
            {"constraint_id": "R-003", "type": "REQUIREMENT", "statement": "Both old and new decisions remain queryable"},
            {"constraint_id": "L-001", "type": "LIMITATION", "statement": "Supersedes chain should not exceed reasonable depth"},
            {"constraint_id": "L-002", "type": "LIMITATION", "statement": "Long chains may indicate design problem"}
        ],
        "invariants": [
            "Superseded decision remains in database forever",
            "Chain is append-only, never modified",
            "Newest decision in chain is current",
            "Original decision always accessible via chain traversal"
        ],
        "scope": "APPLICATION",
        "blast_radius": "HIGH",
        "version": "1.0.0",
        "created_by": "ATLAS_MANTRA Core Team",
        "related_decisions": ["MANTRA-DECISION-001", "MANTRA-DECISION-003"]
    },
    "stored_by": "'"$STORED_BY"'"
}' "MANTRA-DECISION-004 (Supersedes Chain)"

# MANTRA-DECISION-005: Four Group Taxonomy
create_decision '{
    "decision": {
        "group_id": "INT",
        "feature_id": "F-03",
        "statement": "Decisions are classified into 4 Groups x 4 Features = 16 cells. Every decision belongs to exactly one cell.",
        "rationale": "The 4-group taxonomy provides: (1) Clarity - know where each decision belongs, (2) Balance - forces consideration of all aspects, (3) Completeness - 16 cells cover decision space, (4) Navigation - easy to find related decisions, (5) Governance - different groups may have different approval flows.",
        "constraints": [
            {"constraint_id": "R-001", "type": "REQUIREMENT", "statement": "Every decision MUST have valid group_id (INT, ARCH, CTL, EVO)"},
            {"constraint_id": "R-002", "type": "REQUIREMENT", "statement": "Every decision MUST have valid feature_id (F-01 to F-16)"},
            {"constraint_id": "R-003", "type": "REQUIREMENT", "statement": "Feature must belong to its group (F-01-F-04 in INT, etc)"},
            {"constraint_id": "L-001", "type": "LIMITATION", "statement": "One decision per cell recommended, not enforced"}
        ],
        "invariants": [
            "Exactly 4 groups exist",
            "Exactly 16 features exist (4 per group)",
            "Every decision has exactly one group and one feature",
            "Group-Feature mapping is fixed"
        ],
        "scope": "ORGANIZATION",
        "blast_radius": "HIGH",
        "version": "1.0.0",
        "created_by": "ATLAS_MANTRA Core Team",
        "related_decisions": []
    },
    "stored_by": "'"$STORED_BY"'"
}' "MANTRA-DECISION-005 (Four Group Taxonomy)"

echo ""
echo "================================================"
echo "  Seed Complete!"
echo "================================================"
echo ""
echo "Verify at: $API_URL/api/v1/decisions"
