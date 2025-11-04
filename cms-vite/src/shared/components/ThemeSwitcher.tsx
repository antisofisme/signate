/**
 * Theme Switcher Component
 * Toggle between light and dark theme
 */

import { Moon, Sun } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useUIStore } from '@/lib/stores/uiStore';

export function ThemeSwitcher() {
  const { t } = useTranslation();
  const { toggleTheme } = useUIStore();

  return (
    <button
      onClick={toggleTheme}
      className="relative inline-flex h-9 w-9 items-center justify-center rounded-md border-2 border-input bg-white dark:bg-gray-800 hover:bg-yellow-50 dark:hover:bg-gray-700 hover:border-yellow-500 dark:hover:border-yellow-400 transition-all shadow-sm"
      aria-label={t('theme.toggle')}
      title={t('theme.toggle')}
    >
      <Sun className="h-[1.2rem] w-[1.2rem] text-yellow-600 dark:text-yellow-400 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-[1.2rem] w-[1.2rem] text-blue-600 dark:text-blue-400 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">{t('theme.toggle')}</span>
    </button>
  );
}
