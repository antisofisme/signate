import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiKeysApi, ApiKey, ApiKeyCreateRequest, ApiKeyCreatedResponse } from '../../shared/api'
import { SkeletonTable } from '../../components/ui/skeleton'
import { ScrollTable } from '../../components/ui/scroll-table'

// =============================================================================
// Permission badges
// =============================================================================

const PERMISSION_COLORS: Record<string, string> = {
  read: 'bg-blue-100 text-blue-800',
  write: 'bg-green-100 text-green-800',
  propose: 'bg-purple-100 text-purple-800',
  admin: 'bg-red-100 text-red-800',
}

function PermissionBadge({ permission }: { permission: string }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${PERMISSION_COLORS[permission] || 'bg-gray-100 text-gray-800'}`}>
      {permission}
    </span>
  )
}

// =============================================================================
// Helper functions
// =============================================================================

function formatTimestamp(timestamp: string | null) {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString()
}

function formatRelativeTime(timestamp: string | null) {
  if (!timestamp) return 'never'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'just now'
}

// =============================================================================
// Create Key Dialog
// =============================================================================

interface CreateKeyDialogProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (response: ApiKeyCreatedResponse) => void
}

function CreateKeyDialog({ isOpen, onClose, onCreated }: CreateKeyDialogProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [permissions, setPermissions] = useState<string[]>(['read'])
  const [expiresIn, setExpiresIn] = useState<string>('never')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      let expiresAt: string | null = null
      if (expiresIn !== 'never') {
        const now = new Date()
        const days = parseInt(expiresIn)
        now.setDate(now.getDate() + days)
        expiresAt = now.toISOString()
      }

      const request: ApiKeyCreateRequest = {
        name,
        description: description || undefined,
        permissions,
        expires_at: expiresAt,
      }

      const response = await apiKeysApi.create(request, 'admin')
      onCreated(response)
      onClose()
      // Reset form
      setName('')
      setDescription('')
      setPermissions(['read'])
      setExpiresIn('never')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create API key')
    } finally {
      setIsSubmitting(false)
    }
  }

  const togglePermission = (perm: string) => {
    if (permissions.includes(perm)) {
      setPermissions(permissions.filter(p => p !== perm))
    } else {
      setPermissions([...permissions, perm])
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Create API Key</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Production MCP Key"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description..."
                rows={2}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Permissions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Permissions</label>
              <div className="flex flex-wrap gap-2">
                {['read', 'write', 'propose', 'admin'].map(perm => (
                  <button
                    key={perm}
                    type="button"
                    onClick={() => togglePermission(perm)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      permissions.includes(perm)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {perm}
                  </button>
                ))}
              </div>
            </div>

            {/* Expiration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expiration</label>
              <select
                value={expiresIn}
                onChange={(e) => setExpiresIn(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="never">Never expires</option>
                <option value="7">7 days</option>
                <option value="30">30 days</option>
                <option value="90">90 days</option>
                <option value="365">1 year</option>
              </select>
            </div>

            {/* Error */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !name.trim() || permissions.length === 0}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? 'Creating...' : 'Create Key'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Key Created Dialog (shows full key ONCE)
// =============================================================================

interface KeyCreatedDialogProps {
  keyData: ApiKeyCreatedResponse | null
  onClose: () => void
}

function KeyCreatedDialog({ keyData, onClose }: KeyCreatedDialogProps) {
  const [copied, setCopied] = useState(false)

  if (!keyData) return null

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(keyData.full_key)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-100 rounded-full">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900">API Key Created</h2>
          </div>

          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="text-amber-800 font-medium">Save this key now!</p>
                <p className="text-amber-700 text-sm mt-1">
                  This is the only time you'll see the full API key. Copy it and store it securely.
                </p>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Your API Key</label>
            <div className="flex items-center gap-2">
              <code className="flex-1 p-3 bg-gray-900 text-green-400 rounded-lg text-sm font-mono break-all">
                {keyData.full_key}
              </code>
              <button
                onClick={copyToClipboard}
                className="p-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                title="Copy to clipboard"
              >
                {copied ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className="text-sm text-gray-600 mb-4 space-y-1">
            <p><strong>Name:</strong> {keyData.name}</p>
            <p><strong>Permissions:</strong> {keyData.permissions.join(', ')}</p>
            <p><strong>Expires:</strong> {keyData.expires_at ? formatTimestamp(keyData.expires_at) : 'Never'}</p>
          </div>

          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Confirm Dialog
// =============================================================================

interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  message: string
  confirmLabel: string
  confirmClass?: string
  onConfirm: () => void
  onCancel: () => void
}

function ConfirmDialog({ isOpen, title, message, confirmLabel, confirmClass, onConfirm, onCancel }: ConfirmDialogProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onCancel} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-lg transition-colors ${confirmClass || 'bg-red-600 text-white hover:bg-red-700'}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Main Component
// =============================================================================

export default function ApiKeys() {
  const queryClient = useQueryClient()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [createdKey, setCreatedKey] = useState<ApiKeyCreatedResponse | null>(null)
  const [revokeKeyId, setRevokeKeyId] = useState<string | null>(null)
  const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => apiKeysApi.list(),
    refetchInterval: 30000,
  })

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => apiKeysApi.revoke(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      setRevokeKeyId(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (keyId: string) => apiKeysApi.delete(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      setDeleteKeyId(null)
    },
  })

  const handleKeyCreated = (response: ApiKeyCreatedResponse) => {
    setCreatedKey(response)
    queryClient.invalidateQueries({ queryKey: ['api-keys'] })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-8 w-32 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-4 w-64 bg-gray-200 rounded animate-pulse" />
          </div>
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
        </div>
        <SkeletonTable rows={5} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="mt-1 text-gray-600">
            Manage API keys for MCP Server authentication
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
          <button
            onClick={() => setShowCreateDialog(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Key
          </button>
        </div>
      </div>

      {/* Info Card */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-sm text-blue-800">
            <p className="font-medium">About API Keys</p>
            <p className="mt-1">
              API keys are used to authenticate with the MCP Server. Keys start with <code className="px-1 py-0.5 bg-blue-100 rounded">mk_</code>.
              When you create a key, copy it immediately - it won't be shown again.
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <ScrollTable>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Key</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Permissions</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Used</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data?.keys.map((key: ApiKey) => (
                <tr key={key.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div>
                      <div className="font-medium text-gray-900">{key.name}</div>
                      {key.description && (
                        <div className="text-sm text-gray-500 truncate max-w-xs">{key.description}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-sm font-mono text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      {key.key_prefix}
                    </code>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {key.permissions.map(perm => (
                        <PermissionBadge key={perm} permission={perm} />
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {key.is_active ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                        Revoked
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500" title={formatTimestamp(key.last_used_at)}>
                    {formatRelativeTime(key.last_used_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500" title={formatTimestamp(key.created_at)}>
                    {formatRelativeTime(key.created_at)}
                    <div className="text-xs text-gray-400">by {key.created_by}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {key.is_active && (
                        <button
                          onClick={() => setRevokeKeyId(key.id)}
                          className="text-orange-600 hover:text-orange-800 text-sm font-medium"
                        >
                          Revoke
                        </button>
                      )}
                      <button
                        onClick={() => setDeleteKeyId(key.id)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {(!data?.keys || data.keys.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              <p className="font-medium">No API keys yet</p>
              <p className="text-sm mt-1">Create your first API key to authenticate with the MCP Server.</p>
            </div>
          )}
        </ScrollTable>
      </div>

      {/* Dialogs */}
      <CreateKeyDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onCreated={handleKeyCreated}
      />

      <KeyCreatedDialog
        keyData={createdKey}
        onClose={() => setCreatedKey(null)}
      />

      <ConfirmDialog
        isOpen={!!revokeKeyId}
        title="Revoke API Key"
        message="Are you sure you want to revoke this API key? It will immediately become invalid and cannot be used for authentication."
        confirmLabel="Revoke Key"
        confirmClass="bg-orange-600 text-white hover:bg-orange-700"
        onConfirm={() => revokeKeyId && revokeMutation.mutate(revokeKeyId)}
        onCancel={() => setRevokeKeyId(null)}
      />

      <ConfirmDialog
        isOpen={!!deleteKeyId}
        title="Delete API Key"
        message="Are you sure you want to permanently delete this API key? This action cannot be undone."
        confirmLabel="Delete Key"
        onConfirm={() => deleteKeyId && deleteMutation.mutate(deleteKeyId)}
        onCancel={() => setDeleteKeyId(null)}
      />
    </div>
  )
}
