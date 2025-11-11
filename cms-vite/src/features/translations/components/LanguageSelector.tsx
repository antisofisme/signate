/**
 * Language Selector Component
 * Select language with visual cards showing flags and names
 */

import { LANGUAGES, type Language } from '../types/translation.types'

interface LanguageSelectorProps {
  selectedLanguage?: Language
  onSelect: (language: Language) => void
  disabled?: boolean
  label?: string
  multiSelect?: boolean
  selectedLanguages?: Language[]
  onMultiSelect?: (languages: Language[]) => void
}

export const LanguageSelector = ({
  selectedLanguage,
  onSelect,
  disabled = false,
  label = 'Select Language',
  multiSelect = false,
  selectedLanguages = [],
  onMultiSelect,
}: LanguageSelectorProps) => {
  const handleLanguageClick = (language: Language) => {
    if (disabled) return

    if (multiSelect && onMultiSelect) {
      // Toggle language in multi-select mode
      if (selectedLanguages.includes(language)) {
        onMultiSelect(selectedLanguages.filter((lang) => lang !== language))
      } else {
        onMultiSelect([...selectedLanguages, language])
      }
    } else {
      // Single select mode
      onSelect(language)
    }
  }

  const isSelected = (language: Language) => {
    if (multiSelect) {
      return selectedLanguages.includes(language)
    }
    return selectedLanguage === language
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-3">
        {label}
        {multiSelect && (
          <span className="ml-2 text-xs text-gray-500">
            ({selectedLanguages.length} selected)
          </span>
        )}
      </label>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.values(LANGUAGES).map((lang) => {
          const selected = isSelected(lang.code)

          return (
            <button
              key={lang.code}
              type="button"
              onClick={() => handleLanguageClick(lang.code)}
              disabled={disabled}
              className={`
                p-3 rounded-lg border-2 transition-all
                ${
                  selected
                    ? 'border-blue-500 bg-blue-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex flex-col items-center gap-1">
                <span className="text-3xl">{lang.flag}</span>
                <span className="text-xs font-semibold text-gray-900">
                  {lang.name}
                </span>
                <span className="text-xs text-gray-600">{lang.nativeName}</span>
              </div>
            </button>
          )
        })}
      </div>

      {multiSelect && selectedLanguages.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {selectedLanguages.map((langCode) => {
            const lang = LANGUAGES[langCode]
            return (
              <div
                key={langCode}
                className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
              >
                <span>{lang.flag}</span>
                <span>{lang.name}</span>
                <button
                  type="button"
                  onClick={() => handleLanguageClick(langCode)}
                  className="ml-1 hover:text-blue-900"
                >
                  ×
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default LanguageSelector
