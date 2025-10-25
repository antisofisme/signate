import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, devicesAPI, tagsAPI } from '../services/api'
import { API_BASE_URL } from '../utils/constants'
import UploadModal from '../components/content/modals/UploadModal'
import AssignModal from '../components/content/modals/AssignModal'
import PreviewModal from '../components/content/modals/PreviewModal'
import BulkEditModal from '../components/content/modals/BulkEditModal'
import BulkTagModal from '../components/content/modals/BulkTagModal'
import ContentToolbar from '../components/content/ContentToolbar'
import GroupingControls from '../components/content/GroupingControls'
import ContentCard from '../components/content/ContentCard'
import useContentGrouping from '../hooks/useContentGrouping'
import { FileImage } from 'lucide-react'
import { showToast } from '../utils/toast'

// Helper function to get proxy image URL
const getImageUrl = (content) => {
  // Use backend proxy endpoint which serves images with correct Content-Type
  return `${API_BASE_URL}/api/content/${content.id}/image`
}

export default function Content() {
  const queryClient = useQueryClient()
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [showBulkEditForm, setShowBulkEditForm] = useState(false)
  const [showBulkTagForm, setShowBulkTagForm] = useState(false)
  const [selectedContent, setSelectedContent] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())

  // Fetch content
  const { data: contentData } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  // Fetch tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Fetch devices
  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
  })

  // Fetch all assignments to map content to tags/devices
  const { data: allAssignmentsData } = useQuery({
    queryKey: ['all-assignments'],
    queryFn: async () => {
      if (!contentData?.items) return {}

      const assignmentsMap = {}
      for (const content of contentData.items) {
        const res = await contentAPI.getAssignments(content.id)
        assignmentsMap[content.id] = res.data
      }
      return assignmentsMap
    },
    enabled: !!contentData?.items,
  })

  // Use content grouping hook
  const {
    groupBy,
    groupedContent,
    expandedGroups,
    setGroupBy,
    toggleGroup,
    expandAllGroups,
    collapseAllGroups
  } = useContentGrouping(
    contentData?.items,
    tagsData?.items,
    devicesData?.devices,
    allAssignmentsData
  )

  // Upload content mutation
  const uploadMutation = useMutation({
    mutationFn: contentAPI.upload,
    onSuccess: () => {
      queryClient.invalidateQueries(['content'])
      setShowUploadForm(false)
      showToast.success('Content uploaded successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Upload failed')
    }
  })

  // Assign content mutation
  const assignMutation = useMutation({
    mutationFn: ({ id, data }) => contentAPI.assign(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['content-assignments', variables.id])
      setShowAssignForm(false)
      showToast.success('Content assigned successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Delete content mutation
  const deleteMutation = useMutation({
    mutationFn: contentAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['content'])
      showToast.success('Content deleted successfully!')
    },
  })

  const handleAssign = (e, content) => {
    e.stopPropagation()
    setSelectedContent(content)
    setShowAssignForm(true)
  }

  const handlePreview = (content) => {
    setSelectedContent(content)
    setShowPreviewModal(true)
  }

  const toggleSelection = (contentId, e) => {
    e.stopPropagation()
    setSelectedIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(contentId)) {
        newSet.delete(contentId)
      } else {
        newSet.add(contentId)
      }
      return newSet
    })
  }

  const toggleSelectAll = () => {
    const allContent = contentData?.items || []
    if (selectedIds.size === allContent.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(allContent.map(c => c.id)))
    }
  }

  const clearSelection = () => {
    setSelectedIds(new Set())
  }

  return (
    <div>
      {/* Toolbar */}
      <ContentToolbar
        selectedIds={selectedIds}
        totalCount={contentData?.items?.length}
        onClearSelection={clearSelection}
        onToggleSelectAll={toggleSelectAll}
        onBulkEdit={() => setShowBulkEditForm(true)}
        onBulkTag={() => setShowBulkTagForm(true)}
        onUpload={() => setShowUploadForm(true)}
      />

      {/* Grouping Controls */}
      <GroupingControls
        groupBy={groupBy}
        onGroupByChange={setGroupBy}
        onExpandAll={expandAllGroups}
        onCollapseAll={collapseAllGroups}
        totalCount={contentData?.items?.length}
      />

      {/* Grouped Content */}
      {groupedContent.map((group) => (
        <div key={group.key} className="mb-6">
          {/* Group Header */}
          {groupBy !== 'none' && (
            <button
              onClick={() => toggleGroup(group.key)}
              className="w-full bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-300 rounded-lg px-4 py-3 mb-4 flex items-center justify-between hover:from-gray-100 hover:to-gray-200 transition-all"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{group.icon}</span>
                <h2 className="text-xl font-bold text-gray-800">{group.name}</h2>
                <span className="bg-white px-3 py-1 rounded-full text-sm font-medium text-gray-600 shadow-sm">
                  {group.items.length} items
                </span>
              </div>
              <div className="text-gray-600">
                {expandedGroups.has(group.key) ? '▼' : '▶'}
              </div>
            </button>
          )}

          {/* Group Content */}
          {(groupBy === 'none' || expandedGroups.has(group.key)) && (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {group.items.map((content) => (
                <ContentCard
                  key={content.id}
                  content={content}
                  isSelected={selectedIds.has(content.id)}
                  onToggleSelection={toggleSelection}
                  onPreview={handlePreview}
                  onEdit={handleAssign}
                  onDelete={(id) => deleteMutation.mutate(id)}
                />
              ))}
            </div>
          )}
        </div>
      ))}

      {contentData?.items?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <FileImage className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>No content uploaded yet</p>
        </div>
      )}

      {/* Upload Form Modal */}
      {showUploadForm && <UploadModal onClose={() => setShowUploadForm(false)} onSubmit={uploadMutation.mutate} />}

      {/* Assign Form Modal */}
      {showAssignForm && <AssignModal content={selectedContent} onClose={() => setShowAssignForm(false)} onSubmit={assignMutation.mutate} />}

      {/* Preview Modal */}
      {showPreviewModal && selectedContent && (
        <PreviewModal content={selectedContent} onClose={() => setShowPreviewModal(false)} />
      )}

      {/* Bulk Edit Modal */}
      {showBulkEditForm && (
        <BulkEditModal
          selectedIds={selectedIds}
          contentData={contentData}
          onClose={() => setShowBulkEditForm(false)}
          onComplete={() => {
            setShowBulkEditForm(false)
            clearSelection()
          }}
        />
      )}

      {/* Bulk Tag Modal */}
      {showBulkTagForm && (
        <BulkTagModal
          selectedIds={selectedIds}
          contentData={contentData}
          onClose={() => setShowBulkTagForm(false)}
          onComplete={() => {
            setShowBulkTagForm(false)
            clearSelection()
          }}
        />
      )}
    </div>
  )
}
