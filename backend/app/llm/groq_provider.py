# Groq implementation of LLMProvider.
# Uses Groq for fast, free chat completions (Llama 3) and Gemini for embeddings
# (Groq does not offer a public embedding API).
from google import genai
from groq import AsyncGroq
from groq.types.chat import ChatCompletionMessageParam

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider


class GroqProvider(LLMProvider):
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
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise LLMError(str(exc)) from exc

    async def embed(self, text: str) -> list[float]:
        try:
            result = await self._gemini.aio.models.embed_content(
                model=self._embedding_model,
                contents=text,
            )
            embeddings = result.embeddings
            if not embeddings:
                raise LLMError("Gemini returned no embeddings")
            values = embeddings[0].values
            if values is None:
                raise LLMError("Gemini embedding values are None")
            return list(values)
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(str(exc)) from exc
