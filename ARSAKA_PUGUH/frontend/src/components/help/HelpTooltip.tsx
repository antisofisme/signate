/**
 * HelpTooltip - Contextual help tooltip component
 * Provides inline help with optional documentation links
 */

import { ReactNode } from 'react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { HelpCircle, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

interface HelpTooltipProps {
  content: string
  learnMoreUrl?: string
  children?: ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  align?: 'start' | 'center' | 'end'
  className?: string
  iconClassName?: string
  showIcon?: boolean
}

export function HelpTooltip({
  content,
  learnMoreUrl,
  children,
  side = 'top',
  align = 'center',
  className,
  iconClassName,
  showIcon = true,
}: HelpTooltipProps) {
  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={cn('inline-flex items-center gap-1', className)}>
            {children}
            {showIcon && (
              <HelpCircle
                className={cn(
                  'h-4 w-4 text-muted-foreground cursor-help hover:text-foreground transition-colors',
                  iconClassName
                )}
              />
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent side={side} align={align} className="max-w-xs">
          <p className="text-sm">{content}</p>
          {learnMoreUrl && (
            <a
              href={learnMoreUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-amber-500 hover:text-amber-600 mt-1"
              onClick={(e) => e.stopPropagation()}
            >
              Learn more
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

/**
 * Inline help icon only (no wrapper)
 */
interface HelpIconProps {
  content: string
  learnMoreUrl?: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  className?: string
}

export function HelpIcon({
  content,
  learnMoreUrl,
  side = 'top',
  className,
}: HelpIconProps) {
  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <HelpCircle
            className={cn(
              'h-4 w-4 text-muted-foreground cursor-help hover:text-foreground transition-colors',
              className
            )}
          />
        </TooltipTrigger>
        <TooltipContent side={side} className="max-w-xs">
          <p className="text-sm">{content}</p>
          {learnMoreUrl && (
            <a
              href={learnMoreUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-amber-500 hover:text-amber-600 mt-1"
              onClick={(e) => e.stopPropagation()}
            >
              Learn more
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
