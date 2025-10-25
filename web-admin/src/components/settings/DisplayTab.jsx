import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsAPI } from '../../services/api'
import { Save, RotateCcw } from 'lucide-react'
import { showToast } from '../../utils/toast'
import { Button, FormInput } from '../shared'

/**
 * DisplayTab Component
 * Display and content playback settings
 *
 * Settings:
 * - Default content duration
 * - Transition effects
 * - Screen orientation
 * - Resolution settings
 * - Refresh interval
 */
export default function DisplayTab() {
  const queryClient = useQueryClient()

  // Fetch display settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings', 'display'],
    queryFn: () => settingsAPI.getDisplay().then(res => res.data),
  })

  const [formData, setFormData] = useState({
    default_duration: settings?.default_duration || 10,
    transition_effect: settings?.transition_effect || 'fade',
    transition_duration: settings?.transition_duration || 1000,
    screen_orientation: settings?.screen_orientation || 'landscape',
    resolution: settings?.resolution || '1920x1080',
    refresh_interval: settings?.refresh_interval || 30
  })

  // Update settings mutation
  const updateMutation = useMutation({
    mutationFn: (data) => settingsAPI.updateDisplay(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['settings', 'display'])
      showToast.success('Display settings saved successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to save settings')
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    updateMutation.mutate(formData)
  }

  const handleReset = () => {
    if (confirm('Reset to default settings?')) {
      setFormData({
        default_duration: 10,
        transition_effect: 'fade',
        transition_duration: 1000,
        screen_orientation: 'landscape',
        resolution: '1920x1080',
        refresh_interval: 30
      })
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Display Settings</h3>
        <p className="text-sm text-gray-600">Configure default content playback and display settings</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Content Duration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormInput
            label="Default Content Duration"
            type="number"
            value={formData.default_duration}
            onChange={(e) => setFormData({...formData, default_duration: parseInt(e.target.value)})}
            min={1}
            max={3600}
            description="Default duration in seconds for content without specified duration"
          />

          <FormInput
            label="Transition Effect"
            type="select"
            value={formData.transition_effect}
            onChange={(e) => setFormData({...formData, transition_effect: e.target.value})}
            options={[
              { value: 'none', label: 'None' },
              { value: 'fade', label: 'Fade' },
              { value: 'slide', label: 'Slide' },
              { value: 'zoom', label: 'Zoom' }
            ]}
            description="Transition effect between content items"
          />
        </div>

        {/* Transition Duration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormInput
            label="Transition Duration"
            type="number"
            value={formData.transition_duration}
            onChange={(e) => setFormData({...formData, transition_duration: parseInt(e.target.value)})}
            min={100}
            max={5000}
            description="Transition duration in milliseconds"
          />

          <FormInput
            label="Screen Orientation"
            type="select"
            value={formData.screen_orientation}
            onChange={(e) => setFormData({...formData, screen_orientation: e.target.value})}
            options={[
              { value: 'landscape', label: 'Landscape' },
              { value: 'portrait', label: 'Portrait' }
            ]}
            description="Default screen orientation for displays"
          />
        </div>

        {/* Resolution & Refresh */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormInput
            label="Default Resolution"
            type="select"
            value={formData.resolution}
            onChange={(e) => setFormData({...formData, resolution: e.target.value})}
            options={[
              { value: '1280x720', label: '1280x720 (HD)' },
              { value: '1920x1080', label: '1920x1080 (Full HD)' },
              { value: '2560x1440', label: '2560x1440 (2K)' },
              { value: '3840x2160', label: '3840x2160 (4K)' }
            ]}
            description="Recommended resolution for content"
          />

          <FormInput
            label="Playlist Refresh Interval"
            type="number"
            value={formData.refresh_interval}
            onChange={(e) => setFormData({...formData, refresh_interval: parseInt(e.target.value)})}
            min={10}
            max={300}
            description="How often devices check for playlist updates (seconds)"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-4 border-t">
          <Button
            type="submit"
            variant="primary"
            leftIcon={<Save className="w-4 h-4" />}
            disabled={updateMutation.isLoading}
          >
            {updateMutation.isLoading ? 'Saving...' : 'Save Settings'}
          </Button>

          <Button
            type="button"
            variant="secondary"
            leftIcon={<RotateCcw className="w-4 h-4" />}
            onClick={handleReset}
          >
            Reset to Defaults
          </Button>
        </div>
      </form>
    </div>
  )
}
