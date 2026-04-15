# Abstract base class (interface) for LLM providers.
# Strategy pattern: all providers must implement this interface.
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str | None = None) -> str:
        """Generate a text completion. Returns the model's response as a string."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return a vector embedding for the given text."""
        ...
