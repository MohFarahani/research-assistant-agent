import math

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Condition,
    FieldCondition,
    Filter,
    MatchValue,
)

from app.config import settings
from app.core.exceptions import ChunkNotFoundError
from app.llm.base import LLMProvider
from app.schemas.source import HighlightRange, SourceChunkResponse

# Minimum cosine similarity to consider a window worth highlighting.
# Windows below this score are not shown — the chunk may simply be
# weakly related to this specific query phrase.
_SEMANTIC_THRESHOLD = 0.55

# Sliding window size in words. Chosen to be long enough to carry
# semantic meaning but short enough to pinpoint the relevant phrase.
_WINDOW_WORDS = 20
_WINDOW_STEP = 10  # step between windows (50% overlap)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _word_windows(text: str) -> list[tuple[str, int, int]]:
    """
    Slide a fixed-size word window over `text`.
    Returns (window_text, char_start, char_end) tuples.
    Language-agnostic: splits only on whitespace.
    """
    # Build (word, char_start) pairs
    words: list[tuple[str, int]] = []
    i = 0
    while i < len(text):
        # Skip whitespace
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            break
        # Collect word
        j = i
        while j < len(text) and not text[j].isspace():
            j += 1
        words.append((text[i:j], i))
        i = j

    if not words:
        return []

    windows: list[tuple[str, int, int]] = []
    n = len(words)
    step = max(1, _WINDOW_STEP)
    size = min(_WINDOW_WORDS, n)

    for start_idx in range(0, n, step):
        end_idx = min(start_idx + size, n)
        window_words = words[start_idx:end_idx]
        char_start = window_words[0][1]
        last_word, last_start = window_words[-1]
        char_end = last_start + len(last_word)
        window_text = text[char_start:char_end]
        windows.append((window_text, char_start, char_end))
        if end_idx == n:
            break

    return windows


class SourceService:
    def __init__(self, qdrant: AsyncQdrantClient, llm: LLMProvider) -> None:
        self._qdrant = qdrant
        self._llm = llm

    async def get_chunk(
        self, doc_id: str, chunk_id: str, query: str = "", user_id: str = ""
    ) -> SourceChunkResponse:
        must: list[Condition] = [
            FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id)),
            FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
        ]
        if user_id:
            must.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
        results, _ = await self._qdrant.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(must=must),
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

    async def _compute_highlights(self, text: str, query: str) -> list[HighlightRange]:
        if not query or not text:
            return []

        windows = _word_windows(text)
        if not windows:
            return []

        try:
            query_vec = await self._llm.embed(query)
            scored: list[tuple[float, int, int]] = []
            for win_text, start, end in windows:
                win_vec = await self._llm.embed(win_text)
                similarity = _cosine(query_vec, win_vec)
                scored.append((similarity, start, end))

            if not scored:
                return []

            scored.sort(key=lambda x: -x[0])
            best_score = scored[0][0]

            # Only highlight if the best window clears the threshold
            if best_score < _SEMANTIC_THRESHOLD:
                return []

            # Return windows within 0.03 of the best (covers adjacent overlap windows)
            top = [s for s in scored if best_score - s[0] <= 0.03][:3]
            return [HighlightRange(start=s[1], end=s[2]) for s in top]

        except Exception:
            return []
