import openai

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model
        self._embedding_model = embedding_model

    async def complete(self, prompt: str, system: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=2048,
            )
            return resp.choices[0].message.content or ""
        except openai.OpenAIError as e:
            raise LLMError(str(e)) from e

    async def embed(self, text: str) -> list[float]:
        try:
            resp = await self._client.embeddings.create(
                model=self._embedding_model,
                input=text,
            )
            return resp.data[0].embedding
        except openai.OpenAIError as e:
            raise LLMError(str(e)) from e
