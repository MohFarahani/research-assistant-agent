from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.rate_limiter import get_rate_limiter
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.llm.usage import current_rate_keys

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


async def check_rate_limit(request: Request) -> None:
    user_id: str = request.state.user_id
    client_ip = request.client.host if request.client else "unknown"
    current_rate_keys.set((user_id, client_ip))
    await get_rate_limiter().check(user_id, client_ip)


DBSession = Annotated[AsyncSession, Depends(get_db)]
QdrantDep = Annotated[AsyncQdrantClient, Depends(get_qdrant)]
LLMDep = Annotated[LLMProvider, Depends(get_llm)]
UserIdDep = Annotated[str, Depends(get_user_id)]
RateLimitCheck = Annotated[None, Depends(check_rate_limit)]
