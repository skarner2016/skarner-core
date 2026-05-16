# skarner-core

Python 基础设施库，为分布式服务提供认证、追踪、限流、日志、数据库连接等核心能力。

## 安装

```bash
# 基础安装
pip install skarner-core

# 含 MySQL 支持
pip install "skarner-core[mysql]"

# 含 PostgreSQL 支持
pip install "skarner-core[postgresql]"
```

## 模块概览

| 模块 | 功能 |
|------|------|
| `skarner.core.auth` | JWT 令牌签发与验证 |
| `skarner.core.tracing` | 分布式 Trace ID 生成与传播 |
| `skarner.core.ratelimit` | 滑动窗口限流（内存 / Redis） |
| `skarner.core.logging` | 结构化日志，自动注入 Trace ID |
| `skarner.core.db` | SQLAlchemy 2.x 异步数据库连接 |
| `skarner.core.integrations.fastapi` | FastAPI 中间件与依赖注入 |

---

## 使用示例

### JWT 认证

```python
from skarner.core.auth import JWTManager, JWTExpiredError, JWTDecodeError

jwt = JWTManager(secret="your-secret-key")

# 签发令牌，有效期 3600 秒
token = jwt.encode({"user_id": 42, "role": "admin"}, expires_in=3600)

# 验证并解码
try:
    payload = jwt.decode(token)
    print(payload["user_id"])  # 42
except JWTExpiredError:
    print("令牌已过期")
except JWTDecodeError:
    print("令牌无效")
```

---

### 分布式追踪

```python
from skarner.core.tracing import generate_trace_id, set_trace_id, get_trace_id

# 在请求入口生成并存储 Trace ID
trace_id = generate_trace_id()
set_trace_id(trace_id)

# 在任意下游代码中获取（异步安全）
print(get_trace_id())  # e.g. "a3f1c2d4e5b6..."
```

---

### 限流

```python
from skarner.core.ratelimit import MemoryRateLimiter

limiter = MemoryRateLimiter()

result = limiter.limit("user:42:/api/feed", rate=10, per_seconds=60)
if result.allowed:
    print(f"通过，剩余配额: {result.remaining}")
else:
    print("已触发限流")
```

多进程部署时使用 `RedisRateLimiter`：

```python
import redis.asyncio as aioredis
from skarner.core.ratelimit import RedisRateLimiter

redis_client = aioredis.from_url("redis://localhost:6379")
limiter = RedisRateLimiter(redis_client)
```

---

### 结构化日志

```python
import logging
from skarner.core.logging import setup_logging, get_logger
from skarner.core.tracing import set_trace_id, generate_trace_id

setup_logging(level=logging.INFO, log_dir="logs")

set_trace_id(generate_trace_id())

log = get_logger(__name__)
log.info("用户登录")
# 输出: 2026-05-16 10:00:00 [INFO] [trace_id=a3f1c2d4...] __main__ - 用户登录
```

---

### 数据库连接（异步 MySQL / PostgreSQL）

```python
from sqlalchemy import text
from skarner.core.db import DatabaseConfig, DatabaseDialect, create_engine, AsyncSessionManager

# MySQL
config = DatabaseConfig(
    dialect=DatabaseDialect.MYSQL,
    host="localhost",
    port=3306,
    user="root",
    password="secret",
    database="mydb",
    pool_size=10,
    max_overflow=20,
)

# PostgreSQL
# config = DatabaseConfig(
#     dialect=DatabaseDialect.POSTGRESQL,
#     host="localhost",
#     port=5432,
#     user="admin",
#     password="secret",
#     database="pgdb",
# )

engine = create_engine(config)
db = AsyncSessionManager(engine)

async def get_users():
    async with db.session() as session:
        result = await session.execute(text("SELECT id, name FROM users LIMIT 10"))
        return result.fetchall()

# 应用退出时释放连接池
async def shutdown():
    await db.close()
```

---

### FastAPI 完整集成示例

```python
from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text

from skarner.core.auth import JWTManager, JWTDecodeError
from skarner.core.db import AsyncSessionManager, DatabaseConfig, DatabaseDialect, create_engine
from skarner.core.integrations.fastapi import TraceIDMiddleware, rate_limit
from skarner.core.logging import get_logger, setup_logging
from skarner.core.ratelimit import MemoryRateLimiter

setup_logging(level=logging.INFO, log_dir="logs")
log = get_logger(__name__)

jwt = JWTManager(secret="your-secret-key")
limiter = MemoryRateLimiter()

db_config = DatabaseConfig(
    dialect=DatabaseDialect.POSTGRESQL,
    host="localhost",
    port=5432,
    user="admin",
    password="secret",
    database="myapp",
)
engine = create_engine(db_config)
db = AsyncSessionManager(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(TraceIDMiddleware)  # 自动注入 x-trace-id


@app.get("/users/me")
async def get_me(
    token: str,
    _=Depends(rate_limit(limiter, rate=30, per_seconds=60)),
):
    try:
        payload = jwt.decode(token)
    except JWTDecodeError:
        raise HTTPException(status_code=401, detail="invalid token")

    user_id = payload["user_id"]
    log.info("fetching user", extra={"user_id": user_id})

    async with db.session() as session:
        row = await session.execute(
            text("SELECT id, name FROM users WHERE id = :id"),
            {"id": user_id},
        )
        user = row.fetchone()

    return {"id": user.id, "name": user.name}
```

---

## 开发

```bash
# 构建测试镜像并运行全部测试
docker build -f Dockerfile.test -t skarner-core-test .
docker run --rm skarner-core-test pytest tests/ -v
```
