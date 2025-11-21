/**
 * Assignment History Component
 *
 * Features:
 * - Timeline view of assignments
 * - Filter by type (playlist/content/tag)
 * - Show assigned_at timestamps
 * - Pagination for large histories
 * - Export to CSV option
 */

import React, { useState, useMemo } from 'react';
import { formatDistanceToNow, format } from 'date-fns';
import { Download, Filter, Calendar, Tag, FileText, List } from 'lucide-react';
import {
  useDevicePlaylists,
  useDeviceContents,
  useDeviceTags,
} from '../hooks/useDeviceAssignments';
import type { AssignmentType } from '../types/assignment';
import { usePagination } from '@/shared/hooks';
import { PaginationCompact } from '@/shared/components';

interface AssignmentHistoryProps {
  deviceId: number;
  deviceName?: string;
}

interface HistoryItem {
  id: string;
  type: AssignmentType;
  name: string;
  assigned_at: string;
  assigned_by?: string;
  metadata?: Record<string, any>;
}

export const AssignmentHistory: React.FC<AssignmentHistoryProps> = ({
  deviceId,
  deviceName,
}) => {
  const [typeFilter, setTypeFilter] = useState<AssignmentType | 'all'>('all');

  // Standardized pagination hook (client-side pagination)
  const pagination = usePagination({ pageSize: 10 });

  // Fetch all assignments
  const { data: playlistsData, isLoading: loadingPlaylists } = useDevicePlaylists(deviceId);
  const { data: contentsData, isLoading: loadingContents } = useDeviceContents(deviceId);
  const { data: tagsData, isLoading: loadingTags } = useDeviceTags(deviceId);

  const isLoading = loadingPlaylists || loadingContents || loadingTags;

  // Combine all assignments into unified history
  const allHistory = useMemo<HistoryItem[]>(() => {
    const items: HistoryItem[] = [];

    // Playlists
    if (playlistsData?.items) {
      playlistsData.items.forEach((pl) => {
        items.push({
          id: `playlist-${pl.id}`,
          type: 'playlist',
          name: pl.playlist_name,
          assigned_at: pl.assigned_at,
          assigned_by: pl.assigned_by_name,
          metadata: {
            description: pl.playlist_description,
            is_active: pl.is_active,
          },
        });
      });
    }

    // Contents
    if (contentsData?.items) {
      contentsData.items.forEach((ct) => {
        items.push({
          id: `content-${ct.id}`,
          type: 'content',
          name: ct.content_name,
          assigned_at: ct.assigned_at,
          assigned_by: ct.assigned_by_name,
          metadata: {
            type: ct.content_type,
            priority: ct.priority,
            expires_at: ct.expires_at,
          },
        });
      });
    }

    // Tags
    if (tagsData?.items) {
      tagsData.items.forEach((tg) => {
        items.push({
          id: `tag-${tg.id}`,
          type: 'tag',
          name: tg.tag_name,
          assigned_at: tg.assigned_at,
          assigned_by: tg.assigned_by_name,
          metadata: {
            color: tg.tag_color,
          },
        });
      });
    }

    // Sort by assigned_at (newest first)
    return items.sort((a, b) => {
      return new Date(b.assigned_at).getTime() - new Date(a.assigned_at).getTime();
    });
  }, [playlistsData, contentsData, tagsData]);

  // Filter by type
  const filteredHistory = useMemo(() => {
    if (typeFilter === 'all') return allHistory;
    return allHistory.filter((item) => item.type === typeFilter);
  }, [allHistory, typeFilter]);

  // Paginate using standardized hook
  const totalPages = pagination.getTotalPages(filteredHistory.length);
  const paginatedHistory = useMemo(() => {
    return filteredHistory.slice(pagination.skip, pagination.skip + pagination.pageSize);
  }, [filteredHistory, pagination.skip, pagination.pageSize]);

  // Export to CSV
  const handleExportCSV = () => {
    const headers = ['Type', 'Name', 'Assigned At', 'Assigned By', 'Metadata'];
    const rows = filteredHistory.map((item) => [
      item.type,
      item.name,
      format(new Date(item.assigned_at), 'yyyy-MM-dd HH:mm:ss'),
      item.assigned_by || 'N/A',
      JSON.stringify(item.metadata || {}),
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers, ...rows].map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');

    const link = document.createElement('a');
    link.href = encodeURI(csvContent);
    link.download = `assignment-history-${deviceName || deviceId}-${format(new Date(), 'yyyyMMdd')}.csv`;
    link.click();
  };

  // Get icon for type
  const getTypeIcon = (type: AssignmentType) => {
    switch (type) {
      case 'playlist':
        return <List className="w-4 h-4" />;
      case 'content':
        return <FileText className="w-4 h-4" />;
      case 'tag':
        return <Tag className="w-4 h-4" />;
    }
  };

  // Get color for type
  const getTypeColor = (type: AssignmentType) => {
    switch (type) {
      case 'playlist':
        return 'text-blue-600 bg-blue-100';
      case 'content':
        return 'text-green-600 bg-green-100';
      case 'tag':
        return 'text-purple-600 bg-purple-100';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Assignment History</h3>
          <p className="text-sm text-gray-500">
            {filteredHistory.length} total assignments
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          disabled={filteredHistory.length === 0}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-white border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-500" />
        <span className="text-sm text-gray-600">Filter by type:</span>
        <div className="flex gap-2">
          <button
            onClick={() => setTypeFilter('all')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              typeFilter === 'all'
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({allHistory.length})
          </button>
          <button
            onClick={() => setTypeFilter('playlist')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              typeFilter === 'playlist'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Playlists ({allHistory.filter((i) => i.type === 'playlist').length})
          </button>
          <button
            onClick={() => setTypeFilter('content')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              typeFilter === 'content'
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Content ({allHistory.filter((i) => i.type === 'content').length})
          </button>
          <button
            onClick={() => setTypeFilter('tag')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              typeFilter === 'tag'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Tags ({allHistory.filter((i) => i.type === 'tag').length})
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div className="border rounded-lg">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading history...</div>
        ) : paginatedHistory.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No assignments found</div>
        ) : (
          <div className="divide-y">
            {paginatedHistory.map((item) => (
              <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-3">
                  {/* Type icon */}
                  <div
                    className={`p-2 rounded-lg ${getTypeColor(item.type)} flex-shrink-0`}
                  >
                    {getTypeIcon(item.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{item.name}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-500 capitalize">
                            {item.type}
                          </span>
                          {item.assigned_by && (
                            <>
                              <span className="text-gray-300">•</span>
                              <span className="text-xs text-gray-500">
                                by {item.assigned_by}
                              </span>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Calendar className="w-3 h-3" />
                        <span title={format(new Date(item.assigned_at), 'PPpp')}>
                          {formatDistanceToNow(new Date(item.assigned_at), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                    </div>

                    {/* Metadata */}
                    {item.metadata && Object.keys(item.metadata).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {item.type === 'content' && item.metadata.priority && (
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                            Priority: {item.metadata.priority}
                          </span>
                        )}
                        {item.type === 'content' && item.metadata.expires_at && (
                          <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-600 rounded">
                            Expires: {format(new Date(item.metadata.expires_at), 'PP')}
                          </span>
                        )}
                        {item.type === 'playlist' && item.metadata.is_active !== undefined && (
                          <span
                            className={`text-xs px-2 py-0.5 rounded ${
                              item.metadata.is_active
                                ? 'bg-green-100 text-green-600'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {item.metadata.is_active ? 'Active' : 'Inactive'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination - Using standardized component */}
      {totalPages > 1 && (
        <PaginationCompact
          currentPage={pagination.currentPage}
          totalPages={totalPages}
          totalItems={filteredHistory.length}
          pageSize={pagination.pageSize}
          onPageChange={pagination.goToPage}
        />
      )}
    </div>
  );
};
