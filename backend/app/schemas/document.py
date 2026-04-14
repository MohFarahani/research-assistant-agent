import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: Literal["processing", "ready", "error"]
    created_at: datetime
    page_count: int | None = None

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: Literal["processing", "ready", "error"]
