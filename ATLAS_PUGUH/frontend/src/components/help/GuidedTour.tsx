/**
 * GuidedTour - Step-by-step guided tour component
 * Uses a lightweight custom implementation
 */

import { useEffect, useState, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { X, ChevronLeft, ChevronRight, Check } from 'lucide-react'
import { useHelpStore } from '@/stores/helpStore'

export interface TourStep {
  target: string // CSS selector
  title: string
  content: string
  placement?: 'top' | 'right' | 'bottom' | 'left'
  spotlightPadding?: number
}

export interface Tour {
  id: string
  name: string
  steps: TourStep[]
}

// Tour definitions
export const tours: Record<string, Tour> = {
  'dashboard-intro': {
    id: 'dashboard-intro',
    name: 'Dashboard Tour',
    steps: [
      {
        target: '[data-tour="service-cards"]',
        title: 'Core Services',
        content:
          'These are your 5 core services. Click any card to navigate to that domain: IAM, Tenant, Decision, Workflow, or Control.',
        placement: 'bottom',
      },
      {
        target: '[data-tour="quick-stats"]',
        title: 'Quick Statistics',
        content:
          'View real-time statistics for decisions, active rules, and pending workflows at a glance.',
        placement: 'left',
      },
      {
        target: '[data-tour="sidebar"]',
        title: 'Navigation Sidebar',
        content:
          'Use the sidebar to navigate between different domains. Each domain has its own set of pages.',
        placement: 'right',
      },
      {
        target: '[data-tour="tenant-selector"]',
        title: 'Tenant Selector',
        content:
          'Switch between tenants (organizations) you belong to using this dropdown.',
        placement: 'bottom',
      },
      {
        target: '[data-tour="help-button"]',
        title: 'Need Help?',
        content:
          'Click this button anytime to open contextual help for the current page.',
        placement: 'left',
      },
    ],
  },
  'rule-builder-intro': {
    id: 'rule-builder-intro',
    name: 'Rule Builder Tour',
    steps: [
      {
        target: '[data-tour="rule-name"]',
        title: 'Rule Name',
        content:
          'Give your rule a descriptive name that explains what it does.',
        placement: 'bottom',
      },
      {
        target: '[data-tour="condition-builder"]',
        title: 'Condition Builder',
        content:
          'Build conditions that determine when this rule applies. Use AND/OR logic to combine multiple conditions.',
        placement: 'right',
      },
      {
        target: '[data-tour="action-panel"]',
        title: 'Action Configuration',
        content:
          'Define what happens when conditions are met: Allow, Deny, Require Approval, or Flag for review.',
        placement: 'left',
      },
      {
        target: '[data-tour="test-panel"]',
        title: 'Test Your Rule',
        content:
          'Test your rule with sample data before activating to ensure it works as expected.',
        placement: 'top',
      },
    ],
  },
  'workflow-intro': {
    id: 'workflow-intro',
    name: 'Workflow Tour',
    steps: [
      {
        target: '[data-tour="pending-workflows"]',
        title: 'Pending Workflows',
        content:
          'View all workflows waiting for your action. Take action to approve, reject, or delegate.',
        placement: 'bottom',
      },
      {
        target: '[data-tour="workflow-actions"]',
        title: 'Quick Actions',
        content:
          'Approve or reject workflows directly from the list, or click for more options.',
        placement: 'left',
      },
      {
        target: '[data-tour="workflow-filters"]',
        title: 'Filter Workflows',
        content:
          'Filter workflows by status, type, or date range to find what you need.',
        placement: 'bottom',
      },
    ],
  },
}

interface TourOverlayProps {
  tour: Tour
  currentStep: number
  onNext: () => void
  onPrev: () => void
  onSkip: () => void
  onComplete: () => void
}

function TourOverlay({
  tour,
  currentStep,
  onNext,
  onPrev,
  onSkip,
  onComplete,
}: TourOverlayProps) {
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0, height: 0 })
  const [cardPosition, setCardPosition] = useState({ top: 0, left: 0 })

  const step = tour.steps[currentStep]
  const isFirst = currentStep === 0
  const isLast = currentStep === tour.steps.length - 1
  const progress = ((currentStep + 1) / tour.steps.length) * 100

  // Position the spotlight and card
  useEffect(() => {
    const targetEl = document.querySelector(step.target)
    if (!targetEl) {
      console.warn(`Tour target not found: ${step.target}`)
      return
    }

    const rect = targetEl.getBoundingClientRect()
    const padding = step.spotlightPadding ?? 8

    setPosition({
      top: rect.top - padding + window.scrollY,
      left: rect.left - padding,
      width: rect.width + padding * 2,
      height: rect.height + padding * 2,
    })

    // Calculate card position based on placement
    const cardWidth = 320
    const cardHeight = 200 // approximate
    let cardTop = 0
    let cardLeft = 0

    switch (step.placement) {
      case 'top':
        cardTop = rect.top + window.scrollY - cardHeight - 16
        cardLeft = rect.left + rect.width / 2 - cardWidth / 2
        break
      case 'bottom':
        cardTop = rect.bottom + window.scrollY + 16
        cardLeft = rect.left + rect.width / 2 - cardWidth / 2
        break
      case 'left':
        cardTop = rect.top + window.scrollY + rect.height / 2 - cardHeight / 2
        cardLeft = rect.left - cardWidth - 16
        break
      case 'right':
      default:
        cardTop = rect.top + window.scrollY + rect.height / 2 - cardHeight / 2
        cardLeft = rect.right + 16
        break
    }

    // Keep card within viewport
    cardLeft = Math.max(16, Math.min(cardLeft, window.innerWidth - cardWidth - 16))
    cardTop = Math.max(16, cardTop)

    setCardPosition({ top: cardTop, left: cardLeft })
  }, [step])

  return createPortal(
    <>
      {/* Overlay backdrop */}
      <div className="fixed inset-0 z-[9998]">
        {/* Semi-transparent overlay */}
        <div
          className="absolute inset-0 bg-black/50"
          onClick={onSkip}
        />

        {/* Spotlight cutout */}
        <div
          className="absolute bg-transparent border-2 border-amber-500 rounded-lg shadow-[0_0_0_9999px_rgba(0,0,0,0.5)] transition-all duration-300"
          style={{
            top: position.top,
            left: position.left,
            width: position.width,
            height: position.height,
          }}
        />
      </div>

      {/* Tour card */}
      <Card
        className="fixed z-[9999] w-80 shadow-xl animate-in fade-in slide-in-from-bottom-2"
        style={{
          top: cardPosition.top,
          left: cardPosition.left,
        }}
      >
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">{step.title}</CardTitle>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={onSkip}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <Progress value={progress} className="h-1" />
        </CardHeader>
        <CardContent className="pb-3">
          <p className="text-sm text-muted-foreground">{step.content}</p>
        </CardContent>
        <CardFooter className="pt-0">
          <div className="flex items-center justify-between w-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={onPrev}
              disabled={isFirst}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
            <span className="text-xs text-muted-foreground">
              {currentStep + 1} / {tour.steps.length}
            </span>
            {isLast ? (
              <Button size="sm" onClick={onComplete}>
                <Check className="h-4 w-4 mr-1" />
                Done
              </Button>
            ) : (
              <Button size="sm" onClick={onNext}>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>
    </>,
    document.body
  )
}

export function GuidedTour() {
  const { activeTour, setActiveTour, completedTours, markTourComplete } =
    useHelpStore()
  const [currentStep, setCurrentStep] = useState(0)

  const tour = activeTour ? tours[activeTour] : null

  // Skip if already completed or no active tour
  if (!tour || completedTours.includes(activeTour!)) {
    return null
  }

  const handleNext = () => {
    if (currentStep < tour.steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    setCurrentStep(0)
    setActiveTour(null)
  }

  const handleComplete = () => {
    markTourComplete(activeTour!)
    setCurrentStep(0)
  }

  return (
    <TourOverlay
      tour={tour}
      currentStep={currentStep}
      onNext={handleNext}
      onPrev={handlePrev}
      onSkip={handleSkip}
      onComplete={handleComplete}
    />
  )
}

/**
 * Hook to start a tour programmatically
 */
export function useStartTour() {
  const { setActiveTour, completedTours } = useHelpStore()

  return useCallback(
    (tourId: string, force = false) => {
      if (force || !completedTours.includes(tourId)) {
        setActiveTour(tourId)
      }
    },
    [setActiveTour, completedTours]
  )
}
