import { useState } from 'react'
import { Modal, ModalFooter, Button, FormInput } from '../../shared'

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
          onChange={(e) => setFormData({...formData, ip_address: e.target.value})}
          placeholder="192.168.1.100"
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
