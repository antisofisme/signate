/**
 * Modal Component
 *
 * Centralized, reusable modal wrapper using createPortal
 * Renders to #modal-root to avoid CSS interference from parent components
 *
 * Features:
 * - Keyboard navigation (Escape to close)
 * - Focus trap (keeps focus within modal)
 * - ARIA attributes for screen readers
 * - Body scroll lock when open
 *
 * @usage
 * <Modal isOpen={isOpen} onClose={onClose} title="My Modal" maxWidth="lg">
 *   <div className="p-6">Content here</div>
 * </Modal>
 */

import { ReactNode, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import Button from './common/Button';

// Constants - centralized configuration
const MODAL_Z_INDEX = 9999;
const MODAL_ROOT_ID = 'modal-root';

const MAX_WIDTH_CLASSES = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
  '7xl': 'max-w-7xl',
} as const;

type MaxWidthKey = keyof typeof MAX_WIDTH_CLASSES;

// Overlay styles - inline to override any parent CSS (like space-y-*)
const overlayStyles: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  width: '100vw',
  height: '100vh',
  zIndex: MODAL_Z_INDEX,
  margin: 0,
  marginTop: 0,
};

/**
 * Get the modal root element
 */
function getModalRoot(): HTMLElement {
  return document.getElementById(MODAL_ROOT_ID) || document.body;
}

// ============================================================================
// MODAL PROPS
// ============================================================================

interface ModalProps {
  /** Whether the modal is visible */
  isOpen: boolean;
  /** Callback when modal should close */
  onClose: () => void;
  /** Modal content */
  children: ReactNode;
  /** Optional title in header */
  title?: string | ReactNode;
  /** Optional subtitle below title */
  subtitle?: string;
  /** Max width of modal content */
  maxWidth?: MaxWidthKey;
  /** Show close button in header */
  showCloseButton?: boolean;
  /** Show header (title area) */
  showHeader?: boolean;
  /** Custom header content (replaces default header) */
  customHeader?: ReactNode;
  /** Custom footer content (static, doesn't scroll) */
  footer?: ReactNode;
  /** Close on backdrop click */
  closeOnBackdropClick?: boolean;
  /** Background opacity (0-100) */
  backdropOpacity?: number;
  /** Optional className for modal container */
  className?: string;
}

// ============================================================================
// MODAL COMPONENT
// ============================================================================

// Focusable elements selector for focus trap
const FOCUSABLE_SELECTOR = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export function Modal({
  isOpen,
  onClose,
  children,
  title,
  subtitle,
  maxWidth = 'md',
  showCloseButton = true,
  showHeader = true,
  customHeader,
  footer,
  closeOnBackdropClick = true,
  backdropOpacity = 50,
  className = '',
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);
  const hasInitialFocus = useRef(false);

  // Store onClose in ref to avoid dependency issues
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  // Handle Escape key and focus trap
  useEffect(() => {
    if (!isOpen) {
      hasInitialFocus.current = false;
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onCloseRef.current();
      }

      // Focus trap - Tab key
      if (event.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll(FOCUSABLE_SELECTOR);
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        if (event.shiftKey) {
          // Shift + Tab: if on first element, go to last
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          // Tab: if on last element, go to first
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    // Store the previously focused element
    previousActiveElement.current = document.activeElement as HTMLElement;

    // Lock body scroll
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Add keyboard listener
    document.addEventListener('keydown', handleKeyDown);

    // Focus the first input element ONLY on initial open
    let timeoutId: ReturnType<typeof setTimeout> | undefined;
    if (!hasInitialFocus.current) {
      hasInitialFocus.current = true;
      timeoutId = setTimeout(() => {
        if (modalRef.current) {
          // Prefer input/textarea over buttons for forms
          const firstInput = modalRef.current.querySelector('input:not([type="checkbox"]):not([type="radio"]), textarea') as HTMLElement;
          if (firstInput) {
            firstInput.focus();
          } else {
            const firstFocusable = modalRef.current.querySelector(FOCUSABLE_SELECTOR) as HTMLElement;
            if (firstFocusable) {
              firstFocusable.focus();
            } else {
              modalRef.current.focus();
            }
          }
        }
      }, 0);
    }

    // Cleanup
    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener('keydown', handleKeyDown);
      if (timeoutId) clearTimeout(timeoutId);

      // Restore focus to previous element
      if (previousActiveElement.current && previousActiveElement.current.focus) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen]); // Only depend on isOpen, not handleKeyDown

  if (!isOpen) return null;

  const handleBackdropClick = () => {
    if (closeOnBackdropClick) {
      onClose();
    }
  };

  // Generate unique ID for title if it exists
  const titleId = title ? `modal-title-${Math.random().toString(36).substr(2, 9)}` : undefined;

  return createPortal(
    <div
      className="flex items-center justify-center"
      style={{
        ...overlayStyles,
        backgroundColor: `rgba(0, 0, 0, ${backdropOpacity / 100})`,
      }}
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        ref={modalRef}
        className={`bg-white dark:bg-gray-800 rounded-lg w-full ${MAX_WIDTH_CLASSES[maxWidth]} max-h-[90vh] overflow-hidden flex flex-col mx-4 ${className}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
      >
        {/* Custom Header */}
        {customHeader}

        {/* Default Header */}
        {!customHeader && showHeader && (title || showCloseButton) && (
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-6 py-4">
            <div>
              {title && (
                <h2 id={titleId} className="text-xl font-semibold text-gray-900 dark:text-white">
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {subtitle}
                </p>
              )}
            </div>
            {showCloseButton && (
              <Button
                variant="icon"
                size="md"
                onClick={onClose}
                aria-label="Close modal"
              >
                <X className="w-5 h-5" aria-hidden="true" />
              </Button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex-shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>,
    getModalRoot()
  );
}

// ============================================================================
// MODAL OVERLAY (for custom implementations)
// ============================================================================

interface ModalOverlayProps {
  /** Whether the modal is visible */
  isOpen: boolean;
  /** Callback when backdrop is clicked */
  onClose?: () => void;
  /** Custom content (you handle all styling) */
  children: ReactNode;
  /** Background opacity (0-100) */
  backdropOpacity?: number;
}

/**
 * ModalOverlay - Bare portal wrapper for fully custom modal implementations
 * Use this when you need complete control over modal styling
 */
export function ModalOverlay({
  isOpen,
  onClose,
  children,
  backdropOpacity = 50,
}: ModalOverlayProps) {
  if (!isOpen) return null;

  return createPortal(
    <div
      className="flex items-center justify-center"
      style={{
        ...overlayStyles,
        backgroundColor: `rgba(0, 0, 0, ${backdropOpacity / 100})`,
      }}
      onClick={onClose}
    >
      {children}
    </div>,
    getModalRoot()
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export type { ModalProps, ModalOverlayProps, MaxWidthKey };
