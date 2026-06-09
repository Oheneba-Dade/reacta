'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ChevronDown } from 'lucide-react'
import { isAuthenticated } from '@/lib/auth'
import { useClips } from '@/hooks/useClips'
import { useTags } from '@/hooks/useTags'
import { ClipGrid } from '@/components/clips/ClipGrid'
import { ClipModal } from '@/components/clips/ClipModal'
import { TagFilter } from '@/components/tags/TagFilter'
import { TagBadge } from '@/components/tags/TagBadge'

export default function LibraryPage() {
  const router = useRouter()
  const { clips, loading, refetch } = useClips()
  const { tags } = useTags()
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null)
  const [filterOpen, setFilterOpen] = useState(false)

  useEffect(() => {
    if (!isAuthenticated()) router.replace('/')
  }, [router])

  function toggleTag(id: string) {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    )
  }

  const filtered =
    selectedTags.length === 0
      ? clips
      : clips.filter((c) => c.tags.some((t) => selectedTags.includes(t.id)))

  return (
    <div className="flex min-h-[calc(100vh-120px)] md:min-h-[calc(100vh-56px)]">
      {/* Sidebar — desktop only */}
      <aside className="hidden w-60 flex-shrink-0 border-r border-[#e5e5e5] p-6 md:block">
        <TagFilter
          tags={tags}
          selected={selectedTags}
          onToggle={toggleTag}
          onClear={() => setSelectedTags([])}
        />
      </aside>

      {/* Main */}
      <div className="flex-1 p-4 md:p-6">
        <div className="mb-4 flex items-center justify-between md:mb-6">
          <div>
            <h1 className="text-[18px] font-medium lowercase tracking-[-0.02em] text-[#1a1c1c]">
              your library
            </h1>
            {!loading && (
              <p className="tabular text-[14px] text-[#747878]">
                {filtered.length} clip{filtered.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>
          <Link
            href="/upload"
            className="rounded-md border border-[#e5e5e5] px-4 py-2 text-[14px] lowercase text-[#1a1c1c] hover:border-[#4648d4]"
          >
            <span className="md:hidden text-[18px] leading-none">+</span>
            <span className="hidden md:inline">upload</span>
          </Link>
        </div>

        {/* Mobile tag filter */}
        {tags.length > 0 && (
          <div className="mb-4 md:hidden">
            <button
              onClick={() => setFilterOpen((o) => !o)}
              className="flex items-center gap-1 text-[14px] lowercase text-[#747878]"
            >
              filter{selectedTags.length > 0 ? ` (${selectedTags.length})` : ''}
              <ChevronDown
                className={`h-4 w-4 transition-transform duration-200 ${filterOpen ? 'rotate-180' : ''}`}
              />
            </button>
            {filterOpen && (
              <div className="mt-3 flex flex-wrap gap-2">
                {tags.map((t) => (
                  <TagBadge
                    key={t.id}
                    label={t.label}
                    active={selectedTags.includes(t.id)}
                    onClick={() => toggleTag(t.id)}
                  />
                ))}
                {selectedTags.length > 0 && (
                  <button
                    onClick={() => setSelectedTags([])}
                    className="text-[12px] lowercase text-[#4648d4] hover:underline"
                  >
                    clear
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="rounded-lg border border-[#e5e5e5] bg-white">
                <div className="aspect-video animate-pulse rounded-t-lg bg-[#f3f3f3]" />
                <div className="space-y-2 p-4">
                  <div className="h-4 w-3/4 animate-pulse rounded bg-[#f3f3f3]" />
                  <div className="h-3 animate-pulse rounded bg-[#f3f3f3]" />
                </div>
              </div>
            ))}
          </div>
        ) : clips.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <h2 className="text-[18px] font-medium lowercase text-[#1a1c1c]">
              your library is empty
            </h2>
            <p className="mt-2 text-[14px] text-[#747878]">
              upload your first reaction clip to get started
            </p>
            <Link
              href="/upload"
              className="mt-6 rounded-md bg-black px-6 py-2.5 text-[14px] lowercase text-white"
            >
              upload a clip
            </Link>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-[14px] text-[#747878]">no clips match your filters</p>
            <button
              onClick={() => setSelectedTags([])}
              className="mt-2 text-[14px] text-[#4648d4] hover:underline lowercase"
            >
              clear filters
            </button>
          </div>
        ) : (
          <ClipGrid clips={filtered} onSelect={setSelectedClipId} />
        )}
      </div>

      {selectedClipId && (
        <ClipModal
          clipId={selectedClipId}
          onClose={() => setSelectedClipId(null)}
          onDelete={() => refetch()}
        />
      )}
    </div>
  )
}
