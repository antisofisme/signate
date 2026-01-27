---
sidebar_position: 3
---

# Testing Rules

Learn how to test rules before deploying them to production.

## Why Test Rules?

Testing rules is critical because:

- **Catch errors early**: Find bugs before they affect real decisions
- **Validate logic**: Ensure conditions work as expected
- **Prevent regressions**: Changes don't break existing behavior
- **Document behavior**: Tests serve as executable documentation

## Test Methods

### 1. Quick Test (Rule Builder)

The fastest way to test during development:

1. Open a rule in the editor
2. Click **"Test Rule"**
3. Enter sample data
4. See immediate results

### 2. Test Scenarios

Save reusable test cases:

1. Go to rule details
2. Click **"Test Scenarios"** tab
3. Create scenarios for:
   - Expected matches
   - Expected non-matches
   - Edge cases

### 3. Batch Testing

Test multiple rules together:

1. Go to **Decision > Testing**
2. Select rules to test
3. Upload test data file
4. Run batch test
5. Review results

## Creating Test Scenarios

### Scenario Structure

```json
{
  "name": "High value equipment should require approval",
  "description": "Purchases over $5000 for equipment need manager sign-off",
  "input": {
    "amount": 7500,
    "category": "equipment",
    "department": "engineering"
  },
  "expected": {
    "matches": true,
    "action": "REQUIRE_APPROVAL"
  }
}
```

### Scenario Types

#### Positive Tests
Verify the rule matches when it should:

```json
{
  "name": "Should match - amount exceeds threshold",
  "input": { "amount": 15000 },
  "expected": { "matches": true }
}
```

#### Negative Tests
Verify the rule doesn't match when it shouldn't:

```json
{
  "name": "Should not match - amount below threshold",
  "input": { "amount": 500 },
  "expected": { "matches": false }
}
```

#### Boundary Tests
Test values at the edge:

```json
{
  "name": "Boundary - exactly at threshold",
  "input": { "amount": 5000 },
  "expected": { "matches": false }  // > 5000, not >=
}
```

#### Null Tests
Verify null handling:

```json
{
  "name": "Null department should not match",
  "input": { "amount": 10000, "department": null },
  "expected": { "matches": false }
}
```

## Test Results

### Result Structure

```json
{
  "scenario": "High value equipment",
  "passed": true,
  "actual": {
    "matches": true,
    "action": "REQUIRE_APPROVAL",
    "conditions_evaluated": [
      { "field": "amount", "result": true },
      { "field": "category", "result": true }
    ]
  },
  "expected": {
    "matches": true,
    "action": "REQUIRE_APPROVAL"
  },
  "execution_time_ms": 2
}
```

### Understanding Failures

When a test fails, you'll see:

```
❌ FAILED: High value equipment should require approval

Expected: matches = true, action = REQUIRE_APPROVAL
Actual:   matches = false

Condition Results:
  ✓ amount > 5000 → true (7500 > 5000)
  ✗ category = "equipment" → false (actual: "supplies")
```

## Test Coverage

### Viewing Coverage

Go to **Decision > Testing > Coverage** to see:

- Percentage of rules with tests
- Rules without any tests
- Conditions never tested

### Coverage Metrics

| Metric | Description |
|--------|-------------|
| **Rule Coverage** | % of rules with at least one test |
| **Condition Coverage** | % of conditions tested |
| **Action Coverage** | % of actions verified |

### Improving Coverage

1. Add tests for all active rules
2. Cover all condition branches
3. Test all possible actions
4. Include edge cases

## Batch Testing

### Uploading Test Data

Create a CSV or JSON file:

**CSV Format:**
```csv
amount,category,department,expected_matches,expected_action
7500,equipment,engineering,true,REQUIRE_APPROVAL
500,supplies,sales,false,
15000,equipment,executive,false,
```

**JSON Format:**
```json
{
  "tests": [
    {
      "input": { "amount": 7500, "category": "equipment" },
      "expected": { "matches": true, "action": "REQUIRE_APPROVAL" }
    }
  ]
}
```

### Running Batch Tests

1. Go to **Decision > Testing**
2. Click **"Upload Test File"**
3. Select your file
4. Click **"Run Tests"**
5. Download results

### Batch Results

Results show:
- Total tests run
- Passed / Failed count
- Detailed failures
- Performance metrics

## Automated Testing

### CI/CD Integration

Test rules in your deployment pipeline:

```yaml
# GitHub Actions example
- name: Test PUGUH Rules
  run: |
    puguh-cli test \
      --tenant ${{ secrets.PUGUH_TENANT_ID }} \
      --api-key ${{ secrets.PUGUH_API_KEY }} \
      --scenarios ./tests/rules/*.json \
      --fail-on-error
```

### API Testing

```typescript
import { PuguhClient } from '@atlashub/puguh-sdk';

const client = new PuguhClient({ apiKey: '...' });

// Test a specific rule
const result = await client.testRule('rule-id', {
  amount: 7500,
  category: 'equipment'
});

expect(result.matches).toBe(true);
expect(result.action).toBe('REQUIRE_APPROVAL');
```

### Webhook Testing

Test webhook actions:

```typescript
// Mock your webhook endpoint
const mockServer = createMockServer();

// Test rule with CUSTOM action
const result = await client.testRule('webhook-rule', testData);

// Verify webhook was called correctly
expect(mockServer.lastRequest.body).toMatchObject({
  rule_id: 'webhook-rule',
  context: testData
});
```

## Testing Best Practices

### 1. Test Before Activation
Never activate a rule without tests.

### 2. Name Tests Clearly
"Should require approval for amounts over $5000 in engineering"

### 3. Cover Edge Cases
- Minimum and maximum values
- Empty strings and nulls
- Special characters

### 4. Test Priority Interactions
Verify higher-priority rules override correctly.

### 5. Keep Tests Updated
Update tests when rule logic changes.

### 6. Use Realistic Data
Test with data similar to production.

## Debugging Failed Tests

### Step 1: Check Conditions
Review each condition's result:
- Which condition failed?
- What was the actual value?

### Step 2: Verify Input
Ensure test input matches expected format:
- Correct field names
- Correct data types
- No typos

### Step 3: Check Priority
Maybe another rule matched first:
- View all matching rules
- Check priority order

### Step 4: Review History
Did the rule change recently?
- Compare versions
- Check recent edits

## Related

- [Rules Overview](/docs/user-guides/decisions/rules)
- [Rule Builder](/docs/user-guides/decisions/rule-builder)
- [Versioning](/docs/user-guides/decisions/versioning)
