/**
 * IAM Domain - Role List
 * READ-ONLY
 */

import { DomainPage, ReadOnlyNotice } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useNavigate } from 'react-router-dom'
import { Shield, Users } from 'lucide-react'

// Mock data
const mockRoles = [
  { id: '1', name: 'ADMIN', description: 'Full system access', userCount: 2, permissions: 15 },
  { id: '2', name: 'OPERATOR', description: 'Operational access', userCount: 5, permissions: 10 },
  { id: '3', name: 'VIEWER', description: 'Read-only access', userCount: 12, permissions: 5 },
  { id: '4', name: 'APPROVER', description: 'Workflow approval access', userCount: 3, permissions: 8 },
]

export function RoleList() {
  const navigate = useNavigate()

  return (
    <DomainPage
      domain="iam"
      title="Roles"
      description="View all roles and their permissions"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="iam" />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockRoles.map((role) => (
          <Card
            key={role.id}
            className="cursor-pointer hover:border-iam/50 transition-colors"
            onClick={() => navigate(`/iam/roles/${role.id}`)}
          >
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-iam" />
                  {role.name}
                </div>
                <Badge variant="iam">{role.permissions} perms</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                {role.description}
              </p>
              <div className="flex items-center gap-2 text-sm">
                <Users className="h-4 w-4" />
                <span>{role.userCount} users</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </DomainPage>
  )
}
