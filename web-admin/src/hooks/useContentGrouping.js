import { useState, useMemo } from 'react'

/**
 * useContentGrouping Hook
 * Custom hook for managing content grouping logic
 *
 * Features:
 * - Group content by: none, extension, tag, device
 * - Automatic grouping based on content metadata
 * - Expand/collapse group functionality
 * - Group management utilities
 *
 * @param {Array} contentItems - Array of content items to group
 * @param {Array} tags - Array of tag objects
 * @param {Array} devices - Array of device objects
 * @param {Object} allAssignmentsData - Map of content ID to assignments
 * @returns {Object} Grouping state and control functions
 */
export default function useContentGrouping(contentItems, tags, devices, allAssignmentsData) {
  const [groupBy, setGroupBy] = useState('none')
  const [expandedGroups, setExpandedGroups] = useState(new Set())

  // Group content based on selected grouping mode
  const groupedContent = useMemo(() => {
    if (!contentItems) return []

    if (groupBy === 'none') {
      return [{ name: 'All Content', items: contentItems, key: 'all' }]
    }

    if (groupBy === 'extension') {
      const groups = {}
      contentItems.forEach(content => {
        const mimeType = content.mime_type || 'unknown'
        const category = mimeType.startsWith('image/') ? 'Images'
                      : mimeType.startsWith('video/') ? 'Videos'
                      : 'Other'

        if (!groups[category]) {
          groups[category] = []
        }
        groups[category].push(content)
      })

      return Object.entries(groups).map(([name, items]) => ({
        name,
        items,
        key: name.toLowerCase(),
        icon: name === 'Images' ? '🖼️' : name === 'Videos' ? '🎬' : '📄'
      }))
    }

    if (groupBy === 'tag' && allAssignmentsData) {
      const groups = {}
      const untagged = []

      contentItems.forEach(content => {
        const assignments = allAssignmentsData[content.id] || []
        const contentTags = assignments.filter(a => a.tag_id).map(a => a.tag_id)

        if (contentTags.length === 0) {
          untagged.push(content)
        } else {
          contentTags.forEach(tagId => {
            const tag = tags?.find(t => t.id === tagId)
            const tagName = tag?.tag_name || `Tag #${tagId}`

            if (!groups[tagName]) {
              groups[tagName] = []
            }
            groups[tagName].push(content)
          })
        }
      })

      const result = Object.entries(groups).map(([name, items]) => ({
        name,
        items,
        key: `tag-${name}`,
        icon: '🏷️'
      }))

      if (untagged.length > 0) {
        result.push({ name: 'Untagged', items: untagged, key: 'untagged', icon: '❓' })
      }

      return result
    }

    if (groupBy === 'device' && allAssignmentsData) {
      const groups = {}
      const unassigned = []

      contentItems.forEach(content => {
        const assignments = allAssignmentsData[content.id] || []
        const contentDevices = assignments.filter(a => a.device_id).map(a => a.device_id)

        if (contentDevices.length === 0) {
          unassigned.push(content)
        } else {
          contentDevices.forEach(deviceId => {
            const device = devices?.find(d => d.id === deviceId)
            const deviceName = device?.device_name || `Device #${deviceId}`

            if (!groups[deviceName]) {
              groups[deviceName] = []
            }
            groups[deviceName].push(content)
          })
        }
      })

      const result = Object.entries(groups).map(([name, items]) => ({
        name,
        items,
        key: `device-${name}`,
        icon: '📺'
      }))

      if (unassigned.length > 0) {
        result.push({ name: 'Unassigned', items: unassigned, key: 'unassigned', icon: '❓' })
      }

      return result
    }

    return []
  }, [contentItems, groupBy, allAssignmentsData, tags, devices])

  const toggleGroup = (groupKey) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev)
      if (newSet.has(groupKey)) {
        newSet.delete(groupKey)
      } else {
        newSet.add(groupKey)
      }
      return newSet
    })
  }

  const expandAllGroups = () => {
    const allKeys = groupedContent.map(g => g.key)
    setExpandedGroups(new Set(allKeys))
  }

  const collapseAllGroups = () => {
    setExpandedGroups(new Set())
  }

  const handleGroupByChange = (newGroupBy) => {
    setGroupBy(newGroupBy)
    if (newGroupBy !== 'none') {
      expandAllGroups()
    }
  }

  return {
    groupBy,
    groupedContent,
    expandedGroups,
    setGroupBy: handleGroupByChange,
    toggleGroup,
    expandAllGroups,
    collapseAllGroups
  }
}
