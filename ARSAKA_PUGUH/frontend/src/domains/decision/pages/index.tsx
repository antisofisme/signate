/**
 * Decision Domain - Pages
 * 4 MUTATIONS: Create Rule Draft, Request Activation, Update Rule, Delete Rule
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { DomainPage, ReadOnlyNotice, MutationWarning } from '@/components/layout/DomainPage'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import {
  Plus,
  History,
  FileText,
  GitBranch,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Pencil,
  Trash2,
} from 'lucide-react'
import {
  useGetRules,
  useGetRule,
  useGetRuleVersions,
  useGetDecisionTypes,
  useGetDecisionHistory,
  useGetDecision,
  useCreateRuleDraft,
  useRequestActivation,
  useUpdateRule,
  useDeleteRule,
} from '../api'
import { useRuleFilters, useRuleStatusBadge, useRuleForm, useEditRuleForm, useActivationForm } from '../hooks'
import type { RuleStatus } from '../types'

// ============================================
// Rule List Page
// ============================================

export function RuleList() {
  const navigate = useNavigate()
  const { filters, updateFilter, resetFilters } = useRuleFilters()
  const { data, isLoading, error } = useGetRules(filters)
  const { getStatusLabel, getStatusVariant } = useRuleStatusBadge()

  return (
    <DomainPage
      domain="decision"
      title="Rules"
      description="Manage decision rules"
      actions={
        <Button variant="decision" onClick={() => navigate('/app/decision/rules/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Create Rule Draft
        </Button>
      }
    >
      {/* Filters */}
      <Card className="mb-4">
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search rules..."
                value={filters.search || ''}
                onChange={(e) => updateFilter('search', e.target.value)}
              />
            </div>
            <Select
              value={filters.status || 'all'}
              onValueChange={(v) => updateFilter('status', v === 'all' ? undefined : v as RuleStatus)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="PENDING_ACTIVATION">Pending</SelectItem>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="DEPRECATED">Deprecated</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={resetFilters}>
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Rules Table */}
      <Card>
        <CardContent className="pt-6">
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load rules</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((rule) => (
                  <TableRow key={rule.id}>
                    <TableCell className="font-medium">{rule.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{rule.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(rule.status) as 'success' | 'warning' | 'secondary' | 'outline'}>
                        {getStatusLabel(rule.status)}
                      </Badge>
                    </TableCell>
                    <TableCell>v{rule.version}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(rule.updatedAt).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/app/decision/rules/${rule.id}`)}
                        >
                          View
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/app/decision/rules/${rule.id}/versions`)}
                        >
                          <GitBranch className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data?.items || data.items.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                      No rules found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Rule Detail Page
// ============================================

export function RuleDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: rule, isLoading, error } = useGetRule(id || '')
  const { getStatusLabel, getStatusVariant } = useRuleStatusBadge()
  const deleteRule = useDeleteRule()
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)

  const handleDelete = async () => {
    if (!id) return
    try {
      await deleteRule.mutateAsync(id)
      navigate('/app/decision/rules')
    } catch (err) {
      console.error('Failed to delete rule:', err)
    }
  }

  if (isLoading) {
    return (
      <DomainPage domain="decision" title="Loading..." backTo="/app/decision/rules">
        <Card>
          <CardContent className="py-12">
            <div className="space-y-4">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-64" />
              <Skeleton className="h-32 w-full" />
            </div>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  if (error || !rule) {
    return (
      <DomainPage domain="decision" title="Error" backTo="/app/decision/rules">
        <Card>
          <CardContent className="py-12 text-center text-red-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load rule</p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  const isDraft = rule.status === 'DRAFT'

  return (
    <DomainPage
      domain="decision"
      title={rule.name}
      description={`Rule type: ${rule.type}`}
      badge={{ label: isDraft ? 'EDITABLE' : 'READ-ONLY', variant: isDraft ? 'warning' : 'info' }}
      backTo="/app/decision/rules"
      actions={
        <div className="flex gap-2">
          {isDraft && (
            <>
              <Button variant="outline" onClick={() => navigate(`/app/decision/rules/${id}/edit`)}>
                <Pencil className="h-4 w-4 mr-2" />
                Edit
              </Button>
              <Button variant="decision" onClick={() => navigate(`/app/decision/rules/${id}/activate`)}>
                <Play className="h-4 w-4 mr-2" />
                Request Activation
              </Button>
            </>
          )}
        </div>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Rule Configuration</CardTitle>
                <Badge variant={getStatusVariant(rule.status) as 'success' | 'warning' | 'secondary' | 'outline'}>
                  {getStatusLabel(rule.status)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label className="text-muted-foreground">Description</Label>
                  <p className="mt-1">{rule.description || 'No description'}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">Version</Label>
                    <p className="mt-1 font-mono">v{rule.version}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Type</Label>
                    <p className="mt-1">{rule.type}</p>
                  </div>
                </div>
                <div>
                  <Label className="text-muted-foreground">Rule Logic</Label>
                  <pre className="mt-1 p-4 bg-muted rounded-md text-sm overflow-x-auto">
                    {JSON.stringify(rule.logic || {}, null, 2)}
                  </pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-muted-foreground text-xs">Created</Label>
                <p className="text-sm">{new Date(rule.createdAt).toLocaleString()}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Updated</Label>
                <p className="text-sm">{new Date(rule.updatedAt).toLocaleString()}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-xs">Created By</Label>
                <p className="text-sm">{rule.createdBy || 'System'}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate(`/app/decision/rules/${id}/versions`)}
              >
                <GitBranch className="h-4 w-4 mr-2" />
                View Versions
              </Button>

              <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Rule
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Rule</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to delete the rule "{rule.name}"?
                      <br /><br />
                      <strong className="text-red-600">Warning:</strong> This action cannot be undone.
                      The rule will be permanently removed from the system.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDelete}
                      className="bg-red-600 hover:bg-red-700"
                      disabled={deleteRule.isPending}
                    >
                      {deleteRule.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </CardContent>
          </Card>
        </div>
      </div>
    </DomainPage>
  )
}

// ============================================
// Create Rule Draft Page (MUTATION)
// ============================================

export function CreateRuleDraft() {
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useRuleForm()
  const { data: types } = useGetDecisionTypes()
  const createRule = useCreateRuleDraft()

  const onSubmit = async (data: { name: string; type: string; description?: string }) => {
    try {
      await createRule.mutateAsync(data)
      navigate('/app/decision/rules')
    } catch (err) {
      console.error('Failed to create rule:', err)
    }
  }

  return (
    <DomainPage
      domain="decision"
      title="Create Rule Draft"
      description="Create a new rule in DRAFT status"
      badge={{ label: 'MUTATION', variant: 'warning' }}
      backTo="/app/decision/rules"
    >
      <MutationWarning
        action="CREATE a new rule draft"
        consequences={[
          'Create a rule in DRAFT status',
          'Generate an audit record',
          'Rule will NOT affect live decisions until activated',
        ]}
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Rule Information</CardTitle>
          <CardDescription>
            Rules created will start in DRAFT status and require approval for activation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name *</Label>
              <Input
                id="name"
                placeholder="e.g., high-value-purchase-approval"
                {...register('name')}
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="type">Rule Type *</Label>
              <Select onValueChange={(v) => register('type').onChange({ target: { value: v } })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a type" />
                </SelectTrigger>
                <SelectContent>
                  {types?.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  )) || (
                    <>
                      <SelectItem value="purchase.approval">Purchase Approval</SelectItem>
                      <SelectItem value="security.alert">Security Alert</SelectItem>
                      <SelectItem value="access.control">Access Control</SelectItem>
                    </>
                  )}
                </SelectContent>
              </Select>
              {errors.type && (
                <p className="text-sm text-red-500">{errors.type.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe what this rule does..."
                {...register('description')}
              />
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/app/decision/rules')}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="decision"
                disabled={isSubmitting || createRule.isPending}
              >
                {(isSubmitting || createRule.isPending) && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Create Draft
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Edit Rule Page (MUTATION)
// ============================================

export function EditRule() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: rule, isLoading: loadingRule, error: loadError } = useGetRule(id || '')
  const updateRule = useUpdateRule()
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useEditRuleForm()

  // Set form values when rule data is loaded
  useEffect(() => {
    if (rule) {
      setValue('name', rule.name)
      setValue('description', rule.description || '')
      setValue('conditions', JSON.stringify(rule.conditions || [], null, 2))
      setValue('action', JSON.stringify(rule.logic || {}, null, 2))
    }
  }, [rule, setValue])

  const onSubmit = async (data: { name: string; description?: string; conditions: string; action: string }) => {
    if (!id) return
    try {
      const updateData: { name?: string; description?: string; conditions?: Record<string, unknown>; action?: Record<string, unknown> } = {
        name: data.name,
        description: data.description,
      }

      // Parse JSON fields if provided
      if (data.conditions && data.conditions.trim() !== '') {
        updateData.conditions = JSON.parse(data.conditions)
      }
      if (data.action && data.action.trim() !== '') {
        updateData.action = JSON.parse(data.action)
      }

      await updateRule.mutateAsync({ ruleId: id, data: updateData })
      navigate(`/app/decision/rules/${id}`)
    } catch (err) {
      console.error('Failed to update rule:', err)
    }
  }

  if (loadingRule) {
    return (
      <DomainPage domain="decision" title="Loading..." backTo="/app/decision/rules">
        <Skeleton className="h-64 w-full" />
      </DomainPage>
    )
  }

  if (loadError || !rule) {
    return (
      <DomainPage domain="decision" title="Error" backTo="/app/decision/rules">
        <Card>
          <CardContent className="py-12 text-center text-red-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load rule</p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  // Only allow editing DRAFT rules
  if (rule.status !== 'DRAFT') {
    return (
      <DomainPage domain="decision" title="Cannot Edit" backTo={`/decision/rules/${id}`}>
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-8 w-8 mx-auto mb-2 text-amber-500" />
            <p className="text-lg font-medium">Rule Cannot Be Edited</p>
            <p className="text-muted-foreground mt-2">
              Only rules in DRAFT status can be edited. This rule is currently in {rule.status} status.
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => navigate(`/app/decision/rules/${id}`)}
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="decision"
      title={`Edit: ${rule.name}`}
      description="Update rule configuration"
      badge={{ label: 'MUTATION', variant: 'warning' }}
      backTo={`/decision/rules/${id}`}
    >
      <MutationWarning
        action="UPDATE the rule"
        consequences={[
          'Modify rule configuration',
          'Create an audit record',
          'Increment version number',
        ]}
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Edit Rule</CardTitle>
          <CardDescription>
            Modify the rule configuration. Only DRAFT rules can be edited.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name *</Label>
              <Input
                id="name"
                placeholder="e.g., high-value-purchase-approval"
                {...register('name')}
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe what this rule does..."
                {...register('description')}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="conditions">Conditions (JSON)</Label>
              <Textarea
                id="conditions"
                placeholder='[{"field": "amount", "operator": "gt", "value": 1000}]'
                {...register('conditions')}
                rows={6}
                className="font-mono text-sm"
              />
              {errors.conditions && (
                <p className="text-sm text-red-500">{errors.conditions.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Define rule conditions as JSON array. Each condition should have field, operator, and value.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="action">Action / Logic (JSON)</Label>
              <Textarea
                id="action"
                placeholder='{"approve": true, "notify": ["admin@example.com"]}'
                {...register('action')}
                rows={6}
                className="font-mono text-sm"
              />
              {errors.action && (
                <p className="text-sm text-red-500">{errors.action.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Define the action to take when conditions are met.
              </p>
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(`/app/decision/rules/${id}`)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="decision"
                disabled={isSubmitting || updateRule.isPending}
              >
                {(isSubmitting || updateRule.isPending) && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Rule Versions Page
// ============================================

export function RuleVersions() {
  const { id } = useParams<{ id: string }>()
  const { data: versions, isLoading, error } = useGetRuleVersions(id || '')
  const { getStatusLabel, getStatusVariant } = useRuleStatusBadge()

  return (
    <DomainPage
      domain="decision"
      title="Rule Versions"
      description="Version history for this rule"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      backTo={`/decision/rules/${id}`}
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Version History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load versions</p>
            </div>
          ) : (
            <div className="space-y-4">
              {versions?.map((version, index) => (
                <div
                  key={version.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-2xl font-bold text-muted-foreground">
                      v{version.version}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{version.name}</span>
                        {index === 0 && (
                          <Badge variant="outline">Latest</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {new Date(version.createdAt).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Badge variant={getStatusVariant(version.status) as 'success' | 'warning' | 'secondary' | 'outline'}>
                    {getStatusLabel(version.status)}
                  </Badge>
                </div>
              ))}
              {(!versions || versions.length === 0) && (
                <p className="text-center py-12 text-muted-foreground">
                  No version history available
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Request Activation Page (MUTATION)
// ============================================

export function RequestActivation() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: rule, isLoading: loadingRule } = useGetRule(id || '')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useActivationForm()
  const requestActivation = useRequestActivation()

  const onSubmit = async (data: { reason: string }) => {
    if (!rule) return
    try {
      await requestActivation.mutateAsync({
        ruleId: id!,
        version: rule.version,
        reason: data.reason,
      })
      navigate(`/app/decision/rules/${id}`)
    } catch (err) {
      console.error('Failed to request activation:', err)
    }
  }

  if (loadingRule) {
    return (
      <DomainPage domain="decision" title="Loading..." backTo="/app/decision/rules">
        <Skeleton className="h-64 w-full" />
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="decision"
      title="Request Activation"
      description={`Request activation for rule: ${rule?.name}`}
      badge={{ label: 'MUTATION', variant: 'warning' }}
      backTo={`/decision/rules/${id}`}
    >
      <MutationWarning
        action="REQUEST rule activation"
        consequences={[
          'Create a decision record',
          'Create an approval workflow',
          'Notify approvers',
          'Rule will NOT be active until approved',
        ]}
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Activation Request</CardTitle>
          <CardDescription>
            This will create an approval workflow. The rule will be activated once approved.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-6 p-4 bg-muted rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Rule:</span>
                <span className="ml-2 font-medium">{rule?.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Version:</span>
                <span className="ml-2 font-mono">v{rule?.version}</span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reason">Reason for Activation *</Label>
              <Textarea
                id="reason"
                placeholder="Explain why this rule should be activated..."
                {...register('reason')}
                rows={4}
              />
              {errors.reason && (
                <p className="text-sm text-red-500">{errors.reason.message}</p>
              )}
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(`/app/decision/rules/${id}`)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="decision"
                disabled={isSubmitting || requestActivation.isPending}
              >
                {(isSubmitting || requestActivation.isPending) && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Submit Request
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Decision Types Page
// ============================================

export function DecisionTypes() {
  const { data: types, isLoading, error } = useGetDecisionTypes()

  return (
    <DomainPage
      domain="decision"
      title="Decision Types"
      description="Available decision types in the system"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="decision" />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Available Types
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load types</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {types?.map((type) => (
                <div
                  key={type}
                  className="flex items-center gap-3 p-4 border rounded-lg"
                >
                  <div className="p-2 bg-amber-100 rounded">
                    <FileText className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="font-medium">{type}</p>
                    <p className="text-sm text-muted-foreground">
                      Decision type for {type.split('.')[0]} rules
                    </p>
                  </div>
                </div>
              )) || (
                <p className="col-span-2 text-center py-12 text-muted-foreground">
                  No decision types available
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Decision History Page
// ============================================

export function DecisionHistory() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetDecisionHistory()

  return (
    <DomainPage
      domain="decision"
      title="Decision History"
      description="View all past decisions"
      badge={{ label: 'READ-ONLY', variant: 'info' }}
    >
      <ReadOnlyNotice domain="decision" />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Recent Decisions
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load history</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Decision</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Outcome</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items?.map((decision) => (
                  <TableRow key={decision.id}>
                    <TableCell className="font-medium">{decision.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{decision.type}</Badge>
                    </TableCell>
                    <TableCell>
                      {decision.outcome === 'APPROVED' ? (
                        <Badge variant="success">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Approved
                        </Badge>
                      ) : decision.outcome === 'REJECTED' ? (
                        <Badge variant="destructive">Rejected</Badge>
                      ) : (
                        <Badge variant="warning">
                          <Clock className="h-3 w-3 mr-1" />
                          Pending
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(decision.createdAt).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/app/decision/history/${decision.id}`)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data?.items || data.items.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                      No decisions found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </DomainPage>
  )
}

// ============================================
// Decision Detail Page
// ============================================

export function DecisionDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: decision, isLoading, error } = useGetDecision(id || '')

  if (isLoading) {
    return (
      <DomainPage domain="decision" title="Loading..." backTo="/app/decision/history">
        <Skeleton className="h-64 w-full" />
      </DomainPage>
    )
  }

  if (error || !decision) {
    return (
      <DomainPage domain="decision" title="Error" backTo="/app/decision/history">
        <Card>
          <CardContent className="py-12 text-center text-red-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load decision</p>
          </CardContent>
        </Card>
      </DomainPage>
    )
  }

  return (
    <DomainPage
      domain="decision"
      title={decision.name}
      description={`Decision type: ${decision.type}`}
      badge={{ label: 'READ-ONLY', variant: 'info' }}
      backTo="/app/decision/history"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Decision Details</CardTitle>
                {decision.outcome === 'APPROVED' ? (
                  <Badge variant="success">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Approved
                  </Badge>
                ) : decision.outcome === 'REJECTED' ? (
                  <Badge variant="destructive">Rejected</Badge>
                ) : (
                  <Badge variant="warning">
                    <Clock className="h-3 w-3 mr-1" />
                    Pending
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label className="text-muted-foreground">Description</Label>
                  <p className="mt-1">{decision.description || 'No description'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Input Data</Label>
                  <pre className="mt-1 p-4 bg-muted rounded-md text-sm overflow-x-auto">
                    {JSON.stringify(decision.input || {}, null, 2)}
                  </pre>
                </div>
                <div>
                  <Label className="text-muted-foreground">Output Data</Label>
                  <pre className="mt-1 p-4 bg-muted rounded-md text-sm overflow-x-auto">
                    {JSON.stringify(decision.output || {}, null, 2)}
                  </pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="p-1 bg-green-100 rounded-full">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Created</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(decision.createdAt).toLocaleString()}
                    </p>
                  </div>
                </div>
                {decision.processedAt && (
                  <div className="flex items-start gap-3">
                    <div className="p-1 bg-blue-100 rounded-full">
                      <Clock className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">Processed</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(decision.processedAt).toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DomainPage>
  )
}
