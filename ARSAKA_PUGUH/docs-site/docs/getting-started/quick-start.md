---
sidebar_position: 1
---

# Quick Start Guide

Get up and running with ATLAS PUGUH in under 5 minutes.

## Prerequisites

- A modern web browser (Chrome, Firefox, Safari, Edge)
- An email address for registration

## Step 1: Create Your Account

1. Navigate to [puguh.arsaka.io](https://puguh.arsaka.io)
2. Click **"Get Started"** or **"Register"**
3. Enter your email and create a password
4. Verify your email address by clicking the link sent to your inbox

:::tip
You can also sign up using Google or GitHub OAuth for faster onboarding.
:::

## Step 2: Create Your First Tenant

After registration, you'll be prompted to create your first **Tenant** (organization):

1. Enter your organization name (e.g., "Acme Corp")
2. Choose a unique slug (e.g., "acme-corp") - this appears in URLs
3. Select your initial plan (Free tier is available)

Your tenant is now ready! You'll be redirected to the dashboard.

## Step 3: Explore the Dashboard

The dashboard shows your 5 core services:

| Service | Description |
|---------|-------------|
| **IAM** | Manage users, roles, and permissions |
| **Tenant** | Organization settings and members |
| **Decision** | Create and manage rules |
| **Workflow** | Set up approval workflows |
| **Control** | View audit logs and events |

## Step 4: Create Your First Rule

Let's create a simple approval rule:

1. Navigate to **Decision > Rules**
2. Click **"New Rule"**
3. Configure the rule:
   - **Name**: "High Value Approval"
   - **Condition**: `amount > 10000`
   - **Action**: `require_approval`
4. Click **"Save Draft"**
5. Test the rule with sample data
6. Request activation when ready

## Step 5: Integrate with Your Application

Use our SDK to integrate PUGUH into your application:

```typescript
import { PuguhClient } from '@arsaka/puguh-sdk';

const client = new PuguhClient({
  apiKey: 'your-api-key',
  tenantId: 'your-tenant-id',
});

// Request a decision
const decision = await client.decide({
  type: 'expense_approval',
  context: {
    amount: 15000,
    department: 'engineering',
    requestor: 'john@example.com',
  },
});

// Handle the decision
if (decision.outcome === 'APPROVED') {
  // Process the expense
} else if (decision.outcome === 'REQUIRES_APPROVAL') {
  // Route to approval workflow
}
```

## Next Steps

Now that you have the basics:

- [Create your first project](/docs/getting-started/first-project) for better organization
- [Build more complex rules](/docs/user-guides/decisions/rule-builder) using our visual builder
- [Set up approval workflows](/docs/user-guides/workflows/creating) for multi-step processes
- [Configure team access](/docs/user-guides/iam/users) with role-based permissions

## Need Help?

- Check our [troubleshooting guide](/docs/advanced/troubleshooting)
- Contact [support@arsaka.io](mailto:support@arsaka.io)
- Join our [Discord community](https://discord.gg/atlashub)
