/**
 * Content Tab - Device Management Modal
 *
 * Unified content assignment management:
 * - Priority 1: Direct content assignment (drag & drop)
 * - Priority 2: Tag-based content
 * - Priority 3: Playlist assignment
 *
 * All in one view to show content priority cascade
 * Updated: Single manage button opens modal with tabs
 */

import { useState } from 'react';
import { FileText, Tag as TagIcon, List, ChevronDown, ChevronUp } from 'lucide-react';
import type { Device } from '../../../types/device';
import {
  useDeviceContents,
  useDeviceTags,
  useDevicePlaylists,
} from '../../../hooks/useDevices';
import { UnifiedContentAssignmentModal, type ContentAssignmentTabId } from '../UnifiedContentAssignmentModal';

interface ContentTabProps {
  device: Device;
}

export function ContentTab({ device }: ContentTabProps) {
  const [expandedSections, setExpandedSections] = useState({
    priority1: true,
    priority2: true,
    priority3: true,
  });

  // Unified content assignment modal state
  const [assignmentModal, setAssignmentModal] = useState<{
    isOpen: boolean;
    defaultTab: ContentAssignmentTabId;
  }>({ isOpen: false, defaultTab: 'direct' });

  // Fetch all assignments
  const { data: contentsData } = useDeviceContents(device.id, true);
  const { data: tagsData } = useDeviceTags(device.id, true);
  const { data: playlistsData } = useDevicePlaylists(device.id, true);

  const assignedContents = contentsData?.items || [];
  const assignedTags = tagsData?.items || [];
  const assignedPlaylists = playlistsData?.items || [];

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="p-6 space-y-4">
      {/* Priority Flow Diagram */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
          Content Priority Flow
        </h4>
        <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
          <span className="font-medium">Priority 1 (Direct)</span>
          <span>→</span>
          <span className="font-medium">Priority 2 (Tags)</span>
          <span>→</span>
          <span className="font-medium">Priority 3 (Playlists)</span>
        </div>
        <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
          Content is selected from left to right. If Priority 1 has content, it plays. Otherwise,
          Priority 2. If no Priority 2, then Priority 3.
        </p>
      </div>

      {/* Priority 1: Direct Content */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          onClick={() => toggleSection('priority1')}
          className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors rounded-t-lg"
        >
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-red-600 dark:text-red-400" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                Priority 1: Direct Content Assignment
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Highest priority - {assignedContents.length} content assigned
              </p>
            </div>
          </div>
          {expandedSections.priority1 ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {expandedSections.priority1 && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            {assignedContents.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No direct content assigned. Click "Manage" to assign content.
              </p>
            ) : (
              <div className="space-y-2 mb-3">
                {assignedContents.slice(0, 3).map((content) => (
                  <div
                    key={content.id}
                    className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700 rounded"
                  >
                    <FileText className="w-4 h-4 text-gray-400" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {content.content_name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Priority: {content.priority}
                      </p>
                    </div>
                  </div>
                ))}
                {assignedContents.length > 3 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    +{assignedContents.length - 3} more
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Priority 2: Tags */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          onClick={() => toggleSection('priority2')}
          className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors rounded-t-lg"
        >
          <div className="flex items-center gap-3">
            <TagIcon className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                Priority 2: Tag-based Content
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Medium priority - {assignedTags.length} tags assigned
              </p>
            </div>
          </div>
          {expandedSections.priority2 ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {expandedSections.priority2 && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            {assignedTags.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No tags assigned. Click "Manage" to assign tags.
              </p>
            ) : (
              <div className="space-y-2 mb-3">
                {assignedTags.slice(0, 3).map((tag) => (
                  <div
                    key={tag.id}
                    className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700 rounded"
                  >
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: tag.tag_color }}
                    />
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {tag.tag_name}
                    </p>
                  </div>
                ))}
                {assignedTags.length > 3 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    +{assignedTags.length - 3} more
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Priority 3: Playlists */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          onClick={() => toggleSection('priority3')}
          className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors rounded-t-lg"
        >
          <div className="flex items-center gap-3">
            <List className="w-5 h-5 text-green-600 dark:text-green-400" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                Priority 3: Playlist Assignment
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Lowest priority (fallback) - {assignedPlaylists.length} playlists assigned
              </p>
            </div>
          </div>
          {expandedSections.priority3 ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {expandedSections.priority3 && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            {assignedPlaylists.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No playlists assigned. Click "Manage" to assign playlists.
              </p>
            ) : (
              <div className="space-y-2 mb-3">
                {assignedPlaylists.slice(0, 3).map((playlist) => (
                  <div
                    key={playlist.id}
                    className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700 rounded"
                  >
                    <List className="w-4 h-4 text-gray-400" />
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {playlist.playlist_name}
                    </p>
                  </div>
                ))}
                {assignedPlaylists.length > 3 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    +{assignedPlaylists.length - 3} more
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Unified Manage Content Button */}
      <div className="mt-6">
        <button
          onClick={() => setAssignmentModal({ isOpen: true, defaultTab: 'direct' })}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-base shadow-sm hover:shadow-md flex items-center justify-center gap-2"
        >
          <FileText className="w-5 h-5" />
          Manage Content Assignment
        </button>
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-2">
          Manage all content types (Direct, Tags, Playlists) in one modal with tabs
        </p>
      </div>

      {/* Currently Playing Info */}
      <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
          Currently Playing
        </h4>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {assignedContents.length > 0
            ? `Playing from Priority 1 (${assignedContents.length} direct content)`
            : assignedTags.length > 0
            ? `Playing from Priority 2 (${assignedTags.length} tags)`
            : assignedPlaylists.length > 0
            ? `Playing from Priority 3 (${assignedPlaylists.length} playlists)`
            : 'No content assigned - device will show default screen'}
        </p>
      </div>

      {/* Unified Assignment Modal */}
      <UnifiedContentAssignmentModal
        isOpen={assignmentModal.isOpen}
        device={device}
        defaultTab={assignmentModal.defaultTab}
        onClose={() => setAssignmentModal({ isOpen: false, defaultTab: 'direct' })}
      />
    </div>
  );
}
