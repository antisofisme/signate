import { useQuery } from '@tanstack/react-query'
import { contentAPI } from '../../services/api'
import { Link as LinkIcon } from 'lucide-react'

/**
 * AssignmentBadge Component
 * Displays assignment count badge for content
 *
 * Features:
 * - Shows number of assignments (devices/tags) for content
 * - Purple badge with link icon
 * - Hidden when no assignments
 * - Auto-updates via React Query
 *
 * @param {number} contentId - Content ID to fetch assignments for
 */
export default function AssignmentBadge({ contentId }) {
  const { data: assignmentsData } = useQuery({
    queryKey: ['content-assignments', contentId],
    queryFn: () => contentAPI.getAssignments(contentId).then(res => res.data),
  })

  const count = assignmentsData?.length || 0

  if (count === 0) return null

  return (
    <div className="bg-purple-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
      <LinkIcon className="w-3 h-3" />
      {count}
    </div>
  )
}
