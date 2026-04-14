import anthropic
import openai

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic provider for chat completions.

    Embeddings are delegated to OpenAI (text-embedding-3-small) because
    the Anthropic SDK does not expose an embedding endpoint.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        openai_api_key: str = "",
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._embed_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self._embedding_model = embedding_model

    async def complete(self, prompt: str, system: str | None = None) -> str:
        try:
            msg = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=system or "You are a helpful research assistant.",
                messages=[{"role": "user", "content": prompt}],
            )
            block = msg.content[0]
            if block.type == "text":
                return block.text
            return ""
        except anthropic.APIError as e:
            raise LLMError(str(e)) from e

    async def embed(self, text: str) -> list[float]:
        try:
            resp = await self._embed_client.embeddings.create(
                model=self._embedding_model,
                input=text,
            )
            return resp.data[0].embedding
        except openai.OpenAIError as e:
            raise LLMError(str(e)) from e
