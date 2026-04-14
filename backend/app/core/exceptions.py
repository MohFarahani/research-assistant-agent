# Custom application exception classes.
from fastapi import HTTPException


class LLMError(Exception):
    """Raised when an LLM provider call fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def llm_error_to_http(exc: LLMError) -> HTTPException:
    return HTTPException(status_code=502, detail=f"LLM error: {exc.message}")
