import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesAPI } from '../services/api'
import { Tv } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'

// Components
import TVRegisterModal from '../components/devices/modals/TVRegisterModal'
import DeviceDetailModal from '../components/devices/modals/DeviceDetailModal'
import Button from '../components/shared/Button'
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

  const pendingDevices = devicesData?.devices?.filter(d => d.status === 'pending') || []
  const activeDevices = devicesData?.devices?.filter(d => d.status === 'active') || []
  const inactiveDevices = devicesData?.devices?.filter(d => d.status === 'inactive') || []

  return (
    <div>
      <Toaster />

      {/* Header */}
      <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
        <div className="flex items-center justify-between pt-4">
          <h1 className="text-3xl font-bold text-gray-800">Devices</h1>
          <Button
            onClick={() => setShowTVForm(true)}
            variant="primary"
            leftIcon={<Tv className="w-5 h-5" />}
          >
            Register TV
          </Button>
        </div>
      </div>

      {/* Debug Info */}
      <div className="mb-4 p-3 bg-blue-100 border border-blue-300 rounded">
        <p className="text-sm">
          <strong>Debug Info:</strong> Total devices: {devicesData?.devices?.length || 0} |
          Pending: {pendingDevices.length} | Active: {activeDevices.length} | Released: {inactiveDevices.length}
        </p>
      </div>

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
      <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">
            Active Devices ({activeDevices.length})
          </h2>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code/UUID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Seen</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
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

      {/* Released Devices Section */}
      {inactiveDevices.length > 0 && (
        <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
          <div className="px-6 py-4 bg-gray-100 border-b border-gray-300">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-500 rounded-full mr-3"></div>
              <h2 className="text-xl font-bold text-gray-700">
                Released Devices ({inactiveDevices.length})
              </h2>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Devices that have been released from viewers. They can be reactivated or deleted.
            </p>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Released At</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
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
      )}

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
