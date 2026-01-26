/**
 * IAM Domain - User Detail
 * READ-ONLY
 */

import { DomainPage } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useParams } from 'react-router-dom'
import { User, Mail, Shield, Clock } from 'lucide-react'

// Mock data
const mockUser = {
  id: '1',
  username: 'admin',
  email: 'admin@example.com',
  role: 'ADMIN',
  status: 'active',
  createdAt: '2026-01-01T00:00:00Z',
  lastLogin: '2026-01-24T10:00:00Z',
  permissions: ['users.read', 'users.write', 'roles.read', 'decisions.read', 'decisions.write'],
}

export function UserDetail() {
  const { id } = useParams()

  return (
    <DomainPage
      domain="iam"
      title={`User: ${mockUser.username}`}
      description={`User ID: ${id}`}
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      backTo="/iam/users"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User Info */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User size={20} />
              User Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Username</div>
                <div className="font-medium">{mockUser.username}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Email</div>
                <div className="font-medium flex items-center gap-2">
                  <Mail size={14} />
                  {mockUser.email}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Role</div>
                <div className="font-medium flex items-center gap-2">
                  <Shield size={14} />
                  <Badge variant="iam">{mockUser.role}</Badge>
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Status</div>
                <Badge variant={mockUser.status === 'active' ? 'success' : 'secondary'}>
                  {mockUser.status}
                </Badge>
              </div>
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground flex items-center gap-1">
                  <Clock size={14} />
                  Created At
                </div>
                <div className="font-medium">
                  {new Date(mockUser.createdAt).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground flex items-center gap-1">
                  <Clock size={14} />
                  Last Login
                </div>
                <div className="font-medium">
                  {new Date(mockUser.lastLogin).toLocaleString()}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Permissions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield size={20} />
              Permissions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {mockUser.permissions.map((perm) => (
                <Badge key={perm} variant="outline" className="text-xs">
                  {perm}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DomainPage>
  )
}
