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
