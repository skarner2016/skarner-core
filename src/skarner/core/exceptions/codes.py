"""Error code definitions organized by domain."""
from enum import IntEnum


class ErrorCode(IntEnum):
    """Business error codes organized by domain ranges.

    Ranges:
    - 1000-1999: Authentication/Authorization
    - 2000-2999: Validation
    - 3000-3999: Database
    - 4000-4999: Rate Limiting
    - 9000-9999: Internal/System
    """

    # Authentication (1000-1999)
    AUTH_INVALID_TOKEN = 1001
    AUTH_TOKEN_EXPIRED = 1002
    AUTH_UNAUTHORIZED = 1003
    AUTH_FORBIDDEN = 1004

    # Validation (2000-2999)
    VALIDATION_ERROR = 2001
    VALIDATION_MISSING_FIELD = 2002
    VALIDATION_INVALID_FORMAT = 2003

    # Database (3000-3999)
    DB_CONNECTION_ERROR = 3001
    DB_QUERY_ERROR = 3002
    DB_RECORD_NOT_FOUND = 3003
    DB_DUPLICATE_ENTRY = 3004

    # Rate Limiting (4000-4999)
    RATE_LIMIT_EXCEEDED = 4001

    # Internal/System (9000-9999)
    INTERNAL_ERROR = 9001
    SERVICE_UNAVAILABLE = 9002
