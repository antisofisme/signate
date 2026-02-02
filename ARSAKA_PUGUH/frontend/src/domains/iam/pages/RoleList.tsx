/**
 * IAM Domain - Role List with CRUD Operations
 * Following ARSAKA_PANDAWA standards
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { DomainPage } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
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
import { Shield, Users, Plus, Trash2, Loader2 } from 'lucide-react'
import { useGetRoles, useGetPermissions, useCreateRole, useDeleteRole } from '../api'
import type { CreateRoleRequest, Permission } from '../types'

// Form Schema
const createRoleSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(50, 'Name must be less than 50 characters'),
  description: z.string().min(5, 'Description must be at least 5 characters').max(200, 'Description must be less than 200 characters'),
  permissions: z.array(z.string()).min(1, 'Select at least one permission'),
})

type CreateRoleFormData = z.infer<typeof createRoleSchema>

// Permission Checkbox Component
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

export function RoleList() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [deletingRoleId, setDeletingRoleId] = useState<string | null>(null)

  // Queries
  const { data: rolesData, isLoading: rolesLoading, error: rolesError } = useGetRoles()
  const { data: permissionsData } = useGetPermissions()
  const roles = rolesData?.data || []
  const permissions = permissionsData?.data || []

  // Mutations
  const createRole = useCreateRole()

  // Form
  const form = useForm<CreateRoleFormData>({
    resolver: zodResolver(createRoleSchema),
    defaultValues: {
      name: '',
      description: '',
      permissions: [],
    },
  })

  const selectedPermissions = form.watch('permissions')

  const handleCreateRole = async (values: CreateRoleFormData) => {
    try {
      await createRole.mutateAsync(values as CreateRoleRequest)
      toast({
        title: 'Role created',
        description: `${values.name} has been created successfully.`,
      })
      form.reset()
      setCreateDialogOpen(false)
    } catch (err) {
      toast({
        title: 'Failed to create role',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleTogglePermission = (permissionCode: string, checked: boolean) => {
    const current = form.getValues('permissions')
    if (checked) {
      form.setValue('permissions', [...current, permissionCode], { shouldValidate: true })
    } else {
      form.setValue('permissions', current.filter((p) => p !== permissionCode), { shouldValidate: true })
    }
  }

  // Group permissions by module
  const permissionsByModule = permissions.reduce<Record<string, Permission[]>>((acc, perm) => {
    const module = perm.module || 'Other'
    if (!acc[module]) {
      acc[module] = []
    }
    acc[module].push(perm)
    return acc
  }, {})

  return (
    <DomainPage
      domain="iam"
      title="Roles"
      description="Manage roles and their permissions"
      actions={
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Role
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <form onSubmit={form.handleSubmit(handleCreateRole)}>
              <DialogHeader>
                <DialogTitle>Create New Role</DialogTitle>
                <DialogDescription>
                  Define a new role with specific permissions for your organization.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="role-name">Role Name</Label>
                  <Input
                    id="role-name"
                    placeholder="e.g., MANAGER"
                    {...form.register('name')}
                  />
                  {form.formState.errors.name && (
                    <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role-description">Description</Label>
                  <Textarea
                    id="role-description"
                    placeholder="Describe the purpose of this role..."
                    rows={2}
                    {...form.register('description')}
                  />
                  {form.formState.errors.description && (
                    <p className="text-sm text-destructive">{form.formState.errors.description.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Permissions</Label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Select the permissions this role should have. ({selectedPermissions.length} selected)
                  </p>
                  {form.formState.errors.permissions && (
                    <p className="text-sm text-destructive mb-2">{form.formState.errors.permissions.message}</p>
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
                    {permissions.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No permissions available. Contact your administrator.
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createRole.isPending}>
                  {createRole.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create Role
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      }
    >
      {rolesLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-20" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : rolesError ? (
        <Card className="border-destructive">
          <CardContent className="py-6 text-center text-destructive">
            Failed to load roles. Please try again.
          </CardContent>
        </Card>
      ) : roles.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Shield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No roles yet</h3>
            <p className="text-muted-foreground mb-4">Create your first role to get started.</p>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Role
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {roles.map((role) => (
            <RoleCard
              key={role.id}
              role={role}
              onNavigate={() => navigate(`/app/iam/roles/${role.id}`)}
              onDeleteStart={() => setDeletingRoleId(role.id)}
              isDeleting={deletingRoleId === role.id}
            />
          ))}
        </div>
      )}
    </DomainPage>
  )
}

// Separate component for role card with delete functionality
interface RoleCardProps {
  role: {
    id: string
    name: string
    description: string
    permissions: string[]
    userCount: number
  }
  onNavigate: () => void
  onDeleteStart: () => void
  isDeleting: boolean
}

function RoleCard({ role, onNavigate, onDeleteStart, isDeleting }: RoleCardProps) {
  const { toast } = useToast()
  const deleteRole = useDeleteRole(role.id)

  const handleDelete = async () => {
    try {
      await deleteRole.mutateAsync()
      toast({
        title: 'Role deleted',
        description: `${role.name} has been deleted successfully.`,
      })
    } catch (err) {
      toast({
        title: 'Failed to delete role',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  // Prevent system roles from being deleted
  const isSystemRole = ['SUPER_ADMIN', 'ADMIN', 'VIEWER'].includes(role.name)

  return (
    <Card className="group relative">
      <div
        className="cursor-pointer"
        onClick={onNavigate}
      >
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-iam" />
              {role.name}
            </div>
            <Badge variant="secondary">{role.permissions?.length || 0} perms</Badge>
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
      </div>
      <CardFooter className="pt-0">
        <div className="flex justify-end w-full">
          {!isSystemRole && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:text-destructive hover:bg-destructive/10"
                  disabled={isDeleting || deleteRole.isPending}
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteStart()
                  }}
                >
                  {(isDeleting || deleteRole.isPending) && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                  {!(isDeleting || deleteRole.isPending) && <Trash2 className="h-4 w-4 mr-1" />}
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
                    onClick={handleDelete}
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
          {isSystemRole && (
            <span className="text-xs text-muted-foreground">System role</span>
          )}
        </div>
      </CardFooter>
    </Card>
  )
}
