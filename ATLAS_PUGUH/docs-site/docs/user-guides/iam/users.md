---
sidebar_position: 1
---

# User Management

Learn how to manage users in your ATLAS PUGUH tenant.

## Understanding Users

Users in PUGUH represent individuals or services that can access your tenant's resources. Each user has:

- **Email**: Unique identifier for login
- **Role**: Permissions level within the tenant
- **Status**: Active, Suspended, or Pending Verification

## User Types

### Human Users
Regular team members who access PUGUH through the web interface or API.

- Log in via email/password or OAuth (Google/GitHub)
- Can use the dashboard and all UI features
- Actions are tracked in audit logs

### Service Accounts
Programmatic access for integrations and automated systems.

- API-only access (no UI login)
- Use API keys for authentication
- Perfect for CI/CD, background jobs, integrations

## Viewing Users

Navigate to **IAM > Users** to see all users in your tenant.

The user list shows:
| Column | Description |
|--------|-------------|
| Name | User's display name |
| Email | Login email |
| Role | Current role in tenant |
| Status | Active/Suspended/Pending |
| Joined | When they joined the tenant |

### Filtering Users

Use the filters to narrow down the list:
- **By Role**: Show only admins, members, etc.
- **By Status**: Active, suspended, or pending
- **Search**: Find users by name or email

## Inviting Users

To invite a new team member:

1. Click **"Invite User"** button
2. Enter their email address
3. Select their role:
   - **Admin**: Full management access
   - **Member**: Create and edit resources
   - **Viewer**: Read-only access
4. Click **"Send Invitation"**

The invitee will receive an email with a link to accept.

:::tip
You cannot invite someone as Owner - there can only be one Owner per tenant.
:::

## Managing User Roles

To change a user's role:

1. Click on the user in the list
2. Go to the **Role** section
3. Select the new role from the dropdown
4. Click **"Update Role"**

### Role Permissions

| Permission | Owner | Admin | Member | Viewer |
|------------|-------|-------|--------|--------|
| View resources | Yes | Yes | Yes | Yes |
| Create rules | Yes | Yes | Yes | No |
| Edit rules | Yes | Yes | Yes | No |
| Delete rules | Yes | Yes | No | No |
| Manage workflows | Yes | Yes | Yes | No |
| Invite users | Yes | Yes | No | No |
| Remove users | Yes | Yes | No | No |
| Billing access | Yes | No | No | No |
| Delete tenant | Yes | No | No | No |

## Suspending Users

To temporarily disable a user's access:

1. Click on the user
2. Click **"Suspend User"**
3. Confirm the action

Suspended users:
- Cannot log in
- API keys stop working
- Can be reactivated later

## Removing Users

To permanently remove a user from your tenant:

1. Click on the user
2. Click **"Remove from Tenant"**
3. Confirm the action

:::caution
This action cannot be undone. The user will lose all access and will need a new invitation to rejoin.
:::

## User Details Page

Click any user to view their details:

### Profile Tab
- Name and email
- Role and status
- Join date

### Activity Tab
- Recent actions
- Login history
- API usage

### Permissions Tab
- Effective permissions
- Role inheritance

## Best Practices

1. **Use Least Privilege**: Give users only the access they need
2. **Regular Audits**: Review user list periodically
3. **Prompt Removal**: Remove users who leave the organization
4. **Service Accounts**: Use service accounts for integrations instead of personal accounts
5. **Strong Passwords**: Encourage or require strong passwords

## Related

- [Roles & Permissions](/docs/user-guides/iam/roles)
- [Service Accounts](/docs/user-guides/iam/access-control)
- [Audit Trail](/docs/user-guides/control/environments)
