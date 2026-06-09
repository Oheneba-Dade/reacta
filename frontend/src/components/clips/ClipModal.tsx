'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Pencil, Copy, Check } from 'lucide-react'
import { toast } from 'sonner'
import { clips as clipsApi } from '@/lib/api'
import { useTags } from '@/hooks/useTags'
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
  onDelete?: () => void
  onUpdate?: (clip: Clip) => void
}

function isFullyDone(c: Clip) {
  return (
    (c.processing_status === 'ready' || c.processing_status === 'failed') &&
    (c.transcript_status === 'completed' || c.transcript_status === 'failed') &&
    (c.desc_embedding_status === 'completed' || c.desc_embedding_status === 'failed')
  )
}

export function ClipModal({ clipId, onClose, onDelete, onUpdate }: Props) {
  const [clip, setClip] = useState<Clip | null>(null)
  const { tags } = useTags()

  // Edit state
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editTagIds, setEditTagIds] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

  // Delete state
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Copy state
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    clipsApi.get(clipId).then((fresh) => {
      console.log('[ClipModal] fetched clip:', fresh)
      setClip(fresh)
    }).catch(console.error)
  }, [clipId])

  useEffect(() => {
    if (!clip) return
    if (isFullyDone(clip)) return

    const id = setInterval(async () => {
      try {
        const updated = await clipsApi.get(clipId)
        setClip(updated)
        if (isFullyDone(updated)) {
          clearInterval(id)
        }
      } catch {}
    }, 5000)

    return () => clearInterval(id)
  }, [clip?.processing_status, clip?.transcript_status, clip?.desc_embedding_status, clipId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (editing) { setEditing(false); return }
        if (confirmingDelete) { setConfirmingDelete(false); return }
        onClose()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose, editing, confirmingDelete])

  function startEditing() {
    if (!clip) return
    setEditTitle(clip.title ?? '')
    setEditDescription(clip.description ?? '')
    setEditTagIds(clip.tags.map((t) => t.id))
    setEditing(true)
  }

  async function handleSave() {
    if (!clip) return
    setSaving(true)
    try {
      const updated = await clipsApi.update(clip.id, {
        title: editTitle.trim() || undefined,
        description: editDescription.trim() || undefined,
        tag_ids: editTagIds,
      })
      setClip(updated)
      onUpdate?.(updated)
      setEditing(false)
      toast.success('clip updated')
    } catch {
      toast.error('failed to save changes')
    } finally {
      setSaving(false)
    }
  }

  async function handleReprocess() {
    if (!clip) return
    try {
      await clipsApi.reprocess(clip.id)
      const updated = await clipsApi.get(clip.id)
      setClip(updated)
    } catch {
      toast.error('reprocess failed')
    }
  }

  async function handleDelete() {
    if (!clip) return
    setDeleting(true)
    try {
      await clipsApi.delete(clip.id)
      toast.success('clip deleted')
      onDelete?.()
      onClose()
    } catch {
      toast.error('failed to delete clip')
      setDeleting(false)
      setConfirmingDelete(false)
    }
  }

  async function handleCopy() {
    if (!videoUrl) return
    await navigator.clipboard.writeText(videoUrl)
    setCopied(true)
    toast.success('copied to clipboard, meme away!')
    setTimeout(() => setCopied(false), 2000)
  }

  const inputClass =
    'w-full rounded-md border border-[#e5e5e5] px-3 py-2 text-[16px] md:text-[14px] text-[#1a1c1c] placeholder-[#747878] outline-none focus:border-[#4648d4]'

  const videoUrl = clip?.storage_key
    ? `${process.env.NEXT_PUBLIC_B2_PUBLIC_URL_BASE}/${clip.storage_key}`
    : null

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
              {clip?.processing_status === 'ready' && videoUrl ? (
                <video
                  controls
                  className="w-full md:rounded-l-lg"
                  src={videoUrl}
                />
              ) : (
                <div className="flex min-h-[160px] flex-col items-center justify-center gap-3 p-6 text-center md:min-h-[360px]">
                  <div className="h-2 w-2 rounded-full bg-[#747878] pulse-dot" />
                  <p className="text-[14px] text-[#444748]">processing in background</p>
                </div>
              )}
            </div>

            {/* Metadata column */}
            <div className="flex flex-col p-4 md:p-6">

              {/* Header */}
              <div className="mb-4 flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  {editing ? (
                    <input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="untitled"
                      className={inputClass}
                    />
                  ) : (
                    <h2 className="text-[18px] font-medium leading-snug text-[#1a1c1c]">
                      {clip?.title ?? clip?.original_filename ?? '—'}
                    </h2>
                  )}
                </div>
                <div className="flex flex-shrink-0 items-center gap-2">
                  {!editing && videoUrl && (
                    <button
                      onClick={handleCopy}
                      className="text-[#747878] hover:text-[#1a1c1c]"
                      title="copy link"
                    >
                      {copied
                        ? <Check className="h-4 w-4 text-green-500" />
                        : <Copy className="h-4 w-4" />}
                    </button>
                  )}
                  {!editing && (
                    <button
                      onClick={startEditing}
                      className="text-[#747878] hover:text-[#1a1c1c]"
                      title="edit"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={onClose}
                    className="text-[#747878] hover:text-[#1a1c1c]"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Description */}
              <div className="mb-4">
                {editing ? (
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    placeholder="describe this clip..."
                    rows={3}
                    className={`${inputClass} resize-none`}
                  />
                ) : (
                  clip?.description && (
                    <p className="text-[14px] leading-relaxed text-[#444748]">
                      {clip.description}
                    </p>
                  )
                )}
              </div>

              <hr className="border-[#f5f5f5]" />

              {/* Metadata list */}
              <dl className="my-4 space-y-2 text-[14px]">
                {[
                  ['duration', formatDuration(clip?.duration_seconds ?? 0)],
                  ['size', formatFileSize(clip?.file_size_bytes ?? 0)],
                  ['uploaded', clip ? formatDate(clip.created_at) : '—'],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between">
                    <dt className="lowercase text-[#747878]">{label}</dt>
                    <dd className="tabular text-[#444748]">{value}</dd>
                  </div>
                ))}
              </dl>

              <hr className="border-[#f5f5f5]" />

              {/* Tags */}
              <div className="my-4">
                {editing ? (
                  <div className="flex flex-wrap gap-2">
                    {tags.map((t) => (
                      <TagBadge
                        key={t.id}
                        label={t.label}
                        active={editTagIds.includes(t.id)}
                        onClick={() =>
                          setEditTagIds((prev) =>
                            prev.includes(t.id)
                              ? prev.filter((id) => id !== t.id)
                              : [...prev, t.id]
                          )
                        }
                      />
                    ))}
                  </div>
                ) : (
                  clip && clip.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {clip.tags.map((t) => (
                        <TagBadge key={t.id} label={t.label} />
                      ))}
                    </div>
                  )
                )}
              </div>

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
                          status === 'completed' || status === 'ready' ? 'ready'
                          : status === 'pending' ? 'pending'
                          : status === 'processing' ? 'processing'
                          : 'failed'
                        }
                      />
                    )}
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="mt-auto space-y-2">
                {editing ? (
                  <div className="flex gap-2">
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="flex-1 rounded-md bg-black py-2 text-[14px] lowercase text-white disabled:opacity-40"
                    >
                      {saving ? 'saving...' : 'save'}
                    </button>
                    <button
                      onClick={() => setEditing(false)}
                      className="flex-1 rounded-md border border-[#e5e5e5] py-2 text-[14px] lowercase text-[#1a1c1c] hover:border-[#4648d4]"
                    >
                      cancel
                    </button>
                  </div>
                ) : (
                  <>
                    {clip?.processing_status === 'failed' && (
                      <button
                        onClick={handleReprocess}
                        className="w-full rounded-md border border-[#e5e5e5] py-2 text-[14px] lowercase text-[#1a1c1c] hover:border-[#4648d4]"
                      >
                        reprocess
                      </button>
                    )}
                    {confirmingDelete ? (
                      <div className="flex gap-2">
                        <button
                          onClick={handleDelete}
                          disabled={deleting}
                          className="flex-1 rounded-md bg-[#ba1a1a] py-2 text-[14px] lowercase text-white disabled:opacity-40"
                        >
                          {deleting ? 'deleting...' : 'confirm delete'}
                        </button>
                        <button
                          onClick={() => setConfirmingDelete(false)}
                          className="flex-1 rounded-md border border-[#e5e5e5] py-2 text-[14px] lowercase text-[#1a1c1c]"
                        >
                          cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmingDelete(true)}
                        className="w-full rounded-md border border-[#e5e5e5] py-2 text-[14px] lowercase text-[#ba1a1a] hover:border-[#ba1a1a]"
                      >
                        delete clip
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
