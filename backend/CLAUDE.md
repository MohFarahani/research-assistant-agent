# Backend — Python / FastAPI

## Stack
Python 3.12+, FastAPI, uv, SQLAlchemy, Alembic, PyMuPDF, Qdrant, Anthropic SDK, OpenAI SDK

## Commands
- Install: `uv sync`
- Dev server: `uv run uvicorn app.main:app --reload`
- Tests: `uv run pytest`
- Lint: `uv run ruff check . && uv run ruff format .`
- Type check: `uv run mypy app/`
- Migrations: `uv run alembic upgrade head`

## Architecture Rules
- Route handlers (api/) must be thin — logic goes in services/
- LLM calls go only through app/llm/factory.py — never import anthropic/openai directly in services
- All DB access goes through repositories/ — no raw queries in services
- schemas/ = Pydantic models (API boundary); models/ = SQLAlchemy ORM (DB tables only)
- All new code requires type annotations (mypy enforced)
- Every new endpoint needs a test in tests/

## Do Not
- No business logic in api/ route handlers
- No direct LLM SDK imports outside app/llm/
- No raw SQL — use SQLAlchemy ORM
