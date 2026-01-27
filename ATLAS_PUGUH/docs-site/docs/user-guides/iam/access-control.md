---
sidebar_position: 4
---

# Access Control

Configure access control for your ATLAS PUGUH resources.

## Access Control Layers

PUGUH provides multiple layers of access control:

1. **Tenant Isolation**: Each tenant's data is completely separate
2. **Role-Based Access**: Permissions determined by user role
3. **Project Scoping**: Resources can be scoped to specific projects
4. **Rule-Level Access**: Fine-grained control on individual resources

## Service Accounts

Service accounts are non-human identities for integrations.

### Creating a Service Account

1. Go to **IAM > Service Accounts**
2. Click **"Create Service Account"**
3. Enter a name and description
4. Select the role/permissions
5. Click **"Create"**

You'll receive an API key - **save it securely**, as it won't be shown again.

### Service Account Best Practices

- **One per integration**: Don't share service accounts
- **Minimal permissions**: Only grant what's needed
- **Rotate regularly**: Update API keys periodically
- **Monitor usage**: Watch for unusual activity
- **Descriptive names**: "ci-pipeline-prod" not "sa-1"

### Rotating API Keys

1. Go to **IAM > Service Accounts**
2. Click on the service account
3. Click **"Rotate Key"**
4. Update your integration with the new key
5. The old key is invalidated immediately

## IP Allowlisting (Enterprise)

Enterprise plans can restrict access by IP address.

### Configuring IP Allowlist

1. Go to **Tenant > Settings > Security**
2. Enable **"IP Allowlist"**
3. Add allowed IP addresses or CIDR ranges
4. Click **"Save"**

```
Examples:
- Single IP: 203.0.113.50
- CIDR range: 10.0.0.0/8
- Office network: 192.168.1.0/24
```

:::warning
Be careful when enabling IP allowlist. Incorrect settings can lock you out. Always include your current IP.
:::

## API Key Management

### API Key Types

| Type | Use Case | Permissions |
|------|----------|-------------|
| **Personal** | Developer testing | User's permissions |
| **Service** | Production integrations | Configured permissions |
| **Project** | Project-specific access | Limited to one project |

### Creating Personal API Keys

1. Click your profile icon
2. Select **"API Keys"**
3. Click **"Create Key"**
4. Enter a name for the key
5. Click **"Create"**

Personal keys inherit your user permissions.

### Key Expiration

Set expiration for added security:
- No expiration (not recommended)
- 30 days
- 90 days
- 1 year

Expired keys stop working automatically.

## OAuth Applications (Enterprise)

Enterprise plans can register OAuth applications for SSO.

### Registering an OAuth App

1. Go to **Tenant > Settings > OAuth**
2. Click **"Register Application"**
3. Configure:
   - Application name
   - Redirect URIs
   - Scopes requested
4. Click **"Register"**

You'll receive a Client ID and Client Secret.

### OAuth Scopes

| Scope | Access |
|-------|--------|
| `read:user` | Read user profile |
| `read:tenant` | Read tenant info |
| `read:resources` | Read rules, workflows |
| `write:resources` | Create/update resources |
| `admin` | Full admin access |

## Session Management

### Active Sessions

View and manage your active sessions:

1. Click your profile icon
2. Select **"Sessions"**
3. See all active sessions with:
   - Device/browser
   - Location (approximate)
   - Last activity

### Revoking Sessions

Click **"Revoke"** to end a session:
- Useful if you lose a device
- Immediately logs out that session
- Doesn't affect other sessions

### Session Settings (Admin)

Admins can configure session policies:

| Setting | Description |
|---------|-------------|
| **Session timeout** | Auto-logout after inactivity |
| **Max sessions** | Limit concurrent sessions |
| **Require 2FA** | Enforce two-factor auth |

## Two-Factor Authentication

### Enabling 2FA

1. Click your profile icon
2. Select **"Security"**
3. Click **"Enable 2FA"**
4. Scan QR code with authenticator app
5. Enter verification code
6. Save backup codes securely

### Backup Codes

Backup codes let you log in if you lose your authenticator:
- 10 single-use codes generated
- Store them securely offline
- Each code works once only

### Recovery

If you lose access to both authenticator and backup codes:
1. Contact your tenant admin
2. Admin can reset your 2FA
3. You'll need to set it up again

## Audit Logging

All access control changes are logged:

- User role changes
- Service account creation/deletion
- API key rotation
- Login attempts (success/failure)
- Permission changes

View logs at **Control > Audit Trail**.

## Security Recommendations

1. **Enable 2FA**: For all admin users at minimum
2. **Use Service Accounts**: For integrations, not personal keys
3. **Regular Audits**: Review access quarterly
4. **Principle of Least Privilege**: Minimal necessary access
5. **Monitor Anomalies**: Watch for unusual patterns

## Related

- [Users](/docs/user-guides/iam/users)
- [Roles](/docs/user-guides/iam/roles)
- [Permissions](/docs/user-guides/iam/permissions)
- [API Authentication](/docs/api-reference/authentication)
