# Google Gemini implementation of LLMProvider.
# Uses the google-genai SDK. Free tier: 15 RPM, 1M context window.
from __future__ import annotations

from typing import TYPE_CHECKING

from google import genai
from google.genai import types

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider
from app.llm.usage import LLMUsage, current_rate_keys

if TYPE_CHECKING:
    from app.core.rate_limiter import RateLimiter


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        embedding_model: str,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._embedding_model = embedding_model
        self._rate_limiter = rate_limiter

    async def complete(self, prompt: str, system: str | None = None) -> str:
        config: types.GenerateContentConfig | None = None
        if system:
            config = types.GenerateContentConfig(system_instruction=system)
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            await self._record_usage(response)
            return response.text or ""
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(str(exc)) from exc

    async def embed(self, text: str) -> list[float]:
        try:
            result = await self._client.aio.models.embed_content(
                model=self._embedding_model,
                contents=text,
            )
            # result.embeddings is a list of ContentEmbedding; take the first
            embeddings = result.embeddings
            if not embeddings:
                raise LLMError("Gemini returned no embeddings")
            values = embeddings[0].values
            if values is None:
                raise LLMError("Gemini embedding values are None")
            await self._record_embed_usage(text)
            return list(values)
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Usage recording
    # ------------------------------------------------------------------

    async def _record_usage(self, response: types.GenerateContentResponse) -> None:
        if not self._rate_limiter:
            return
        keys = current_rate_keys.get()
        if not keys:
            return
        meta = response.usage_metadata
        usage = LLMUsage(
            input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
            output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
        )
        await self._rate_limiter.record(keys[0], keys[1], usage)

    async def _record_embed_usage(self, text: str) -> None:
        if not self._rate_limiter:
            return
        keys = current_rate_keys.get()
        if not keys:
            return
        # Rough estimate: ~1 token per 4 characters
        estimated_tokens = max(len(text) // 4, 1)
        usage = LLMUsage(input_tokens=estimated_tokens, output_tokens=0)
        await self._rate_limiter.record(keys[0], keys[1], usage)
