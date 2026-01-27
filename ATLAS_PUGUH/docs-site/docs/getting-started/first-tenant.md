---
sidebar_position: 2
---

# Create Your First Tenant

A **Tenant** in ATLAS PUGUH represents your organization or workspace. All your rules, workflows, and team members are scoped within a tenant.

## Understanding Tenants

Think of a tenant as your company's private space within PUGUH:

- **Isolated data**: Each tenant's data is completely separate
- **Team collaboration**: Invite team members with different roles
- **Billing**: Each tenant has its own subscription plan
- **Projects**: Organize work into multiple projects within a tenant

## Creating a Tenant

### Via the Dashboard

1. After logging in, click your profile icon in the top-right
2. Select **"Create New Tenant"** from the dropdown
3. Fill in the tenant details:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Your organization name | "Acme Corporation" |
| **Slug** | URL-friendly identifier | "acme-corp" |
| **Description** | Optional description | "Main production tenant" |

4. Click **"Create Tenant"**

### Via API

```bash
curl -X POST https://api-puguh.atlashub.com/api/v1/tenants \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "description": "Main production tenant"
  }'
```

## Tenant Plans

Each tenant operates on a subscription plan that determines limits:

| Plan | Projects | Decisions/mo | Team Members | Price |
|------|----------|--------------|--------------|-------|
| **Free** | 1 | 1,000 | 3 | Rp 0 |
| **Starter** | 5 | 10,000 | 10 | Rp 290K/mo |
| **Pro** | Unlimited | 100,000 | Unlimited | Rp 990K/mo |
| **Enterprise** | Unlimited | Unlimited | Unlimited | Custom |

:::info
You can start with the Free plan and upgrade anytime. Your data is preserved when upgrading.
:::

## Inviting Team Members

Once your tenant is created, invite your team:

1. Navigate to **Tenant > Members**
2. Click **"Invite Member"**
3. Enter their email address
4. Select their role:
   - **Owner**: Full control, billing access
   - **Admin**: Manage rules, workflows, members
   - **Member**: Create and edit resources
   - **Viewer**: Read-only access

5. Click **"Send Invitation"**

The invited user will receive an email with a link to join your tenant.

## Tenant Roles

| Role | Create Rules | Manage Workflows | Invite Members | Billing | Delete Tenant |
|------|-------------|------------------|----------------|---------|---------------|
| **Owner** | Yes | Yes | Yes | Yes | Yes |
| **Admin** | Yes | Yes | Yes | No | No |
| **Member** | Yes | Yes | No | No | No |
| **Viewer** | No | No | No | No | No |

## Switching Between Tenants

If you belong to multiple tenants:

1. Click your profile icon or the tenant name in the header
2. Select from the **"Switch Tenant"** dropdown
3. Your context will update to the selected tenant

:::tip
The current tenant is shown in the URL: `/app/{tenant-slug}/...`
:::

## Tenant Settings

Access tenant settings via **Tenant > Settings**:

- **General**: Update name, description
- **Members**: Manage team access
- **Billing**: View/change subscription
- **Danger Zone**: Delete tenant (owner only)

## Next Steps

With your tenant created:

- [Create a project](/docs/getting-started/first-project) to organize your rules
- [Invite team members](#inviting-team-members) to collaborate
- [Upgrade your plan](#tenant-plans) if you need more capacity
