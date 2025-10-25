import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { appsAPI } from '../services/api'
import { Smartphone, Plus, Trash2, Edit2, Download, Upload } from 'lucide-react'
import { showToast } from '../utils/toast'
import { Button } from '../components/shared'

/**
 * Apps Page
 * Manage WebOS TV applications (IPK packages)
 *
 * Features:
 * - List all uploaded apps
 * - Upload new IPK packages
 * - Edit app metadata
 * - Delete apps
 * - Deploy apps to specific devices
 * - View app installation status
 */
export default function Apps() {
  const queryClient = useQueryClient()
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeployModal, setShowDeployModal] = useState(false)
  const [selectedApp, setSelectedApp] = useState(null)

  // Fetch apps
  const { data: appsData, isLoading } = useQuery({
    queryKey: ['apps'],
    queryFn: () => appsAPI.list().then(res => res.data),
  })

  // Upload app mutation
  const uploadMutation = useMutation({
    mutationFn: appsAPI.upload,
    onSuccess: () => {
      queryClient.invalidateQueries(['apps'])
      setShowUploadModal(false)
      showToast.success('App uploaded successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to upload app')
    }
  })

  // Update app mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => appsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['apps'])
      setShowEditModal(false)
      setSelectedApp(null)
      showToast.success('App updated successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to update app')
    }
  })

  // Delete app mutation
  const deleteMutation = useMutation({
    mutationFn: appsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['apps'])
      showToast.success('App deleted successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to delete app')
    }
  })

  const handleEdit = (app) => {
    setSelectedApp(app)
    setShowEditModal(true)
  }

  const handleDeploy = (app) => {
    setSelectedApp(app)
    setShowDeployModal(true)
  }

  const handleDelete = (id, name) => {
    if (confirm(`Delete app "${name}"?\n\nThe IPK file will be permanently removed.`)) {
      deleteMutation.mutate(id)
    }
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A'
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(2)} MB`
  }

  return (
    <div>
      {/* Header */}
      <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
        <div className="flex items-center justify-between pt-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Apps</h1>
            <p className="text-gray-600 text-sm mt-1">
              Manage WebOS TV applications and deploy to devices
            </p>
          </div>
          <Button
            variant="primary"
            leftIcon={<Upload className="w-5 h-5" />}
            onClick={() => setShowUploadModal(true)}
          >
            Upload App
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!appsData?.items || appsData.items.length === 0) && (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <Smartphone className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No Apps Uploaded</h3>
          <p className="text-gray-600 mb-6">
            Upload your first WebOS app (IPK package) to deploy to TV devices
          </p>
          <Button
            variant="primary"
            leftIcon={<Upload className="w-5 h-5" />}
            onClick={() => setShowUploadModal(true)}
          >
            Upload First App
          </Button>
        </div>
      )}

      {/* Apps Table */}
      {!isLoading && appsData?.items && appsData.items.length > 0 && (
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">App Info</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Package ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uploaded</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {appsData.items.map((app) => (
                <tr key={app.id} className="hover:bg-gray-50">
                  {/* App Info */}
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center mr-3">
                        <Smartphone className="w-5 h-5 text-indigo-600" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-800">{app.app_name}</p>
                        {app.description && (
                          <p className="text-sm text-gray-500 line-clamp-1">{app.description}</p>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Package ID */}
                  <td className="px-6 py-4">
                    <span className="font-mono text-sm text-gray-600">{app.package_id}</span>
                  </td>

                  {/* Version */}
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                      v{app.version}
                    </span>
                  </td>

                  {/* File Size */}
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {formatFileSize(app.file_size)}
                  </td>

                  {/* Status */}
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      app.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {app.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>

                  {/* Upload Date */}
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {app.uploaded_at ? new Date(app.uploaded_at).toLocaleDateString() : '-'}
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="primary"
                        size="sm"
                        leftIcon={<Download className="w-4 h-4" />}
                        onClick={() => handleDeploy(app)}
                        title="Deploy to devices"
                      >
                        Deploy
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleEdit(app)}
                        title="Edit app details"
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(app.id, app.app_name)}
                        title="Delete app"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals - Will be created later */}
      {/* {showUploadModal && (
        <AppUploadModal
          onClose={() => setShowUploadModal(false)}
          onSubmit={(formData) => uploadMutation.mutate(formData)}
        />
      )}

      {showEditModal && selectedApp && (
        <AppEditModal
          app={selectedApp}
          onClose={() => {
            setShowEditModal(false)
            setSelectedApp(null)
          }}
          onSubmit={(data) => updateMutation.mutate({ id: selectedApp.id, data })}
        />
      )}

      {showDeployModal && selectedApp && (
        <AppDeployModal
          app={selectedApp}
          onClose={() => {
            setShowDeployModal(false)
            setSelectedApp(null)
          }}
        />
      )} */}
    </div>
  )
}
