# Research Assistant Agent

A web-based research assistant powered by a configurable LLM (Claude or OpenAI). Upload PDFs, ask questions via RAG, manage citations, and summarize papers.

## Stack
- **Backend**: Python 3.12+, FastAPI, uv, PostgreSQL, Qdrant
- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, pnpm, TailwindCSS

## Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [pnpm](https://pnpm.io/installation)

### Local development

```bash
# 1. Copy and fill in environment variables
cp .env.example .env

# 2. Start infrastructure (PostgreSQL + Qdrant)
docker-compose up postgres qdrant -d

# 3. Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload

# 4. Frontend (new terminal)
cd frontend
pnpm install
pnpm dev
```

Or run everything via Docker:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
docker-compose up
```

## Project Structure
```
backend/    # FastAPI application (uv)
frontend/   # Next.js 15 application (pnpm)
docker/     # Dockerfiles
.github/    # CI workflows
```
