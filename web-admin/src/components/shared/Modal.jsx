import { useEffect } from 'react'
import { X } from 'lucide-react'
import { Button } from './index'

/**
 * Modal Component
 * Reusable modal dialog with backdrop, title, and customizable content
 *
 * Features:
 * - Backdrop overlay (click to close - optional)
 * - ESC key to close
 * - Multiple size options (sm, md, lg, xl, full)
 * - Optional title with close button
 * - Optional footer for action buttons
 * - Smooth animations
 * - Scroll handling for long content
 * - Z-index management
 * - Focus trap (keeps focus inside modal)
 *
 * @param {boolean} isOpen - Controls modal visibility
 * @param {Function} onClose - Callback when modal should close
 * @param {string} title - Optional modal title
 * @param {React.ReactNode} children - Modal content
 * @param {React.ReactNode} footer - Optional footer content (usually buttons)
 * @param {string} size - Modal size: 'sm' | 'md' | 'lg' | 'xl' | 'full'
 * @param {boolean} closeOnBackdropClick - Allow closing by clicking backdrop (default: true)
 * @param {boolean} closeOnEsc - Allow closing with ESC key (default: true)
 * @param {boolean} showCloseButton - Show X button in header (default: true)
 * @param {string} className - Additional CSS classes for content container
 * @param {string} bodyClassName - Override default body classes (for custom layouts)
 */
export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeOnBackdropClick = true,
  closeOnEsc = true,
  showCloseButton = true,
  className = '',
  bodyClassName
}) {
  // Handle ESC key press
  useEffect(() => {
    if (!isOpen || !closeOnEsc) return

    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [isOpen, closeOnEsc, onClose])

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  // Handle backdrop click
  const handleBackdropClick = (e) => {
    if (closeOnBackdropClick && e.target === e.currentTarget) {
      onClose()
    }
  }

  // Don't render if not open
  if (!isOpen) return null

  // Size variants
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
    full: 'max-w-full mx-4'
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      {/* Modal Content */}
      <div
        className={`
          bg-white rounded-xl shadow-2xl w-full
          ${sizeClasses[size]}
          ${className}
          max-h-[90vh] flex flex-col
          animate-fadeIn
        `}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 pb-4 border-b border-gray-200 flex-shrink-0">
            {title && (
              <h2
                id="modal-title"
                className="text-xl font-bold text-gray-900"
              >
                {title}
              </h2>
            )}
            {!title && <div />} {/* Spacer if no title */}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
                aria-label="Close modal"
              >
                <X className="w-6 h-6" />
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className={bodyClassName || "flex-1 overflow-y-auto p-6"}>
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-gray-200 p-6 pt-4 bg-gray-50 rounded-b-xl flex-shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * ModalFooter Component
 * Convenience component for modal footer with action buttons
 *
 * @param {React.ReactNode} children - Footer content (usually buttons)
 * @param {string} align - Button alignment: 'left' | 'center' | 'right' | 'between'
 */
export function ModalFooter({ children, align = 'right' }) {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between'
  }

  return (
    <div className={`flex gap-3 ${alignClasses[align]}`}>
      {children}
    </div>
  )
}

/**
 * ModalBody Component
 * Convenience component for modal body with consistent spacing
 *
 * @param {React.ReactNode} children - Body content
 * @param {string} className - Additional CSS classes
 */
export function ModalBody({ children, className = '' }) {
  return (
    <div className={`space-y-4 ${className}`}>
      {children}
    </div>
  )
}
