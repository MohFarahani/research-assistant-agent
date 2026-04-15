import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.core.dependencies import DBSession, LLMDep, QdrantDep
from app.schemas.document import DocumentResponse, UploadResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

_UPLOAD_DIR = Path("uploads")


async def _run_ingestion(
    doc_id: uuid.UUID, filename: str, file_path: Path
) -> None:
    """Standalone background coroutine with its own DB session."""
    from app.core.dependencies import _async_session, get_llm, get_qdrant

    async with _async_session() as session:
        service = DocumentService(session, get_qdrant(), get_llm())
        await service.ingest(doc_id=doc_id, filename=filename, file_path=file_path)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: DBSession, qdrant: QdrantDep, llm: LLMDep
) -> list[DocumentResponse]:
    service = DocumentService(db, qdrant, llm)
    docs = await service.list_documents()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    db: DBSession,
    qdrant: QdrantDep,
    llm: LLMDep,
    file: UploadFile = File(...),
) -> UploadResponse:
    filename = file.filename or "upload.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    service = DocumentService(db, qdrant, llm)
    doc_id = await service.create_pending(filename=filename)

    _UPLOAD_DIR.mkdir(exist_ok=True)
    file_path = _UPLOAD_DIR / f"{doc_id}.pdf"
    with file_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(_run_ingestion, doc_id, filename, file_path)

    return UploadResponse(id=doc_id, filename=filename, status="processing")
