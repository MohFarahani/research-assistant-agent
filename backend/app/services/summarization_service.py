from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import settings
from app.llm.base import LLMProvider

_SUMMARY_SYSTEM = (
    "You are a research document summarizer. "
    "Provide a clear, concise, well-structured summary."
)

_MAX_CHARS = 80_000


class SummarizationService:
    def __init__(self, qdrant: AsyncQdrantClient, llm: LLMProvider) -> None:
        self._qdrant = qdrant
        self._llm = llm

    async def summarize(self, doc_id: str) -> str:
        results, _ = await self._qdrant.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
            limit=500,
            with_payload=True,
        )

        if not results:
            return "Document has no content to summarize."

        results.sort(
            key=lambda r: int(r.payload.get("chunk_index", 0)) if r.payload else 0
        )

        full_text = "\n\n".join(
            str(r.payload.get("text", "")) for r in results if r.payload
        )[:_MAX_CHARS]

        prompt = (
            "Please provide a comprehensive summary of the following document:\n\n"
            + full_text
        )
        return await self._llm.complete(prompt, system=_SUMMARY_SYSTEM)
