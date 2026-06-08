'use client'

import { motion } from 'framer-motion'
import { ClipCard } from './ClipCard'
import type { Clip, SearchResult } from '@/lib/types'

interface Props {
  clips: Clip[]
  matchSources?: Record<string, SearchResult['match_source']>
  onSelect: (id: string) => void
}

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.05 },
  },
}

export function ClipGrid({ clips, matchSources, onSelect }: Props) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
    >
      {clips.map((clip) => (
        <ClipCard
          key={clip.id}
          clip={clip}
          matchSource={matchSources?.[clip.id]}
          onClick={() => onSelect(clip.id)}
        />
      ))}
    </motion.div>
  )
}
