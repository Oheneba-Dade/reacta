'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'

const links = [
  { href: '/library', label: 'library' },
  { href: '/search', label: 'search' },
  { href: '/upload', label: 'upload' },
]

export function TopNav() {
  const pathname = usePathname()
  const { logout } = useAuth()

  return (
    <nav className="hidden h-14 items-center justify-between border-b border-[#e5e5e5] bg-white px-6 md:flex">
      <Link href="/library" className="text-[18px] font-semibold lowercase text-[#1a1c1c]">
        reacta
      </Link>
      <div className="flex items-center gap-8">
        {links.map(({ href, label }) => {
          const active = pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={`pb-0.5 text-[14px] lowercase transition-colors ${
                active
                  ? 'border-b-2 border-[#4648d4] text-[#1a1c1c]'
                  : 'text-[#1a1c1c] hover:text-[#4648d4]'
              }`}
            >
              {label}
            </Link>
          )
        })}
        <button
          onClick={logout}
          className="text-[14px] lowercase text-[#747878] hover:text-[#1a1c1c]"
        >
          sign out
        </button>
      </div>
    </nav>
  )
}
