/**
 * Card Component
 * Reusable card layout with optional padding and hover effects
 */

export default function Card({
  children,
  className = '',
  hover = false,
  padding = true,
  onClick
}) {
  const baseStyles = 'bg-white rounded-lg shadow'
  const hoverStyles = hover ? 'hover:shadow-lg transition-shadow duration-200 cursor-pointer' : ''
  const paddingStyles = padding ? 'p-6' : ''

  const classes = `${baseStyles} ${hoverStyles} ${paddingStyles} ${className}`

  return (
    <div className={classes} onClick={onClick}>
      {children}
    </div>
  )
}
