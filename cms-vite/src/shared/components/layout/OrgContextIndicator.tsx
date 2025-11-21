/**
 * Organization Context Indicator Component
 *
 * Visual badge/chip showing the current organization context.
 * Displayed in various locations (navbar, breadcrumbs, sidebar) to provide
 * constant visual feedback about which organization the user is working in.
 *
 * Features:
 * - Color-coded by organization (stable hash-based colors)
 * - Shows organization name and icon
 * - Multiple display variants (badge, chip, inline)
 * - Responsive design
 */

import { Building2 } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/authStore';
import { useMemo } from 'react';

/**
 * Display variants for the indicator
 */
export type OrgIndicatorVariant = 'badge' | 'chip' | 'inline' | 'compact';

/**
 * Props for OrgContextIndicator
 */
export interface OrgContextIndicatorProps {
  /**
   * Visual variant
   * - badge: Pill-shaped with background color
   * - chip: Small compact version
   * - inline: Text-only with icon
   * - compact: Icon only (for mobile)
   * @default 'badge'
   */
  variant?: OrgIndicatorVariant;

  /**
   * Show organization icon
   * @default true
   */
  showIcon?: boolean;

  /**
   * CSS class name for custom styling
   */
  className?: string;

  /**
   * Click handler (optional, e.g., to open org switcher)
   */
  onClick?: () => void;

  /**
   * Show as clickable/interactive
   * @default false
   */
  interactive?: boolean;
}

/**
 * Generate a stable color for an organization based on its ID
 * Uses hash function to ensure same org always gets same color
 */
