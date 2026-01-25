import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Users as UsersIcon, Mail, Shield } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@/components/ui'
import { listUsers, createUser, deleteUser, listTenants } from '@/lib/api'
import { formatDate, formatRelativeTime } from '@/lib/utils'
import { toast } from 'sonner'
import type { User, UserFormData, TenantConfig } from '@/types'

export function Users() {
  const [selectedTenant, setSelectedTenant] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState<UserFormData>({
    external_user_id: '',
    email: '',
    display_name: '',
    role: 'user',
  })

  const queryClient = useQueryClient()

  const { data: tenants } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => listTenants(),
  })

  const { data: users, isLoading } = useQuery({
    queryKey: ['users', selectedTenant],
    queryFn: () => listUsers(selectedTenant),
    enabled: !!selectedTenant,
  })

  const createMutation = useMutation({
    mutationFn: (data: UserFormData) => createUser(selectedTenant, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users', selectedTenant] })
      setShowForm(false)
      setFormData({ external_user_id: '', email: '', display_name: '', role: 'user' })
      toast.success('User created successfully')
    },
    onError: () => {
      toast.error('Failed to create user')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (userId: string) => deleteUser(selectedTenant, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users', selectedTenant] })
      toast.success('User deleted')
    },
    onError: () => {
      toast.error('Failed to delete user')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.display_name || !formData.external_user_id) return
    createMutation.mutate(formData)
  }

  const handleDelete = (userId: string) => {
    if (confirm('Are you sure you want to delete this user?')) {
      deleteMutation.mutate(userId)
    }
  }

  const getRoleBadge = (role: string) => {
    const colors: Record<string, string> = {
      admin: 'bg-red-100 text-red-700',
      user: 'bg-blue-100 text-blue-700',
      readonly: 'bg-gray-100 text-gray-700',
    }
    return colors[role] || colors.user
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Users</h1>
          <p className="text-gray-500">Manage tenant users</p>
        </div>
        {selectedTenant && (
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4 mr-2" />
            New User
          </Button>
        )}
      </div>

      {/* Tenant Selector */}
      <Card>
        <CardContent className="pt-6">
          <label className="text-sm font-medium">Select Tenant</label>
          <select
            className="w-full h-10 rounded-md border px-3 mt-1"
            value={selectedTenant}
            onChange={(e) => setSelectedTenant(e.target.value)}
          >
            <option value="">Choose a tenant...</option>
            {tenants?.map((tenant: TenantConfig) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      {/* Create Form */}
      {showForm && selectedTenant && (
        <Card>
          <CardHeader>
            <CardTitle>Create New User</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">Display Name *</label>
                  <Input
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    placeholder="John Doe"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">External User ID *</label>
                  <Input
                    value={formData.external_user_id}
                    onChange={(e) => setFormData({ ...formData, external_user_id: e.target.value })}
                    placeholder="user_123"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Email</label>
                  <Input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="john@example.com"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Role</label>
                  <select
                    className="w-full h-9 rounded-md border px-3"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'user' | 'readonly' })}
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                    <option value="readonly">Read Only</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit" isLoading={createMutation.isPending}>
                  Create User
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Users List */}
      {selectedTenant && (
        <>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : users?.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <UsersIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No users found. Create your first user to get started.</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {users?.map((user: User) => (
                <Card key={user.id}>
                  <CardHeader className="flex flex-row items-start justify-between pb-2">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white font-medium">
                        {user.display_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <CardTitle className="text-base">{user.display_name}</CardTitle>
                        <p className="text-xs text-gray-500">{user.external_user_id}</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {user.email && (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Mail className="h-4 w-4" />
                          {user.email}
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-gray-400" />
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRoleBadge(user.role)}`}>
                          {user.role}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {user.last_seen_at ? (
                          <span>Last seen {formatRelativeTime(user.last_seen_at)}</span>
                        ) : (
                          <span>Created {formatDate(user.created_at)}</span>
                        )}
                      </div>
                    </div>

                    <div className="flex justify-end mt-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => handleDelete(user.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {!selectedTenant && (
        <div className="text-center py-12 text-gray-500">
          <UsersIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Select a tenant to view and manage users.</p>
        </div>
      )}
    </div>
  )
}
