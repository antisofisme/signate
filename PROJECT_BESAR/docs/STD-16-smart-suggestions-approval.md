# Smart Suggestions & Human-in-the-Loop Processing

> **Standard #47**: Semi-Automatic Processing with User Confirmation & Approval Workflows
>
> **Last Updated**: 2025-12-13
> **Status**: ✅ Standard Approved
> **Related**: STD-02 (Validation), STD-03 (Events), BIZ-03 (Accounting), SPEC-04 (Data Integration)

---

## Overview

**Philosophy**: "Suggest, don't automate. Reduce manual work without removing human control."

This standard establishes patterns for systems that process data, generate suggestions, and require user review before execution. Critical for reducing errors while maintaining human oversight—especially for high-stakes processes like accounting, reconciliation, and OCR data.

---

## 1. Core Principle: Confidence-Based Processing

### 1.1 The Pattern

```
User Input / Data
       ↓
System Process
       ↓
Generate Suggestion(s)
  - What to do
  - Confidence score (0-100%)
  - Reasoning/evidence
       ↓
Present to User for Review
  - Auto-checkboxes for high confidence
  - Manual review checkboxes for medium
  - Flagged as "needs attention" for low
       ↓
User Confirms/Rejects/Modifies
       ↓
Execute (Create Records)
       ↓
Audit Trail: User choices, approvals, timestamp
```

### 1.2 Never Fully Automatic

```
❌ BAD: OCR extracts name → auto-saves profile
   Risk: OCR misread, data saved incorrectly, discovered later

✅ GOOD: OCR extracts name → shows suggestion → user reviews → confirms → saves
   Benefit: User catches OCR errors before data committed

❌ BAD: Bank reconciliation auto-matches & auto-posts GL
   Risk: Wrong match, GL corrupted, discovery delayed

✅ GOOD: Bank reconciliation auto-matches with confidence scores → presents to user → user confirms → posts GL
   Benefit: User approves match, full audit trail, easy to rollback
```

---

## 2. Confidence Scoring System

### 2.1 Confidence Levels

```
Confidence Range | Decision | UI Treatment | Approval Required
═════════════════════════════════════════════════════════════════
>= 95%          | TRUST    | Pre-checked  | User review only
                |          | (checkbox    | (auto-approve if
                |          | checked)     | user doesn't reject)
───────────────────────────────────────────────────────────────
70-94%          | REVIEW   | Unchecked    | User must manually
                |          | (user must   | check + confirm
                |          | click to     |
                |          | accept)      |
───────────────────────────────────────────────────────────────
50-69%          | WARNING  | Unchecked    | User review +
                |          | + Yellow     | manager approval
                |          | alert        | (if amount/risk high)
───────────────────────────────────────────────────────────────
< 50%           | IGNORE   | Not shown    | Skip, requires
                |          | (hidden)     | manual handling
───────────────────────────────────────────────────────────────
```

### 2.2 Confidence Calculation

Depends on process. Examples:

```python
# BANK RECONCILIATION CONFIDENCE
def calc_reconciliation_confidence(bank_txn, gl_entry):
    score = 0

    # Amount match
    if bank_txn.amount == gl_entry.amount:
        score += 50  # Exact match = 50 points
    elif abs(bank_txn.amount - gl_entry.amount) < 1000:
        score += 30  # Close match = 30 points

    # Date proximity
    date_diff = abs((bank_txn.date - gl_entry.date).days)
    if date_diff == 0:
        score += 30  # Same day = 30 points
    elif date_diff <= 3:
        score += 20  # Within 3 days = 20 points
    elif date_diff <= 7:
        score += 10  # Within week = 10 points

    # Description similarity (fuzzy match)
    similarity = fuzzy_match(bank_txn.description, gl_entry.description)
    score += int(similarity * 10)  # 0-10 points

    # Previously matched? (historical accuracy)
    if has_historical_match(bank_txn.account, gl_entry.account):
        score += 10  # Common pair = 10 points

    return min(score, 100)

# Result examples:
# (Rp 10M, same day, exact desc, common account) = 95%+ = TRUST
# (Rp 10M, 2 days later, similar desc) = 80-90% = REVIEW
# (Rp 10M, no desc match, rare account) = 60% = WARNING
```

