import math
import re

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import settings
from app.core.exceptions import ChunkNotFoundError
from app.llm.base import LLMProvider
from app.schemas.source import HighlightRange, SourceChunkResponse

# Split on punctuation + whitespace + uppercase (real sentence boundary).
# Avoids splitting "3. Application" or "DA99 (pressing)." mid-item.
_SENTENCE_SPLIT = re.compile(r"(?<=[.?!])\s+(?=[A-Z])")

# Minimum cosine similarity for a sentence to be highlighted semantically
_SEMANTIC_THRESHOLD = 0.75

# Common English stop words to exclude from keyword fallback
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


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class SourceService:
    def __init__(self, qdrant: AsyncQdrantClient, llm: LLMProvider) -> None:
        self._qdrant = qdrant
        self._llm = llm

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

        highlight_ranges = await self._compute_highlights(text, query)

        return SourceChunkResponse(
            doc_id=doc_id,
            chunk_id=chunk_id,
            page=page,
            text=text,
            doc_label=doc_label,
            highlight_ranges=highlight_ranges,
        )

    def _split_sentences(self, text: str) -> list[tuple[str, int, int]]:
        """Split text into (sentence, start, end) tuples, preserving char positions."""
        parts: list[tuple[str, int, int]] = []
        pos = 0
        for seg in _SENTENCE_SPLIT.split(text):
            seg_stripped = seg.strip()
            # Skip trivially short fragments (numbers, punctuation, etc.)
            if len(seg_stripped) < 10:
                pos += len(seg)
                # Account for the whitespace consumed by the split
                while pos < len(text) and text[pos] in " \t\n":
                    pos += 1
                continue
            start = text.find(seg_stripped, pos)
            if start == -1:
                start = pos
            end = start + len(seg_stripped)
            parts.append((seg_stripped, start, end))
            pos = end
        return parts

    async def _compute_highlights(self, text: str, query: str) -> list[HighlightRange]:
        if not query:
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        # --- Strategy 1: semantic similarity via embeddings ---
        try:
            query_vec = await self._llm.embed(query)
            scored: list[tuple[float, int, int]] = []
            for sent_text, start, end in sentences:
                sent_vec = await self._llm.embed(sent_text)
                similarity = _cosine(query_vec, sent_vec)
                scored.append((similarity, start, end))

            if scored:
                scored.sort(key=lambda x: -x[0])
                best_score = scored[0][0]
                # Include all sentences within 0.05 of the best score (up to 3)
                top = [s for s in scored if best_score - s[0] <= 0.05][:3]
                return [HighlightRange(start=s[1], end=s[2]) for s in top]

        except Exception:
            pass  # Fall through to lexical fallback

        # --- Strategy 2: lexical fallback (keyword overlap) ---
        raw_words = re.findall(r"[a-zA-Z0-9]+", query.lower())
        keywords = [w for w in raw_words if w not in _STOP_WORDS and len(w) >= 3]
        if not keywords:
            return []

        lex_scored: list[tuple[int, int, int]] = []
        for sent_text, start, end in sentences:
            sentence_lower = sent_text.lower()
            hits = sum(1 for kw in keywords if kw in sentence_lower)
            if hits > 0:
                lex_scored.append((hits, start, end))

        if lex_scored:
            lex_scored.sort(key=lambda x: -x[0])
            best_score_lex = lex_scored[0][0]
            return [
                HighlightRange(start=s[1], end=s[2])
                for s in lex_scored
                if s[0] == best_score_lex
            ][:3]

        return []
