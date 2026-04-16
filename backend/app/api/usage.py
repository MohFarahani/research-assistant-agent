from fastapi import APIRouter, Request

from app.core.dependencies import UserIdDep
from app.core.rate_limiter import get_rate_limiter

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("")
async def get_usage(request: Request, user_id: UserIdDep) -> dict[str, object]:
    client_ip = request.client.host if request.client else "unknown"
    return await get_rate_limiter().get_status(user_id, client_ip)
