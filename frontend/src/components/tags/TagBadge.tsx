'use client'

import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'

interface Props {
  label: string
  active?: boolean
  onClick?: () => void
  className?: string
}

export function TagBadge({ label, active = false, onClick, className }: Props) {
  return (
    <motion.button
      type="button"
      whileTap={{ scale: 0.96 }}
      transition={{ duration: 0.15 }}
      onClick={onClick}
      className={cn(
        'inline-flex rounded-full px-3 py-1 text-[12px] font-medium lowercase tracking-[0.02em] transition-colors',
        active
          ? 'border border-transparent bg-[#4648d4] text-white'
          : 'border border-[#e5e5e5] bg-white text-[#444748] hover:border-[#4648d4]',
        className
      )}
    >
      {label}
    </motion.button>
  )
}
