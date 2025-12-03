/**
 * Organization Switch Hook
 *
 * Listens for organization switch events and automatically invalidates
 * organization-scoped React Query caches. Ensures data consistency when
 * switching between organizations.
 */

import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ORG_SWITCH_EVENT_NAME } from '@/lib/stores/authStore';
import type { OrgSwitchEvent } from '@/features/auth/types/userPreferences';
import { toast } from 'sonner';
import { logger } from '@/shared/utils/logger';

/**
 * Configuration for cache invalidation behavior
 */
export interface OrgSwitchConfig {
  /**
   * Whether to show toast notification when switching
   * @default true
   */
  showToast?: boolean;

  /**
   * Whether to invalidate all organization-scoped queries
   * @default true
   */
  invalidateCaches?: boolean;

  /**
   * Custom query keys to invalidate (in addition to defaults)
   * @default []
   */
  customQueryKeys?: string[];

  /**
   * Callback fired before cache invalidation
   */
  onBeforeSwitch?: (event: OrgSwitchEvent) => void;

  /**
   * Callback fired after cache invalidation completes
   */
  onAfterSwitch?: (event: OrgSwitchEvent) => void;

  /**
   * Debounce time in milliseconds to prevent rapid switching
   * @default 300
   */
  debounceMs?: number;
}

/**
 * Default organization-scoped query keys to invalidate
 *
 * These are the core queries that depend on selected organization.
 * All query keys that fetch organization-specific data must be listed here
 * to ensure proper cache invalidation when user switches organizations.
 */
const DEFAULT_ORG_SCOPED_QUERY_KEYS = [
  // Core entities
  'devices',
  'device',
  'content',
  'contents',
  'playlists',
  'playlist',
  'playlist-widgets',
  'schedules',
  'schedule',
  'schedule-occurrences',
  'device-schedules',
  'playlist-schedules',
  'tags',
  'tag',
  // Dashboard & Analytics
  'dashboard',
  'stats',
  'analytics',
  'reports',
  'assignments',
  // User Management
  'users',
  'user',
  'roles',
  'role',
  'sessions',
  'session',
  // Audit & Organization
  'audit-logs',
  'audit',
  'organization-quota',
  'quota',
  // Templates & Widgets
  'templates',
  'template',
  'widgets',
  'widget',
  // Integrations
  'weather',
  'weather-config',
  'weather-locations',
  'pms',
  'pms-config',
  'pms-rooms',
];

/**
 * Hook: useOrgSwitch
 *
 * Automatically handles cache invalidation and UI feedback when user
 * switches organizations. Listens to the global org-switch event and
 * invalidates all organization-scoped React Query caches.
 *
 * @param config - Configuration options
 *
 * @example
 * ```tsx
 * // Basic usage - automatic cache invalidation with toast
 * useOrgSwitch();
 *
 * // Custom configuration
 * useOrgSwitch({
 *   showToast: true,
 *   customQueryKeys: ['custom-data'],
 *   onAfterSwitch: (event) => {
 *     console.log(`Switched to ${event.organizationName}`);
 *   },
 * });
 * ```
 */
