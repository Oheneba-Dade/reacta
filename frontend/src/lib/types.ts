export interface User {
  id: string
  username: string
  email: string
  created_at: string
}

export interface Tag {
  id: string
  label: string
}

export interface Clip {
  id: string
  owner_id: string
  title: string | null
  description: string | null
  original_filename: string
  file_extension: string
  storage_key: string
  duration_seconds: number
  file_size_bytes: number
  is_public: boolean
  processing_status: 'pending' | 'processing' | 'ready' | 'failed'
  desc_embedding_status: 'pending' | 'completed' | 'failed'
  transcript_status: 'pending' | 'completed' | 'failed'
  tags: Tag[]
  created_at: string
  updated_at: string
}

export interface ClipStatus {
  id: string
  processing_status: 'pending' | 'processing' | 'ready' | 'failed'
  desc_embedding_status: 'pending' | 'completed' | 'failed'
  transcript_status: 'pending' | 'completed' | 'failed'
}

export interface SearchResult {
  clip: Clip
  score: number
  match_source: 'description' | 'transcript' | 'both'
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}
