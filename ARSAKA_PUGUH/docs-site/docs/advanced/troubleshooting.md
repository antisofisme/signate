---
sidebar_position: 4
---

# Troubleshooting

Common issues and how to resolve them.

## Authentication Issues

### "Invalid or expired token"

**Cause**: JWT token has expired or is malformed.

**Solution**:
1. Check token expiration time
2. Refresh the token
3. Re-authenticate if refresh fails

```typescript
try {
  await client.listRules();
} catch (error) {
  if (error.code === 'TOKEN_EXPIRED') {
    await client.refreshToken();
    await client.listRules(); // Retry
  }
}
```

### "API key not found"

**Cause**: Invalid or revoked API key.

**Solution**:
1. Verify the API key is correct
2. Check if the key was rotated
3. Ensure the key is for the right tenant

### "Permission denied"

**Cause**: User lacks required permission.

**Solution**:
1. Check user's role in IAM
2. Verify the required permission
3. Request role upgrade if needed

```typescript
// Check required permission
const hasPermission = await client.checkPermission('decision.rules.create');
if (!hasPermission) {
  console.log('Contact your admin to request access');
}
```

## Rule Issues

### Rule Not Matching

**Symptoms**: Decision returns NO_MATCH when you expect a rule to trigger.

**Debugging Steps**:

1. **Check Rule Status**
   ```typescript
   const rule = await client.getRule(ruleId);
   console.log(rule.status); // Should be 'active'
   ```

2. **Verify Conditions**
   ```typescript
   const result = await client.testRule(ruleId, testContext);
   console.log(result.evaluation.conditions);
   // See which conditions failed
   ```

3. **Check Priority**
   ```typescript
   const rules = await client.listRules({
     decisionType: 'expense_approval',
     status: 'active'
   });
   // Higher priority rule might be matching first
   ```

4. **Check Scope**
   ```typescript
   // Rule might be in wrong project
   console.log(rule.scope, rule.projectId);
   ```

### Wrong Rule Matching

**Symptoms**: Unexpected rule is matching.

**Debugging Steps**:

1. **View Evaluation Trace**
   ```typescript
   const decision = await client.decide({
     type: 'expense_approval',
     context: testContext,
     options: { includeEvaluation: true }
   });

   console.log(decision.evaluation.trace);
   // Shows all rules evaluated in order
   ```

2. **Check Priorities**
   ```typescript
   // List rules by priority
   const rules = await client.listRules({
     decisionType: 'expense_approval',
     orderBy: 'priority',
     order: 'desc'
   });
   ```

3. **Review Condition Logic**
   ```
   Expected: amount > 5000
   Actual condition might be: amount >= 5000
   Check for off-by-one errors
   ```

### Rule Update Not Taking Effect

**Symptoms**: Changed a rule but behavior unchanged.

**Causes & Solutions**:

1. **Still in Draft**
   - Activate the rule after editing

2. **Caching**
   - Wait for cache to expire (usually 60s)
   - Or request with `cache: false`

3. **Wrong Version**
   - Check which version is active
   - Verify edit created new version

## Workflow Issues

### Workflow Stuck

**Symptoms**: Workflow not progressing to next stage.

**Debugging Steps**:

1. **Check Current Stage**
   ```typescript
   const workflow = await client.getWorkflow(workflowId);
   console.log(workflow.currentStage);
   console.log(workflow.assignedTo);
   ```

2. **Check Assignee**
   - Is the assignee active?
   - Do they have access?
   - Are notifications working?

3. **Check Timeout**
   ```typescript
   console.log(workflow.stageDeadline);
   // If past deadline, check timeout action
   ```

4. **Manual Override**
   ```typescript
   // Admin can reassign
   await client.delegateWorkflow(workflowId, {
     to: 'backup-approver@company.com',
     reason: 'Original assignee unavailable'
   });
   ```

### Workflow Notifications Not Sending

**Symptoms**: Approvers not receiving emails.

**Check**:

1. **Email Configuration**
   - Verify email addresses are correct
   - Check spam folders

2. **Notification Settings**
   - User might have disabled notifications
   - Check tenant notification settings

