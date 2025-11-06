import { memo } from 'react'
import { Monitor, Tv, CheckCircle, Edit, Trash2, FileText } from 'lucide-react'

/**
 * DeviceTableRow Component
 * Displays a single device row in the devices table
 * Memoized to prevent unnecessary re-renders in large device lists
 *
 * Features:
 * - Device ID, name, type, IP/code, status, last seen
 * - Device icon based on type (TV or Monitor)
 * - Status badge with color coding
 * - Click to assign content functionality
 * - Action buttons: Edit (view info), Delete
 * - Activate button for pending devices
 * - Hover effects and visual feedback
 *
 * @param {Object} device - Device object to display
 * @param {Function} onRowClick - Callback when row is clicked (assign content)
 * @param {Function} onEdit - Callback when edit button is clicked
 * @param {Function} onDelete - Callback when delete button is clicked
 * @param {Function} onActivate - Callback when activate button is clicked (pending only)
 * @param {Function} onViewLogs - Callback when view logs button is clicked
 */
function DeviceTableRow({
  device,
  onRowClick,
  onEdit,
  onDelete,
  onActivate,
  onViewLogs
}) {
  // Determine if device is TV based on platform
  const isTv = device.platform && ['webOS', 'Tizen', 'Android TV'].includes(device.platform)

  return (
    <tr
      onClick={() => onRowClick(device)}
      className="cursor-pointer hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors"
    >
      {/* ID Column */}
      <td className="px-6 py-4 whitespace-nowrap">
        <span className="font-mono font-bold text-blue-600">{device.id}</span>
      </td>

      {/* Device Name Column */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          {isTv ? (
            <Tv className="w-5 h-5 text-blue-600 mr-2" />
          ) : (
            <Monitor className="w-5 h-5 text-green-600 mr-2" />
          )}
          <span className="font-medium text-gray-900 dark:text-gray-100">{device.device_name}</span>
        </div>
      </td>

      {/* Platform Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
        {device.platform || device.device_type.charAt(0).toUpperCase() + device.device_type.slice(1)}
      </td>

      {/* IP Address Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
        <span className="font-mono">{device.ip_address || '-'}</span>
      </td>

      {/* Code Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm">
        {device.unique_code ? (
          <span className="font-mono font-bold text-green-600">
            {device.unique_code}
          </span>
        ) : (
          <span className="text-gray-400 dark:text-gray-500">-</span>
        )}
      </td>

      {/* Status Column */}
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          device.status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
          device.status === 'pending' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
          'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
        }`}>
          {device.status}
        </span>
      </td>

      {/* Last Seen Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
        {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
      </td>

      {/* Actions Column - Sticky Right */}
      <td className="px-6 py-4 whitespace-nowrap text-sm sticky right-0 bg-white dark:bg-gray-800 shadow-[-4px_0_6px_-1px_rgba(0,0,0,0.1)]">
        <div className="flex items-center gap-3">
          {/* Activate button for pending devices */}
          {device.status === 'pending' && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                if (confirm(`Activate ${device.device_name}?\n\nCode: ${device.unique_code || 'N/A'}`)) {
                  onActivate(device.id)
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
              onEdit(device)
            }}
            className="text-blue-600 hover:text-blue-800"
            title="View device information"
          >
            <Edit className="w-5 h-5" />
          </button>

          {/* View Logs button */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              onViewLogs(device)
            }}
            className="text-purple-600 hover:text-purple-800"
            title="View device logs (real-time)"
          >
            <FileText className="w-5 h-5" />
          </button>

          {/* Delete button */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (confirm('Delete this device?')) {
                onDelete(device.id)
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
  )
}

export default memo(DeviceTableRow)
