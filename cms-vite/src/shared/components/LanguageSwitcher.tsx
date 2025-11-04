/**
 * Language Switcher Component
 * Toggle between Indonesian and English
 */

import { Languages } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useUIStore } from '@/lib/stores/uiStore';

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const { language, setLanguage } = useUIStore();

  const toggleLanguage = () => {
    const newLang = language === 'id' ? 'en' : 'id';
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  return (
    <button
      onClick={toggleLanguage}
      className="relative inline-flex h-9 items-center gap-2 rounded-md border-2 border-input bg-white dark:bg-gray-800 px-3 hover:bg-blue-50 dark:hover:bg-gray-700 hover:border-blue-500 dark:hover:border-blue-400 transition-all text-sm font-semibold shadow-sm"
      aria-label={t('language.switch')}
      title={t('language.switch')}
    >
      <Languages className="h-[1.1rem] w-[1.1rem] text-blue-600 dark:text-blue-400" />
      <span className="uppercase text-gray-900 dark:text-gray-100">{language}</span>
      <span className="sr-only">{t('language.switch')}</span>
    </button>
  );
}