---

## 3. UI Pattern: Suggestion Presentation

### 3.1 General Suggestion UI

```
┌────────────────────────────────────────────────────────────┐
│ Smart Suggestion Review                                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Summary                                                    │
│ ─────────────────────────────────────────────────────────  │
│ • Total suggestions: 50                                   │
│ • Auto-matched (>95%): 40 ✅                              │
│ • Needs review (70-95%): 8 ⚠️                             │
│ • Low confidence (<70%): 2 ❌                             │
│ • Unmatched: 0                                            │
│                                                            │
│ ═════════════════════════════════════════════════════════ │
│                                                            │
│ Auto-Matched (40)                                          │
│ ─────────────────────────────────────────────────────────  │
│ [Collapse / Expand]                                       │
│                                                            │
│ ═════════════════════════════════════════════════════════ │
│                                                            │
│ Needs Your Review (8)                                     │
│ ─────────────────────────────────────────────────────────  │
│                                                            │
│ □ Bank TXN Rp 10M (2025-12-10)                            │
│   ← GL Entry Rp 10M "Guest checkout" (2025-12-09)        │
│   [Confidence: 92%] [Reasoning: Amount match, 1-day diff] │
│   [✓ ACCEPT] [✗ REJECT] [? SKIP]                          │
│                                                            │
│ □ Bank TXN Rp 7.5M (2025-12-10)                           │
│   ← GL Entry Rp 7.5M "Room service" (2025-12-10)         │
│   [Confidence: 88%] [Reasoning: Exact amount & date match]│
│   [✓ ACCEPT] [✗ REJECT] [? SKIP]                          │
│                                                            │
│ ⚠️  Low Confidence (2)                                      │
│                                                            │
│ Bank TXN Rp 2M "Transfer XYZ" (no GL match)               │
│ → Suggestion: Manual review needed                        │
│                                                            │
│ ═════════════════════════════════════════════════════════ │
│                                                            │
│ User Notes (Optional)                                     │
│ ┌──────────────────────────────────────┐                 │
│ │ Bank TXN Rp 2M pending invoice PO-123│                 │
│ └──────────────────────────────────────┘                 │
│                                                            │
│ [CONFIRM] [CANCEL] [UNDO RECENT] [SAVE DRAFT]            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 OCR Suggestion UI

```
┌────────────────────────────────────────────────────────────┐
│ OCR Data Extraction Review                                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Uploaded: KTP (ID Card)                                   │
│ Image: scan_ktp_12345.jpg → scan_ktp_12345.webp (25KB)   │
│                                                            │
│ Extracted Data                                             │
│ ─────────────────────────────────────────────────────────  │
│                                                            │
│ First Name                    Last Name                   │
│ ┌─────────────────────┐      ┌─────────────────────┐      │
│ │ KHOIRUL      ✓ 99% │      │ USER       ✓ 87%   │      │
│ └─────────────────────┘      └─────────────────────┘      │
│  Confident: Keep as-is       Medium confidence: Review    │
│                                                            │
│ ID Number                     ID Type                     │
│ ┌─────────────────────┐      ┌─────────────────────┐      │
│ │ 123456789    ✓ 99% │      │ KTP        ✓ 99%   │      │
│ └─────────────────────┘      └─────────────────────┘      │
│                                                            │
│ Date of Birth                 Address                     │
│ ┌─────────────────────┐      ┌─────────────────────┐      │
│ │ 1990-05-15   ✓ 95% │      │ Jl. Merdeka... ✓ 82│      │
│ └─────────────────────┘      └─────────────────────┘      │
│                                                            │
│ Gender                        City                        │
│ ┌─────────────────────┐      ┌─────────────────────┐      │
│ │ Male         ✓ 99% │      │ Jakarta    ⚠️ 65%  │      │
│ └─────────────────────┘      └─────────────────────┘      │
│  Fields marked ⚠️ = manual review recommended             │
│                                                            │
│ [CONFIRM & SAVE] [EDIT] [RETRY OCR] [CANCEL]              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.3 Expense Categorization Suggestion

