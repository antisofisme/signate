import { useState } from 'react'
import { Modal, Button, FormInput } from '../../shared'
import { isValidIPv4 } from '../../../utils/helpers'
import { Tv } from 'lucide-react'

/**
 * TVRegisterModal Component
 * Modal for registering new TV/Smart TV devices to the system
 *
 * Features:
 * - Proper modal structure: sticky header, scrollable content, sticky footer
 * - Device name input with validation
 * - IP address input for network connection with IPv4 validation
 * - Passphrase for device authentication
 * - Form validation before submission
 * - Click outside to close, ESC to close
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
  const [errors, setErrors] = useState({})

  const validateIPAddress = (ip) => {
    if (!ip) {
      return 'IP address is required'
    }
    if (!isValidIPv4(ip)) {
      return 'Invalid IPv4 address format (e.g., 192.168.1.100)'
    }
    return null
  }

  const handleIPChange = (e) => {
    const newIP = e.target.value
    setFormData({...formData, ip_address: newIP})

    // Clear error when user starts typing
    if (errors.ip_address) {
      setErrors({...errors, ip_address: null})
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    // Validate IP address before submitting
    const ipError = validateIPAddress(formData.ip_address)
    if (ipError) {
      setErrors({...errors, ip_address: ipError})
      return
    }

    onSubmit(formData)
  }

  // Footer with action buttons
  const footer = (
    <div className="flex gap-3">
      <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
        Cancel
      </Button>
      <Button type="submit" variant="primary" onClick={handleSubmit} className="flex-1">
        Register TV
      </Button>
    </div>
  )

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <Tv className="w-6 h-6 text-blue-600" />
          <span>Register TV Device</span>
        </div>
      }
      size="lg"
      footer={footer}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormInput
          label="Device Name"
          type="text"
          value={formData.device_name}
          onChange={(e) => setFormData({...formData, device_name: e.target.value})}
          placeholder="e.g., TV - Living Room, Smart TV - Office"
          required
          autoFocus
        />

        <FormInput
          label="IP Address"
          type="text"
          value={formData.ip_address}
          onChange={handleIPChange}
          placeholder="192.168.1.100"
          error={errors.ip_address}
          required
          helpText="Enter the TV's IP address on your local network"
        />

        <FormInput
          label="Passphrase"
          type="text"
          value={formData.passphrase}
          onChange={(e) => setFormData({...formData, passphrase: e.target.value})}
          placeholder="Enter device passphrase"
          required
          helpText="Authentication passphrase for the TV device"
        />

        {/* Info Box */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-300 font-medium mb-2">
            Registration Steps:
          </p>
          <ol className="list-decimal list-inside space-y-1 text-xs text-blue-700 dark:text-blue-400">
            <li>Ensure the TV is connected to the same network</li>
            <li>Find the TV's IP address in network settings</li>
            <li>Enter the device name and credentials above</li>
            <li>Click "Register TV" to add the device</li>
          </ol>
        </div>
      </form>
    </Modal>
  )
}
