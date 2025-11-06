/**
 * Edit Content Modal Component
 * Edit individual content metadata
 */

import { useState, useEffect } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
import { useUpdateContent } from '../hooks/useContent';
import type { Content } from '../types/content';

interface EditContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: Content | null;
}

export function EditContentModal({ isOpen, onClose, content }: EditContentModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState(10);
  const [isActive, setIsActive] = useState(true);

  const updateMutation = useUpdateContent();

  // Pre-populate form when content changes
  useEffect(() => {
    if (content) {
      setTitle(content.title || '');
      setDescription(content.description || '');
      setDuration(content.duration || 10);
      setIsActive(content.is_active ?? true);
    }
  }, [content]);

  if (!isOpen || !content) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id: content.id,
        data: {
          title: title.trim(),
          description: description.trim() || undefined,
          duration,
          is_active: isActive,
        },
      });

      onClose();
    } catch (error) {
      // Error handled by mutation hook
      console.error('Update error:', error);
    }
  };

  const handleClose = () => {
    if (updateMutation.isPending) return;
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Edit Content
          </h2>
          <button
            onClick={handleClose}
            disabled={updateMutation.isPending}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Content Info */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 dark:text-gray-400">File Name</p>
                <p className="text-gray-900 dark:text-white font-medium truncate">
                  {content.original_filename}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Type</p>
                <p className="text-gray-900 dark:text-white font-medium">
                  {content.content_type.toUpperCase()}
                </p>
              </div>
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={updateMutation.isPending}
              className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
              placeholder="Enter content title"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={updateMutation.isPending}
              className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
              placeholder="Enter content description (optional)"
              rows={3}
            />
          </div>

          {/* Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Display Duration (seconds)
            </label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              disabled={updateMutation.isPending}
              className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
              min={1}
              max={86400}
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              How long this content should display in playlists (1-86400 seconds)
            </p>
          </div>

          {/* Active Status */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="edit-is-active"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              disabled={updateMutation.isPending}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            />
            <label
              htmlFor="edit-is-active"
              className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Active (available for playlists)
            </label>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              disabled={updateMutation.isPending}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || updateMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
