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

  async function runSearch(q: string) {
    if (!q.trim()) return
    setQuery(q)
    setLoading(true)
    setError(null)
    setHasSearched(true)
    try {
      const data = await searchApi.query(q)
      setResults(data.results)
    } catch {
      setError('Search failed. Please try again.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return { query, results, loading, error, hasSearched, runSearch }
}
