from fastapi import APIRouter

from app.core.dependencies import (
    DBSession,
    LLMDep,
    QdrantDep,
    RateLimitCheck,
    UserIdDep,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: DBSession,
    qdrant: QdrantDep,
    llm: LLMDep,
    user_id: UserIdDep,
    _rate_check: RateLimitCheck,
) -> ChatResponse:
    service = ChatService(db, qdrant, llm)
    return await service.chat(body.message, user_id=user_id)
