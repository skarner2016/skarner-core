# Project: skarner-core

## 1. Project Overview

This is a Python infrastructure library providing reusable core components:

- JWT handling (sign/verify)
- Trace ID generation and propagation
- Rate limiting (memory and Redis)

The project follows a modular, extensible architecture and is intended for reuse across multiple FastAPI services.

---

## 2. Tech Stack

- Python >= 3.20
- Package manager: uv
- Packaging: pyproject.toml (PEP 621)
- Layout: src-based
- Optional integrations: FastAPI, Redis

---

## 3. Project Structure (STRICT)

You MUST follow this structure exactly:

src/
  skarner/
    core/
      auth/
      tracing/
      ratelimit/
      config/
      integrations/
        fastapi/

Do NOT:
- Create flat utils dumping ground
- Mix FastAPI logic into core modules
- Introduce new top-level modules without justification

---

## 4. Design Principles

### 4.1 Separation of Concerns

- core modules must be framework-agnostic
- FastAPI-specific logic MUST go under `integrations/fastapi`

---

### 4.2 API Design

- Prefer explicit classes over implicit globals
- Avoid hidden state
- All public APIs must be deterministic

---

### 4.3 Extensibility

Each module must support extension:

- ratelimit:
  - base interface
  - memory implementation
  - redis implementation

Do NOT hardcode implementations.

---

### 4.4 Minimal Dependencies

- Do not introduce heavy dependencies unless necessary
- Core modules must not depend on FastAPI
- Redis is optional (only in redis backend)

---

## 5. Module Specifications

---

### 5.1 auth.jwt

Implement a `JWTManager` class:

Responsibilities:
- encode(payload, expires_in)
- decode(token)
- support HS256

Constraints:
- Use pyjwt
- No global secret
- Secret must be injected

---

### 5.2 tracing

Implement trace ID utilities:

- generate_trace_id() -> str
- use contextvars to store current trace_id

Also provide:

- get_trace_id()
- set_trace_id()

---

### 5.3 ratelimit

Design:

- BaseRateLimiter (abstract)
- MemoryRateLimiter
- RedisRateLimiter

Support:

- limit(key, rate, per_seconds)

Return:
- allowed (bool)
- remaining (int)

---

### 5.4 integrations.fastapi

Provide:

- Middleware for trace_id
- Dependency for rate limit

Do NOT:
- Put business logic here
- Duplicate core logic

---

## 6. Code Style

- Use type hints everywhere
- Follow PEP8
- Prefer small, testable functions
- Avoid over-engineering

---

## 7. Testing

- Write unit tests for each module
- No external services required (mock Redis)

---

## 8. What NOT to do

- Do NOT introduce global singletons
- Do NOT mix concerns across modules
- Do NOT redesign the architecture
- Do NOT rename modules arbitrarily

---

## 9. Output Requirements

When generating code:

- Respect file structure
- Include imports
- Ensure code is runnable
- Do not omit error handling
