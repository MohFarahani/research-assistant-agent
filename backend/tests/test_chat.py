# Tests for POST /chat RAG endpoint (answer + citations).
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import chat
from app.core.dependencies import get_db, get_llm, get_qdrant
from app.llm.base import LLMProvider
from app.schemas.chat import ChatResponse, CitationRef


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat.router)
    return app


@pytest.fixture()
def mock_llm() -> LLMProvider:
    llm = MagicMock(spec=LLMProvider)
    llm.embed = AsyncMock(return_value=[0.1] * 1536)
    return llm


@pytest.fixture()
def mock_qdrant() -> AsyncQdrantClient:
    return MagicMock(spec=AsyncQdrantClient)


@pytest.fixture()
def mock_db() -> AsyncSession:
    return MagicMock(spec=AsyncSession)


def _build_client(
    mock_db: AsyncSession,
    mock_qdrant: AsyncQdrantClient,
    mock_llm: LLMProvider,
) -> AsyncClient:
    app = _make_app()

    async def override_db() -> Any:
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_qdrant] = lambda: mock_qdrant
    app.dependency_overrides[get_llm] = lambda: mock_llm

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestChatEndpoint:
    async def test_chat_returns_answer_and_citations(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        expected = ChatResponse(
            answer="The boiling point of water is 100°C.",
            citations=[
                CitationRef(
                    doc_id="doc-123",
                    chunk_id="chunk-abc",
                    doc_label="chemistry.pdf",
                    page=3,
                )
            ],
        )
        mock_service = MagicMock()
        mock_service.chat = AsyncMock(return_value=expected)

        with patch("app.api.chat.ChatService", return_value=mock_service):
            async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
                response = await client.post(
                    "/chat", json={"message": "What is the boiling point of water?"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == expected.answer
        assert len(data["citations"]) == 1
        assert data["citations"][0]["chunk_id"] == "chunk-abc"
        assert data["citations"][0]["page"] == 3

    async def test_chat_no_documents_returns_empty_citations(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        expected = ChatResponse(
            answer="No relevant documents found. Please upload a document first.",
            citations=[],
        )
        mock_service = MagicMock()
        mock_service.chat = AsyncMock(return_value=expected)

        with patch("app.api.chat.ChatService", return_value=mock_service):
            async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
                response = await client.post("/chat", json={"message": "anything"})

        assert response.status_code == 200
        data = response.json()
        assert data["citations"] == []
        assert "upload" in data["answer"].lower()

    async def test_chat_missing_message_returns_422(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
            response = await client.post("/chat", json={})

        assert response.status_code == 422

    async def test_chat_passes_message_to_service(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        mock_service = MagicMock()
        mock_service.chat = AsyncMock(return_value=ChatResponse(answer="ok", citations=[]))

        with patch("app.api.chat.ChatService", return_value=mock_service):
            async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
                await client.post("/chat", json={"message": "hello world"})

        mock_service.chat.assert_awaited_once_with("hello world")
