/**
 * Keyboard Shortcuts Hook
 *
 * Provides keyboard shortcut functionality for organization switching and other actions.
 * Supports both Mac (Cmd) and Windows/Linux (Ctrl) modifiers.
 */

import { useEffect, useCallback, useRef } from 'react';

/**
 * Keyboard shortcut configuration
 */
export interface KeyboardShortcut {
  /**
   * Key to press (e.g., 'k', '1', 'ArrowDown')
   */
  key: string;

  /**
   * Whether Ctrl (Windows/Linux) or Cmd (Mac) must be pressed
   */
  ctrlOrCmd?: boolean;

  /**
   * Whether Shift must be pressed
   */
  shift?: boolean;

  /**
   * Whether Alt must be pressed
   */
  alt?: boolean;

  /**
   * Callback to execute when shortcut is pressed
   */
  callback: (event: KeyboardEvent) => void;

  /**
   * Description for documentation
   */
  description?: string;

  /**
   * Whether to prevent default browser behavior
   */
  preventDefault?: boolean;

  /**
   * Whether shortcut is enabled
   */
  enabled?: boolean;
}

/**
 * Hook: useKeyboardShortcuts
 *
 * Register multiple keyboard shortcuts with automatic cleanup.
 *
 * @param shortcuts - Array of keyboard shortcut configurations
 * @param dependencies - Dependencies array for callback updates
 *
 * @example
 * ```tsx
 * useKeyboardShortcuts([
 *   {
 *     key: 'k',
 *     ctrlOrCmd: true,
 *     callback: () => setIsOpen(true),
 *     description: 'Open organization switcher',
 *     preventDefault: true,
 *   },
 *   {
 *     key: '1',
 *     ctrlOrCmd: true,
 *     callback: () => switchToOrg(0),
 *     description: 'Switch to first organization',
 *   },
 * ], [isOpen, switchToOrg]);
 * ```
 */
export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  dependencies: unknown[] = []
): void {
  // Store shortcuts in ref to avoid recreating listeners
  const shortcutsRef = useRef<KeyboardShortcut[]>(shortcuts);

  // Update ref when shortcuts change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  // Keyboard event handler
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const activeElement = document.activeElement;
    const tagName = activeElement?.tagName.toLowerCase();

    // Don't trigger shortcuts when typing in input fields
    if (
      tagName === 'input' ||
      tagName === 'textarea' ||
      tagName === 'select' ||
      (activeElement as HTMLElement)?.isContentEditable
    ) {
      return;
    }

    // Check each shortcut
    for (const shortcut of shortcutsRef.current) {
      // Skip if disabled
      if (shortcut.enabled === false) continue;

      // Check key match
      if (event.key.toLowerCase() !== shortcut.key.toLowerCase()) continue;

      // Check modifiers
      const ctrlOrCmdPressed =
        (event.ctrlKey && !isMac()) || (event.metaKey && isMac());
      const shiftPressed = event.shiftKey;
      const altPressed = event.altKey;

      const ctrlOrCmdMatch = shortcut.ctrlOrCmd ? ctrlOrCmdPressed : true;
      const shiftMatch = shortcut.shift ? shiftPressed : !shiftPressed;
      const altMatch = shortcut.alt ? altPressed : !altPressed;

      // Execute if all modifiers match
      if (ctrlOrCmdMatch && shiftMatch && altMatch) {
        if (shortcut.preventDefault !== false) {
          event.preventDefault();
          event.stopPropagation();
        }

        shortcut.callback(event);
        return;
      }
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  // Register event listener
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

/**
 * Check if running on Mac
 */
function isMac(): boolean {
  return /Mac|iPod|iPhone|iPad/.test(navigator.platform);
}

/**
 * Get modifier key label (Cmd on Mac, Ctrl on others)
 */
export function getModifierKeyLabel(): string {
  return isMac() ? '⌘' : 'Ctrl';
}

/**
 * Format keyboard shortcut for display
 *
 * @example
 * formatShortcut({ key: 'k', ctrlOrCmd: true }) => 'Cmd+K' or 'Ctrl+K'
 * formatShortcut({ key: 'S', shift: true, ctrlOrCmd: true }) => 'Cmd+Shift+S'
 */
export function formatShortcut(shortcut: Omit<KeyboardShortcut, 'callback'>): string {
  const parts: string[] = [];

  if (shortcut.ctrlOrCmd) {
    parts.push(getModifierKeyLabel());
  }

  if (shortcut.shift) {
    parts.push('Shift');
  }

  if (shortcut.alt) {
    parts.push('Alt');
  }

  parts.push(shortcut.key.toUpperCase());

  return parts.join('+');
}

/**
 * Hook: useKeyboardShortcut (singular)
 *
 * Register a single keyboard shortcut (convenience wrapper).
 *
 * @example
 * ```tsx
 * useKeyboardShortcut('k', () => setIsOpen(true), { ctrlOrCmd: true });
 * ```
 */
export function useKeyboardShortcut(
  key: string,
  callback: (event: KeyboardEvent) => void,
  options: {
    ctrlOrCmd?: boolean;
    shift?: boolean;
    alt?: boolean;
    preventDefault?: boolean;
    enabled?: boolean;
  } = {}
): void {
  const shortcut: KeyboardShortcut = {
    key,
    callback,
    ...options,
  };

  useKeyboardShortcuts([shortcut], [callback]);
}

/**
 * Hook: useArrowKeyNavigation
 *
 * Handle arrow key navigation in a list or menu.
 *
 * @param itemCount - Number of items in the list
 * @param onSelect - Callback when Enter is pressed on current item
 * @param isEnabled - Whether navigation is enabled
 * @returns Current focused index and setter
 *
 * @example
 * ```tsx
 * const [focusedIndex, setFocusedIndex] = useArrowKeyNavigation(
 *   items.length,
 *   (index) => selectItem(items[index]),
 *   isDropdownOpen
 * );
 * ```
 */
export function useArrowKeyNavigation(
  itemCount: number,
  onSelect: (index: number) => void,
  isEnabled: boolean = true
): [number, React.Dispatch<React.SetStateAction<number>>] {
  const [focusedIndex, setFocusedIndex] = React.useState<number>(0);

  useKeyboardShortcuts(
    [
      {
        key: 'ArrowDown',
        callback: () =>
          setFocusedIndex((prev) => (prev + 1) % itemCount),
        enabled: isEnabled,
      },
      {
        key: 'ArrowUp',
        callback: () =>
          setFocusedIndex((prev) => (prev - 1 + itemCount) % itemCount),
        enabled: isEnabled,
      },
      {
        key: 'Enter',
        callback: () => onSelect(focusedIndex),
        enabled: isEnabled,
      },
      {
        key: 'Escape',
        callback: () => setFocusedIndex(0),
        enabled: isEnabled,
      },
    ],
    [itemCount, focusedIndex, onSelect, isEnabled]
  );

  return [focusedIndex, setFocusedIndex];
}

// Fix React import for useArrowKeyNavigation
import React from 'react';
