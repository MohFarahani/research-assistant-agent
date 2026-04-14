# Factory: reads LLM_PROVIDER from config and returns the correct LLMProvider instance.
from functools import lru_cache

from app.llm.base import LLMProvider


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    from app.config import settings

    if settings.llm_provider == "gemini":
        from app.llm.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            embedding_model=settings.gemini_embedding_model,
        )

    if settings.llm_provider == "groq":
        from app.llm.groq_provider import GroqProvider

        return GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            gemini_api_key=settings.gemini_api_key,
            embedding_model=settings.gemini_embedding_model,
        )

    if settings.llm_provider == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            openai_api_key=settings.openai_api_key,
            embedding_model=settings.openai_embedding_model,
        )

    if settings.llm_provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}. Choose from: gemini, groq, anthropic, openai")
