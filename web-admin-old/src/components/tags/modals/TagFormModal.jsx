import { useState } from 'react'
import { Modal, Button, FormInput } from '../../shared'

/**
 * TagFormModal Component
 * Modal for creating or editing tags with color selection
 *
 * Features:
 * - Proper modal structure: sticky header, scrollable content, sticky footer
 * - Tag name input with validation
 * - Description textarea for tag details
 * - Color picker with preset palette
 * - Support for both create and edit modes
 * - Visual color preview with selection feedback
 * - Click outside to close, ESC to close
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

  // Footer with action buttons
  const footer = (
    <div className="flex gap-3">
      <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
        Cancel
      </Button>
      <Button type="submit" variant="primary" onClick={handleSubmit} className="flex-1">
        {tag ? 'Update Tag' : 'Create Tag'}
      </Button>
    </div>
  )

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={tag ? 'Edit Tag' : 'Create Tag'}
      size="lg"
      footer={footer}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormInput
          label="Tag Name"
          type="text"
          value={formData.tag_name}
          onChange={(e) => setFormData({...formData, tag_name: e.target.value})}
          placeholder="e.g., Promo, News, Featured"
          required
        />

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            placeholder="Optional description of what this tag represents..."
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            Color
          </label>
          <div className="flex items-center gap-2 mb-3">
            {colorPresets.map((color) => (
              <button
                key={color}
                type="button"
                onClick={() => setFormData({...formData, color})}
                className={`w-10 h-10 rounded-full transition-all ${
                  formData.color === color
                    ? 'ring-4 ring-blue-500 ring-offset-2 dark:ring-offset-gray-800 scale-110'
                    : 'hover:scale-105 border-2 border-gray-200 dark:border-gray-700'
                }`}
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
          <div className="flex items-center gap-3">
            <input
              type="color"
              value={formData.color}
              onChange={(e) => setFormData({...formData, color: e.target.value})}
              className="w-16 h-10 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer"
            />
            <input
              type="text"
              value={formData.color}
              onChange={(e) => setFormData({...formData, color: e.target.value})}
              pattern="^#[0-9A-Fa-f]{6}$"
              placeholder="#3B82F6"
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Select from presets or enter a custom hex color code
          </p>
        </div>
      </form>
    </Modal>
  )
}
