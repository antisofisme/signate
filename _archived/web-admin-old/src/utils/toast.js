import toast from 'react-hot-toast'

/**
 * Toast Utility
 * Centralized toast notification helper using react-hot-toast
 *
 * Provides consistent toast notifications across the application
 * with pre-configured styling and behavior.
 *
 * Usage:
 * import { showToast } from '@/utils/toast'
 *
 * showToast.success('Operation completed!')
 * showToast.error('Something went wrong')
 * showToast.loading('Processing...')
 */

// Toast configuration
const toastConfig = {
  // Default duration
  duration: 3000,

  // Position
  position: 'top-center',

  // Styling
  style: {
    borderRadius: '8px',
    background: '#333',
    color: '#fff',
    padding: '12px 16px',
    fontSize: '14px',
  },
}

// Success toast (green)
const success = (message, options = {}) => {
  return toast.success(message, {
    ...toastConfig,
    icon: '✅',
    style: {
      ...toastConfig.style,
      background: '#10B981',
    },
    ...options,
  })
}

// Error toast (red)
const error = (message, options = {}) => {
  return toast.error(message, {
    ...toastConfig,
    icon: '❌',
    duration: 4000, // Longer for errors
    style: {
      ...toastConfig.style,
      background: '#EF4444',
    },
    ...options,
  })
}

// Warning toast (orange)
const warning = (message, options = {}) => {
  return toast(message, {
    ...toastConfig,
    icon: '⚠️',
    style: {
      ...toastConfig.style,
      background: '#F59E0B',
    },
    ...options,
  })
}

// Info toast (blue)
const info = (message, options = {}) => {
  return toast(message, {
    ...toastConfig,
    icon: 'ℹ️',
    style: {
      ...toastConfig.style,
      background: '#3B82F6',
    },
    ...options,
  })
}

// Loading toast (spinner)
const loading = (message, options = {}) => {
  return toast.loading(message, {
    ...toastConfig,
    ...options,
  })
}

// Promise toast (for async operations)
const promise = (promiseFunction, messages, options = {}) => {
  return toast.promise(
    promiseFunction,
    {
      loading: messages.loading || 'Loading...',
      success: messages.success || 'Success!',
      error: messages.error || 'Error occurred',
    },
    {
      ...toastConfig,
      ...options,
    }
  )
}

// Dismiss all toasts
const dismiss = (toastId) => {
  if (toastId) {
    toast.dismiss(toastId)
  } else {
    toast.dismiss()
  }
}

// Custom toast (for advanced usage)
const custom = (message, options = {}) => {
  return toast(message, {
    ...toastConfig,
    ...options,
  })
}

// Export as named exports
export const showToast = {
  success,
  error,
  warning,
  info,
  loading,
  promise,
  dismiss,
  custom,
}

// Default export
export default showToast
