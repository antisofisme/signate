/**
 * Tags Management Page (Wrapper)
 * Wrapper for feature-based TagsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import TagsPageContent from '@/features/tags/pages/TagsPage';
import { useTranslation } from 'react-i18next';

export default function TagsPage() {
  const { t } = useTranslation();

  return (
    <>
      <PageHeader
        title={t('tags.title')}
        description={t('tags.description')}
      />
      <TagsPageContent />
    </>
  );
}