```
┌────────────────────────────────────────────────────────────┐
│ Auto-Categorization Review                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Expense: "Electricity bill PLN Rp 2,000,000"             │
│                                                            │
│ Suggestion: COA 5410 (Utilities - Electricity)            │
│ Confidence: 98% [exact keyword match, vendor history]    │
│                                                            │
│ [✓ ACCEPT] [✗ REJECT]                                    │
│                                                            │
│ Or manually select:                                       │
│ ┌──────────────────────────────────┐                     │
│ │ Search COA...                    │                     │
│ │ 5410 - Utilities (Electricity)   │                     │
│ │ 5411 - Utilities (Water)         │                     │
│ │ 5400 - Facilities & Utilities    │                     │
│ └──────────────────────────────────┘                     │
│                                                            │
│ [CONFIRM & POST] [CANCEL]                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 4. Approval Workflow Patterns

### 4.1 Simple Approval (User Only)

```
System suggests → User reviews → User confirms → Execute

Use when:
  - Low financial impact (< Rp 1M)
  - Non-sensitive data (descriptions, memos)
  - Quick turnaround needed
```

### 4.2 Manager Approval

```
System suggests → User reviews → Submit for approval
                                        ↓
                                  Manager receives
                                  Manager reviews → Approve/Reject
                                        ↓
                                      Execute (if approved)

Use when:
  - Medium financial impact (Rp 1M - Rp 50M)
  - Accounting entries requiring oversight
  - Policy compliance check needed

Implementation:
  - Show: "Awaiting approval from manager_name"
  - Notify: Email/in-app notification to manager
  - Track: Who approved, when, any comments
  - Timeout: Auto-reject if not approved in 24h? (configurable)
```

### 4.3 Multi-Level Approval (Risk-Based)

```
System suggests → User reviews
                        ↓
                  Amount < Rp 5M?
                   /            \
                YES             NO
               /                  \
         Auto-approve         Manager needed?
              ↓                    /        \
            Execute            YES         NO
                              /              \
                         Manager         Director
                           ↓               ↓
                         (if            (if >
                        approved)      Rp 50M)
                           ↓
                         Execute

Use when:
  - High financial impact (> Rp 5M)
  - Treasury/payroll operations
  - System-critical operations
```

### 4.4 Approval with Comments

```typescript
interface ApprovalRequest {
  id: string;
  suggestion_id: string;      // Reference to suggestion
  requester_id: UUID;         // Who requested
  requested_at: timestamp;

  // What needs approval
  action: 'BANK_RECONCILIATION' | 'EXPENSE_CATEGORIZATION' | etc;
  data: {
    // Specific to action type
  };

  // Approval trail
  approvals: [{
    approver_id: UUID;
    status: 'PENDING' | 'APPROVED' | 'REJECTED';
    level: 'AUTO' | 'MANAGER' | 'DIRECTOR';
    comments?: string;
    approved_at?: timestamp;
    reason_if_rejected?: string;
  }];

  // Execution
  execution_status: 'PENDING' | 'EXECUTED' | 'FAILED';
  executed_at?: timestamp;
}
```

---

## 5. Handling User Responses

### 5.1 User Can Accept, Reject, or Modify

```
SUGGESTION: Auto-categorize expense to COA 5410 (Confidence 92%)

User has 3 options:

1. ACCEPT
   ✅ Use system suggestion as-is
   → Proceeds with approval workflow (if needed)

