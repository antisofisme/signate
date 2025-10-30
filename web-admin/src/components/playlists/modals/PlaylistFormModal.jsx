import { useState } from 'react'
import { Modal, Button, FormInput } from '../../shared'

/**
 * PlaylistFormModal Component
 * Modal for creating or editing playlists with scheduling options
 *
 * Features:
 * - Proper modal structure: sticky header, scrollable content, sticky footer
 * - Playlist name and description inputs
 * - Active/Inactive status toggle
 * - Schedule configuration (start time, end time)
 * - Day of week selection for scheduling
 * - Support for both create and edit modes
 * - Validation for time inputs
 * - Click outside to close
 * - ESC to close
 *
 * @param {Object} playlist - Optional playlist object for edit mode (null for create mode)
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSubmit - Callback when form is submitted with formData
 */
export default function PlaylistFormModal({ playlist, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    name: playlist?.name || '',
    description: playlist?.description || '',
    is_active: playlist?.is_active ?? true,
    priority: playlist?.priority || 1,
    schedule_mode: playlist?.schedule_mode || 'inclusive',
    schedule_timezone: playlist?.schedule_timezone || 'Asia/Jakarta',
    schedule: {
      start_time: playlist?.schedule?.start_time || '00:00',
      end_time: playlist?.schedule?.end_time || '23:59',
      days: playlist?.schedule?.days || ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
      start_date: playlist?.schedule?.start_date || '',
      end_date: playlist?.schedule?.end_date || '',
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()

    // Validate that start time is before end time
    if (formData.schedule.start_time >= formData.schedule.end_time) {
      alert('Start time must be before end time')
      return
    }

    // Validate at least one day is selected
    if (formData.schedule.days.length === 0) {
      alert('Please select at least one day')
      return
    }

    // Validate date range if both are provided
    if (formData.schedule.start_date && formData.schedule.end_date) {
      if (formData.schedule.start_date > formData.schedule.end_date) {
        alert('Start date must be before end date')
        return
      }
    }

    onSubmit(formData)
  }

  const toggleDay = (day) => {
    setFormData(prev => ({
      ...prev,
      schedule: {
        ...prev.schedule,
        days: prev.schedule.days.includes(day)
          ? prev.schedule.days.filter(d => d !== day)
          : [...prev.schedule.days, day]
      }
    }))
  }

  const daysOfWeek = [
    { value: 'monday', label: 'Mon' },
    { value: 'tuesday', label: 'Tue' },
    { value: 'wednesday', label: 'Wed' },
    { value: 'thursday', label: 'Thu' },
    { value: 'friday', label: 'Fri' },
    { value: 'saturday', label: 'Sat' },
    { value: 'sunday', label: 'Sun' },
  ]

  // Footer with action buttons
  const footer = (
    <div className="flex gap-3">
      <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
        Cancel
      </Button>
      <Button type="submit" variant="primary" onClick={handleSubmit} className="flex-1">
        {playlist ? 'Update Playlist' : 'Create Playlist'}
      </Button>
    </div>
  )

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={playlist ? 'Edit Playlist' : 'Create Playlist'}
      size="2xl"
      footer={footer}
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="space-y-4">
          <FormInput
            label="Playlist Name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="e.g., Morning Show, Lunch Menu, Evening Ads"
            required
          />

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Optional description of what this playlist contains..."
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
        </div>

        {/* Active Status Toggle */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            Status
          </label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setFormData({...formData, is_active: !formData.is_active})}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                formData.is_active ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  formData.is_active ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {formData.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {formData.is_active ? 'Playlist is active and will be displayed' : 'Playlist is inactive and will not be displayed'}
          </p>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            Priority
          </label>
          <FormInput
            type="number"
            min="1"
            max="10"
            value={formData.priority}
            onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
            placeholder="1-10 (higher number = higher priority)"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            When multiple playlists overlap, the one with higher priority will be shown (1-10, default: 1)
          </p>
        </div>

        {/* Schedule Section */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          <h3 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-4">Schedule Configuration</h3>

          {/* Schedule Mode */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              Schedule Mode
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setFormData({...formData, schedule_mode: 'inclusive'})}
                className={`px-4 py-3 rounded-lg font-medium transition-colors border-2 text-left ${
                  formData.schedule_mode === 'inclusive'
                    ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-700 dark:text-blue-400'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-blue-300'
                }`}
              >
                <div className="font-bold">📋 Inclusive</div>
                <div className="text-xs mt-1">Add to existing rotation</div>
              </button>
              <button
                type="button"
                onClick={() => setFormData({...formData, schedule_mode: 'exclusive'})}
                className={`px-4 py-3 rounded-lg font-medium transition-colors border-2 text-left ${
                  formData.schedule_mode === 'exclusive'
                    ? 'bg-purple-50 dark:bg-purple-900/30 border-purple-500 text-purple-700 dark:text-purple-400'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-purple-300'
                }`}
              >
                <div className="font-bold">🎯 Exclusive</div>
                <div className="text-xs mt-1">Replace all playlists</div>
              </button>
            </div>
          </div>

          {/* Time Range */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <FormInput
              label="Start Time"
              type="time"
              value={formData.schedule.start_time}
              onChange={(e) => setFormData({
                ...formData,
                schedule: {...formData.schedule, start_time: e.target.value}
              })}
            />
            <FormInput
              label="End Time"
              type="time"
              value={formData.schedule.end_time}
              onChange={(e) => setFormData({
                ...formData,
                schedule: {...formData.schedule, end_time: e.target.value}
              })}
            />
          </div>

          {/* Days of Week */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              Days of Week
            </label>
            <div className="flex gap-2 flex-wrap">
              {daysOfWeek.map(day => (
                <button
                  key={day.value}
                  type="button"
                  onClick={() => toggleDay(day.value)}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                    formData.schedule.days.includes(day.value)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  {day.label}
                </button>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <FormInput
              label="Start Date (Optional)"
              type="date"
              value={formData.schedule.start_date}
              onChange={(e) => setFormData({
                ...formData,
                schedule: {...formData.schedule, start_date: e.target.value}
              })}
            />
            <FormInput
              label="End Date (Optional)"
              type="date"
              value={formData.schedule.end_date}
              onChange={(e) => setFormData({
                ...formData,
                schedule: {...formData.schedule, end_date: e.target.value}
              })}
            />
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Leave dates empty for ongoing schedule
          </p>
        </div>
      </form>
    </Modal>
  )
}