3. **Integration Status**
   - Check Slack/email integration health
   - View notification logs in Control > Events

### Duplicate Workflows

**Symptoms**: Same request creates multiple workflows.

**Cause**: Idempotency key not used.

**Solution**:
```typescript
const decision = await client.decide({
  type: 'expense_approval',
  context: expense,
  options: {
    idempotencyKey: `expense-${expense.id}` // Unique per request
  }
});
```

## Performance Issues

### Slow Decisions

**Symptoms**: Decision latency higher than expected.

**Debugging**:

1. **Check Rule Count**
   ```typescript
   const rules = await client.listRules({
     decisionType: 'expense_approval',
     status: 'active'
   });
   console.log(`Active rules: ${rules.length}`);
   // Too many rules = slower evaluation
   ```

2. **Check Rule Complexity**
   - Deeply nested conditions are slower
   - Simplify or split complex rules

3. **Check Context Size**
   - Large context objects slow down evaluation
   - Only include necessary fields

4. **Check Network Latency**
   - Use regional API endpoints
   - Consider caching for repeated requests

### Rate Limiting

**Symptoms**: 429 errors.

**Solution**:

1. **Check Usage**
   ```typescript
   const usage = await client.getTenantUsage();
   console.log(`Decisions: ${usage.decisions.used}/${usage.decisions.limit}`);
   ```

2. **Implement Retry Logic**
   ```typescript
   const client = new PuguhClient({
     retries: 3,
     retryDelay: 1000,
   });
   ```

3. **Batch Requests**
   ```typescript
   // Instead of individual calls
   const decisions = await client.decideBatch(requests);
   ```

4. **Upgrade Plan**
   - Higher plans have higher rate limits

## Data Issues

### Missing Decisions

**Symptoms**: Decisions not appearing in history.

**Check**:

1. **Dry Run Mode**
   ```typescript
   // Dry run decisions aren't persisted
   const decision = await client.decide({
     context: {...},
     options: { dryRun: false } // Make sure this is false
   });
   ```

2. **Time Range**
   - Expand date range in query
   - Check timezone settings

3. **Project Filter**
   - Decisions might be in different project
   - Check project scope

### Audit Log Gaps

**Symptoms**: Missing entries in audit trail.

**Causes**:

1. **Retention Period**
   - Free plan: 7 days
   - Check your plan's retention

2. **Filter Settings**
   - Remove filters to see all entries
   - Check action type filters

3. **Export Archived Logs**
   - Contact support for older logs (Enterprise)

## Integration Issues

### Webhook Not Firing

**Symptoms**: External system not receiving events.

**Debugging**:

1. **Check Webhook Status**
   - Go to Settings > Webhooks
   - Check webhook health status

2. **Verify Endpoint**
   - Ensure URL is reachable
   - Check for HTTPS requirement

3. **Check Signature**
   ```typescript
   // Your webhook handler
   const isValid = verifyWebhookSignature(
     req.body,
     req.headers['x-puguh-signature'],
     webhookSecret
   );
   ```

4. **Review Webhook Logs**
   - Control > Events shows webhook delivery attempts
   - Check for error responses

### SDK Connection Issues

**Symptoms**: SDK calls timing out or failing.

**Check**:

1. **Network Connectivity**
   ```bash
   curl https://api.puguh.arsaka.io/health
   ```

2. **Firewall Rules**
   - Ensure outbound HTTPS allowed
   - Check corporate proxy settings

3. **SDK Configuration**
   ```typescript
   const client = new PuguhClient({
     timeout: 30000, // Increase timeout
     baseUrl: 'https://api.puguh.arsaka.io', // Correct URL
   });
   ```

## Getting Help

If you can't resolve an issue:

1. **Check Status Page**: https://status.arsaka.io
2. **Review Docs**: Search documentation
3. **Contact Support**: support@arsaka.io
4. **Include Details**:
   - Tenant ID
   - Timestamp of issue
   - Error messages
   - Steps to reproduce

## Related

- [Best Practices](/docs/advanced/best-practices)
- [API Reference](/docs/api-reference/authentication)
- [Audit Trail](/docs/user-guides/control/environments)
