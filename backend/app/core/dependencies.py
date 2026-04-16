from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.rate_limiter import get_rate_limiter
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider

_engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
_async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    _engine, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session() as session:
        yield session


def get_qdrant() -> AsyncQdrantClient:
    return AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def get_llm() -> LLMProvider:
    return get_llm_provider()


def get_user_id(request: Request) -> str:
    return request.state.user_id  # type: ignore[no-any-return]


def get_client_ip(request: Request) -> str:
    """Return the real client IP, looking through reverse-proxy headers first."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Header may be a comma-separated list: "client, proxy1, proxy2"
        return str(forwarded_for.split(",")[0].strip())
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return str(real_ip.strip())
    return str(request.client.host) if request.client else "unknown"


async def check_rate_limit(request: Request) -> tuple[str, str]:
    """Check rate limit and return (user_id, client_ip) for contextvar injection."""
    user_id: str = request.state.user_id
    client_ip = get_client_ip(request)
    await get_rate_limiter().check(user_id, client_ip)
    return (user_id, client_ip)


DBSession = Annotated[AsyncSession, Depends(get_db)]
QdrantDep = Annotated[AsyncQdrantClient, Depends(get_qdrant)]
LLMDep = Annotated[LLMProvider, Depends(get_llm)]
UserIdDep = Annotated[str, Depends(get_user_id)]
RateLimitCheck = Annotated[tuple[str, str], Depends(check_rate_limit)]
