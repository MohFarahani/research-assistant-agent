# Tests for POST /documents/upload and GET /documents endpoints.
import io
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import documents
from app.core.dependencies import get_db, get_llm, get_qdrant
from app.llm.base import LLMProvider
from app.models.document import Document


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(documents.router)
    return app


def _fake_document(
    filename: str = "test.pdf",
    status: str = "processing",
    page_count: int | None = None,
) -> Document:
    doc = MagicMock(spec=Document)
    doc.id = uuid.uuid4()
    doc.filename = filename
    doc.status = status
    doc.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    doc.page_count = page_count
    return doc


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


class TestUploadDocument:
    async def test_upload_pdf_returns_202(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        doc_id = uuid.uuid4()
        mock_service = MagicMock()
        mock_service.create_pending = AsyncMock(return_value=doc_id)

        with (
            patch("app.api.documents.DocumentService", return_value=mock_service),
            patch("app.api.documents._run_ingestion", new=AsyncMock()),
        ):
            async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
                response = await client.post(
                    "/documents/upload",
                    files={
                        "file": (
                            "report.pdf",
                            io.BytesIO(b"%PDF-fake"),
                            "application/pdf",
                        )
                    },
                )

        assert response.status_code == 202
        data = response.json()
        assert data["filename"] == "report.pdf"
        assert data["status"] == "processing"
        assert data["id"] == str(doc_id)

    async def test_upload_non_pdf_returns_422(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
            response = await client.post(
                "/documents/upload",
                files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
            )

        assert response.status_code == 422
        assert "PDF" in response.json()["detail"]

    async def test_upload_no_extension_returns_422(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
            response = await client.post(
                "/documents/upload",
                files={
                    "file": (
                        "nodotpdf",
                        io.BytesIO(b"%PDF-"),
                        "application/octet-stream",
                    )
                },
            )

        assert response.status_code == 422


class TestListDocuments:
    async def test_list_returns_documents(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        docs = [
            _fake_document("a.pdf", "ready", 5),
            _fake_document("b.pdf", "processing"),
        ]
        mock_service = MagicMock()
        mock_service.list_documents = AsyncMock(return_value=docs)

        with patch("app.api.documents.DocumentService", return_value=mock_service):
            async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
                response = await client.get("/documents")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["filename"] == "a.pdf"
        assert data[0]["status"] == "ready"
        assert data[0]["page_count"] == 5
        assert data[1]["filename"] == "b.pdf"

    async def test_list_empty(
        self,
        mock_db: AsyncSession,
        mock_qdrant: AsyncQdrantClient,
        mock_llm: LLMProvider,
    ) -> None:
        mock_service = MagicMock()
        mock_service.list_documents = AsyncMock(return_value=[])

        with patch("app.api.documents.DocumentService", return_value=mock_service):
            async with _build_client(mock_db, mock_qdrant, mock_llm) as client:
                response = await client.get("/documents")

        assert response.status_code == 200
        assert response.json() == []
