/**
 * useDuplicateGrouping Hook
 *
 * Generic hook for managing duplicate content/file grouping with expand/collapse.
 * Eliminates duplicated logic from ContentTable and MenuMediaTable.
 *
 * @example
 * const {
 *   duplicateMap,
 *   expandedGroups,
 *   toggleGroupExpand,
 *   isGroupExpanded,
 *   getDuplicateInfo,
 *   hasDuplicates
 * } = useDuplicateGrouping(duplicateData);
 */

import { useState, useCallback, useMemo } from 'react';

/**
 * Generic usage info interface
 * ContentTable uses: playlists, tags, devices
 * MenuMediaTable uses: menus
 */
export interface BaseUsage {
  playlists?: { id: number; name: string }[];
  tags?: { id: number; name: string }[];
  devices?: { id: number; name: string }[];
  menus?: { id: number; name: string }[];
}

/**
 * Generic duplicate group interface
 */
export interface DuplicateGroup<T extends BaseUsage = BaseUsage> {
  file_hash: string;
  total_count: number;
  total_size: number;
  contents: {
    id: number;
    usage: T;
    [key: string]: any;
  }[];
}

/**
 * Duplicate info for a single item
 */
export interface DuplicateInfo<T extends BaseUsage = BaseUsage> {
  hash: string;
  usage: T;
  group: DuplicateGroup<T>;
  duplicateCount: number;
  isFirstInGroup: boolean;
}

export interface UseDuplicateGroupingOptions {
  /** Auto-expand groups with only one duplicate */
  autoExpandSingle?: boolean;
  /** Initial expanded hashes */
  initialExpanded?: string[];
}

export interface UseDuplicateGroupingReturn<T extends BaseUsage = BaseUsage> {
  /** Map of item ID to duplicate info */
  duplicateMap: Map<number, DuplicateInfo<T>>;
  /** Set of expanded group hashes */
  expandedGroups: Set<string>;
  /** Toggle expand/collapse for a group */
  toggleGroupExpand: (hash: string) => void;
  /** Check if a group is expanded */
  isGroupExpanded: (hash: string) => boolean;
  /** Get duplicate info for an item */
  getDuplicateInfo: (id: number) => DuplicateInfo<T> | undefined;
  /** Check if an item has duplicates */
  hasDuplicates: (id: number) => boolean;
  /** Check if usage has any references */
  hasUsage: (usage: T) => boolean;
  /** Expand all groups */
  expandAll: () => void;
  /** Collapse all groups */
  collapseAll: () => void;
  /** Get all unique hashes */
  allHashes: string[];
}

export function useDuplicateGrouping<T extends BaseUsage = BaseUsage>(
  duplicateData: DuplicateGroup<T>[] | { data?: DuplicateGroup<T>[] } | null | undefined,
  options: UseDuplicateGroupingOptions = {}
): UseDuplicateGroupingReturn<T> {
  const { autoExpandSingle = false, initialExpanded = [] } = options;

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    () => new Set(initialExpanded)
  );

  // Normalize data - handle both array and { data: [] } formats
  const groups = useMemo(() => {
    if (!duplicateData) return [];
    if (Array.isArray(duplicateData)) return duplicateData;
    return (duplicateData as any).data || [];
  }, [duplicateData]);

  // Build duplicate lookup map
  const duplicateMap = useMemo(() => {
    const map = new Map<number, DuplicateInfo<T>>();

    groups.forEach((group: DuplicateGroup<T>) => {
      group.contents.forEach((item, index) => {
        map.set(item.id, {
          hash: group.file_hash,
          usage: item.usage,
          group,
          duplicateCount: group.total_count,
          isFirstInGroup: index === 0,
        });
      });

      // Auto-expand single duplicates if enabled
      if (autoExpandSingle && group.total_count === 2) {
        setExpandedGroups((prev) => {
          const newSet = new Set(prev);
          newSet.add(group.file_hash);
          return newSet;
        });
      }
    });

    return map;
  }, [groups, autoExpandSingle]);

  // Get all unique hashes
  const allHashes = useMemo(
    () => groups.map((g: DuplicateGroup<T>) => g.file_hash),
    [groups]
  );

  // Toggle group expansion
  const toggleGroupExpand = useCallback((hash: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(hash)) {
        newSet.delete(hash);
      } else {
        newSet.add(hash);
      }
      return newSet;
    });
  }, []);

  // Check if group is expanded
  const isGroupExpanded = useCallback(
    (hash: string): boolean => expandedGroups.has(hash),
    [expandedGroups]
  );

  // Get duplicate info for an item
  const getDuplicateInfo = useCallback(
    (id: number): DuplicateInfo<T> | undefined => duplicateMap.get(id),
    [duplicateMap]
  );

  // Check if item has duplicates
  const hasDuplicates = useCallback(
    (id: number): boolean => duplicateMap.has(id),
    [duplicateMap]
  );

  // Check if usage has any references
  const hasUsage = useCallback((usage: T): boolean => {
    return (
      (usage.playlists?.length ?? 0) > 0 ||
      (usage.tags?.length ?? 0) > 0 ||
      (usage.devices?.length ?? 0) > 0 ||
      (usage.menus?.length ?? 0) > 0
    );
  }, []);

  // Expand all groups
  const expandAll = useCallback(() => {
    setExpandedGroups(new Set(allHashes));
  }, [allHashes]);

  // Collapse all groups
  const collapseAll = useCallback(() => {
    setExpandedGroups(new Set());
  }, []);

  return {
    duplicateMap,
    expandedGroups,
    toggleGroupExpand,
    isGroupExpanded,
    getDuplicateInfo,
    hasDuplicates,
    hasUsage,
    expandAll,
    collapseAll,
    allHashes,
  };
}
