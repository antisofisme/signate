/**
 * Modal Component
 *
 * Centralized, reusable modal wrapper using createPortal
 * Renders to #modal-root to avoid CSS interference from parent components
 *
 * @usage
 * <Modal isOpen={isOpen} onClose={onClose} title="My Modal" maxWidth="lg">
 *   <div className="p-6">Content here</div>
 * </Modal>
 */

import { ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

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
  title?: string;
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
  /** Close on backdrop click */
  closeOnBackdropClick?: boolean;
  /** Background opacity (0-100) */
  backdropOpacity?: number;
}

// ============================================================================
// MODAL COMPONENT
// ============================================================================

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
  closeOnBackdropClick = true,
  backdropOpacity = 50,
}: ModalProps) {
  if (!isOpen) return null;

  const handleBackdropClick = () => {
    if (closeOnBackdropClick) {
      onClose();
    }
  };

  return createPortal(
    <div
      className={`bg-black/${backdropOpacity} flex items-center justify-center`}
      style={overlayStyles}
      onClick={handleBackdropClick}
    >
      <div
        className={`bg-white dark:bg-gray-800 rounded-lg w-full ${MAX_WIDTH_CLASSES[maxWidth]} max-h-[90vh] overflow-hidden flex flex-col mx-4`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Custom Header */}
        {customHeader}

        {/* Default Header */}
        {!customHeader && showHeader && (title || showCloseButton) && (
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-6 py-4">
            <div>
              {title && (
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
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
              <button
                onClick={onClose}
                className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400 transition-colors"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
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
      className={`bg-black/${backdropOpacity} flex items-center justify-center`}
      style={overlayStyles}
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
