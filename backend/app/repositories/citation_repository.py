import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.citation import Citation


class CitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        doc_id: uuid.UUID,
        chunk_id: str,
        page: int,
        doc_label: str,
    ) -> Citation:
        citation = Citation(
            doc_id=doc_id, chunk_id=chunk_id, page=page, doc_label=doc_label
        )
        self._session.add(citation)
        await self._session.commit()
        await self._session.refresh(citation)
        return citation

    async def get_by_id(self, citation_id: uuid.UUID) -> Citation | None:
        result = await self._session.execute(
            select(Citation).where(Citation.id == citation_id)
        )
        return result.scalar_one_or_none()
