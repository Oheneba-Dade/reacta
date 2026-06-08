'use client'

import { cn } from '@/lib/utils'
import type { Clip } from '@/lib/types'

type ProcessingStatus = Clip['processing_status']

const config: Record<ProcessingStatus, { label: string; className: string; pulse?: boolean }> = {
  pending: { label: 'pending', className: 'bg-[#f3f3f3] text-[#747878]' },
  processing: { label: 'processing', className: 'bg-[#f3f3f3] text-[#747878]', pulse: true },
  ready: { label: 'ready', className: 'bg-[#f3f3f3] text-[#444748]' },
  failed: { label: 'failed', className: 'bg-[#ffdad6] text-[#ba1a1a]' },
}

interface Props {
  status: ProcessingStatus
  className?: string
}

export function StatusBadge({ status, className }: Props) {
  const { label, className: baseClass, pulse } = config[status]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-[2px] px-2 py-0.5',
        'text-[11px] font-medium leading-none tracking-[0.02em]',
        baseClass,
        className
      )}
    >
      {pulse && (
        <span className="inline-block h-1 w-1 rounded-full bg-current pulse-dot" />
      )}
      {label}
    </span>
  )
}
