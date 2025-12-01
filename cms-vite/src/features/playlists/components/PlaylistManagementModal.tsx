/**
 * Playlist Management Modal
 *
 * Features:
 * - Two tabs: Content | Device
 * - Each tab has two-column layout: Available (left) | Assigned (right)
 * - Click to assign/unassign items
 * - Optimistic UI updates
 *
 * Based on TagManagementModal pattern
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Image,
  Film,
  Music,
  FileText,
  Trash2,
  Loader2,
  ArrowRight,
  Monitor,
  Tv,
  List,
} from 'lucide-react';
import { Modal, Tabs, TabPanel, type Tab } from '@/shared/components';
import {
  usePlaylistContent,
  usePlaylistAssignments,
  useAddContentToPlaylist,
  useRemoveContentFromPlaylist,
  useAssignPlaylistToDevices,
  useUnassignPlaylistFromDevices,
} from '../hooks/usePlaylist';
import { useContentList } from '@/features/contents/hooks/useContent';
import { useDeviceList } from '@/features/devices/hooks/useDevices';
import type { Content } from '@/features/contents/types/content';
import type { PlaylistContent, PlaylistDevice } from '../types/playlist';

interface PlaylistManagementModalProps {
  playlistId: number;
  playlistName: string;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'content' | 'device';

// Content type icon helper
function ContentTypeIcon({ type, className }: { type: string; className?: string }) {
  switch (type) {
    case 'image':
      return <Image className={className} />;
    case 'video':
      return <Film className={className} />;
    case 'audio':
      return <Music className={className} />;
    default:
      return <FileText className={className} />;
  }
}

// Device type icon helper
function DeviceTypeIcon({ type, className }: { type: string; className?: string }) {
  switch (type?.toLowerCase()) {
    case 'tv':
      return <Tv className={className} />;
    default:
      return <Monitor className={className} />;
  }
}

export default function PlaylistManagementModal({
  playlistId,
  playlistName,
  isOpen,
  onClose,
}: PlaylistManagementModalProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabType>('content');

  // =========================================================================
  // CONTENT TAB STATE & LOGIC
  // =========================================================================

  // Local state for optimistic UI
  const [assignedContentItems, setAssignedContentItems] = useState<PlaylistContent[]>([]);

  // Fetch content in this playlist (assigned)
  const { data: playlistContentData, isLoading: isLoadingPlaylistContent } =
    usePlaylistContent(playlistId);

  // Fetch all content
  const { data: allContentData, isLoading: isLoadingAllContent } = useContentList({ limit: 1000 });

  // Content mutations
  const addContentMutation = useAddContentToPlaylist();
  const removeContentMutation = useRemoveContentFromPlaylist();

  const allContent = allContentData?.data || [];

  // Sync assigned content from query data
  useEffect(() => {
    if (!playlistContentData) return;
    const newItems = playlistContentData.items || [];
    const currentIds = assignedContentItems.map((c) => c.id).sort().join(',');
    const newIds = newItems.map((c: PlaylistContent) => c.id).sort().join(',');
    if (currentIds !== newIds) {
      setAssignedContentItems(newItems);
    }
  }, [playlistContentData]);

  // Get assigned content IDs
  const assignedContentIds = assignedContentItems.map((item) => item.content_id);

  // Derive available content (not in playlist)
  const availableContent = allContent.filter(
    (content) => !assignedContentIds.includes(content.id)
  );

  // Handle add content with optimistic UI
  const handleAddContent = async (contentId: number) => {
    const contentToAdd = allContent.find((c) => c.id === contentId);
    if (!contentToAdd) return;

    // Optimistic: Add to local state
    const tempItem: PlaylistContent = {
      id: Date.now(), // Temp ID
      content_id: contentId,
      playlist_id: playlistId,
      order_index: assignedContentItems.length,
      title: contentToAdd.title,
      file_type: contentToAdd.content_type,
    };
    setAssignedContentItems((prev) => [...prev, tempItem]);

    try {
      await addContentMutation.mutateAsync({
        id: playlistId,
        data: { content_ids: [contentId] },
      });
    } catch {
      // Rollback on error
      setAssignedContentItems((prev) => prev.filter((c) => c.content_id !== contentId));
    }
  };

  // Handle remove content with optimistic UI
  const handleRemoveContent = async (itemId: number, contentId: number) => {
    const itemToRemove = assignedContentItems.find((c) => c.id === itemId);
    if (!itemToRemove) return;

    // Optimistic: Remove from local state
    setAssignedContentItems((prev) => prev.filter((c) => c.id !== itemId));

    try {
      await removeContentMutation.mutateAsync({
        playlistId,
        itemId,
      });
    } catch {
      // Rollback on error
      setAssignedContentItems((prev) => [...prev, itemToRemove]);
    }
  };

  // =========================================================================
  // DEVICE TAB STATE & LOGIC
  // =========================================================================

  interface DeviceItem {
    id: number;
    device_id?: number;
    device_name: string;
    device_type?: string;
    status?: string;
    location?: string;
  }

  const [assignedDevices, setAssignedDevices] = useState<DeviceItem[]>([]);

  // Fetch devices assigned to this playlist
  const { data: playlistAssignmentsData, isLoading: isLoadingAssignments } =
    usePlaylistAssignments(playlistId);

  // Fetch all devices
  const { data: allDevicesResponse, isLoading: isLoadingAllDevices } = useDeviceList();

  // Device mutations
  const assignDeviceMutation = useAssignPlaylistToDevices();
  const unassignDeviceMutation = useUnassignPlaylistFromDevices();

  const allDevices: DeviceItem[] = (allDevicesResponse?.items || []).map((d: any) => ({
    id: d.id,
    device_name: d.device_name,
    device_type: d.device_type,
    status: d.status,
  }));

  // Sync assigned devices from query data
  useEffect(() => {
    if (!playlistAssignmentsData) return;
    const newItems = (playlistAssignmentsData.devices || []).map((d: PlaylistDevice) => ({
      id: d.device_id,
      device_id: d.device_id,
      device_name: d.device_name || `Device ${d.device_id}`,
      location: d.location,
    }));
    const currentIds = assignedDevices.map((d) => d.id).sort().join(',');
    const newIds = newItems.map((d: DeviceItem) => d.id).sort().join(',');
    if (currentIds !== newIds) {
      setAssignedDevices(newItems);
    }
  }, [playlistAssignmentsData]);

  // Derive available devices
  const assignedDeviceIds = assignedDevices.map((d) => d.id);
  const availableDevices = allDevices.filter((device) => !assignedDeviceIds.includes(device.id));

  // Handle assign device with optimistic UI
  const handleAssignDevice = async (deviceId: number) => {
    const deviceToAssign = allDevices.find((d) => d.id === deviceId);
    if (!deviceToAssign) return;

    setAssignedDevices((prev) => [...prev, deviceToAssign]);

    try {
      await assignDeviceMutation.mutateAsync({
        id: playlistId,
        data: { device_ids: [deviceId] },
      });
    } catch {
      setAssignedDevices((prev) => prev.filter((d) => d.id !== deviceId));
    }
  };

  // Handle unassign device with optimistic UI
  const handleUnassignDevice = async (deviceId: number) => {
    const deviceToRemove = assignedDevices.find((d) => d.id === deviceId);
    if (!deviceToRemove) return;

    setAssignedDevices((prev) => prev.filter((d) => d.id !== deviceId));

    try {
      await unassignDeviceMutation.mutateAsync({
        id: playlistId,
        data: { device_ids: [deviceId] },
      });
    } catch {
      setAssignedDevices((prev) => [...prev, deviceToRemove]);
    }
  };

  // =========================================================================
  // RENDER
  // =========================================================================

  if (!isOpen) return null;

  const isContentOperationPending =
    addContentMutation.isPending || removeContentMutation.isPending;
  const isDeviceOperationPending =
    assignDeviceMutation.isPending || unassignDeviceMutation.isPending;
  const isOperationPending = isContentOperationPending || isDeviceOperationPending;

  const isContentLoading = isLoadingPlaylistContent || isLoadingAllContent;
  const isDeviceLoading = isLoadingAssignments || isLoadingAllDevices;

  // Tab configuration
  const TABS: Tab[] = [
    {
      id: 'content',
      label: t('playlists.managementModal.tabContent', 'Content'),
      icon: FileText,
      badge: assignedContentItems.length,
    },
    {
      id: 'device',
      label: t('playlists.managementModal.tabDevice', 'Device'),
      icon: Monitor,
      badge: assignedDevices.length,
    },
  ];

  // Custom header
  const customHeader = (
    <div className="sticky top-0 bg-white dark:bg-gray-800 z-10">
      {/* Playlist Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {t('playlists.managementModal.title', 'Manage Playlist')}
        </h2>
        <div className="flex items-center gap-2 mt-1">
          <List className="w-4 h-4 text-purple-500" />
          <p className="text-sm text-gray-500 dark:text-gray-400">{playlistName}</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs tabs={TABS} activeTab={activeTab} onChange={(id) => setActiveTab(id as TabType)} />
    </div>
  );

  // Footer with close button
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end">
        <button
          onClick={onClose}
          disabled={isOperationPending}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
        >
          {t('common.close', 'Close')}
        </button>
      </div>
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
      <div className="p-6 min-h-[500px]">
        {/* Content Tab */}
        {activeTab === 'content' && (
          <>
            {isContentLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-6 h-full">
                {/* Left Column - Available Content */}
                <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    {t('playlists.managementModal.availableContent', 'Available Content')} (
                    {availableContent.length})
                  </h4>

                  {availableContent.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'playlists.managementModal.allContentAdded',
                          'All content is already in this playlist'
                        )}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[calc(85vh-320px)] overflow-y-auto pr-2">
                      {availableContent.map((content) => (
                        <div
                          key={content.id}
                          className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer bg-white dark:bg-gray-800"
                          onClick={() => handleAddContent(content.id)}
                        >
                          <div className="flex gap-3">
                            <div className="w-14 h-14 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                              {content.thumbnail_url ? (
                                <img
                                  src={content.thumbnail_url}
                                  alt={content.title}
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <ContentTypeIcon
                                    type={content.content_type}
                                    className="w-6 h-6 text-gray-400"
                                  />
                                </div>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {content.title}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {content.content_type} • {content.duration}s
                              </p>
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAddContent(content.id);
                              }}
                              disabled={isContentOperationPending}
                              className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all self-center"
                              title={t('common.add', 'Add')}
                            >
                              <ArrowRight className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Column - Content in Playlist */}
                <div className="pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <List className="w-4 h-4 text-purple-500" />
                    {t('playlists.managementModal.playlistContent', 'Playlist Content')} (
                    {assignedContentItems.length})
                  </h4>

                  {assignedContentItems.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'playlists.managementModal.noContent',
                          'No content in this playlist yet'
                        )}
                      </p>
                      <p className="text-xs mt-1">
                        {t('playlists.managementModal.clickToAdd', 'Click content on the left to add')}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[calc(85vh-320px)] overflow-y-auto pr-2">
                      {assignedContentItems.map((item, index) => {
                        const content = allContent.find((c) => c.id === item.content_id);
                        return (
                          <div
                            key={item.id}
                            className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
                          >
                            <div className="flex gap-3">
                              <div className="w-8 h-14 flex-shrink-0 flex items-center justify-center text-gray-400 font-medium text-sm">
                                #{index + 1}
                              </div>
                              <div className="w-14 h-14 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                                {content?.thumbnail_url ? (
                                  <img
                                    src={content.thumbnail_url}
                                    alt={item.title || content?.title}
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center">
                                    <ContentTypeIcon
                                      type={item.file_type || content?.content_type || 'file'}
                                      className="w-6 h-6 text-gray-400"
                                    />
                                  </div>
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                  {item.title || content?.title || `Content ${item.content_id}`}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                  {item.file_type || content?.content_type} • {item.duration || content?.duration}s
                                </p>
                              </div>
                              <button
                                onClick={() => handleRemoveContent(item.id, item.content_id)}
                                disabled={isContentOperationPending}
                                className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all self-center"
                                title={t('common.remove', 'Remove')}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {/* Device Tab */}
        {activeTab === 'device' && (
          <>
            {isDeviceLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-6 h-full">
                {/* Left Column - Available Devices */}
                <div className="border-r border-gray-200 dark:border-gray-700 pr-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <Monitor className="w-4 h-4" />
                    {t('playlists.managementModal.availableDevices', 'Available Devices')} (
                    {availableDevices.length})
                  </h4>

                  {availableDevices.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Monitor className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'playlists.managementModal.allDevicesAssigned',
                          'All devices are already assigned to this playlist'
                        )}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[calc(85vh-320px)] overflow-y-auto pr-2">
                      {availableDevices.map((device) => (
                        <div
                          key={device.id}
                          className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer bg-white dark:bg-gray-800"
                          onClick={() => handleAssignDevice(device.id)}
                        >
                          <div className="flex gap-3">
                            <div className="w-14 h-14 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                              <DeviceTypeIcon
                                type={device.device_type || 'monitor'}
                                className="w-6 h-6 text-gray-400"
                              />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {device.device_name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {device.device_type} •{' '}
                                <span
                                  className={
                                    device.status === 'online'
                                      ? 'text-green-600'
                                      : 'text-gray-400'
                                  }
                                >
                                  {device.status}
                                </span>
                              </p>
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAssignDevice(device.id);
                              }}
                              disabled={isDeviceOperationPending}
                              className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all self-center"
                              title={t('common.add', 'Add')}
                            >
                              <ArrowRight className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Column - Assigned Devices */}
                <div className="pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <List className="w-4 h-4 text-purple-500" />
                    {t('playlists.managementModal.assignedDevices', 'Assigned Devices')} (
                    {assignedDevices.length})
                  </h4>

                  {assignedDevices.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Monitor className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'playlists.managementModal.noDevices',
                          'No devices assigned to this playlist yet'
                        )}
                      </p>
                      <p className="text-xs mt-1">
                        {t(
                          'playlists.managementModal.clickToAddDevice',
                          'Click device on the left to add'
                        )}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[calc(85vh-320px)] overflow-y-auto pr-2">
                      {assignedDevices.map((device) => {
                        const fullDevice = allDevices.find((d) => d.id === device.id);
                        return (
                          <div
                            key={device.id}
                            className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
                          >
                            <div className="flex gap-3">
                              <div className="w-14 h-14 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                                <DeviceTypeIcon
                                  type={fullDevice?.device_type || 'monitor'}
                                  className="w-6 h-6 text-gray-400"
                                />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                  {device.device_name}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                  {fullDevice?.device_type || 'Device'} •{' '}
                                  <span
                                    className={
                                      fullDevice?.status === 'online'
                                        ? 'text-green-600'
                                        : 'text-gray-400'
                                    }
                                  >
                                    {fullDevice?.status || 'unknown'}
                                  </span>
                                </p>
                              </div>
                              <button
                                onClick={() => handleUnassignDevice(device.id)}
                                disabled={isDeviceOperationPending}
                                className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all self-center"
                                title={t('common.remove', 'Remove')}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}
