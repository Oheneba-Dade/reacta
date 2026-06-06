# Architecture Decision Records (ADRs)

This directory contains all major architectural decisions for Reacta.

## Why ADRs Matter

ADRs explain _why_ we chose A over B. They're essential for:

- Understanding design trade-offs
- Onboarding new developers (or AI assistants)
- Reviewing decisions later
- Tracking how the system evolved

## Format

Each ADR:

- Is one file: `ADR-XXX-title.md`
- Has a unique number (ADR-001, ADR-002, etc.)
- Includes: Context, Decision, Rationale, Alternatives, Consequences
- Is immutable (once accepted, don't edit—create new ADR if reversing)

## Current ADRs

_Will be added as project progresses._

To be created:

- ADR-001: Semantic search (not keywords)
- ADR-002: Local embeddings (sentence-transformers)
- ADR-003: Multi-user architecture
- ADR-004: PostgreSQL + pgvector
- ADR-005: Whisper for transcription
- ADR-006: Transcript chunking strategy
- ADR-007: Tag weighting in search
- ADR-008: FastAPI + React split
- ADR-009: Docker deployment
- ADR-010: VPS storage (Phase 1)

## Template
