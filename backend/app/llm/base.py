from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str | None = None) -> str: ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...
