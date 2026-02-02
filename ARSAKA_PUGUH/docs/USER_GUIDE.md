# ARSAKA_PUGUH User Guide

Welcome to ARSAKA_PUGUH - the Constitutional Law System for AI Decisions.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Organizations (Tenants)](#organizations-tenants)
4. [Projects](#projects)
5. [Billing & Subscriptions](#billing--subscriptions)
6. [Core Features](#core-features)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Internet connection

### Quick Start

1. **Register** at `/register` with your email
2. **Verify** your email via the link sent to your inbox
3. **Login** at `/login`
4. **Create** your first organization and project
5. **Start** using the decision engine

---

## Authentication

### Registration

1. Navigate to `/register`
2. Enter your email and password
3. Complete the form with your name
4. Click "Create Account"
5. Check your email for verification link
6. Click the link to verify your email

### Login

1. Navigate to `/login`
2. Enter your email and password
3. Click "Sign In"
4. You'll be redirected to the dashboard

### OAuth Login (Google/GitHub)

1. Click "Continue with Google" or "Continue with GitHub"
2. Authorize ARSAKA_PUGUH to access your account
3. You'll be automatically logged in

### Password Reset

1. Navigate to `/forgot-password`
2. Enter your email
3. Click "Send Reset Link"
4. Check your email and click the reset link
5. Enter your new password

---

## Organizations (Tenants)

Organizations (also called "tenants") are the top-level grouping for all your resources.

### Creating an Organization

1. After registration, your first organization is created automatically
2. To create additional organizations:
   - Click your profile menu
   - Select "Create Organization"
   - Enter organization name
   - Click "Create"

### Managing Members

1. Navigate to Organization Settings
2. Click "Members" tab
3. Click "Invite Member"
4. Enter email and select role:
   - **Owner**: Full control, billing access
   - **Admin**: Full control, no billing
   - **Member**: Create/edit resources
   - **Viewer**: Read-only access

### Switching Organizations

1. Click the organization selector in the header
2. Choose the organization you want to work with

---

## Projects

Projects provide resource isolation within an organization.

### Creating a Project

1. Navigate to Projects page (`/app/{org}/projects`)
2. Click "New Project"
3. Enter:
   - **Name**: Display name for the project
   - **Description**: Optional description
   - **Environment**: Development, Testing, Staging, or Production
4. Click "Create Project"

### Project Environments

| Environment | Purpose |
|-------------|---------|
| **Development** | Local development and experimentation |
| **Testing** | Automated testing and QA |
| **Staging** | Pre-production validation |
| **Production** | Live production workloads |

### Project Members

Projects can have their own member list for fine-grained access control:

- If no project members are defined, all organization members have access
- Add project-specific members to restrict access
- Project roles: Admin, Member, Viewer

---

## Billing & Subscriptions

### Subscription Plans

| Plan | Price (IDR) | Projects | Decisions/mo | Team Members |
|------|-------------|----------|--------------|--------------|
| **Free** | 0 | 1 | 1,000 | 3 |
| **Starter** | 290,000/mo | 5 | 10,000 | 10 |
| **Pro** | 990,000/mo | Unlimited | 100,000 | Unlimited |
| **Enterprise** | Custom | Custom | Custom | Custom |

### Upgrading Your Plan

1. Navigate to Billing (`/app/billing`)
2. Click "Upgrade Plan"
3. Select your desired plan
4. Complete payment via Midtrans
5. Your plan is upgraded immediately

### Payment Methods

Supported via Midtrans:
- Credit/Debit Cards (Visa, Mastercard)
- GoPay
- OVO
- Bank Transfer (BCA, BNI, Mandiri, etc.)

### Viewing Invoices

1. Navigate to Billing > Invoices (`/app/billing/invoices`)
2. View all past invoices
3. Click "Download" for PDF receipt

---

## Core Features

### 1. IAM (Identity & Access Management)

View and manage users, roles, and permissions.

- **Users**: View all users in your organization
- **Roles**: View defined roles and their permissions
- **Service Accounts**: API access for integrations
- **Permission Matrix**: Visual permission overview

### 2. Decision Engine

Create and manage decision rules.

- **Rules**: Define decision logic
- **Rule Versions**: Track rule changes
- **Decision Types**: Categorize decisions
- **Decision History**: Audit all decisions made

### 3. Workflow

Manage approval workflows.

- **My Pending**: Items waiting for your approval
- **All Workflows**: View all workflow instances
- **Escalations**: Handle escalated items

### 4. Control Panel

Monitor system health and audit trail.

- **Audit Trail**: Complete audit log
- **Event Timeline**: System events
- **DLQ View**: Dead letter queue (failed events)
- **Metrics Dashboard**: Performance metrics

---

## API Reference

### Base URL

```
Production: https://api.puguh.arsaka.io
Development: http://localhost:8001
```

### Authentication

Include JWT token in Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Common Endpoints

#### Auth
```
POST /api/v1/auth/register    # Register new user
POST /api/v1/auth/login       # Login
POST /api/v1/auth/refresh     # Refresh token
POST /api/v1/auth/logout      # Logout
```

#### Tenants
```
GET  /api/v1/tenants          # List tenants
POST /api/v1/tenants          # Create tenant
GET  /api/v1/tenants/{id}     # Get tenant
PATCH /api/v1/tenants/{id}    # Update tenant
```

#### Projects
```
GET  /api/v1/projects?tenant_id=...         # List projects
POST /api/v1/projects?tenant_id=...         # Create project
GET  /api/v1/projects/{id}?tenant_id=...    # Get project
PATCH /api/v1/projects/{id}?tenant_id=...   # Update project
DELETE /api/v1/projects/{id}?tenant_id=...  # Delete project
```

#### Billing
```
GET  /api/v1/billing/plans                  # List plans
GET  /api/v1/billing/subscription           # Current subscription
POST /api/v1/billing/checkout               # Create checkout
GET  /api/v1/billing/invoices               # List invoices
```

### Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "meta": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

---

## Troubleshooting

### Login Issues

**"Invalid credentials"**
- Verify email and password are correct
- Check if account exists (try password reset)
- Ensure email is verified

**"Email not verified"**
- Check spam folder for verification email
- Request new verification email at `/verify-email`

### Billing Issues

**"Payment failed"**
- Verify payment method has sufficient funds
- Try a different payment method
- Contact support if issue persists

**"Plan limit exceeded"**
- Upgrade to a higher plan
- Delete unused projects/resources
- Contact sales for enterprise pricing

### Performance Issues

**"Slow loading"**
- Check internet connection
- Clear browser cache
- Try incognito/private mode

**"API timeout"**
- Retry the request
- Check system status page
- Contact support if persistent

### Getting Help

- **Documentation**: `/docs`
- **API Status**: `/health`
- **Support Email**: support@arsaka.io
- **GitHub Issues**: [Report bugs](https://github.com/arsaka/arsaka-puguh/issues)

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Quick search |
| `G then D` | Go to Dashboard |
| `G then P` | Go to Projects |
| `G then B` | Go to Billing |
| `?` | Show help |

---

## Security Best Practices

1. **Use strong passwords** (12+ characters, mix of types)
2. **Enable OAuth** for easier, more secure login
3. **Review member access** regularly
4. **Use project isolation** for sensitive workloads
5. **Monitor audit logs** for suspicious activity
6. **Keep API keys secure** - never commit to git

---

*Last updated: January 2026*
