import re

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import settings
from app.core.exceptions import ChunkNotFoundError
from app.schemas.source import HighlightRange, SourceChunkResponse

_SENTENCE_SPLIT = re.compile(r"[^.?!]+[.?!]?")

# Common English stop words to exclude from keyword matching
_STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "and",
    "or",
    "but",
    "if",
    "then",
    "there",
    "what",
    "which",
    "who",
    "how",
    "when",
    "where",
    "why",
    "not",
    "no",
    "so",
    "up",
    "out",
    "about",
    "into",
    "than",
    "i",
    "you",
    "he",
    "she",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "his",
    "their",
}


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

        # Extract meaningful keywords (strip stop words, keep tokens >= 3 chars)
        raw_words = re.findall(r"[a-zA-Z0-9]+", query.lower())
        keywords = [w for w in raw_words if w not in _STOP_WORDS and len(w) >= 3]

        if not keywords:
            return []

        text_lower = text.lower()

        # Strategy 1: find sentences that contain the most keyword hits
        scored: list[tuple[int, int, int]] = []
        for m in _SENTENCE_SPLIT.finditer(text):
            sentence_lower = m.group().lower()
            hits = sum(1 for kw in keywords if kw in sentence_lower)
            if hits > 0:
                scored.append((hits, m.start(), m.end()))

        if scored:
            scored.sort(key=lambda x: -x[0])
            best_score = scored[0][0]
            # Return all sentences that match the best score (up to 3)
            top_sentences = [s for s in scored if s[0] == best_score][:3]
            return [HighlightRange(start=s[1], end=s[2]) for s in top_sentences]

        # Strategy 2 (fallback): directly highlight keyword occurrences in the text
        ranges: list[HighlightRange] = []
        for kw in keywords:
            start = 0
            while True:
                pos = text_lower.find(kw, start)
                if pos == -1:
                    break
                ranges.append(HighlightRange(start=pos, end=pos + len(kw)))
                start = pos + len(kw)

        return ranges
