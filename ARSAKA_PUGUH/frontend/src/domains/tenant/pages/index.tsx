/**
 * Tenant Domain - Page Exports
 * Following ARSAKA_PANDAWA standards
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { DomainPage } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
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
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/hooks/use-toast'
import {
  Building2,
  Users,
  Shield,
  Calendar,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Plus,
  Pencil,
  Trash2,
  UserPlus,
  Mail,
  Loader2,
  Settings,
} from 'lucide-react'
import {
  useGetTenants,
  useGetTenant,
  useGetTenantMembers,
  useGetTenantInvitations,
  useGetIsolationCheck,
  useCreateTenant,
  useUpdateTenant,
  useDeleteTenant,
  useInviteMember,
  useRemoveMember,
  useCancelInvitation,
} from '../api'
import type { CreateTenantRequest, UpdateTenantRequest, InviteMemberRequest } from '../types'
import { TENANT_ROLE_LABELS, TENANT_ROLE_DESCRIPTIONS } from '../types'

// Invite role options (exclude OWNER which is auto-assigned)
type InviteRole = 'ADMIN' | 'OPERATOR' | 'VIEWER'

// ============================================
// Form Schemas
// ============================================

const createTenantSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  slug: z.string()
    .min(2, 'Slug must be at least 2 characters')
    .regex(/^[a-z0-9-]+$/, 'Slug can only contain lowercase letters, numbers, and hyphens'),
})

const updateTenantSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  timezone: z.string().optional(),
  currency: z.string().optional(),
  language: z.string().optional(),
})

const inviteMemberSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  role: z.enum(['ADMIN', 'OPERATOR', 'VIEWER'] as const),
})

// ============================================
// Tenant List Page
// ============================================

export function TenantList() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetTenants()
  const tenants = data?.data?.items || []

  return (
    <DomainPage
      domain="tenant"
      title="Tenants"
      description="Manage your organization tenants"
      actions={
        <Button onClick={() => navigate('/app/tenant/create')}>
          <Plus className="h-4 w-4 mr-2" />
          Create Tenant
        </Button>
      }
    >
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-20" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="py-6 text-center text-destructive">
            Failed to load tenants. Please try again.
          </CardContent>
        </Card>
      ) : tenants.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No tenants yet</h3>
            <p className="text-muted-foreground mb-4">Create your first tenant to get started.</p>
            <Button onClick={() => navigate('/app/tenant/create')}>
              <Plus className="h-4 w-4 mr-2" />
              Create Tenant
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tenants.map((tenant) => (
            <Card
              key={tenant.id}
              className="cursor-pointer hover:border-tenant/50 transition-colors"
              onClick={() => navigate(`/app/tenant/${tenant.id}`)}
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
      )}
    </DomainPage>
  )
}

// ============================================
// Tenant Create Page
// ============================================

export function TenantCreate() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const createTenant = useCreateTenant()

  const form = useForm<z.infer<typeof createTenantSchema>>({
    resolver: zodResolver(createTenantSchema),
    defaultValues: {
      name: '',
      slug: '',
    },
  })

  const onSubmit = async (values: z.infer<typeof createTenantSchema>) => {
    try {
      const result = await createTenant.mutateAsync(values as CreateTenantRequest)
      toast({
        title: 'Tenant created',
        description: `${values.name} has been created successfully.`,
      })
      navigate(`/app/tenant/${result.data?.id || ''}`)
    } catch (err) {
      toast({
        title: 'Failed to create tenant',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  // Auto-generate slug from name
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value
    form.setValue('name', name)
    if (!form.getValues('slug') || form.getValues('slug') === slugify(form.getValues('name').slice(0, -1))) {
      form.setValue('slug', slugify(name))
    }
  }

  return (
    <DomainPage
      domain="tenant"
      title="Create Tenant"
      description="Set up a new organization tenant"
      backTo="/app/tenant/list"
    >
      <Card className="max-w-lg">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              New Tenant
            </CardTitle>
            <CardDescription>
              Create a new tenant to organize your team and projects.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Tenant Name</Label>
              <Input
                id="name"
                placeholder="Acme Corporation"
                {...form.register('name')}
                onChange={handleNameChange}
              />
              {form.formState.errors.name && (
                <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="slug">URL Slug</Label>
              <Input
                id="slug"
                placeholder="acme-corp"
                {...form.register('slug')}
              />
              <p className="text-xs text-muted-foreground">
                Used in URLs: app.puguh.io/<strong>{form.watch('slug') || 'your-slug'}</strong>
              </p>
              {form.formState.errors.slug && (
                <p className="text-sm text-destructive">{form.formState.errors.slug.message}</p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createTenant.isPending}>
              {createTenant.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Create Tenant
            </Button>
          </CardFooter>
        </form>
      </Card>
    </DomainPage>
  )
}

// Helper function to generate slug
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

// ============================================
// Tenant Detail Page
// ============================================

export function TenantDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const { data, isLoading, error } = useGetTenant(id || '')
  const deleteTenant = useDeleteTenant(id || '')
  const tenant = data?.data

  const handleDelete = async () => {
    try {
      await deleteTenant.mutateAsync()
      toast({
        title: 'Tenant deleted',
        description: 'The tenant has been deleted successfully.',
      })
      navigate('/app/tenant/list')
    } catch (err) {
      toast({
        title: 'Failed to delete tenant',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  if (isLoading) {
    return (
      <DomainPage domain="tenant" title="Loading..." backTo="/app/tenant/list">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader><Skeleton className="h-6 w-48" /></CardHeader>
            <CardContent><Skeleton className="h-32 w-full" /></CardContent>
          </Card>
        </div>
      </DomainPage>
    )
  }

  if (error || !tenant) {
    return (
      <DomainPage domain="tenant" title="Error" backTo="/app/tenant/list">
        <Card className="border-destructive">
          <CardContent className="py-6 text-center text-destructive">
            Failed to load tenant details.
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="tenant"
      title={tenant.name}
      description={`Tenant ID: ${id}`}
      backTo="/app/tenant/list"
      actions={
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate(`/app/tenant/${id}/edit`)}>
            <Pencil className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Tenant?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete "{tenant.name}" and all associated data.
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  {deleteTenant.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : null}
                  Delete Tenant
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      }
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
                <p className="font-medium">{tenant.name}</p>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Slug</label>
                <p className="font-mono">{tenant.slug}</p>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Status</label>
                <div className="mt-1">
                  <Badge variant={tenant.status === 'active' ? 'success' : 'secondary'}>
                    {tenant.status}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Members</label>
                <p className="font-medium">{tenant.memberCount}</p>
              </div>
            </div>

            <Separator />

            <div>
              <h4 className="font-medium mb-2">Created</h4>
              <p className="text-sm text-muted-foreground">
                {new Date(tenant.createdAt).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate(`/app/tenant/${id}/members`)}
            >
              <Users className="h-4 w-4 mr-2" />
              Manage Members
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate(`/app/tenant/${id}/edit`)}
            >
              <Settings className="h-4 w-4 mr-2" />
              Tenant Settings
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate('/app/tenant/isolation-check')}
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
// Tenant Edit Page
// ============================================

export function TenantEdit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const { data, isLoading } = useGetTenant(id || '')
  const updateTenant = useUpdateTenant(id || '')
  const tenant = data?.data

  const form = useForm<z.infer<typeof updateTenantSchema>>({
    resolver: zodResolver(updateTenantSchema),
    defaultValues: {
      name: '',
      timezone: 'Asia/Jakarta',
      currency: 'IDR',
      language: 'id',
    },
  })

  // Update form when tenant data loads
  useState(() => {
    if (tenant) {
      form.reset({
        name: tenant.name,
        timezone: 'Asia/Jakarta',
        currency: 'IDR',
        language: 'id',
      })
    }
  })

  const onSubmit = async (values: z.infer<typeof updateTenantSchema>) => {
    try {
      const updateData: UpdateTenantRequest = {
        name: values.name,
        settings: {
          timezone: values.timezone,
          currency: values.currency,
          language: values.language,
        },
      }
      await updateTenant.mutateAsync(updateData)
      toast({
        title: 'Tenant updated',
        description: 'Settings have been saved successfully.',
      })
      navigate(`/app/tenant/${id}`)
    } catch (err) {
      toast({
        title: 'Failed to update tenant',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  if (isLoading) {
    return (
      <DomainPage domain="tenant" title="Loading..." backTo={`/app/tenant/${id}`}>
        <Card className="max-w-lg">
          <CardContent className="py-6">
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="tenant"
      title="Edit Tenant"
      description={`Editing ${tenant?.name || 'tenant'}`}
      backTo={`/app/tenant/${id}`}
    >
      <Card className="max-w-lg">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Tenant Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Tenant Name</Label>
              <Input
                id="name"
                defaultValue={tenant?.name}
                {...form.register('name')}
              />
              {form.formState.errors.name && (
                <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
              )}
            </div>

            <Separator />

            <div className="space-y-4">
              <h4 className="font-medium">Regional Settings</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select
                    value={form.watch('timezone') || 'Asia/Jakarta'}
                    onValueChange={(v) => form.setValue('timezone', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Jakarta">Asia/Jakarta</SelectItem>
                      <SelectItem value="Asia/Singapore">Asia/Singapore</SelectItem>
                      <SelectItem value="UTC">UTC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="currency">Currency</Label>
                  <Select
                    value={form.watch('currency') || 'IDR'}
                    onValueChange={(v) => form.setValue('currency', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="IDR">IDR</SelectItem>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="SGD">SGD</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select
                    value={form.watch('language') || 'id'}
                    onValueChange={(v) => form.setValue('language', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="id">Indonesian</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateTenant.isPending}>
              {updateTenant.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Save Changes
            </Button>
          </CardFooter>
        </form>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Tenant Members Page
// ============================================

export function TenantMembers() {
  const { id } = useParams<{ id: string }>()
  const { toast } = useToast()
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteRole, setInviteRole] = useState<InviteRole>('VIEWER')

  const { data: tenantData } = useGetTenant(id || '')
  const { data: membersData, isLoading: membersLoading } = useGetTenantMembers(id || '')
  const { data: invitationsData } = useGetTenantInvitations(id || '')
  const inviteMember = useInviteMember(id || '')
  const removeMember = useRemoveMember(id || '')
  const cancelInvitation = useCancelInvitation(id || '')

  const tenant = tenantData?.data
  const members = membersData?.data || []
  const invitations = invitationsData?.data?.filter((i) => i.status === 'pending') || []

  const form = useForm<z.infer<typeof inviteMemberSchema>>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: {
      email: '',
      role: 'VIEWER',
    },
  })

  const onInvite = async (values: z.infer<typeof inviteMemberSchema>) => {
    try {
      await inviteMember.mutateAsync(values as InviteMemberRequest)
      toast({
        title: 'Invitation sent',
        description: `An invitation has been sent to ${values.email}.`,
      })
      form.reset()
      setInviteOpen(false)
    } catch (err) {
      toast({
        title: 'Failed to send invitation',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleRemoveMember = async (userId: string) => {
    try {
      await removeMember.mutateAsync(userId)
      toast({
        title: 'Member removed',
        description: 'The member has been removed from this tenant.',
      })
    } catch (err) {
      toast({
        title: 'Failed to remove member',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleCancelInvitation = async (invitationId: string) => {
    try {
      await cancelInvitation.mutateAsync(invitationId)
      toast({
        title: 'Invitation cancelled',
        description: 'The invitation has been cancelled.',
      })
    } catch (err) {
      toast({
        title: 'Failed to cancel invitation',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  return (
    <DomainPage
      domain="tenant"
      title="Tenant Members"
      description={`Manage members of ${tenant?.name || 'tenant'}`}
      backTo={`/app/tenant/${id}`}
      actions={
        <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
          <DialogTrigger asChild>
            <Button>
              <UserPlus className="h-4 w-4 mr-2" />
              Invite Member
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={form.handleSubmit(onInvite)}>
              <DialogHeader>
                <DialogTitle>Invite Team Member</DialogTitle>
                <DialogDescription>
                  Send an invitation to join this tenant.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="invite-email">Email Address</Label>
                  <Input
                    id="invite-email"
                    type="email"
                    placeholder="colleague@company.com"
                    {...form.register('email')}
                  />
                  {form.formState.errors.email && (
                    <p className="text-sm text-destructive">{form.formState.errors.email.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-role">Role</Label>
                  <Select
                    value={inviteRole}
                    onValueChange={(v) => {
                      setInviteRole(v as InviteRole)
                      form.setValue('role', v as InviteRole)
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(['ADMIN', 'OPERATOR', 'VIEWER'] as const).map((role) => (
                        <SelectItem key={role} value={role}>
                          <div>
                            <div className="font-medium">{TENANT_ROLE_LABELS[role]}</div>
                            <div className="text-xs text-muted-foreground">
                              {TENANT_ROLE_DESCRIPTIONS[role]}
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setInviteOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={inviteMember.isPending}>
                  {inviteMember.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Send Invitation
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      }
    >
      <div className="space-y-6">
        {/* Members Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Members ({members.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {membersLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : members.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No members yet. Invite someone to get started.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead className="w-12"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {members.map((member) => (
                    <TableRow key={member.id}>
                      <TableCell className="font-medium">{member.userName}</TableCell>
                      <TableCell className="text-muted-foreground">{member.userEmail}</TableCell>
                      <TableCell>
                        <Badge variant={member.role === 'OWNER' ? 'default' : 'outline'}>
                          {TENANT_ROLE_LABELS[member.role] || member.role}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(member.joinedAt).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {member.role !== 'OWNER' && (
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Remove Member?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will remove {member.userName} from this tenant.
                                  They will lose access to all tenant resources.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleRemoveMember(member.userId)}
                                  className="bg-destructive text-destructive-foreground"
                                >
                                  Remove Member
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Pending Invitations */}
        {invitations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Pending Invitations ({invitations.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead className="w-12"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invitations.map((invitation) => (
                    <TableRow key={invitation.id}>
                      <TableCell className="font-medium">{invitation.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {TENANT_ROLE_LABELS[invitation.role] || invitation.role}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(invitation.expiresAt).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleCancelInvitation(invitation.id)}
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </DomainPage>
  )
}

// ============================================
// Isolation Check Page
// ============================================

export function IsolationCheck() {
  const { data, isLoading, error, refetch } = useGetIsolationCheck()
  const result = data?.data
  const allPassed = result?.passed ?? false
  const checks = result?.checks ?? []

  if (isLoading) {
    return (
      <DomainPage domain="tenant" title="Isolation Check" description="Verifying tenant isolation...">
        <Card>
          <CardContent className="py-6">
            <div className="flex items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <p>Running isolation checks...</p>
            </div>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  if (error) {
    return (
      <DomainPage domain="tenant" title="Isolation Check" description="Verify tenant data isolation">
        <Card className="border-destructive">
          <CardContent className="py-6 text-center">
            <XCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive">Failed to run isolation checks.</p>
            <Button variant="outline" className="mt-4" onClick={() => refetch()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="tenant"
      title="Isolation Check"
      description="Verify tenant data isolation"
      actions={
        <Button variant="outline" onClick={() => refetch()}>
          <Shield className="h-4 w-4 mr-2" />
          Run Again
        </Button>
      }
    >
      {/* Summary */}
      <Card className={allPassed ? 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950' : 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950'}>
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
              {result?.checkedAt && (
                <p className="text-xs text-muted-foreground mt-1">
                  Last checked: {new Date(result.checkedAt).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Check Results */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Isolation Checks ({checks.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {checks.map((check, index) => (
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