2. REJECT
   ❌ Disagree with suggestion
   → Mark as rejected, system learns (feedback loop)
   → User must manually select COA
   → Approval workflow proceeds with user's choice

3. MODIFY
   ✏️ Adjust suggestion (e.g., amount, date, description)
   → Show: "You modified suggestion, new values vs original"
   → System treats as manual entry (may need approval)

AFTER USER ACTION:
  Record: User choice, timestamp, reasoning (if provided)
  → Audit trail: "System suggested 5410 (92%), user selected 5411 (reason: bulk utilities)"
```

### 5.2 Partial Acceptance

```
BANK RECONCILIATION SUGGESTION:
  • 40 matches with >95% confidence
  • 8 matches with 70-94% confidence
  • 2 unmatched

User can:
  ✅ Accept all 40 high-confidence matches
  ✅ Accept 5 of 8 medium-confidence matches
  ⏭️  Skip 3 medium-confidence (not sure)
  ❌ Reject 2 unmatched (waiting for invoice)

  Click [CONFIRM]

Result:
  • 45 matches confirmed → GL posting created
  • 3 matches put in PENDING → manual review later
  • 2 unmatched → wait for documents

Audit:
  "User accepted 45/50 suggestions (90%)
   Confidence avg: 91%
   Rejected: 2 (waiting), 3 (pending user confirmation)
   Confirmed by: user123, 2025-12-13 14:30"
```

---

## 6. Feedback Loop & Learning

### 6.1 System Improves Based on User Feedback

```
FIRST RUN: System suggests COA based on keywords
  Confidence: 80%
  Suggestion: COA 5410 (Utilities)
  User rejects: "Actually it's 5411"

FEEDBACK RECORDED:
  keyword: "electricity"
  vendor: "PLN"
  expense_type: "utility"
  → Correctly classified as: COA 5411
  user_feedback: "User corrected to 5411"

LEARNING:
  System builds ML model:
    If (keyword = "electricity" AND vendor = "PLN")
      → COA 5411 with confidence boost

SECOND RUN (Same type of expense):
  System suggests: COA 5411 (Utilities - Water)
  Confidence: Now 94% (improved from 80%)
  User accepts immediately

OVER TIME:
  System becomes more accurate for recurring transactions
  Less user intervention needed
  Confidence scores increase
```

### 6.2 Feedback Storage

```python
class SuggestionFeedback(Base):
    __tablename__ = 'suggestion_feedback'

    id = Column(UUID, primary_key=True)
    suggestion_id = Column(UUID, ForeignKey('suggestions.id'))

    # User action
    user_action = Column(Enum)  # ACCEPTED, REJECTED, MODIFIED

    # Improvement
    original_suggestion: dict    # What system suggested
    user_correction: dict       # What user chose instead

    # Context for learning
    context: dict              # vendor, keywords, amount, date, etc

    # Metadata
    recorded_by = Column(UUID, ForeignKey('users.id'))
    recorded_at = Column(DateTime)

    # Quality metrics
    was_correct = Column(Boolean)  # Did user's choice improve accuracy?
    confidence_before = Column(Integer)
    confidence_after = Column(Integer)  # After learning
```

---

## 7. Error Handling & Rollback

### 7.1 If Suggestion Was Wrong

```
SCENARIO: User confirmed suggestion, but later found it was wrong

Bank Reconciliation Match (confirmed by user):
  Bank TXN Rp 10M ←→ GL Entry Rp 10M
  Later: "Wait, GL entry was for Rp 9M not 10M!"

USER OPTION:
  [UNDO MATCH] ← Only within 24h or before period lock

If undo clicked:
  • Matched transaction moved back to UNMATCHED
  • GL reversal entry created (if already posted)
  • Audit: "Match undone by user123, reason: amount mismatch discovered"
  • System learns: "This suggestion was incorrect, boost error checks"

