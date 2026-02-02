import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Key, Trash2, Copy, Eye, EyeOff } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@/components/ui'
import { listAPIKeys, createAPIKey, revokeAPIKey, listTenants } from '@/lib/api'
import { formatDate, copyToClipboard } from '@/lib/utils'
import { toast } from 'sonner'
import type { APIKey, APIKeyWithSecret, APIKeyFormData, TenantConfig } from '@/types'

const AVAILABLE_PERMISSIONS = [
  { id: 'chat.read', label: 'Read Chat' },
  { id: 'chat.write', label: 'Write Chat' },
  { id: 'session.read', label: 'Read Sessions' },
  { id: 'session.write', label: 'Write Sessions' },
  { id: 'knowledge.read', label: 'Read Knowledge' },
  { id: 'knowledge.write', label: 'Write Knowledge' },
  { id: 'admin', label: 'Admin Access' },
]

export function APIKeys() {
  const [selectedTenant, setSelectedTenant] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [newApiKey, setNewApiKey] = useState<string | null>(null)
  const [showKey, setShowKey] = useState(false)
  const [formData, setFormData] = useState<APIKeyFormData>({
    name: '',
    permissions: ['chat.read', 'chat.write'],
    rate_limit_per_minute: 100,
    expires_in_days: 90,
  })

  const queryClient = useQueryClient()

  const { data: tenants } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => listTenants(),
  })

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ['apiKeys', selectedTenant],
    queryFn: () => listAPIKeys(selectedTenant),
    enabled: !!selectedTenant,
  })

  const createMutation = useMutation({
    mutationFn: (data: APIKeyFormData) => createAPIKey(selectedTenant, data),
    onSuccess: (response: APIKeyWithSecret) => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys', selectedTenant] })
      setNewApiKey(response.api_key)
      setShowForm(false)
      setFormData({
        name: '',
        permissions: ['chat.read', 'chat.write'],
        rate_limit_per_minute: 100,
        expires_in_days: 90,
      })
      toast.success('API key created')
    },
    onError: () => {
      toast.error('Failed to create API key')
    },
  })

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => revokeAPIKey(selectedTenant, keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys', selectedTenant] })
      toast.success('API key revoked')
    },
    onError: () => {
      toast.error('Failed to revoke API key')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name) return
    createMutation.mutate(formData)
  }

  const handleRevoke = (keyId: string) => {
    if (confirm('Are you sure you want to revoke this API key? This cannot be undone.')) {
      revokeMutation.mutate(keyId)
    }
  }

  const handleCopy = async (text: string) => {
    await copyToClipboard(text)
    toast.success('Copied to clipboard')
  }

  const togglePermission = (permId: string) => {
    setFormData((prev) => ({
      ...prev,
      permissions: prev.permissions.includes(permId)
        ? prev.permissions.filter((p) => p !== permId)
        : [...prev.permissions, permId],
    }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">API Keys</h1>
          <p className="text-gray-500">Manage programmatic access</p>
        </div>
        {selectedTenant && (
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4 mr-2" />
            New API Key
          </Button>
        )}
      </div>

      {/* New Key Display */}
      {newApiKey && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-green-700 mb-3">
              <Key className="h-5 w-5" />
              <span className="font-medium">New API Key Created</span>
            </div>
            <p className="text-sm text-green-600 mb-3">
              Make sure to copy your API key now. You won't be able to see it again!
            </p>
            <div className="flex items-center gap-2 bg-white rounded-md border p-3">
              <code className="flex-1 text-sm font-mono break-all">
                {showKey ? newApiKey : '••••••••••••••••••••••••••••••••'}
              </code>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleCopy(newApiKey)}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => setNewApiKey(null)}
            >
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

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
            <CardTitle>Create New API Key</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">Name *</label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Production API Key"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Rate Limit (per minute)</label>
                  <Input
                    type="number"
                    min="1"
                    max="1000"
                    value={formData.rate_limit_per_minute}
                    onChange={(e) =>
                      setFormData({ ...formData, rate_limit_per_minute: parseInt(e.target.value) })
                    }
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Permissions</label>
                <div className="grid gap-2 md:grid-cols-3 mt-2">
                  {AVAILABLE_PERMISSIONS.map((perm) => (
                    <label
                      key={perm.id}
                      className="flex items-center gap-2 text-sm cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={formData.permissions.includes(perm.id)}
                        onChange={() => togglePermission(perm.id)}
                        className="rounded border-gray-300"
                      />
                      {perm.label}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Expires In (days)</label>
                <Input
                  type="number"
                  min="1"
                  max="365"
                  value={formData.expires_in_days || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      expires_in_days: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                  placeholder="90 (leave empty for no expiry)"
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit" isLoading={createMutation.isPending}>
                  Create API Key
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* API Keys List */}
      {selectedTenant && (
        <>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : apiKeys?.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Key className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No API keys found. Create your first API key to enable programmatic access.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys?.map((key: APIKey) => (
                <Card key={key.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="rounded-lg bg-purple-100 p-2">
                          <Key className="h-5 w-5 text-purple-600" />
                        </div>
                        <div>
                          <h3 className="font-medium">{key.name}</h3>
                          <code className="text-xs text-gray-500">
                            {key.key_prefix}••••••••
                          </code>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {key.permissions.map((perm) => (
                              <span
                                key={perm}
                                className="px-2 py-0.5 bg-gray-100 rounded text-xs"
                              >
                                {perm}
                              </span>
                            ))}
                          </div>
                          <div className="text-xs text-gray-500 mt-2 space-y-1">
                            <p>Rate limit: {key.rate_limit_per_minute}/min</p>
                            {key.expires_at && <p>Expires: {formatDate(key.expires_at)}</p>}
                            {key.last_used_at && (
                              <p>Last used: {formatDate(key.last_used_at)}</p>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => handleRevoke(key.id)}
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
          <Key className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Select a tenant to view and manage API keys.</p>
        </div>
      )}
    </div>
  )
}
