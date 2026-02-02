---
sidebar_position: 3
---

# Create Your First Project

**Projects** help you organize rules, workflows, and decisions within a tenant. They're ideal for separating environments (production/staging) or different applications.

## Understanding Projects

Projects provide an additional layer of organization:

```
Tenant (Acme Corp)
├── Project: Production
│   ├── Rules for live environment
│   ├── Production workflows
│   └── Decision history
├── Project: Staging
│   ├── Test rules
│   └── Development workflows
└── Project: Mobile App
    ├── App-specific rules
    └── Mobile workflows
```

## Creating a Project

### Via the Dashboard

1. Navigate to your tenant's dashboard
2. Click **"Projects"** in the sidebar or header
3. Click **"New Project"**
4. Fill in the project details:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Descriptive project name | "Production API" |
| **Slug** | URL identifier | "production-api" |
| **Environment** | Type of environment | Production/Staging/Development |
| **Description** | Optional details | "Main production rules" |

5. Click **"Create Project"**

### Via API

```bash
curl -X POST https://api.puguh.arsaka.io/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API",
    "slug": "production-api",
    "environment": "production",
    "description": "Main production rules"
  }'
```

## Project Environments

We recommend using environments to separate concerns:

| Environment | Purpose | Characteristics |
|-------------|---------|-----------------|
| **Production** | Live traffic | Strict change control, monitoring |
| **Staging** | Pre-production testing | Mirrors production, safe to test |
| **Development** | Active development | Frequent changes, experimentation |

:::warning
Be careful when modifying rules in Production projects. Always test in Staging first.
:::

## Project Scoping

Resources can be scoped at two levels:

### Tenant-Level Resources
- Shared across all projects in the tenant
- Useful for company-wide policies
- Example: "All transactions over $100K require CFO approval"

### Project-Level Resources
- Isolated to a specific project
- Environment-specific configurations
- Example: "Staging allows higher risk scores for testing"

When creating a rule, you can choose the scope:

```
Scope: [Tenant-wide] or [This Project Only]
```

## Project Limits by Plan

| Plan | Max Projects |
|------|--------------|
| Free | 1 |
| Starter | 5 |
| Pro | Unlimited |
| Enterprise | Unlimited |

## Switching Between Projects

If your tenant has multiple projects:

1. Use the project selector in the header (next to tenant)
2. Or navigate via **Projects** in the sidebar
3. The URL updates to reflect the project: `/app/{tenant}/{project}/...`

## Project Settings

Access project settings via the project's gear icon or settings page:

- **General**: Name, description, environment type
- **Access**: Who can access this project
- **API Keys**: Project-specific API credentials
- **Danger Zone**: Delete project

:::caution
Deleting a project removes all its rules, workflows, and decision history. This cannot be undone.
:::

## Best Practices

### 1. Separate by Environment
Create distinct projects for production, staging, and development.

### 2. Use Meaningful Names
Name projects clearly: "Backend API - Production" is better than "Project 1".

### 3. Limit Production Access
Restrict who can modify production project rules.

### 4. Test Before Promoting
Always test rules in staging/dev before activating in production.

## Next Steps

With your project created:

- [Create your first rule](/docs/getting-started/first-rule) within the project
- [Set up workflows](/docs/user-guides/workflows/creating) for approval processes
- [Configure project access](/docs/user-guides/iam/access-control) for team members
