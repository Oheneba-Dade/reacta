'use client'

import { motion } from 'framer-motion'
import { Play } from 'lucide-react'
import { StatusBadge } from './StatusBadge'
import { MatchSourceBadge } from './MatchSourceBadge'
import type { Clip, SearchResult } from '@/lib/types'

function formatDuration(secs: number): string {
  const s = Math.floor(secs)
  const m = Math.floor(s / 60)
  const rem = s % 60
  return m > 0 ? `${m}:${rem.toString().padStart(2, '0')}` : `${rem}s`
}

interface Props {
  clip: Clip
  matchSource?: SearchResult['match_source']
  onClick: () => void
}

export const cardVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0 },
}

export function ClipCard({ clip, matchSource, onClick }: Props) {
  const displayTitle = clip.title ?? clip.original_filename
  const visibleTags = clip.tags.slice(0, 2)
  const extraTags = clip.tags.length - visibleTags.length

  return (
    <motion.div
      variants={cardVariants}
      onClick={onClick}
      className="cursor-pointer rounded-lg border border-[#e5e5e5] bg-white transition-shadow hover:shadow-[0px_4px_12px_rgba(0,0,0,0.03)]"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video rounded-t-lg bg-[#f3f3f3]">
        <div className="flex h-full items-center justify-center">
          <Play className="h-8 w-8 text-[#c4c7c7]" />
        </div>
        {clip.processing_status !== 'ready' && (
          <div className="absolute bottom-2 left-2">
            <StatusBadge status={clip.processing_status} />
          </div>
        )}
        {matchSource && (
          <div className="absolute right-2 top-2">
            <MatchSourceBadge source={matchSource} />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3 md:p-4">
        <p className="text-[14px] font-medium leading-snug text-[#1a1c1c] line-clamp-1 md:text-[16px]">
          {displayTitle}
        </p>
        {clip.description && (
          <p className="mt-1 text-[13px] leading-snug text-[#444748] line-clamp-2 md:text-[14px]">
            {clip.description}
          </p>
        )}

        {/* Footer */}
        <div className="mt-2 flex items-center justify-between md:mt-3">
          <span className="tabular text-[12px] font-medium text-[#747878]">
            {formatDuration(clip.duration_seconds)}
          </span>
          <div className="flex flex-wrap justify-end gap-1">
            {visibleTags.map((t) => (
              <span
                key={t.id}
                className="rounded-full border border-[#e5e5e5] bg-white px-2 py-0.5 text-[11px] lowercase text-[#444748]"
              >
                {t.label}
              </span>
            ))}
            {extraTags > 0 && (
              <span className="text-[11px] text-[#747878]">+{extraTags}</span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
