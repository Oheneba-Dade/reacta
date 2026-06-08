'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { AuthForm } from '@/components/auth/AuthForm'

export default function AuthPage() {
  const router = useRouter()

  useEffect(() => {
    if (isAuthenticated()) router.replace('/library')
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f9f9f9] p-4">
      <div className="w-full max-w-[400px] rounded-lg border border-[#e5e5e5] bg-white p-8">
        <h1 className="mb-6 text-[24px] font-semibold lowercase tracking-[-0.03em] text-[#1a1c1c]">
          reacta
        </h1>
        <AuthForm />
      </div>
    </div>
  )
}
