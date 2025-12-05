/**
 * Shared Hooks
 *
 * Re-exports all shared custom hooks for easy importing.
 */

export { usePagination } from './usePagination';
export type { PaginationConfig, UsePaginationReturn } from './usePagination';

// Organization-aware query utilities
export {
  useSelectedOrgId,
  createOrgScopedKeys,
  // Query key factories
  deviceKeys,
  contentKeys,
  playlistKeys,
  scheduleKeys,
  tagKeys,
  userKeys,
  roleKeys,
  auditKeys,
  dashboardKeys,
  analyticsKeys,
  templateKeys,
  widgetKeys,
  sessionKeys,
  menuKeys,
  translationKeys,
  organizationKeys,
  weatherKeys,
  pmsKeys,
} from './useOrgQuery';

// Organization switch handlers
export {
  useOrgSwitch,
  useInvalidateOnOrgSwitch,
  useOrgSwitchCallback,
} from './useOrgSwitch';
export type { OrgSwitchConfig } from './useOrgSwitch';

// Table utilities
export { useTableSort } from './useTableSort';
export { useTableSelection } from './useTableSelection';
export type { UseTableSelectionOptions, UseTableSelectionReturn } from './useTableSelection';
export { useDuplicateGrouping } from './useDuplicateGrouping';
export type {
  BaseUsage,
  DuplicateGroup,
  DuplicateInfo,
  UseDuplicateGroupingOptions,
  UseDuplicateGroupingReturn,
} from './useDuplicateGrouping';
