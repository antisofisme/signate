/**
 * ScrollTable - Table wrapper with horizontal scroll indicator
 * Shows visual hint when table is scrollable on mobile
 */

import { useRef, useState, useEffect } from 'react'
import { clsx } from 'clsx'

interface ScrollTableProps {
  children: React.ReactNode
  className?: string
}

export function ScrollTable({ children, className }: ScrollTableProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const checkScroll = () => {
    const el = containerRef.current
    if (!el) return

    setCanScrollLeft(el.scrollLeft > 0)
    setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 1)
  }

  useEffect(() => {
    checkScroll()
    window.addEventListener('resize', checkScroll)
    return () => window.removeEventListener('resize', checkScroll)
  }, [])

  return (
    <div className={clsx("relative", className)}>
      {/* Left scroll indicator */}
      {canScrollLeft && (
        <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none lg:hidden" />
      )}

      {/* Right scroll indicator */}
      {canScrollRight && (
        <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none lg:hidden" />
      )}

      {/* Scroll hint text */}
      {canScrollRight && (
        <div className="absolute top-2 right-2 text-xs text-gray-400 bg-white/90 px-2 py-1 rounded shadow-sm z-20 lg:hidden flex items-center gap-1">
          <span>Scroll</span>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      )}

      <div
        ref={containerRef}
        onScroll={checkScroll}
        className="overflow-x-auto"
      >
        {children}
      </div>
    </div>
  )
}
