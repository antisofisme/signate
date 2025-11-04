/**
 * i18n Configuration
 * Using i18next for internationalization
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import id from './locales/id.json';
import en from './locales/en.json';

// Get initial language from localStorage or default to 'id'
const getInitialLanguage = (): string => {
  if (typeof window === 'undefined') return 'id';

  const stored = localStorage.getItem('ui-preferences');
  if (stored) {
    try {
      const { language } = JSON.parse(stored).state || {};
      return language || 'id';
    } catch {
      return 'id';
    }
  }
  return 'id';
};

i18n
  .use(initReactI18next)
  .init({
    resources: {
      id: { translation: id },
      en: { translation: en },
    },
    lng: getInitialLanguage(),
    fallbackLng: 'id',
    interpolation: {
      escapeValue: false, // React already escapes
    },
  });

export default i18n;
