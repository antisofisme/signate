/**
 * Language Selector Component
 * Dropdown with language flags and search capability
 */

import React, { useState, useMemo } from 'react';
import { SUPPORTED_LANGUAGES, Language } from '../../types/translation';

interface LanguageSelectorProps {
  value: string;
  onChange: (languageCode: string) => void;
  excludeLanguages?: string[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  value,
  onChange,
  excludeLanguages = [],
  placeholder = 'Select language',
  disabled = false,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const availableLanguages = useMemo(() => {
    return SUPPORTED_LANGUAGES.filter(
      (lang) => !excludeLanguages.includes(lang.code)
    );
  }, [excludeLanguages]);

  const filteredLanguages = useMemo(() => {
    if (!searchTerm) return availableLanguages;

    const search = searchTerm.toLowerCase();
    return availableLanguages.filter(
      (lang) =>
        lang.name.toLowerCase().includes(search) ||
        lang.nativeName.toLowerCase().includes(search) ||
        lang.code.toLowerCase().includes(search)
    );
  }, [availableLanguages, searchTerm]);

  const selectedLanguage = SUPPORTED_LANGUAGES.find((lang) => lang.code === value);

  const handleSelect = (language: Language) => {
    onChange(language.code);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Selected Value Display */}
      <button
        type="button"
        onClick={handleToggle}
        disabled={disabled}
        className={`
          w-full px-4 py-2 text-left border rounded-lg
          flex items-center justify-between gap-2
          transition-colors
          ${
            disabled
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-white hover:bg-gray-50 text-gray-900'
          }
          ${isOpen ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-gray-300'}
        `}
      >
        {selectedLanguage ? (
          <div className="flex items-center gap-2">
            <span className="text-xl">{selectedLanguage.flag}</span>
            <span className="font-medium">{selectedLanguage.name}</span>
            <span className="text-sm text-gray-500">
              ({selectedLanguage.nativeName})
            </span>
            {selectedLanguage.isRTL && (
              <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                RTL
              </span>
            )}
          </div>
        ) : (
          <span className="text-gray-500">{placeholder}</span>
        )}
        <svg
          className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute z-20 w-full mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-hidden">
            {/* Search Input */}
            <div className="p-2 border-b border-gray-200">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search languages..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                autoFocus
              />
            </div>

            {/* Language List */}
            <div className="overflow-y-auto max-h-80">
              {filteredLanguages.length > 0 ? (
                filteredLanguages.map((language) => (
                  <button
                    key={language.code}
                    type="button"
                    onClick={() => handleSelect(language)}
                    className={`
                      w-full px-4 py-2 text-left flex items-center gap-3
                      hover:bg-gray-50 transition-colors
                      ${value === language.code ? 'bg-blue-50' : ''}
                    `}
                  >
                    <span className="text-2xl">{language.flag}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {language.name}
                        </span>
                        {language.isRTL && (
                          <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                            RTL
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">
                        {language.nativeName} ({language.code})
                      </div>
                    </div>
                    {value === language.code && (
                      <svg
                        className="w-5 h-5 text-blue-600"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </button>
                ))
              ) : (
                <div className="px-4 py-8 text-center text-gray-500">
                  <svg
                    className="w-12 h-12 mx-auto mb-2 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                  <p>No languages found</p>
                  <p className="text-sm">Try a different search term</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-600">
              {filteredLanguages.length} of {availableLanguages.length} languages
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default LanguageSelector;
