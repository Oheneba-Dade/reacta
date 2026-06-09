'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/hooks/useAuth'

export function AuthForm() {
  const router = useRouter()
  const { login, register } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      router.push('/library')
    } catch {
      setError('invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register(username, email, password)
      await login(email, password)
      router.push('/library')
    } catch {
      setError('registration failed — username or email already in use')
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'w-full rounded-md border border-[#e5e5e5] px-3 py-2 text-[16px] md:text-[14px] text-[#1a1c1c] placeholder-[#747878] outline-none transition-colors focus:border-[#4648d4]'
  const labelClass = 'block mb-1 text-[12px] font-medium lowercase tracking-[0.02em] text-[#1a1c1c]'

  return (
    <Tabs defaultValue="login" className="w-full" onValueChange={() => setError(null)}>
      <TabsList className="mb-6 flex w-full gap-0 rounded-none border-b border-[#e5e5e5] bg-transparent p-0">
        {['login', 'register'].map((tab) => (
          <TabsTrigger
            key={tab}
            value={tab}
            className="flex-1 rounded-none border-b-2 border-transparent pb-3 text-[14px] lowercase text-[#747878] data-[state=active]:border-[#4648d4] data-[state=active]:text-[#1a1c1c] data-[state=active]:shadow-none bg-transparent"
          >
            {tab}
          </TabsTrigger>
        ))}
      </TabsList>

      <TabsContent value="login">
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className={labelClass}>email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required className={inputClass} />
          </div>
          {error && <p className="text-[14px] text-[#ba1a1a]">{error}</p>}
          <button type="submit" disabled={loading} className="w-full rounded-md bg-black py-2.5 text-[14px] font-medium lowercase text-white disabled:opacity-40">
            {loading ? 'signing in...' : 'sign in'}
          </button>
        </form>
      </TabsContent>

      <TabsContent value="register">
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className={labelClass}>username</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="yourname" required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required className={inputClass} />
          </div>
          {error && <p className="text-[14px] text-[#ba1a1a]">{error}</p>}
          <button type="submit" disabled={loading} className="w-full rounded-md bg-black py-2.5 text-[14px] font-medium lowercase text-white disabled:opacity-40">
            {loading ? 'creating account...' : 'create account'}
          </button>
        </form>
      </TabsContent>
    </Tabs>
  )
}
