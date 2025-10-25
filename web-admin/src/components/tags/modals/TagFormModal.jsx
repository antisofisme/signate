import { useState } from 'react'
import { Modal, ModalFooter, Button, FormInput } from '../../shared'

/**
 * TagFormModal Component
 * Modal for creating or editing tags with color selection
 *
 * Features:
 * - Tag name input with validation
 * - Description textarea for tag details
 * - Color picker with preset palette
 * - Support for both create and edit modes
 * - Visual color preview with selection feedback
 * - Cancel and submit actions
 *
 * @param {Object} tag - Optional tag object for edit mode (null for create mode)
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSubmit - Callback when form is submitted with formData
 */
export default function TagFormModal({ tag, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    tag_name: tag?.tag_name || '',
    description: tag?.description || '',
    color: tag?.color || '#3B82F6',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const colorPresets = [
    '#3B82F6', // Blue
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#EF4444', // Red
    '#8B5CF6', // Purple
    '#EC4899', // Pink
    '#14B8A6', // Teal
    '#F97316', // Orange
  ]

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={tag ? 'Edit Tag' : 'Create Tag'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormInput
          label="Tag Name"
          type="text"
          value={formData.tag_name}
          onChange={(e) => setFormData({...formData, tag_name: e.target.value})}
          required
        />
        <FormInput
          label="Description"
          type="textarea"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          rows={2}
        />
        <div>
          <label className="block text-sm font-medium mb-1">Color</label>
          <div className="flex items-center gap-2 mb-2">
            {colorPresets.map((color) => (
              <button
                key={color}
                type="button"
                onClick={() => setFormData({...formData, color})}
                className={`w-8 h-8 rounded-full border-2 ${
                  formData.color === color ? 'border-gray-800' : 'border-transparent'
                }`}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
          <input
            type="color"
            value={formData.color}
            onChange={(e) => setFormData({...formData, color: e.target.value})}
            className="w-full h-10 border rounded-lg cursor-pointer"
          />
        </div>

        {/* Footer with action buttons */}
        <ModalFooter>
          <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" variant="primary" className="flex-1">
            {tag ? 'Update' : 'Create'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
