import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { activitiesAPI } from '../../services/api'
import {
  Activity, Tv, Upload, ListVideo, Tag, Link, Trash2,
  Edit, CheckCircle, XCircle, User, Settings, Clock
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

/**
 * FASE 3.2: Activity Timeline Component for Dashboard
 *
 * Displays recent activities in a compact timeline format
 * - Shows last 10 activities
 * - Auto-refresh every 30 seconds
 * - Icon & color per action type
 * - Link to full Activity Logs page
 */
export default function ActivityTimeline() {
  const navigate = useNavigate()

  const { data: activities, isLoading } = useQuery({
    queryKey: ['activities', 'recent'],
    queryFn: () => activitiesAPI.list({ limit: 10 }).then(res => res.data),
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  const getActivityIcon = (actionType) => {
    // Device actions
    if (actionType.includes('DEVICE_REGISTERED')) return <Tv className="w-4 h-4" />
    if (actionType.includes('DEVICE_APPROVED')) return <CheckCircle className="w-4 h-4" />
    if (actionType.includes('DEVICE_REJECTED')) return <XCircle className="w-4 h-4" />
    if (actionType.includes('DEVICE')) return <Tv className="w-4 h-4" />

    // Content actions
    if (actionType.includes('CONTENT_UPLOADED')) return <Upload className="w-4 h-4" />
    if (actionType.includes('CONTENT')) return <Upload className="w-4 h-4" />

    // Playlist actions
    if (actionType.includes('PLAYLIST')) return <ListVideo className="w-4 h-4" />

    // Tag actions
    if (actionType.includes('TAG')) return <Tag className="w-4 h-4" />

    // Assignment actions
    if (actionType.includes('ASSIGNED') || actionType.includes('UNASSIGNED')) return <Link className="w-4 h-4" />

    // User actions
    if (actionType.includes('USER')) return <User className="w-4 h-4" />

    // System actions
    if (actionType.includes('SETTINGS') || actionType.includes('SYSTEM')) return <Settings className="w-4 h-4" />

    // Default
    return <Activity className="w-4 h-4" />
  }

  const getActionColor = (actionType) => {
    // Deletions - Red
    if (actionType.includes('DELETE') || actionType.includes('REJECTED') || actionType.includes('UNASSIGNED')) {
      return 'red'
    }
    // Creations & Approvals - Green
    if (actionType.includes('CREATE') || actionType.includes('UPLOAD') || actionType.includes('APPROVED') || actionType.includes('REGISTERED') || actionType.includes('ASSIGNED')) {
      return 'green'
    }
    // Updates - Blue
    if (actionType.includes('UPDATE')) {
      return 'blue'
    }
    // Default - Gray
    return 'gray'
  }

  const formatActivityMessage = (activity) => {
    const user = activity.user ? activity.user.username : 'System'
    const entityName = activity.entity_name || `${activity.entity_type} #${activity.entity_id}`

    // Format action in past tense
    let actionText = activity.action_type.toLowerCase().replace(/_/g, ' ')

    // Convert to past tense for better readability
    if (actionText.includes('create')) actionText = actionText.replace('create', 'created')
    if (actionText.includes('update')) actionText = actionText.replace('update', 'updated')
    if (actionText.includes('delete')) actionText = actionText.replace('delete', 'deleted')
    if (actionText.includes('upload')) actionText = actionText.replace('upload', 'uploaded')
    if (actionText.includes('approve')) actionText = actionText.replace('approve', 'approved')
    if (actionText.includes('reject')) actionText = actionText.replace('reject', 'rejected')
    if (actionText.includes('register')) actionText = actionText.replace('register', 'registered')
    if (actionText.includes('assign')) actionText = actionText.replace('assign', 'assigned')

    return (
      <>
        <span className="font-semibold">{user}</span>
        {' '}{actionText}{' '}
        <span className="font-semibold">{entityName}</span>
      </>
    )
  }

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Recent Activity
          </h2>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse flex items-start gap-3">
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const hasActivities = activities?.items && activities.items.length > 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Recent Activity
        </h2>
        <button
          onClick={() => navigate('/activities')}
          className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
        >
          View All →
        </button>
      </div>

      {!hasActivities ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No recent activities</p>
        </div>
      ) : (
        <div className="space-y-3">
          {activities.items.map((activity) => {
            const color = getActionColor(activity.action_type)
            const bgColor = {
              red: 'bg-red-100 dark:bg-red-900/30',
              green: 'bg-green-100 dark:bg-green-900/30',
              blue: 'bg-blue-100 dark:bg-blue-900/30',
              gray: 'bg-gray-100 dark:bg-gray-700',
            }[color]

            const textColor = {
              red: 'text-red-600 dark:text-red-400',
              green: 'text-green-600 dark:text-green-400',
              blue: 'text-blue-600 dark:text-blue-400',
              gray: 'text-gray-600 dark:text-gray-400',
            }[color]

            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors cursor-pointer group"
                onClick={() => navigate('/activities')}
              >
                <div className={`p-2 rounded-full ${bgColor} ${textColor} flex-shrink-0`}>
                  {getActivityIcon(activity.action_type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 dark:text-gray-200 truncate">
                    {formatActivityMessage(activity)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
