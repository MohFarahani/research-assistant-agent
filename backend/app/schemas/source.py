from pydantic import BaseModel


class HighlightRange(BaseModel):
    start: int
    end: int


class SourceChunkResponse(BaseModel):
    doc_id: str
    chunk_id: str
    page: int
    text: str
    doc_label: str
    highlight_ranges: list[HighlightRange]
