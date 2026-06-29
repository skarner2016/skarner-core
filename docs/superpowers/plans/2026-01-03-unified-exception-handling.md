# 统一异常处理实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `BusinessError(code, message)` 异常类和 FastAPI 全局异常处理器，自动转换为 `ResponseModel` 标准错误格式。

**Architecture:** 新建 `core/exceptions/` 模块（框架无关），定义 `ErrorCode` 枚举和 `BusinessError` 类；在 `integrations/fastapi/` 实现异常处理器，捕获 `BusinessError` 和 `ValueError/TypeError`，转换为 `ResponseModel` 格式。现有 JWT 异常标记为废弃。

**Tech Stack:** Python 3.20+, Pydantic, FastAPI, IntEnum

---

## 文件结构

```
src/skarner/core/
├── exceptions/
│   ├── __init__.py          # 导出 BusinessError, ErrorCode
│   ├── codes.py             # ErrorCode 枚举
│   └── base.py              # BusinessError 类
├── auth/
│   └── jwt.py               # [修改] 废弃现有异常类
└── integrations/fastapi/
    └── exception_handler.py # FastAPI 异常处理器

tests/
├── test_exceptions.py       # 单元测试
└── integrations/fastapi/
    └── test_exception_handler.py  # 集成测试
```

---

## Task 1: 定义 ErrorCode 枚举

**Files:**
- Create: `src/skarner/core/exceptions/codes.py`
- Test: `tests/test_exceptions.py`

- [ ] **Step 1: Write the failing test for ErrorCode enum**

```python
# tests/test_exceptions.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_exceptions.py::test_error_code_is_int_enum -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'skarner.core.exceptions'"

- [ ] **Step 3: Create exceptions module directory**

```bash
mkdir -p src/skarner/core/exceptions
touch src/skarner/core/exceptions/__init__.py
```

- [ ] **Step 4: Implement ErrorCode enum**

```python
# src/skarner/core/exceptions/codes.py
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
```

- [ ] **Step 5: Export ErrorCode from module**

```python
# src/skarner/core/exceptions/__init__.py
"""Unified exception handling for skarner-core."""
from .codes import ErrorCode

__all__ = ["ErrorCode"]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_exceptions.py -v`

Expected: All 6 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/skarner/core/exceptions/ tests/test_exceptions.py
git commit -m "feat(exceptions): add ErrorCode enum with categorized ranges

Define ErrorCode IntEnum with domain-based ranges:
- 1000-1999: Authentication/Authorization
- 2000-2999: Validation
- 3000-3999: Database
- 4000-4999: Rate Limiting
- 9000-9999: Internal/System

Includes comprehensive test coverage for all error code ranges."
```

---

## Task 2: 实现 BusinessError 类

**Files:**
- Create: `src/skarner/core/exceptions/base.py`
- Modify: `src/skarner/core/exceptions/__init__.py`
- Test: `tests/test_exceptions.py`

- [ ] **Step 1: Write the failing test for BusinessError**

```python
# tests/test_exceptions.py - append to existing file


def test_business_error_inherits_from_exception():
    """BusinessError should inherit from Exception."""
    from skarner.core.exceptions import BusinessError, ErrorCode
    
    error = BusinessError(ErrorCode.AUTH_INVALID_TOKEN, "Invalid token")
    assert isinstance(error, Exception)


def test_business_error_stores_code_and_message():
    """BusinessError should store code and message."""
    from skarner.core.exceptions import BusinessError, ErrorCode
    
    error = BusinessError(ErrorCode.AUTH_INVALID_TOKEN, "Invalid token")
    assert error.code == ErrorCode.AUTH_INVALID_TOKEN
    assert error.message == "Invalid token"


def test_business_error_string_representation():
    """BusinessError string should include code name and message."""
    from skarner.core.exceptions import BusinessError, ErrorCode
    
    error = BusinessError(ErrorCode.DB_RECORD_NOT_FOUND, "User not found")
    assert str(error) == "DB_RECORD_NOT_FOUND: User not found"


def test_business_error_can_be_raised_and_caught():
    """BusinessError should be raisable and catchable."""
    from skarner.core.exceptions import BusinessError, ErrorCode
    
    with pytest.raises(BusinessError) as exc_info:
        raise BusinessError(ErrorCode.AUTH_FORBIDDEN, "Access denied")
    
    assert exc_info.value.code == ErrorCode.AUTH_FORBIDDEN
    assert exc_info.value.message == "Access denied"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_exceptions.py::test_business_error_inherits_from_exception -v`

