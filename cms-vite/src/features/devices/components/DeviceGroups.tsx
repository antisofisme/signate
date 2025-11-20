/**
 * Device Groups Component
 * Manage device groups with hierarchical structure
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Folder, Plus, Users, Edit, Trash2, MoreVertical } from 'lucide-react'
import { groupsApi } from '../api/groupsApi'
import type { DeviceGroup, CreateDeviceGroupRequest, UpdateDeviceGroupRequest } from '../types/groups'

export function DeviceGroups() {
  const queryClient = useQueryClient()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<DeviceGroup | null>(null)

  // Fetch all groups
  const { data: groupsData, isLoading } = useQuery({
    queryKey: ['device-groups'],
    queryFn: groupsApi.getGroups,
  })

  // Create group mutation
  const createGroupMutation = useMutation({
    mutationFn: groupsApi.createGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
      setIsCreateModalOpen(false)
    },
  })

  // Update group mutation
  const updateGroupMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateDeviceGroupRequest }) =>
      groupsApi.updateGroup(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
      setIsEditModalOpen(false)
      setSelectedGroup(null)
    },
  })

  // Delete group mutation
  const deleteGroupMutation = useMutation({
    mutationFn: groupsApi.deleteGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-groups'] })
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

  const handleDeleteGroup = (groupId: number) => {
    if (confirm('Are you sure you want to delete this group?')) {
      deleteGroupMutation.mutate(groupId)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading groups...</div>
      </div>
    )
  }

  const groups = groupsData?.items || []

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <div className="flex justify-end">
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Group
        </button>
      </div>

      {/* Groups Grid */}
      {groups.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Folder className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No groups yet</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Create your first device group to organize your devices
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create First Group
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map((group) => (
            <GroupCard
              key={group.id}
              group={group}
              onEdit={handleEditClick}
              onDelete={handleDeleteGroup}
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
    </div>
  )
}

// Group Card Component
function GroupCard({
  group,
  onEdit,
  onDelete,
}: {
  group: DeviceGroup
  onEdit: (group: DeviceGroup) => void
  onDelete: (id: number) => void
}) {
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
          <span className="text-gray-500 dark:text-gray-400">devices</span>
        </div>
        <div className="flex items-center gap-2">
          {stats && (
            <>
              <span className="text-xs text-green-600 dark:text-green-400">
                {stats.online_devices} online
              </span>
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {stats.offline_devices} offline
              </span>
            </>
          )}
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <button
          onClick={() => onEdit(group)}
          className="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <Edit className="w-4 h-4 inline mr-1" />
          Edit
        </button>
        <button
          onClick={() => onDelete(group.id)}
          className="px-3 py-2 text-sm bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
        >
          <Trash2 className="w-4 h-4 inline" />
        </button>
      </div>
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
  const [formData, setFormData] = useState<UpdateDeviceGroupRequest>({
    name: group.name,
    description: group.description || '',
    group_type: group.group_type,
    parent_group_id: group.parent_group_id || undefined,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onUpdate(formData)
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Edit Device Group</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Group Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="e.g., Lobby Displays"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              rows={3}
              placeholder="Optional description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Group Type
            </label>
            <select
              value={formData.group_type}
              onChange={(e) => setFormData({ ...formData, group_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="custom">Custom</option>
              <option value="chain">Chain</option>
              <option value="hotel">Hotel</option>
              <option value="floor">Floor</option>
              <option value="location">Location</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Parent Group (Optional)
            </label>
            <select
              value={formData.parent_group_id || ''}
              onChange={(e) => setFormData({
                ...formData,
                parent_group_id: e.target.value ? parseInt(e.target.value) : undefined
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">None (Top Level)</option>
              {availableParentGroups.map(g => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Create hierarchical structure by nesting groups
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Updating...' : 'Update Group'}
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

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Create Device Group</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Group Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="e.g., Lobby Displays"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              rows={3}
              placeholder="Optional description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Group Type
            </label>
            <select
              value={formData.group_type}
              onChange={(e) => setFormData({ ...formData, group_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="custom">Custom</option>
              <option value="chain">Chain</option>
              <option value="hotel">Hotel</option>
              <option value="floor">Floor</option>
              <option value="location">Location</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Parent Group (Optional)
            </label>
            <select
              value={formData.parent_group_id || ''}
              onChange={(e) => setFormData({
                ...formData,
                parent_group_id: e.target.value ? parseInt(e.target.value) : undefined
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">None (Top Level)</option>
              {allGroups.map(g => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Create hierarchical structure by nesting groups
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating...' : 'Create Group'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
