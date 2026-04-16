# Groq implementation of LLMProvider.
# Uses Groq for fast, free chat completions (Llama 3) and Gemini for embeddings
# (Groq does not offer a public embedding API).
from google import genai
from google.genai import errors as genai_errors
from groq import AsyncGroq
from groq import RateLimitError as GroqRateLimitError
from groq.types.chat import ChatCompletionMessageParam

from app.core.exceptions import LLMError, QuotaExceededError
from app.llm.base import LLMProvider
from app.llm.usage import LLMUsage


def _is_gemini_quota_error(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.ClientError):
        if getattr(exc, "code", None) == 429:
            return True
        status = getattr(exc, "status", None)
        if isinstance(status, str) and "RESOURCE_EXHAUSTED" in status:
            return True
    return False


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        gemini_api_key: str,
        embedding_model: str,
    ) -> None:
        self._client = AsyncGroq(api_key=api_key)
        self._gemini = genai.Client(api_key=gemini_api_key)
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
        messages: list[ChatCompletionMessageParam] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=2048,
            )
        except GroqRateLimitError as exc:
            raise QuotaExceededError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        text = response.choices[0].message.content or ""
        meta = response.usage
        usage = LLMUsage(
            input_tokens=getattr(meta, "prompt_tokens", 0) or 0,
            output_tokens=getattr(meta, "completion_tokens", 0) or 0,
        )
        return text, usage

    async def embed_with_usage(self, text: str) -> tuple[list[float], LLMUsage]:
        try:
            result = await self._gemini.aio.models.embed_content(
                model=self._embedding_model,
                contents=text,
            )
        except Exception as exc:
            if _is_gemini_quota_error(exc):
                raise QuotaExceededError(str(exc)) from exc
            raise LLMError(str(exc)) from exc

        embeddings = result.embeddings
        if not embeddings:
            raise LLMError("Gemini returned no embeddings")
        values = embeddings[0].values
        if values is None:
            raise LLMError("Gemini embedding values are None")
        estimated_tokens = max(len(text) // 4, 1)
        usage = LLMUsage(input_tokens=estimated_tokens, output_tokens=0)
        return list(values), usage
