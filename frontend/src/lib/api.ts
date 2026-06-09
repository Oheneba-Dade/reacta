import axios from 'axios'
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '@/lib/auth'
import type { AuthTokens, Clip, ClipStatus, SearchResult, Tag, User } from '@/lib/types'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let _refreshing: Promise<string> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retried) {
      original._retried = true
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        try {
          if (!_refreshing) {
            _refreshing = axios
              .post<AuthTokens>(
                `${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`,
                { refresh_token: refreshToken }
              )
              .then((r) => {
                saveTokens(r.data.access_token, r.data.refresh_token ?? refreshToken)
                return r.data.access_token
              })
              .finally(() => { _refreshing = null })
          }
          const newToken = await _refreshing
          original.headers.Authorization = `Bearer ${newToken}`
          return api(original)
        } catch {
          // refresh failed — fall through to logout
        }
      }
      clearTokens()
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export const getVideoUrl = (storageKey: string): string => {
  const base = process.env.NEXT_PUBLIC_B2_PUBLIC_URL_BASE ?? ''
  return `${base.replace(/\/$/, '')}/${storageKey}`
}

export const auth = {
  register: (username: string, email: string, password: string) =>
    api.post<User>('/auth/register', { username, email, password }).then((r) => r.data),

  login: (email: string, password: string) =>
    api.post<AuthTokens>('/auth/login', { email, password }).then((r) => r.data),
}

export const clips = {
  list: () => api.get<Clip[]>('/clips').then((r) => r.data),

  get: (id: string) => api.get<Clip>(`/clips/${id}`).then((r) => r.data),

  upload: (formData: FormData) =>
    api
      .post<{ id: string; processing_status: string }>('/clips', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data),

  update: (id: string, body: { title?: string; description?: string; tag_ids?: string[] }) =>
    api.patch<Clip>(`/clips/${id}`, body).then((r) => r.data),

  status: (id: string) => api.get<ClipStatus>(`/clips/${id}/status`).then((r) => r.data),

  delete: (id: string) => api.delete(`/clips/${id}`).then(() => undefined),

  reprocess: (id: string) =>
    api.post<{ id: string; processing_status: string }>(`/clips/${id}/reprocess`).then((r) => r.data),
}

export const search = {
  query: (q: string, limit: number = 3) =>
    api.post<{ results: SearchResult[] }>('/search', { query: q, limit }).then((r) => r.data),
}

export const tags = {
  list: () => api.get<Tag[]>('/tags').then((r) => r.data),
}

export default api
