import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesAPI } from '../services/api'
import { Tv, Search } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'

// Components
import TVRegisterModal from '../components/devices/modals/TVRegisterModal'
import DeviceDetailModal from '../components/devices/modals/DeviceDetailModal'
import { Button, PageHeader, FormInput, LoadingSkeleton } from '../components/shared'
import DeviceEditModal from '../components/devices/modals/DeviceEditModal'
import DeviceLogsModal from '../components/devices/modals/DeviceLogsModal'
import PendingDeviceCard from '../components/devices/PendingDeviceCard'
import DeviceTableRow from '../components/devices/DeviceTableRow'

export default function Devices() {
  const queryClient = useQueryClient()
  const [showTVForm, setShowTVForm] = useState(false)
  const [showDeviceDetailModal, setShowDeviceDetailModal] = useState(false)
  const [showDeviceEditModal, setShowDeviceEditModal] = useState(false)
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('newest')
  const [activeFilter, setActiveFilter] = useState('all')

  // Fetch devices with auto-refresh every 5 seconds
  const { data: devicesData, isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => {
      console.log('Devices API Response:', res.data)
      return res.data
    }),
    refetchInterval: 5000, // Auto-refresh every 5 seconds to show new pending devices
  })

  // Register TV mutation
  const registerTVMutation = useMutation({
    mutationFn: devicesAPI.registerTV,
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      setShowTVForm(false)
      toast.success('TV registered successfully!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to register TV', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Update device mutation (for activating)
  const updateDeviceMutation = useMutation({
    mutationFn: ({ id, data }) => devicesAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      toast.success('Device activated successfully!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to activate device', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Delete device mutation
  const deleteDeviceMutation = useMutation({
    mutationFn: devicesAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      toast.success('Device deleted successfully!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to delete device', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  const handleApprove = useCallback((deviceId) => {
    updateDeviceMutation.mutate({
      id: deviceId,
      data: { status: 'active' }
    })
  }, [updateDeviceMutation])

  const handleRowClick = useCallback((device) => {
    setSelectedDevice(device)
    setShowDeviceDetailModal(true)
  }, [])

  const handleEdit = useCallback((device) => {
    setSelectedDevice(device)
    setShowDeviceEditModal(true)
  }, [])

  const handleDelete = useCallback((deviceId) => {
    deleteDeviceMutation.mutate(deviceId)
  }, [deleteDeviceMutation])

  const handleViewLogs = useCallback((device) => {
    setSelectedDevice(device)
    setShowLogsModal(true)
  }, [])

  // Filter and sort devices
  const filteredAndSortedDevices = useMemo(() => {
    if (!devicesData?.devices) return []

    let filtered = devicesData.devices

    // Apply status filter
    if (activeFilter === 'pending') {
      filtered = filtered.filter(d => d.status === 'pending')
    } else if (activeFilter === 'active') {
      filtered = filtered.filter(d => d.status === 'active')
    } else if (activeFilter === 'inactive') {
      filtered = filtered.filter(d => d.status === 'inactive')
    } else if (activeFilter === 'browser') {
      filtered = filtered.filter(d => d.device_type === 'monitor')
    } else if (activeFilter === 'app') {
      filtered = filtered.filter(d => d.device_type === 'tv')
    }
    // 'all' shows everything

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(device =>
        device.device_name?.toLowerCase().includes(query) ||
        device.ip_address?.toLowerCase().includes(query) ||
        device.pairing_code?.toLowerCase().includes(query)
      )
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at) - new Date(a.created_at)
        case 'oldest':
          return new Date(a.created_at) - new Date(b.created_at)
        case 'name_asc':
          return (a.device_name || '').localeCompare(b.device_name || '')
        case 'name_desc':
          return (b.device_name || '').localeCompare(a.device_name || '')
        default:
          return 0
      }
    })

    return sorted
  }, [devicesData?.devices, searchQuery, sortBy, activeFilter])

  const pendingDevices = filteredAndSortedDevices.filter(d => d.status === 'pending')
  const activeDevices = filteredAndSortedDevices.filter(d => d.status === 'active')
  const inactiveDevices = filteredAndSortedDevices.filter(d => d.status === 'inactive')

  // Calculate stats with filterKey
  const stats = useMemo(() => {
    const total = devicesData?.devices?.length || 0
    const pending = devicesData?.devices?.filter(d => d.status === 'pending').length || 0
    const active = devicesData?.devices?.filter(d => d.status === 'active').length || 0
    const inactive = devicesData?.devices?.filter(d => d.status === 'inactive').length || 0
    const browser = devicesData?.devices?.filter(d => d.device_type === 'monitor').length || 0
    const app = devicesData?.devices?.filter(d => d.device_type === 'tv').length || 0

    return [
      { label: 'All Devices', value: total, color: 'blue', filterKey: 'all' },
      { label: 'Pending', value: pending, color: 'yellow', filterKey: 'pending' },
      { label: 'Active', value: active, color: 'green', filterKey: 'active' },
      { label: 'Inactive', value: inactive, color: 'gray', filterKey: 'inactive' },
      { label: 'Browser', value: browser, color: 'purple', filterKey: 'browser' },
      { label: 'App', value: app, color: 'blue', filterKey: 'app' }
    ]
  }, [devicesData?.devices])

  // Show loading skeleton while fetching
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
        <Toaster />

        {/* PageHeader Skeleton */}
        <div className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 lg:px-8 py-4">
          <div className="h-8 w-32 bg-gray-200 rounded animate-pulse mb-2"></div>
          <div className="h-4 w-64 bg-gray-200 rounded animate-pulse"></div>
        </div>

        {/* Content Area */}
        <div className="pt-40 sm:pt-[172px] lg:pt-44">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {/* Pending Devices Skeleton */}
            <LoadingSkeleton variant="pending-approvals" count={2} className="mb-6" />

            {/* Devices Table Skeleton */}
            <LoadingSkeleton variant="table" count={5} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
      <Toaster />

      <PageHeader
        title="Devices"
        description="Manage and monitor all registered devices"
        actions={
          <Button
            onClick={() => setShowTVForm(true)}
            variant="primary"
            leftIcon={<Tv className="w-5 h-5" />}
          >
            Register TV
          </Button>
        }
        searchBar={
          <div className="flex gap-3 max-w-xl">
            <div className="flex-1">
              <FormInput
                icon={Search}
                type="text"
                placeholder="Search devices..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="newest">Terbaru</option>
              <option value="oldest">Terlama</option>
              <option value="name_asc">Nama: A-Z</option>
              <option value="name_desc">Nama: Z-A</option>
            </select>
          </div>
        }
        stats={stats}
        activeFilter={activeFilter}
        onStatClick={setActiveFilter}
      />

      {/* Content with padding to account for fixed header */}
      {/* pt-40 (160px) mobile, pt-[172px] tablet (custom value between pt-42/168px and pt-44/176px), pt-44 (176px) desktop */}
      <div className="pt-40 sm:pt-[172px] lg:pt-44 animate-fade-in">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Pending Approval Section */}
      {pendingDevices.length > 0 && (
        <div className="mb-6 bg-yellow-50 border-2 border-yellow-200 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse mr-3"></div>
            <h2 className="text-xl font-bold text-yellow-800">
              Pending Approval ({pendingDevices.length})
            </h2>
          </div>
          <div className="grid gap-3">
            {pendingDevices.map(device => (
              <PendingDeviceCard
                key={device.id}
                device={device}
                onApprove={handleApprove}
              />
            ))}
          </div>
        </div>
      )}

      {/* Active Devices Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 overflow-hidden mb-6">
        <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Device</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Platform</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">IP Address</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Code</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Seen</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase sticky right-0 bg-gray-50 dark:bg-gray-700 shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.1)]">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {activeDevices.map((device) => (
              <DeviceTableRow
                key={device.id}
                device={device}
                onRowClick={handleRowClick}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onActivate={handleApprove}
                onViewLogs={handleViewLogs}
              />
            ))}
          </tbody>
        </table>
        </div>
      </div>

      {/* Released Devices Section */}
      {inactiveDevices.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 overflow-hidden mb-6">
          <div className="px-6 py-4 bg-gray-100 dark:bg-gray-700 border-b border-gray-300 dark:border-gray-600">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-500 rounded-full mr-3"></div>
              <h2 className="text-xl font-bold text-gray-700 dark:text-gray-300">
                Released Devices ({inactiveDevices.length})
              </h2>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Devices that have been released from viewers. They can be reactivated or deleted.
            </p>
          </div>
          <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Device</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Platform</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">IP Address</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Released At</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase sticky right-0 bg-gray-50 dark:bg-gray-700 shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.1)]">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {inactiveDevices.map((device) => (
                <DeviceTableRow
                  key={device.id}
                  device={device}
                  onRowClick={handleRowClick}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onActivate={handleApprove}
                  onViewLogs={handleViewLogs}
                />
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}
        </div>
      </div>

      {/* Modals */}
      {showTVForm && (
        <TVRegisterModal
          onClose={() => setShowTVForm(false)}
          onSubmit={registerTVMutation.mutate}
        />
      )}

      {showDeviceDetailModal && selectedDevice && (
        <DeviceDetailModal
          device={selectedDevice}
          onClose={() => {
            setShowDeviceDetailModal(false)
            setSelectedDevice(null)
          }}
          onEdit={handleEdit}
          onViewLogs={handleViewLogs}
          onDelete={handleDelete}
        />
      )}

      {showDeviceEditModal && selectedDevice && (
        <DeviceEditModal
          device={selectedDevice}
          onClose={() => {
            setShowDeviceEditModal(false)
            setSelectedDevice(null)
          }}
          onSave={async () => {
            // Immediately refetch and wait for completion before modal closes
            await queryClient.refetchQueries(['devices'])
          }}
        />
      )}

      {showLogsModal && selectedDevice && (
        <DeviceLogsModal
          device={selectedDevice}
          onClose={() => {
            setShowLogsModal(false)
            setSelectedDevice(null)
          }}
        />
      )}
    </div>
  )
}
