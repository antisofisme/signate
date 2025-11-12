/**
 * Playlists Management Page (Wrapper)
 * Wrapper for feature-based PlaylistsPage with PageHeader
 */

import { PageHeader } from '@/shared/components';
import PlaylistsPageContent from '@/features/playlists/pages/PlaylistsPage';

export default function PlaylistsPage() {
  return (
    <>
      <PageHeader
        title="Playlist Management"
        description="Manage content playlists for your devices"
      />
      <PlaylistsPageContent />
    </>
  );
}