Expected: FAIL with "ImportError: cannot import name 'BusinessError'"

- [ ] **Step 3: Implement BusinessError class**

```python
# src/skarner/core/exceptions/base.py
"""Business error exception class."""
from .codes import ErrorCode


class BusinessError(Exception):
    """业务异常基类。
    
    用于表示业务逻辑中的可预期错误，会被 FastAPI 异常处理器自动捕获并转换为标准响应格式。
    
    Example:
        >>> from skarner.core.exceptions import BusinessError, ErrorCode
        >>> raise BusinessError(ErrorCode.AUTH_INVALID_TOKEN, "Invalid credentials")
    """
    
    def __init__(self, code: ErrorCode, message: str):
        """初始化业务异常。
        
        Args:
            code: 错误码（ErrorCode 枚举值）
            message: 错误描述信息
        """
        self.code = code
        self.message = message
        super().__init__(f"{code.name}: {message}")
```

- [ ] **Step 4: Export BusinessError from module**

```python
# src/skarner/core/exceptions/__init__.py
"""Unified exception handling for skarner-core."""
from .base import BusinessError
from .codes import ErrorCode

__all__ = ["BusinessError", "ErrorCode"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_exceptions.py -v`

Expected: All 10 tests PASS (6 ErrorCode + 4 BusinessError)

- [ ] **Step 6: Commit**

```bash
git add src/skarner/core/exceptions/ tests/test_exceptions.py
git commit -m "feat(exceptions): add BusinessError exception class

Implement BusinessError exception with:
- Stores ErrorCode and message
- String representation: 'ERROR_CODE_NAME: message'
- Inherits from Exception for standard try/except usage

Includes comprehensive test coverage."
```

---

## Task 3: 实现 FastAPI 异常处理器

**Files:**
- Create: `src/skarner/core/integrations/fastapi/exception_handler.py`
- Test: `tests/integrations/fastapi/test_exception_handler.py`

- [ ] **Step 1: Write the failing test for exception handler**

