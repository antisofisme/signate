import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { contentAPI } from '../../../services/api'
import { showToast } from '../../../utils/toast'
import { validateFileUpload, formatFileSize } from '../../../utils/helpers'
import { Modal, Button, FormInput } from '../../shared'

/**
 * UploadModal Component
 * Modal for uploading multiple content files (images/videos) with bulk upload support
 *
 * Features:
 * - Multiple file selection with validation
 * - File size, MIME type, and magic number validation
 * - Parallel upload processing
 * - Per-file upload progress tracking
 * - File format information and recommendations
 * - Default duration setting for all files
 * - Upload summary (success/fail counts)
 * - Automatic query cache invalidation on success
 *
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSubmit - Optional callback after successful upload
 */
export default function UploadModal({ onClose, onSubmit }) {
  const queryClient = useQueryClient()
  const [files, setFiles] = useState([])
  const [duration, setDuration] = useState(10)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState([])
  const [validating, setValidating] = useState(false)

  const handleFileSelect = async (e) => {
    const selectedFiles = Array.from(e.target.files)

    if (selectedFiles.length === 0) {
      return
    }

    setValidating(true)

    // Validate all files
    const validationResults = await Promise.all(
      selectedFiles.map(file => validateFileUpload(file))
    )

    // Filter out invalid files and show warnings
    const validFiles = []
    const invalidFiles = []

    selectedFiles.forEach((file, index) => {
      const validation = validationResults[index]
      if (validation.isValid) {
        validFiles.push(file)
      } else {
        invalidFiles.push({ file, errors: validation.errors })
      }
    })

    setValidating(false)

    // Show validation errors for invalid files
    if (invalidFiles.length > 0) {
      invalidFiles.forEach(({ file, errors }) => {
        showToast.error(
          `${file.name}: ${errors.join(', ')}`,
          { duration: 6000 }
        )
      })
    }

    // Show success message for valid files
    if (validFiles.length > 0) {
      showToast.success(
        `${validFiles.length} file(s) validated successfully`,
        { duration: 3000 }
      )
    }

    // Only set valid files
    if (validFiles.length > 0) {
      setFiles(validFiles)
      // Initialize progress for each valid file
      setUploadProgress(validFiles.map(() => ({ status: 'pending', error: null })))
    } else {
      setFiles([])
      setUploadProgress([])
    }
  }

  const handleBulkUpload = async (e) => {
    e.preventDefault()
    if (files.length === 0) {
      showToast.warning('Please select at least one file')
      return
    }

    setUploading(true)
    let successCount = 0
    let failCount = 0

    // Upload all files in parallel
    const uploadPromises = files.map(async (file, index) => {
      try {
        // Update status to uploading
        setUploadProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'uploading', error: null }
          return newProgress
        })

        const formData = new FormData()
        formData.append('file', file)
        formData.append('title', file.name.split('.')[0]) // Use filename as title
        formData.append('description', '')
        formData.append('duration', duration)
        formData.append('is_active', 'true')

        await contentAPI.upload(formData)

        // Update status to success
        setUploadProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'success', error: null }
          return newProgress
        })
        successCount++
      } catch (error) {
        // Update status to failed
        setUploadProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = {
            status: 'failed',
            error: error.response?.data?.detail || 'Upload failed'
          }
          return newProgress
        })
        failCount++
      }
    })

    // Wait for all uploads to complete
    await Promise.all(uploadPromises)

    // Refresh content list
    queryClient.invalidateQueries(['content'])

    setUploading(false)

    // Show summary based on results
    if (failCount === 0) {
      showToast.success(`Upload complete! ✅ ${successCount} files uploaded`)
    } else if (successCount === 0) {
      showToast.error(`Upload failed! ❌ ${failCount} files failed`)
    } else {
      showToast.warning(`Upload complete! ✅ ${successCount} success, ❌ ${failCount} failed`)
    }

    if (successCount > 0) {
      onClose()
    }
  }

  // Footer with action buttons
  const footer = (
    <div className="flex gap-3 justify-end">
      <Button
        type="button"
        onClick={onClose}
        disabled={uploading}
        variant="secondary"
        className="flex-1"
      >
        {uploading ? 'Please wait...' : 'Cancel'}
      </Button>
      <Button
        type="submit"
        disabled={uploading || files.length === 0}
        variant="primary"
        className="flex-1"
        onClick={handleBulkUpload}
      >
        {uploading ? 'Uploading...' : `Upload ${files.length} File(s)`}
      </Button>
    </div>
  )

  return (
    <Modal isOpen={true} onClose={onClose} title="Upload Content" size="2xl" footer={footer}>
      <form onSubmit={handleBulkUpload} className="space-y-4">
          {/* File Input */}
          <FormInput
            label="Select Files"
            type="file"
            accept="image/*,video/*"
            multiple
            onChange={handleFileSelect}
            disabled={uploading || validating}
            description={validating ? 'Validating files...' : 'Select one or more image/video files'}
          />
          <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
            <p className="text-xs font-semibold text-blue-800 dark:text-blue-300 mb-2">📋 Supported File Formats:</p>
            <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
              <div>
                <p className="font-semibold mb-1">Images (Recommended):</p>
                <p className="ml-3">✅ PNG - Best for graphics, logos, transparent images</p>
                <p className="ml-3">✅ JPEG/JPG - Best for photographs</p>
                <p className="ml-3">✅ WebP - Modern format with better compression</p>
                <p className="ml-3 text-gray-600 dark:text-gray-400">⚠️ GIF, BMP, SVG - Supported but may have limitations</p>
              </div>
              <div className="mt-2">
                <p className="font-semibold mb-1">Videos (Recommended):</p>
                <p className="ml-3">✅ MP4 (H.264/AAC) - Best compatibility, max 1920x1080 @ 30fps</p>
                <p className="ml-3 text-gray-600 dark:text-gray-400">⚠️ WebM, OGV - Supported but browser-dependent</p>
              </div>
            </div>
            <div className="mt-2 pt-2 border-t border-blue-200 dark:border-blue-700">
              <p className="text-xs text-gray-700 dark:text-gray-300">💡 You can select multiple files to upload at once</p>
              <p className="text-xs text-gray-700 dark:text-gray-300">📏 Recommended: Images &lt;5MB, Videos &lt;100MB</p>
            </div>
          </div>

          {/* Duration Setting */}
          <FormInput
            label="Default Duration (seconds)"
            type="number"
            value={duration}
            onChange={(e) => setDuration(parseInt(e.target.value))}
            min={1}
            disabled={uploading}
            description="This duration will be applied to all files"
          />

          {/* File List */}
          {files.length > 0 && (
            <div className="flex-1 overflow-hidden flex flex-col">
              <h3 className="text-sm font-medium mb-2">Selected Files ({files.length})</h3>
              <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 p-3 rounded-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{file.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <div className="ml-3 flex items-center gap-2">
                      {uploadProgress[index]?.status === 'pending' && (
                        <span className="text-gray-400 dark:text-gray-500">⏳</span>
                      )}
                      {uploadProgress[index]?.status === 'uploading' && (
                        <span className="text-blue-500 animate-spin">🔄</span>
                      )}
                      {uploadProgress[index]?.status === 'success' && (
                        <span className="text-green-500">✅</span>
                      )}
                      {uploadProgress[index]?.status === 'failed' && (
                        <span className="text-red-500" title={uploadProgress[index]?.error}>
                          ❌
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
      </form>
    </Modal>
  )
}
