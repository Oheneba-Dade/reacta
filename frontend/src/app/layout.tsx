import type { Metadata } from 'next'
import './globals.css'
import { TopNav } from '@/components/nav/TopNav'
import { BottomNav } from '@/components/nav/BottomNav'
import { Toaster } from '@/components/ui/sonner'

export const metadata: Metadata = {
  title: 'reacta',
  description: 'your personal reaction clip library',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col bg-[#f9f9f9]" style={{ fontFamily: "'Raleway', sans-serif" }}>
        <TopNav />
        <main className="flex-1 pb-16 md:pb-0">{children}</main>
        <BottomNav />
        <Toaster position="top-right" />
      </body>
    </html>
  )
}
