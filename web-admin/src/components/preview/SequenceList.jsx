import { Film, Image as ImageIcon, Play } from 'lucide-react'

/**
 * SequenceList Component
 * Displays scrollable list of content in playback sequence
 *
 * Props:
 * - sequence: Array of content objects in playback order
 * - currentIndex: Index of currently playing content
 * - onJumpTo: Callback when clicking on a content item
 */
export default function SequenceList({ sequence, currentIndex, onJumpTo }) {
  if (!sequence || sequence.length === 0) {
    return (
      <div className="p-6 text-center text-gray-400">
        <p>No content in sequence</p>
      </div>
    )
  }

  // Get source badge config
  const getSourceBadge = (source) => {
    if (!source) return { color: 'bg-gray-600', icon: '?', label: 'Unknown' }

    switch (source.type) {
      case 'direct':
        return {
          color: 'bg-red-600',
          icon: '🎯',
          label: source.name,
          priority: source.priority
        }
      case 'playlist':
        return {
          color: 'bg-blue-600',
          icon: '📋',
          label: source.name,
          priority: source.priority
        }
      case 'tag':
        return {
          color: 'bg-purple-600',
          icon: '🏷️',
          label: source.name,
          priority: source.priority
        }
      default:
        return {
          color: 'bg-gray-600',
          icon: '?',
          label: source.name || 'Unknown'
        }
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 bg-gray-900">
        <h3 className="font-semibold text-white">
          🎬 Playback Sequence
        </h3>
        <p className="text-xs text-gray-400 mt-1">
          {sequence.length} items • Click to jump
        </p>
      </div>

      {/* Content List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-2">
          {sequence.map((item, index) => {
            const badge = getSourceBadge(item.source)
            const isActive = index === currentIndex
            const contentIcon = item.content_type === 'video' || item.content_type === 'webpage'
              ? <Film className="w-4 h-4" />
              : <ImageIcon className="w-4 h-4" />

            return (
              <div
                key={index}
                onClick={() => onJumpTo(index)}
                className={`
                  relative rounded-lg p-3 cursor-pointer transition-all
                  ${isActive
                    ? 'bg-blue-600 ring-2 ring-blue-400'
                    : 'bg-gray-700 hover:bg-gray-600'
                  }
                `}
              >
                {/* Current Playing Indicator */}
                {isActive && (
                  <div className="absolute -left-1 top-1/2 -translate-y-1/2">
                    <Play className="w-5 h-5 text-blue-300 fill-blue-300" />
                  </div>
                )}

                {/* Sequence Number */}
                <div className="flex items-start gap-3">
                  <span className={`
                    flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                    ${isActive ? 'bg-white text-blue-600' : 'bg-gray-600 text-white'}
                  `}>
                    {index + 1}
                  </span>

                  <div className="flex-1 min-w-0">
                    {/* Content Title */}
                    <div className="flex items-center gap-2 mb-1">
                      <span className={isActive ? 'text-blue-100' : 'text-gray-300'}>
                        {contentIcon}
                      </span>
                      <h4 className={`
                        font-medium text-sm truncate
                        ${isActive ? 'text-white' : 'text-gray-100'}
                      `}>
                        {item.title}
                      </h4>
                    </div>

                    {/* Content Type & Duration */}
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`
                        text-xs px-2 py-0.5 rounded
                        ${isActive
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-600 text-gray-200'
                        }
                      `}>
                        {item.content_type}
                      </span>
                      <span className={`
                        text-xs
                        ${isActive ? 'text-blue-100' : 'text-gray-400'}
                      `}>
                        {item.duration}s
                      </span>
                    </div>

                    {/* Source Badge */}
                    <div className={`
                      inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs
                      ${badge.color} text-white
                    `}>
                      <span>{badge.icon}</span>
                      <span className="font-medium">{badge.label}</span>
                      {badge.priority !== undefined && (
                        <span className="text-[10px] opacity-75">
                          P:{badge.priority}
                        </span>
                      )}
                    </div>

                    {/* Description (if available) */}
                    {item.description && (
                      <p className={`
                        text-xs mt-2 line-clamp-2
                        ${isActive ? 'text-blue-100' : 'text-gray-400'}
                      `}>
                        {item.description}
                      </p>
                    )}

                    {/* Thumbnail (if available) */}
                    {item.thumbnail_url && (
                      <div className="mt-2 rounded overflow-hidden">
                        <img
                          src={item.thumbnail_url}
                          alt={item.title}
                          className="w-full h-20 object-cover"
                          loading="lazy"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer Stats */}
      <div className="px-4 py-3 border-t border-gray-700 bg-gray-900">
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div>
            <p className="text-gray-400">Direct</p>
            <p className="text-red-400 font-bold">
              {sequence.filter(s => s.source?.type === 'direct').length}
            </p>
          </div>
          <div>
            <p className="text-gray-400">Playlist</p>
            <p className="text-blue-400 font-bold">
              {sequence.filter(s => s.source?.type === 'playlist').length}
            </p>
          </div>
          <div>
            <p className="text-gray-400">Tag</p>
            <p className="text-purple-400 font-bold">
              {sequence.filter(s => s.source?.type === 'tag').length}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
