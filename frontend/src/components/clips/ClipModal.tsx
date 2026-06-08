'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { clips as clipsApi, getVideoUrl } from '@/lib/api'
import { StatusBadge } from './StatusBadge'
import { TagBadge } from '@/components/tags/TagBadge'
import type { Clip } from '@/lib/types'

function formatDuration(secs: number) {
  const s = Math.round(secs * 10) / 10
  return `${s}s`
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

interface Props {
  clipId: string
  onClose: () => void
}

const TERMINAL = ['ready', 'failed']

export function ClipModal({ clipId, onClose }: Props) {
  const [clip, setClip] = useState<Clip | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    clipsApi.get(clipId).then(setClip).catch(console.error)
  }, [clipId])

  useEffect(() => {
    if (!clip) return
    if (!TERMINAL.includes(clip.processing_status)) {
      intervalRef.current = setInterval(async () => {
        try {
          const status = await clipsApi.status(clipId)
          if (TERMINAL.includes(status.processing_status)) {
            clearInterval(intervalRef.current!)
            const updated = await clipsApi.get(clipId)
            setClip(updated)
          } else {
            setClip((prev) =>
              prev
                ? {
                    ...prev,
                    processing_status: status.processing_status,
                    desc_embedding_status: status.desc_embedding_status,
                    transcript_status: status.transcript_status,
                  }
                : prev
            )
          }
        } catch {}
      }, 5000)
    }
    return () => clearInterval(intervalRef.current!)
  }, [clip?.processing_status, clipId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  async function handleReprocess() {
    if (!clip) return
    try {
      await clipsApi.reprocess(clip.id)
      const updated = await clipsApi.get(clip.id)
      setClip(updated)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={(e) => e.stopPropagation()}
          className="relative max-h-[90vh] w-[90vw] max-w-[880px] overflow-y-auto rounded-lg border border-[#e5e5e5] bg-white"
        >
          <div className="grid grid-cols-1 md:grid-cols-[1fr_320px]">
            {/* Video column */}
            <div className="bg-black md:rounded-l-lg">
              {clip?.processing_status === 'ready' ? (
                <video
                  controls
                  className="w-full rounded-l-none md:rounded-l-lg"
                  src={getVideoUrl(clip.storage_key)}
                />
              ) : (
                <div className="flex min-h-[240px] flex-col items-center justify-center gap-3 p-8 text-center md:min-h-[360px]">
                  <div className="h-2 w-2 rounded-full bg-[#747878] pulse-dot" />
                  <p className="text-[14px] text-[#444748]">processing in background</p>
                </div>
              )}
            </div>

            {/* Metadata column */}
            <div className="flex flex-col gap-0 p-6">
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h2 className="text-[18px] font-medium leading-snug text-[#1a1c1c]">
                    {clip?.title ?? clip?.original_filename ?? '—'}
                  </h2>
                  {clip?.description && (
                    <p className="mt-1 text-[14px] leading-relaxed text-[#444748]">
                      {clip.description}
                    </p>
                  )}
                </div>
                <button
                  onClick={onClose}
                  className="ml-4 flex-shrink-0 text-[#747878] hover:text-[#1a1c1c]"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <hr className="border-[#f5f5f5]" />

              {/* Metadata list */}
              <dl className="my-4 space-y-2 text-[14px]">
                {[
                  ['duration', formatDuration(clip?.duration_seconds ?? 0)],
                  ['size', formatFileSize(clip?.file_size_bytes ?? 0)],
                  ['uploaded', clip ? formatDate(clip.created_at) : '—'],
                  ['file', clip?.original_filename ?? '—'],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between">
                    <dt className="lowercase text-[#747878]">{label}</dt>
                    <dd className="tabular text-[#444748]">{value}</dd>
                  </div>
                ))}
              </dl>

              <hr className="border-[#f5f5f5]" />

              {/* Tags */}
              {clip && clip.tags.length > 0 && (
                <div className="my-4 flex flex-wrap gap-2">
                  {clip.tags.map((t) => (
                    <TagBadge key={t.id} label={t.label} />
                  ))}
                </div>
              )}

              <hr className="border-[#f5f5f5]" />

              {/* Status rows */}
              <div className="my-4 space-y-2 text-[14px]">
                {([
                  ['processing', clip?.processing_status],
                  ['transcription', clip?.transcript_status],
                  ['embedding', clip?.desc_embedding_status],
                ] as const).map(([label, status]) => (
                  <div key={label} className="flex items-center justify-between">
                    <span className="lowercase text-[#747878]">{label}</span>
                    {status && (
                      <StatusBadge
                        status={
                          status === 'completed'
                            ? 'ready'
                            : status === 'pending'
                            ? 'pending'
                            : status === 'processing'
                            ? 'processing'
                            : 'failed'
                        }
                      />
                    )}
                  </div>
                ))}
              </div>

              {clip?.processing_status === 'failed' && (
                <button
                  onClick={handleReprocess}
                  className="mt-2 w-full rounded-md border border-[#e5e5e5] py-2 text-[14px] lowercase text-[#1a1c1c] hover:border-[#4648d4]"
                >
                  reprocess
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