If >24h or period locked:
  • Can't undo directly
  • Must use Reversal + New Entry (per BIZ-03 standard)
```

---

## 8. Semi-Automatic Processing in Different Contexts

### 8.1 OCR Profile Extraction

```
┌─ Upload Image
│       ↓
├─ OCR Process
│  ├─ Extract text fields
│  ├─ Validate format (phone, email, DOB)
│  └─ Calculate confidence per field
│       ↓
├─ Present Suggestion
│  ├─ High confidence (>90%): pre-filled, user reviews
│  ├─ Medium (70-90%): empty field, suggest as hint
│  └─ Low (<70%): flag for manual entry
│       ↓
├─ User Confirm/Edit
│  └─ Correct any fields
│       ↓
└─ Save Profile
   └─ Audit: "Created with OCR, confidence 92%, manually edited 2 fields"
```

### 8.2 Bank Reconciliation

```
┌─ Import Bank Statement
│       ↓
├─ Parse Bank Data
│       ↓
├─ Match GL Entries
│  ├─ Amount match
│  ├─ Date proximity
│  ├─ Description similarity
│  └─ Calculate confidence
│       ↓
├─ Present Suggestion
│  ├─ Auto-matched >95%: pre-checked
│  ├─ Suggested 70-95%: unchecked, user review
│  └─ Unmatched: not shown
│       ↓
├─ User Review & Confirm
│  ├─ Accept all auto-matched
│  ├─ Accept/reject/skip medium confidence
│  └─ Notes on unmatched
│       ↓
├─ Approval (if needed)
│  └─ Manager review & approve
│       ↓
└─ Post GL
   ├─ Create reconciliation entries
   └─ Audit: "48 matched (40 auto, 8 manual), approved by manager456"
```

### 8.3 Expense Categorization

```
┌─ Import Expense
│  ├─ Description: "Electricity bill PLN"
│  ├─ Amount: Rp 2M
│  └─ Vendor: PLN
│       ↓
├─ Analyze & Suggest
│  ├─ Keyword match: "electricity" → 5410
│  ├─ Vendor history: PLN usually 5410
│  ├─ Amount reasonable for utilities
│  └─ Confidence: 95%
│       ↓
├─ Present Suggestion
│  └─ COA 5410 (Utilities), confidence 95%, accept?
│       ↓
├─ User Confirm
│  └─ Click [ACCEPT]
│       ↓
└─ Post GL
   ├─ Debit 5410, Credit Cash/AP
   └─ Audit: "Auto-categorized (95% confidence), confirmed by user123"
```

---

## 9. Implementation Checklist

### 9.1 For Each Semi-Automatic Feature

- [ ] **Define Confidence Calculation**: What factors determine confidence?
- [ ] **Set Thresholds**: At what confidence is pre-checking acceptable?
- [ ] **Design UI**: How are suggestions presented to users?
- [ ] **Approval Workflow**: Who needs to approve? When?
- [ ] **User Feedback**: How can user reject/modify suggestion?
- [ ] **Audit Trail**: Track suggestion, user action, approval, execution
- [ ] **Rollback Plan**: How to undo if suggestion was wrong?
- [ ] **Error Handling**: What if system crashes during processing?
- [ ] **Learning Loop**: Does system improve from user feedback?
- [ ] **Testing**: Unit tests for confidence calc, integration tests for workflow

---

## 10. Key Takeaways

**Semi-Automatic ≠ Fully Automatic**

```
✅ Reduces manual work (system suggests)
✅ Maintains human control (user confirms)
✅ Builds audit trail (track all decisions)
✅ Enables learning (system improves over time)
✅ Allows rollback (easy to undo if wrong)

Perfect for:
  - OCR data extraction
  - Bank reconciliation
  - Expense categorization
  - Data matching/deduplication
  - Workflow automation with approval

Pattern: Process → Suggest → Review → Confirm → Execute → Audit
```

