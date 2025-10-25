import { memo } from 'react'

/**
 * Button Component
 * Unified button component with consistent styling across the application
 *
 * Features:
 * - Multiple variants (primary, secondary, danger, success, ghost, outline)
 * - Three sizes (sm, md, lg)
 * - Loading state with spinner
 * - Disabled state
 * - Icon support (left/right)
 * - Full width option
 * - Uses design tokens for consistency
 *
 * @param {string} variant - Button style variant (default: 'primary')
 * @param {string} size - Button size (default: 'md')
 * @param {boolean} disabled - Disabled state
 * @param {boolean} loading - Show loading spinner
 * @param {boolean} fullWidth - Make button full width
 * @param {React.ReactNode} children - Button content
 * @param {React.ReactNode} leftIcon - Icon to display on left
 * @param {React.ReactNode} rightIcon - Icon to display on right
 * @param {string} className - Additional CSS classes
 * @param {Function} onClick - Click handler
 * @param {string} type - Button type (button, submit, reset)
 */
const Button = memo(function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  children,
  leftIcon,
  rightIcon,
  className = '',
  onClick,
  type = 'button',
  ...props
}) {
  // Base styles
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'

  // Size variants
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-base gap-2',
    lg: 'px-6 py-3 text-lg gap-2.5',
  }

  // Variant styles with hardcoded colors for reliability
  const variantStyles = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 shadow-sm hover:shadow-md',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-400 shadow-sm',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-sm hover:shadow-md',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500 shadow-sm hover:shadow-md',
    warning: 'bg-orange-600 text-white hover:bg-orange-700 focus:ring-orange-500 shadow-sm hover:shadow-md',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-400',
    outline: 'bg-transparent border-2 border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400 focus:ring-gray-400',
  }

  // Loading spinner component
  const LoadingSpinner = () => (
    <svg
      className="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  )

  // Combine all styles
  const combinedStyles = `
    ${baseStyles}
    ${sizeStyles[size]}
    ${variantStyles[variant]}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `.trim().replace(/\s+/g, ' ')

  return (
    <button
      type={type}
      className={combinedStyles}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && <LoadingSpinner />}
      {!loading && leftIcon && <span className="inline-flex">{leftIcon}</span>}
      <span>{children}</span>
      {!loading && rightIcon && <span className="inline-flex">{rightIcon}</span>}
    </button>
  )
})

export default Button
