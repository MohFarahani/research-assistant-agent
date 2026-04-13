# Research Assistant Agent

A web-based RAG research assistant. Users upload PDFs, ask questions, get LLM answers with clickable citation badges that open the exact retrieved source chunk in a side panel.

## Monorepo Layout

```
backend/    # Python 3.12, FastAPI, uv — see backend/CLAUDE.md
frontend/   # Next.js 15 App Router, pnpm — see frontend/CLAUDE.md
docker/     # Dockerfiles for backend and frontend
.github/    # CI workflows (backend-ci.yml, frontend-ci.yml)
```

## Architecture Overview

### Backend (backend/app/)
- `api/`          — Thin route handlers only (no business logic)
- `services/`     — Business logic layer (RAG pipeline, PDF parsing, summarization)
- `llm/`          — Strategy pattern: abstract LLMProvider + Anthropic/OpenAI implementations + factory
- `repositories/` — Data access layer (SQLAlchemy ORM; no raw SQL elsewhere)
- `schemas/`      — Pydantic models for API request/response (boundary layer)
- `models/`       — SQLAlchemy ORM models (DB tables only — separate from schemas)
- `core/`         — Shared exceptions and FastAPI dependency injection helpers

### Frontend (frontend/src/)
- `app/`          — Next.js App Router pages (layout.tsx + page.tsx)
- `components/`   — UI components grouped by domain (layout/, chat/, documents/, source/)
- `services/`     — API client functions (no fetch() directly in components)
- `hooks/`        — React Query hooks for server state
- `store/`        — Zustand store for client UI state (source panel open/close)
- `types/`        — Shared TypeScript interfaces

### UI Layout (3-panel)
```
┌─────────────────┬──────────────────────────┬────────────────────┐
│  Left Sidebar   │      Chat Area           │   Source Panel     │
│  (Documents)    │  (RAG conversation)      │  (slides open on   │
│                 │                          │   citation click)  │
│  • Upload btn   │  User msgs → right       │                    │
│  • Doc list     │  AI msgs ← left          │  Exact retrieved   │
│  • Active state │  [Doc 1, Page 4] badges  │  chunk, sentences  │
│                 │  Sticky input bar        │  highlighted       │
└─────────────────┴──────────────────────────┴────────────────────┘
```

### Key Data Flow
1. User uploads PDF → `document_service` extracts text, ingests chunks into Qdrant
2. User sends message → `chat_service` retrieves chunks from Qdrant → LLM answers with citations
3. User clicks `[Doc 1, Page 4]` badge → `source_service` returns raw chunk + highlight ranges → SourcePanel opens

## Infrastructure (Docker)

| Service    | Image                  | Port | Purpose                        |
|------------|------------------------|------|--------------------------------|
| `backend`  | docker/backend.Dockerfile | 8000 | FastAPI app                 |
| `frontend` | docker/frontend.Dockerfile | 3000 | Next.js app                |
| `postgres` | postgres:16-alpine     | 5432 | Document/citation metadata     |
| `qdrant`   | qdrant/qdrant          | 6333 | Vector store for RAG retrieval |

## LLM Provider (Strategy Pattern)
Controlled by `LLM_PROVIDER` env var (`"anthropic"` or `"openai"`).
All LLM calls must go through `backend/app/llm/factory.py` — never import `anthropic`/`openai` SDKs directly in services.

## Environment Variables
Copy `.env.example` → `.env`. Key vars:
- `LLM_PROVIDER` — `anthropic` or `openai`
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
- `DATABASE_URL` — PostgreSQL connection string
- `QDRANT_HOST` / `QDRANT_PORT`

## Repo Rules
- Branching: GitHub Flow — `feature/<name>` branches off `main`, PRs required
- Commit style: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`)
- Never commit `.env` files
- Never bypass git hooks (`--no-verify`)
- CI must pass before merging any PR
- Branch protection: no direct push to `main`
