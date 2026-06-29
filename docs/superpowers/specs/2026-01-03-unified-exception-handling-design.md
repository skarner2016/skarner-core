# 统一异常处理系统设计规格

## 1. 概述

为 skarner-core 实现统一的异常处理系统，提供：
- `BusinessError(code, message)` 异常类
- 分类的 `ErrorCode` 枚举（按领域划分错误码范围）
- FastAPI 全局异常处理器（自动转换为 `ResponseModel` 格式）
- 标准错误输出格式

## 2. 架构设计

### 2.1 模块结构

```
src/skarner/core/
├── exceptions/
│   ├── __init__.py          # 导出 BusinessError, ErrorCode
│   ├── base.py              # BusinessError 类定义
│   └── codes.py             # ErrorCode 枚举（分类错误码）
└── integrations/fastapi/
    └── exception_handler.py # FastAPI 全局异常处理器
```

### 2.2 设计原则

- **框架无关**：`BusinessError` 和 `ErrorCode` 位于 core 层，不依赖 FastAPI
- **关注点分离**：FastAPI 特定的异常处理逻辑放在 `integrations/fastapi/`
- **类型安全**：使用 `IntEnum` 提供类型检查和 IDE 自动补全
- **简洁性**：异常只携带 `code` 和 `message`，不携带额外上下文数据

### 2.3 错误处理流程

```
业务代码抛出 BusinessError(ErrorCode.XXX, "message")
    ↓
FastAPI 异常处理器捕获
    ↓
转换为 ResponseModel 格式：fail(code=XXX, message="...")
    ↓
返回 JSON 响应（包含 trace_id）
```

## 3. ErrorCode 枚举设计

### 3.1 错误码范围

按领域划分，便于管理和扩展：

| 范围 | 领域 | 说明 |
|------|------|------|
| 1000-1999 | 认证/授权 | 令牌、权限相关错误 |
| 2000-2999 | 数据验证 | 输入验证、格式错误 |
| 3000-3999 | 数据库 | 连接、查询、约束错误 |
| 4000-4999 | 限流 | 速率限制错误 |
| 9000-9999 | 内部/系统 | 服务内部错误 |

### 3.2 预定义错误码

```python
class ErrorCode(IntEnum):
    # 认证/授权 (1000-1999)
    AUTH_INVALID_TOKEN = 1001      # 无效的令牌
    AUTH_TOKEN_EXPIRED = 1002      # 令牌已过期
    AUTH_UNAUTHORIZED = 1003       # 未认证
    AUTH_FORBIDDEN = 1004          # 无权限
    
    # 数据验证 (2000-2999)
    VALIDATION_ERROR = 2001        # 通用验证错误
    VALIDATION_MISSING_FIELD = 2002  # 缺少必填字段
    VALIDATION_INVALID_FORMAT = 2003 # 格式不正确
    
    # 数据库 (3000-3999)
    DB_CONNECTION_ERROR = 3001     # 数据库连接错误
    DB_QUERY_ERROR = 3002          # 查询错误
    DB_RECORD_NOT_FOUND = 3003     # 记录不存在
    DB_DUPLICATE_ENTRY = 3004      # 重复记录
    
    # 限流 (4000-4999)
    RATE_LIMIT_EXCEEDED = 4001     # 超出速率限制
    
    # 内部/系统 (9000-9999)
    INTERNAL_ERROR = 9001          # 内部错误
    SERVICE_UNAVAILABLE = 9002     # 服务不可用
```

### 3.3 扩展性

用户可以：
- 使用预定义错误码
- 在自己的项目中定义新的 `ErrorCode` 枚举（继承或新建）

## 4. BusinessError 类设计

### 4.1 类定义

