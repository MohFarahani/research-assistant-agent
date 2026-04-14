from fastapi import APIRouter

from app.core.dependencies import LLMDep, QdrantDep
from app.schemas.summarization import SummarizeRequest, SummarizeResponse
from app.services.summarization_service import SummarizationService

router = APIRouter(prefix="/summarize", tags=["summarize"])


@router.post("", response_model=SummarizeResponse)
async def summarize(
    body: SummarizeRequest,
    qdrant: QdrantDep,
    llm: LLMDep,
) -> SummarizeResponse:
    service = SummarizationService(qdrant, llm)
    summary = await service.summarize(body.doc_id)
    return SummarizeResponse(doc_id=body.doc_id, summary=summary)
