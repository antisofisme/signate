/**
 * IAM Domain - Page Exports
 * Following ARSAKA_PANDAWA standards
 */

export { UserList } from './UserList'
export { UserDetail } from './UserDetail'
export { RoleList } from './RoleList'

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { DomainPage, ReadOnlyNotice } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/hooks/use-toast'
import { Shield, Key, Server, Check, X, Pencil, UserPlus, Trash2, Loader2 } from 'lucide-react'
import {
  useGetRole,
  useGetPermissions,
  useGetUsers,
  useUpdateRole,
  useDeleteRole,
  useAssignRoleToUser,
} from '../api'
import type { Permission, UpdateRoleRequest, AssignRoleRequest } from '../types'

// ============================================
// Form Schemas
// ============================================

const updateRoleSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(50, 'Name must be less than 50 characters'),
  description: z.string().min(5, 'Description must be at least 5 characters').max(200, 'Description must be less than 200 characters'),
  permissions: z.array(z.string()).min(1, 'Select at least one permission'),
})

type UpdateRoleFormData = z.infer<typeof updateRoleSchema>

const assignRoleSchema = z.object({
  userId: z.string().min(1, 'Select a user'),
})

type AssignRoleFormData = z.infer<typeof assignRoleSchema>

// ============================================
// Permission Checkbox Component (reusable)
// ============================================

interface PermissionCheckboxProps {
  permission: Permission
  checked: boolean
  onChange: (checked: boolean) => void
}