```python
class BusinessError(Exception):
    """业务异常基类。
    
    用于表示业务逻辑中的可预期错误，会被 FastAPI 异常处理器自动捕获并转换为标准响应格式。
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

### 4.2 设计决策

- **简洁性**：只包含 `code` 和 `message`，不携带额外上下文数据
- **可读性**：`__str__` 返回 `"ERROR_CODE_NAME: message"` 格式，便于日志记录
- **继承自 Exception**：可以被标准 `try/except` 捕获

## 5. FastAPI 异常处理器

### 5.1 处理器注册

```python
def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。
    
    Args:
        app: FastAPI 应用实例
    """
    # 处理 BusinessError
    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
        return JSONResponse(
            status_code=get_http_status(exc.code),
            content=fail(code=int(exc.code), message=exc.message).model_dump(),
        )
    
    # 处理 ValueError/TypeError（转换为验证错误）
    @app.exception_handler(ValueError)
    @app.exception_handler(TypeError)
    async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=fail(
                code=int(ErrorCode.VALIDATION_ERROR),
                message=str(exc)
            ).model_dump(),
        )
```

### 5.2 HTTP 状态码映射

```python
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
```

### 5.3 处理范围

- **BusinessError**：所有业务异常，转换为对应的 HTTP 状态码
- **ValueError/TypeError**：转换为 `VALIDATION_ERROR`（HTTP 422）
- **其他异常**：不捕获，让 FastAPI 默认处理（或用户自行处理）

## 6. 与现有模块的集成

### 6.1 JWT 模块迁移策略

现有 `JWTDecodeError` 和 `JWTExpiredError` 采用**废弃并替换**策略：

```python
# core/auth/jwt.py
import warnings

class JWTDecodeError(Exception):
    """[已废弃] 请使用 BusinessError(ErrorCode.AUTH_INVALID_TOKEN, message) 替代。"""
    
    def __init__(self, message: str = "Invalid token"):
        warnings.warn(
            "JWTDecodeError is deprecated. Use BusinessError(ErrorCode.AUTH_INVALID_TOKEN, message) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(message)


class JWTExpiredError(JWTDecodeError):
    """[已废弃] 请使用 BusinessError(ErrorCode.AUTH_TOKEN_EXPIRED, message) 替代。"""
    
    def __init__(self, message: str = "Token expired"):
        warnings.warn(
            "JWTExpiredError is deprecated. Use BusinessError(ErrorCode.AUTH_TOKEN_EXPIRED, message) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        Exception.__init__(self, message)
```

### 6.2 向后兼容

- 现有代码可以继续使用 `JWTDecodeError` 和 `JWTExpiredError`
- 会收到 `DeprecationWarning` 警告
- 新代码应直接使用 `BusinessError`

## 7. 使用示例

### 7.1 抛出业务异常

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

### 7.2 数据库错误

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = db.query(User).get(user_id)
    if not user:
        raise BusinessError(
            ErrorCode.DB_RECORD_NOT_FOUND,
            f"用户 {user_id} 不存在"
        )
    return success(data=user.to_dict())
```

### 7.3 注册异常处理器

```python
from fastapi import FastAPI
from skarner.core.integrations.fastapi.exception_handler import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

### 7.4 响应格式

所有错误响应遵循 `ResponseModel` 格式：

```json
{
  "code": 1001,
  "message": "用户名或密码错误",
  "data": null,
  "trace_id": "abc123def456"
}
```

## 8. 测试策略

### 8.1 单元测试

- **BusinessError**：测试初始化、属性、字符串表示
- **ErrorCode**：测试枚举值、范围正确性
- **get_http_status**：测试各类错误码的 HTTP 状态码映射

### 8.2 集成测试

- **FastAPI 异常处理器**：
  - 抛出 `BusinessError` → 返回正确的 JSON 响应
  - 抛出 `ValueError` → 返回 422 响应
  - 验证响应格式符合 `ResponseModel`
  - 验证 HTTP 状态码正确性

### 8.3 测试原则

- 不依赖外部服务（使用 FastAPI TestClient）
- 覆盖所有错误码范围
- 验证 trace_id 正确传递

## 9. 文档要求

- `core/exceptions/__init__.py`：模块说明和使用示例
- `BusinessError` 类：详细的 docstring
- `ErrorCode` 枚举：每个错误码的中文说明
- `register_exception_handlers`：使用示例
- README 或单独文档：完整的使用指南

## 10. 实现清单

- [ ] 创建 `core/exceptions/codes.py`：定义 `ErrorCode` 枚举
- [ ] 创建 `core/exceptions/base.py`：定义 `BusinessError` 类
- [ ] 创建 `core/exceptions/__init__.py`：导出公共 API
- [ ] 创建 `integrations/fastapi/exception_handler.py`：实现异常处理器
- [ ] 更新 `core/auth/jwt.py`：废弃现有异常类，添加警告
- [ ] 编写单元测试：`tests/test_exceptions.py`
- [ ] 编写集成测试：`tests/integrations/fastapi/test_exception_handler.py`
- [ ] 更新文档：README 或使用指南
- [ ] 更新 TODO.md：标记任务完成

## 11. 约束与限制

- **Python 版本**：>= 3.20（使用 `IntEnum`、类型注解）
- **依赖**：Pydantic（已存在）、FastAPI（可选依赖）
- **向后兼容**：保留现有 JWT 异常类，标记为废弃
- **不破坏现有功能**：所有改动都是增量式的

## 12. 未来扩展

- 支持自定义错误码注册表
- 支持错误码国际化（i18n）
- 支持错误上下文数据（可选扩展）
- 集成到更多框架（Flask、Django 等）
