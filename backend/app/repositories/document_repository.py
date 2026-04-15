import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, filename: str, user_id: str) -> Document:
        doc = Document(filename=filename, status="processing", user_id=user_id)
        self._session.add(doc)
        await self._session.commit()
        await self._session.refresh(doc)
        return doc

    async def get_by_id(self, doc_id: uuid.UUID, user_id: str) -> Document | None:
        """Public-facing lookup — enforces ownership."""
        result = await self._session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_by_id_internal(self, doc_id: uuid.UUID) -> Document | None:
        """Internal lookup — no ownership check (used by update_status)."""
        result = await self._session.execute(
            select(Document).where(Document.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, user_id: str) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        doc_id: uuid.UUID,
        status: str,
        page_count: int | None = None,
        chunk_count: int | None = None,
    ) -> Document | None:
        doc = await self._get_by_id_internal(doc_id)
        if doc is None:
            return None
        doc.status = status
        if page_count is not None:
            doc.page_count = page_count
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        await self._session.commit()
        await self._session.refresh(doc)
        return doc
