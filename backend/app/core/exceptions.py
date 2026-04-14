class AppError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"


class DocumentNotFoundError(AppError):
    status_code = 404

    def __init__(self, doc_id: str) -> None:
        self.detail = f"Document {doc_id} not found"
        super().__init__(self.detail)


class ChunkNotFoundError(AppError):
    status_code = 404

    def __init__(self, chunk_id: str) -> None:
        self.detail = f"Chunk {chunk_id} not found"
        super().__init__(self.detail)


class IngestionError(AppError):
    status_code = 500

    def __init__(self, message: str) -> None:
        self.detail = f"Ingestion failed: {message}"
        super().__init__(self.detail)


class LLMError(AppError):
    status_code = 502

    def __init__(self, message: str) -> None:
        self.detail = f"LLM call failed: {message}"
        super().__init__(self.detail)
