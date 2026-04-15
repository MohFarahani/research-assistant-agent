import re

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm.base import LLMProvider
from app.schemas.chat import ChatResponse, CitationRef

_CITE_RE = re.compile(r"\[CITE:([a-f0-9\-]+)\]")

_RAG_SYSTEM = (
    "You are a precise research assistant. "
    "Answer using only the provided sources. "
    "Cite using [CITE:chunk_id] tokens inline after each claim."
)

_RAG_PROMPT = """\
SOURCES:
{sources}

QUESTION: {question}

Instructions: Answer the question using only the sources above. \
After each claim insert [CITE:chunk_id] where chunk_id comes from the source header. \
Keep the answer concise and factual."""


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

    async def chat(self, message: str) -> ChatResponse:
        # 1. Embed query
        query_vector = await self._llm.embed(message)

        # 2. Search Qdrant
        try:
            result = await self._qdrant.query_points(
                collection_name=settings.qdrant_collection,
                query=query_vector,
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
                        page=int(p.get("page", 0)),
                    )
                )

        # 6. Strip citation tokens and tidy whitespace
        clean_answer = _CITE_RE.sub("", raw_answer).strip()
        clean_answer = re.sub(r" {2,}", " ", clean_answer)

        return ChatResponse(answer=clean_answer, citations=citations)
