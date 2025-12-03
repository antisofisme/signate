/**
 * SidePanel Component
 *
 * Responsive sidebar panel that shows as:
 * - Desktop (lg+): Fixed sidebar on the right
 * - Mobile (<lg): Drawer overlay that slides in from right
 *
 * Features:
 * - Smooth slide-in animation
 * - Body scroll lock on mobile when open
 * - Keyboard navigation (Escape to close)
 * - Backdrop click to close
 * - Dark mode support
 *
 * @usage
 * <SidePanel
 *   isOpen={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   title="Details"
 * >
 *   <div>Content here</div>
 * </SidePanel>
 */

import { memo, ReactNode, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import Button from './common/Button';
import { Z_INDEX } from '@/shared/constants/zIndex';

interface SidePanelProps {
  /** Whether the mobile drawer is open (only affects mobile view) */
  isOpen: boolean;
  /** Callback when panel should close */
  onClose: () => void;
  /** Optional title in header */
  title?: string;
  /** Optional subtitle below title */
  subtitle?: string;
  /** Panel content */
  children: ReactNode;
  /** Width of the panel */
  width?: 'sm' | 'md' | 'lg';
  /** Show close button */
  showCloseButton?: boolean;
  /** Show header */
  showHeader?: boolean;
  /** Additional className for the panel content */
  className?: string;
  /** Additional className for desktop sidebar container */
  desktopClassName?: string;
}

// Width classes
const WIDTH_CLASSES = {
  sm: 'lg:w-[300px] max-w-[300px]',
  md: 'lg:w-[360px] max-w-[360px]',
  lg: 'lg:w-[420px] max-w-[420px]',
} as const;

const SidePanel = memo<SidePanelProps>(function SidePanel({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  width = 'md',
  showCloseButton = true,
  showHeader = true,
  className = '',
  desktopClassName = '',
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Handle Escape key and body scroll lock on mobile
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    // Lock body scroll on mobile when drawer is open
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Header component (shared between desktop and mobile)
  const Header = () => (
    showHeader && (title || showCloseButton) ? (
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex-shrink-0">
        <div className="min-w-0 flex-1">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5 truncate">
              {subtitle}
            </p>
          )}
        </div>
        {showCloseButton && (
          <Button
            variant="icon"
            size="sm"
            onClick={onClose}
            aria-label="Close panel"
            className="ml-2 flex-shrink-0 lg:hidden"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </Button>
        )}
      </div>
    ) : null
  );

  // Mobile drawer (portal-based)
  const MobileDrawer = () => {
    if (!isOpen) return null;

    return createPortal(
      <div
        className="lg:hidden fixed inset-0"
        style={{ zIndex: Z_INDEX.MODAL }}
        role="dialog"
        aria-modal="true"
        aria-label={title || 'Side panel'}
      >
        {/* Backdrop */}
        <div
          className="absolute inset-0 bg-black/50 transition-opacity duration-300"
          onClick={onClose}
          aria-hidden="true"
        />

        {/* Panel */}
        <div
          ref={panelRef}
          className={`
            absolute right-0 top-0 h-full w-[85%] ${WIDTH_CLASSES[width]}
            bg-white dark:bg-gray-800 shadow-xl
            transform transition-transform duration-300 ease-out
            flex flex-col
            ${isOpen ? 'translate-x-0' : 'translate-x-full'}
          `}
        >
          <Header />
          <div className={`flex-1 overflow-y-auto ${className}`}>
            {children}
          </div>
        </div>
      </div>,
      document.body
    );
  };

  return (
    <>
      {/* Desktop: Fixed sidebar */}
      <div
        className={`
          hidden lg:flex lg:flex-col
          ${WIDTH_CLASSES[width].replace('max-w-', 'lg:max-w-')}
          flex-shrink-0 border-l border-gray-200 dark:border-gray-700
          bg-white dark:bg-gray-800
          ${desktopClassName}
        `}
      >
        <Header />
        <div className={`flex-1 overflow-y-auto ${className}`}>
          {children}
        </div>
      </div>

      {/* Mobile: Drawer overlay */}
      <MobileDrawer />
    </>
  );
});

export default SidePanel;
export type { SidePanelProps };
