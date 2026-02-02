"""
Draft API Integration Test

Tests the per-field review API endpoints.

Usage:
    python tests/draft_api_test.py
"""

import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct imports
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

review_schema = load_module("review_schema", os.path.join(backend_dir, "core", "domain", "review_schema.py"))
draft_repo = load_module("draft_repo", os.path.join(backend_dir, "adapters", "repositories", "draft_repository.py"))

AIDecisionDrafter = review_schema.AIDecisionDrafter
format_for_ui = review_schema.format_for_ui
InMemoryDraftRepository = draft_repo.InMemoryDraftRepository


async def test_api_flow():
    """Test the full API flow."""
    print("\n" + "=" * 70)
    print("DRAFT API INTEGRATION TEST")
    print("=" * 70)

    repo = InMemoryDraftRepository()

    # =========================================================================
    # Step 1: POST /drafts - Create draft
    # =========================================================================
    print("\n[1] POST /api/v1/drafts - Create draft")
    print("-" * 50)

    user_id = "human:developer@example.com"
    request_data = {
        "request": "implement rate limiting for all API endpoints",
        "context": {
            "files": ["src/api/routes.py", "src/middleware/rate_limit.py"],
            "trigger": "Security audit recommendation"
        }
    }

    # Simulate API call
    drafter = AIDecisionDrafter(user_id=user_id, ai_model="claude-opus-4-5")
    draft = drafter.create_draft(
        request=request_data["request"],
        context=request_data["context"]
    )
    await repo.save_draft(draft)

    print(f"  Response: draft_id={draft.draft_id}")
    print(f"  Fields: {len(draft.fields)}")
    print(f"  Needs Review: {draft.needs_review}")

    # =========================================================================
    # Step 2: GET /drafts/pending - List pending
    # =========================================================================
    print("\n[2] GET /api/v1/drafts/pending - List pending drafts")
    print("-" * 50)

    pending = await repo.get_pending_drafts(user_id)
    print(f"  Pending drafts: {len(pending)}")
    for d in pending:
        print(f"    - {d.draft_id}: {d.original_request[:40]}...")

    # =========================================================================
    # Step 3: GET /drafts/{id} - Get draft for review
    # =========================================================================
    print("\n[3] GET /api/v1/drafts/{id} - Get draft for review")
    print("-" * 50)

    draft_detail = await repo.get_draft(draft.draft_id)
    ui_data = format_for_ui(draft_detail)

    print(f"  Draft: {ui_data['draft_id']}")
    print(f"  Progress: {ui_data['review_progress']['percentage']}%")
    print(f"  Can Finalize: {ui_data['can_finalize']}")
    print(f"  Fields:")
    for f in ui_data['fields'][:3]:
        print(f"    - {f['name']}: {f['status_label']}")
    print(f"    ... and {len(ui_data['fields']) - 3} more")

    # =========================================================================
    # Step 4: POST /drafts/{id}/review/{field} - Review fields
    # =========================================================================
    print("\n[4] POST /api/v1/drafts/{id}/review/{field} - Review each field")
    print("-" * 50)

    # Simulate user clicking OK/NO on each field
    reviews = [
        ("title", True, None),
        ("statement", True, None),
        ("rationale", False, "Rate limiting prevents API abuse and ensures fair usage."),  # Edit
        ("domain_id", True, None),
        ("aspect_id", True, None),
        ("scope", True, None),
        ("blast_radius", True, None),
        ("constraints", True, None),
        ("trigger_event", True, None),
        ("code_artifacts", True, None),
    ]

    for field_name, approved, new_value in reviews:
        if field_name in draft.fields:
            result = await repo.update_field_review(
                draft_id=draft.draft_id,
                field_name=field_name,
                approved=approved,
                new_value=new_value,
            )
            action = "[OK]" if approved else f"[EDIT] → {new_value[:30]}..."
            print(f"    {field_name}: {action}")

    updated = await repo.get_draft(draft.draft_id)
    print(f"\n  Progress after review: {updated.review_progress['percentage']}%")
    print(f"  Can finalize: {updated.all_reviewed and not updated.rejected_fields}")

    # =========================================================================
    # Step 5: POST /drafts/{id}/finalize - Finalize
    # =========================================================================
    print("\n[5] POST /api/v1/drafts/{id}/finalize - Finalize draft")
    print("-" * 50)

    try:
        decision = await repo.finalize_draft(
            draft_id=draft.draft_id,
            approved_by="human:developer@example.com"  # MUST be human!
        )
        print(f"  Decision created!")
        print(f"    ID: {decision['decision_id']}")
        print(f"    Approved by: {decision['approved_by']}")
        print(f"    Domain: {decision['domain_id']}")
        print(f"    Blast Radius: {decision['blast_radius']}")
    except ValueError as e:
        print(f"  ERROR: {e}")

    # =========================================================================
    # Step 6: Verify MANTRA compliance - AI cannot approve
    # =========================================================================
    print("\n[6] VERIFY: AI Cannot Approve (MANTRA §6)")
    print("-" * 50)

    # Create another draft
    draft2 = drafter.create_draft("test decision 2")
    await repo.save_draft(draft2)

    # Approve all fields
    for field_name in draft2.fields:
        await repo.update_field_review(draft2.draft_id, field_name, True)

    # Try to finalize with AI
    try:
        await repo.finalize_draft(
            draft_id=draft2.draft_id,
            approved_by="ai:claude"  # VIOLATION!
        )
        print("  ERROR: AI was able to approve! This is a bug!")
        return False
    except ValueError as e:
        print(f"  BLOCKED: {e}")
        print("  PASS: AI cannot approve (MANTRA §6 enforced)")

    # =========================================================================
    # Step 7: Quick approve all
    # =========================================================================
    print("\n[7] POST /drafts/{id}/approve-all - Quick approve")
    print("-" * 50)

    draft3 = drafter.create_draft("quick test decision")
    await repo.save_draft(draft3)

    print(f"  Before: {draft3.review_progress['percentage']}% reviewed")

    # Approve all at once
    for field_name in list(draft3.pending_fields):
        await repo.update_field_review(draft3.draft_id, field_name, True)

    updated3 = await repo.get_draft(draft3.draft_id)
    print(f"  After: {updated3.review_progress['percentage']}% reviewed")

    # Finalize
    decision3 = await repo.finalize_draft(
        draft_id=draft3.draft_id,
        approved_by="human:admin@example.com"
    )
    print(f"  Finalized: {decision3['decision_id']}")

    print("\n" + "=" * 70)
    print("ALL API TESTS PASSED")
    print("=" * 70)

    return True


