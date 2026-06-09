'use client'

import { useState } from 'react'
import { search as searchApi } from '@/lib/api'
import type { SearchResult } from '@/lib/types'

export function useSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)
  const [limit, setLimit] = useState(3)

  async function runSearch(q: string, overrideLimit?: number) {
    if (!q.trim()) return
    setQuery(q)
    setLoading(true)
    setError(null)
    setHasSearched(true)
    try {
      const data = await searchApi.query(q, overrideLimit ?? limit)
      setResults(data.results)
    } catch {
      setError('Search failed. Please try again.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  async function changeLimit(n: number) {
    setLimit(n)
    if (query) await runSearch(query, n)
  }

  return { query, results, loading, error, hasSearched, runSearch, limit, changeLimit }
}
