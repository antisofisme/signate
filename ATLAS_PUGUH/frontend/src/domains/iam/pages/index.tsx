/**
 * IAM Domain - Page Exports
 * Following ATLAS_PANDAWA standards
 */

export { UserList } from './UserList'
export { UserDetail } from './UserDetail'
export { RoleList } from './RoleList'

import { DomainPage, ReadOnlyNotice } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useParams } from 'react-router-dom'
import { Shield, Key, Server, Check, X } from 'lucide-react'

// ============================================
// Role Detail Page
// ============================================

const mockRoleDetail = {
  id: '1',
  name: 'ADMIN',
  description: 'Full administrative access within tenant',
  permissions: [
    { code: 'users:read', name: 'View Users', granted: true },
    { code: 'users:write', name: 'Manage Users', granted: true },
    { code: 'roles:read', name: 'View Roles', granted: true },
    { code: 'roles:write', name: 'Manage Roles', granted: false },
    { code: 'workflow:read', name: 'View Workflows', granted: true },
    { code: 'workflow:approve', name: 'Approve Workflows', granted: true },
    { code: 'decision:read', name: 'View Decisions', granted: true },
    { code: 'decision:create', name: 'Create Decisions', granted: true },
  ],
  userCount: 5,
  createdAt: '2026-01-01T00:00:00Z',
}

export function RoleDetail() {
  const { id: _roleId } = useParams<{ id: string }>()

  return (
    <DomainPage
      domain="iam"
      title={`Role: ${mockRoleDetail.name}`}
      description={mockRoleDetail.description}
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      backTo="/iam/roles"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Role Info */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Role Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-muted-foreground">Role Name</label>
                <p className="font-medium">{mockRoleDetail.name}</p>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Users Assigned</label>
                <p className="font-medium">{mockRoleDetail.userCount}</p>
              </div>
              <div className="col-span-2">
                <label className="text-sm text-muted-foreground">Description</label>
                <p className="font-medium">{mockRoleDetail.description}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Permission Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Total Permissions</span>
                <span className="font-medium">{mockRoleDetail.permissions.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Granted</span>
                <span className="font-medium text-green-600">
                  {mockRoleDetail.permissions.filter((p) => p.granted).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Denied</span>
                <span className="font-medium text-red-600">
                  {mockRoleDetail.permissions.filter((p) => !p.granted).length}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Permissions List */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Permissions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {mockRoleDetail.permissions.map((perm) => (
                <div
                  key={perm.code}
                  className={`p-3 rounded-lg border ${
                    perm.granted ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm">{perm.code}</span>
                    {perm.granted ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <X className="h-4 w-4 text-red-600" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{perm.name}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DomainPage>
  )
}

// ============================================
// Service Accounts Page
// ============================================

const mockServiceAccounts = [
  {
    id: '1',
    name: 'api-integration',
    description: 'External API integration service',
    clientId: 'svc_abc123',
    permissions: ['api:read', 'api:write'],
    lastUsedAt: '2026-01-24T10:00:00Z',
    status: 'active',
  },
  {
    id: '2',
    name: 'webhook-processor',
    description: 'Webhook event processor',
    clientId: 'svc_def456',
    permissions: ['webhook:process'],
    lastUsedAt: '2026-01-23T15:30:00Z',
    status: 'active',
  },
]

export function ServiceAccounts() {
  return (
    <DomainPage
      domain="iam"
      title="Service Accounts"
      description="View service accounts and API credentials"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="iam" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {mockServiceAccounts.map((account) => (
          <Card key={account.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-iam" />
                  {account.name}
                </div>
                <Badge variant={account.status === 'active' ? 'success' : 'secondary'}>
                  {account.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">{account.description}</p>

              <div>
                <label className="text-xs text-muted-foreground">Client ID</label>
                <p className="font-mono text-sm bg-muted px-2 py-1 rounded">
                  {account.clientId}
                </p>
              </div>

              <div>
                <label className="text-xs text-muted-foreground">Permissions</label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {account.permissions.map((perm) => (
                    <Badge key={perm} variant="outline" className="text-xs font-mono">
                      {perm}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="text-xs text-muted-foreground">
                Last used: {new Date(account.lastUsedAt).toLocaleString()}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </DomainPage>
  )
}

// ============================================
// Permission Matrix Page
// ============================================

const mockPermissionMatrix = {
  roles: ['ADMIN', 'OPERATOR', 'VIEWER'],
  modules: [
    {
      name: 'IAM',
      permissions: [
        { code: 'users:read', roles: { ADMIN: true, OPERATOR: true, VIEWER: true } },
        { code: 'users:write', roles: { ADMIN: true, OPERATOR: false, VIEWER: false } },
        { code: 'roles:read', roles: { ADMIN: true, OPERATOR: true, VIEWER: true } },
      ],
    },
    {
      name: 'Workflow',
      permissions: [
        { code: 'workflow:read', roles: { ADMIN: true, OPERATOR: true, VIEWER: true } },
        { code: 'workflow:approve', roles: { ADMIN: true, OPERATOR: true, VIEWER: false } },
        { code: 'workflow:reject', roles: { ADMIN: true, OPERATOR: true, VIEWER: false } },
      ],
    },
    {
      name: 'Decision',
      permissions: [
        { code: 'decision:read', roles: { ADMIN: true, OPERATOR: true, VIEWER: true } },
        { code: 'decision:create', roles: { ADMIN: true, OPERATOR: true, VIEWER: false } },
      ],
    },
  ],
}

export function PermissionMatrix() {
  return (
    <DomainPage
      domain="iam"
      title="Permission Matrix"
      description="View all permissions across roles"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="iam" />

      <Card>
        <CardContent className="pt-6 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-3 font-medium">Permission</th>
                {mockPermissionMatrix.roles.map((role) => (
                  <th key={role} className="text-center py-2 px-3 font-medium">
                    {role}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {mockPermissionMatrix.modules.map((module) => (
                <>
                  <tr key={module.name} className="bg-muted/50">
                    <td
                      colSpan={mockPermissionMatrix.roles.length + 1}
                      className="py-2 px-3 font-semibold"
                    >
                      {module.name}
                    </td>
                  </tr>
                  {module.permissions.map((perm) => (
                    <tr key={perm.code} className="border-b">
                      <td className="py-2 px-3 font-mono text-xs">{perm.code}</td>
                      {mockPermissionMatrix.roles.map((role) => (
                        <td key={role} className="text-center py-2 px-3">
                          {perm.roles[role as keyof typeof perm.roles] ? (
                            <Check className="h-4 w-4 text-green-600 mx-auto" />
                          ) : (
                            <X className="h-4 w-4 text-red-400 mx-auto" />
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </DomainPage>
  )
}
