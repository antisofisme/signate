/**
 * EmptyState Component
 * Displayed when no data is available
 */

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {Icon && (
        <div className="mb-4 text-gray-400 dark:text-gray-500">
          <Icon size={64} />
        </div>
      )}

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>

      {description && (
        <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md">
          {description}
        </p>
      )}

      {action && (
        <div>
          {action}
        </div>
      )}
    </div>
  )
}
