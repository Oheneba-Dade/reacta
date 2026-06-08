'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { UploadForm } from '@/components/upload/UploadForm'

export default function UploadPage() {
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated()) router.replace('/')
  }, [router])

  return (
    <div className="mx-auto max-w-[560px] px-4 py-6 md:py-12">
      <h1 className="mb-8 text-[18px] font-medium lowercase tracking-[-0.02em] text-[#1a1c1c]">
        upload a clip
      </h1>
      <UploadForm />
    </div>
  )
}
