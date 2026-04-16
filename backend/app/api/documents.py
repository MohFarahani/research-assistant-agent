import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile

from app.core.dependencies import (
    DBSession,
    LLMDep,
    QdrantDep,
    RateLimitCheck,
    UserIdDep,
    get_client_ip,
)
from app.schemas.document import DocumentResponse, UploadResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

_UPLOAD_DIR = Path("uploads")


async def _run_ingestion(
    doc_id: uuid.UUID,
    filename: str,
    file_path: Path,
    user_id: str,
    client_ip: str,
) -> None:
    """Standalone background coroutine with its own DB session."""
    from app.core.dependencies import _async_session, get_llm, get_qdrant
    from app.llm.usage import current_rate_keys

    current_rate_keys.set((user_id, client_ip))
    async with _async_session() as session:
        service = DocumentService(session, get_qdrant(), get_llm())
        await service.ingest(
            doc_id=doc_id, filename=filename, file_path=file_path, user_id=user_id
        )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: DBSession, qdrant: QdrantDep, llm: LLMDep, user_id: UserIdDep
) -> list[DocumentResponse]:
    service = DocumentService(db, qdrant, llm)
    docs = await service.list_documents(user_id=user_id)
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DBSession,
    qdrant: QdrantDep,
    llm: LLMDep,
    user_id: UserIdDep,
    _rate_check: RateLimitCheck,
    file: UploadFile = File(...),
) -> UploadResponse:
    filename = file.filename or "upload.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    service = DocumentService(db, qdrant, llm)
    doc_id = await service.create_pending(filename=filename, user_id=user_id)

    _UPLOAD_DIR.mkdir(exist_ok=True)
    file_path = _UPLOAD_DIR / f"{doc_id}.pdf"
    with file_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Capture user_id + client_ip here (request.state unavailable in bg tasks)
    client_ip = get_client_ip(request)
    background_tasks.add_task(
        _run_ingestion, doc_id, filename, file_path, user_id, client_ip
    )

    return UploadResponse(id=doc_id, filename=filename, status="processing")
