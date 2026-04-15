from fastapi import APIRouter

from app.core.dependencies import DBSession, LLMDep, QdrantDep
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: DBSession,
    qdrant: QdrantDep,
    llm: LLMDep,
) -> ChatResponse:
    service = ChatService(db, qdrant, llm)
    return await service.chat(body.message)