```python
# tests/integrations/fastapi/test_exception_handler.py
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
    # Create a custom error code outside defined ranges
    class CustomCode(ErrorCode):
        CUSTOM_ERROR = 5000
    
    assert get_http_status(CustomCode.CUSTOM_ERROR) == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integrations/fastapi/test_exception_handler.py::test_business_error_returns_correct_response -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'skarner.core.integrations.fastapi.exception_handler'"

- [ ] **Step 3: Implement exception handler**

```python
# src/skarner/core/integrations/fastapi/exception_handler.py
"""FastAPI exception handler integration."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from skarner.core.exceptions import BusinessError, ErrorCode
from skarner.core.response import fail


def get_http_status(code: ErrorCode) -> int:
    """根据错误码返回对应的 HTTP 状态码。
    
    Args:
        code: ErrorCode 枚举值
    
    Returns:
        HTTP 状态码
    """
    # 认证/授权错误
    if 1000 <= code < 2000:
        if code in [ErrorCode.AUTH_INVALID_TOKEN, ErrorCode.AUTH_TOKEN_EXPIRED]:
            return 401  # Unauthorized
        return 403  # Forbidden
    
    # 验证错误
    if 2000 <= code < 3000:
        return 422  # Unprocessable Entity
    
    # 限流错误
    if 4000 <= code < 5000:
        return 429  # Too Many Requests
    
    # 内部错误
    if 9000 <= code < 10000:
        return 500  # Internal Server Error
    
    # 默认
    return 400  # Bad Request


async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    """处理 BusinessError 异常。
    
    Args:
        request: FastAPI 请求对象
        exc: BusinessError 异常实例
    
    Returns:
        JSONResponse: ResponseModel 格式的错误响应
    """
    return JSONResponse(
        status_code=get_http_status(exc.code),
        content=fail(code=int(exc.code), message=exc.message).model_dump(),
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理 ValueError/TypeError 异常。
    
    Args:
        request: FastAPI 请求对象
        exc: ValueError 或 TypeError 异常实例
    
    Returns:
        JSONResponse: ResponseModel 格式的错误响应（VALIDATION_ERROR）
    """
    return JSONResponse(
        status_code=422,
        content=fail(code=int(ErrorCode.VALIDATION_ERROR), message=str(exc)).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。
    
    Args:
        app: FastAPI 应用实例
    
    Example:
        >>> from fastapi import FastAPI
        >>> from skarner.core.integrations.fastapi.exception_handler import register_exception_handlers
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    app.add_exception_handler(BusinessError, business_error_handler)
    app.add_exception_handler(ValueError, validation_error_handler)
    app.add_exception_handler(TypeError, validation_error_handler)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integrations/fastapi/test_exception_handler.py -v`

Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/skarner/core/integrations/fastapi/exception_handler.py tests/integrations/fastapi/test_exception_handler.py
git commit -m "feat(fastapi): add global exception handler

Implement FastAPI exception handler with:
- register_exception_handlers(app) to register handlers
- BusinessError handler with automatic HTTP status mapping
- ValueError/TypeError handler for validation errors (422)
- get_http_status() for ErrorCode to HTTP status conversion
- All responses use ResponseModel format

Includes comprehensive test coverage."
```

---

## Task 4: 废弃 JWT 异常类

**Files:**
- Modify: `src/skarner/core/auth/jwt.py`
- Test: `tests/test_jwt.py`

- [ ] **Step 1: Write the failing test for deprecation warnings**

```python
# tests/test_jwt.py - append to existing file


def test_jwt_decode_error_deprecation_warning():
    """JWTDecodeError should emit deprecation warning."""
    from skarner.core.auth import JWTDecodeError
    
    with pytest.warns(DeprecationWarning) as warning_info:
        raise JWTDecodeError("test")
    
    assert "deprecated" in str(warning_info.value).lower()
    assert "BusinessError" in str(warning_info.value)


def test_jwt_expired_error_deprecation_warning():
    """JWTExpiredError should emit deprecation warning."""
    from skarner.core.auth import JWTExpiredError
    
    with pytest.warns(DeprecationWarning) as warning_info:
        raise JWTExpiredError("test")
    
    assert "deprecated" in str(warning_info.value).lower()
    assert "BusinessError" in str(warning_info.value)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_jwt.py::test_jwt_decode_error_deprecation_warning -v`

Expected: FAIL with "Failed: DID NOT WARN"

- [ ] **Step 3: Add deprecation warnings to JWT exceptions**

```python
# src/skarner/core/auth/jwt.py - modify existing file
from datetime import datetime, timedelta, timezone
from typing import Any
import warnings

import jwt

__all__ = ["JWTManager", "JWTDecodeError", "JWTExpiredError"]


class JWTDecodeError(Exception):
    """[已废弃] JWT 解码错误。
    
    .. deprecated::
        请使用 ``BusinessError(ErrorCode.AUTH_INVALID_TOKEN, message)`` 替代。
    """
    
    def __init__(self, message: str = "Invalid token"):
        warnings.warn(
            "JWTDecodeError is deprecated. Use BusinessError(ErrorCode.AUTH_INVALID_TOKEN, message) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message)


class JWTExpiredError(JWTDecodeError):
    """[已废弃] JWT 过期错误。
    
    .. deprecated::
        请使用 ``BusinessError(ErrorCode.AUTH_TOKEN_EXPIRED, message)`` 替代。
    """
    
    def __init__(self, message: str = "Token expired"):
        warnings.warn(
            "JWTExpiredError is deprecated. Use BusinessError(ErrorCode.AUTH_TOKEN_EXPIRED, message) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        Exception.__init__(self, message)


class JWTManager:
    def __init__(self, secret: str, algorithm: str = "HS256") -> None:
        if not secret:
            raise ValueError("secret must not be empty")
        self._secret = secret
        self._algorithm = algorithm

    def encode(self, payload: dict[str, Any], expires_in: int) -> str:
        """Sign a payload and return a JWT string.

        Args:
            payload: Claims to include in the token.
            expires_in: Token lifetime in seconds.
        """
        data = payload.copy()
        data["exp"] = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
        return jwt.encode(data, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT string.

        Raises:
            JWTExpiredError: Token has expired.
            JWTDecodeError: Token is invalid.
        """
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError as e:
            raise JWTExpiredError("token has expired") from e
        except jwt.PyJWTError as e:
            raise JWTDecodeError(f"invalid token: {e}") from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_jwt.py -v`

Expected: All tests PASS (existing + 2 new deprecation tests)

- [ ] **Step 5: Commit**

```bash
git add src/skarner/core/auth/jwt.py tests/test_jwt.py
git commit -m "refactor(auth): deprecate JWTDecodeError and JWTExpiredError

Add DeprecationWarning to existing JWT exception classes:
- JWTDecodeError: recommend BusinessError(ErrorCode.AUTH_INVALID_TOKEN)
- JWTExpiredError: recommend BusinessError(ErrorCode.AUTH_TOKEN_EXPIRED)
- Maintain backward compatibility with warnings
- Update docstrings with migration instructions

Includes test coverage for deprecation warnings."
```

---

## Task 5: 创建使用示例文档

**Files:**
- Create: `docs/exception-handling-guide.md`

- [ ] **Step 1: Create usage guide**

```markdown
# 统一异常处理使用指南

本指南介绍如何使用 skarner-core 的统一异常处理系统。

## 概述

统一异常处理系统提供：
- `BusinessError` 异常类，携带错误码和消息
- `ErrorCode` 枚举，按领域分类的错误码
- FastAPI 全局异常处理器，自动转换为标准响应格式

## 快速开始

### 1. 注册异常处理器

在你的 FastAPI 应用中注册全局异常处理器：

```python
from fastapi import FastAPI
from skarner.core.integrations.fastapi.exception_handler import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

### 2. 抛出业务异常

在业务逻辑中使用 `BusinessError`：

```python
from skarner.core.exceptions import BusinessError, ErrorCode

@app.post("/login")
def login(credentials: LoginRequest):
    user = authenticate(credentials.username, credentials.password)
    if not user:
        raise BusinessError(
            ErrorCode.AUTH_INVALID_TOKEN,
            "用户名或密码错误"
        )
    return success(data={"token": create_token(user)})
```

### 3. 错误响应格式

所有错误响应遵循 `ResponseModel` 格式：

```json
{
  "code": 1001,
  "message": "用户名或密码错误",
  "data": null,
  "trace_id": "abc123def456"
}
```

## ErrorCode 分类

错误码按领域划分：

| 范围 | 领域 | 示例 |
|------|------|------|
| 1000-1999 | 认证/授权 | `AUTH_INVALID_TOKEN`, `AUTH_FORBIDDEN` |
| 2000-2999 | 数据验证 | `VALIDATION_ERROR`, `VALIDATION_MISSING_FIELD` |
| 3000-3999 | 数据库 | `DB_RECORD_NOT_FOUND`, `DB_DUPLICATE_ENTRY` |
| 4000-4999 | 限流 | `RATE_LIMIT_EXCEEDED` |
| 9000-9999 | 内部/系统 | `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE` |

## HTTP 状态码映射

异常处理器自动将错误码映射到 HTTP 状态码：

| 错误码范围 | HTTP 状态码 | 说明 |
|------------|-------------|------|
| 1001-1002 | 401 | Unauthorized（令牌无效/过期） |
| 1003-1004 | 403 | Forbidden（未认证/无权限） |
| 2000-2999 | 422 | Unprocessable Entity（验证错误） |
| 4000-4999 | 429 | Too Many Requests（限流） |
| 9000-9999 | 500 | Internal Server Error（内部错误） |
| 其他 | 400 | Bad Request（默认） |

## 自定义错误码

你可以在自己的项目中定义新的错误码：

```python
from enum import IntEnum
from skarner.core.exceptions import ErrorCode

class MyErrorCode(IntEnum):
    # 使用未占用的范围，例如 5000-5999
    CUSTOM_ERROR = 5001
    ANOTHER_ERROR = 5002

# 使用自定义错误码
raise BusinessError(MyErrorCode.CUSTOM_ERROR, "Custom error message")
```

## 迁移指南

### 从 JWTDecodeError 迁移

**旧代码：**
```python
from skarner.core.auth import JWTDecodeError

raise JWTDecodeError("Invalid token")
```

**新代码：**
```python
from skarner.core.exceptions import BusinessError, ErrorCode

raise BusinessError(ErrorCode.AUTH_INVALID_TOKEN, "Invalid token")
```

### 从 HTTPException 迁移

**旧代码：**
```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="User not found")
```

**新代码：**
```python
from skarner.core.exceptions import BusinessError, ErrorCode

raise BusinessError(ErrorCode.DB_RECORD_NOT_FOUND, "User not found")
```

## 最佳实践

1. **使用具体的错误码**：选择最匹配的错误码，而不是通用的 `VALIDATION_ERROR`
2. **提供清晰的错误消息**：消息应该对用户友好，帮助理解问题
3. **不要捕获 BusinessError**：让异常处理器统一处理
4. **记录异常**：在关键业务逻辑中记录异常以便调试

## 常见问题

**Q: 为什么错误响应使用 HTTP 200？**  
A: 错误响应不使用 HTTP 200，而是根据错误类型返回相应的状态码（401/403/422/429/500 等）。

**Q: 如何添加错误详情？**  
A: 当前版本不支持额外详情。保持异常简洁，使用 `message` 传达关键信息。

**Q: 可以在非 FastAPI 项目中使用吗？**  
A: 可以。`BusinessError` 和 `ErrorCode` 是框架无关的，可以在任何 Python 项目中使用。异常处理器是 FastAPI 特定的。
```

- [ ] **Step 2: Commit documentation**

```bash
git add docs/exception-handling-guide.md
git commit -m "docs: add comprehensive exception handling usage guide

Create detailed guide covering:
- Quick start with registration and usage
- ErrorCode categories and HTTP status mapping
- Custom error code definition
- Migration guide from JWTDecodeError and HTTPException
- Best practices and FAQ

Provides clear examples for common use cases."
```

---

## Task 6: 更新 TODO.md

**Files:**
- Modify: `TODO.md`

- [ ] **Step 1: Mark exception handling as complete**

```markdown
# TODO.md - 找到"统一异常体系"行并更新

| 功能 | 说明 | 现状 |
|---|---|---|
| ✅ **统一异常体系** | `BusinessError(code, message)` + FastAPI 全局 exception_handler，输出标准错误格式 | 已完成 |
```

- [ ] **Step 2: Commit TODO update**

```bash
git add TODO.md
git commit -m "docs: mark unified exception handling as complete

Update TODO.md to reflect completion of P0 priority item:
- BusinessError exception class
- ErrorCode enum with categorized ranges
- FastAPI global exception handler
- Comprehensive documentation"
```

---

## Task 7: 最终验证和清理

**Files:**
- All existing files

- [ ] **Step 1: Run all tests**

Run: `pytest -v`

Expected: All tests PASS (existing 59 + new exception tests)

- [ ] **Step 2: Verify imports work correctly**

```bash
python -c "from skarner.core.exceptions import BusinessError, ErrorCode; print('✓ Exceptions module imports successfully')"
python -c "from skarner.core.integrations.fastapi.exception_handler import register_exception_handlers; print('✓ Exception handler imports successfully')"
```

Expected: Both imports succeed without errors

- [ ] **Step 3: Test integration example**

```python
# test_integration.py
from fastapi import FastAPI
from fastapi.testclient import TestClient
from skarner.core.exceptions import BusinessError, ErrorCode
from skarner.core.integrations.fastapi.exception_handler import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)

