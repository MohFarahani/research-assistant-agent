from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, documents, sources, summarize
from app.config import settings
from app.core.exceptions import AppError

app = FastAPI(title="Research Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(sources.router)
app.include_router(summarize.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
