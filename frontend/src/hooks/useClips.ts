'use client'

import { useState, useEffect, useCallback } from 'react'
import { clips as clipsApi } from '@/lib/api'
import type { Clip } from '@/lib/types'

export function useClips() {
  const [clips, setClips] = useState<Clip[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await clipsApi.list()
      setClips(data)
    } catch {
      setError('Failed to load clips')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { clips, loading, error, refetch: fetch }
}
