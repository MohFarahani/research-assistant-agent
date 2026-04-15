from fastapi import APIRouter, HTTPException, Query

from app.core.dependencies import LLMDep, QdrantDep
from app.core.exceptions import ChunkNotFoundError
from app.schemas.source import SourceChunkResponse
from app.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/{doc_id}/chunk/{chunk_id}", response_model=SourceChunkResponse)
async def get_source_chunk(
    doc_id: str,
    chunk_id: str,
    qdrant: QdrantDep,
    llm: LLMDep,
    query: str = Query(default=""),
) -> SourceChunkResponse:
    service = SourceService(qdrant, llm)
    try:
        return await service.get_chunk(doc_id=doc_id, chunk_id=chunk_id, query=query)
    except ChunkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
