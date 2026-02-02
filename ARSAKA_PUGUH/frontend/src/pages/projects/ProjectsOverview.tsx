/**
 * Projects Overview Page
 *
 * Shows all projects across all tenants the user has access to
 */

import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  FolderKanban,
  Building2,
  Plus,
  ArrowRight,
  Scale,
  CheckCircle,
} from 'lucide-react'
import { projectApi } from '@/features/project/api'
import { useTenantStore } from '@/stores/tenantStore'
import type { Project, ProjectListResponse } from '@/features/project/types'

export function ProjectsOverview() {
  const { availableTenants, currentTenant } = useTenantStore()

  // Fetch projects for current tenant
  const { data, isLoading, error } = useQuery<ProjectListResponse>({
    queryKey: ['projects', currentTenant?.tenant_id],
    queryFn: () => projectApi.list(currentTenant!.tenant_id),
    enabled: !!currentTenant?.tenant_id,
  })

  const projects = data?.projects || []

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-card rounded-lg border border-l-4 border-l-indigo-600 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-indigo-600/10 rounded-lg">
              <FolderKanban className="h-6 w-6 text-indigo-600" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">Projects</h1>
                <Badge variant="default">{projects.length} Total</Badge>
              </div>
              <p className="text-muted-foreground mt-1">
                Manage all your projects across organizations
              </p>
            </div>
          </div>
          {currentTenant && (
            <Link to={`/app/${currentTenant.slug}/projects`}>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Project
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-indigo-100 rounded-lg">
                <FolderKanban className="h-6 w-6 text-indigo-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{projects.length}</p>
                <p className="text-sm text-muted-foreground">Total Projects</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-tenant/10 rounded-lg">
                <Building2 className="h-6 w-6 text-tenant" />
              </div>
              <div>
                <p className="text-2xl font-bold">{availableTenants.length}</p>
                <p className="text-sm text-muted-foreground">Organizations</p>
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
                <p className="text-2xl font-bold">-</p>
                <p className="text-sm text-muted-foreground">Active Rules</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-workflow/10 rounded-lg">
                <CheckCircle className="h-6 w-6 text-workflow" />
              </div>
              <div>
                <p className="text-2xl font-bold">-</p>
                <p className="text-sm text-muted-foreground">Pending Approvals</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Projects List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="py-6 text-center text-destructive">
            Failed to load projects. Please try again.
          </CardContent>
        </Card>
      ) : projects.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FolderKanban className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No projects yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first project to start using the Decision Engine.
            </p>
            {currentTenant && (
              <Link to={`/app/${currentTenant.slug}/projects`}>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Project
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project: Project) => (
            <Card key={project.project_id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 rounded-lg">
                      <FolderKanban className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{project.name}</CardTitle>
                      <CardDescription className="flex items-center gap-1">
                        <Building2 className="h-3 w-3" />
                        {currentTenant?.name || 'Unknown Organization'}
                      </CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {project.description || 'No description'}
                </p>
                <div className="flex items-center justify-between">
                  <Badge variant={project.is_active ? 'default' : 'secondary'}>
                    {project.environment}
                  </Badge>
                  <Link to={`/app/${currentTenant?.slug}/${project.slug}/settings`}>
                    <Button variant="ghost" size="sm">
                      Open
                      <ArrowRight className="h-4 w-4 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Quick Actions by Tenant */}
      {availableTenants.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Browse by Organization</CardTitle>
            <CardDescription>
              View projects in each of your organizations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {availableTenants.map((membership) => (
                <Link key={membership.tenant.tenant_id} to={`/app/${membership.tenant.slug}/projects`}>
                  <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-tenant/10 rounded-lg">
                        <Building2 className="h-4 w-4 text-tenant" />
                      </div>
                      <div>
                        <p className="font-medium">{membership.tenant.name}</p>
                        <p className="text-xs text-muted-foreground">{membership.role}</p>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ProjectsOverview
