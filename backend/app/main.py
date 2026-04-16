from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, documents, sources, summarize, usage
from app.config import settings
from app.core.exceptions import AppError
from app.core.rate_limiter import RateLimitError
from app.middleware.user_id import UserIdMiddleware

app = FastAPI(title="Research Assistant API", version="0.1.0")

# Middleware is applied in LIFO order — UserIdMiddleware runs inside CORS
app.add_middleware(UserIdMiddleware)
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


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Daily usage limit exceeded. Please try again later.",
            "reset_at": exc.reset_at.isoformat(),
            "usage": {
                "tokens_used": exc.tokens_used,
                "tokens_limit": exc.tokens_limit,
                "requests_used": exc.requests_used,
                "requests_limit": exc.requests_limit,
            },
        },
    )


app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(sources.router)
app.include_router(summarize.router)
app.include_router(usage.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
