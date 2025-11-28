/**
 * Session Card Component
 * Displays session information in a card format
 */

import {
  Monitor,
  Smartphone,
  Tablet,
  MapPin,
  Clock,
  Globe,
  LogOut,
  CheckCircle,
  Loader2,
  AlertTriangle,
  Calendar,
  Timer,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { Session } from '../types/session.types'
import { parseUserAgent, getBrowserString, getOSString } from '@/shared/utils/userAgentParser'

interface SessionCardProps {
  session: Session
  onRevoke?: (session: Session) => void
  isRevoking?: boolean
}

export function SessionCard({ session, onRevoke, isRevoking }: SessionCardProps) {
  const isCurrent = session.is_current
  const location = session.location

  // Parse user agent for display
  const parsedUA = parseUserAgent(session.user_agent)

  // Get device icon based on parsed user agent
  const getDeviceIcon = () => {
    switch (parsedUA.device) {
      case 'mobile':
        return <Smartphone className="w-5 h-5" />
      case 'tablet':
        return <Tablet className="w-5 h-5" />
      case 'desktop':
      default:
        return <Monitor className="w-5 h-5" />
    }
  }

  // Get device color
  const getDeviceColor = () => {
    if (isCurrent) return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30'
    return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
  }

  // Format time
  const formatTime = (dateString: string | undefined) => {
    if (!dateString) return 'Unknown'
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true })
    } catch {
      return 'Unknown'
    }
  }

  // Check if session is expiring soon (< 24 hours)
  const isExpiringSoon = () => {
    try {
      const expiresAt = new Date(session.expires_at)
      const now = new Date()
      const hoursUntilExpiry = (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60)
      return hoursUntilExpiry < 24 && hoursUntilExpiry > 0
    } catch {
      return false
    }
  }

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg border ${
        isCurrent
          ? 'border-green-200 dark:border-green-800 ring-2 ring-green-500/20'
          : 'border-gray-200 dark:border-gray-700'
      } p-6 hover:shadow-lg transition-shadow`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${getDeviceColor()}`}>{getDeviceIcon()}</div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {getBrowserString(parsedUA)}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {getOSString(parsedUA)}
            </p>
          </div>
        </div>

        {/* Current Badge */}
        {isCurrent && (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300 rounded">
            <CheckCircle className="w-3 h-3" />
            Current
          </span>
        )}

        {/* Expiring Soon Warning */}
        {!isCurrent && isExpiringSoon() && (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300 rounded">
            <AlertTriangle className="w-3 h-3" />
            Expiring Soon
          </span>
        )}
      </div>

      {/* Info Grid */}
      <div className="space-y-2 mb-4">
        {/* Location */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <MapPin className="w-4 h-4 flex-shrink-0" />
          <span>
            {location && (location.city || location.country)
              ? [location.city, location.region, location.country].filter(Boolean).join(', ')
              : 'Location unknown'}
          </span>
        </div>

        {/* IP Address */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Globe className="w-4 h-4 flex-shrink-0" />
          <span className="font-mono">{session.ip_address || 'Unknown'}</span>
        </div>

        {/* Last Activity */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Clock className="w-4 h-4 flex-shrink-0" />
          <span>Last active {formatTime(session.last_activity || session.last_activity_at)}</span>
        </div>

        {/* Expires At */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Timer className="w-4 h-4 flex-shrink-0" />
          <span>Expires {formatTime(session.expires_at)}</span>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Created {formatTime(session.created_at)}
        </div>

        {/* Revoke Button (not for current session) */}
        {!isCurrent && onRevoke && (
          <button
            onClick={() => onRevoke(session)}
            disabled={isRevoking}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRevoking ? (
              <>
                <Loader2 className="animate-spin h-4 w-4" />
                Revoking...
              </>
            ) : (
              <>
                <LogOut className="w-4 h-4" />
                Revoke
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )
}
