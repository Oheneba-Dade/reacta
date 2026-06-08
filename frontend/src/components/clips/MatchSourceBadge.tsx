'use client'

import { cn } from '@/lib/utils'
import type { SearchResult } from '@/lib/types'

type MatchSource = SearchResult['match_source']

const config: Record<MatchSource, { label: string; className: string }> = {
  description: { label: 'DESCRIPTION', className: 'bg-[#f5f5f5] text-[#444748]' },
  transcript: { label: 'TRANSCRIPT', className: 'bg-[#eef2ff] text-[#4648d4]' },
  both: { label: 'BOTH', className: 'bg-[#4648d4] text-white' },
}

interface Props {
  source: MatchSource
  className?: string
}

export function MatchSourceBadge({ source, className }: Props) {
  const { label, className: baseClass } = config[source]
  return (
    <span
      className={cn(
        'inline-flex rounded-[2px] px-2 py-0.5',
        'text-[11px] font-medium leading-none tracking-[0.02em]',
        baseClass,
        className
      )}
    >
      {label}
    </span>
  )
}
