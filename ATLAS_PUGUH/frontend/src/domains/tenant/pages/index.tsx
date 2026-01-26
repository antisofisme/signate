/**
 * Tenant Domain - Page Exports
 * Following ATLAS_PANDAWA standards
 */

import { useParams, useNavigate } from 'react-router-dom'
import { DomainPage, ReadOnlyNotice } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Separator } from '@/components/ui/separator'
import {
  Building2,
  Users,
  Shield,
  Calendar,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react'

// ============================================
// Mock Data
// ============================================

const mockTenants = [
  {
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Acme Corp',
    slug: 'acme-corp',
    status: 'active' as const,
    memberCount: 15,
    createdAt: '2026-01-01T00:00:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    name: 'TechStart Inc',
    slug: 'techstart',
    status: 'active' as const,
    memberCount: 8,
    createdAt: '2026-01-15T00:00:00Z',
  },
]

const mockTenantDetail = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  name: 'Acme Corp',
  slug: 'acme-corp',
  status: 'active' as const,
  memberCount: 15,
  createdAt: '2026-01-01T00:00:00Z',
  settings: {
    timezone: 'Asia/Jakarta',
    currency: 'IDR',
    language: 'id',
  },
}

const mockMembers = [
  { id: '1', userId: '1', userName: 'Admin User', userEmail: 'admin@acme.com', role: 'ADMIN', joinedAt: '2026-01-01T00:00:00Z' },
  { id: '2', userId: '2', userName: 'Operator 1', userEmail: 'op1@acme.com', role: 'OPERATOR', joinedAt: '2026-01-05T00:00:00Z' },
  { id: '3', userId: '3', userName: 'Viewer 1', userEmail: 'viewer@acme.com', role: 'VIEWER', joinedAt: '2026-01-10T00:00:00Z' },
]

const mockIsolationChecks: Array<{ name: string; status: 'passed' | 'failed' | 'warning'; message: string }> = [
  { name: 'Database Row-Level Security', status: 'passed', message: 'All tables have tenant_id filters' },
  { name: 'API Tenant Context', status: 'passed', message: 'X-Tenant-ID header validated on all requests' },
  { name: 'File Storage Isolation', status: 'passed', message: 'Tenant-scoped storage paths enforced' },
  { name: 'Cache Key Isolation', status: 'passed', message: 'All cache keys include tenant prefix' },
  { name: 'Audit Log Separation', status: 'passed', message: 'Audit logs properly scoped to tenant' },
]

// ============================================
// Tenant List Page
// ============================================

export function TenantList() {
  const navigate = useNavigate()

  return (
    <DomainPage
      domain="tenant"
      title="Tenants"
      description="View tenant information"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="tenant" />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockTenants.map((tenant) => (
          <Card
            key={tenant.id}
            className="cursor-pointer hover:border-tenant/50 transition-colors"
            onClick={() => navigate(`/tenant/${tenant.id}`)}
          >
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-tenant" />
                  {tenant.name}
                </div>
                <Badge variant={tenant.status === 'active' ? 'success' : 'secondary'}>
                  {tenant.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm text-muted-foreground font-mono">{tenant.slug}</p>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Users className="h-4 w-4" />
                {tenant.memberCount} members
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Calendar className="h-3 w-3" />
                Created {new Date(tenant.createdAt).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </DomainPage>
  )
}

// ============================================
// Tenant Detail Page
// ============================================

export function TenantDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <DomainPage
      domain="tenant"
      title={mockTenantDetail.name}
      description={`Tenant ID: ${id}`}
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      backTo="/tenant/list"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tenant Info */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Tenant Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-muted-foreground">Name</label>
                <p className="font-medium">{mockTenantDetail.name}</p>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Slug</label>
                <p className="font-mono">{mockTenantDetail.slug}</p>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Status</label>
                <div className="mt-1">
                  <Badge variant="success">{mockTenantDetail.status}</Badge>
                </div>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Members</label>
                <p className="font-medium">{mockTenantDetail.memberCount}</p>
              </div>
            </div>

            <Separator />

            <div>
              <h4 className="font-medium mb-2">Settings</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <label className="text-muted-foreground">Timezone</label>
                  <p>{mockTenantDetail.settings.timezone}</p>
                </div>
                <div>
                  <label className="text-muted-foreground">Currency</label>
                  <p>{mockTenantDetail.settings.currency}</p>
                </div>
                <div>
                  <label className="text-muted-foreground">Language</label>
                  <p>{mockTenantDetail.settings.language}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Links</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate(`/tenant/${id}/members`)}
            >
              <Users className="h-4 w-4 mr-2" />
              View Members
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate('/tenant/isolation-check')}
            >
              <Shield className="h-4 w-4 mr-2" />
              Isolation Check
            </Button>
          </CardContent>
        </Card>
      </div>
    </DomainPage>
  )
}

// ============================================
// Tenant Members Page
// ============================================

export function TenantMembers() {
  const { id } = useParams<{ id: string }>()

  return (
    <DomainPage
      domain="tenant"
      title="Tenant Members"
      description={`Members of ${mockTenantDetail.name}`}
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      backTo={`/tenant/${id}`}
    >
      <ReadOnlyNotice domain="tenant" />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Members ({mockMembers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Joined</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockMembers.map((member) => (
                <TableRow key={member.id}>
                  <TableCell className="font-medium">{member.userName}</TableCell>
                  <TableCell className="text-muted-foreground">{member.userEmail}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{member.role}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(member.joinedAt).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Isolation Check Page
// ============================================

export function IsolationCheck() {
  const allPassed = mockIsolationChecks.every((c) => c.status === 'passed')

  return (
    <DomainPage
      domain="tenant"
      title="Isolation Check"
      description="Verify tenant data isolation"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="tenant" />

      {/* Summary */}
      <Card className={allPassed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
        <CardContent className="py-6">
          <div className="flex items-center gap-4">
            {allPassed ? (
              <CheckCircle className="h-12 w-12 text-green-600" />
            ) : (
              <XCircle className="h-12 w-12 text-red-600" />
            )}
            <div>
              <h2 className="text-xl font-semibold">
                {allPassed ? 'All Checks Passed' : 'Some Checks Failed'}
              </h2>
              <p className="text-muted-foreground">
                {allPassed
                  ? 'Tenant data isolation is properly configured.'
                  : 'Please review the failed checks below.'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Check Results */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Isolation Checks
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockIsolationChecks.map((check, index) => (
              <div
                key={index}
                className="flex items-start gap-4 p-4 rounded-lg border"
              >
                {check.status === 'passed' && (
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                )}
                {check.status === 'failed' && (
                  <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                )}
                {check.status === 'warning' && (
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                )}
                <div>
                  <h4 className="font-medium">{check.name}</h4>
                  <p className="text-sm text-muted-foreground">{check.message}</p>
                </div>
                <Badge
                  variant={
                    check.status === 'passed'
                      ? 'success'
                      : check.status === 'failed'
                      ? 'destructive'
                      : 'warning'
                  }
                  className="ml-auto"
                >
                  {check.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </DomainPage>
  )
}
