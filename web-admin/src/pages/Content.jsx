import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, devicesAPI, tagsAPI } from '../services/api'
import { API_BASE_URL } from '../utils/constants'
import UploadModal from '../components/content/modals/UploadModal'
import EditContentModal from '../components/content/modals/EditContentModal'
import PreviewModal from '../components/content/modals/PreviewModal'
import BulkEditModal from '../components/content/modals/BulkEditModal'
import BulkTagModal from '../components/content/modals/BulkTagModal'
import ContentCard from '../components/content/ContentCard'
import { FileImage, Upload, CheckSquare, Square, Edit, Tag as TagIcon, Search } from 'lucide-react'
import { showToast } from '../utils/toast'
import { Button, PageHeader, FormInput, LoadingSkeleton } from '../components/shared'

// Helper function to get proxy image URL
const getImageUrl = (content) => {
  // Use backend proxy endpoint which serves images with correct Content-Type
  return `${API_BASE_URL}/api/content/${content.id}/image`
}

export default function Content() {
  const queryClient = useQueryClient()
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [showBulkEditForm, setShowBulkEditForm] = useState(false)
  const [showBulkTagForm, setShowBulkTagForm] = useState(false)
  const [selectedContent, setSelectedContent] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')
  const [sortBy, setSortBy] = useState('newest')

  // Fetch content
  const { data: contentData, isLoading } = useQuery({
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

  // Filter and sort content
  const filteredContent = useMemo(() => {
    if (!contentData?.items) return []

    let filtered = contentData.items

    // Apply stat filter
    if (activeFilter === 'images') {
      filtered = filtered.filter(c => c.content_type === 'image')
    } else if (activeFilter === 'videos') {
      filtered = filtered.filter(c => c.content_type === 'video')
    } else if (activeFilter === 'assigned') {
      filtered = filtered.filter(c => {
        const assignments = allAssignmentsData?.[c.id]
        return assignments && assignments.length > 0
      })
    } else if (activeFilter === 'unassigned') {
      filtered = filtered.filter(c => {
        const assignments = allAssignmentsData?.[c.id]
        return !assignments || assignments.length === 0
      })
    }
    // 'all' shows everything

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(content =>
        content.file_name?.toLowerCase().includes(query) ||
        content.title?.toLowerCase().includes(query) ||
        content.description?.toLowerCase().includes(query)
      )
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at) - new Date(a.created_at)
        case 'oldest':
          return new Date(a.created_at) - new Date(b.created_at)
        case 'name_asc':
          return (a.file_name || '').localeCompare(b.file_name || '')
        case 'name_desc':
          return (b.file_name || '').localeCompare(a.file_name || '')
        default:
          return 0
      }
    })

    return sorted
  }, [contentData?.items, searchQuery, activeFilter, allAssignmentsData, sortBy])

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
      setShowEditForm(false)
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
    setShowEditForm(true)
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

  // Calculate stats
  const stats = useMemo(() => {
    if (!contentData?.items) return []

    const total = contentData.items.length
    const images = contentData.items.filter(c => c.content_type === 'image').length
    const videos = contentData.items.filter(c => c.content_type === 'video').length

    // Count assigned content (content that has assignments)
    const assigned = contentData.items.filter(c => {
      const assignments = allAssignmentsData?.[c.id]
      return assignments && assignments.length > 0
    }).length
    const unassigned = total - assigned

    return [
      { label: 'All Content', value: total, color: 'blue', filterKey: 'all' },
      { label: 'Images', value: images, color: 'purple', filterKey: 'images' },
      { label: 'Videos', value: videos, color: 'green', filterKey: 'videos' },
      { label: 'Assigned', value: assigned, color: 'green', filterKey: 'assigned' },
      { label: 'Unassigned', value: unassigned, color: 'gray', filterKey: 'unassigned' }
    ]
  }, [contentData?.items, allAssignmentsData])

  const selectedCount = selectedIds.size
  const totalCount = contentData?.items?.length || 0

  // Show loading skeleton while fetching
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
        {/* PageHeader Skeleton */}
        <div className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 lg:px-8 py-4">
          <div className="h-8 w-32 bg-gray-200 rounded animate-pulse mb-2"></div>
          <div className="h-4 w-64 bg-gray-200 rounded animate-pulse"></div>
        </div>

        {/* Content Grid Skeleton */}
        <div className="pt-40 sm:pt-[172px] lg:pt-44">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              <LoadingSkeleton variant="grid" count={8} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
      <PageHeader
        title="Content"
        description="Manage and organize media content"
        actions={
          <div className="flex items-center gap-3">
            {totalCount > 0 && (
              <Button
                variant="secondary"
                leftIcon={selectedCount === totalCount ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5" />}
                onClick={toggleSelectAll}
              >
                {selectedCount === totalCount ? 'Deselect All' : 'Select All'}
              </Button>
            )}
            {selectedCount > 0 && (
              <>
                <Button
                  variant="warning"
                  leftIcon={<Edit className="w-5 h-5" />}
                  onClick={() => setShowBulkEditForm(true)}
                >
                  Bulk Edit ({selectedCount})
                </Button>
                <Button
                  variant="success"
                  leftIcon={<TagIcon className="w-5 h-5" />}
                  onClick={() => setShowBulkTagForm(true)}
                >
                  Bulk Tag ({selectedCount})
                </Button>
              </>
            )}
            <Button
              variant="primary"
              leftIcon={<Upload className="w-5 h-5" />}
              onClick={() => setShowUploadForm(true)}
            >
              Upload Content
            </Button>
          </div>
        }
        searchBar={
          <div className="flex gap-3 max-w-xl">
            <div className="flex-1">
              <FormInput
                icon={Search}
                type="text"
                placeholder="Search content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="newest">Terbaru</option>
              <option value="oldest">Terlama</option>
              <option value="name_asc">Nama: A-Z</option>
              <option value="name_desc">Nama: Z-A</option>
            </select>
          </div>
        }
        stats={stats}
        activeFilter={activeFilter}
        onStatClick={setActiveFilter}
      />

      {/* Content with padding to account for fixed header */}
      {/* pt-40 (160px) mobile, pt-[172px] tablet (custom value between pt-42/168px and pt-44/176px), pt-44 (176px) desktop */}
      <div className="pt-40 sm:pt-[172px] lg:pt-44">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Selection Info */}
          {selectedCount > 0 && (
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg px-4 py-3 mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full text-sm font-medium">
                  {selectedCount} selected
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
                className="underline"
              >
                Clear Selection
              </Button>
            </div>
          )}

          {/* Content Grid */}
          {filteredContent.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {filteredContent.map((content) => (
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

          {contentData?.items?.length === 0 && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <FileImage className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>No content uploaded yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Upload Form Modal */}
      {showUploadForm && <UploadModal onClose={() => setShowUploadForm(false)} onSubmit={uploadMutation.mutate} />}

      {/* Edit Content Modal */}
      {showEditForm && <EditContentModal content={selectedContent} onClose={() => setShowEditForm(false)} onSubmit={assignMutation.mutate} />}

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

      {/* Floating Action Buttons - Mobile Only */}
      <div className="sm:hidden">
        {/* Upload Button - Bottom (Primary) */}
        <button
          onClick={() => setShowUploadForm(true)}
          className="fixed bottom-6 right-6 z-[55] w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 active:bg-blue-800 transition-colors flex items-center justify-center"
          aria-label="Upload Content"
        >
          <Upload className="w-6 h-6" />
        </button>

        {/* Select All Button - Above Upload */}
        {totalCount > 0 && (
          <button
            onClick={toggleSelectAll}
            className="fixed bottom-24 right-6 z-[55] w-14 h-14 bg-gray-600 text-white rounded-full shadow-lg hover:bg-gray-700 active:bg-gray-800 transition-colors flex items-center justify-center"
            aria-label={selectedCount === totalCount ? 'Deselect All' : 'Select All'}
          >
            {selectedCount === totalCount ? <CheckSquare className="w-6 h-6" /> : <Square className="w-6 h-6" />}
          </button>
        )}

        {/* Bulk Action Buttons - Above Select All */}
        {selectedCount > 0 && (
          <>
            {/* Bulk Tag Button */}
            <button
              onClick={() => setShowBulkTagForm(true)}
              className="fixed bottom-[168px] right-6 z-[55] w-14 h-14 bg-green-600 text-white rounded-full shadow-lg hover:bg-green-700 active:bg-green-800 transition-colors flex items-center justify-center"
              aria-label="Bulk Tag"
            >
              <TagIcon className="w-6 h-6" />
            </button>

            {/* Bulk Edit Button */}
            <button
              onClick={() => setShowBulkEditForm(true)}
              className="fixed bottom-[240px] right-6 z-[55] w-14 h-14 bg-yellow-600 text-white rounded-full shadow-lg hover:bg-yellow-700 active:bg-yellow-800 transition-colors flex items-center justify-center"
              aria-label="Bulk Edit"
            >
              <Edit className="w-6 h-6" />
            </button>
          </>
        )}
      </div>
    </div>
  )
}
