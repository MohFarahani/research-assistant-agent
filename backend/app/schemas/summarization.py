from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    doc_id: str


class SummarizeResponse(BaseModel):
    doc_id: str
    summary: str
