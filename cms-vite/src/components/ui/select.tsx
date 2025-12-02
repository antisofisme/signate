/**
 * Select Component (shadcn/ui)
 * Custom dropdown select with keyboard navigation
 */

import * as React from 'react';
import { ChevronDown } from 'lucide-react';

interface SelectProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
  disabled?: boolean;
}

interface SelectOption {
  value: string;
  label: string;
}

interface SelectContextValue {
  value: string;
  onValueChange: (value: string) => void;
  open: boolean;
  setOpen: (open: boolean) => void;
  options: SelectOption[];
  registerOption: (option: SelectOption) => void;
}

const SelectContext = React.createContext<SelectContextValue | undefined>(undefined);

function useSelectContext() {
  const context = React.useContext(SelectContext);
  if (!context) {
    throw new Error('Select compound components must be used within Select');
  }
  return context;
}

export function Select({ value, onValueChange, children, disabled = false }: SelectProps) {
  const [open, setOpen] = React.useState(false);
  const [options, setOptions] = React.useState<SelectOption[]>([]);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Register option to track labels
  const registerOption = React.useCallback((option: SelectOption) => {
    setOptions(prev => {
      // Avoid duplicates
      if (prev.some(o => o.value === option.value)) {
        return prev;
      }
      return [...prev, option];
    });
  }, []);

  // Close dropdown when clicking outside the entire select container
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open]);

  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen, options, registerOption }}>
      <div ref={containerRef} className="relative inline-block w-full">{children}</div>
    </SelectContext.Provider>
  );
}

interface SelectTriggerProps {
  className?: string;
  children: React.ReactNode;
  disabled?: boolean;
}

export function SelectTrigger({
  className = '',
  children,
  disabled = false,
}: SelectTriggerProps) {
  const { open, setOpen } = useSelectContext();

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => setOpen(!open)}
      className={`
        flex items-center justify-between w-full px-3 py-2 text-sm
        bg-white dark:bg-gray-800
        border border-gray-300 dark:border-gray-600
        rounded-md shadow-sm
        hover:bg-gray-50 dark:hover:bg-gray-700
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors
        ${className}
      `}
    >
      {children}
      <ChevronDown
        className={`w-4 h-4 ml-2 transition-transform ${open ? 'rotate-180' : ''}`}
      />
    </button>
  );
}

interface SelectValueProps {
  placeholder?: string;
}

export function SelectValue({ placeholder = 'Select...' }: SelectValueProps) {
  const { value, options } = useSelectContext();

  // Find the label for the current value
  const selectedOption = options.find(o => o.value === value);
  const displayText = selectedOption?.label || value || placeholder;

  return (
    <span className={`block truncate ${value ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>
      {displayText}
    </span>
  );
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

export function SelectContent({ children, className = '' }: SelectContentProps) {
  const { open } = useSelectContext();

  if (!open) return null;

  return (
    <div
      className={`
        absolute z-50 w-full mt-1
        bg-white dark:bg-gray-800
        border border-gray-300 dark:border-gray-600
        rounded-md shadow-lg
        max-h-60 overflow-auto
        ${className}
      `}
    >
      {children}
    </div>
  );
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export function SelectItem({ value, children, className = '' }: SelectItemProps) {
  const { value: selectedValue, onValueChange, setOpen, registerOption } = useSelectContext();
  const isSelected = selectedValue === value;

  // Register this option so SelectValue can show the label
  React.useEffect(() => {
    // Extract text content from children for the label
    const label = typeof children === 'string' ? children : value;
    registerOption({ value, label });
  }, [value, children, registerOption]);

  return (
    <button
      type="button"
      onClick={() => {
        onValueChange(value);
        setOpen(false);
      }}
      className={`
        w-full px-3 py-2 text-left text-sm
        hover:bg-gray-100 dark:hover:bg-gray-700
        focus:bg-gray-100 dark:focus:bg-gray-700
        focus:outline-none
        transition-colors
        ${isSelected ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-900 dark:text-gray-100'}
        ${className}
      `}
    >
      {children}
    </button>
  );
}
