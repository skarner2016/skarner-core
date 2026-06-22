"""Tests for unified exception handling system."""
import pytest
from enum import IntEnum


def test_error_code_is_int_enum():
    """ErrorCode should be an IntEnum for type safety."""
    from skarner.core.exceptions import ErrorCode

    assert issubclass(ErrorCode, IntEnum)


def test_error_code_auth_range():
    """Authentication errors should be in 1000-1999 range."""
    from skarner.core.exceptions import ErrorCode

    assert ErrorCode.AUTH_INVALID_TOKEN == 1001
    assert ErrorCode.AUTH_TOKEN_EXPIRED == 1002
    assert ErrorCode.AUTH_UNAUTHORIZED == 1003
    assert ErrorCode.AUTH_FORBIDDEN == 1004


def test_error_code_validation_range():
    """Validation errors should be in 2000-2999 range."""
    from skarner.core.exceptions import ErrorCode

    assert ErrorCode.VALIDATION_ERROR == 2001
    assert ErrorCode.VALIDATION_MISSING_FIELD == 2002
    assert ErrorCode.VALIDATION_INVALID_FORMAT == 2003


def test_error_code_database_range():
    """Database errors should be in 3000-3999 range."""
    from skarner.core.exceptions import ErrorCode

    assert ErrorCode.DB_CONNECTION_ERROR == 3001
    assert ErrorCode.DB_QUERY_ERROR == 3002
    assert ErrorCode.DB_RECORD_NOT_FOUND == 3003
    assert ErrorCode.DB_DUPLICATE_ENTRY == 3004


def test_error_code_ratelimit_range():
    """Rate limit errors should be in 4000-4999 range."""
    from skarner.core.exceptions import ErrorCode

    assert ErrorCode.RATE_LIMIT_EXCEEDED == 4001


def test_error_code_internal_range():
    """Internal errors should be in 9000-9999 range."""
    from skarner.core.exceptions import ErrorCode

    assert ErrorCode.INTERNAL_ERROR == 9001
    assert ErrorCode.SERVICE_UNAVAILABLE == 9002
