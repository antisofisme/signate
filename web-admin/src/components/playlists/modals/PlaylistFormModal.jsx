import { useState } from 'react'
import { Modal, ModalFooter, Button, FormInput } from '../../shared'

/**
 * PlaylistFormModal Component
 * Modal for creating or editing playlists with scheduling options
 *
 * Features:
 * - Playlist name and description inputs
 * - Active/Inactive status toggle
 * - Schedule configuration (start time, end time)
 * - Day of week selection for scheduling
 * - Support for both create and edit modes
 * - Validation for time inputs
 * - Cancel and submit actions
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

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={playlist ? 'Edit Playlist' : 'Create Playlist'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Basic Information */}
        <FormInput
          label="Playlist Name"
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          placeholder="e.g., Morning Show, Lunch Menu, Evening Ads"
          required
        />

        <FormInput
          label="Description"
          type="textarea"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          placeholder="Describe the purpose of this playlist"
          rows={3}
        />

        {/* Active Status Toggle */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">
            Status
          </label>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setFormData({...formData, is_active: true})}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                formData.is_active
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Active
            </button>
            <button
              type="button"
              onClick={() => setFormData({...formData, is_active: false})}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                !formData.is_active
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Inactive
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {formData.is_active ? 'Playlist is active and will be displayed' : 'Playlist is inactive and will not be displayed'}
          </p>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">
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
          <p className="text-xs text-gray-500 mt-1">
            When multiple playlists overlap, the one with higher priority will be shown (1-10, default: 1)
          </p>
        </div>

        {/* Schedule Section */}
        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Schedule</h3>

          {/* Schedule Mode */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-gray-700">
              Schedule Mode
            </label>
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => setFormData({...formData, schedule_mode: 'inclusive'})}
                className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors border-2 ${
                  formData.schedule_mode === 'inclusive'
                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-blue-300'
                }`}
              >
                <div className="text-left">
                  <div className="font-bold">📋 Inclusive</div>
                  <div className="text-xs mt-1">Add to existing rotation</div>
                </div>
              </button>
              <button
                type="button"
                onClick={() => setFormData({...formData, schedule_mode: 'exclusive'})}
                className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors border-2 ${
                  formData.schedule_mode === 'exclusive'
                    ? 'bg-red-50 border-red-500 text-red-700'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-red-300'
                }`}
              >
                <div className="text-left">
                  <div className="font-bold">🚨 Exclusive</div>
                  <div className="text-xs mt-1">Replace all other content</div>
                </div>
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {formData.schedule_mode === 'inclusive'
                ? '✓ This playlist will be added to existing content during the schedule'
                : '⚠️ This playlist will REPLACE all other content during the schedule (use for emergencies/events)'
              }
            </p>
          </div>

          {/* Timezone */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-gray-700">
              Timezone
            </label>
            <select
              value={formData.schedule_timezone}
              onChange={(e) => setFormData({...formData, schedule_timezone: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Asia/Jakarta">Asia/Jakarta (WIB - UTC+7)</option>
              <option value="Asia/Makassar">Asia/Makassar (WITA - UTC+8)</option>
              <option value="Asia/Jayapura">Asia/Jayapura (WIT - UTC+9)</option>
              <option value="Asia/Singapore">Asia/Singapore (SGT - UTC+8)</option>
              <option value="Asia/Kuala_Lumpur">Asia/Kuala_Lumpur (MYT - UTC+8)</option>
              <option value="Asia/Bangkok">Asia/Bangkok (ICT - UTC+7)</option>
              <option value="Asia/Manila">Asia/Manila (PHT - UTC+8)</option>
              <option value="UTC">UTC (UTC+0)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Schedule times will be interpreted in this timezone
            </p>
          </div>

          {/* Date Range (Optional) */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-gray-700">
              Date Range (Optional)
            </label>
            <div className="grid grid-cols-2 gap-4">
              <FormInput
                label="Start Date"
                type="date"
                value={formData.schedule.start_date}
                onChange={(e) => setFormData({
                  ...formData,
                  schedule: {...formData.schedule, start_date: e.target.value}
                })}
                placeholder="Leave empty for no start limit"
              />
              <FormInput
                label="End Date"
                type="date"
                value={formData.schedule.end_date}
                onChange={(e) => setFormData({
                  ...formData,
                  schedule: {...formData.schedule, end_date: e.target.value}
                })}
                placeholder="Leave empty for no end limit"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Limit when this playlist can be active. Leave empty for unlimited duration.
            </p>
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
              required
            />
            <FormInput
              label="End Time"
              type="time"
              value={formData.schedule.end_time}
              onChange={(e) => setFormData({
                ...formData,
                schedule: {...formData.schedule, end_time: e.target.value}
              })}
              required
            />
          </div>

          {/* Days of Week */}
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700">
              Days of Week
            </label>
            <div className="flex flex-wrap gap-2">
              {daysOfWeek.map((day) => (
                <button
                  key={day.value}
                  type="button"
                  onClick={() => toggleDay(day.value)}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                    formData.schedule.days.includes(day.value)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {day.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Select the days when this playlist should be active
            </p>
          </div>
        </div>

        {/* Footer with action buttons */}
        <ModalFooter>
          <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" variant="primary" className="flex-1">
            {playlist ? 'Update Playlist' : 'Create Playlist'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
