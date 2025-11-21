/**
 * User Preferences Types
 *
 * Manages user-specific preferences for organization switching and UI behavior.
 * These preferences are persisted in localStorage via Zustand.
 */

/**
 * User preferences for organization switching behavior
 */
export interface UserPreferences {
  /**
   * ID of the last selected organization
   * Used to auto-restore organization selection on login/page refresh
   */
  lastSelectedOrgId: number | null;

  /**
   * History of recently selected organization IDs
   * Maintains last 3 organizations for quick switching
   * Most recent is at index 0
   */
  orgSwitchHistory: number[];

  /**
   * Whether to remember the last selected organization
   * If true, auto-selects lastSelectedOrgId on login
   * If false, always shows organization selector
   */
  rememberOrganization: boolean;

  /**
   * Timestamp of last organization switch
   * Used for analytics and session tracking
   */
  lastSwitchTimestamp: number | null;
}

/**
 * Default user preferences
 */
export const DEFAULT_USER_PREFERENCES: UserPreferences = {
  lastSelectedOrgId: null,
  orgSwitchHistory: [],
  rememberOrganization: true, // Auto-remember by default for better UX
  lastSwitchTimestamp: null,
};

/**
 * Organization switch event payload
 * Emitted when user switches organizations
 */
export interface OrgSwitchEvent {
  /**
   * Previous organization ID (null if first selection)
   */
  previousOrgId: number | null;

  /**
   * New organization ID
   */
  newOrgId: number;

  /**
   * Organization name for display in toasts
   */
  organizationName: string;

  /**
   * Timestamp of the switch
   */
  timestamp: number;

  /**
   * Whether this was triggered by user action or auto-restore
   */
  isUserTriggered: boolean;
}

/**
 * Helper: Add organization ID to switch history
 * Maintains max 3 items, most recent first
 */
export function addToOrgHistory(
  history: number[],
  orgId: number
): number[] {
  // Remove existing occurrence
  const filtered = history.filter((id) => id !== orgId);

  // Add to front
  const updated = [orgId, ...filtered];

  // Keep only last 3
  return updated.slice(0, 3);
}

/**
 * Helper: Validate organization ID exists in user's organizations
 */
export function isValidOrgId(
  orgId: number | null,
  validOrgIds: number[]
): boolean {
  if (orgId === null) return false;
  return validOrgIds.includes(orgId);
}
