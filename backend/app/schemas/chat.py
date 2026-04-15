from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class CitationRef(BaseModel):
    doc_id: str
    chunk_id: str
    doc_label: str
    page: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationRef]
