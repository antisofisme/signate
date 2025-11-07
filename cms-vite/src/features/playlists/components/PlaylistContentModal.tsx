/**
 * Playlist Content Management Modal
 *
 * Features:
 * - View current playlist content
 * - Add new content (multi-select from available content)
 * - Remove content items
 * - Reorder content with drag & drop
 * - Edit duration per item
 */

import { useState, useEffect } from 'react';
import { X, Plus, Trash2, GripVertical, Clock } from 'lucide-react';
import { toast } from 'sonner';
import {
  usePlaylistContent,
  useAddContentToPlaylist,
  useRemoveContentFromPlaylist,
  useReorderPlaylistContent,
} from '../hooks/usePlaylist';
import { useContentList } from '@/features/contents/hooks/useContent';

interface PlaylistContentModalProps {
  playlistId: number;
  playlistName: string;
  isOpen: boolean;
  onClose: () => void;
}

interface ContentItem {
  id: number;
  content_id: number;
  order_index: number;
  duration: number;
  // From joined content
  content_name?: string;
  content_type?: string;
  file_path?: string;
}

export default function PlaylistContentModal({
  playlistId,
  playlistName,
  isOpen,
  onClose,
}: PlaylistContentModalProps) {
  const [showAddContent, setShowAddContent] = useState(false);
  const [selectedContentIds, setSelectedContentIds] = useState<number[]>([]);
  const [editingDuration, setEditingDuration] = useState<{ [key: number]: number }>({});
  const [localContent, setLocalContent] = useState<ContentItem[]>([]);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // Fetch playlist content
  const { data: contentData, isLoading: loadingContent } = usePlaylistContent(
    playlistId,
    isOpen
  );

  // Fetch available content
  const { data: availableContentData } = useContentList(
    { skip: 0, limit: 100 },
    showAddContent
  );

  // Mutations
  const addContent = useAddContentToPlaylist();
  const removeContent = useRemoveContentFromPlaylist();
  const reorderContent = useReorderPlaylistContent();

  // Update local state when data changes
  useEffect(() => {
    if (contentData?.items) {
      setLocalContent(contentData.items);
    }
  }, [contentData]);

  if (!isOpen) return null;

  const handleAddContent = async () => {
    if (selectedContentIds.length === 0) {
      toast.error('Please select at least one content item');
      return;
    }

    try {
      await addContent.mutateAsync({
        id: playlistId,
        data: { content_ids: selectedContentIds },
      });
      setSelectedContentIds([]);
      setShowAddContent(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const handleRemoveContent = async (itemId: number) => {
    if (!confirm('Remove this content from playlist?')) return;

    try {
      await removeContent.mutateAsync({
        playlistId,
        itemId,
      });
    } catch (error) {
      // Error handled by hook
    }
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const newContent = [...localContent];
    const draggedItem = newContent[draggedIndex];
    newContent.splice(draggedIndex, 1);
    newContent.splice(index, 0, draggedItem);

    setDraggedIndex(index);
    setLocalContent(newContent);
  };

  const handleDragEnd = async () => {
    if (draggedIndex === null) return;

    // Update order_index for all items
    const reorderedItems = localContent.map((item, index) => ({
      id: item.id,
      order_index: index,
      duration: editingDuration[item.id] ?? item.duration,
    }));

    try {
      await reorderContent.mutateAsync({
        id: playlistId,
        data: { content_items: reorderedItems },
      });
      toast.success('Content reordered successfully');
    } catch (error) {
      // Revert on error
      if (contentData?.items) {
        setLocalContent(contentData.items);
      }
    }

    setDraggedIndex(null);
  };

  const handleDurationChange = (itemId: number, duration: number) => {
    setEditingDuration((prev) => ({
      ...prev,
      [itemId]: duration,
    }));
  };

  const handleSaveDuration = async (itemId: number) => {
    const newDuration = editingDuration[itemId];
    if (newDuration === undefined) return;

    const reorderedItems = localContent.map((item) => ({
      id: item.id,
      order_index: item.order_index,
      duration: item.id === itemId ? newDuration : item.duration,
    }));

    try {
      await reorderContent.mutateAsync({
        id: playlistId,
        data: { content_items: reorderedItems },
      });
      toast.success('Duration updated');
      setEditingDuration((prev) => {
        const { [itemId]: _, ...rest } = prev;
        return rest;
      });
    } catch (error) {
      // Error handled by hook
    }
  };

  const availableContents = (availableContentData?.items || []).filter(
    (content) => !localContent.some((item) => item.content_id === content.id)
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Manage Content
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {playlistName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Add Content Section */}
          {showAddContent ? (
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                Add Content to Playlist
              </h3>

              <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
                {availableContents.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No available content to add
                  </p>
                ) : (
                  availableContents.map((content) => (
                    <label
                      key={content.id}
                      className="flex items-center gap-3 p-3 bg-white dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600"
                    >
                      <input
                        type="checkbox"
                        checked={selectedContentIds.includes(content.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedContentIds([...selectedContentIds, content.id]);
                          } else {
                            setSelectedContentIds(
                              selectedContentIds.filter((id) => id !== content.id)
                            );
                          }
                        }}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 dark:text-white">
                          {content.file_name}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {content.content_type} • {content.duration}s
                        </p>
                      </div>
                    </label>
                  ))
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleAddContent}
                  disabled={selectedContentIds.length === 0 || addContent.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {addContent.isPending ? 'Adding...' : `Add ${selectedContentIds.length} item(s)`}
                </button>
                <button
                  onClick={() => {
                    setShowAddContent(false);
                    setSelectedContentIds([]);
                  }}
                  className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowAddContent(true)}
              className="mb-6 w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
            >
              <Plus className="w-5 h-5" />
              Add Content
            </button>
          )}

          {/* Current Content List */}
          <div className="space-y-2">
            <h3 className="font-medium text-gray-900 dark:text-white mb-3">
              Content Items ({localContent.length})
            </h3>

            {loadingContent ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                Loading content...
              </div>
            ) : localContent.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No content in this playlist yet
              </div>
            ) : (
              localContent.map((item, index) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={() => handleDragStart(index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragEnd={handleDragEnd}
                  className={`flex items-center gap-3 p-4 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 cursor-move ${
                    draggedIndex === index ? 'opacity-50' : ''
                  }`}
                >
                  <GripVertical className="w-5 h-5 text-gray-400 flex-shrink-0" />

                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {item.content_name || `Content #${item.content_id}`}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {item.content_type} • Position: {index + 1}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <input
                      type="number"
                      min="1"
                      value={editingDuration[item.id] ?? item.duration}
                      onChange={(e) =>
                        handleDurationChange(item.id, parseInt(e.target.value) || 0)
                      }
                      onBlur={() => {
                        if (editingDuration[item.id] !== undefined) {
                          handleSaveDuration(item.id);
                        }
                      }}
                      className="w-16 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    <span className="text-sm text-gray-500 dark:text-gray-400">s</span>
                  </div>

                  <button
                    onClick={() => handleRemoveContent(item.id)}
                    disabled={removeContent.isPending}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
