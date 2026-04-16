# Google Gemini implementation of LLMProvider.
# Uses the google-genai SDK. Free tier: 15 RPM, 1M context window.
from __future__ import annotations

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.core.exceptions import LLMError, QuotaExceededError
from app.llm.base import LLMProvider
from app.llm.usage import LLMUsage


def _is_quota_error(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.ClientError):
        if getattr(exc, "code", None) == 429:
            return True
        status = getattr(exc, "status", None)
        if isinstance(status, str) and "RESOURCE_EXHAUSTED" in status:
            return True
    return False


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        embedding_model: str,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._embedding_model = embedding_model

    async def complete(self, prompt: str, system: str | None = None) -> str:
        text, _ = await self.complete_with_usage(prompt, system)
        return text

    async def embed(self, text: str) -> list[float]:
        values, _ = await self.embed_with_usage(text)
        return values

    async def complete_with_usage(
        self, prompt: str, system: str | None = None
    ) -> tuple[str, LLMUsage]:
        config: types.GenerateContentConfig | None = None
        if system:
            config = types.GenerateContentConfig(system_instruction=system)
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            if _is_quota_error(exc):
                raise QuotaExceededError(str(exc)) from exc
            raise LLMError(str(exc)) from exc

        meta = response.usage_metadata
        usage = LLMUsage(
            input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
            output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
        )
        return response.text or "", usage

    async def embed_with_usage(self, text: str) -> tuple[list[float], LLMUsage]:
        try:
            result = await self._client.aio.models.embed_content(
                model=self._embedding_model,
                contents=text,
            )
        except Exception as exc:
            if _is_quota_error(exc):
                raise QuotaExceededError(str(exc)) from exc
            raise LLMError(str(exc)) from exc

        embeddings = result.embeddings
        if not embeddings:
            raise LLMError("Gemini returned no embeddings")
        values = embeddings[0].values
        if values is None:
            raise LLMError("Gemini embedding values are None")
        # Gemini doesn't return token counts for embeddings; rough estimate.
        estimated_tokens = max(len(text) // 4, 1)
        usage = LLMUsage(input_tokens=estimated_tokens, output_tokens=0)
        return list(values), usage
