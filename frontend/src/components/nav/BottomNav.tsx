'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Library, Search, Upload, LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

const links = [
  { href: '/library', label: 'library', Icon: Library },
  { href: '/search', label: 'search', Icon: Search },
  { href: '/upload', label: 'upload', Icon: Upload },
]

export function BottomNav() {
  const pathname = usePathname()
  const { logout } = useAuth()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 flex h-16 items-center justify-around border-t border-[#e5e5e5] bg-white md:hidden">
      {links.map(({ href, label, Icon }) => {
        const active = pathname.startsWith(href)
        return (
          <Link
            key={href}
            href={href}
            className={`flex flex-col items-center gap-0.5 px-4 ${
              active ? 'text-[#4648d4]' : 'text-[#747878]'
            }`}
          >
            <Icon className="h-5 w-5" />
            <span className="text-[11px] lowercase">{label}</span>
          </Link>
        )
      })}
      <button
        onClick={logout}
        className="flex flex-col items-center gap-0.5 px-4 text-[#747878]"
      >
        <LogOut className="h-5 w-5" />
        <span className="text-[11px] lowercase">sign out</span>
      </button>
    </nav>
  )
}
