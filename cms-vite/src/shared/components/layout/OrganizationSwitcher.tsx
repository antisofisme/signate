/**
 * Organization Switcher Component
 *
 * Dropdown component for seamless organization switching from any page.
 * Replaces the need to navigate to a separate organization selection page.
 *
 * Features:
 * - Dropdown menu with all user organizations
 * - Current organization highlighted
 * - Keyboard shortcuts (Ctrl/Cmd+K to open, arrow keys to navigate)
 * - Smooth transitions and loading states
 * - Auto-invalidates organization-scoped caches
 * - Works on mobile (responsive design)
 */

import { useState, useMemo } from 'react';
import { Building2, Check, ChevronDown, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/authStore';
import { useOrgSwitch } from '@/shared/hooks/useOrgSwitch';
import { useKeyboardShortcut } from '@/shared/hooks/useKeyboardShortcuts';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

/**
 * Props for OrganizationSwitcher component
 */
export interface OrganizationSwitcherProps {
  /**
   * CSS class name for custom styling
   */
  className?: string;

  /**
   * Show organization PIN in dropdown
   * @default false
   */
  showPin?: boolean;

  /**
   * Maximum organizations to show before scrolling
   * @default 8
   */
  maxVisibleOrgs?: number;
}

/**
 * OrganizationSwitcher Component
 *
 * @example
 * ```tsx
 * <OrganizationSwitcher />
 * <OrganizationSwitcher showPin={true} />
 * ```
 */
export function OrganizationSwitcher({
  className = '',
  showPin = false,
  maxVisibleOrgs = 8,
}: OrganizationSwitcherProps) {
  const { organizations, selectedOrgId, switchOrganization } = useAuthStore();
  const { isSwitching } = useOrgSwitch();
  const [isOpen, setIsOpen] = useState(false);

  // Current organization
  const currentOrg = useMemo(() => {
    return organizations.find((org) => org.id === selectedOrgId);
  }, [organizations, selectedOrgId]);

  // Active organizations only
  const activeOrganizations = useMemo(() => {
    return organizations.filter((org) => org.is_active);
  }, [organizations]);

  // Handle organization switch
  const handleSwitch = (orgId: number) => {
    if (orgId === selectedOrgId) {
      setIsOpen(false);
      return;
    }

    switchOrganization(orgId, true);
    setIsOpen(false);
  };

  // Keyboard shortcut: Ctrl/Cmd+K to open switcher
  useKeyboardShortcut(
    'k',
    () => {
      setIsOpen((prev) => !prev);
    },
    {
      ctrlOrCmd: true,
      enabled: activeOrganizations.length > 1,
    }
  );

  // Quick switch shortcuts: Ctrl/Cmd+1-9
  for (let i = 0; i < Math.min(9, activeOrganizations.length); i++) {
    useKeyboardShortcut(
      `${i + 1}`,
      () => {
        if (activeOrganizations[i]) {
          handleSwitch(activeOrganizations[i].id);
        }
      },
      {
        ctrlOrCmd: true,
        enabled: activeOrganizations.length > 1,
      }
    );
  }

  // Don't show switcher if user has only one organization
  if (organizations.length <= 1) {
    return null;
  }

  return (
    <DropdownMenu.Root open={isOpen} onOpenChange={setIsOpen}>
      {/* Trigger Button */}
      <DropdownMenu.Trigger asChild>
        <button
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg
            bg-white dark:bg-gray-800
            border border-gray-300 dark:border-gray-600
            hover:bg-gray-50 dark:hover:bg-gray-700
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            transition-all duration-200
            ${isSwitching ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
            ${className}
          `}
          disabled={isSwitching}
          title="Beralih organisasi (Ctrl/Cmd+K)"
        >
          {/* Icon */}
          <Building2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />

          {/* Organization Name */}
          <span className="text-sm font-medium text-gray-900 dark:text-white max-w-[200px] truncate">
            {currentOrg?.name || 'Pilih Organisasi'}
          </span>

          {/* Loading Spinner or Chevron */}
          {isSwitching ? (
            <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
          ) : (
            <ChevronDown
              className={`
                w-4 h-4 text-gray-400 transition-transform duration-200
                ${isOpen ? 'rotate-180' : ''}
              `}
            />
          )}
        </button>
      </DropdownMenu.Trigger>

      {/* Dropdown Content */}
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className={`
            min-w-[280px] p-1 rounded-lg shadow-lg
            bg-white dark:bg-gray-800
            border border-gray-200 dark:border-gray-700
            z-50
            animate-in fade-in-0 zoom-in-95
            data-[side=bottom]:slide-in-from-top-2
            data-[side=top]:slide-in-from-bottom-2
          `}
          sideOffset={5}
          align="start"
          style={{
            maxHeight: `${maxVisibleOrgs * 60 + 16}px`,
            overflowY: 'auto',
          }}
        >
          {/* Header */}
          <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Pilih Organisasi
            </p>
          </div>

          {/* Organization List */}
          <div className="py-1">
            {activeOrganizations.map((org, index) => {
              const isCurrent = org.id === selectedOrgId;

              return (
                <DropdownMenu.Item
                  key={org.id}
                  className={`
                    flex items-center justify-between gap-3 px-3 py-2.5 mx-1 rounded-md
                    cursor-pointer outline-none
                    transition-colors duration-150
                    ${
                      isCurrent
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white'
                    }
                    focus:bg-gray-100 dark:focus:bg-gray-700
                  `}
                  onClick={() => handleSwitch(org.id)}
                >
                  {/* Left: Organization Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {/* Organization Name */}
                      <p
                        className={`
                        text-sm font-medium truncate
                        ${isCurrent ? 'font-semibold' : ''}
                      `}
                      >
                        {org.name}
                      </p>

                      {/* Current Badge */}
                      {isCurrent && (
                        <span className="px-1.5 py-0.5 text-xs font-medium rounded bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200">
                          Aktif
                        </span>
                      )}
                    </div>

                    {/* Organization PIN (optional) */}
                    {showPin && org.organization_pin && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-0.5">
                        PIN: {org.organization_pin}
                      </p>
                    )}

                    {/* Keyboard Shortcut Hint (first 9 orgs) */}
                    {index < 9 && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                        Ctrl/Cmd+{index + 1}
                      </p>
                    )}
                  </div>

                  {/* Right: Check Icon */}
                  {isCurrent && (
                    <Check className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                  )}
                </DropdownMenu.Item>
              );
            })}
          </div>

          {/* Footer: Keyboard Shortcut Hint */}
          <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Tekan <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 font-mono">Ctrl/Cmd+K</kbd> untuk membuka
            </p>
          </div>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

/**
 * Compact version of OrganizationSwitcher for mobile/sidebar
 */
export function OrganizationSwitcherCompact({
  className = '',
}: {
  className?: string;
}) {
  const { organizations, selectedOrgId, switchOrganization } = useAuthStore();
  const { isSwitching } = useOrgSwitch();
  const [isOpen, setIsOpen] = useState(false);

  const currentOrg = organizations.find((org) => org.id === selectedOrgId);
  const activeOrganizations = organizations.filter((org) => org.is_active);

  const handleSwitch = (orgId: number) => {
    if (orgId !== selectedOrgId) {
      switchOrganization(orgId, true);
    }
    setIsOpen(false);
  };

  if (organizations.length <= 1) {
    return null;
  }

  return (
    <DropdownMenu.Root open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenu.Trigger asChild>
        <button
          className={`
            flex items-center justify-between w-full px-3 py-2 rounded-lg
            bg-gray-100 dark:bg-gray-800
            hover:bg-gray-200 dark:hover:bg-gray-700
            focus:outline-none focus:ring-2 focus:ring-blue-500
            transition-all duration-200
            ${isSwitching ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
            ${className}
          `}
          disabled={isSwitching}
        >
          <div className="flex items-center gap-2 min-w-0">
            <Building2 className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0" />
            <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {currentOrg?.name || 'Pilih'}
            </span>
          </div>
          {isSwitching ? (
            <Loader2 className="w-4 h-4 text-gray-400 animate-spin flex-shrink-0" />
          ) : (
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          )}
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="min-w-[240px] p-1 rounded-lg shadow-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 z-50"
          sideOffset={5}
        >
          {activeOrganizations.map((org) => (
            <DropdownMenu.Item
              key={org.id}
              className={`
                flex items-center justify-between gap-2 px-3 py-2 rounded-md cursor-pointer outline-none
                ${
                  org.id === selectedOrgId
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white'
                }
              `}
              onClick={() => handleSwitch(org.id)}
            >
              <span className="text-sm font-medium truncate">{org.name}</span>
              {org.id === selectedOrgId && (
                <Check className="w-4 h-4 flex-shrink-0" />
              )}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
