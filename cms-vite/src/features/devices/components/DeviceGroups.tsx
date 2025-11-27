/**
 * Device Groups Component
 * Manage device groups with hierarchical structure
 */

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { Folder, Plus, Users, Edit, Trash2, MoreVertical, Grid, List, ChevronRight, ChevronDown, Settings, X, Check, Monitor } from 'lucide-react'
import { getApiErrorMessage } from '@/shared/utils/types'
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions'
import {
  CardGridSkeleton,
  EmptyState,
  ErrorDisplay,
  ConfirmDialog
} from '@/shared/components'
import { Button } from '@/components/ui/button'
import { groupsApi } from '../api/groupsApi'
import { deviceApi } from '../api/deviceApi'
import type { DeviceGroup, CreateDeviceGroupRequest, UpdateDeviceGroupRequest } from '../types/groups'
import type { Device } from '../types/device'

type ViewMode = 'grid' | 'tree'

export function DeviceGroups() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeviceModalOpen, setIsDeviceModalOpen] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<DeviceGroup | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set())
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [groupToDelete, setGroupToDelete] = useState<DeviceGroup | null>(null)

  // Check permissions using useCanPerformAction
  const { hasPermission: canCreate } = useCanPerformAction('device_groups', 'create')
  const { hasPermission: canEdit } = useCanPerformAction('device_groups', 'edit')
  const { hasPermission: canDelete } = useCanPerformAction('device_groups', 'delete')

  // Fetch all groups
  const { data: groupsData, isLoading, error, refetch } = useQuery({
    queryKey: ['device-groups'],
    queryFn: groupsApi.getGroups,
  })

  // Create group mutation
  const createGroupMutation = useMutation({
    mutationFn: groupsApi.createGroup,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
      setIsCreateModalOpen(false)
      toast.success(t('deviceGroups.toast.createSuccess'), {
        description: t('deviceGroups.toast.createSuccessDescription', { name: data.name })
      })
    },
    onError: (error: unknown) => {
      toast.error(t('deviceGroups.toast.createError'), {
        description: getApiErrorMessage(error, t('deviceGroups.toast.tryAgain'))
      })
    },
  })

  // Update group mutation
  const updateGroupMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateDeviceGroupRequest }) =>
      groupsApi.updateGroup(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
      setIsEditModalOpen(false)
      setSelectedGroup(null)
      toast.success(t('deviceGroups.toast.updateSuccess'), {
        description: t('deviceGroups.toast.updateSuccessDescription', { name: data.name })
      })
    },
    onError: (error: unknown) => {
      toast.error(t('deviceGroups.toast.updateError'), {
        description: getApiErrorMessage(error, t('deviceGroups.toast.tryAgain'))
      })
    },
  })

  // Delete group mutation
  const deleteGroupMutation = useMutation({
    mutationFn: groupsApi.deleteGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
      toast.success(t('deviceGroups.toast.deleteSuccess'))
    },
    onError: (error: unknown) => {
      toast.error(t('deviceGroups.toast.deleteError'), {
        description: getApiErrorMessage(error, t('deviceGroups.toast.tryAgain'))
      })
    },
  })

  const handleCreateGroup = (data: CreateDeviceGroupRequest) => {
    createGroupMutation.mutate(data)
  }

  const handleUpdateGroup = (data: UpdateDeviceGroupRequest) => {
    if (selectedGroup) {
      updateGroupMutation.mutate({ id: selectedGroup.id, data })
    }
  }

  const handleEditClick = (group: DeviceGroup) => {
    setSelectedGroup(group)
    setIsEditModalOpen(true)
  }

  const handleManageDevices = (group: DeviceGroup) => {
    setSelectedGroup(group)
    setIsDeviceModalOpen(true)
  }

  const handleDeleteGroup = (group: DeviceGroup) => {
    setGroupToDelete(group)
    setDeleteConfirmOpen(true)
  }

  const confirmDelete = () => {
    if (groupToDelete) {
      deleteGroupMutation.mutate(groupToDelete.id)
      setDeleteConfirmOpen(false)
      setGroupToDelete(null)
    }
  }

  const toggleNode = (groupId: number) => {
    setExpandedNodes(prev => {
      const next = new Set(prev)
      if (next.has(groupId)) {
        next.delete(groupId)
      } else {
        next.add(groupId)
      }
      return next
    })
  }

  // Build tree structure from flat list
  const buildTree = (groups: DeviceGroup[]): DeviceGroup[] => {
    const groupMap = new Map<number, DeviceGroup & { children: DeviceGroup[] }>()
    const rootGroups: (DeviceGroup & { children: DeviceGroup[] })[] = []

    // First pass: create map of all groups with empty children arrays
    groups.forEach(group => {
      groupMap.set(group.id, { ...group, children: [] })
    })

    // Second pass: build tree structure
    groups.forEach(group => {
      const node = groupMap.get(group.id)!
      if (group.parent_group_id && groupMap.has(group.parent_group_id)) {
        const parent = groupMap.get(group.parent_group_id)!
        parent.children.push(node)
      } else {
        rootGroups.push(node)
      }
    })

    return rootGroups
  }

  // Loading state
  if (isLoading) {
    return <CardGridSkeleton count={6} columns={3} />
  }

  // Error state
  if (error) {
    return (
      <ErrorDisplay
        error={error}
        onRetry={refetch}
      />
    )
  }

  const groups = groupsData?.items || []
  const treeData = buildTree(groups)

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <div className="flex justify-between items-center">
        {/* View Mode Toggle */}
        <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded transition-colors ${
              viewMode === 'grid'
                ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <Grid className="w-4 h-4" />
            <span className="text-sm font-medium">{t('deviceGroups.viewMode.grid')}</span>
          </button>
          <button
            onClick={() => setViewMode('tree')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded transition-colors ${
              viewMode === 'tree'
                ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <List className="w-4 h-4" />
            <span className="text-sm font-medium">{t('deviceGroups.viewMode.tree')}</span>
          </button>
        </div>

        {canCreate && (
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            {t('deviceGroups.createGroup')}
          </button>
        )}
      </div>

      {/* Groups Display */}
      {groups.length === 0 ? (
        <EmptyState
          icon={Folder}
          title={t('deviceGroups.noGroups')}
          description={t('deviceGroups.noGroupsDescription')}
          action={canCreate && (
            <Button onClick={() => setIsCreateModalOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              {t('deviceGroups.createFirstGroup')}
            </Button>
          )}
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map((group) => (
            <GroupCard
              key={group.id}
              group={group}
              onEdit={handleEditClick}
              onManageDevices={handleManageDevices}
              onDelete={handleDeleteGroup}
              canEdit={canEdit}
              canDelete={canDelete}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          {treeData.map((group) => (
            <TreeNode
              key={group.id}
              group={group}
              level={0}
              expandedNodes={expandedNodes}
              onToggle={toggleNode}
              onEdit={handleEditClick}
              onManageDevices={handleManageDevices}
              onDelete={handleDeleteGroup}
              canEdit={canEdit}
              canDelete={canDelete}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {isCreateModalOpen && (
        <CreateGroupModal
          onClose={() => setIsCreateModalOpen(false)}
          onCreate={handleCreateGroup}
          isLoading={createGroupMutation.isPending}
          allGroups={groups}
        />
      )}

      {/* Edit Modal */}
      {isEditModalOpen && selectedGroup && (
        <EditGroupModal
          group={selectedGroup}
          onClose={() => {
            setIsEditModalOpen(false)
            setSelectedGroup(null)
          }}
          onUpdate={handleUpdateGroup}
          isLoading={updateGroupMutation.isPending}
          allGroups={groups}
        />
      )}

      {/* Device Assignment Modal */}
      {isDeviceModalOpen && selectedGroup && (
        <DeviceAssignmentModal
          group={selectedGroup}
          onClose={() => {
            setIsDeviceModalOpen(false)
            setSelectedGroup(null)
          }}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteConfirmOpen}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteConfirmOpen(false)
            setGroupToDelete(null)
          }
        }}
        onConfirm={confirmDelete}
        title={t('deviceGroups.confirmDelete')}
        description={groupToDelete ? t('deviceGroups.confirmDeleteMessage', { name: groupToDelete.name }) : ''}
        variant="danger"
        confirmLabel={t('common.delete')}
        cancelLabel={t('common.cancel')}
        isLoading={deleteGroupMutation.isPending}
      />
    </div>
  )
}

// Group Card Component
function GroupCard({
  group,
  onEdit,
  onManageDevices,
  onDelete,
  canEdit,
  canDelete,
}: {
  group: DeviceGroup
  onEdit: (group: DeviceGroup) => void
  onManageDevices: (group: DeviceGroup) => void
  onDelete: (group: DeviceGroup) => void
  canEdit: boolean
  canDelete: boolean
}) {
  const { t } = useTranslation()
  const { data: stats } = useQuery({
    queryKey: ['device-group-stats', group.id],
    queryFn: () => groupsApi.getGroupStats(group.id),
  })

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <Folder className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{group.name}</h3>
            {group.group_type && (
              <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                {group.group_type}
              </span>
            )}
          </div>
        </div>
        <button className="text-gray-400 hover:text-gray-600">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>

      {group.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
          {group.description}
        </p>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 text-sm">
          <Users className="w-4 h-4 text-gray-400" />
          <span className="text-gray-900 dark:text-white font-medium">
            {stats?.total_devices || 0}
          </span>
          <span className="text-gray-500 dark:text-gray-400">
            {t((stats?.total_devices || 0) !== 1 ? 'deviceGroups.devicesPlural' : 'deviceGroups.devices')}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {stats && (
            <>
              <span className="text-xs text-green-600 dark:text-green-400">
                {stats.online_devices} {t('deviceGroups.online')}
              </span>
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {stats.offline_devices} {t('deviceGroups.offline')}
              </span>
            </>
          )}
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <button
          onClick={() => onManageDevices(group)}
          className="flex-1 px-3 py-2 text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
        >
          <Settings className="w-4 h-4 inline mr-1" />
          {t('deviceGroups.manageDevices')}
        </button>
        {canEdit && (
          <button
            onClick={() => onEdit(group)}
            className="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            <Edit className="w-4 h-4 inline mr-1" />
            {t('deviceGroups.edit')}
          </button>
        )}
        {canDelete && (
          <button
            onClick={() => onDelete(group)}
            className="px-3 py-2 text-sm bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
          >
            <Trash2 className="w-4 h-4 inline" />
          </button>
        )}
      </div>
    </div>
  )
}

// Tree Node Component
function TreeNode({
  group,
  level,
  expandedNodes,
  onToggle,
  onEdit,
  onManageDevices,
  onDelete,
  canEdit,
  canDelete,
}: {
  group: DeviceGroup & { children?: DeviceGroup[] }
  level: number
  expandedNodes: Set<number>
  onToggle: (id: number) => void
  onEdit: (group: DeviceGroup) => void
  onManageDevices: (group: DeviceGroup) => void
  onDelete: (group: DeviceGroup) => void
  canEdit: boolean
  canDelete: boolean
}) {
  const { t } = useTranslation()
  const hasChildren = group.children && group.children.length > 0
  const isExpanded = expandedNodes.has(group.id)
  const indentPx = level * 24

  const { data: stats } = useQuery({
    queryKey: ['device-group-stats', group.id],
    queryFn: () => groupsApi.getGroupStats(group.id),
  })

  return (
    <div>
      {/* Node Row */}
      <div
        className="flex items-center gap-2 py-2 px-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors group"
        style={{ paddingLeft: `${indentPx + 12}px` }}
      >
        {/* Expand/Collapse Button */}
        {hasChildren ? (
          <button
            onClick={() => onToggle(group.id)}
            className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        ) : (
          <div className="w-5 h-5 flex-shrink-0" />
        )}

        {/* Folder Icon */}
        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded flex items-center justify-center">
          <Folder className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        </div>

        {/* Group Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-white truncate">
              {group.name}
            </span>
            {group.group_type && (
              <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                {group.group_type}
              </span>
            )}
          </div>
          {group.description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {group.description}
            </p>
          )}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm flex-shrink-0">
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4 text-gray-400" />
            <span className="text-gray-900 dark:text-white font-medium">
              {stats?.total_devices || 0}
            </span>
          </div>
          {stats && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-green-600 dark:text-green-400">
                {stats.online_devices}
              </span>
              <span className="text-xs text-gray-400">/</span>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {stats.offline_devices}
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <button
            onClick={() => onManageDevices(group)}
            className="p-1.5 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20"
            title={t('deviceGroups.manageDevices')}
          >
            <Settings className="w-4 h-4" />
          </button>
          {canEdit && (
            <button
              onClick={() => onEdit(group)}
              className="p-1.5 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20"
              title={t('deviceGroups.editGroup')}
            >
              <Edit className="w-4 h-4" />
            </button>
          )}
          {canDelete && (
            <button
              onClick={() => onDelete(group)}
              className="p-1.5 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
              title={t('deviceGroups.deleteGroup')}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {group.children!.map((child) => (
            <TreeNode
              key={child.id}
              group={child}
              level={level + 1}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
              onEdit={onEdit}
              onManageDevices={onManageDevices}
              onDelete={onDelete}
              canEdit={canEdit}
              canDelete={canDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Edit Group Modal Component
function EditGroupModal({
  group,
  onClose,
  onUpdate,
  isLoading,
  allGroups,
}: {
  group: DeviceGroup
  onClose: () => void
  onUpdate: (data: UpdateDeviceGroupRequest) => void
  isLoading: boolean
  allGroups: DeviceGroup[]
}) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<UpdateDeviceGroupRequest>({
    name: group.name,
    description: group.description || '',
    group_type: group.group_type as 'chain' | 'hotel' | 'floor' | 'location' | 'custom' | undefined,
    parent_group_id: group.parent_group_id || undefined,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onUpdate(formData)
  }

  // ESC key handler to close modal
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isLoading, onClose])

  // Click outside to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose()
    }
  }

  // Filter out current group and its descendants from parent options
  const availableParentGroups = allGroups.filter(g => {
    // Cannot be parent of itself
    if (g.id === group.id) return false
    // Cannot be parent if it's already a child of current group
    if (g.parent_group_id === group.id) return false
    return true
  })

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">{t('deviceGroups.modal.editTitle')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.groupName')} *
            </label>
            <input
              type="text"
              required
              maxLength={200}
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder={t('deviceGroups.modal.groupNamePlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.description')}
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              rows={3}
              placeholder={t('deviceGroups.modal.descriptionPlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.groupType')}
            </label>
            <select
              value={formData.group_type}
              onChange={(e) => setFormData({ ...formData, group_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="custom">{t('deviceGroups.modal.types.custom')}</option>
              <option value="chain">{t('deviceGroups.modal.types.chain')}</option>
              <option value="hotel">{t('deviceGroups.modal.types.hotel')}</option>
              <option value="floor">{t('deviceGroups.modal.types.floor')}</option>
              <option value="location">{t('deviceGroups.modal.types.location')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.parentGroup')}
            </label>
            <select
              value={formData.parent_group_id || ''}
              onChange={(e) => setFormData({
                ...formData,
                parent_group_id: e.target.value ? parseInt(e.target.value) : undefined
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">{t('deviceGroups.modal.noneTopLevel')}</option>
              {availableParentGroups.map(g => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {t('deviceGroups.modal.hierarchicalHint')}
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              {t('deviceGroups.modal.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('deviceGroups.modal.updating') : t('deviceGroups.modal.updateGroup')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Create Group Modal Component
function CreateGroupModal({
  onClose,
  onCreate,
  isLoading,
  allGroups,
}: {
  onClose: () => void
  onCreate: (data: CreateDeviceGroupRequest) => void
  isLoading: boolean
  allGroups: DeviceGroup[]
}) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<CreateDeviceGroupRequest>({
    name: '',
    description: '',
    group_type: 'custom',
    parent_group_id: undefined,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCreate(formData)
  }

  // ESC key handler to close modal
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isLoading, onClose])

  // Click outside to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose()
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">{t('deviceGroups.modal.createTitle')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.groupName')} *
            </label>
            <input
              type="text"
              required
              maxLength={200}
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder={t('deviceGroups.modal.groupNamePlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.description')}
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              rows={3}
              placeholder={t('deviceGroups.modal.descriptionPlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.groupType')}
            </label>
            <select
              value={formData.group_type}
              onChange={(e) => setFormData({ ...formData, group_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="custom">{t('deviceGroups.modal.types.custom')}</option>
              <option value="chain">{t('deviceGroups.modal.types.chain')}</option>
              <option value="hotel">{t('deviceGroups.modal.types.hotel')}</option>
              <option value="floor">{t('deviceGroups.modal.types.floor')}</option>
              <option value="location">{t('deviceGroups.modal.types.location')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('deviceGroups.modal.parentGroup')}
            </label>
            <select
              value={formData.parent_group_id || ''}
              onChange={(e) => setFormData({
                ...formData,
                parent_group_id: e.target.value ? parseInt(e.target.value) : undefined
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">{t('deviceGroups.modal.noneTopLevel')}</option>
              {allGroups.map(g => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {t('deviceGroups.modal.hierarchicalHint')}
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              {t('deviceGroups.modal.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('deviceGroups.modal.creating') : t('deviceGroups.modal.createGroup')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Device Assignment Modal Component
function DeviceAssignmentModal({
  group,
  onClose,
}: {
  group: DeviceGroup
  onClose: () => void
}) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch all devices
  const { data: devicesData, isLoading: isLoadingDevices } = useQuery({
    queryKey: ['devices'],
    queryFn: () => deviceApi.list(),
  })

  // Fetch devices in this group
  const { data: groupDevicesData, isLoading: isLoadingGroupDevices } = useQuery({
    queryKey: ['device-group-devices', group.id],
    queryFn: () => groupsApi.getGroupDevices(group.id),
  })

  // Add device mutation
  const addDeviceMutation = useMutation({
    mutationFn: (deviceId: number) => groupsApi.addDeviceToGroup(group.id, deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-group-devices', group.id] })
      queryClient.invalidateQueries({ queryKey: ['device-group-stats', group.id] })
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
    },
  })

  // Remove device mutation
  const removeDeviceMutation = useMutation({
    mutationFn: (deviceId: number) => groupsApi.removeDeviceFromGroup(group.id, deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-group-devices', group.id] })
      queryClient.invalidateQueries({ queryKey: ['device-group-stats', group.id] })
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
    },
  })

  const devices = devicesData?.items || []
  const assignedDeviceIds = new Set(groupDevicesData?.devices || [])

  // Filter devices by search query
  const filteredDevices = devices.filter(device =>
    device.device_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    device.ip_address?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleToggleDevice = (deviceId: number) => {
    if (assignedDeviceIds.has(deviceId)) {
      removeDeviceMutation.mutate(deviceId)
    } else {
      addDeviceMutation.mutate(deviceId)
    }
  }

  const isLoading = isLoadingDevices || isLoadingGroupDevices

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{t('deviceGroups.assignment.title')}</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {t('deviceGroups.assignment.group')}: {group.name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <input
            type="text"
            placeholder={t('deviceGroups.assignment.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Device List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-gray-500">{t('deviceGroups.assignment.loadingDevices')}</div>
            </div>
          ) : filteredDevices.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              {t('deviceGroups.assignment.noDevices')}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDevices.map((device) => {
                const isAssigned = assignedDeviceIds.has(device.id)
                const isOnline = device.status === 'active'

                return (
                  <div
                    key={device.id}
                    className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                      isAssigned
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                        : 'bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                        isOnline
                          ? 'bg-green-100 dark:bg-green-900'
                          : 'bg-gray-100 dark:bg-gray-600'
                      }`}>
                        <Monitor className={`w-5 h-5 ${
                          isOnline
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-gray-400'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-white truncate">
                            {device.device_name}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            isOnline
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400'
                              : 'bg-gray-100 text-gray-600 dark:bg-gray-600 dark:text-gray-400'
                          }`}>
                            {isOnline ? t('deviceGroups.online') : t('deviceGroups.offline')}
                          </span>
                        </div>
                        {device.ip_address && (
                          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                            {device.ip_address}
                          </p>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => handleToggleDevice(device.id)}
                      disabled={addDeviceMutation.isPending || removeDeviceMutation.isPending}
                      className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
                        isAssigned
                          ? 'bg-blue-600 text-white hover:bg-blue-700'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {isAssigned ? (
                        <Check className="w-5 h-5" />
                      ) : (
                        <Plus className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {t(assignedDeviceIds.size !== 1 ? 'deviceGroups.assignment.devicesAssignedPlural' : 'deviceGroups.assignment.devicesAssigned', { count: assignedDeviceIds.size })}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('deviceGroups.assignment.done')}
          </button>
        </div>
      </div>
    </div>
  )
}
