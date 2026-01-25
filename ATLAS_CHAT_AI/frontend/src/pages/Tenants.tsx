import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Building2, Check, X } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@/components/ui'
import { listTenants, createTenant, deleteTenant } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'
import type { TenantConfig, TenantFormData } from '@/types'

export function Tenants() {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState<Partial<TenantFormData>>({
    name: '',
    description: '',
    llm_provider: 'openai',
    llm_model: 'gpt-4o-mini',
    llm_temperature: 0.7,
    llm_max_tokens: 1000,
    embedding_provider: 'openai',
    embedding_model: 'text-embedding-3-small',
    rag_strategy: 'hybrid',
    rag_top_k: 5,
    rag_score_threshold: 0.3,
    features_memory_extraction: true,
    features_temporal_memory: true,
    features_streaming: true,
    features_session_summarization: true,
  })

  const queryClient = useQueryClient()

  const { data: tenants, isLoading, error } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => listTenants({ active_only: false }),
  })

  const createMutation = useMutation({
    mutationFn: createTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
      setShowForm(false)
      setFormData({ name: '', description: '' })
      toast.success('Tenant created successfully')
    },
    onError: () => {
      toast.error('Failed to create tenant')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
      toast.success('Tenant deleted')
    },
    onError: () => {
      toast.error('Failed to delete tenant')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name) return
    createMutation.mutate(formData as TenantFormData)
  }

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this tenant?')) {
      deleteMutation.mutate(id)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 p-4">
        Failed to load tenants. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Tenants</h1>
          <p className="text-gray-500">Manage chat tenants and configurations</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-2" />
          New Tenant
        </Button>
      </div>

      {/* Create Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Tenant</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">Name *</label>
                  <Input
                    value={formData.name || ''}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Tenant name"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Description</label>
                  <Input
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Optional description"
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <label className="text-sm font-medium">LLM Provider</label>
                  <select
                    className="w-full h-9 rounded-md border px-3"
                    value={formData.llm_provider}
                    onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
                  >
                    <option value="openai">OpenAI</option>
                    <option value="deepseek">DeepSeek</option>
                    <option value="groq">Groq</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Model</label>
                  <Input
                    value={formData.llm_model || ''}
                    onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
                    placeholder="gpt-4o-mini"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Temperature</label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={formData.llm_temperature || 0.7}
                    onChange={(e) => setFormData({ ...formData, llm_temperature: parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit" isLoading={createMutation.isPending}>
                  Create Tenant
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tenants List */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {tenants?.map((tenant: TenantConfig) => (
          <Card key={tenant.id}>
            <CardHeader className="flex flex-row items-start justify-between pb-2">
              <div className="flex items-center gap-2">
                <div className="rounded-lg bg-blue-100 p-2">
                  <Building2 className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <CardTitle className="text-base">{tenant.name}</CardTitle>
                  <p className="text-xs text-gray-500">{tenant.id.slice(0, 8)}...</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {tenant.is_active ? (
                  <span className="flex items-center gap-1 text-xs text-green-600">
                    <Check className="h-3 w-3" /> Active
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-red-600">
                    <X className="h-3 w-3" /> Inactive
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {tenant.description && (
                <p className="text-sm text-gray-600 mb-3">{tenant.description}</p>
              )}

              <div className="space-y-2 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>LLM</span>
                  <span className="font-medium">{tenant.llm_config.model}</span>
                </div>
                <div className="flex justify-between">
                  <span>RAG Strategy</span>
                  <span className="font-medium capitalize">{tenant.rag_config.strategy}</span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span>{formatDate(tenant.created_at)}</span>
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <Button variant="outline" size="sm" className="flex-1">
                  <Edit2 className="h-3 w-3 mr-1" />
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:bg-red-50"
                  onClick={() => handleDelete(tenant.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {tenants?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No tenants found. Create your first tenant to get started.</p>
        </div>
      )}
    </div>
  )
}
