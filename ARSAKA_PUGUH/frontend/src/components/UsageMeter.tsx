/**
 * Usage Meter Component
 *
 * Displays current usage vs plan limit with progress bar.
 */

import { cn } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

interface UsageMeterProps {
  label: string
  used: number
  limit: number | null
  className?: string
  showPercentage?: boolean
}

export function UsageMeter({
  label,
  used,
  limit,
  className,
  showPercentage = true,
}: UsageMeterProps) {
  const isUnlimited = limit === null || limit === -1
  const percentage = isUnlimited ? 0 : Math.min((used / limit) * 100, 100)
  const isNearLimit = percentage >= 80
  const isOverLimit = percentage >= 100

  const formatNumber = (n: number) => n.toLocaleString()

  const getStatusIcon = () => {
    if (isUnlimited) return <CheckCircle className="h-4 w-4 text-green-500" />
    if (isOverLimit) return <XCircle className="h-4 w-4 text-red-500" />
    if (isNearLimit) return <AlertTriangle className="h-4 w-4 text-yellow-500" />
    return <CheckCircle className="h-4 w-4 text-green-500" />
  }

  const getProgressColor = () => {
    if (isUnlimited) return 'bg-green-500'
    if (isOverLimit) return 'bg-red-500'
    if (isNearLimit) return 'bg-yellow-500'
    return 'bg-primary'
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="font-medium">{label}</span>
        </div>
        <span className="text-muted-foreground">
          {formatNumber(used)} / {isUnlimited ? 'Unlimited' : formatNumber(limit)}
          {showPercentage && !isUnlimited && (
            <span className="ml-1">({Math.round(percentage)}%)</span>
          )}
        </span>
      </div>

      {!isUnlimited && (
        <Progress
          value={percentage}
          className="h-2"
          indicatorClassName={getProgressColor()}
        />
      )}

      {isNearLimit && !isOverLimit && (
        <p className="text-xs text-yellow-600">
          Approaching limit. Consider upgrading your plan.
        </p>
      )}

      {isOverLimit && (
        <p className="text-xs text-red-600">
          Limit exceeded. Upgrade to continue using this feature.
        </p>
      )}
    </div>
  )
}

export default UsageMeter
