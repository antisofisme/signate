/**
 * Tags Input Component
 * Tag-style input with comma-separated badges for menu item tags
 */

import { useState, useRef } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TagsInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const TagsInput = ({
  value,
  onChange,
  disabled = false,
  placeholder = 'Add tags...',
}: TagsInputProps) => {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Parse comma-separated value into array
  const tags = value
    ? value.split(',').map((v) => v.trim()).filter(Boolean)
    : [];

  const addTag = (tag: string) => {
    const trimmed = tag.trim();
    if (!trimmed) return;

    // Check if already exists (case-insensitive)
    if (tags.some((t) => t.toLowerCase() === trimmed.toLowerCase())) {
      setInputValue('');
      return;
    }

    const newTags = [...tags, trimmed];
    onChange(newTags.join(', '));
    setInputValue('');
    inputRef.current?.focus();
  };

  const removeTag = (index: number) => {
    const newTags = tags.filter((_, i) => i !== index);
    onChange(newTags.join(', '));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
      // Remove last tag when backspace on empty input
      removeTag(tags.length - 1);
    }
  };

  const handleBlur = () => {
    // Add tag on blur if there's input
    if (inputValue.trim()) {
      addTag(inputValue);
    }
  };

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-1.5 h-[32px] px-2 py-1 border rounded-md',
        'bg-white dark:bg-gray-900 text-gray-900 dark:text-white',
        'border-gray-300 dark:border-gray-600',
        'focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500',
        disabled && 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed opacity-60'
      )}
      onClick={() => !disabled && inputRef.current?.focus()}
    >
      {/* Tag Badges */}
      {tags.map((tag, index) => (
        <span
          key={index}
          className={cn(
            'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
            'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200'
          )}
        >
          {tag}
          {!disabled && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                removeTag(index);
              }}
              className="hover:text-amber-600 dark:hover:text-amber-400 focus:outline-none"
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
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={tags.length === 0 ? placeholder : ''}
        disabled={disabled}
        className={cn(
          'flex-1 min-w-[60px] outline-none bg-transparent text-sm',
          'text-gray-900 dark:text-white placeholder-gray-400',
          disabled && 'cursor-not-allowed'
        )}
      />
    </div>
  );
};
