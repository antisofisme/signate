/**
 * Add to Playlist Modal
 * Modal for adding content to a playlist
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, List, CheckCircle, Loader2 } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { usePlaylistList, useAddContentToPlaylist } from '@/features/playlists/hooks/usePlaylist';
import type { Content } from '../types/content';

interface AddToPlaylistModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  content: Content | null;
  /** For bulk add - array of content IDs */
  contentIds?: number[];
  onSuccess?: () => void;
}

export function AddToPlaylistModal({
  open,
  onOpenChange,
  content,
  contentIds,
  onSuccess,
}: AddToPlaylistModalProps) {
  const { t } = useTranslation();
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch playlists
  const { data: playlistsData, isLoading: isLoadingPlaylists } = usePlaylistList({ is_active: true });
  const playlists = playlistsData?.items || [];

  // Add content mutation
  const addContentMutation = useAddContentToPlaylist();

  // Filter playlists by search
  const filteredPlaylists = playlists.filter((playlist) =>
    playlist.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Get content IDs to add
  const idsToAdd = contentIds || (content ? [content.id] : []);

  const handleAdd = async () => {
    if (!selectedPlaylistId || idsToAdd.length === 0) return;

    await addContentMutation.mutateAsync({
      id: selectedPlaylistId,
      data: { content_ids: idsToAdd },
    });

    // Reset state and close
    setSelectedPlaylistId(null);
    setSearchQuery('');
    onOpenChange(false);
    onSuccess?.();
  };

  const handleClose = () => {
    setSelectedPlaylistId(null);
    setSearchQuery('');
    onOpenChange(false);
  };

  const contentCount = idsToAdd.length;
  const contentName = content?.title || `${contentCount} item(s)`;

  return (
    <Modal
      isOpen={open}
      onClose={handleClose}
      title={t('contents.addToPlaylist.title', 'Add to Playlist')}
      subtitle={t('contents.addToPlaylist.description', 'Select a playlist to add "{{name}}" to', { name: contentName })}
      maxWidth="md"
    >
      <div className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t('contents.addToPlaylist.searchPlaceholder', 'Search playlists...')}
            className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Playlist List */}
        <div className="max-h-[300px] overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
          {isLoadingPlaylists ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
            </div>
          ) : filteredPlaylists.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-gray-500">
              <List className="w-8 h-8 mb-2" />
              <p className="text-sm">{t('contents.addToPlaylist.noPlaylists', 'No playlists found')}</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredPlaylists.map((playlist) => (
                <button
                  key={playlist.id}
                  onClick={() => setSelectedPlaylistId(playlist.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                    selectedPlaylistId === playlist.id
                      ? 'bg-blue-50 dark:bg-blue-900/20'
                      : ''
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                      selectedPlaylistId === playlist.id
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300 dark:border-gray-600'
                    }`}
                  >
                    {selectedPlaylistId === playlist.id && (
                      <CheckCircle className="w-4 h-4 text-white" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {playlist.name}
                    </p>
                    {playlist.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {playlist.description}
                      </p>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {playlist.content_count || 0} {t('contents.addToPlaylist.items', 'items')}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={handleClose}>
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button
            variant="primary"
            onClick={handleAdd}
            disabled={!selectedPlaylistId || addContentMutation.isPending}
            loading={addContentMutation.isPending}
          >
            {t('contents.addToPlaylist.add', 'Add to Playlist')}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export default AddToPlaylistModal;
