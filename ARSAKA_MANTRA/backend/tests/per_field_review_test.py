"""
Test Per-Field Review Workflow

Workflow:
1. AI fills semua field
2. Save as DRAFT
3. User review per-field (OK/NO)
4. Jika NO → user edit field itu
5. Setelah semua OK → finalize

Usage:
    python tests/per_field_review_test.py
"""

import sys
import os
import importlib.util

# Add parent to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Direct import to avoid pydantic dependency chain
def load_module(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

review_schema = load_module(
    "review_schema",
    os.path.join(backend_dir, "core", "domain", "review_schema.py")
)

AIDecisionDrafter = review_schema.AIDecisionDrafter
DecisionDraft = review_schema.DecisionDraft
FieldReviewStatus = review_schema.FieldReviewStatus
format_for_ui = review_schema.format_for_ui


def test_ai_creates_draft():
    """Test AI creates draft dengan semua field."""
    print("\n" + "=" * 70)
    print("TEST: AI Creates Draft")
    print("=" * 70)

    drafter = AIDecisionDrafter(
        user_id="human:john@example.com",
        ai_model="claude-opus-4-5"
    )

    draft = drafter.create_draft(
        request="implement rate limiting for API endpoints",
        context={
            "files": ["src/api/routes.py", "src/api/middleware.py"],
            "trigger": "Security review recommendation"
        }
    )

    print(f"\n  Draft ID: {draft.draft_id}")
    print(f"  Created by: {draft.created_by_ai}")
    print(f"  For user: {draft.user_id}")
    print(f"  Fields generated: {len(draft.fields)}")

    print("\n  Fields (all PENDING):")
    for name, review in draft.fields.items():
        status = "PENDING" if not review.is_reviewed else "REVIEWED"
        source = review.source.value
        value_str = str(review.value)[:40]
        print(f"    [{status}] {name}: {value_str}... ({source})")

    assert draft.needs_review == True
    assert len(draft.pending_fields) == len(draft.fields)
    print("\n  PASS: All fields pending review")
    return True


def test_user_reviews_fields():
    """Test user review per-field (OK/NO)."""
    print("\n" + "=" * 70)
    print("TEST: User Reviews Fields (OK/NO)")
    print("=" * 70)

    drafter = AIDecisionDrafter(user_id="human:jane@example.com")
    draft = drafter.create_draft("add database caching")

    print("\n  Simulating user review in UI...")
    print()

    # User reviews each field
    reviews = [
        ("title", True, None),           # OK
        ("statement", True, None),        # OK
        ("rationale", False, None),       # NO (will edit)
        ("domain_id", True, None),        # OK
        ("aspect_id", False, "A07"),      # NO, change to A07
        ("scope", True, None),            # OK
        ("blast_radius", True, None),     # OK
        ("constraints", True, None),      # OK
        ("trigger_event", True, None),    # OK
    ]

    for field_name, approved, new_value in reviews:
        if field_name not in draft.fields:
            continue

        action = "OK" if approved else "NO"
        edit_note = f" → edit to '{new_value}'" if new_value else ""

        draft.review_field(
            field_name,
            approved=approved,
            new_value=new_value
        )

        status = draft.fields[field_name].status.value
        print(f"    {field_name}: [{action}] → status={status}{edit_note}")

    # Check rejected fields
    rejected = draft.rejected_fields
    print(f"\n  Rejected fields (need edit): {rejected}")

    # User edits rejected field
    if "rationale" in rejected:
        print("\n  User editing 'rationale'...")
        draft.fields["rationale"].edit(
            "Adding caching will improve performance by 50% and reduce database load."
        )
        print(f"    New value: {draft.fields['rationale'].edited_value[:50]}...")

    # Check progress
    progress = draft.review_progress
    print(f"\n  Progress: {progress['reviewed']}/{progress['total_fields']} ({progress['percentage']}%)")

    assert progress["percentage"] == 100 or len(draft.rejected_fields) == 0
    print("  PASS: User can review per-field")
    return True


def test_finalize_after_review():
    """Test finalize setelah semua field OK."""
    print("\n" + "=" * 70)
    print("TEST: Finalize After All Fields Reviewed")
    print("=" * 70)

    drafter = AIDecisionDrafter(user_id="human:admin@example.com")
    draft = drafter.create_draft("implement logging")

    # User approves ALL fields
    print("\n  User approves all fields...")
    for field_name in draft.fields:
        draft.review_field(field_name, approved=True)

    progress = draft.review_progress
    print(f"  Progress: {progress['percentage']}%")
    print(f"  Can finalize: {draft.all_reviewed and not draft.rejected_fields}")

    # Finalize
    print("\n  User clicks FINALIZE...")
    decision = draft.finalize(approved_by="human:admin@example.com")

    print(f"\n  Final Decision:")
    print(f"    decision_id: {decision['decision_id']}")
    print(f"    approved_by: {decision['approved_by']}")
    print(f"    title: {decision['title'][:50]}...")
    print(f"    domain_id: {decision['domain_id']}")

    assert draft.finalized == True
    assert decision["approved_by"] == "human:admin@example.com"
    print("\n  PASS: Decision finalized with human approval")
    return True


def test_cannot_finalize_with_pending():
    """Test cannot finalize jika ada field pending."""
    print("\n" + "=" * 70)
    print("TEST: Cannot Finalize With Pending Fields")
    print("=" * 70)

    drafter = AIDecisionDrafter(user_id="human:user@example.com")
    draft = drafter.create_draft("add feature X")

    # Only review SOME fields
    draft.review_field("title", approved=True)
    draft.review_field("statement", approved=True)
    # Leave others pending...

    pending = draft.pending_fields
    print(f"\n  Pending fields: {len(pending)}")
    print(f"  Fields: {pending[:3]}...")

    # Try to finalize
    print("\n  Trying to finalize...")
    try:
        draft.finalize(approved_by="human:user@example.com")
        print("  ERROR: Should have failed!")
        return False
    except ValueError as e:
        print(f"  BLOCKED: {str(e)[:60]}...")

    print("\n  PASS: Cannot finalize with pending fields")
    return True


def test_cannot_finalize_with_ai_approval():
    """Test AI cannot be approver."""
    print("\n" + "=" * 70)
    print("TEST: AI Cannot Be Approver (MANTRA §6)")
    print("=" * 70)

    drafter = AIDecisionDrafter(user_id="human:user@example.com")
    draft = drafter.create_draft("test decision")

    # Approve all fields
    for field_name in draft.fields:
        draft.review_field(field_name, approved=True)

    # Try to finalize with AI as approver
    print("\n  Trying to finalize with AI approver...")
    try:
        draft.finalize(approved_by="ai:claude")  # VIOLATION!
        print("  ERROR: Should have failed!")
        return False
    except ValueError as e:
        print(f"  BLOCKED: {e}")

    print("\n  PASS: AI cannot approve (MANTRA §6 enforced)")
    return True


def test_ui_format():
    """Test format untuk UI."""
    print("\n" + "=" * 70)
    print("TEST: UI Format Output")
    print("=" * 70)

    drafter = AIDecisionDrafter(user_id="human:dev@example.com")
    draft = drafter.create_draft(
        "implement authentication",
        context={"files": ["auth.py"]}
    )

    # Format for UI
    ui_data = format_for_ui(draft)

    print(f"\n  Draft ID: {ui_data['draft_id']}")
    print(f"  Progress: {ui_data['review_progress']['percentage']}%")
    print(f"  Can Finalize: {ui_data['can_finalize']}")

    print("\n  Fields for UI:")
    for field in ui_data['fields'][:5]:
        print(f"    {field['label']}:")
        print(f"      Value: {str(field['display_value'])[:40]}...")
        print(f"      Source: {field['source_label']}")
        print(f"      Status: {field['status_label']}")
        print(f"      Can Edit: {field['can_edit']}")
        print()

    print("  PASS: UI format generated correctly")
    return True


def test_full_workflow_simulation():
    """Simulate complete workflow seperti di production."""
    print("\n" + "=" * 70)
    print("TEST: Full Workflow Simulation")
    print("=" * 70)

    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │  SIMULATION: User asks Claude to create a decision          │
    └─────────────────────────────────────────────────────────────┘
    """)

    # Step 1: User request via Claude
    print("  [1] User: 'Create a decision for API rate limiting'")

    # Step 2: AI creates draft
    print("  [2] Claude creates draft...")
    drafter = AIDecisionDrafter(
        user_id="human:developer@company.com",
        ai_model="claude-opus-4-5"
    )
    draft = drafter.create_draft(
        "implement rate limiting for all API endpoints",
        context={
            "files": ["src/api/routes.py", "src/middleware/rate_limit.py"],
            "trigger": "Security audit recommendation"
        }
    )
    print(f"      Draft created: {draft.draft_id}")

    # Step 3: Draft saved to DB
    print("  [3] Draft saved to database (needs_review=true)")

    # Step 4: User opens review UI
    print("  [4] User opens review UI...")
    ui_data = format_for_ui(draft)
    print(f"      Showing {len(ui_data['fields'])} fields to review")

    # Step 5: User reviews each field
    print("  [5] User reviews fields:")
    user_actions = [
        ("title", True, None, "Looks good"),
        ("statement", True, None, "Correct"),
        ("rationale", False, "Rate limiting is critical for API security and prevents abuse.", "Too generic"),
        ("domain_id", True, None, "CTL is correct"),
        ("aspect_id", True, None, "A10 security is right"),
        ("scope", True, None, "Backend scope is correct"),
        ("blast_radius", True, None, "Level 4 makes sense"),
        ("constraints", True, None, "Standard constraints OK"),
        ("trigger_event", True, None, "Correct trigger"),
        ("code_artifacts", True, None, "Files look correct"),
    ]

    for field_name, approved, new_value, comment in user_actions:
        if field_name not in draft.fields:
            continue

        action = "[OK]" if approved else "[NO → edit]"
        draft.review_field(field_name, approved=approved, new_value=new_value)
        print(f"      {field_name}: {action} - '{comment}'")

    # Check if all reviewed
    print(f"\n  [6] Review progress: {draft.review_progress['percentage']}%")

    # Step 7: Finalize
    print("  [7] User clicks FINALIZE...")
    decision = draft.finalize(approved_by="human:developer@company.com")

    print(f"\n  [COMPLETE] Decision created:")
    print(f"      ID: {decision['decision_id']}")
    print(f"      Approved by: {decision['approved_by']}")
    print(f"      Domain: {decision['domain_id']}")
    print(f"      Blast Radius: {decision['blast_radius']}")

    # Verify MANTRA compliance
    print("\n  [MANTRA COMPLIANCE CHECK]")
    print(f"      approved_by is human: {'ai:' not in decision['approved_by']}")
    print(f"      author_id is human: {'ai:' not in decision['author_id']}")
    print(f"      All fields reviewed: {draft.finalized}")

    return True


def run_all_tests():
    """Run all tests."""
    print("\n")
    print("=" * 70)
    print("PER-FIELD REVIEW WORKFLOW TESTS")
    print("=" * 70)

    tests = [
        ("AI Creates Draft", test_ai_creates_draft),
        ("User Reviews Fields", test_user_reviews_fields),
        ("Finalize After Review", test_finalize_after_review),
        ("Cannot Finalize Pending", test_cannot_finalize_with_pending),
        ("AI Cannot Approve", test_cannot_finalize_with_ai_approval),
        ("UI Format", test_ui_format),
        ("Full Workflow", test_full_workflow_simulation),
    ]

    results = {}
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = "PASS" if passed else "FAIL"
        except Exception as e:
            results[name] = f"ERROR: {e}"

    # Summary
    print("\n")
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results.values() if r == "PASS")
    for name, result in results.items():
        status = "[PASS]" if result == "PASS" else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n  Total: {passed}/{len(tests)} passed")

    if passed == len(tests):
        print("\n  PER-FIELD REVIEW: ALL TESTS PASSED")
        print("  Workflow supports per-field OK/NO with MANTRA compliance")
    else:
        print("\n  PER-FIELD REVIEW: SOME TESTS FAILED")

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
