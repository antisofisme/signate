import { useState } from 'react'
import { Building2, Plus, Search, Monitor, Users, Calendar, Edit2, Pause, Play, LogIn, Eye, MoreVertical, CheckCircle2, XCircle } from 'lucide-react'
import { Button } from '../../components/shared'

/**
 * TenantsManagement Component
 * Manage all tenant organizations
 *
 * Features:
 * - List all organizations with stats
 * - Add new organization
 * - Search and filter
 * - View, Edit, Suspend/Activate
 * - "Login as" tenant feature
 * - Organization details modal
 *
 * Uses mock data - ready to connect to API
 */
export default function TenantsManagement() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [showAddModal, setShowAddModal] = useState(false)

  // Mock data - replace with API calls
  const tenants = [
    {
      id: 1,
      name: 'Hotel Santika Group',
      email: 'admin@santika.com',
      status: 'active',
      devices: 125,
      users: 18,
      content: 850,
      subscription: 'Enterprise',
      created_at: '2024-01-15',
      last_login: '2 hours ago'
    },
    {
      id: 2,
      name: 'PT. Retail Indonesia',
      email: 'contact@retail.co.id',
      status: 'active',
      devices: 89,
      users: 12,
      content: 456,
      subscription: 'Professional',
      created_at: '2024-02-20',
      last_login: '1 day ago'
    },
    {
      id: 3,
      name: 'Mall Plaza Jakarta',
      email: 'info@mallplaza.com',
      status: 'active',
      devices: 234,
      users: 25,
      content: 1250,
      subscription: 'Enterprise',
      created_at: '2023-11-10',
      last_login: '5 minutes ago'
    },
    {
      id: 4,
      name: 'Hotel Bali Resort',
      email: 'admin@baliresort.com',
      status: 'active',
      devices: 67,
      users: 8,
      content: 320,
      subscription: 'Professional',
      created_at: '2024-03-05',
      last_login: '1 hour ago'
    },
    {
      id: 5,
      name: 'Demo Company',
      email: 'demo@example.com',
      status: 'suspended',
      devices: 15,
      users: 3,
      content: 45,
      subscription: 'Basic',
      created_at: '2024-01-01',
      last_login: '2 weeks ago'
    }
  ]

  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         tenant.email.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || tenant.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const handleLoginAs = (tenant) => {
    // TODO: Implement login as tenant
    alert(`Login as ${tenant.name} - This will switch to tenant view`)
  }

  const handleSuspend = (tenant) => {
    // TODO: Implement suspend
    alert(`Suspend ${tenant.name}`)
  }

  const handleActivate = (tenant) => {
    // TODO: Implement activate
    alert(`Activate ${tenant.name}`)
  }

  const getSubscriptionBadge = (subscription) => {
    const badges = {
      'Enterprise': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
      'Professional': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      'Basic': 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
    return badges[subscription] || badges.Basic
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Organizations Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage all tenant organizations and their subscriptions
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<Plus className="w-5 h-5" />}
          onClick={() => setShowAddModal(true)}
        >
          Add Organization
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search organizations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
          </select>

          <select
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
          >
            <option>All Plans</option>
            <option>Enterprise</option>
            <option>Professional</option>
            <option>Basic</option>
          </select>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Organizations</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{tenants.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Active</p>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
            {tenants.filter(t => t.status === 'active').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Suspended</p>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
            {tenants.filter(t => t.status === 'suspended').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Devices</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
            {tenants.reduce((sum, t) => sum + t.devices, 0)}
          </p>
        </div>
      </div>

      {/* Tenants Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredTenants.map((tenant) => (
          <div
            key={tenant.id}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 hover:shadow-lg transition-shadow overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Building2 className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-gray-900 dark:text-white text-lg truncate">
                      {tenant.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {tenant.email}
                    </p>
                  </div>
                </div>
                {tenant.status === 'active' ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                )}
              </div>

              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSubscriptionBadge(tenant.subscription)}`}>
                  {tenant.subscription}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  tenant.status === 'active'
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                    : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                }`}>
                  {tenant.status}
                </span>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 p-6 bg-gray-50 dark:bg-gray-700/50">
              <div className="text-center">
                <Monitor className="w-5 h-5 text-purple-600 dark:text-purple-400 mx-auto mb-1" />
                <p className="text-lg font-bold text-gray-900 dark:text-white">{tenant.devices}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Devices</p>
              </div>
              <div className="text-center">
                <Users className="w-5 h-5 text-blue-600 dark:text-blue-400 mx-auto mb-1" />
                <p className="text-lg font-bold text-gray-900 dark:text-white">{tenant.users}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Users</p>
              </div>
              <div className="text-center">
                <Calendar className="w-5 h-5 text-green-600 dark:text-green-400 mx-auto mb-1" />
                <p className="text-lg font-bold text-gray-900 dark:text-white">{tenant.content}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Content</p>
              </div>
            </div>

            {/* Actions */}
            <div className="p-4 flex items-center gap-2">
              <Button
                variant="primary"
                size="sm"
                leftIcon={<LogIn className="w-4 h-4" />}
                onClick={() => handleLoginAs(tenant)}
                className="flex-1"
              >
                Login as
              </Button>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<Eye className="w-4 h-4" />}
                className="flex-1"
              >
                View
              </Button>
              {tenant.status === 'active' ? (
                <Button
                  variant="warning"
                  size="sm"
                  leftIcon={<Pause className="w-4 h-4" />}
                  onClick={() => handleSuspend(tenant)}
                >
                  Suspend
                </Button>
              ) : (
                <Button
                  variant="success"
                  size="sm"
                  leftIcon={<Play className="w-4 h-4" />}
                  onClick={() => handleActivate(tenant)}
                >
                  Activate
                </Button>
              )}
            </div>

            {/* Footer Info */}
            <div className="px-6 pb-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>Created: {new Date(tenant.created_at).toLocaleDateString()}</span>
              <span>Last login: {tenant.last_login}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredTenants.length === 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-12 text-center">
          <Building2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No organizations found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Try adjusting your search or filters
          </p>
        </div>
      )}

      {/* Add Modal Placeholder */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Add New Organization
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Modal form will be implemented here
            </p>
            <Button
              variant="secondary"
              onClick={() => setShowAddModal(false)}
              className="w-full"
            >
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
