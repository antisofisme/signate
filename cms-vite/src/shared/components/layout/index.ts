/**
 * Layout Components Barrel Export
 *
 * Centralized exports for all layout-related components.
 */

export { default as DashboardLayout } from './DashboardLayout';
export { default as Topbar } from './Topbar';
export { default as Sidebar } from './Sidebar';
export { default as PageHeader } from './PageHeader';

// Organization Switcher Components
export {
  OrganizationSwitcher,
  OrganizationSwitcherCompact,
  type OrganizationSwitcherProps,
} from './OrganizationSwitcher';

// Organization Context Indicator Components
export {
  OrgContextIndicator,
  OrgContextBreadcrumb,
  OrgContextSidebarWidget,
  type OrgContextIndicatorProps,
  type OrgIndicatorVariant,
} from './OrgContextIndicator';

// Page Layout Components (Standardized)
export { PageToolbar, default as PageToolbarDefault } from './PageToolbar';
export { PageStats, default as PageStatsDefault } from './PageStats';
export { ViewTabs, default as ViewTabsDefault } from './ViewTabs';
export { FilterButtonGroup, default as FilterButtonGroupDefault } from './FilterButtonGroup';
