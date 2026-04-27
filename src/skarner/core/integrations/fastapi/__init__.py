from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException

from skarner.core.tracing import generate_trace_id, set_trace_id
from skarner.core.ratelimit import BaseRateLimiter

TRACE_ID_HEADER = "x-trace-id"


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get(TRACE_ID_HEADER) or generate_trace_id()
        set_trace_id(trace_id)
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response


def rate_limit(limiter: BaseRateLimiter, rate: int, per_seconds: int):
    """FastAPI dependency factory for per-user-per-endpoint rate limiting.

    Usage:
        @app.get("/feed")
        def feed(user_id: int, _=Depends(rate_limit(limiter, rate=10, per_seconds=60))):
            ...

    The key is composed as "<user_id>:<path>" so each user gets an independent quota
    per endpoint. Swap the key format to share quotas across endpoints.
    """
    def dependency(request: Request, user_id: int):
        key = f"{user_id}:{request.url.path}"
        result = limiter.limit(key, rate=rate, per_seconds=per_seconds)
        if not result.allowed:
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        return result

    return dependency
