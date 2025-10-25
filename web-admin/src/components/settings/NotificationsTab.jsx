import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsAPI } from '../../services/api'
import { Save, Mail, AlertCircle, CheckCircle } from 'lucide-react'
import { showToast } from '../../utils/toast'
import { Button, FormInput } from '../shared'

/**
 * NotificationsTab Component
 * Notification and alert settings
 *
 * Settings:
 * - Email notifications
 * - Device offline alerts
 * - Content upload notifications
 * - Error notifications
 * - Email recipients
 */
export default function NotificationsTab() {
  const queryClient = useQueryClient()

  // Fetch notification settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings', 'notifications'],
    queryFn: () => settingsAPI.getNotifications().then(res => res.data),
  })

  const [formData, setFormData] = useState({
    email_enabled: settings?.email_enabled || false,
    device_offline_alerts: settings?.device_offline_alerts || true,
    content_upload_notifications: settings?.content_upload_notifications || false,
    error_notifications: settings?.error_notifications || true,
    notification_emails: settings?.notification_emails || '',
    offline_threshold_minutes: settings?.offline_threshold_minutes || 5
  })

  // Update settings mutation
  const updateMutation = useMutation({
    mutationFn: (data) => settingsAPI.updateNotifications(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['settings', 'notifications'])
      showToast.success('Notification settings saved successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to save settings')
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    updateMutation.mutate(formData)
  }

  const handleToggle = (field) => {
    setFormData({...formData, [field]: !formData[field]})
  }

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Notification Settings</h3>
        <p className="text-sm text-gray-600">Configure alert and notification preferences</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Email Notifications Toggle */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <label className="flex items-center justify-between cursor-pointer">
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-gray-600" />
              <div>
                <p className="font-medium text-gray-800">Email Notifications</p>
                <p className="text-sm text-gray-600">Enable email notifications for alerts</p>
              </div>
            </div>
            <div className="relative">
              <input
                type="checkbox"
                checked={formData.email_enabled}
                onChange={() => handleToggle('email_enabled')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-300 rounded-full peer peer-checked:bg-blue-600 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </div>
          </label>
        </div>

        {/* Notification Types */}
        <div className="space-y-3">
          <p className="font-medium text-gray-800">Notification Types</p>

          {/* Device Offline Alerts */}
          <label className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-orange-600" />
              <div>
                <p className="font-medium text-gray-800">Device Offline Alerts</p>
                <p className="text-sm text-gray-600">Get notified when devices go offline</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={formData.device_offline_alerts}
              onChange={() => handleToggle('device_offline_alerts')}
              className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
            />
          </label>

          {/* Content Upload Notifications */}
          <label className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="font-medium text-gray-800">Content Upload Notifications</p>
                <p className="text-sm text-gray-600">Get notified on successful uploads</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={formData.content_upload_notifications}
              onChange={() => handleToggle('content_upload_notifications')}
              className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
            />
          </label>

          {/* Error Notifications */}
          <label className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <div>
                <p className="font-medium text-gray-800">Error Notifications</p>
                <p className="text-sm text-gray-600">Get notified of system errors</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={formData.error_notifications}
              onChange={() => handleToggle('error_notifications')}
              className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
            />
          </label>
        </div>

        {/* Email Recipients */}
        <FormInput
          label="Notification Email Recipients"
          type="text"
          value={formData.notification_emails}
          onChange={(e) => setFormData({...formData, notification_emails: e.target.value})}
          placeholder="admin@example.com, user@example.com"
          description="Comma-separated email addresses"
          disabled={!formData.email_enabled}
        />

        {/* Offline Threshold */}
        <FormInput
          label="Device Offline Threshold (Minutes)"
          type="number"
          value={formData.offline_threshold_minutes}
          onChange={(e) => setFormData({...formData, offline_threshold_minutes: parseInt(e.target.value)})}
          min={1}
          max={60}
          description="Minutes of inactivity before device is considered offline"
        />

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
        </div>
      </form>
    </div>
  )
}
