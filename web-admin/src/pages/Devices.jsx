import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesAPI, contentAPI, clientAPI } from '../services/api'
import { Monitor, Tv, Plus, Trash2, Activity, CheckCircle, FileImage, ArrowRight, ArrowLeft } from 'lucide-react'

export default function Devices() {
  const queryClient = useQueryClient()
  const [showTVForm, setShowTVForm] = useState(false)
  const [showMonitorForm, setShowMonitorForm] = useState(false)
  const [showActivateForm, setShowActivateForm] = useState(false)
  const [showContentModal, setShowContentModal] = useState(false)
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
      alert('TV registered successfully!')
    },
  })

  // Generate Monitor Code mutation
  const generateMonitorMutation = useMutation({
    mutationFn: devicesAPI.generateMonitorCode,
    onSuccess: (data) => {
      queryClient.invalidateQueries(['devices'])
      setShowMonitorForm(false)
      alert(`Monitor code generated: ${data.data.unique_code}\nExpires in 10 minutes`)
    },
  })

  // Activate Monitor mutation
  const activateMonitorMutation = useMutation({
    mutationFn: devicesAPI.activateMonitor,
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      setShowActivateForm(false)
      alert('Monitor activated successfully!')
    },
  })

  // Update device mutation (for activating)
  const updateDeviceMutation = useMutation({
    mutationFn: ({ id, data }) => devicesAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      alert('Device activated successfully!')
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Failed to activate device')
    }
  })

  // Delete device mutation
  const deleteDeviceMutation = useMutation({
    mutationFn: devicesAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      alert('Device deleted successfully!')
    },
  })

  return (
    <div>
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
          <button
            onClick={() => setShowMonitorForm(true)}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Monitor className="w-5 h-5 mr-2" />
            Generate Monitor Code
          </button>
          <button
            onClick={() => setShowActivateForm(true)}
            className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Activity className="w-5 h-5 mr-2" />
            Activate Monitor
          </button>
        </div>
      </div>

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
            {devicesData?.devices?.map((device) => (
              <tr
                key={device.id}
                onClick={() => {
                  if (device.status === 'active') {
                    setSelectedDevice(device)
                    setShowContentModal(true)
                  }
                }}
                className={device.status === 'active' ? 'cursor-pointer hover:bg-blue-50 transition-colors' : ''}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="font-mono font-bold text-blue-600">{device.id}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {device.device_type === 'tv' ? (
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
      {showTVForm && <TVRegisterForm onClose={() => setShowTVForm(false)} onSubmit={registerTVMutation.mutate} />}

      {/* Generate Monitor Code Modal */}
      {showMonitorForm && <MonitorCodeForm onClose={() => setShowMonitorForm(false)} onSubmit={generateMonitorMutation.mutate} />}

      {/* Activate Monitor Modal */}
      {showActivateForm && <ActivateMonitorForm onClose={() => setShowActivateForm(false)} onSubmit={activateMonitorMutation.mutate} />}

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
    </div>
  )
}

function TVRegisterForm({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    device_name: '',
    ip_address: '',
    passphrase: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Register TV</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Device Name</label>
            <input
              type="text"
              value={formData.device_name}
              onChange={(e) => setFormData({...formData, device_name: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">IP Address</label>
            <input
              type="text"
              value={formData.ip_address}
              onChange={(e) => setFormData({...formData, ip_address: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="192.168.1.100"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Passphrase</label>
            <input
              type="text"
              value={formData.passphrase}
              onChange={(e) => setFormData({...formData, passphrase: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-blue-600 text-white py-2 rounded-lg">Register</button>
            <button type="button" onClick={onClose} className="flex-1 bg-gray-200 py-2 rounded-lg">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function MonitorCodeForm({ onClose, onSubmit }) {
  const [deviceName, setDeviceName] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ device_name: deviceName })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Generate Monitor Code</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Device Name</label>
            <input
              type="text"
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-green-600 text-white py-2 rounded-lg">Generate</button>
            <button type="button" onClick={onClose} className="flex-1 bg-gray-200 py-2 rounded-lg">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ActivateMonitorForm({ onClose, onSubmit }) {
  const [code, setCode] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ unique_code: code })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Activate Monitor</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Activation Code</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 border rounded-lg text-center text-2xl font-mono"
              placeholder="ABC123"
              maxLength={6}
              required
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-purple-600 text-white py-2 rounded-lg">Activate</button>
            <button type="button" onClick={onClose} className="flex-1 bg-gray-200 py-2 rounded-lg">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function AssignContentModal({ device, onClose }) {
  const queryClient = useQueryClient()

  // Fetch all content
  const { data: contentData } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  // Fetch device playlist to see what's assigned
  const { data: playlistData } = useQuery({
    queryKey: ['device-playlist', device.id],
    queryFn: () => clientAPI.getPlaylist(device.id).then(res => res.data),
  })

  // Assign content mutation
  const assignMutation = useMutation({
    mutationFn: ({ contentId }) => contentAPI.assign(contentId, {
      device_id: device.id,
      priority: 0
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['device-playlist', device.id])
      queryClient.invalidateQueries(['devices'])
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Unassign content mutation
  const unassignMutation = useMutation({
    mutationFn: ({ contentId }) => contentAPI.unassign(contentId, {
      device_id: device.id,
      priority: 0
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['device-playlist', device.id])
      queryClient.invalidateQueries(['devices'])
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Unassignment failed')
    }
  })

  const handleAssign = (contentId) => {
    assignMutation.mutate({ contentId })
  }

  const handleUnassign = (contentId) => {
    unassignMutation.mutate({ contentId })
  }

  const assignedContentIds = playlistData?.playlist?.map(item => item.content_id) || []
  const allContent = contentData?.items || []
  const unassignedContent = allContent.filter(c => !assignedContentIds.includes(c.id))
  const assignedContent = allContent.filter(c => assignedContentIds.includes(c.id))

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center">
            {device.device_type === 'tv' ? (
              <Tv className="w-6 h-6 text-blue-600 mr-3" />
            ) : (
              <Monitor className="w-6 h-6 text-green-600 mr-3" />
            )}
            <h2 className="text-2xl font-bold">Assign Content: {device.device_name}</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">
            ✕
          </button>
        </div>

        {/* Two-column layout */}
        <div className="flex-1 grid grid-cols-2 gap-6 p-6 overflow-hidden min-h-0">
          {/* Left: Unassigned Content */}
          <div className="flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="font-bold text-gray-800 text-lg">Available Content</h3>
              <span className="text-sm text-gray-600">
                {unassignedContent.length} items
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 pr-2 min-h-0">
              {unassignedContent.map((content) => (
                <div
                  key={content.id}
                  onClick={() => handleAssign(content.id)}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors group"
                >
                  <div className="flex items-center flex-1 min-w-0">
                    <div className="flex-shrink-0 w-16 h-16 bg-gray-200 rounded mr-3 overflow-hidden">
                      <img
                        src={`http://192.168.5.12:8001/api/content/${content.id}/image`}
                        alt={content.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none'
                        }}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">{content.title}</p>
                      <p className="text-sm text-gray-600">
                        {content.content_type.toUpperCase()} • {content.duration}s
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors flex-shrink-0 ml-2" />
                </div>
              ))}
              {unassignedContent.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <FileImage className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>All content assigned</p>
                </div>
              )}
            </div>
          </div>

          {/* Right: Assigned Content */}
          <div className="flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="font-bold text-gray-800 text-lg">Assigned Content</h3>
              <span className="text-sm text-gray-600">
                {assignedContent.length} items
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 pr-2 min-h-0">
              {assignedContent.map((content) => (
                <div
                  key={content.id}
                  onClick={() => handleUnassign(content.id)}
                  className="flex items-center justify-between p-4 bg-green-50 rounded-lg hover:bg-red-50 cursor-pointer transition-colors group"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-400 group-hover:text-red-600 transition-colors flex-shrink-0 mr-2" />
                  <div className="flex items-center flex-1 min-w-0">
                    <div className="flex-shrink-0 w-16 h-16 bg-gray-200 rounded mr-3 overflow-hidden">
                      <img
                        src={`http://192.168.5.12:8001/api/content/${content.id}/image`}
                        alt={content.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none'
                        }}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">{content.title}</p>
                      <p className="text-sm text-gray-600">
                        {content.content_type.toUpperCase()} • {content.duration}s
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {assignedContent.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <FileImage className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No content assigned</p>
                  <p className="text-xs mt-1">Click content from left to assign</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
