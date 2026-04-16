# FallbackProvider: wraps an ordered chain of LLMProviders and advances to the
# next one when upstream returns a quota / rate-limit error.
#
# Invariants:
#   - A provider flagged exhausted by RateLimiter is skipped for the rest of
#     the UTC day (shared across all users because our API key is shared).
#   - User-level daily budget is enforced upstream by check_rate_limit; this
#     wrapper only records usage via RateLimiter.record.
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from app.core.exceptions import LLMError, QuotaExceededError
from app.llm.base import LLMProvider
from app.llm.usage import LLMUsage, current_rate_keys

if TYPE_CHECKING:
    from app.core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class _UsageCapableProvider(Protocol):
    async def complete_with_usage(
        self, prompt: str, system: str | None = None
    ) -> tuple[str, LLMUsage]: ...

    async def embed_with_usage(self, text: str) -> tuple[list[float], LLMUsage]: ...


class FallbackProvider(LLMProvider):
    def __init__(
        self,
        providers: list[tuple[str, _UsageCapableProvider]],
        rate_limiter: RateLimiter,
    ) -> None:
        if not providers:
            raise ValueError("FallbackProvider requires at least one provider")
        self._providers = providers
        self._rate_limiter = rate_limiter

    async def complete(self, prompt: str, system: str | None = None) -> str:
        keys = current_rate_keys.get()
        last_error: Exception | None = None
        for name, provider in self._providers:
            if await self._rate_limiter.is_provider_exhausted(name):
                continue
            try:
                text, usage = await provider.complete_with_usage(prompt, system)
            except QuotaExceededError as exc:
                await self._rate_limiter.mark_provider_exhausted(name)
                logger.warning(
                    "llm_upstream_quota_exhausted",
                    extra={
                        "provider": name,
                        "user_id": keys[0] if keys else None,
                    },
                )
                last_error = exc
                continue
            if keys:
                await self._rate_limiter.record(keys[0], keys[1], usage)
            return text
        raise LLMError(
            "All configured LLM providers have hit their upstream quota."
        ) from last_error

    async def embed(self, text: str) -> list[float]:
        keys = current_rate_keys.get()
        last_error: Exception | None = None
        for name, provider in self._providers:
            if await self._rate_limiter.is_provider_exhausted(name):
                continue
            try:
                values, usage = await provider.embed_with_usage(text)
            except QuotaExceededError as exc:
                await self._rate_limiter.mark_provider_exhausted(name)
                logger.warning(
                    "llm_upstream_quota_exhausted",
                    extra={
                        "provider": name,
                        "user_id": keys[0] if keys else None,
                        "op": "embed",
                    },
                )
                last_error = exc
                continue
            if keys:
                await self._rate_limiter.record(keys[0], keys[1], usage)
            return values
        raise LLMError(
            "All configured LLM providers have hit their upstream quota."
        ) from last_error
