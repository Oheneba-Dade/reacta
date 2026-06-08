'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { useSearch } from '@/hooks/useSearch'
import { SearchBar } from '@/components/search/SearchBar'
import { SearchResults } from '@/components/search/SearchResults'
import { ClipModal } from '@/components/clips/ClipModal'

export default function SearchPage() {
  const router = useRouter()
  const { query, results, loading, error, hasSearched, runSearch } = useSearch()
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated()) router.replace('/')
  }, [router])

  return (
    <div className="mx-auto max-w-[800px] px-4 py-6 md:px-6 md:py-12">
      <div className="mb-8 flex justify-center">
        <div className="w-full max-w-[640px]">
          <SearchBar onSearch={runSearch} />
        </div>
      </div>

      {!hasSearched && (
        <div className="text-center">
          <h1 className="text-[18px] font-medium lowercase tracking-[-0.02em] text-[#1a1c1c]">
            search your reaction library
          </h1>
        </div>
      )}

      {error && (
        <p className="text-center text-[14px] text-[#ba1a1a]">{error}</p>
      )}

      {hasSearched && (
        <SearchResults
          query={query}
          results={results}
          loading={loading}
          onSelectClip={setSelectedClipId}
        />
      )}

      {hasSearched && (
        <footer className="mt-12 border-t border-[#e5e5e5] pt-6">
          <p className="mx-auto max-w-[640px] text-center text-[14px] leading-relaxed text-[#747878]">
            results are ranked by a combination of semantic similarity to your description, transcript content, and keyword relevance. matched via both means the clip was found through multiple signals.
          </p>
        </footer>
      )}

      {selectedClipId && (
        <ClipModal clipId={selectedClipId} onClose={() => setSelectedClipId(null)} />
      )}
    </div>
  )
}
