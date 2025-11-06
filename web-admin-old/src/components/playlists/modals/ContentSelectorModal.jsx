import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { contentAPI } from '../../../services/api'
import { Modal, Button, FormInput, Thumbnail } from '../../shared'
import { Search, Image as ImageIcon, Video, Check } from 'lucide-react'

/**
 * ContentSelectorModal Component
 * Modal for browsing and selecting content to add to playlists
 *
 * Features:
 * - Browse all available content (images & videos)
 * - Search and filter content by name/type
 * - Multi-select content with visual feedback
 * - Thumbnail previews for all content
 * - Filter by content type (all/image/video)
 * - Selected count indicator
 * - Submit selected content to parent
 *
 * @param {Array} alreadySelected - Array of content IDs already in the playlist (to prevent duplicates)
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSubmit - Callback when content is selected, receives array of content objects
 */
export default function ContentSelectorModal({ alreadySelected = [], onClose, onSubmit }) {
  const [selectedContent, setSelectedContent] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('all') // 'all', 'image', 'video'

  // Fetch all content
  const { data: contentData, isLoading } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  // Filter content based on search and type
  const filteredContent = contentData?.items?.filter(content => {
    // Exclude already selected content
    if (alreadySelected.includes(content.id)) {
      return false
    }

    // Filter by search query
    const matchesSearch = content.title.toLowerCase().includes(searchQuery.toLowerCase())

    // Filter by type
    const matchesType = typeFilter === 'all' || content.content_type === typeFilter

    return matchesSearch && matchesType
  }) || []

  // Toggle content selection
  const toggleSelection = (content) => {
    setSelectedContent(prev => {
      const exists = prev.find(c => c.id === content.id)
      if (exists) {
        return prev.filter(c => c.id !== content.id)
      } else {
        return [...prev, content]
      }
    })
  }

  // Check if content is selected
  const isSelected = (contentId) => {
    return selectedContent.some(c => c.id === contentId)
  }

  const handleSubmit = () => {
    if (selectedContent.length === 0) {
      alert('Please select at least one content item')
      return
    }
    onSubmit(selectedContent)
  }

  // Footer with action buttons
  const footer = (
    <div className="flex gap-3">
      <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
        Cancel
      </Button>
      <Button
        type="button"
        variant="primary"
        onClick={handleSubmit}
        disabled={selectedContent.length === 0}
        className="flex-1"
      >
        Add {selectedContent.length > 0 && `(${selectedContent.length})`} to Playlist
      </Button>
    </div>
  )

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Add Content to Playlist"
      size="3xl"
      footer={footer}
    >
      <div className="space-y-4">
        {/* Search and Filter Controls */}
        <div className="flex gap-3">
          {/* Search Input */}
          <div className="flex-1">
            <FormInput
              type="text"
              placeholder="Search content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4 text-gray-400 dark:text-gray-500" />}
            />
          </div>

          {/* Type Filter */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setTypeFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                typeFilter === 'all'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => setTypeFilter('image')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-1 ${
                typeFilter === 'image'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
              Images
            </button>
            <button
              type="button"
              onClick={() => setTypeFilter('video')}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-1 ${
                typeFilter === 'video'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <Video className="w-4 h-4" />
              Videos
            </button>
          </div>
        </div>

        {/* Selected Count */}
        {selectedContent.length > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg px-4 py-2 text-sm text-blue-700 dark:text-blue-300">
            {selectedContent.length} item{selectedContent.length > 1 ? 's' : ''} selected
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Content Grid */}
        {!isLoading && filteredContent.length === 0 && (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg">
            <p className="text-gray-600 dark:text-gray-400 font-medium">
              {searchQuery || typeFilter !== 'all'
                ? 'No content found matching your filters'
                : 'No content available'
              }
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {searchQuery && 'Try adjusting your search query'}
            </p>
          </div>
        )}

        {!isLoading && filteredContent.length > 0 && (
          <div
            className="grid grid-cols-3 gap-4 max-h-[400px] overflow-y-auto pr-2"
            style={{ scrollbarWidth: 'thin' }}
          >
            {filteredContent.map((content) => {
              const selected = isSelected(content.id)

              return (
                <div
                  key={content.id}
                  onClick={() => toggleSelection(content)}
                  className={`
                    relative cursor-pointer group
                    rounded-lg overflow-hidden transition-all
                    ${selected
                      ? 'ring-4 ring-blue-500 shadow-lg'
                      : 'hover:ring-2 hover:ring-gray-300 dark:ring-gray-600'
                    }
                  `}
                >
                  {/* Thumbnail */}
                  <Thumbnail
                    content={content}
                    size="md"
                    aspectRatio="video"
                  />

                  {/* Selection Overlay */}
                  <div className={`
                    absolute top-2 right-2 w-6 h-6 rounded-full border-2
                    flex items-center justify-center transition-all
                    ${selected
                      ? 'bg-blue-500 border-blue-500'
                      : 'bg-white border-gray-300 group-hover:border-blue-400'
                    }
                  `}>
                    {selected && <Check className="w-4 h-4 text-white" />}
                  </div>

                  {/* Content Info */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                    <p className="text-white text-sm font-medium truncate">
                      {content.title}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-300 mt-1">
                      <span className="capitalize">{content.content_type}</span>
                      {content.duration && (
                        <>
                          <span>•</span>
                          <span>{Math.floor(content.duration)}s</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </Modal>
  )
}
