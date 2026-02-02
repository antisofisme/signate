/**
 * Toast Hook
 * Simple toast notification system
 */

import { useCallback } from 'react'

interface Toast {
  id: string
  title: string
  description?: string
  variant?: 'default' | 'destructive'
}

interface ToastInput {
  title: string
  description?: string
  variant?: 'default' | 'destructive'
}

// Simple toast implementation using native alert for now
// Can be replaced with proper toast component later
export function useToast() {
  const toast = useCallback(({ title, description, variant }: ToastInput) => {
    // For now, use console and alert as fallback
    // This can be replaced with a proper toast system
    if (variant === 'destructive') {
      console.error(`[Error] ${title}: ${description || ''}`)
    } else {
      console.log(`[Toast] ${title}: ${description || ''}`)
    }

    // Optional: Show native notification if supported
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body: description })
    }

    // For visual feedback in development, we'll log to console
    // In production, this should use a proper toast UI
  }, [])

  return { toast }
}

// Re-export for convenience
export type { Toast, ToastInput }
