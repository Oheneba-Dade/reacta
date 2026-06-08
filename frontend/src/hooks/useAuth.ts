'use client'

import { useState, useEffect } from 'react'
import { auth as authApi } from '@/lib/api'
import { clearTokens, isAuthenticated, saveTokens } from '@/lib/auth'

export function useAuth() {
  const [authed, setAuthed] = useState(false)

  useEffect(() => {
    setAuthed(isAuthenticated())
  }, [])

  async function login(email: string, password: string) {
    const tokens = await authApi.login(email, password)
    saveTokens(tokens.access_token, tokens.refresh_token)
    setAuthed(true)
    return tokens
  }

  async function register(username: string, email: string, password: string) {
    return authApi.register(username, email, password)
  }

  function logout() {
    clearTokens()
    setAuthed(false)
    window.location.href = '/'
  }

  return { authed, login, register, logout }
}
