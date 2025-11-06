/**
 * Bulk Edit Modal Component
 * Edit multiple content items at once with simplified bulk update
 */

import { useState } from 'react';
import { X, Save, Loader2, FileImage, FileVideo, FileAudio } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { Content } from '../types/content';
import { contentKeys } from '../hooks/useContent';

interface BulkEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: Content[];
}

export function BulkEditModal({ isOpen, onClose, selectedContent }: BulkEditModalProps) {
  const queryClient = useQueryClient();
  const [updating, setUpdating] = useState(false);
  const [updateProgress, setUpdateProgress] = useState<{[key: number]: 'pending' | 'updating' | 'success' | 'error'}>({});

  // Bulk update mode: Apply same changes to all
  const [bulkDuration, setBulkDuration] = useState<number | ''>('');
  const [bulkIsActive, setBulkIsActive] = useState<boolean | null>(null);

  if (!isOpen) return null;

  const handleBulkUpdate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (bulkDuration === '' && bulkIsActive === null) {
      toast.error('Please set at least one field to update');
      return;
    }

    setUpdating(true);

    // Initialize progress
    const initialProgress: {[key: number]: 'pending' | 'updating' | 'success' | 'error'} = {};
    selectedContent.forEach(content => {
      initialProgress[content.id] = 'pending';
    });
    setUpdateProgress(initialProgress);

    let successCount = 0;
    let failCount = 0;

    // Update all content in parallel
    const updatePromises = selectedContent.map(async (content) => {
      try {
        setUpdateProgress(prev => ({ ...prev, [content.id]: 'updating' }));

        const updateData: any = {};
        if (bulkDuration !== '') updateData.duration = bulkDuration;
        if (bulkIsActive !== null) updateData.is_active = bulkIsActive;

        await apiClient.put(API_ENDPOINTS.CONTENT.UPDATE(content.id), updateData);

        setUpdateProgress(prev => ({ ...prev, [content.id]: 'success' }));
        successCount++;
      } catch (error) {
        setUpdateProgress(prev => ({ ...prev, [content.id]: 'error' }));
        failCount++;
        console.error(`Failed to update content ${content.id}:`, error);
      }
    });

    await Promise.all(updatePromises);

    // Invalidate queries
    queryClient.invalidateQueries({ queryKey: contentKeys.lists() });

    setUpdating(false);

    // Show result
    if (failCount === 0) {
      toast.success(`Successfully updated ${successCount} content items`);
      onClose();
    } else {
      toast.warning(`Updated ${successCount} items, ${failCount} failed`);
    }
  };

  const getContentIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <FileImage className="w-5 h-5 text-green-600" />;
      case 'video':
        return <FileVideo className="w-5 h-5 text-blue-600" />;
      case 'audio':
        return <FileAudio className="w-5 h-5 text-purple-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: 'pending' | 'updating' | 'success' | 'error') => {
    switch (status) {
      case 'pending':
        return <span className="text-xs text-gray-500">Pending</span>;
      case 'updating':
        return <span className="text-xs text-blue-600 flex items-center gap-1">
          <Loader2 className="w-3 h-3 animate-spin" /> Updating...
        </span>;
      case 'success':
        return <span className="text-xs text-green-600">✓ Success</span>;
      case 'error':
        return <span className="text-xs text-red-600">✗ Failed</span>;
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Bulk Edit Content
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Editing {selectedContent.length} content items
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={updating}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleBulkUpdate} className="space-y-6">
          {/* Bulk Update Fields */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
              📝 Apply to All Selected Items
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {/* Duration */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Duration (seconds)
                </label>
                <input
                  type="number"
                  value={bulkDuration}
                  onChange={(e) => setBulkDuration(e.target.value ? parseInt(e.target.value) : '')}
                  disabled={updating}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
                  placeholder="Leave empty to skip"
                  min={1}
                  max={86400}
                />
              </div>

              {/* Active Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Active Status
                </label>
                <select
                  value={bulkIsActive === null ? '' : bulkIsActive.toString()}
                  onChange={(e) => setBulkIsActive(e.target.value === '' ? null : e.target.value === 'true')}
                  disabled={updating}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
                >
                  <option value="">Don't change</option>
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>
            </div>
          </div>

          {/* Selected Content List */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Selected Content ({selectedContent.length})
            </h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {selectedContent.map((content) => (
                <div
                  key={content.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {getContentIcon(content.content_type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {content.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {content.original_filename}
                      </p>
                    </div>
                  </div>
                  {updating && updateProgress[content.id] && (
                    <div>{getStatusBadge(updateProgress[content.id])}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              disabled={updating}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updating || (bulkDuration === '' && bulkIsActive === null)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {updating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Updating {selectedContent.length} items...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Update All
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
