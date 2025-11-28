/**
 * Translations Management Page (Wrapper)
 * Wrapper for feature-based TranslationsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import TranslationsPageContent from '@/features/translations/pages/TranslationsPage';

export default function TranslationsPage() {
  return (
    <>
      <PageHeader
        title="Translation Manager"
        description="Manage translations for multi-language support"
      />
      <TranslationsPageContent />
    </>
  );
}
