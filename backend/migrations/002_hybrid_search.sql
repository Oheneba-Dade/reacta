-- Full-text search on transcript chunks (primary lexical signal)
ALTER TABLE transcript_embeddings
  ADD COLUMN IF NOT EXISTS chunk_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', transcript_chunk)) STORED;

CREATE INDEX IF NOT EXISTS idx_transcript_chunk_gin
  ON transcript_embeddings USING GIN(chunk_tsv);

-- Full-text search on clip description (secondary lexical signal)
ALTER TABLE clips
  ADD COLUMN IF NOT EXISTS description_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', COALESCE(description, ''))) STORED;

CREATE INDEX IF NOT EXISTS idx_clips_description_gin
  ON clips USING GIN(description_tsv);
