import { Modal, Button } from '../../shared'
import TagStatsCard from '../TagStatsCard'
import { BarChart3 } from 'lucide-react'

/**
 * TagStatsModal Component
 * Modal for displaying tag statistics
 *
 * Features:
 * - Shows TagStatsCard in a modal
 * - Device online/offline statistics
 * - Content and playlist counts (when backend supports)
 *
 * @param {Object} tag - Tag object to show statistics for
 * @param {Function} onClose - Callback when modal should close
 */
export default function TagStatsModal({ tag, onClose }) {
  // Footer with action buttons

  const footer = (

    <div className="flex gap-3 justify-end">

  <Button variant="secondary" onClick={onClose} className="flex-1">
            Close
          </Button>

    </div>

  )


  
  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2"
      footer={footer}>
          <BarChart3 className="w-6 h-6 text-blue-600" />
          <span>Tag Statistics: {tag.tag_name}</span>
        </div>
      }
      size="lg"
    >
      <div className="space-y-4">
        {/* Description */}
        {tag.description && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <span className="font-semibold">Description:</span> {tag.description}
            </p>
          </div>
        )}

        {/* Stats Card */}
        <TagStatsCard tag={tag} />

        {/* Info Box */}
        <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-300">
          <p className="font-semibold mb-1">📊 About These Statistics</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>Device statistics are updated in real-time based on last heartbeat</li>
            <li>Content and Playlist statistics require backend API support</li>
            <li>Use tags to organize and manage devices in bulk</li>
          </ul>
        </div>

        {/* Footer */}</div>
    </Modal>
  )
}
