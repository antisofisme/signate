import { Monitor, Tv, CheckCircle, Edit, Trash2 } from 'lucide-react'

/**
 * DeviceTableRow Component
 * Displays a single device row in the devices table
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
 */
export default function DeviceTableRow({
  device,
  onRowClick,
  onEdit,
  onDelete,
  onActivate
}) {
  return (
    <tr
      onClick={() => onRowClick(device)}
      className="cursor-pointer hover:bg-blue-50 transition-colors"
    >
      {/* ID Column */}
      <td className="px-6 py-4 whitespace-nowrap">
        <span className="font-mono font-bold text-blue-600">{device.id}</span>
      </td>

      {/* Device Name Column */}
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

      {/* Type Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {device.device_type.toUpperCase()}
      </td>

      {/* IP/Code Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {device.ip_address || device.unique_code || 'N/A'}
      </td>

      {/* Status Column */}
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          device.status === 'active' ? 'bg-green-100 text-green-700' :
          device.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {device.status}
        </span>
      </td>

      {/* Last Seen Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
      </td>

      {/* Actions Column */}
      <td className="px-6 py-4 whitespace-nowrap text-sm">
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
