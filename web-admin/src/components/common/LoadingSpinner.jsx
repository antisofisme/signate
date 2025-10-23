/**
 * LoadingSpinner Component
 * Loading indicator with optional text
 */

export default function LoadingSpinner({ size = 'md', text }) {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  }

  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className={`${sizes[size]} border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin`} />
      {text && (
        <p className="mt-4 text-gray-600">
          {text}
        </p>
      )}
    </div>
  )
}
