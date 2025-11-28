/**
 * Playlists Management Page (Wrapper)
 * Wrapper for feature-based PlaylistsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import PlaylistsPageContent from '@/features/playlists/pages/PlaylistsPage';
import { useTranslation } from 'react-i18next';

export default function PlaylistsPage() {
  const { t } = useTranslation();

  return (
    <>
      <PageHeader
        title={t('playlists.title')}
        description={t('playlists.subtitle', 'Create and manage content playlists for your devices')}
      />
      <PlaylistsPageContent />
    </>
  );
}
