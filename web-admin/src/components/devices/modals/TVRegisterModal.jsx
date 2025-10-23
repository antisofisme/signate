import { useState } from 'react'

/**
 * TVRegisterModal Component
 * Modal for registering new TV/Smart TV devices to the system
 *
 * Features:
 * - Device name input with validation
 * - IP address input for network connection
 * - Passphrase for device authentication
 * - Form validation before submission
 * - Cancel and submit actions
 *
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSubmit - Callback when form is submitted with formData
 */
export default function TVRegisterModal({ onClose, onSubmit }) {
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
            <button type="submit" className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
              Register
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
