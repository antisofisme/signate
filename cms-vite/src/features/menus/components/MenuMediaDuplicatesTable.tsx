/**
 * Menu Media Duplicates Table Component
 * Shows groups of duplicate files (same hash) with usage info
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Copy,
  Trash2,
  Loader2,
  FileImage,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  HardDrive,
  Check,
} from 'lucide-react';
import {
  EmptyState,
  ErrorDisplay,
  TableSkeleton,
  ConfirmDialog,
  Button,
} from '@/shared/components';
import { useDuplicateMenuMedia, useDeleteMenuMedia } from '../hooks/useMenuMedia';
import type { MenuMediaDuplicateGroup } from '../types/menu';

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Get file type label
const getFileTypeLabel = (mimeType: string) => {
  if (mimeType.includes('jpeg') || mimeType.includes('jpg')) return 'JPEG';
  if (mimeType.includes('png')) return 'PNG';
  if (mimeType.includes('gif')) return 'GIF';
  if (mimeType.includes('webp')) return 'WebP';
  return mimeType.split('/')[1]?.toUpperCase() || 'Image';
};

export function MenuMediaDuplicatesTable() {
  const { t } = useTranslation();
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [mediaToDelete, setMediaToDelete] = useState<{ id: number; title: string } | null>(null);

  // Queries
  const { data: duplicatesData, isLoading, error, refetch } = useDuplicateMenuMedia();
  const deleteMutation = useDeleteMenuMedia();

  // Toggle group expansion
  const toggleGroup = (hash: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(hash)) {
        newSet.delete(hash);
      } else {
        newSet.add(hash);
      }
      return newSet;
    });
  };

  // Handle delete duplicate
  const handleDelete = async () => {
    if (mediaToDelete) {
      await deleteMutation.mutateAsync(mediaToDelete.id);
      setMediaToDelete(null);
      refetch();
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <TableSkeleton columns={4} rows={5} />
      </div>
    );
  }

  // Error state
  if (error) {
    return <ErrorDisplay error={error} onRetry={refetch} />;
  }

  // No duplicates
  if (!duplicatesData || duplicatesData.duplicates.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8">
        <EmptyState
          icon={Check}
          title={t('menus.media.duplicates.emptyTitle')}
          description={t('menus.media.duplicates.emptyDescription')}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
              {t('menus.media.duplicates.groupsFound', { count: duplicatesData.total_groups })}
            </h3>
            <p className="text-sm text-yellow-700 dark:text-yellow-400 mt-1">
              {t('menus.media.duplicates.summaryMessage', { size: duplicatesData.total_wasted_readable })}
            </p>
          </div>
          <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-400">
            <HardDrive className="w-4 h-4" />
            <span className="text-sm font-medium">{duplicatesData.total_wasted_readable}</span>
          </div>
        </div>
      </div>

      {/* Duplicates List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {duplicatesData.duplicates.map((group) => (
            <DuplicateGroupRow
              key={group.file_hash}
              group={group}
              isExpanded={expandedGroups.has(group.file_hash)}
              onToggle={() => toggleGroup(group.file_hash)}
              onDelete={(id, title) => setMediaToDelete({ id, title })}
            />
          ))}
        </div>
      </div>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!mediaToDelete}
        onOpenChange={(open) => !open && setMediaToDelete(null)}
        title={t('menus.media.duplicates.deleteDialogTitle')}
        description={t('menus.media.duplicates.deleteDialogMessage', { name: mediaToDelete?.title })}
        variant="danger"
        confirmLabel={t('menus.media.actions.delete')}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

// Duplicate Group Row Component
function DuplicateGroupRow({
  group,
  isExpanded,
  onToggle,
  onDelete,
}: {
  group: MenuMediaDuplicateGroup;
  isExpanded: boolean;
  onToggle: () => void;
  onDelete: (id: number, title: string) => void;
}) {
  const { t } = useTranslation();

  return (
    <div>
      {/* Group Header */}
      <div
        className="flex items-center gap-4 px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
        onClick={onToggle}
      >
        <button className="text-gray-500">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5" />
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </button>

        <div className="flex items-center gap-2">
          <Copy className="w-4 h-4 text-yellow-500" />
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {t('menus.media.duplicates.duplicateCount', { count: group.duplicate_count })}
          </span>
        </div>

        <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
          {getFileTypeLabel(group.mime_type)}
        </span>

        <span className="text-sm text-gray-500 dark:text-gray-400">
          {t('menus.media.duplicates.sizeEach', { size: formatFileSize(group.file_size) })}
        </span>

        <span className="text-sm text-yellow-600 dark:text-yellow-400 font-medium">
          {t('menus.media.duplicates.wastedStorage', { size: formatFileSize(group.wasted_storage) })}
        </span>

        <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
          {group.file_hash}
        </span>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="bg-gray-50 dark:bg-gray-900 px-4 pb-4">
          <div className="pl-9 space-y-2">
            {group.media.map((media, index) => (
              <div
                key={media.id}
                className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center gap-3">
                  <FileImage className="w-4 h-4 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {media.title}
                      {index === 0 && (
                        <span className="ml-2 px-1.5 py-0.5 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded">
                          {t('menus.media.duplicates.original')}
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {media.original_filename}
                    </p>
                    {media.usage.used_count > 0 && (
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                        {t('menus.media.duplicates.usedInItems', { count: media.usage.used_count })}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Show delete only for duplicates (not the first/original) */}
                  {index > 0 && media.usage.used_count === 0 && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(media.id, media.title);
                      }}
                      leftIcon={<Trash2 className="w-3 h-3" />}
                    >
                      {t('menus.media.actions.delete')}
                    </Button>
                  )}
                  {media.usage.used_count > 0 && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {t('menus.media.duplicates.inUseCannotDelete')}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
