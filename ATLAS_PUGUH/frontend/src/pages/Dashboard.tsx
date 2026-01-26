/**
 * Dashboard - Home Page
 * Overview of all 5 domains
 * Using consistent styling with DomainPage
 */

import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Users,
  Building2,
  Scale,
  CheckCircle,
  BarChart3,
  ArrowRight,
  Clock,
  AlertTriangle,
  Activity,
  FileText,
  Shield,
  TrendingUp,
  LayoutDashboard,
} from 'lucide-react'

// Domain configurations
const domains = [
  {
    name: 'IAM',
    path: '/iam',
    icon: Users,
    color: 'bg-iam',
    textColor: 'text-iam',
    borderColor: 'border-l-iam',
    description: 'Identity & Access Management',
    features: ['Users', 'Roles', 'Permissions', 'Service Accounts'],
    badge: 'READ-ONLY',
    badgeVariant: 'info' as const,
    stats: { label: 'Active Users', value: '24' },
  },
  {
    name: 'Tenant',
    path: '/tenant',
    icon: Building2,
    color: 'bg-tenant',
    textColor: 'text-tenant',
    borderColor: 'border-l-tenant',
    description: 'Multi-Tenant Isolation',
    features: ['Tenants', 'Members', 'Isolation Check'],
    badge: 'READ-ONLY',
    badgeVariant: 'info' as const,
    stats: { label: 'Tenants', value: '3' },
  },
  {
    name: 'Decision',
    path: '/decision',
    icon: Scale,
    color: 'bg-decision',
    textColor: 'text-decision',
    borderColor: 'border-l-decision',
    description: 'Rules & Policy Engine',
    features: ['Rules', 'Decision Types', 'History'],
    badge: '2 MUTATIONS',
    badgeVariant: 'warning' as const,
    stats: { label: 'Active Rules', value: '12' },
  },
  {
    name: 'Workflow',
    path: '/workflow',
    icon: CheckCircle,
    color: 'bg-workflow',
    textColor: 'text-workflow',
    borderColor: 'border-l-workflow',
    description: 'Approval Workflows',
    features: ['My Pending', 'All Workflows', 'Escalations'],
    badge: '4 MUTATIONS',
    badgeVariant: 'warning' as const,
    stats: { label: 'Pending', value: '5' },
  },
  {
    name: 'Control',
    path: '/control',
    icon: BarChart3,
    color: 'bg-control',
    textColor: 'text-control',
    borderColor: 'border-l-control',
    description: 'Audit & Observability',
    features: ['Audit Trail', 'Events', 'DLQ', 'Metrics'],
    badge: 'READ-ONLY',
    badgeVariant: 'info' as const,
    stats: { label: 'Events Today', value: '142' },
  },
]

// Quick actions
const quickActions = [
  { label: 'View Pending Approvals', path: '/workflow/pending', icon: Clock, color: 'text-workflow' },
  { label: 'Create Rule Draft', path: '/decision/rules/new', icon: FileText, color: 'text-decision' },
  { label: 'View Audit Trail', path: '/control/audit', icon: Shield, color: 'text-control' },
  { label: 'Check Metrics', path: '/control/metrics', icon: TrendingUp, color: 'text-control' },
]

export function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Page Header - Same style as DomainPage */}
      <div className="bg-card rounded-lg border border-l-4 border-l-primary p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-primary/10 rounded-lg">
              <LayoutDashboard className="h-6 w-6 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">Dashboard</h1>
                <Badge variant="default">Overview</Badge>
              </div>
              <p className="text-muted-foreground mt-1">
                ATLAS_PUGUH Phase 4 - 5-Domain CMS Architecture
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-workflow/10 rounded-lg">
                <Clock className="h-6 w-6 text-workflow" />
              </div>
              <div>
                <p className="text-2xl font-bold">5</p>
                <p className="text-sm text-muted-foreground">Pending Approvals</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-decision/10 rounded-lg">
                <Scale className="h-6 w-6 text-decision" />
              </div>
              <div>
                <p className="text-2xl font-bold">12</p>
                <p className="text-sm text-muted-foreground">Active Rules</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Activity className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">98%</p>
                <p className="text-sm text-muted-foreground">System Health</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-100 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">0</p>
                <p className="text-sm text-muted-foreground">DLQ Events</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {quickActions.map((action) => (
              <Link key={action.path} to={action.path}>
                <Button variant="outline" className="w-full justify-start h-auto py-3">
                  <action.icon className={`h-4 w-4 mr-2 ${action.color}`} />
                  <span className="text-sm">{action.label}</span>
                </Button>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Domain Cards */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Domains</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {domains.map((domain) => (
            <Link key={domain.path} to={domain.path}>
              <Card className={`h-full hover:shadow-md transition-shadow cursor-pointer border-l-4 ${domain.borderColor}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 ${domain.color} rounded-lg`}>
                        <domain.icon className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{domain.name}</CardTitle>
                        <CardDescription className="text-xs">
                          {domain.description}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Badge */}
                  <div className="mb-3">
                    <Badge variant={domain.badgeVariant} className="text-xs">
                      {domain.badge}
                    </Badge>
                  </div>

                  {/* Stats */}
                  <div className="mb-4 p-3 bg-muted/50 rounded-lg">
                    <p className="text-2xl font-bold">{domain.stats.value}</p>
                    <p className="text-xs text-muted-foreground">{domain.stats.label}</p>
                  </div>

                  {/* Features */}
                  <div className="flex flex-wrap gap-1">
                    {domain.features.map((feature) => (
                      <Badge key={feature} variant="outline" className="text-xs font-normal">
                        {feature}
                      </Badge>
                    ))}
                  </div>

                  {/* Link */}
                  <div className="mt-4 flex items-center text-sm text-primary">
                    <span>Go to {domain.name}</span>
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Architecture Info */}
      <Card className="bg-muted/30 border-l-4 border-l-yellow-500">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <h3 className="font-semibold">Phase 4 Architecture</h3>
              <p className="text-sm text-muted-foreground mt-1">
                This CMS is the <strong>operational UI layer</strong> only. All business logic
                and enforcement happens via <strong>SDK → Core API</strong>.
                READ-ONLY domains display data from Core API without modifications.
                MUTATION domains (Decision: 2, Workflow: 4) create records that trigger
                Core API workflows.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
