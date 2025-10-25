import { useState } from 'react'
import { Modal, ModalFooter, Button, FormInput } from '../../shared'
import { isValidIPv4 } from '../../../utils/helpers'

/**
 * TVRegisterModal Component
 * Modal for registering new TV/Smart TV devices to the system
 *
 * Features:
 * - Device name input with validation
 * - IP address input for network connection with IPv4 validation
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

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Register TV"
      size="md"
      footer={
        <ModalFooter>
          <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" variant="primary" onClick={handleSubmit} className="flex-1">
            Register
          </Button>
        </ModalFooter>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormInput
          label="Device Name"
          type="text"
          value={formData.device_name}
          onChange={(e) => setFormData({...formData, device_name: e.target.value})}
          required
        />
        <FormInput
          label="IP Address"
          type="text"
          value={formData.ip_address}
          onChange={handleIPChange}
          placeholder="192.168.1.100"
          error={errors.ip_address}
          required
        />
        <FormInput
          label="Passphrase"
          type="text"
          value={formData.passphrase}
          onChange={(e) => setFormData({...formData, passphrase: e.target.value})}
          required
        />
      </form>
    </Modal>
  )
}
