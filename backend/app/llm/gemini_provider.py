# Google Gemini implementation of LLMProvider.
# Uses the google-genai SDK. Free tier: 15 RPM, 1M context window.
from google import genai
from google.genai import types

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, embedding_model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._embedding_model = embedding_model

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
            return response.text or ""
        except Exception as exc:
            raise LLMError(str(exc)) from exc

    async def embed(self, text: str) -> list[float]:
        try:
            result = await self._client.aio.models.embed_content(
                model=self._embedding_model,
                contents=text,
            )
            # result.embeddings is a list of ContentEmbedding; take the first
            return list(result.embeddings[0].values)
        except Exception as exc:
            raise LLMError(str(exc)) from exc
