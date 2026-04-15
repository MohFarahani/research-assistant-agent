# Tests for POST /summarize endpoint.
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from qdrant_client import AsyncQdrantClient

from app.api import summarize
from app.core.dependencies import get_llm, get_qdrant, get_user_id
from app.llm.base import LLMProvider

_TEST_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(summarize.router)
    return app


@pytest.fixture()
def mock_llm() -> LLMProvider:
    llm = MagicMock(spec=LLMProvider)
    llm.complete = AsyncMock(return_value="A concise summary.")
    return llm


@pytest.fixture()
def mock_qdrant() -> AsyncQdrantClient:
    return MagicMock(spec=AsyncQdrantClient)


def _build_client(
    mock_qdrant: AsyncQdrantClient,
    mock_llm: LLMProvider,
) -> AsyncClient:
    app = _make_app()
    app.dependency_overrides[get_qdrant] = lambda: mock_qdrant
    app.dependency_overrides[get_llm] = lambda: mock_llm
    app.dependency_overrides[get_user_id] = lambda: _TEST_USER_ID
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestSummarizeEndpoint:
    async def test_summarize_returns_summary(
        self,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        doc_id = "doc-abc-123"
        mock_service = MagicMock()
        mock_service.summarize = AsyncMock(return_value="This paper covers XYZ.")

        with patch("app.api.summarize.SummarizationService", return_value=mock_service):
            async with _build_client(mock_qdrant, mock_llm) as client:
                response = await client.post("/summarize", json={"doc_id": doc_id})

        assert response.status_code == 200
        data = response.json()
        assert data["doc_id"] == doc_id
        assert data["summary"] == "This paper covers XYZ."

    async def test_summarize_no_content(
        self,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        mock_service = MagicMock()
        mock_service.summarize = AsyncMock(
            return_value="Document has no content to summarize."
        )

        with patch("app.api.summarize.SummarizationService", return_value=mock_service):
            async with _build_client(mock_qdrant, mock_llm) as client:
                response = await client.post("/summarize", json={"doc_id": "empty-doc"})

        assert response.status_code == 200
        assert "no content" in response.json()["summary"]

    async def test_summarize_missing_doc_id_returns_422(
        self,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        async with _build_client(mock_qdrant, mock_llm) as client:
            response = await client.post("/summarize", json={})

        assert response.status_code == 422

    async def test_summarize_passes_doc_id_to_service(
        self,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        mock_service = MagicMock()
        mock_service.summarize = AsyncMock(return_value="summary text")

        with patch("app.api.summarize.SummarizationService", return_value=mock_service):
            async with _build_client(mock_qdrant, mock_llm) as client:
                await client.post("/summarize", json={"doc_id": "my-doc-id"})

        mock_service.summarize.assert_awaited_once_with(
            "my-doc-id", user_id=_TEST_USER_ID
        )
