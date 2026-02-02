/**
 * IAM Domain - User List
 * READ-ONLY
 */

import { DomainPage, ReadOnlyNotice } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useNavigate } from 'react-router-dom'
import { Users, Search, Loader2, AlertTriangle } from 'lucide-react'
import { useState } from 'react'
import { useGetUsers, useGetUserStats } from '../api'

export function UserList() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')

  // Use real API hooks
  const { data: usersResponse, isLoading: isLoadingUsers, error: usersError } = useGetUsers({ q: search || undefined })
  const { data: statsResponse, isLoading: isLoadingStats } = useGetUserStats()

  const users = usersResponse?.data?.items || []
  const stats = statsResponse?.data || { total: 0, active: 0, inactive: 0 }
  const isLoading = isLoadingUsers || isLoadingStats

  // Client-side filtering if search is applied (API may not support all filters)
  const filteredUsers = search
    ? users.filter((u: Record<string, unknown>) =>
        String(u.username || u.email || u.name || '').toLowerCase().includes(search.toLowerCase()) ||
        String(u.email || '').toLowerCase().includes(search.toLowerCase())
      )
    : users

  // Loading state
  if (isLoading) {
    return (
      <DomainPage
        domain="iam"
        title="Users"
        description="View all users in current tenant"
        badge={{ label: 'READ-ONLY', variant: 'info' }}
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-iam" />
        </div>
      </DomainPage>
    )
  }

  // Error state
  if (usersError) {
    return (
      <DomainPage
        domain="iam"
        title="Users"
        description="View all users in current tenant"
        badge={{ label: 'READ-ONLY', variant: 'info' }}
      >
        <Card className="border-destructive">
          <CardContent className="py-6 text-center">
            <AlertTriangle className="h-8 w-8 mx-auto text-destructive mb-2" />
            <p className="text-sm text-muted-foreground">
              Failed to load users. Please try again.
            </p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="iam"
      title="Users"
      description="View all users in current tenant"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="iam" />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total || users.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.active || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Inactive</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-400">
              {stats.inactive || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search & Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search users..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border rounded-md text-sm"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Login</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((user: Record<string, unknown>) => (
                <TableRow
                  key={String(user.id)}
                  className="cursor-pointer"
                  onClick={() => navigate(`/app/iam/users/${user.id}`)}
                >
                  <TableCell className="font-medium">
                    {String(user.name || user.display_name || user.username || 'N/A')}
                  </TableCell>
                  <TableCell>{String(user.email || 'N/A')}</TableCell>
                  <TableCell>
                    {user.roles && Array.isArray(user.roles) && user.roles.length > 0 ? (
                      user.roles.slice(0, 2).map((role: Record<string, unknown>, i: number) => (
                        <Badge key={i} variant="outline" className="mr-1">
                          {String(role.name || role)}
                        </Badge>
                      ))
                    ) : (
                      <Badge variant="outline">{String(user.role || 'Member')}</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.status === 'active' || user.is_active ? 'success' : 'secondary'}>
                      {user.status || (user.is_active ? 'active' : 'inactive')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {user.last_login_at || user.lastLogin
                      ? new Date(String(user.last_login_at || user.lastLogin)).toLocaleString()
                      : 'Never'}
                  </TableCell>
                </TableRow>
              ))}
              {filteredUsers.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No users found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </DomainPage>
  )
}
