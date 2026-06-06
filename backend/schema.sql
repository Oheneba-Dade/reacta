-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Lifecycle enums
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'ready', 'failed');
CREATE TYPE transcript_status AS ENUM ('pending', 'completed', 'failed');
CREATE TYPE embedding_status  AS ENUM ('pending', 'completed', 'failed');

-- Users
CREATE TABLE users (
  id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  username      VARCHAR(255) UNIQUE NOT NULL,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at    TIMESTAMPTZ  DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  DEFAULT NOW()
);

-- Clips
CREATE TABLE clips (
  id                    UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id              UUID              NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Display metadata
  title                 VARCHAR(255),
  description           TEXT,
  original_filename     VARCHAR(255)      NOT NULL,
  file_extension        VARCHAR(10)       NOT NULL,

  -- Storage
  storage_key           VARCHAR(500)      NOT NULL,
  duration_seconds      FLOAT             NOT NULL,
  file_size_bytes       BIGINT            NOT NULL,

  -- Visibility
  is_public             BOOLEAN           DEFAULT FALSE,

  -- Processing lifecycle
  processing_status     processing_status NOT NULL DEFAULT 'pending',

  -- Description embedding
  description_embedding VECTOR(384),
  desc_embedding_status embedding_status  DEFAULT 'pending',
  desc_embedding_error  TEXT,

  -- Whisper transcript
  transcript            TEXT,
  transcript_status     transcript_status DEFAULT 'pending',
  transcript_error      TEXT,

  created_at            TIMESTAMPTZ       DEFAULT NOW(),
  updated_at            TIMESTAMPTZ       DEFAULT NOW()
);

-- Global predefined tag vocabulary
CREATE TABLE tag_definitions (
  id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  label      VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ  DEFAULT NOW()
);

-- Which tags are applied to which clip
CREATE TABLE clip_tags (
  clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  tag_id  UUID NOT NULL REFERENCES tag_definitions(id) ON DELETE CASCADE,
  PRIMARY KEY (clip_id, tag_id)
);

-- Transcript chunks for semantic search
CREATE TABLE transcript_embeddings (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  clip_id          UUID        NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  transcript_chunk TEXT        NOT NULL,
  chunk_index      INT         NOT NULL,
  embedding        VECTOR(384),
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Standard indexes
CREATE INDEX idx_clips_owner_id          ON clips(owner_id);
CREATE INDEX idx_clips_is_public         ON clips(is_public);
CREATE INDEX idx_clips_processing_status ON clips(processing_status);
CREATE INDEX idx_clip_tags_clip_id       ON clip_tags(clip_id);
CREATE INDEX idx_clip_tags_tag_id        ON clip_tags(tag_id);
CREATE INDEX idx_transcript_clip_id      ON transcript_embeddings(clip_id);

-- Vector indexes
CREATE INDEX idx_clips_desc_embedding ON clips
  USING hnsw (description_embedding vector_cosine_ops);

CREATE INDEX idx_transcript_embedding ON transcript_embeddings
  USING hnsw (embedding vector_cosine_ops);