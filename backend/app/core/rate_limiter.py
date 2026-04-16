# In-memory per-user rate limiter with dual-key (cookie + IP) tracking.
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from app.llm.usage import LLMUsage


def _next_midnight() -> datetime:
    now = datetime.now(UTC)
    tomorrow = now.date() + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=UTC)


@dataclass
class _Bucket:
    tokens_used: int = 0
    requests_used: int = 0
    reset_at: datetime = field(default_factory=_next_midnight)


class RateLimitError(Exception):
    """Raised when a user exceeds their daily budget."""

    def __init__(
        self,
        reset_at: datetime,
        tokens_used: int,
        tokens_limit: int,
        requests_used: int,
        requests_limit: int,
    ) -> None:
        self.reset_at = reset_at
        self.tokens_used = tokens_used
        self.tokens_limit = tokens_limit
        self.requests_used = requests_used
        self.requests_limit = requests_limit
        super().__init__("Rate limit exceeded")


class RateLimiter:
    def __init__(self, daily_token_limit: int, daily_request_limit: int) -> None:
        self._daily_token_limit = daily_token_limit
        self._daily_request_limit = daily_request_limit
        self._user_buckets: dict[str, _Bucket] = {}
        self._ip_buckets: dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()
        # Global (app-wide) flag set: providers whose upstream quota is
        # exhausted for the current UTC day. Shared across all users because
        # the quota is on our single API key per provider.
        self._exhausted_providers: set[str] = set()
        self._exhausted_day: date = datetime.now(UTC).date()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_bucket(self, store: dict[str, _Bucket], key: str) -> _Bucket:
        now = datetime.now(UTC)
        bucket = store.get(key)
        if bucket is None or now >= bucket.reset_at:
            bucket = _Bucket()
            store[key] = bucket
        return bucket

    def _is_over_limit(self, bucket: _Bucket) -> bool:
        return (
            bucket.tokens_used >= self._daily_token_limit
            or bucket.requests_used >= self._daily_request_limit
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check(self, user_id: str, client_ip: str) -> None:
        """Raise ``RateLimitError`` if **either** key is over budget."""
        async with self._lock:
            ub = self._get_bucket(self._user_buckets, user_id)
            ib = self._get_bucket(self._ip_buckets, client_ip)
            # Use the stricter (higher-usage) bucket for the error report
            over = (
                ub
                if self._is_over_limit(ub)
                else ib
                if self._is_over_limit(ib)
                else None
            )
            if over is not None:
                raise RateLimitError(
                    reset_at=over.reset_at,
                    tokens_used=over.tokens_used,
                    tokens_limit=self._daily_token_limit,
                    requests_used=over.requests_used,
                    requests_limit=self._daily_request_limit,
                )

    async def record(self, user_id: str, client_ip: str, usage: LLMUsage) -> None:
        """Record token consumption under **both** keys."""
        async with self._lock:
            for store, key in (
                (self._user_buckets, user_id),
                (self._ip_buckets, client_ip),
            ):
                bucket = self._get_bucket(store, key)
                bucket.tokens_used += usage.total_tokens
                bucket.requests_used += 1

    def _roll_provider_day_if_needed(self) -> None:
        today = datetime.now(UTC).date()
        if today != self._exhausted_day:
            self._exhausted_providers.clear()
            self._exhausted_day = today

    async def mark_provider_exhausted(self, provider: str) -> None:
        """Mark an upstream provider as exhausted for the current UTC day."""
        async with self._lock:
            self._roll_provider_day_if_needed()
            self._exhausted_providers.add(provider)

    async def is_provider_exhausted(self, provider: str) -> bool:
        async with self._lock:
            self._roll_provider_day_if_needed()
            return provider in self._exhausted_providers

    async def get_status(self, user_id: str, client_ip: str) -> dict[str, object]:
        """Return the stricter of the two budgets for display."""
        async with self._lock:
            ub = self._get_bucket(self._user_buckets, user_id)
            ib = self._get_bucket(self._ip_buckets, client_ip)
            worse = ub if ub.tokens_used >= ib.tokens_used else ib
            return {
                "tokens_used": worse.tokens_used,
                "tokens_limit": self._daily_token_limit,
                "requests_used": worse.requests_used,
                "requests_limit": self._daily_request_limit,
                "reset_at": worse.reset_at.isoformat(),
            }


# Module-level singleton ------------------------------------------------

_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter  # noqa: PLW0603
    if _rate_limiter is None:
        from app.config import settings

        _rate_limiter = RateLimiter(
            daily_token_limit=settings.rate_limit_daily_tokens,
            daily_request_limit=settings.rate_limit_daily_requests,
        )
    return _rate_limiter
