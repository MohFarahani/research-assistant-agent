import re
import uuid
from pathlib import Path

import fitz  # PyMuPDF
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import IngestionError
from app.llm.base import LLMProvider
from app.repositories.document_repository import DocumentRepository

_SENTENCE_RE = re.compile(r"(?<=[.?!])\s+")


class DocumentService:
    def __init__(
        self,
        db: AsyncSession,
        qdrant: AsyncQdrantClient,
        llm: LLMProvider,
    ) -> None:
        self._db = db
        self._qdrant = qdrant
        self._llm = llm
        self._repo = DocumentRepository(db)

    async def create_pending(self, filename: str) -> uuid.UUID:
        doc = await self._repo.create(filename=filename)
        return doc.id

    async def ingest(
        self,
        doc_id: uuid.UUID,
        filename: str,
        file_path: Path,
    ) -> None:
        try:
            await self._ensure_collection()
            pages = self._extract_pages(file_path)
            chunks = self._chunk_pages(doc_id, filename, pages)
            await self._embed_and_upsert(chunks)
            await self._repo.update_status(
                doc_id,
                status="ready",
                page_count=len(pages),
                chunk_count=len(chunks),
            )
        except Exception as exc:
            await self._repo.update_status(doc_id, status="error")
            raise IngestionError(str(exc)) from exc

    async def list_documents(self) -> list:
        return await self._repo.list_all()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    async def _ensure_collection(self) -> None:
        collections = await self._qdrant.get_collections()
        names = [c.name for c in collections.collections]
        if settings.qdrant_collection in names:
            info = await self._qdrant.get_collection(settings.qdrant_collection)
            existing_dim = info.config.params.vectors.size  # type: ignore[union-attr]
            if existing_dim != settings.embedding_dimensions:
                await self._qdrant.delete_collection(settings.qdrant_collection)
            else:
                return
        await self._qdrant.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )

    def _extract_pages(self, file_path: Path) -> list[dict[str, object]]:
        doc = fitz.open(str(file_path))
        pages: list[dict[str, object]] = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()  # type: ignore[attr-defined]
            if text:
                pages.append({"page_num": i + 1, "text": text})
        doc.close()
        return pages

    def _chunk_pages(
        self,
        doc_id: uuid.UUID,
        filename: str,
        pages: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        chunks: list[dict[str, object]] = []
        chunk_index = 0

        for page in pages:
            page_num = page["page_num"]
            raw_text = str(page["text"])
            sentences = [s.strip() for s in _SENTENCE_RE.split(raw_text) if s.strip()]

            current_sentences: list[str] = []
            current_chars = 0
            i = 0

            while i < len(sentences):
                sentence = sentences[i]
                if (
                    current_chars + len(sentence) > settings.chunk_max_chars
                    and current_sentences
                ):
                    chunk_text = " ".join(current_sentences)
                    chunks.append(
                        {
                            "chunk_id": str(uuid.uuid4()),
                            "doc_id": str(doc_id),
                            "doc_label": filename,
                            "page": page_num,
                            "chunk_index": chunk_index,
                            "text": chunk_text,
                        }
                    )
                    chunk_index += 1
                    # Keep overlap sentences
                    current_sentences = current_sentences[
                        -settings.chunk_overlap_sentences :
                    ]
                    current_chars = sum(len(s) for s in current_sentences)
                else:
                    current_sentences.append(sentence)
                    current_chars += len(sentence)
                    i += 1

            if current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    {
                        "chunk_id": str(uuid.uuid4()),
                        "doc_id": str(doc_id),
                        "doc_label": filename,
                        "page": page_num,
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                    }
                )
                chunk_index += 1

        return chunks

    async def _embed_and_upsert(self, chunks: list[dict[str, object]]) -> None:
        points: list[PointStruct] = []
        for chunk in chunks:
            vector = await self._llm.embed(str(chunk["text"]))
            points.append(
                PointStruct(
                    id=str(chunk["chunk_id"]),
                    vector=vector,
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "doc_id": chunk["doc_id"],
                        "doc_label": chunk["doc_label"],
                        "page": chunk["page"],
                        "chunk_index": chunk["chunk_index"],
                        "text": chunk["text"],
                    },
                )
            )

        batch_size = 100
        for i in range(0, len(points), batch_size):
            await self._qdrant.upsert(
                collection_name=settings.qdrant_collection,
                points=points[i : i + batch_size],
            )
