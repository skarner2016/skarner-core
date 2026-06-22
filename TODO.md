# TODO — skarner-core 功能补全规划

> 对照业界主流方案（Microsoft FastAPI Template、Full Stack FastAPI Template、FastAPI Best Practices、字节/阿里内部脚手架），梳理当前 starter kit 缺失的能力，按优先级分三层。

---

## 🔴 P0 — 几乎每个服务都需要，必补

| 功能 | 说明 | 现状 |
|---|---|---|
| ✅ **配置管理** (`core.config`) | 基于 `pydantic-settings` 的分层配置：`.env` / `.env.{profile}` / env var，支持 dev/prod profile，与 `DatabaseConfig` 桥接（远端配置中心后续做） | 已实现，待联网安装 `pydantic-settings` 后跑测试验证 |
| **统一异常体系** | `BusinessError(code, message)` + FastAPI 全局 exception_handler，输出标准错误格式 | 缺失 |
| ✅ **统一响应封装** | `ResponseModel[code, data, message, trace_id]` + 便捷 `success()` / `fail()` | 已完成 |
| **健康检查** | `/health`（存活）+ `/ready`（就绪，探 DB/Redis 连通性），K8s 必备 | 缺失 |
| **分页/排序抽象** | 通用 `Page[T]`、`cursor` / `offset` 分页、排序参数解析 | 缺失 |
| **DB 迁移集成** | Alembic 初始化脚本、多环境配置、与 `AsyncSessionManager` 联动 | 缺失 |

---

## 🟡 P1 — 生产环境标配，强烈建议补

| 功能 | 说明 |
|---|---|
| **Metrics / Observability** | Prometheus 指标（QPS、延迟、错误率）+ OpenTelemetry trace 导出；目前只有本地 trace_id |
| **通用 Redis 客户端封装** | ratelimit 模块依赖 redis-py，但没暴露通用 client（连接池、JSON 序列化、key 命名规范） |
| **HTTP Client 封装** | 带重试、超时、trace_id 注入、metrics 的 `httpx.AsyncClient` 工厂，服务间调用必备 |
| **缓存抽象** | `@cached(ttl, key_fn)` 装饰器 + cache-aside 模式，支持内存 / Redis 双后端 |
| **敏感数据脱敏** | 日志 / 响应中的手机号、身份证、token 自动掩码 |
| **Security 工具集** | 密码哈希（argon2 / bcrypt）、CSRF token、XSS 防护头（Helmet 类） |
| **Middleware 集合** | RequestTiming、CORS 规范配置、GZip、AccessLog —— 目前只有 trace 中间件 |

---

## 🟢 P2 — 按业务需要按需补

| 功能 | 适用场景 |
|---|---|
| **对象存储客户端** | S3 / MinIO / 阿里云 OSS 统一接口 |
| **消息队列抽象** | Redis Pub-Sub / RabbitMQ / Kafka 的发布-订阅封装 |
| **任务队列** | ARQ / Celery 异步任务集成 |
| **Feature Flag** | 特性开关，灰度发布 |
| **审计日志** | 关键操作写审计表 / MQ |
| **i18n** | 国际化多语言 |
| **多租户** | 租户隔离、租户级配置 |
| **事件总线** | 领域事件 / 进程内 EventEmitter |

---

## 推荐补全顺序

```
第 1 批（1 周内）：config → 统一响应 → 统一异常 → 健康检查
第 2 批（2 周内）：metrics → HTTP client → Redis 客户端 → Middleware 集合
第 3 批（按需）：缓存 → 对象存储 → MQ → 任务队列
```

---

## 架构备注

当前 `core/` 目录已按 `CLAUDE.md` 规划好 `config/` 占位，但尚未实现。建议**最先做配置管理**——因为它是其他所有模块的基础（DB 连接串、Redis 地址、JWT secret 都应该从配置中心读），补上之后整个 starter kit 才真正「可用」。
