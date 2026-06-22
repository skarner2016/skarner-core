from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

from skarner.core.tracing import get_trace_id

__all__ = ["ResponseModel", "success", "fail", "CODE_SUCCESS"]

T = TypeVar("T")

#: Business code denoting a successful response. Non-zero codes are errors.
CODE_SUCCESS = 0


class ResponseModel(BaseModel, Generic[T]):
    """Unified API response envelope.

    ``code == 0`` means success; any non-zero value is a business error code,
    decoupled from the HTTP status code. ``trace_id`` carries the current
    request trace for end-to-end correlation.
    """

    code: int = CODE_SUCCESS
    message: str = "ok"
    data: T | None = None
    trace_id: str = ""


def success(
    data: T | None = None,
    *,
    message: str = "ok",
    trace_id: str | None = None,
) -> ResponseModel[T]:
    """Build a success response (``code=0``).

    Args:
        data: Payload to return.
        message: Human-readable message.
        trace_id: Override the trace id. Defaults to the current contextvar
            (populated by TraceIDMiddleware during a request).
    """
    return ResponseModel[T](
        code=CODE_SUCCESS,
        message=message,
        data=data,
        trace_id=trace_id if trace_id is not None else get_trace_id(),
    )


def fail(
    code: int,
    message: str,
    *,
    data: T | None = None,
    trace_id: str | None = None,
) -> ResponseModel[T]:
    """Build an error response with a non-zero business ``code``.

    Args:
        code: Non-zero business error code.
        message: Human-readable error message.
        data: Optional extra payload (e.g. field-level errors).
        trace_id: Override the trace id. Defaults to the current contextvar.

    Raises:
        ValueError: ``code`` is 0 (use ``success()`` for success responses).
    """
    if code == CODE_SUCCESS:
        raise ValueError("fail() requires a non-zero code")
    return ResponseModel[T](
        code=code,
        message=message,
        data=data,
        trace_id=trace_id if trace_id is not None else get_trace_id(),
    )
