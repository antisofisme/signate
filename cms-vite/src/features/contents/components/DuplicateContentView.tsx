/**
 * Duplicate Content View Component
 *
 * LAYER 1: PRESENTATION
 * Displays duplicate content groups (files with same hash) with usage info
 * Helps users identify and clean up duplicate uploads
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ChevronDown,
  ChevronRight,
  FileImage,
  FileVideo,
  FileAudio,
  Copy,
  List,
  Tag,
  Monitor,
  AlertCircle,
  CheckCircle,
  RefreshCw,
} from 'lucide-react';
import {
  TableSkeleton,
  EmptyState,
  ErrorDisplay,
  Button,
} from '@/shared/components';
import { useDuplicateContent } from '../hooks/useContent';
import type { DuplicateGroup, DuplicateContentItem, ContentType } from '../types/content';
import { formatFileSize } from '../api/contentApi';

// Get content type icon
function getContentTypeIcon(type: ContentType) {
  switch (type) {
    case 'image':
      return <FileImage className="w-4 h-4" />;
    case 'video':
      return <FileVideo className="w-4 h-4" />;
    case 'audio':
      return <FileAudio className="w-4 h-4" />;
  }
}

// Check if content has any usage
function hasUsage(item: DuplicateContentItem): boolean {
  return (
    item.usage.playlists.length > 0 ||
    item.usage.tags.length > 0 ||
    item.usage.devices.length > 0
  );
}

// Expandable group row
function DuplicateGroupRow({ group }: { group: DuplicateGroup }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const unusedCount = group.contents.filter((c) => !hasUsage(c)).length;

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden mb-3">
      {/* Group Header */}
      <div
        className="flex items-center gap-3 px-4 py-3 bg-gray-50 dark:bg-gray-800 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Expand/Collapse Icon */}
        <button className="text-gray-500">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5" />
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </button>

        {/* Thumbnail */}
        {group.thumbnail_url ? (
          <img
            src={group.thumbnail_url}
            alt="Thumbnail"
            className="w-12 h-12 rounded object-cover flex-shrink-0"
          />
        ) : (
          <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center flex-shrink-0">
            {getContentTypeIcon(group.content_type)}
          </div>
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Copy className="w-4 h-4 text-orange-500" />
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {group.duplicate_count} Duplicate Files
            </span>
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-4">
            <span className="flex items-center gap-1 capitalize">
              {getContentTypeIcon(group.content_type)}
              {group.content_type}
            </span>
            <span>{formatFileSize(group.file_size)}</span>
            <span className="font-mono text-xs truncate max-w-48" title={group.file_hash}>
              Hash: {group.file_hash.slice(0, 12)}...
            </span>
          </div>
        </div>

        {/* Unused Count Badge */}
        {unusedCount > 0 && (
          <div className="flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded text-sm">
            <CheckCircle className="w-4 h-4" />
            {unusedCount} safe to delete
          </div>
        )}
      </div>

      {/* Expanded Content List */}
      {isExpanded && (
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {group.contents.map((item) => (
            <DuplicateContentRow key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

// Individual content row within a group
function DuplicateContentRow({ item }: { item: DuplicateContentItem }) {
  const itemHasUsage = hasUsage(item);

  return (
    <div className="px-4 py-3 pl-14 bg-white dark:bg-gray-900">
      <div className="flex items-start justify-between gap-4">
        {/* Content Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className={`text-sm font-medium truncate ${
                item.is_active
                  ? 'text-gray-900 dark:text-gray-100'
                  : 'text-gray-500 dark:text-gray-400 line-through'
              }`}
              title={item.title}
            >
              {item.title}
            </span>
            {!item.is_active && (
              <span className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded">
                Inactive
              </span>
            )}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            ID: {item.id} | Uploaded: {new Date(item.created_at).toLocaleDateString()}
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500 truncate" title={item.original_filename}>
            {item.original_filename}
          </div>
        </div>

        {/* Usage Info */}
        <div className="flex-shrink-0 text-right">
          {itemHasUsage ? (
            <div className="space-y-1">
              {item.usage.playlists.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
                  <List className="w-3 h-3" />
                  <span>{item.usage.playlists.length} playlist(s)</span>
                </div>
              )}
              {item.usage.tags.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400">
                  <Tag className="w-3 h-3" />
                  <span>{item.usage.tags.length} tag(s)</span>
                </div>
              )}
              {item.usage.devices.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                  <Monitor className="w-3 h-3" />
                  <span>{item.usage.devices.length} device(s)</span>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
              <AlertCircle className="w-3 h-3" />
              <span>Not used anywhere</span>
            </div>
          )}
        </div>

        {/* Status Indicator */}
        <div className="flex-shrink-0">
          {itemHasUsage ? (
            <div className="w-3 h-3 rounded-full bg-yellow-400" title="In use - cannot delete safely" />
          ) : (
            <div className="w-3 h-3 rounded-full bg-green-400" title="Safe to delete" />
          )}
        </div>
      </div>

      {/* Detailed Usage (expanded) */}
      {itemHasUsage && (
        <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-800">
          {item.usage.playlists.length > 0 && (
            <div className="mb-1">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Playlists: </span>
              <span className="text-xs text-gray-600 dark:text-gray-300">
                {item.usage.playlists.map((p) => p.name).join(', ')}
              </span>
            </div>
          )}
          {item.usage.tags.length > 0 && (
            <div className="mb-1 flex items-center gap-1 flex-wrap">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Tags: </span>
              {item.usage.tags.map((tag) => (
                <span
                  key={tag.id}
                  className="text-xs px-1.5 py-0.5 rounded"
                  style={{
                    backgroundColor: `${tag.color}20`,
                    color: tag.color,
                  }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}
          {item.usage.devices.length > 0 && (
            <div>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Devices: </span>
              <span className="text-xs text-gray-600 dark:text-gray-300">
                {item.usage.devices.map((d) => `${d.name} (${d.via})`).join(', ')}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function DuplicateContentView() {
  const { t } = useTranslation();
  const { data: duplicateData, isLoading, error, refetch } = useDuplicateContent();

  // Note: apiClient interceptor unwraps the response, so duplicateData is already the array
  const groups = Array.isArray(duplicateData) ? duplicateData : (duplicateData as any)?.data || [];

  // Calculate stats
  const totalGroups = groups.length;
  const totalDuplicates = groups.reduce(
    (acc: number, group: DuplicateGroup) => acc + group.duplicate_count,
    0
  );
  const totalUnused = groups.reduce(
    (acc: number, group: DuplicateGroup) => acc + group.contents.filter((c) => !hasUsage(c)).length,
    0
  );

  return (
    <div className="space-y-4">
      {/* Header with Stats & Refresh */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {totalGroups > 0 ? (
            <span>
              Found <strong>{totalGroups}</strong> duplicate groups with{' '}
              <strong>{totalDuplicates}</strong> total files.{' '}
              {totalUnused > 0 && (
                <span className="text-green-600 dark:text-green-400">
                  {totalUnused} items safe to delete.
                </span>
              )}
            </span>
          ) : (
            'No duplicate content found'
          )}
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700 dark:text-blue-300">
            <p className="font-medium mb-1">About Duplicate Detection</p>
            <p className="text-blue-600 dark:text-blue-400">
              Files with identical content (same hash) are grouped together. The system already
              optimizes storage by sharing the physical file, but you may want to clean up duplicate
              database entries. Items marked "safe to delete" are not used in any playlist, tag, or
              device assignment.
            </p>
          </div>
        </div>
      </div>

      {/* Empty State */}
      {!isLoading && !error && totalGroups === 0 && (
        <EmptyState
          icon={Copy}
          title={t('contents.duplicates.empty.title', 'No Duplicates Found')}
          description={t(
            'contents.duplicates.empty.description',
            'All your content files are unique. Great job keeping your library organized!'
          )}
        />
      )}

      {/* Error State */}
      {error && (
        <ErrorDisplay
          error={error}
          onRetry={() => refetch()}
        />
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <TableSkeleton columns={4} rows={5} />
        </div>
      )}

      {/* Duplicate Groups */}
      {!isLoading && !error && groups.length > 0 && (
        <div className="space-y-0">
          {groups.map((group: DuplicateGroup) => (
            <DuplicateGroupRow key={group.file_hash} group={group} />
          ))}
        </div>
      )}

      {/* Legend */}
      {!isLoading && totalGroups > 0 && (
        <div className="flex items-center gap-6 text-xs text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-400" />
            <span>Safe to delete (not used)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-400" />
            <span>In use (check before deleting)</span>
          </div>
        </div>
      )}
    </div>
  );
}
