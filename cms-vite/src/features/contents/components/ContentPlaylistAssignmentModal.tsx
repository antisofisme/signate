/**
 * Content Playlist Assignment Modal
 *
 * Kebalikan dari PlaylistContentModal:
 * - PlaylistContentModal: 1 playlist → banyak content (halaman Playlist)
 * - ContentPlaylistAssignmentModal: 1 content → banyak playlist (halaman Konten)
 *
 * Features:
 * - Two-column layout: Available Playlists (left) | Assigned Playlists (right)
 * - Click to assign content to playlist
 * - Remove button to unassign content from playlist
 * - Optimistic UI updates
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { ListMusic, Trash2, Loader2, ArrowRight } from 'lucide-react';
import { Modal, Button } from '@/shared/components';
import { usePlaylistList, useAddContentToPlaylist, useRemoveContentFromPlaylist } from '@/features/playlists/hooks/usePlaylist';
import { useContentPlaylists } from '../hooks/useContent';
import type { Content } from '../types/content';
import type { ContentPlaylistInfo } from '../api/contentApi';

interface ContentPlaylistAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: Content[];
}

export function ContentPlaylistAssignmentModal({
  isOpen,
  onClose,
  selectedContent,
}: ContentPlaylistAssignmentModalProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // LOCAL STATE for optimistic UI updates
  const [assignedPlaylists, setAssignedPlaylists] = useState<ContentPlaylistInfo[]>([]);

  // Fetch all playlists
  const { data: allPlaylistsData, isLoading: isLoadingAllPlaylists } = usePlaylistList({ is_active: true });
  const allPlaylists = allPlaylistsData?.items || [];

  // Fetch playlists already containing the first content item
  const contentId = selectedContent.length === 1 ? selectedContent[0].id : null;
  const { data: contentPlaylists, isLoading: isLoadingContentPlaylists, refetch: refetchContentPlaylists } = useContentPlaylists(contentId, isOpen);

  // Mutations
  const addContentMutation = useAddContentToPlaylist();
  const removeContentMutation = useRemoveContentFromPlaylist();

  // Sync assigned playlists from query data to local state
  // Always sync to get correct item_id from server
  useEffect(() => {
    if (!contentPlaylists) return;
    setAssignedPlaylists(contentPlaylists);
  }, [contentPlaylists]);

  // Reset state when modal closes, invalidate cache when modal opens
  useEffect(() => {
    if (!isOpen) {
      setAssignedPlaylists([]);
    } else if (contentId) {
      // Invalidate cache to force fresh fetch when modal opens
      queryClient.invalidateQueries({ queryKey: ['content', 'playlists', contentId] });
    }
  }, [isOpen, contentId, queryClient]);

  // Derive available playlists from all playlists minus assigned
  const availablePlaylists = allPlaylists.filter(
    (playlist) => !assignedPlaylists.some((assigned) => assigned.id === playlist.id)
  );

  if (!isOpen) return null;

  // Handle assign with OPTIMISTIC UI UPDATE
  const handleAssignPlaylist = async (playlist: typeof allPlaylists[0]) => {
    const contentIds = selectedContent.map((c) => c.id);

    // OPTIMISTIC UPDATE: Add to assigned immediately
    const newAssigned: ContentPlaylistInfo = {
      id: playlist.id,
      item_id: 0, // Will be updated after refetch
      name: playlist.name,
      description: playlist.description || null,
      is_active: playlist.is_active,
      content_count: (playlist.content_count || 0) + 1,
      order_index: 0,
      duration: null,
      created_at: null,
    };
    setAssignedPlaylists((prev) => [...prev, newAssigned]);

    try {
      await addContentMutation.mutateAsync({
        id: playlist.id,
        data: { content_ids: contentIds },
      });
      // Success - refetch to get correct item_id for removal
      await refetchContentPlaylists();
    } catch (error) {
      // ROLLBACK on error: Remove from assigned
      setAssignedPlaylists((prev) => prev.filter((p) => p.id !== playlist.id));
    }
  };

  // Handle unassign with OPTIMISTIC UI UPDATE
  const handleUnassignPlaylist = async (playlist: ContentPlaylistInfo) => {
    // OPTIMISTIC UPDATE: Remove from assigned immediately
    setAssignedPlaylists((prev) => prev.filter((p) => p.id !== playlist.id));

    try {
      await removeContentMutation.mutateAsync({
        playlistId: playlist.id,
        itemId: playlist.item_id,
      });
      // Success - local state already updated
    } catch (error) {
      // ROLLBACK on error: Add back to assigned
      setAssignedPlaylists((prev) => [...prev, playlist]);
    }
  };

  const isOperationPending = addContentMutation.isPending || removeContentMutation.isPending;
  const isLoading = isLoadingAllPlaylists || isLoadingContentPlaylists;

  // Get content title for header
  const contentTitle = selectedContent.length === 1
    ? selectedContent[0].title
    : `${selectedContent.length} ${t('common.contents', 'contents')}`;

  // Custom header with content info
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        {t('contents.playlistModal.title', 'Manage Playlists for Content')}
      </h2>
      <div className="flex items-center gap-2 mt-1">
        {selectedContent.length === 1 && selectedContent[0].thumbnail_url ? (
          <img
            src={selectedContent[0].thumbnail_url}
            alt={contentTitle}
            className="w-6 h-6 rounded object-cover"
          />
        ) : (
          <ListMusic className="w-4 h-4 text-gray-400" />
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
          {contentTitle}
        </p>
      </div>
    </div>
  );

  // Footer with close button
  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button variant="secondary" onClick={onClose} disabled={isOperationPending}>
        {t('common.close', 'Close')}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="5xl"
      customHeader={customHeader}
      footer={footer}
      closeOnBackdropClick={!isOperationPending}
      className="h-[85vh]"
    >
      {/* Two Column Layout */}
      <div className="p-6 min-h-[500px]">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
            {/* Left Column - Available Playlists */}
            <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <ListMusic className="w-4 h-4" />
                {t('contents.playlistModal.availablePlaylists', 'Available Playlists')} ({availablePlaylists.length})
              </h4>

              {availablePlaylists.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <ListMusic className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">
                    {allPlaylists.length > 0
                      ? t('contents.playlistModal.allPlaylistsAssigned', 'Content is in all available playlists')
                      : t('contents.playlistModal.noPlaylistsAvailable', 'No playlists available')}
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[calc(85vh-280px)] overflow-y-auto pr-2">
                  {availablePlaylists.map((playlist) => (
                    <div
                      key={playlist.id}
                      className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-purple-500 dark:hover:border-purple-400 transition-colors cursor-pointer bg-white dark:bg-gray-800"
                      onClick={() => handleAssignPlaylist(playlist)}
                    >
                      <div className="flex gap-3 items-center">
                        {/* Playlist icon */}
                        <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
                          <ListMusic className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                        </div>

                        {/* Playlist info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {playlist.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {playlist.content_count || 0} {t('common.contents', 'contents')}
                          </p>
                        </div>

                        {/* Assign Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAssignPlaylist(playlist);
                          }}
                          disabled={addContentMutation.isPending}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 transition-all"
                          title={t('common.assign', 'Assign')}
                        >
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right Column - Assigned Playlists */}
            <div className="pl-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <ListMusic className="w-4 h-4 text-purple-600" />
                {t('contents.playlistModal.assignedPlaylists', 'Assigned Playlists')} ({assignedPlaylists.length})
              </h4>

              {assignedPlaylists.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <ListMusic className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">{t('contents.playlistModal.noAssignedPlaylists', 'Content is not in any playlist yet')}</p>
                  <p className="text-xs mt-1">{t('contents.playlistModal.clickToAdd', 'Click playlists on the left to add')}</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[calc(85vh-280px)] overflow-y-auto pr-2">
                  {assignedPlaylists.map((playlist) => (
                    <div
                      key={playlist.id}
                      className="group relative border border-purple-200 dark:border-purple-700 rounded-lg p-3 transition-colors bg-purple-50 dark:bg-purple-900/20"
                    >
                      <div className="flex gap-3 items-center">
                        {/* Playlist icon */}
                        <div className="w-10 h-10 rounded-lg bg-purple-200 dark:bg-purple-800/50 flex items-center justify-center flex-shrink-0">
                          <ListMusic className="w-5 h-5 text-purple-700 dark:text-purple-300" />
                        </div>

                        {/* Playlist info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {playlist.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {playlist.content_count || 0} {t('common.contents', 'contents')}
                          </p>
                        </div>

                        {/* Remove Button */}
                        <button
                          onClick={() => handleUnassignPlaylist(playlist)}
                          disabled={removeContentMutation.isPending}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all"
                          title={t('common.remove', 'Remove')}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}

export default ContentPlaylistAssignmentModal;