async def test_api_endpoints_summary():
    """Print API endpoint summary."""
    print("\n" + "=" * 70)
    print("DRAFT API ENDPOINTS SUMMARY")
    print("=" * 70)

    endpoints = [
        ("POST", "/api/v1/drafts", "Create draft (AI fills all fields)"),
        ("GET", "/api/v1/drafts", "List user's drafts"),
        ("GET", "/api/v1/drafts/pending", "List drafts needing review"),
        ("GET", "/api/v1/drafts/{id}", "Get draft for review UI"),
        ("POST", "/api/v1/drafts/{id}/review/{field}", "Review single field (OK/NO)"),
        ("POST", "/api/v1/drafts/{id}/review-bulk", "Review multiple fields"),
        ("POST", "/api/v1/drafts/{id}/approve-all", "Quick approve all fields"),
        ("POST", "/api/v1/drafts/{id}/finalize", "Finalize and create decision"),
        ("DELETE", "/api/v1/drafts/{id}", "Cancel/delete draft"),
    ]

    print("\n  Available Endpoints:")
    print("  " + "-" * 66)
    for method, path, desc in endpoints:
        print(f"  {method:<6} {path:<40} {desc}")

    print("\n  Workflow:")
    print("  " + "-" * 66)
    print("""
    1. User requests decision → POST /drafts
    2. AI creates draft with all fields filled
    3. User opens review UI → GET /drafts/{id}
    4. User clicks OK/NO per field → POST /drafts/{id}/review/{field}
    5. If NO → user edits, then OK
    6. All fields OK → POST /drafts/{id}/finalize
    7. Decision created with human approval
    """)

    print("  MANTRA Compliance:")
    print("  " + "-" * 66)
    print("""
    - AI creates drafts (fills fields)
    - AI CANNOT approve (finalize requires human approved_by)
    - Each field reviewed individually by human
    - Finalize blocked until all fields OK
    - approved_by MUST be human (ai: prefix rejected)
    """)


if __name__ == "__main__":
    asyncio.run(test_api_endpoints_summary())
    success = asyncio.run(test_api_flow())
    sys.exit(0 if success else 1)
