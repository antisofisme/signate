/**
 * Help Content Database
 * Contextual help articles for in-app assistance
 */

export interface HelpArticle {
  id: string
  title: string
  content: string
  pages: string[] // Pages where this article is relevant
  tags: string[]
  docsUrl?: string // Link to Docusaurus page
  priority?: number // Higher = shown first
}

export const helpArticles: HelpArticle[] = [
  // ============================================
  // Dashboard Help
  // ============================================
  {
    id: 'dashboard-overview',
    title: 'Dashboard Overview',
    content: `
The Dashboard provides a quick overview of your PUGUH system:

**Service Cards**
Click any of the 5 service cards to navigate to that domain:
- IAM: User and role management
- Tenant: Organization settings
- Decision: Rules and decision history
- Workflow: Approval processes
- Control: Audit logs and events

**Quick Stats**
View real-time statistics for decisions, rules, and workflows.

**Recent Activity**
See the latest actions across your tenant.
    `.trim(),
    pages: ['/app', '/app/'],
    tags: ['dashboard', 'overview', 'getting-started'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/',
    priority: 100,
  },

  // ============================================
  // Rules Help
  // ============================================
  {
    id: 'rule-basics',
    title: 'Creating Your First Rule',
    content: `
Rules define conditions and actions for your decision engine.

**Steps to Create a Rule:**
1. Click "Create Rule" button
2. Set a descriptive name
3. Add conditions using the visual builder
4. Define actions (allow, deny, flag)
5. Test with sample data
6. Request activation when ready

**Rule States:**
- Draft: Being edited
- Pending: Awaiting approval
- Active: Live and evaluating
- Deprecated: Being phased out
    `.trim(),
    pages: ['/app/decision/rules', '/app/decision/rules/new'],
    tags: ['rules', 'getting-started', 'decision'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/getting-started/first-rule',
    priority: 90,
  },
  {
    id: 'rule-conditions',
    title: 'Rule Conditions Explained',
    content: `
Conditions determine when a rule applies.

**Operators:**
- \`equals\`, \`not_equals\`: Exact match
- \`greater_than\`, \`less_than\`: Numeric comparison
- \`contains\`, \`starts_with\`: String matching
- \`in\`, \`not_in\`: List membership
- \`is_null\`, \`is_not_null\`: Null checks

**Logical Operators:**
- \`ALL\`: Every condition must be true (AND)
- \`ANY\`: At least one must be true (OR)
- \`NOT\`: Negate a condition

**Example:**
\`amount > 1000 AND department = "sales"\`
    `.trim(),
    pages: ['/app/decision/rules', '/app/decision/rules/new'],
    tags: ['rules', 'conditions', 'operators'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/decisions/rule-builder',
    priority: 80,
  },
  {
    id: 'rule-versioning',
    title: 'Rule Versioning',
    content: `
Every rule change creates a new version for audit purposes.

**Version Features:**
- View complete version history
- Compare versions side-by-side
- Rollback to previous versions
- Track who made each change

**Best Practices:**
- Add meaningful descriptions to changes
- Test new versions before activating
- Use staging projects for experiments
    `.trim(),
    pages: ['/app/decision/rules'],
    tags: ['rules', 'versioning', 'history'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/decisions/versioning',
    priority: 70,
  },

  // ============================================
  // Workflow Help
  // ============================================
  {
    id: 'workflow-overview',
    title: 'Understanding Workflows',
    content: `
Workflows manage multi-step approval processes.

**Workflow States:**
- Pending: Awaiting action
- Approved: Completed successfully
- Rejected: Declined
- Escalated: Moved to higher authority
- Delegated: Reassigned to another

**Actions You Can Take:**
- Approve: Complete the workflow
- Reject: Decline with reason
- Delegate: Assign to someone else
- Escalate: Move to supervisor
    `.trim(),
    pages: ['/app/workflow', '/app/workflow/pending', '/app/workflow/all'],
    tags: ['workflow', 'approval', 'getting-started'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/workflows/creating',
    priority: 90,
  },
  {
    id: 'workflow-triggers',
    title: 'Workflow Triggers',
    content: `
Triggers start workflows automatically:

**Trigger Types:**
- **Rule Match**: When a rule evaluates to REQUIRE_APPROVAL
- **Schedule**: Time-based (cron expressions)
- **Webhook**: External HTTP call
- **Manual**: User-initiated

**Configuration:**
Set triggers when creating rules or via the workflow builder.
    `.trim(),
    pages: ['/app/workflow'],
    tags: ['workflow', 'triggers', 'automation'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/workflows/triggers',
    priority: 80,
  },

  // ============================================
  // IAM Help
  // ============================================
  {
    id: 'iam-users',
    title: 'Managing Users',
    content: `
Users represent people or services with access to your tenant.

**User Types:**
- Human users: Team members with email/OAuth
- Service accounts: API-only access for integrations

**User Actions:**
- Invite: Send email invitation
- Suspend: Temporarily disable access
- Remove: Revoke membership entirely

**Permissions:**
Managed via Roles assigned to users.
    `.trim(),
    pages: ['/app/iam/users', '/app/iam'],
    tags: ['iam', 'users', 'management'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/iam/users',
    priority: 90,
  },
  {
    id: 'iam-roles',
    title: 'Roles & Permissions',
    content: `
Roles define what actions users can perform.

**Built-in Roles:**
- **Owner**: Full control, billing access
- **Admin**: Manage resources and members
- **Member**: Create and edit resources
- **Viewer**: Read-only access

**Custom Roles:**
Pro and Enterprise plans can create custom roles with fine-grained permissions.

**Permission Format:**
\`{domain}.{resource}.{action}\`
Example: \`decision.rules.create\`
    `.trim(),
    pages: ['/app/iam/roles', '/app/iam/permissions'],
    tags: ['iam', 'roles', 'permissions', 'rbac'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/iam/roles',
    priority: 85,
  },

  // ============================================
  // Tenant Help
  // ============================================
  {
    id: 'tenant-overview',
    title: 'Tenant Management',
    content: `
A Tenant represents your organization within PUGUH.

**Tenant Features:**
- Isolated data and rules
- Team member management
- Subscription and billing
- Multiple projects

**Switching Tenants:**
Use the tenant selector in the header to switch between organizations you belong to.
    `.trim(),
    pages: ['/app/tenant', '/app/tenant/list'],
    tags: ['tenant', 'organization', 'management'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/getting-started/first-tenant',
    priority: 90,
  },
  {
    id: 'tenant-members',
    title: 'Managing Team Members',
    content: `
Invite and manage team members in your tenant.

**Inviting Members:**
1. Go to Tenant > Members
2. Click "Invite Member"
3. Enter email and select role
4. Click "Send Invitation"

**Member Roles:**
- Owner: Full control
- Admin: Manage resources
- Member: Create/edit
- Viewer: Read-only
    `.trim(),
    pages: ['/app/tenant', '/app/tenant/members'],
    tags: ['tenant', 'members', 'invite', 'team'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/getting-started/first-tenant#inviting-team-members',
    priority: 85,
  },

  // ============================================
  // Control/Audit Help
  // ============================================
  {
    id: 'audit-trail',
    title: 'Understanding Audit Trails',
    content: `
Audit trails record all significant actions in your system.

**What's Recorded:**
- Rule changes
- Decision outcomes
- Workflow actions
- User management
- Configuration changes

**Filtering:**
- By date range
- By user
- By action type
- By resource

**Retention:**
Depends on your plan (7 days to 1 year+).
    `.trim(),
    pages: ['/app/control/audit', '/app/control'],
    tags: ['audit', 'control', 'compliance', 'logging'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/control/environments',
    priority: 90,
  },
  {
    id: 'event-timeline',
    title: 'Event Timeline',
    content: `
The Event Timeline shows real-time system events.

**Event Types:**
- Decision events (evaluated, approved, denied)
- Workflow events (created, completed)
- System events (deployments, errors)

**Use Cases:**
- Debug rule behavior
- Track decision flow
- Monitor system health
    `.trim(),
    pages: ['/app/control/events'],
    tags: ['events', 'timeline', 'monitoring'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/user-guides/control/deployment',
    priority: 80,
  },

  // ============================================
  // Billing Help
  // ============================================
  {
    id: 'billing-plans',
    title: 'Subscription Plans',
    content: `
Choose the plan that fits your needs:

| Plan | Projects | Decisions/mo | Price |
|------|----------|--------------|-------|
| Free | 1 | 1,000 | Rp 0 |
| Starter | 5 | 10,000 | Rp 290K |
| Pro | Unlimited | 100,000 | Rp 990K |
| Enterprise | Custom | Custom | Contact |

**Upgrading:**
Go to Billing Settings to upgrade your plan anytime.
    `.trim(),
    pages: ['/app/billing', '/pricing'],
    tags: ['billing', 'plans', 'pricing', 'subscription'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/',
    priority: 90,
  },
  {
    id: 'billing-invoices',
    title: 'Invoice History',
    content: `
View and download your payment history.

**Invoice Details:**
- Invoice number and date
- Plan and period
- Amount paid
- Payment method
- Download PDF

**Payment Methods:**
- Credit/Debit cards
- GoPay, OVO
- Bank transfer
    `.trim(),
    pages: ['/app/billing/invoices', '/app/billing'],
    tags: ['billing', 'invoices', 'payment'],
    docsUrl: 'https://docs.puguh.atlashub.com/docs/',
    priority: 80,
  },
]

/**
 * Get help articles relevant to the current page
 */
export function getArticlesForPage(page: string, query?: string): HelpArticle[] {
  let articles = helpArticles.filter((article) =>
    article.pages.some((p) => page.includes(p) || page.startsWith(p.replace('*', '')))
  )

  // Apply search filter if query provided
  if (query && query.trim()) {
    const q = query.toLowerCase().trim()
    articles = articles.filter(
      (article) =>
        article.title.toLowerCase().includes(q) ||
        article.content.toLowerCase().includes(q) ||
        article.tags.some((tag) => tag.includes(q))
    )
  }

  // Sort by priority (higher first), then by title
  return articles.sort((a, b) => {
    const priorityDiff = (b.priority || 0) - (a.priority || 0)
    if (priorityDiff !== 0) return priorityDiff
    return a.title.localeCompare(b.title)
  })
}

/**
 * Search all articles by query
 */
export function searchArticles(query: string): HelpArticle[] {
  if (!query || !query.trim()) return []

  const q = query.toLowerCase().trim()
  return helpArticles
    .filter(
      (article) =>
        article.title.toLowerCase().includes(q) ||
        article.content.toLowerCase().includes(q) ||
        article.tags.some((tag) => tag.includes(q))
    )
    .sort((a, b) => (b.priority || 0) - (a.priority || 0))
}

/**
 * Get article by ID
 */
export function getArticleById(id: string): HelpArticle | undefined {
  return helpArticles.find((article) => article.id === id)
}
