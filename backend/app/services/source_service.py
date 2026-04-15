import re

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import settings
from app.core.exceptions import ChunkNotFoundError
from app.schemas.source import HighlightRange, SourceChunkResponse

_SENTENCE_SPLIT = re.compile(r"[^.?!]+[.?!]?")


class SourceService:
    def __init__(self, qdrant: AsyncQdrantClient) -> None:
        self._qdrant = qdrant

    async def get_chunk(
        self, doc_id: str, chunk_id: str, query: str = ""
    ) -> SourceChunkResponse:
        results, _ = await self._qdrant.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id)),
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                ]
            ),
            limit=1,
            with_payload=True,
        )

        if not results:
            raise ChunkNotFoundError(chunk_id)

        payload = results[0].payload or {}
        text = str(payload.get("text", ""))
        page = int(payload.get("page", 0))
        doc_label = str(payload.get("doc_label", ""))

        highlight_ranges = self._compute_highlights(text, query)

        return SourceChunkResponse(
            doc_id=doc_id,
            chunk_id=chunk_id,
            page=page,
            text=text,
            doc_label=doc_label,
            highlight_ranges=highlight_ranges,
        )

    def _compute_highlights(self, text: str, query: str) -> list[HighlightRange]:
        if not query:
            return []

        query_words = set(query.lower().split())
        scored: list[tuple[int, int, int]] = []

        for m in _SENTENCE_SPLIT.finditer(text):
            sentence_words = set(m.group().lower().split())
            overlap = len(query_words & sentence_words)
            scored.append((overlap, m.start(), m.end()))

        scored.sort(key=lambda x: -x[0])
        top = [s for s in scored[:2] if s[0] > 0]

        return [HighlightRange(start=s[1], end=s[2]) for s in top]
