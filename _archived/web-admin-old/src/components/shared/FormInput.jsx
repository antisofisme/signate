/**
 * FormInput Component
 * Reusable form input component with consistent styling and variants
 *
 * Features:
 * - Multiple input types (text, number, email, password, textarea, select, color)
 * - Label and description support
 * - Disabled and readonly states
 * - Error state with error message
 * - Focus ring styles
 * - Consistent spacing and sizing
 * - Full accessibility support
 *
 * @param {string} label - Label text for the input
 * @param {string} description - Optional help text below the input
 * @param {string} type - Input type (text, number, email, password, textarea, select, color)
 * @param {string} value - Controlled value
 * @param {Function} onChange - Change handler
 * @param {boolean} required - Whether the field is required
 * @param {boolean} disabled - Whether the field is disabled
 * @param {boolean} readonly - Whether the field is readonly
 * @param {string} placeholder - Placeholder text
 * @param {string} error - Error message to display
 * @param {Array} options - Options for select type (array of {value, label})
 * @param {number} rows - Number of rows for textarea
 * @param {string} className - Additional classes for the input
 * @param {string} containerClassName - Additional classes for the container
 * @param {Object} ...rest - Additional props to pass to the input element
 */
export default function FormInput({
  label,
  description,
  type = 'text',
  value,
  onChange,
  required = false,
  disabled = false,
  readonly = false,
  placeholder,
  error,
  options = [],
  rows = 3,
  className = '',
  containerClassName = '',
  ...rest
}) {
  // Base classes for all inputs
  const baseClasses = 'w-full px-3 py-2 border rounded-lg transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white'

  // Variant classes based on state
  const variantClasses = error
    ? 'border-red-300 dark:border-red-600 focus:ring-2 focus:ring-red-500 focus:border-red-500'
    : disabled || readonly
    ? 'border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 cursor-not-allowed'
    : 'border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'

  // Color input has different styling
  const colorClasses = 'w-full h-10 border rounded-lg cursor-pointer'

  // Combined classes
  const inputClasses = type === 'color'
    ? `${colorClasses} ${className}`
    : `${baseClasses} ${variantClasses} ${className}`

  // Render the appropriate input element
  const renderInput = () => {
    if (type === 'textarea') {
      return (
        <textarea
          value={value}
          onChange={onChange}
          required={required}
          disabled={disabled}
          readOnly={readonly}
          placeholder={placeholder}
          rows={rows}
          className={inputClasses}
          {...rest}
        />
      )
    }

    if (type === 'select') {
      return (
        <select
          value={value}
          onChange={onChange}
          required={required}
          disabled={disabled}
          className={inputClasses}
          {...rest}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )
    }

    return (
      <input
        type={type}
        value={value}
        onChange={onChange}
        required={required}
        disabled={disabled}
        readOnly={readonly}
        placeholder={placeholder}
        className={inputClasses}
        {...rest}
      />
    )
  }

  return (
    <div className={containerClassName}>
      {label && (
        <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
          {label}
          {required && <span className="text-red-600 dark:text-red-400 ml-1">*</span>}
        </label>
      )}
      {renderInput()}
      {description && !error && (
        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{description}</p>
      )}
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400 mt-1">{error}</p>
      )}
    </div>
  )
}