@app.get("/test")
def test_endpoint():
    raise BusinessError(ErrorCode.AUTH_INVALID_TOKEN, "Test error")

client = TestClient(app)
response = client.get("/test")

assert response.status_code == 401
data = response.json()
assert data["code"] == 1001
assert data["message"] == "Test error"
print("✓ Integration test passed")
```

Run: `python test_integration.py`

Expected: "✓ Integration test passed"

- [ ] **Step 4: Clean up test file**

```bash
rm test_integration.py
```

- [ ] **Step 5: Final commit (if any cleanup needed)**

```bash
git status
# If there are any remaining changes:
git add -A
git commit -m "chore: final cleanup and verification

Verify all tests pass and integration works correctly."
```

---

## 完成标准

实现完成后，应该满足：

- ✅ `BusinessError` 和 `ErrorCode` 可以从 `skarner.core.exceptions` 导入
- ✅ `register_exception_handlers()` 可以从 `skarner.core.integrations.fastapi.exception_handler` 导入
- ✅ 所有单元测试通过（ErrorCode、BusinessError、异常处理器）
- ✅ JWT 异常标记为废弃并发出警告
- ✅ 使用文档完整且清晰
- ✅ TODO.md 已更新

---

## 执行顺序建议

1. **Task 1-2**: 先实现核心异常类（ErrorCode + BusinessError）
2. **Task 3**: 实现 FastAPI 集成
3. **Task 4**: 废弃旧异常类
4. **Task 5-6**: 文档和 TODO 更新
5. **Task 7**: 最终验证

每个 Task 都是独立可测试的，可以逐步提交。
