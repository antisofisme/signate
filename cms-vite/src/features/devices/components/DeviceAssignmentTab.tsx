/**
 * Device Assignment Tab Component
 *
 * Comprehensive tabbed interface for managing all device assignments:
 * - Playlists tab (list + assign/unassign)
 * - Content tab (list + assign/unassign + expiry)
 * - Tags tab (list + assign/unassign)
 * - Assignment history tab
 *
 * Integrates with Device Detail Modal
 */

import React, { useState } from 'react';
import { List, FileText, Tag as TagIcon, History, Plus, Trash2, Loader2 } from 'lucide-react';
import {
  useDevicePlaylists,
  useDeviceContents,
  useDeviceTags,
  useUnassignPlaylist,
  useUnassignContent,
  useUnassignTag,
} from '../hooks/useDeviceAssignments';
import { AssignmentHistory } from './AssignmentHistory';
import { AssignContentWithExpiry } from './AssignContentWithExpiry';

interface DeviceAssignmentTabProps {
  deviceId: number;
  deviceName?: string;
  organizationId: number;
}

type TabType = 'playlists' | 'content' | 'tags' | 'history';

export const DeviceAssignmentTab: React.FC<DeviceAssignmentTabProps> = ({
  deviceId,
  deviceName,
  organizationId,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('playlists');

  // Fetch all assignment data
  const {
    data: playlistsData,
    isLoading: loadingPlaylists,
  } = useDevicePlaylists(deviceId);

  const {
    data: contentsData,
    isLoading: loadingContents,
  } = useDeviceContents(deviceId);

  const {
    data: tagsData,
    isLoading: loadingTags,
  } = useDeviceTags(deviceId);

  // Mutations
  const unassignPlaylist = useUnassignPlaylist();
  const unassignContent = useUnassignContent();
  const unassignTag = useUnassignTag();

  // Tab configuration
  const tabs = [
    {
      id: 'playlists' as TabType,
      label: 'Playlists',
      icon: List,
      count: playlistsData?.total || 0,
    },
    {
      id: 'content' as TabType,
      label: 'Content',
      icon: FileText,
      count: contentsData?.total || 0,
    },
    {
      id: 'tags' as TabType,
      label: 'Tags',
      icon: TagIcon,
      count: tagsData?.total || 0,
    },
    {
      id: 'history' as TabType,
      label: 'History',
      icon: History,
      count: 0,
    },
  ];

  // Handle unassign playlist
  const handleUnassignPlaylist = async (playlistId: number) => {
    await unassignPlaylist.mutateAsync({ deviceId, playlistId });
  };

  // Handle unassign content
  const handleUnassignContent = async (contentId: number) => {
    await unassignContent.mutateAsync({ deviceId, contentId });
  };

  // Handle unassign tag
  const handleUnassignTag = async (tagId: number) => {
    await unassignTag.mutateAsync({ deviceId, tagId });
  };

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="border-b">
        <nav className="flex space-x-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
                {tab.count > 0 && (
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="py-4">
        {/* Playlists Tab */}
        {activeTab === 'playlists' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Assigned Playlists</h3>
              <div className="text-sm text-gray-500">
                {playlistsData?.total || 0} playlist{playlistsData?.total !== 1 ? 's' : ''}
              </div>
            </div>

            {loadingPlaylists ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-500">Loading playlists...</span>
              </div>
            ) : !playlistsData?.items || playlistsData.items.length === 0 ? (
              <div className="text-center py-12 border rounded-lg bg-gray-50">
                <List className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No playlists assigned</p>
                <p className="text-sm text-gray-500 mt-1">
                  Assign playlists to display content on this device
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {playlistsData.items.map((playlist) => (
                  <div
                    key={playlist.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{playlist.playlist_name}</h4>
                        <span
                          className={`px-2 py-0.5 text-xs rounded-full ${
                            playlist.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {playlist.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      {playlist.playlist_description && (
                        <p className="text-sm text-gray-500 mt-1">
                          {playlist.playlist_description}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleUnassignPlaylist(playlist.playlist_id)}
                      disabled={unassignPlaylist.isPending}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Unassign playlist"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Content Tab */}
        {activeTab === 'content' && (
          <AssignContentWithExpiry
            deviceId={deviceId}
            deviceName={deviceName}
          />
        )}

        {/* Tags Tab */}
        {activeTab === 'tags' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Assigned Tags</h3>
              <div className="text-sm text-gray-500">
                {tagsData?.total || 0} tag{tagsData?.total !== 1 ? 's' : ''}
              </div>
            </div>

            {loadingTags ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-500">Loading tags...</span>
              </div>
            ) : !tagsData?.items || tagsData.items.length === 0 ? (
              <div className="text-center py-12 border rounded-lg bg-gray-50">
                <TagIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No tags assigned</p>
                <p className="text-sm text-gray-500 mt-1">
                  Tags help organize and categorize devices
                </p>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tagsData.items.map((tag) => (
                  <div
                    key={tag.id}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg border hover:bg-gray-50 transition-colors"
                    style={{
                      backgroundColor: tag.tag_color ? `${tag.tag_color}15` : undefined,
                      borderColor: tag.tag_color || '#d1d5db',
                    }}
                  >
                    <TagIcon
                      className="w-4 h-4"
                      style={{ color: tag.tag_color || '#6b7280' }}
                    />
                    <span className="font-medium">{tag.tag_name}</span>
                    <button
                      onClick={() => handleUnassignTag(tag.tag_id)}
                      disabled={unassignTag.isPending}
                      className="ml-1 p-1 text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                      title="Remove tag"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <AssignmentHistory deviceId={deviceId} deviceName={deviceName} />
        )}
      </div>

      {/* Assignment Statistics Summary */}
      <div className="border-t pt-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {playlistsData?.total || 0}
            </div>
            <div className="text-sm text-blue-700">Playlists</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {contentsData?.total || 0}
            </div>
            <div className="text-sm text-green-700">Content Items</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {tagsData?.total || 0}
            </div>
            <div className="text-sm text-purple-700">Tags</div>
          </div>
        </div>
      </div>
    </div>
  );
};