export function useOrgSwitch(config: OrgSwitchConfig = {}): {
  isSwitching: boolean;
  lastSwitchEvent: OrgSwitchEvent | null;
} {
  const {
    showToast = true,
    invalidateCaches = true,
    customQueryKeys = [],
    onBeforeSwitch,
    onAfterSwitch,
    debounceMs = 300,
  } = config;

  const queryClient = useQueryClient();
  const [isSwitching, setIsSwitching] = useState(false);
  const [lastSwitchEvent, setLastSwitchEvent] = useState<OrgSwitchEvent | null>(
    null
  );

  useEffect(() => {
    let debounceTimeout: ReturnType<typeof setTimeout> | null = null;

    const handleOrgSwitch = async (event: Event) => {
      const customEvent = event as CustomEvent<OrgSwitchEvent>;
      const switchEvent = customEvent.detail;

      // Clear existing debounce
      if (debounceTimeout) {
        clearTimeout(debounceTimeout);
      }

      // Debounce to prevent rapid switching
      debounceTimeout = setTimeout(async () => {
        logger.debug('[useOrgSwitch] Organization switch detected', {
          from: switchEvent.previousOrgId,
          to: switchEvent.newOrgId,
          name: switchEvent.organizationName,
          isUserTriggered: switchEvent.isUserTriggered,
        });

        // Set switching state
        setIsSwitching(true);
        setLastSwitchEvent(switchEvent);

        try {
          // Callback: before switch
          if (onBeforeSwitch) {
            onBeforeSwitch(switchEvent);
          }

          // Show toast notification (only for user-triggered switches)
          if (showToast && switchEvent.isUserTriggered) {
            toast.info(`Beralih ke ${switchEvent.organizationName}...`);
          }

          // Invalidate caches
          if (invalidateCaches) {
            // Combine default and custom query keys
            const allQueryKeys = [
              ...DEFAULT_ORG_SCOPED_QUERY_KEYS,
              ...customQueryKeys,
            ];

            // Invalidate each query key
            const invalidations = allQueryKeys.map((queryKey) =>
              queryClient.invalidateQueries({
                queryKey: [queryKey],
                refetchType: 'active', // Only refetch active queries
              })
            );

            // Wait for all invalidations to complete
            await Promise.all(invalidations);

            logger.debug('[useOrgSwitch] Cache invalidation complete', {
              invalidatedKeys: allQueryKeys,
            });
          }

          // Show success toast (only for user-triggered switches)
          if (showToast && switchEvent.isUserTriggered) {
            toast.success(`Berhasil beralih ke ${switchEvent.organizationName}`);
          }

          // Callback: after switch
          if (onAfterSwitch) {
            onAfterSwitch(switchEvent);
          }
        } catch (error) {
          logger.error('[useOrgSwitch] Error during organization switch', error);

          if (showToast) {
            toast.error('Terjadi kesalahan saat beralih organisasi');
          }
        } finally {
          // Reset switching state after a small delay
          setTimeout(() => {
            setIsSwitching(false);
          }, 500);
        }
      }, debounceMs);
    };

    // Listen for org switch events
    window.addEventListener(ORG_SWITCH_EVENT_NAME, handleOrgSwitch);

    // Cleanup
    return () => {
      window.removeEventListener(ORG_SWITCH_EVENT_NAME, handleOrgSwitch);
      if (debounceTimeout) {
        clearTimeout(debounceTimeout);
      }
    };
  }, [
    queryClient,
    showToast,
    invalidateCaches,
    customQueryKeys,
    onBeforeSwitch,
    onAfterSwitch,
    debounceMs,
  ]);

  return {
    isSwitching,
    lastSwitchEvent,
  };
}

/**
 * Hook: useInvalidateOnOrgSwitch
 *
 * Simpler version that only invalidates specific query keys on org switch.
 * Useful for feature-specific cache invalidation.
 *
 * @param queryKeys - Array of query keys to invalidate
 * @param enabled - Whether invalidation is enabled
 *
 * @example
 * ```tsx
 * // In a device management component
 * useInvalidateOnOrgSwitch(['devices', 'device-stats']);
 *
 * // Conditional invalidation
 * useInvalidateOnOrgSwitch(['custom-data'], isFeatureEnabled);
 * ```
 */
export function useInvalidateOnOrgSwitch(
  queryKeys: string[],
  enabled: boolean = true
): void {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled) return;

    const handleOrgSwitch = async () => {
      const invalidations = queryKeys.map((queryKey) =>
        queryClient.invalidateQueries({
          queryKey: [queryKey],
          refetchType: 'active',
        })
      );

      await Promise.all(invalidations);

      logger.debug('[useInvalidateOnOrgSwitch] Invalidated:', queryKeys);
    };

    window.addEventListener(ORG_SWITCH_EVENT_NAME, handleOrgSwitch);

    return () => {
      window.removeEventListener(ORG_SWITCH_EVENT_NAME, handleOrgSwitch);
    };
  }, [queryClient, queryKeys, enabled]);
}

/**
 * Hook: useOrgSwitchCallback
 *
 * Execute a custom callback when organization is switched.
 * Useful for analytics, logging, or custom side effects.
 *
 * @param callback - Function to execute on org switch
 * @param deps - Dependencies array for callback
 *
 * @example
 * ```tsx
 * useOrgSwitchCallback((event) => {
 *   analytics.track('organization_switched', {
 *     from: event.previousOrgId,
 *     to: event.newOrgId,
 *   });
 * }, [analytics]);
 * ```
 */
export function useOrgSwitchCallback(
  callback: (event: OrgSwitchEvent) => void,
  deps: unknown[] = []
): void {
  useEffect(() => {
    const handleOrgSwitch = (event: Event) => {
      const customEvent = event as CustomEvent<OrgSwitchEvent>;
      callback(customEvent.detail);
    };

    window.addEventListener(ORG_SWITCH_EVENT_NAME, handleOrgSwitch);

    return () => {
      window.removeEventListener(ORG_SWITCH_EVENT_NAME, handleOrgSwitch);
    };
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps
}
