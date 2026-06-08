'use client'

import { useState } from 'react'
import { Search } from 'lucide-react'

interface Props {
  onSearch: (q: string) => void
  initialValue?: string
}

export function SearchBar({ onSearch, initialValue = '' }: Props) {
  const [value, setValue] = useState(initialValue)

  return (
    <div className="relative w-full">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') onSearch(value) }}
        placeholder="search your reactions..."
        className="w-full rounded-md border border-[#e5e5e5] bg-white py-3 pl-4 pr-12 text-[16px] text-[#1a1c1c] placeholder-[#747878] outline-none transition-colors focus:border-[#4648d4]"
      />
      <button
        onClick={() => onSearch(value)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#747878] hover:text-[#1a1c1c]"
      >
        <Search className="h-5 w-5" />
      </button>
    </div>
  )
}