function getOrgColor(orgId: number): {
  bg: string;
  text: string;
  border: string;
} {
  // Predefined color palette (balanced, professional colors)
  const colors = [
    { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', border: 'border-blue-300 dark:border-blue-700' },
    { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', border: 'border-green-300 dark:border-green-700' },
    { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300', border: 'border-purple-300 dark:border-purple-700' },
    { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300', border: 'border-orange-300 dark:border-orange-700' },
    { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-700 dark:text-pink-300', border: 'border-pink-300 dark:border-pink-700' },
    { bg: 'bg-indigo-100 dark:bg-indigo-900/30', text: 'text-indigo-700 dark:text-indigo-300', border: 'border-indigo-300 dark:border-indigo-700' },
    { bg: 'bg-teal-100 dark:bg-teal-900/30', text: 'text-teal-700 dark:text-teal-300', border: 'border-teal-300 dark:border-teal-700' },
    { bg: 'bg-cyan-100 dark:bg-cyan-900/30', text: 'text-cyan-700 dark:text-cyan-300', border: 'border-cyan-300 dark:border-cyan-700' },
  ];

  // Hash the org ID to get a stable color index
  const hash = Math.abs(orgId * 2654435761) % colors.length;
  return colors[hash];
}

/**
 * OrgContextIndicator Component
 *
 * @example
 * ```tsx
 * // Badge variant (default)
 * <OrgContextIndicator />
 *
 * // Chip variant
 * <OrgContextIndicator variant="chip" />
 *
 * // Inline variant (breadcrumbs)
 * <OrgContextIndicator variant="inline" />
 *
 * // Interactive (clickable)
 * <OrgContextIndicator
 *   interactive
 *   onClick={() => openOrgSwitcher()}
 * />
 * ```
 */
export function OrgContextIndicator({
  variant = 'badge',
  showIcon = true,
  className = '',
  onClick,
  interactive = false,
}: OrgContextIndicatorProps) {
  const { organizations, selectedOrgId } = useAuthStore();

  // Current organization
  const currentOrg = useMemo(() => {
    return organizations.find((org) => org.id === selectedOrgId);
  }, [organizations, selectedOrgId]);

  // Organization color
  const orgColor = useMemo(() => {
    return selectedOrgId ? getOrgColor(selectedOrgId) : null;
  }, [selectedOrgId]);

  // Don't render if no organization selected
  if (!currentOrg || !orgColor) {
    return null;
  }

  // Common classes
  const isClickable = interactive || !!onClick;
  const baseClasses = `
    flex items-center gap-2 transition-all duration-200
    ${isClickable ? 'cursor-pointer hover:opacity-80' : ''}
    ${className}
  `;

  // Variant-specific rendering
  switch (variant) {
    case 'badge':
      return (
        <div
          className={`
            ${baseClasses}
            px-3 py-1.5 rounded-full
            ${orgColor.bg} ${orgColor.text}
            border ${orgColor.border}
          `}
          onClick={onClick}
          role={isClickable ? 'button' : undefined}
          tabIndex={isClickable ? 0 : undefined}
          title={isClickable ? 'Klik untuk beralih organisasi' : currentOrg.name}
        >
          {showIcon && <Building2 className="w-4 h-4" />}
          <span className="text-sm font-medium">{currentOrg.name}</span>
        </div>
      );

    case 'chip':
      return (
        <div
          className={`
            ${baseClasses}
            px-2 py-1 rounded-md
            ${orgColor.bg} ${orgColor.text}
          `}
          onClick={onClick}
          role={isClickable ? 'button' : undefined}
          tabIndex={isClickable ? 0 : undefined}
          title={currentOrg.name}
        >
          {showIcon && <Building2 className="w-3.5 h-3.5" />}
          <span className="text-xs font-medium">{currentOrg.name}</span>
        </div>
      );

    case 'inline':
      return (
        <div
          className={`
            ${baseClasses}
            ${orgColor.text}
          `}
          onClick={onClick}
          role={isClickable ? 'button' : undefined}
          tabIndex={isClickable ? 0 : undefined}
          title={currentOrg.name}
        >
          {showIcon && <Building2 className="w-4 h-4" />}
          <span className="text-sm font-medium">{currentOrg.name}</span>
        </div>
      );

    case 'compact':
      return (
        <div
          className={`
            ${baseClasses}
            p-2 rounded-lg
            ${orgColor.bg} ${orgColor.text}
            border ${orgColor.border}
          `}
          onClick={onClick}
          role={isClickable ? 'button' : undefined}
          tabIndex={isClickable ? 0 : undefined}
          title={currentOrg.name}
        >
          <Building2 className="w-5 h-5" />
        </div>
      );

    default:
      return null;
  }
}

/**
 * OrgContextBreadcrumb Component
 *
 * Displays organization context in breadcrumb format.
 * Useful for page headers and navigation.
 *
 * @example
 * ```tsx
 * <OrgContextBreadcrumb />
 * ```
 */
export function OrgContextBreadcrumb({ className = '' }: { className?: string }) {
  const { organizations, selectedOrgId } = useAuthStore();

  const currentOrg = organizations.find((org) => org.id === selectedOrgId);
  const orgColor = selectedOrgId ? getOrgColor(selectedOrgId) : null;

  if (!currentOrg || !orgColor) {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Building2 className={`w-4 h-4 ${orgColor.text}`} />
      <span className={`text-sm font-medium ${orgColor.text}`}>
        {currentOrg.name}
      </span>
      <span className="text-gray-400 dark:text-gray-600">/</span>
    </div>
  );
}

/**
 * OrgContextSidebarWidget Component
 *
 * Compact organization indicator for sidebar footer.
 * Shows organization name with icon, clickable to open switcher.
 *
 * @example
 * ```tsx
 * <OrgContextSidebarWidget onSwitch={() => openSwitcher()} />
 * ```
 */
export function OrgContextSidebarWidget({
  onSwitch,
  className = '',
}: {
  onSwitch?: () => void;
  className?: string;
}) {
  const { organizations, selectedOrgId } = useAuthStore();

  const currentOrg = organizations.find((org) => org.id === selectedOrgId);
  const orgColor = selectedOrgId ? getOrgColor(selectedOrgId) : null;

  if (!currentOrg || !orgColor) {
    return null;
  }

  return (
    <div
      className={`
        flex items-center gap-3 px-4 py-3 rounded-lg
        ${orgColor.bg}
        border ${orgColor.border}
        ${onSwitch ? 'cursor-pointer hover:opacity-90' : ''}
        transition-all duration-200
        ${className}
      `}
      onClick={onSwitch}
      role={onSwitch ? 'button' : undefined}
      tabIndex={onSwitch ? 0 : undefined}
      title={onSwitch ? 'Klik untuk beralih organisasi' : currentOrg.name}
    >
      {/* Icon */}
      <div className={`p-2 rounded-lg bg-white dark:bg-gray-800 ${orgColor.text}`}>
        <Building2 className="w-5 h-5" />
      </div>

      {/* Organization Info */}
      <div className="flex-1 min-w-0">
        <p className={`text-xs font-medium ${orgColor.text} opacity-75`}>
          Organisasi Aktif
        </p>
        <p className={`text-sm font-semibold ${orgColor.text} truncate`}>
          {currentOrg.name}
        </p>
      </div>

      {/* Arrow hint (if clickable) */}
      {onSwitch && (
        <svg
          className={`w-4 h-4 ${orgColor.text} opacity-50`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      )}
    </div>
  );
}
