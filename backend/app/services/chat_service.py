import re
from typing import cast

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm.base import LLMProvider
from app.schemas.chat import ChatResponse, CitationRef

_CITE_RE = re.compile(r"\[CITE:([a-f0-9\-]+)\]")

_RAG_SYSTEM = (
    "You are a precise research assistant. "
    "Answer using ONLY the provided sources. "
    "You MUST cite every claim with [CITE:chunk_id] tokens inline — "
    "where chunk_id is the exact UUID from each source header. "
    "Never omit citations. Never invent information not in the sources."
)

_RAG_PROMPT = """\
SOURCES:
{sources}

QUESTION: {question}

CRITICAL INSTRUCTIONS:
1. Answer using ONLY the sources above — no outside knowledge.
2. After EVERY sentence or claim, insert [CITE:chunk_id] using the
   exact chunk_id UUID from the source header.
3. You MUST include at least one [CITE:...] token in your answer.
4. Keep the answer concise and factual.

EXAMPLE FORMAT:
Targeting is the first step [CITE:abc-123]. Then qualification
occurs [CITE:abc-123].

Now answer:"""


class ChatService:
    def __init__(
        self,
        db: AsyncSession,
        qdrant: AsyncQdrantClient,
        llm: LLMProvider,
    ) -> None:
        self._db = db
        self._qdrant = qdrant
        self._llm = llm

    async def chat(self, message: str, user_id: str) -> ChatResponse:
        # 1. Embed query
        query_vector = await self._llm.embed(message)

        # 2. Search Qdrant — scoped to the current user's documents
        user_filter = Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        )
        try:
            result = await self._qdrant.query_points(
                collection_name=settings.qdrant_collection,
                query=query_vector,
                query_filter=user_filter,
                limit=settings.rag_top_k,
                with_payload=True,
            )
            hits = result.points
        except UnexpectedResponse as exc:
            if exc.status_code in (404, 400):
                return ChatResponse(
                    answer=(
                        "No relevant documents found. Please upload a document first."
                    ),
                    citations=[],
                )
            raise

        if not hits:
            return ChatResponse(
                answer="No relevant documents found. Please upload a document first.",
                citations=[],
            )

        # 3. Build prompt
        source_blocks: list[str] = []
        payload_map: dict[str, dict[str, object]] = {}

        for i, hit in enumerate(hits, 1):
            p = hit.payload or {}
            chunk_id = str(p.get("chunk_id", ""))
            payload_map[chunk_id] = p
            source_blocks.append(
                f"[{i}] ({p.get('doc_label', 'Unknown')}, "
                f"Page {p.get('page', '?')}, chunk_id={chunk_id})\n"
                f"{p.get('text', '')}"
            )

        prompt = _RAG_PROMPT.format(
            sources="\n\n".join(source_blocks),
            question=message,
        )

        # 4. Call LLM
        raw_answer = await self._llm.complete(prompt, system=_RAG_SYSTEM)

        # 5. Parse citations (preserve order, deduplicate)
        found_ids = list(dict.fromkeys(_CITE_RE.findall(raw_answer)))
        citations: list[CitationRef] = []
        for chunk_id in found_ids:
            if chunk_id in payload_map:
                p = payload_map[chunk_id]
                citations.append(
                    CitationRef(
                        doc_id=str(p.get("doc_id", "")),
                        chunk_id=chunk_id,
                        doc_label=str(p.get("doc_label", "")),
                        page=cast(int, p.get("page", 0)),
                    )
                )

        # 6. Strip citation tokens and tidy whitespace
        clean_answer = _CITE_RE.sub("", raw_answer).strip()
        clean_answer = re.sub(r" {2,}", " ", clean_answer)

        return ChatResponse(answer=clean_answer, citations=citations)
