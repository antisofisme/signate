import { useState } from 'react'
import { Settings as SettingsIcon, Save, Globe, Key } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@/components/ui'
import { useAuthStore } from '@/lib/store'
import { toast } from 'sonner'

export function Settings() {
  const { tenantId, token } = useAuthStore()
  const [apiUrl, setApiUrl] = useState(
    localStorage.getItem('api_url') || import.meta.env.VITE_API_URL || 'http://localhost:8003/api/v1'
  )
  const [tempTenantId, setTempTenantId] = useState(tenantId || '')
  const [tempToken, setTempToken] = useState(token || '')

  const handleSave = () => {
    localStorage.setItem('api_url', apiUrl)
    localStorage.setItem('tenant_id', tempTenantId)
    localStorage.setItem('auth_token', tempToken)
    toast.success('Settings saved. Refresh to apply changes.')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-500">Configure application settings</p>
      </div>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            API Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">API Base URL</label>
            <Input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://localhost:8003/api/v1"
            />
            <p className="text-xs text-gray-500 mt-1">
              The base URL for the ATLAS Chat API
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Authentication */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Authentication
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Tenant ID</label>
            <Input
              value={tempTenantId}
              onChange={(e) => setTempTenantId(e.target.value)}
              placeholder="your-tenant-id"
            />
            <p className="text-xs text-gray-500 mt-1">
              Your tenant identifier for multi-tenant access
            </p>
          </div>

          <div>
            <label className="text-sm font-medium">JWT Token / API Key</label>
            <Input
              type="password"
              value={tempToken}
              onChange={(e) => setTempToken(e.target.value)}
              placeholder="your-jwt-token-or-api-key"
            />
            <p className="text-xs text-gray-500 mt-1">
              Authentication token for API access
            </p>
          </div>
        </CardContent>
      </Card>

      {/* System Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="h-5 w-5" />
            System Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm font-medium">Frontend Version</p>
              <p className="text-gray-600">1.0.0</p>
            </div>
            <div>
              <p className="text-sm font-medium">Environment</p>
              <p className="text-gray-600">{import.meta.env.MODE}</p>
            </div>
            <div>
              <p className="text-sm font-medium">API URL</p>
              <p className="text-gray-600 break-all">{apiUrl}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Current Tenant</p>
              <p className="text-gray-600">{tenantId || 'Not set'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave}>
          <Save className="h-4 w-4 mr-2" />
          Save Settings
        </Button>
      </div>
    </div>
  )
}
