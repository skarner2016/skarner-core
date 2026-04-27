from contextvars import ContextVar
from uuid import uuid4

__all__ = ["generate_trace_id", "get_trace_id", "set_trace_id"]

_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def generate_trace_id() -> str:
    return uuid4().hex


def set_trace_id(trace_id: str) -> None:
    _trace_id_var.set(trace_id)


def get_trace_id() -> str:
    return _trace_id_var.get()
