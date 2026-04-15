import re
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_COOKIE_NAME = "user_id"
_ONE_YEAR = 60 * 60 * 24 * 365

_CallNext = Callable[[Request], Awaitable[Response]]


class UserIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: _CallNext) -> Response:
        raw = request.cookies.get(_COOKIE_NAME, "")
        is_new = not raw or not _UUID_RE.match(raw)
        user_id = str(uuid.uuid4()) if is_new else raw
        request.state.user_id = user_id

        response: Response = await call_next(request)

        if is_new:
            response.set_cookie(
                key=_COOKIE_NAME,
                value=user_id,
                max_age=_ONE_YEAR,
                httponly=True,
                samesite="lax",
                secure=False,  # set True in production behind HTTPS
                path="/",
            )
        return response
