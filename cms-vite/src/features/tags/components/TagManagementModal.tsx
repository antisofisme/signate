/**
 * Tag Management Modal
 *
 * Features:
 * - Two tabs: Content | Device
 * - Each tab has two-column layout: Available (left) | Assigned (right)
 * - Click to assign/unassign items
 * - Optimistic UI updates
 *
 * Based on UnifiedContentAssignmentModal pattern
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
} from 'lucide-react';
import { Modal, Tabs, TabPanel, type Tab } from '@/shared/components';
import {
  useAssignTagToContents,
  useUnassignTagFromContents,
  useTagDevices,
  useAssignTagToDevices,
  useUnassignTagFromDevices,
} from '../hooks/useTags';
import { useContentList } from '@/features/contents/hooks/useContent';
import { useDeviceList } from '@/features/devices/hooks/useDevices';
import type { Content } from '@/features/contents/types/content';

interface TagManagementModalProps {
  tagId: number;
  tagName: string;
  tagColor?: string;
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

export default function TagManagementModal({
  tagId,
  tagName,
  tagColor = '#3B82F6',
  isOpen,
  onClose,
}: TagManagementModalProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabType>('content');

  // =========================================================================
  // CONTENT TAB STATE & LOGIC
  // =========================================================================

  const [assignedContent, setAssignedContent] = useState<Content[]>([]);

  // Fetch content with this tag (assigned)
  const { data: assignedContentData, isLoading: isLoadingAssignedContent } = useContentList(
    { tag_ids: [tagId], limit: 1000 }
  );

  // Fetch all content
  const { data: allContentData, isLoading: isLoadingAllContent } = useContentList(
    { limit: 1000 }
  );

  // Content mutations
  const assignContentMutation = useAssignTagToContents();
  const unassignContentMutation = useUnassignTagFromContents();

  const allContent = allContentData?.data || [];

  // Sync assigned content from query data
  useEffect(() => {
    if (!assignedContentData) return;
    const newItems = assignedContentData.data || [];
    const currentIds = assignedContent.map((c) => c.id).sort().join(',');
    const newIds = newItems.map((c: Content) => c.id).sort().join(',');
    if (currentIds !== newIds) {
      setAssignedContent(newItems);
    }
  }, [assignedContentData]);

  // Derive available content
  const availableContent = allContent.filter(
    (content) => !assignedContent.some((assigned) => assigned.id === content.id)
  );

  // Handle assign content with optimistic UI
  const handleAssignContent = async (contentId: number) => {
    const contentToAssign = allContent.find((c) => c.id === contentId);
    if (!contentToAssign) return;

    setAssignedContent((prev) => [...prev, contentToAssign]);

    try {
      await assignContentMutation.mutateAsync({ tagId, contentIds: [contentId] });
    } catch {
      setAssignedContent((prev) => prev.filter((c) => c.id !== contentId));
    }
  };

  // Handle unassign content with optimistic UI
  const handleUnassignContent = async (contentId: number) => {
    const contentToRemove = assignedContent.find((c) => c.id === contentId);
    if (!contentToRemove) return;

    setAssignedContent((prev) => prev.filter((c) => c.id !== contentId));

    try {
      await unassignContentMutation.mutateAsync({ tagId, contentIds: [contentId] });
    } catch {
      setAssignedContent((prev) => [...prev, contentToRemove]);
    }
  };

  // =========================================================================
  // DEVICE TAB STATE & LOGIC
  // =========================================================================

  interface DeviceItem {
    id: number;
    device_name: string;
    device_type: string;
    status: string;
    assigned_at?: string;
  }

  const [assignedDevices, setAssignedDevices] = useState<DeviceItem[]>([]);

  // Fetch devices with this tag (assigned)
  const { data: assignedDevicesData, isLoading: isLoadingAssignedDevices } = useTagDevices(tagId);

  // Fetch all devices
  const { data: allDevicesResponse, isLoading: isLoadingAllDevices } = useDeviceList();

  // Device mutations
  const assignDeviceMutation = useAssignTagToDevices();
  const unassignDeviceMutation = useUnassignTagFromDevices();

  const allDevices: DeviceItem[] = (allDevicesResponse?.items || []).map((d: any) => ({
    id: d.id,
    device_name: d.device_name,
    device_type: d.device_type,
    status: d.status,
  }));

  // Sync assigned devices from query data
  useEffect(() => {
    if (!assignedDevicesData) return;
    const newItems = assignedDevicesData || [];
    const currentIds = assignedDevices.map((d) => d.id).sort().join(',');
    const newIds = newItems.map((d: DeviceItem) => d.id).sort().join(',');
    if (currentIds !== newIds) {
      setAssignedDevices(newItems);
    }
  }, [assignedDevicesData]);

  // Derive available devices
  const availableDevices = allDevices.filter(
    (device) => !assignedDevices.some((assigned) => assigned.id === device.id)
  );

  // Handle assign device with optimistic UI
  const handleAssignDevice = async (deviceId: number) => {
    const deviceToAssign = allDevices.find((d) => d.id === deviceId);
    if (!deviceToAssign) return;

    setAssignedDevices((prev) => [...prev, deviceToAssign]);

    try {
      await assignDeviceMutation.mutateAsync({ tagId, deviceIds: [deviceId] });
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
      await unassignDeviceMutation.mutateAsync({ tagId, deviceIds: [deviceId] });
    } catch {
      setAssignedDevices((prev) => [...prev, deviceToRemove]);
    }
  };

  // =========================================================================
  // RENDER
  // =========================================================================

  if (!isOpen) return null;

  const isContentOperationPending =
    assignContentMutation.isPending || unassignContentMutation.isPending;
  const isDeviceOperationPending =
    assignDeviceMutation.isPending || unassignDeviceMutation.isPending;
  const isOperationPending = isContentOperationPending || isDeviceOperationPending;

  const isContentLoading = isLoadingAssignedContent || isLoadingAllContent;
  const isDeviceLoading = isLoadingAssignedDevices || isLoadingAllDevices;

  // Tab configuration
  const TABS: Tab[] = [
    {
      id: 'content',
      label: t('tags.managementModal.tabContent', 'Content'),
      icon: FileText,
      badge: assignedContent.length,
    },
    {
      id: 'device',
      label: t('tags.managementModal.tabDevice', 'Device'),
      icon: Monitor,
      badge: assignedDevices.length,
    },
  ];

  // Custom header with tag color indicator
  const customHeader = (
    <div className="sticky top-0 bg-white dark:bg-gray-800 z-10">
      {/* Tag Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {t('tags.managementModal.title', 'Manage Tag Assignments')}
        </h2>
        <div className="flex items-center gap-2 mt-1">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: tagColor }}
          />
          <p className="text-sm text-gray-500 dark:text-gray-400">{tagName}</p>
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
          {t('tags.managementModal.close', 'Close')}
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
                    {t('tags.managementModal.availableContent', 'Available Content')} (
                    {availableContent.length})
                  </h4>

                  {availableContent.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'tags.managementModal.allContentAssigned',
                          'All content is already assigned to this tag'
                        )}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[calc(85vh-320px)] overflow-y-auto pr-2">
                      {availableContent.map((content) => (
                        <div
                          key={content.id}
                          className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer bg-white dark:bg-gray-800"
                          onClick={() => handleAssignContent(content.id)}
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
                                handleAssignContent(content.id);
                              }}
                              disabled={isContentOperationPending}
                              className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all self-center"
                              title={t('tags.managementModal.add', 'Add')}
                            >
                              <ArrowRight className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Column - Assigned Content */}
                <div className="pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: tagColor }}
                    />
                    {t('tags.managementModal.assignedContent', 'Assigned Content')} (
                    {assignedContent.length})
                  </h4>

                  {assignedContent.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'tags.managementModal.noAssignedContent',
                          'No content assigned to this tag yet'
                        )}
                      </p>
                      <p className="text-xs mt-1">
                        {t('tags.managementModal.clickToAdd', 'Click content on the left to add')}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[calc(85vh-320px)] overflow-y-auto pr-2">
                      {assignedContent.map((content) => (
                        <div
                          key={content.id}
                          className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
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
                              onClick={() => handleUnassignContent(content.id)}
                              disabled={isContentOperationPending}
                              className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all self-center"
                              title={t('tags.managementModal.remove', 'Remove')}
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
                    {t('tags.managementModal.availableDevices', 'Available Devices')} (
                    {availableDevices.length})
                  </h4>

                  {availableDevices.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Monitor className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'tags.managementModal.allDevicesAssigned',
                          'All devices are already assigned to this tag'
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
                                type={device.device_type}
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
                              title={t('tags.managementModal.add', 'Add')}
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
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: tagColor }}
                    />
                    {t('tags.managementModal.assignedDevices', 'Assigned Devices')} (
                    {assignedDevices.length})
                  </h4>

                  {assignedDevices.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Monitor className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">
                        {t(
                          'tags.managementModal.noAssignedDevices',
                          'No devices assigned to this tag yet'
                        )}
                      </p>
                      <p className="text-xs mt-1">
                        {t(
                          'tags.managementModal.clickToAddDevice',
                          'Click device on the left to add'
                        )}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[calc(85vh-320px)] overflow-y-auto pr-2">
                      {assignedDevices.map((device) => (
                        <div
                          key={device.id}
                          className="group relative border border-gray-200 dark:border-gray-700 rounded-lg p-3 transition-colors bg-white dark:bg-gray-800"
                        >
                          <div className="flex gap-3">
                            <div className="w-14 h-14 flex-shrink-0 rounded bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                              <DeviceTypeIcon
                                type={device.device_type}
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
                              onClick={() => handleUnassignDevice(device.id)}
                              disabled={isDeviceOperationPending}
                              className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-all self-center"
                              title={t('tags.managementModal.remove', 'Remove')}
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
          </>
        )}
      </div>
    </Modal>
  );
}
