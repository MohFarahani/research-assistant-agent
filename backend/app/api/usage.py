from fastapi import APIRouter, Request

from app.core.dependencies import UserIdDep, get_client_ip
from app.core.rate_limiter import get_rate_limiter

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("")
async def get_usage(request: Request, user_id: UserIdDep) -> dict[str, object]:
    client_ip = get_client_ip(request)
    return await get_rate_limiter().get_status(user_id, client_ip)
