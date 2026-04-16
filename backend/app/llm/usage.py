# Token usage tracking for rate limiting.
from __future__ import annotations

import contextvars
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LLMUsage:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# (user_id, client_ip) — set by the rate-limit dependency, read by the provider.
current_rate_keys: contextvars.ContextVar[tuple[str, str] | None] = (
    contextvars.ContextVar("llm_current_rate_keys", default=None)
)
