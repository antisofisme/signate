import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesAPI } from '../services/api'
import { Tv } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'

// Components
import TVRegisterModal from '../components/devices/modals/TVRegisterModal'
import AssignContentModal from '../components/devices/modals/AssignContentModal'
import DeviceInfoModal from '../components/devices/modals/DeviceInfoModal'
import PendingDeviceCard from '../components/devices/PendingDeviceCard'
import DeviceTableRow from '../components/devices/DeviceTableRow'

export default function Devices() {
  const queryClient = useQueryClient()
  const [showTVForm, setShowTVForm] = useState(false)
  const [showContentModal, setShowContentModal] = useState(false)
  const [showDeviceInfoModal, setShowDeviceInfoModal] = useState(false)
  const [selectedDevice, setSelectedDevice] = useState(null)

  // Fetch devices
  const { data: devicesData, isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => {
      console.log('Devices API Response:', res.data)
      return res.data
    }),
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

  const handleApprove = (deviceId) => {
    updateDeviceMutation.mutate({
      id: deviceId,
      data: { status: 'active' }
    })
  }

  const handleRowClick = (device) => {
    setSelectedDevice(device)
    setShowContentModal(true)
  }

  const handleEdit = (device) => {
    setSelectedDevice(device)
    setShowDeviceInfoModal(true)
  }

  const handleDelete = (deviceId) => {
    deleteDeviceMutation.mutate(deviceId)
  }

  const pendingDevices = devicesData?.devices?.filter(d => d.status === 'pending') || []
  const activeDevices = devicesData?.devices?.filter(d => d.status === 'active') || []

  return (
    <div>
      <Toaster />

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Devices</h1>
        <button
          onClick={() => setShowTVForm(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Tv className="w-5 h-5 mr-2" />
          Register TV
        </button>
      </div>

      {/* Debug Info */}
      <div className="mb-4 p-3 bg-blue-100 border border-blue-300 rounded">
        <p className="text-sm">
          <strong>Debug Info:</strong> Total devices: {devicesData?.devices?.length || 0} |
          Pending: {pendingDevices.length}
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

      {/* Devices Table */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP/Code</th>
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
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {showTVForm && (
        <TVRegisterModal
          onClose={() => setShowTVForm(false)}
          onSubmit={registerTVMutation.mutate}
        />
      )}

      {showContentModal && selectedDevice && (
        <AssignContentModal
          device={selectedDevice}
          onClose={() => {
            setShowContentModal(false)
            setSelectedDevice(null)
          }}
        />
      )}

      {showDeviceInfoModal && selectedDevice && (
        <DeviceInfoModal
          device={selectedDevice}
          onClose={() => {
            setShowDeviceInfoModal(false)
            setSelectedDevice(null)
          }}
        />
      )}
    </div>
  )
}
