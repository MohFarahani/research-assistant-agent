# Tests for FallbackProvider and the RateLimiter provider-exhausted flag.
from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import LLMError, QuotaExceededError
from app.core.rate_limiter import RateLimiter
from app.llm.fallback_provider import FallbackProvider
from app.llm.usage import LLMUsage, current_rate_keys


class _FakeProvider:
    """Implements the `_UsageCapableProvider` protocol for tests."""

    def __init__(
        self,
        complete_side_effect: Any = None,
        embed_side_effect: Any = None,
    ) -> None:
        self.complete_with_usage = AsyncMock(side_effect=complete_side_effect)
        self.embed_with_usage = AsyncMock(side_effect=embed_side_effect)


@pytest.fixture()
def limiter() -> RateLimiter:
    return RateLimiter(daily_token_limit=1_000_000, daily_request_limit=1_000)


@pytest.fixture()
def rate_keys() -> Iterator[None]:
    token = current_rate_keys.set(("user-1", "127.0.0.1"))
    yield
    current_rate_keys.reset(token)


class TestFallbackProviderComplete:
    async def test_first_provider_succeeds_second_untouched(
        self, limiter: RateLimiter, rate_keys: None
    ) -> None:
        gemini = _FakeProvider(
            complete_side_effect=[("hello", LLMUsage(input_tokens=10, output_tokens=5))]
        )
        groq = _FakeProvider()
        wrapper = FallbackProvider([("gemini", gemini), ("groq", groq)], limiter)

        result = await wrapper.complete("q")

        assert result == "hello"
        gemini.complete_with_usage.assert_awaited_once()
        groq.complete_with_usage.assert_not_called()

        status = await limiter.get_status("user-1", "127.0.0.1")
        assert status["tokens_used"] == 15
        assert status["requests_used"] == 1

    async def test_quota_error_falls_back_to_next_provider(
        self, limiter: RateLimiter, rate_keys: None
    ) -> None:
        gemini = _FakeProvider(complete_side_effect=QuotaExceededError("429"))
        groq = _FakeProvider(
            complete_side_effect=[("hi", LLMUsage(input_tokens=3, output_tokens=2))]
        )
        wrapper = FallbackProvider([("gemini", gemini), ("groq", groq)], limiter)

        result = await wrapper.complete("q")

        assert result == "hi"
        assert await limiter.is_provider_exhausted("gemini") is True
        assert await limiter.is_provider_exhausted("groq") is False
        status = await limiter.get_status("user-1", "127.0.0.1")
        assert status["tokens_used"] == 5

    async def test_exhausted_provider_is_skipped_on_subsequent_call(
        self, limiter: RateLimiter, rate_keys: None
    ) -> None:
        await limiter.mark_provider_exhausted("gemini")
        gemini = _FakeProvider(complete_side_effect=AssertionError("should be skipped"))
        groq = _FakeProvider(
            complete_side_effect=[("fast", LLMUsage(input_tokens=1, output_tokens=1))]
        )
        wrapper = FallbackProvider([("gemini", gemini), ("groq", groq)], limiter)

        result = await wrapper.complete("q")

        assert result == "fast"
        gemini.complete_with_usage.assert_not_called()
        groq.complete_with_usage.assert_awaited_once()

    async def test_all_providers_exhausted_raises_llm_error(
        self, limiter: RateLimiter, rate_keys: None
    ) -> None:
        gemini = _FakeProvider(complete_side_effect=QuotaExceededError("g"))
        groq = _FakeProvider(complete_side_effect=QuotaExceededError("q"))
        wrapper = FallbackProvider([("gemini", gemini), ("groq", groq)], limiter)

        with pytest.raises(LLMError) as exc_info:
            await wrapper.complete("q")

        assert "upstream quota" in str(exc_info.value).lower()
        assert await limiter.is_provider_exhausted("gemini") is True
        assert await limiter.is_provider_exhausted("groq") is True

    async def test_non_quota_error_is_not_treated_as_fallback(
        self, limiter: RateLimiter, rate_keys: None
    ) -> None:
        gemini = _FakeProvider(complete_side_effect=LLMError("network boom"))
        groq = _FakeProvider(
            complete_side_effect=[("should-not-reach", LLMUsage(0, 0))]
        )
        wrapper = FallbackProvider([("gemini", gemini), ("groq", groq)], limiter)

        with pytest.raises(LLMError):
            await wrapper.complete("q")

        groq.complete_with_usage.assert_not_called()
        assert await limiter.is_provider_exhausted("gemini") is False

    async def test_works_without_rate_keys_context(self, limiter: RateLimiter) -> None:
        # No contextvar set (e.g. background task). Should not record usage
        # but must still return the completion.
        gemini = _FakeProvider(
            complete_side_effect=[("bg", LLMUsage(input_tokens=2, output_tokens=2))]
        )
        groq = _FakeProvider()
        wrapper = FallbackProvider([("gemini", gemini), ("groq", groq)], limiter)

        result = await wrapper.complete("q")

        assert result == "bg"
        # No user keys ⇒ bucket for any user remains at zero.
        status = await limiter.get_status("user-x", "1.2.3.4")
        assert status["tokens_used"] == 0


class TestFallbackProviderEmbed:
    async def test_embed_falls_back_on_quota(
        self, limiter: RateLimiter, rate_keys: None
    ) -> None:
        gemini = _FakeProvider(embed_side_effect=QuotaExceededError("429"))
        groq = _FakeProvider(
            embed_side_effect=[([0.1, 0.2], LLMUsage(input_tokens=4, output_tokens=0))]
        )
        wrapper = FallbackProvider([("gemini", gemini), ("groq", groq)], limiter)

        vec = await wrapper.embed("hello")

        assert vec == [0.1, 0.2]
        assert await limiter.is_provider_exhausted("gemini") is True


class TestRateLimiterProviderFlag:
    async def test_mark_and_read(self, limiter: RateLimiter) -> None:
        assert await limiter.is_provider_exhausted("gemini") is False
        await limiter.mark_provider_exhausted("gemini")
        assert await limiter.is_provider_exhausted("gemini") is True
        assert await limiter.is_provider_exhausted("groq") is False

    async def test_flag_is_independent_of_user_buckets(
        self, limiter: RateLimiter
    ) -> None:
        # Burn a user bucket; provider flag should remain clear.
        await limiter.record("u", "ip", LLMUsage(input_tokens=999, output_tokens=0))
        assert await limiter.is_provider_exhausted("gemini") is False

        # Mark provider exhausted; user bucket should be unaffected.
        await limiter.mark_provider_exhausted("gemini")
        status = await limiter.get_status("u", "ip")
        assert status["tokens_used"] == 999

    async def test_flag_resets_on_new_utc_day(
        self, limiter: RateLimiter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await limiter.mark_provider_exhausted("gemini")
        assert await limiter.is_provider_exhausted("gemini") is True

        # Advance the clock to tomorrow.
        import app.core.rate_limiter as rl

        tomorrow = datetime.now(UTC) + timedelta(days=1)

        class _FakeDatetime:
            @staticmethod
            def now(tz: Any = None) -> datetime:
                return tomorrow

        monkeypatch.setattr(rl, "datetime", _FakeDatetime)

        assert await limiter.is_provider_exhausted("gemini") is False
