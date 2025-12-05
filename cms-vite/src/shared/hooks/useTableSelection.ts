/**
 * useTableSelection Hook
 *
 * Standardized table row selection for bulk operations.
 * Eliminates duplicated selection logic across ContentTable, MenuMediaTable, etc.
 *
 * @example
 * const { selectedIds, toggleSelection, toggleSelectAll, clearSelection, isSelected, isAllSelected } = useTableSelection<number>();
 *
 * // In checkbox cell:
 * <input type="checkbox" checked={isSelected(item.id)} onChange={() => toggleSelection(item.id)} />
 *
 * // In header checkbox:
 * <input type="checkbox" checked={isAllSelected(items)} onChange={() => toggleSelectAll(items)} />
 */

import { useState, useCallback, useMemo } from 'react';

export interface UseTableSelectionOptions<T> {
  /** Initial selected IDs */
  initialSelection?: T[];
  /** Callback when selection changes */
  onSelectionChange?: (selectedIds: Set<T>) => void;
}

export interface UseTableSelectionReturn<T> {
  /** Set of selected IDs */
  selectedIds: Set<T>;
  /** Number of selected items */
  selectedCount: number;
  /** Check if an item is selected */
  isSelected: (id: T) => boolean;
  /** Toggle selection for a single item */
  toggleSelection: (id: T) => void;
  /** Select multiple items */
  selectMultiple: (ids: T[]) => void;
  /** Check if all items are selected */
  isAllSelected: (items: { id: T }[]) => boolean;
  /** Check if some (but not all) items are selected */
  isIndeterminate: (items: { id: T }[]) => boolean;
  /** Toggle select all items */
  toggleSelectAll: (items: { id: T }[]) => void;
  /** Clear all selections */
  clearSelection: () => void;
  /** Get selected items from data array */
  getSelectedItems: <I extends { id: T }>(items: I[]) => I[];
}

export function useTableSelection<T = number>(
  options: UseTableSelectionOptions<T> = {}
): UseTableSelectionReturn<T> {
  const { initialSelection = [], onSelectionChange } = options;

  const [selectedIds, setSelectedIds] = useState<Set<T>>(
    () => new Set(initialSelection)
  );

  const selectedCount = useMemo(() => selectedIds.size, [selectedIds]);

  const isSelected = useCallback(
    (id: T): boolean => selectedIds.has(id),
    [selectedIds]
  );

  const toggleSelection = useCallback(
    (id: T) => {
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(id)) {
          newSet.delete(id);
        } else {
          newSet.add(id);
        }
        onSelectionChange?.(newSet);
        return newSet;
      });
    },
    [onSelectionChange]
  );

  const selectMultiple = useCallback(
    (ids: T[]) => {
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        ids.forEach((id) => newSet.add(id));
        onSelectionChange?.(newSet);
        return newSet;
      });
    },
    [onSelectionChange]
  );

  const isAllSelected = useCallback(
    (items: { id: T }[]): boolean => {
      if (items.length === 0) return false;
      return items.every((item) => selectedIds.has(item.id));
    },
    [selectedIds]
  );

  const isIndeterminate = useCallback(
    (items: { id: T }[]): boolean => {
      if (items.length === 0) return false;
      const selectedCount = items.filter((item) => selectedIds.has(item.id)).length;
      return selectedCount > 0 && selectedCount < items.length;
    },
    [selectedIds]
  );

  const toggleSelectAll = useCallback(
    (items: { id: T }[]) => {
      setSelectedIds((prev) => {
        // If all are selected, deselect all
        const allSelected = items.every((item) => prev.has(item.id));
        if (allSelected) {
          const newSet = new Set<T>();
          onSelectionChange?.(newSet);
          return newSet;
        }
        // Otherwise, select all
        const newSet = new Set(items.map((item) => item.id));
        onSelectionChange?.(newSet);
        return newSet;
      });
    },
    [onSelectionChange]
  );

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
    onSelectionChange?.(new Set());
  }, [onSelectionChange]);

  const getSelectedItems = useCallback(
    <I extends { id: T }>(items: I[]): I[] => {
      return items.filter((item) => selectedIds.has(item.id));
    },
    [selectedIds]
  );

  return {
    selectedIds,
    selectedCount,
    isSelected,
    toggleSelection,
    selectMultiple,
    isAllSelected,
    isIndeterminate,
    toggleSelectAll,
    clearSelection,
    getSelectedItems,
  };
}
