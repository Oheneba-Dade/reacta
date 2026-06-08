'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { useSearch } from '@/hooks/useSearch'
import { SearchBar } from '@/components/search/SearchBar'
import { SearchResults } from '@/components/search/SearchResults'
import { ClipModal } from '@/components/clips/ClipModal'

const EXAMPLE_QUERIES = [
  'someone saying jesus is lord',
  'football fan losing it',
  'complete shock reaction',
]

export default function SearchPage() {
  const router = useRouter()
  const { query, results, loading, error, hasSearched, runSearch } = useSearch()
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated()) router.replace('/')
  }, [router])

  return (
    <div className="mx-auto max-w-[800px] px-6 py-12">
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
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => runSearch(q)}
                className="rounded-md border border-[#e5e5e5] px-3 py-1.5 text-[14px] text-[#444748] transition-colors hover:border-[#4648d4]"
              >
                {q}
              </button>
            ))}
          </div>
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

      {selectedClipId && (
        <ClipModal clipId={selectedClipId} onClose={() => setSelectedClipId(null)} />
      )}
    </div>
  )
}
