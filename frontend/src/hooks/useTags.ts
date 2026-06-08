'use client'

import { useState, useEffect } from 'react'
import { tags as tagsApi } from '@/lib/api'
import type { Tag } from '@/lib/types'

let _cache: Tag[] = []

export function useTags() {
  const [tagList, setTagList] = useState<Tag[]>(_cache)
  const [loading, setLoading] = useState(_cache.length === 0)

  useEffect(() => {
    if (_cache.length > 0) return
    tagsApi
      .list()
      .then((data) => {
        _cache = data
        setTagList(data)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return { tags: tagList, loading }
}
