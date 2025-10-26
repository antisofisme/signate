/**
 * Badge Component
 * Status badge with color variants
 */

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = ''
}) {
  const baseStyles = 'inline-flex items-center font-medium rounded-full'

  const variants = {
    default: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100',
    primary: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
    success: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
    warning: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
    danger: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    info: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-800 dark:text-cyan-300',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300',
    pink: 'bg-pink-100 dark:bg-pink-900/30 text-pink-800 dark:text-pink-300'
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base'
  }

  const classes = `${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`

  return (
    <span className={classes}>
      {children}
    </span>
  )
}
