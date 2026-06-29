"""Tests for FastAPI exception handler integration."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from skarner.core.integrations.fastapi.exception_handler import (
    register_exception_handlers,
    get_http_status,
)
from skarner.core.exceptions import BusinessError, ErrorCode


@pytest.fixture
def app():
    """Create FastAPI app with exception handlers registered."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/business-error")
    def raise_business_error():
        raise BusinessError(ErrorCode.AUTH_INVALID_TOKEN, "Invalid token")

    @app.get("/value-error")
    def raise_value_error():
        raise ValueError("Invalid value")

    @app.get("/type-error")
    def raise_type_error():
        raise TypeError("Invalid type")

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_business_error_returns_correct_response(client):
    """BusinessError should return ResponseModel format."""
    response = client.get("/business-error")

    assert response.status_code == 401
    data = response.json()
    assert data["code"] == ErrorCode.AUTH_INVALID_TOKEN
    assert data["message"] == "Invalid token"
    assert "trace_id" in data


def test_value_error_returns_validation_error(client):
    """ValueError should return 422 with VALIDATION_ERROR code."""
    response = client.get("/value-error")

    assert response.status_code == 422
    data = response.json()
    assert data["code"] == ErrorCode.VALIDATION_ERROR
    assert data["message"] == "Invalid value"


def test_type_error_returns_validation_error(client):
    """TypeError should return 422 with VALIDATION_ERROR code."""
    response = client.get("/type-error")

    assert response.status_code == 422
    data = response.json()
    assert data["code"] == ErrorCode.VALIDATION_ERROR
    assert data["message"] == "Invalid type"


def test_get_http_status_auth_errors():
    """Auth errors should map to 401/403."""
    assert get_http_status(ErrorCode.AUTH_INVALID_TOKEN) == 401
    assert get_http_status(ErrorCode.AUTH_TOKEN_EXPIRED) == 401
    assert get_http_status(ErrorCode.AUTH_UNAUTHORIZED) == 403
    assert get_http_status(ErrorCode.AUTH_FORBIDDEN) == 403


def test_get_http_status_validation_errors():
    """Validation errors should map to 422."""
    assert get_http_status(ErrorCode.VALIDATION_ERROR) == 422
    assert get_http_status(ErrorCode.VALIDATION_MISSING_FIELD) == 422


def test_get_http_status_ratelimit_errors():
    """Rate limit errors should map to 429."""
    assert get_http_status(ErrorCode.RATE_LIMIT_EXCEEDED) == 429


def test_get_http_status_internal_errors():
    """Internal errors should map to 500."""
    assert get_http_status(ErrorCode.INTERNAL_ERROR) == 500
    assert get_http_status(ErrorCode.SERVICE_UNAVAILABLE) == 500


def test_get_http_status_default():
    """Unknown error codes should map to 400."""
    # Use an int value outside all defined ranges
    assert get_http_status(5001) == 400
