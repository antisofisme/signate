/**
 * Variant Autocomplete Component
 * Tag-style input with auto-suggest for menu item variants
 */

import { useState, useRef, useEffect } from 'react';
import { X, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VariantAutocompleteProps {
  value: string;
  suggestions: string[];
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const VariantAutocomplete = ({
  value,
  suggestions,
  onChange,
  disabled = false,
  placeholder = 'Add variant...',
}: VariantAutocompleteProps) => {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Parse comma-separated value into array
  const variants = value
    ? value.split(',').map((v) => v.trim()).filter(Boolean)
    : [];

  // Filter suggestions based on input and exclude already selected
  const filteredSuggestions = suggestions.filter(
    (s) =>
      s.toLowerCase().includes(inputValue.toLowerCase()) &&
      !variants.some((v) => v.toLowerCase() === s.toLowerCase())
  );

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const addVariant = (variant: string) => {
    const trimmed = variant.trim();
    if (!trimmed) return;

    // Check if already exists (case-insensitive)
    if (variants.some((v) => v.toLowerCase() === trimmed.toLowerCase())) {
      setInputValue('');
      return;
    }

    const newVariants = [...variants, trimmed];
    onChange(newVariants.join(', '));
    setInputValue('');
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const removeVariant = (index: number) => {
    const newVariants = variants.filter((_, i) => i !== index);
    onChange(newVariants.join(', '));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addVariant(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && variants.length > 0) {
      // Remove last variant when backspace on empty input
      removeVariant(variants.length - 1);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <div
        className={cn(
          'flex flex-wrap items-center gap-1.5 min-h-[36px] px-2 py-1.5 border rounded-md bg-white dark:bg-gray-700',
          'focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500',
          disabled
            ? 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed opacity-60'
            : 'border-gray-300 dark:border-gray-600'
        )}
        onClick={() => !disabled && inputRef.current?.focus()}
      >
        {/* Variant Tags */}
        {variants.map((variant, index) => (
          <span
            key={index}
            className={cn(
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
              'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
            )}
          >
            {variant}
            {!disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeVariant(index);
                }}
                className="hover:text-blue-600 dark:hover:text-blue-400 focus:outline-none"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </span>
        ))}

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={handleKeyDown}
          placeholder={variants.length === 0 ? placeholder : ''}
          disabled={disabled}
          className={cn(
            'flex-1 min-w-[80px] outline-none bg-transparent text-sm',
            'text-gray-900 dark:text-white placeholder-gray-400',
            disabled && 'cursor-not-allowed'
          )}
        />
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && !disabled && (filteredSuggestions.length > 0 || inputValue) && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-48 overflow-y-auto">
          {/* Filtered suggestions */}
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              onClick={() => addVariant(suggestion)}
              className={cn(
                'w-full px-3 py-2 text-left text-sm',
                'hover:bg-gray-100 dark:hover:bg-gray-700',
                'text-gray-900 dark:text-white'
              )}
            >
              {suggestion}
            </button>
          ))}

          {/* Add custom option if input has value and not in suggestions */}
          {inputValue &&
            !filteredSuggestions.some(
              (s) => s.toLowerCase() === inputValue.toLowerCase()
            ) && (
              <button
                type="button"
                onClick={() => addVariant(inputValue)}
                className={cn(
                  'w-full px-3 py-2 text-left text-sm flex items-center gap-2',
                  'hover:bg-gray-100 dark:hover:bg-gray-700',
                  'text-blue-600 dark:text-blue-400'
                )}
              >
                <Plus className="w-3 h-3" />
                Add "{inputValue}"
              </button>
            )}
        </div>
      )}
    </div>
  );
};
