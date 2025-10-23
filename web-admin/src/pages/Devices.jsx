import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesAPI, contentAPI, clientAPI } from '../services/api'
import { Monitor, Tv, Plus, Trash2, CheckCircle, FileImage, ArrowRight, ArrowLeft, Edit } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'

// Modal Components
import TVRegisterModal from '../components/devices/modals/TVRegisterModal'
import AssignContentModal from '../components/devices/modals/AssignContentModal'
import DeviceInfoModal from '../components/devices/modals/DeviceInfoModal'

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

  return (
    <div>
      {/* Toast Notifications */}
      <Toaster />

      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Devices</h1>
        <div className="flex gap-3">
          <button
            onClick={() => setShowTVForm(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Tv className="w-5 h-5 mr-2" />
            Register TV
          </button>
        </div>
      </div>

      {/* Debug: Always show this */}
      <div className="mb-4 p-3 bg-blue-100 border border-blue-300 rounded">
        <p className="text-sm">
          <strong>Debug Info:</strong> Total devices: {devicesData?.devices?.length || 0} |
          Pending: {devicesData?.devices?.filter(d => d.status === 'pending').length || 0}
        </p>
      </div>

      {/* Pending Approval Section */}
      {devicesData?.devices?.filter(d => d.status === 'pending').length > 0 && (
        <div className="mb-6 bg-yellow-50 border-2 border-yellow-200 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse mr-3"></div>
            <h2 className="text-xl font-bold text-yellow-800">
              Pending Approval ({devicesData.devices.filter(d => d.status === 'pending').length})
            </h2>
          </div>
          <div className="grid gap-3">
            {devicesData.devices
              .filter(d => d.status === 'pending')
              .map(device => (
                <div key={device.id} className="bg-white rounded-lg p-4 border-2 border-yellow-300 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`flex items-center justify-center w-12 h-12 rounded-full ${
                      device.device_uuid ? 'bg-blue-100' : 'bg-green-100'
                    }`}>
                      {device.device_uuid ? (
                        <Tv className="w-6 h-6 text-blue-600" />
                      ) : (
                        <Monitor className="w-6 h-6 text-green-600" />
                      )}
                    </div>
                    <div>
                      <p className="font-bold text-gray-800">{device.device_name}</p>
                      <div className="flex items-center gap-3 mt-1">
                        {device.device_uuid ? (
                          <>
                            <span className="text-xs text-gray-500">UUID:</span>
                            <span className="font-mono text-sm text-blue-600 bg-blue-50 px-2 py-1 rounded">
                              {device.device_uuid.substring(0, 13)}...
                            </span>
                            {device.platform && (
                              <span className={`text-xs px-2 py-1 rounded-full ${
                                device.platform === 'webOS' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'
                              }`}>
                                {device.platform}
                              </span>
                            )}
                          </>
                        ) : (
                          <>
                            <span className="text-xs text-gray-500">Code:</span>
                            <span className="font-mono text-lg font-bold text-yellow-600">
                              {device.unique_code || 'N/A'}
                            </span>
                          </>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {device.last_seen ? `Last seen: ${new Date(device.last_seen).toLocaleString()}` : 'Waiting for connection...'}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      updateDeviceMutation.mutate({
                        id: device.id,
                        data: { status: 'active' }
                      })
                    }}
                    className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                  >
                    <CheckCircle className="w-5 h-5" />
                    Approve
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Devices List */}
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
            {console.log('Rendering devices:', devicesData?.devices?.length, 'devices')}
            {devicesData?.devices
              ?.filter(device => device.status === 'active')
              .map((device) => (
              <tr
                key={device.id}
                onClick={() => {
                  setSelectedDevice(device)
                  setShowContentModal(true)
                }}
                className="cursor-pointer hover:bg-blue-50 transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="font-mono font-bold text-blue-600">{device.id}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {device.device_uuid ? (
                      <Tv className="w-5 h-5 text-blue-600 mr-2" />
                    ) : (
                      <Monitor className="w-5 h-5 text-green-600 mr-2" />
                    )}
                    <span className="font-medium">{device.device_name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {device.device_type.toUpperCase()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {device.ip_address || device.unique_code || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    device.status === 'active' ? 'bg-green-100 text-green-700' :
                    device.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {device.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex items-center gap-3">
                    {/* Activate button for pending devices */}
                    {device.status === 'pending' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          if (confirm(`Activate ${device.device_name}?\n\nCode: ${device.unique_code || 'N/A'}`)) {
                            updateDeviceMutation.mutate({
                              id: device.id,
                              data: { status: 'active' }
                            })
                          }
                        }}
                        className="text-green-600 hover:text-green-800"
                        title="Activate device"
                      >
                        <CheckCircle className="w-5 h-5" />
                      </button>
                    )}

                    {/* Edit button - Show device info */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedDevice(device)
                        setShowDeviceInfoModal(true)
                      }}
                      className="text-blue-600 hover:text-blue-800"
                      title="View device information"
                    >
                      <Edit className="w-5 h-5" />
                    </button>

                    {/* Delete button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('Delete this device?')) {
                          deleteDeviceMutation.mutate(device.id)
                        }
                      }}
                      className="text-red-600 hover:text-red-800"
                      title="Delete device"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Register TV Modal */}
      {showTVForm && <TVRegisterModal onClose={() => setShowTVForm(false)} onSubmit={registerTVMutation.mutate} />}

      {/* Content Assignment Modal */}
      {showContentModal && selectedDevice && (
        <AssignContentModal
          device={selectedDevice}
          onClose={() => {
            setShowContentModal(false)
            setSelectedDevice(null)
          }}
        />
      )}

      {/* Device Info Modal */}
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
