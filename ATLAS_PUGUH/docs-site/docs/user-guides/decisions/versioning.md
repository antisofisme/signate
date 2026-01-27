---
sidebar_position: 4
---

# Rule Versioning

Learn how rule versioning works in ATLAS PUGUH.

## Why Versioning?

Rule versioning provides:

- **Audit trail**: See who changed what and when
- **Rollback capability**: Restore previous versions
- **Change review**: Compare versions side-by-side
- **Compliance**: Meet regulatory requirements

## Version Lifecycle

```
v1 (Initial) → v2 (Edit) → v3 (Edit) → v4 (Current)
      │             │            │            │
   Active       Superseded   Superseded    Active
```

Every edit creates a new version. Only one version is active at a time.

## Viewing Versions

### Version History

1. Open a rule
2. Click **"History"** or **"Versions"** tab
3. See all versions with:
   - Version number
   - Author
   - Timestamp
   - Change description

### Version Details

Click any version to see:
- Full rule configuration
- Conditions and actions
- Metadata and settings

## Comparing Versions

### Side-by-Side Diff

1. Select two versions to compare
2. Click **"Compare"**
3. See highlighted differences:
   - Green: Added
   - Red: Removed
   - Yellow: Modified

### Example Diff

```diff
  Conditions:
-   amount > 5000
+   amount > 10000

  Actions:
    type: REQUIRE_APPROVAL
-   workflow: manager-approval
+   workflow: director-approval
    priority: high
```

## Creating Versions

### Automatic Versioning

New version created when you:
- Edit conditions
- Change actions
- Update priority
- Modify settings

### Version Metadata

Each version includes:

| Field | Description |
|-------|-------------|
| **Version** | Sequential number (v1, v2, ...) |
| **Author** | Who made the change |
| **Timestamp** | When it was created |
| **Description** | Optional change description |
| **Status** | draft, active, superseded |

### Adding Descriptions

When saving, add a meaningful description:

Good: "Increased threshold from $5K to $10K per Q4 policy"
Bad: "Updated rule"

## Restoring Versions

### Restore Process

1. View the version to restore
2. Click **"Restore This Version"**
3. Confirm the action
4. Creates a NEW version (doesn't delete history)

### What Gets Restored

- Conditions
- Actions
- Priority
- Settings

### What Doesn't Get Restored

- Status (goes to draft)
- Version number (gets new version)
- Metadata (new author/timestamp)

## Version States

### Draft
- Being edited
- Not evaluated
- Can be modified

### Pending Review
- Submitted for activation
- Awaiting approval
- Locked from edits

### Active
- Currently evaluating decisions
- Creates new version on edit
- Only one active version

### Superseded
- Replaced by newer version
- Kept for audit purposes
- Can be restored

## Version Limits

| Plan | Version Retention |
|------|-------------------|
| Free | Last 10 versions |
| Starter | Last 50 versions |
| Pro | Last 100 versions |
| Enterprise | Unlimited |

Older versions are archived but can be retrieved on request.

## Branching (Enterprise)

Enterprise plans support version branching:

```
v1 (main)
 ├── v2 (main)
 │    └── v2.1 (feature-branch)
 │         └── v2.2 (feature-branch)
 └── v3 (main) ← merged from v2.2
```

### Creating a Branch

1. Open a version
2. Click **"Create Branch"**
3. Name your branch
4. Make changes safely

### Merging Branches

1. Open the branch
2. Click **"Merge to Main"**
3. Resolve any conflicts
4. Complete the merge

## API Access

### List Versions

```typescript
const versions = await client.getRuleVersions('rule-id');
// Returns array of version metadata
```

### Get Specific Version

```typescript
const v2 = await client.getRuleVersion('rule-id', 2);
// Returns full rule at version 2
```

### Compare Versions

```typescript
const diff = await client.compareRuleVersions('rule-id', 1, 3);
// Returns structured diff
```

### Restore Version

```typescript
await client.restoreRuleVersion('rule-id', 2, {
  description: 'Reverting bad change'
});
// Creates new version with v2 content
```

## Best Practices

### 1. Write Meaningful Descriptions
Explain WHY you made the change, not just WHAT changed.

### 2. Review Before Activating
Always compare with the previous active version.

### 3. Test New Versions
Run tests against new versions before activation.

### 4. Don't Fear Reverting
It's easy to restore - don't hesitate if something goes wrong.

### 5. Use Branches for Experiments
Test major changes in branches before merging.

## Audit Requirements

For compliance, PUGUH maintains:

- **Immutable history**: Past versions cannot be modified
- **Author tracking**: Every change attributed to a user
- **Timestamp precision**: Microsecond-accurate timestamps
- **Change details**: Full before/after state
- **Export capability**: Download complete history

### Exporting History

1. Open rule history
2. Click **"Export"**
3. Choose format (JSON, CSV)
4. Download file

### Example Export

```json
{
  "rule_id": "rule-123",
  "name": "High Value Approval",
  "versions": [
    {
      "version": 1,
      "author": "john@example.com",
      "created_at": "2025-01-01T10:00:00Z",
      "description": "Initial version",
      "status": "superseded",
      "conditions": {...},
      "actions": {...}
    },
    {
      "version": 2,
      "author": "jane@example.com",
      "created_at": "2025-01-15T14:30:00Z",
      "description": "Increased threshold to $10K",
      "status": "active",
      "conditions": {...},
      "actions": {...}
    }
  ]
}
```

## Related

- [Rules Overview](/docs/user-guides/decisions/rules)
- [Rule Builder](/docs/user-guides/decisions/rule-builder)
- [Testing Rules](/docs/user-guides/decisions/testing)
