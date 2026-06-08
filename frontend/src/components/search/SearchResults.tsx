'use client'

import { ClipGrid } from '@/components/clips/ClipGrid'
import type { SearchResult } from '@/lib/types'

interface Props {
  query: string
  results: SearchResult[]
  loading: boolean
  onSelectClip: (id: string) => void
}

const SkeletonCard = () => (
  <div className="rounded-lg border border-[#e5e5e5] bg-white">
    <div className="aspect-video animate-pulse rounded-t-lg bg-[#f3f3f3]" />
    <div className="space-y-2 p-4">
      <div className="h-4 w-3/4 animate-pulse rounded bg-[#f3f3f3]" />
      <div className="h-3 animate-pulse rounded bg-[#f3f3f3]" />
      <div className="h-3 w-2/3 animate-pulse rounded bg-[#f3f3f3]" />
    </div>
  </div>
)

export function SearchResults({ query, results, loading, onSelectClip }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  if (!query) return null

  const matchSources = Object.fromEntries(
    results.map((r) => [r.clip.id, r.match_source])
  )
  const clips = results.map((r) => r.clip)

  return (
    <div>
      <p className="mb-4 text-[14px] text-[#747878]">
        {results.length === 0
          ? `no clips found for "${query}"`
          : `${results.length} result${results.length === 1 ? '' : 's'} for "${query}"`}
      </p>
      {results.length === 0 ? (
        <p className="text-[14px] text-[#747878]">
          try different wording — semantic search works best with descriptive phrases
        </p>
      ) : (
        <ClipGrid clips={clips} matchSources={matchSources} onSelect={onSelectClip} />
      )}
    </div>
  )
}
