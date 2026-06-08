'use client'

import { TagBadge } from './TagBadge'
import type { Tag } from '@/lib/types'

interface Props {
  tags: Tag[]
  selected: string[]
  onToggle: (id: string) => void
  onClear: () => void
}

export function TagFilter({ tags, selected, onToggle, onClear }: Props) {
  return (
    <div>
      <p className="mb-3 text-[12px] font-medium lowercase tracking-[0.02em] text-[#747878]">
        filter by tag
      </p>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <TagBadge
            key={tag.id}
            label={tag.label}
            active={selected.includes(tag.id)}
            onClick={() => onToggle(tag.id)}
          />
        ))}
      </div>
      {selected.length > 0 && (
        <button
          onClick={onClear}
          className="mt-3 text-[12px] text-[#4648d4] hover:underline lowercase"
        >
          clear filters
        </button>
      )}
    </div>
  )
}
