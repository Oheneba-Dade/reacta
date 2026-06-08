'use client'

import { useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, X } from 'lucide-react'
import { toast } from 'sonner'
import { clips as clipsApi } from '@/lib/api'
import { TagBadge } from '@/components/tags/TagBadge'
import { useTags } from '@/hooks/useTags'

export function UploadForm() {
  const router = useRouter()
  const { tags } = useTags()
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function formatSize(bytes: number) {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  function handleFile(f: File) {
    setFile(f)
    setError(null)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('video/')) handleFile(f)
  }

  function toggleTag(id: string) {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    )
  }

  const canSubmit = !!file && description.trim().length >= 10 && !uploading

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit || !file) return

    setUploading(true)
    setProgress(10)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('description', description)
    if (title.trim()) formData.append('title', title.trim())
    selectedTags.forEach((id) => formData.append('tag_ids', id))

    try {
      setProgress(40)
      await clipsApi.upload(formData)
      setProgress(100)
      toast.success('clip uploaded — processing in background')
      router.push('/library')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message ?? 'Upload failed'
      setError(msg)
      toast.error(msg)
      setUploading(false)
      setProgress(0)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`flex min-h-[160px] flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center transition-colors ${
          dragOver
            ? 'border-[#4648d4] bg-[#eef2ff]'
            : 'border-[#c4c7c7] bg-white'
        }`}
      >
        {file ? (
          <div className="flex items-center gap-2">
            <span className="text-[14px] text-[#1a1c1c]">{file.name}</span>
            <span className="tabular text-[12px] text-[#747878]">{formatSize(file.size)}</span>
            <button
              type="button"
              onClick={() => setFile(null)}
              className="text-[#747878] hover:text-[#ba1a1a]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="h-8 w-8 text-[#c4c7c7]" />
            <p className="text-[14px] text-[#444748]">drag and drop your video</p>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="text-[14px] text-[#4648d4] hover:underline"
            >
              + browse files
            </button>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) handleFile(f)
          }}
        />
      </div>

      {/* Title */}
      <div className="space-y-1">
        <label className="block text-[12px] font-medium lowercase tracking-[0.02em] text-[#1a1c1c]">
          title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="untitled"
          className="w-full rounded-md border border-[#e5e5e5] px-3 py-2 text-[14px] text-[#1a1c1c] placeholder-[#747878] outline-none focus:border-[#4648d4]"
        />
      </div>

      {/* Description */}
      <div className="space-y-1">
        <label className="block text-[12px] font-medium lowercase tracking-[0.02em] text-[#1a1c1c]">
          description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="describe what happens in this clip..."
          rows={4}
          className="w-full rounded-md border border-[#e5e5e5] px-3 py-2 text-[14px] text-[#1a1c1c] placeholder-[#747878] outline-none focus:border-[#4648d4] resize-none"
        />
        <p className="text-[12px] lowercase tracking-[0.02em] text-[#747878]">
          this powers semantic search — be descriptive
        </p>
      </div>

      {/* Tags */}
      <div className="space-y-2">
        <label className="block text-[12px] font-medium lowercase tracking-[0.02em] text-[#1a1c1c]">
          tags
        </label>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <TagBadge
              key={tag.id}
              label={tag.label}
              active={selectedTags.includes(tag.id)}
              onClick={() => toggleTag(tag.id)}
            />
          ))}
        </div>
      </div>

      {/* Progress bar */}
      {uploading && (
        <div className="h-1 w-full overflow-hidden rounded-full bg-[#f3f3f3]">
          <div
            className="h-full bg-[#4648d4] transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {error && (
        <p className="text-[14px] text-[#ba1a1a]">{error}</p>
      )}

      <button
        type="submit"
        disabled={!canSubmit}
        className="w-full rounded-md bg-black py-2.5 text-[14px] font-medium lowercase text-white transition-opacity disabled:opacity-40"
      >
        {uploading ? 'uploading...' : 'upload clip'}
      </button>

      <p className="text-center text-[14px] text-[#747878]">
        your clip will be searchable in a few minutes once transcription and embedding complete.
      </p>
    </form>
  )
}
