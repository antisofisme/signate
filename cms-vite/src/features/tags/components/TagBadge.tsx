/**
 * TagBadge Component
 * Display tag with custom color
 */

import type { Tag } from '../types/tag';

interface TagBadgeProps {
  tag: Tag | { tag_name: string; color: string };
  className?: string;
}

export function TagBadge({ tag, className = '' }: TagBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${className}`}
      style={{
        borderColor: tag.color,
        color: tag.color,
        backgroundColor: `${tag.color}15`,
      }}
    >
      {tag.tag_name}
    </span>
  );
}
