# Claude (Anthropic) implementation of LLMProvider.
import anthropic

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        openai_api_key: str,
        embedding_model: str,
    ) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        # Anthropic has no embedding API; delegate to OpenAI
        self._openai_api_key = openai_api_key
        self._embedding_model = embedding_model

    async def complete(self, prompt: str, system: str | None = None) -> str:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
                system=system if system is not None else anthropic.NOT_GIVEN,
            )
            block = response.content[0]
            return block.text if hasattr(block, "text") else ""
        except Exception as exc:
            raise LLMError(str(exc)) from exc

    async def embed(self, text: str) -> list[float]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._openai_api_key)
        try:
            result = await client.embeddings.create(
                model=self._embedding_model, input=text
            )
            return list(result.data[0].embedding)
        except Exception as exc:
            raise LLMError(str(exc)) from exc
