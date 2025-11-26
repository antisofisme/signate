/**
 * Unified Content Assignment Modal
 *
 * Single modal with tabs for all content assignment types:
 * - Priority 1: Direct Content (drag & drop)
 * - Priority 2: Tags
 * - Priority 3: Playlists
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Tag as TagIcon, List } from 'lucide-react';
import { Modal, Tabs, TabPanel, type Tab } from '@/shared/components';
import type { Device } from '../../types/device';

// Import existing assignment modal content (we'll extract the content parts)
import { DirectContentAssignmentTab } from './assignment-tabs/DirectContentAssignmentTab';
import { TagAssignmentTab } from './assignment-tabs/TagAssignmentTab';
import { PlaylistAssignmentTab } from './assignment-tabs/PlaylistAssignmentTab';

export type ContentAssignmentTabId = 'direct' | 'tags' | 'playlists';

interface UnifiedContentAssignmentModalProps {
  isOpen: boolean;
  device: Device | null;
  defaultTab?: ContentAssignmentTabId;
  onClose: () => void;
}

export function UnifiedContentAssignmentModal({
  isOpen,
  device,
  defaultTab = 'direct',
  onClose,
}: UnifiedContentAssignmentModalProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<ContentAssignmentTabId>(defaultTab);

  if (!device) return null;

  const ASSIGNMENT_TABS: Tab[] = [
    {
      id: 'direct',
      label: t('devices.modals.directContent'),
      icon: FileText,
    },
    {
      id: 'tags',
      label: t('devices.modals.tags'),
      icon: TagIcon,
    },
    {
      id: 'playlists',
      label: t('devices.modals.playlists'),
      icon: List,
    },
  ];

  // Custom header with tabs
  const customHeader = (
    <div className="sticky top-0 bg-white dark:bg-gray-800 z-10">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('devices.modals.manageContentAssignment')}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {device.device_name}
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs
        tabs={ASSIGNMENT_TABS}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as ContentAssignmentTabId)}
      />
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="5xl"
      customHeader={customHeader}
      className="h-[90vh] flex flex-col"
    >
      {/* Tab Panels - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        <TabPanel activeTab={activeTab} tabId="direct">
          <DirectContentAssignmentTab device={device} />
        </TabPanel>

        <TabPanel activeTab={activeTab} tabId="tags">
          <TagAssignmentTab device={device} />
        </TabPanel>

        <TabPanel activeTab={activeTab} tabId="playlists">
          <PlaylistAssignmentTab device={device} />
        </TabPanel>
      </div>
    </Modal>
  );
}
