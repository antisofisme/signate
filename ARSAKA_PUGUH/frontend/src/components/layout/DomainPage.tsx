/**
 * Domain Page Wrapper
 * Provides consistent page structure for all domain screens
 */

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

type DomainType = 'iam' | 'tenant' | 'decision' | 'workflow' | 'control'

interface DomainPageProps {
  domain: DomainType
  title: string
  description?: string
  badge?: {
    label: string
    variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  }
  actions?: ReactNode
  children: ReactNode
  backTo?: string
}

const domainStyles: Record<DomainType, { border: string; badge: string }> = {
  iam: { border: 'border-l-iam', badge: 'iam' },
  tenant: { border: 'border-l-tenant', badge: 'tenant' },
  decision: { border: 'border-l-decision', badge: 'decision' },
  workflow: { border: 'border-l-workflow', badge: 'workflow' },
  control: { border: 'border-l-control', badge: 'control' },
}

export function DomainPage({
  domain,
  title,
  description,
  badge,
  actions,
  children,
  backTo,
}: DomainPageProps) {
  const navigate = useNavigate()
  const styles = domainStyles[domain]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className={cn(
        "bg-card rounded-lg border border-l-4 p-6",
        styles.border
      )}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            {backTo && (
              <button
                onClick={() => navigate(backTo)}
                className="mt-1 p-1 hover:bg-accent rounded"
              >
                <ArrowLeft size={20} className="text-muted-foreground" />
              </button>
            )}
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">{title}</h1>
                {badge && (
                  <Badge variant={badge.variant || 'default'}>
                    {badge.label}
                  </Badge>
                )}
              </div>
              {description && (
                <p className="text-muted-foreground mt-1">{description}</p>
              )}
            </div>
          </div>
          {actions && (
            <div className="flex items-center gap-2">
              {actions}
            </div>
          )}
        </div>
      </div>

      {/* Page Content */}
      {children}
    </div>
  )
}

/**
 * Read-Only Notice Component
 */
export function ReadOnlyNotice({ domain }: { domain: DomainType }) {
  return (
    <div className="bg-muted/50 border rounded-lg p-3 text-sm text-muted-foreground">
      <strong>{domain.toUpperCase()} Domain</strong> is READ-ONLY.
      All data comes from Core API. No mutations allowed.
    </div>
  )
}

/**
 * Mutation Warning Component
 */
export function MutationWarning({
  action,
  consequences,
}: {
  action: string
  consequences: string[]
}) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className="text-yellow-600 text-lg">⚠️</div>
        <div>
          <div className="font-semibold text-yellow-800">Confirm Action</div>
          <p className="text-sm text-yellow-700 mt-1">
            You are about to: <strong>{action}</strong>
          </p>
          <ul className="mt-2 space-y-1 text-sm text-yellow-700">
            {consequences.map((c, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                {c}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm font-medium text-yellow-800">
            This action CANNOT be undone.
          </p>
        </div>
      </div>
    </div>
  )
}
