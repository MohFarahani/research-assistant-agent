# OpenAI implementation of LLMProvider.
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, embedding_model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
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
            result = await self._client.embeddings.create(
                model=self._embedding_model, input=text
            )
            return list(result.data[0].embedding)
        except Exception as exc:
            raise LLMError(str(exc)) from exc