function PermissionCheckbox({ permission, checked, onChange }: PermissionCheckboxProps) {
  return (
    <label
      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
        checked ? 'bg-primary/10 border-primary' : 'hover:bg-muted'
      }`}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 rounded border-gray-300"
      />
      <div className="flex-1 min-w-0">
        <div className="font-mono text-sm">{permission.code}</div>
        <div className="text-xs text-muted-foreground truncate">{permission.description || permission.name}</div>
      </div>
      <Badge variant="outline" className="text-xs shrink-0">
        {permission.module}
      </Badge>
    </label>
  )
}

// ============================================
// Role Detail Page with Edit and Assign
// ============================================

export function RoleDetail() {
  const { id: roleId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()

  // State
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [assignDialogOpen, setAssignDialogOpen] = useState(false)
  const [assigningUserId, setAssigningUserId] = useState('')

  // Queries
  const { data: roleData, isLoading: roleLoading, error: roleError } = useGetRole(roleId || '')
  const { data: permissionsData } = useGetPermissions()
  const { data: usersData } = useGetUsers()

  const role = roleData?.data
  const allPermissions = permissionsData?.data || []
  const users = usersData?.data?.items || []

  // Mutations
  const updateRole = useUpdateRole(roleId || '')
  const deleteRole = useDeleteRole(roleId || '')
  const assignRoleToUser = useAssignRoleToUser(assigningUserId)

  // Edit Form
  const editForm = useForm<UpdateRoleFormData>({
    resolver: zodResolver(updateRoleSchema),
    defaultValues: {
      name: '',
      description: '',
      permissions: [],
    },
  })

  // Assign Form
  const assignForm = useForm<AssignRoleFormData>({
    resolver: zodResolver(assignRoleSchema),
    defaultValues: {
      userId: '',
    },
  })

  // Update edit form when role data loads
  useEffect(() => {
    if (role) {
      editForm.reset({
        name: role.name,
        description: role.description,
        permissions: role.permissions || [],
      })
    }
  }, [role])

  const selectedPermissions = editForm.watch('permissions')

  // Group permissions by module
  const permissionsByModule = allPermissions.reduce<Record<string, Permission[]>>((acc, perm) => {
    const module = perm.module || 'Other'
    if (!acc[module]) {
      acc[module] = []
    }
    acc[module].push(perm)
    return acc
  }, {})

  const handleTogglePermission = (permissionCode: string, checked: boolean) => {
    const current = editForm.getValues('permissions')
    if (checked) {
      editForm.setValue('permissions', [...current, permissionCode], { shouldValidate: true })
    } else {
      editForm.setValue('permissions', current.filter((p) => p !== permissionCode), { shouldValidate: true })
    }
  }

  const handleUpdateRole = async (values: UpdateRoleFormData) => {
    try {
      await updateRole.mutateAsync(values as UpdateRoleRequest)
      toast({
        title: 'Role updated',
        description: `${values.name} has been updated successfully.`,
      })
      setEditDialogOpen(false)
    } catch (err) {
      toast({
        title: 'Failed to update role',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleDeleteRole = async () => {
    try {
      await deleteRole.mutateAsync()
      toast({
        title: 'Role deleted',
        description: 'The role has been deleted successfully.',
      })
      navigate('/app/iam/roles')
    } catch (err) {
      toast({
        title: 'Failed to delete role',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleAssignRole = async (values: AssignRoleFormData) => {
    try {
      setAssigningUserId(values.userId)
      await assignRoleToUser.mutateAsync({ roleId: roleId || '' } as AssignRoleRequest)
      toast({
        title: 'Role assigned',
        description: 'The role has been assigned to the user.',
      })
      assignForm.reset()
      setAssignDialogOpen(false)
    } catch (err) {
      toast({
        title: 'Failed to assign role',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  // Prevent system roles from being edited/deleted
  const isSystemRole = role && ['SUPER_ADMIN', 'ADMIN', 'VIEWER'].includes(role.name)

  // Loading state
  if (roleLoading) {
    return (
      <DomainPage domain="iam" title="Loading..." backTo="/app/iam/roles">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader><Skeleton className="h-6 w-48" /></CardHeader>
            <CardContent><Skeleton className="h-32 w-full" /></CardContent>
          </Card>
          <Card>
            <CardHeader><Skeleton className="h-6 w-32" /></CardHeader>
            <CardContent><Skeleton className="h-24 w-full" /></CardContent>
          </Card>
        </div>
      </DomainPage>
    )
  }

  // Error state
  if (roleError || !role) {
    return (
      <DomainPage domain="iam" title="Error" backTo="/app/iam/roles">
        <Card className="border-destructive">
          <CardContent className="py-6 text-center text-destructive">
            Failed to load role details. The role may not exist.
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="iam"
      title={`Role: ${role.name}`}
      description={role.description}
      backTo="/app/iam/roles"
      actions={
        <div className="flex gap-2">
          {/* Edit Button */}
          {!isSystemRole && (
            <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Pencil className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <form onSubmit={editForm.handleSubmit(handleUpdateRole)}>
                  <DialogHeader>
                    <DialogTitle>Edit Role</DialogTitle>
                    <DialogDescription>
                      Update the role details and permissions.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="edit-role-name">Role Name</Label>
                      <Input
                        id="edit-role-name"
                        {...editForm.register('name')}
                      />
                      {editForm.formState.errors.name && (
                        <p className="text-sm text-destructive">{editForm.formState.errors.name.message}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-role-description">Description</Label>
                      <Textarea
                        id="edit-role-description"
                        rows={2}
                        {...editForm.register('description')}
                      />
                      {editForm.formState.errors.description && (
                        <p className="text-sm text-destructive">{editForm.formState.errors.description.message}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>Permissions</Label>
                      <p className="text-xs text-muted-foreground mb-2">
                        ({selectedPermissions.length} selected)
                      </p>
                      {editForm.formState.errors.permissions && (
                        <p className="text-sm text-destructive mb-2">{editForm.formState.errors.permissions.message}</p>
                      )}
                      <div className="space-y-4 max-h-64 overflow-y-auto border rounded-lg p-4">
                        {Object.entries(permissionsByModule).map(([module, modulePermissions]) => (
                          <div key={module}>
                            <h4 className="font-semibold text-sm mb-2 text-muted-foreground uppercase tracking-wide">
                              {module}
                            </h4>
                            <div className="grid grid-cols-1 gap-2">
                              {modulePermissions.map((perm) => (
                                <PermissionCheckbox
                                  key={perm.id}
                                  permission={perm}
                                  checked={selectedPermissions.includes(perm.code)}
                                  onChange={(checked) => handleTogglePermission(perm.code, checked)}
                                />
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setEditDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={updateRole.isPending}>
                      {updateRole.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      Save Changes
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          )}

          {/* Assign Role to User Button */}
          <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <UserPlus className="h-4 w-4 mr-2" />
                Assign to User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={assignForm.handleSubmit(handleAssignRole)}>
                <DialogHeader>
                  <DialogTitle>Assign Role to User</DialogTitle>
                  <DialogDescription>
                    Select a user to assign the "{role.name}" role.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="assign-user">Select User</Label>
                    <Select
                      value={assignForm.watch('userId')}
                      onValueChange={(value) => assignForm.setValue('userId', value, { shouldValidate: true })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a user..." />
                      </SelectTrigger>
                      <SelectContent>
                        {users.map((user) => (
                          <SelectItem key={user.id} value={user.id}>
                            <div className="flex items-center gap-2">
                              <span>{user.name || user.email}</span>
                              <span className="text-muted-foreground text-xs">({user.email})</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {assignForm.formState.errors.userId && (
                      <p className="text-sm text-destructive">{assignForm.formState.errors.userId.message}</p>
                    )}
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setAssignDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={assignRoleToUser.isPending}>
                    {assignRoleToUser.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    Assign Role
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* Delete Button */}
          {!isSystemRole && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Role?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete the "{role.name}" role.
                    {role.userCount > 0 && (
                      <span className="block mt-2 text-destructive font-medium">
                        Warning: {role.userCount} users are currently assigned to this role.
                      </span>
                    )}
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDeleteRole}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {deleteRole.isPending ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : null}
                    Delete Role
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      }
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
                <p className="font-medium">{role.name}</p>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Users Assigned</label>
                <p className="font-medium">{role.userCount}</p>
              </div>
              <div className="col-span-2">
                <label className="text-sm text-muted-foreground">Description</label>
                <p className="font-medium">{role.description}</p>
              </div>
              {isSystemRole && (
                <div className="col-span-2">
                  <Badge variant="secondary">System Role - Cannot be modified</Badge>
                </div>
              )}
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
                <span className="font-medium">{role.permissions?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Created</span>
                <span className="font-medium text-xs">
                  {role.createdAt ? new Date(role.createdAt).toLocaleDateString() : 'N/A'}
                </span>
              </div>
              {role.updatedAt && (
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Last Updated</span>
                  <span className="font-medium text-xs">
                    {new Date(role.updatedAt).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Permissions List */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Permissions ({role.permissions?.length || 0})</CardTitle>
          </CardHeader>
          <CardContent>
            {role.permissions && role.permissions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {role.permissions.map((permCode) => {
                  const perm = allPermissions.find((p) => p.code === permCode)
                  return (
                    <div
                      key={permCode}
                      className="p-3 rounded-lg border bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm">{permCode}</span>
                        <Check className="h-4 w-4 text-green-600" />
                      </div>
                      {perm && (
                        <p className="text-xs text-muted-foreground mt-1">{perm.name || perm.description}</p>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Key className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No permissions assigned to this role.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DomainPage>
  )
}

// ============================================
// Service Accounts Page
// ============================================

import { useGetServiceAccounts } from '../api'

export function ServiceAccounts() {
  // Use real API hook
  const { data: serviceAccountsResponse, isLoading, error } = useGetServiceAccounts()

  const serviceAccounts = serviceAccountsResponse?.data || []

  // Loading state
  if (isLoading) {
    return (
      <DomainPage
        domain="iam"
        title="Service Accounts"
        description="View service accounts and API credentials"
        badge={{ label: 'READ-ONLY', variant: 'info' }}
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-iam" />
        </div>
      </DomainPage>
    )
  }

  // Error state
  if (error) {
    return (
      <DomainPage
        domain="iam"
        title="Service Accounts"
        description="View service accounts and API credentials"
        badge={{ label: 'READ-ONLY', variant: 'info' }}
      >
        <Card className="border-destructive">
          <CardContent className="py-6 text-center">
            <Server className="h-8 w-8 mx-auto text-destructive mb-2" />
            <p className="text-sm text-muted-foreground">
              Failed to load service accounts. Please try again.
            </p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="iam"
      title="Service Accounts"
      description="View service accounts and API credentials"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="iam" />

      {serviceAccounts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Server className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold">No service accounts</h3>
            <p className="text-muted-foreground">No service accounts have been created yet.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {serviceAccounts.map((account: Record<string, unknown>) => (
            <Card key={String(account.id)}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="h-5 w-5 text-iam" />
                    {String(account.name || 'Unnamed')}
                  </div>
                  <Badge variant={account.status === 'active' || account.is_active ? 'success' : 'secondary'}>
                    {String(account.status || (account.is_active ? 'active' : 'inactive'))}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  {String(account.description || 'No description')}
                </p>

                <div>
                  <label className="text-xs text-muted-foreground">Client ID</label>
                  <p className="font-mono text-sm bg-muted px-2 py-1 rounded">
                    {String(account.client_id || account.clientId || account.id)}
                  </p>
                </div>

                {account.scopes || account.permissions ? (
                  <div>
                    <label className="text-xs text-muted-foreground">Scopes/Permissions</label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {(Array.isArray(account.scopes) ? account.scopes :
                        Array.isArray(account.permissions) ? account.permissions : []
                      ).map((scope: string, i: number) => (
                        <Badge key={i} variant="outline" className="text-xs font-mono">
                          {scope}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ) : null}

                <div className="text-xs text-muted-foreground">
                  {account.last_used_at || account.lastUsedAt
                    ? `Last used: ${new Date(String(account.last_used_at || account.lastUsedAt)).toLocaleString()}`
                    : 'Never used'}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
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
