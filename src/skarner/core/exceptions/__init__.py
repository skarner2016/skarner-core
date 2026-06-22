"""Unified exception handling for skarner-core."""
from .base import BusinessError
from .codes import ErrorCode

__all__ = ["BusinessError", "ErrorCode"]
