"""FastAPI exception handler registration."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from skarner.core.exceptions import BusinessError, ErrorCode
from skarner.core.response import fail


def get_http_status(code: ErrorCode) -> int:
    """Map an ErrorCode to an HTTP status code.

    Args:
        code: The business error code.

    Returns:
        Corresponding HTTP status code.
    """
    value = int(code)
    if 1000 <= value <= 1999:
        if code in (ErrorCode.AUTH_UNAUTHORIZED, ErrorCode.AUTH_FORBIDDEN):
            return 403
        return 401
    if 2000 <= value <= 2999:
        return 422
    if 4000 <= value <= 4999:
        return 429
    if 9000 <= value <= 9999:
        return 500
    return 400


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on a FastAPI app.

    Handles:
    - BusinessError → mapped HTTP status + ResponseModel body
    - ValueError / TypeError → 422 + VALIDATION_ERROR
    """

    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
        status = get_http_status(exc.code)
        body = fail(code=int(exc.code), message=exc.message)
        return JSONResponse(status_code=status, content=body.model_dump())

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        body = fail(code=int(ErrorCode.VALIDATION_ERROR), message=str(exc))
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(TypeError)
    async def type_error_handler(request: Request, exc: TypeError) -> JSONResponse:
        body = fail(code=int(ErrorCode.VALIDATION_ERROR), message=str(exc))
        return JSONResponse(status_code=422, content=body.model_dump())
