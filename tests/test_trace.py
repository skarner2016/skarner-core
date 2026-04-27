import asyncio

import pytest

from skarner.core.tracing import generate_trace_id, get_trace_id, set_trace_id


def test_generate_returns_32_hex_string():
    tid = generate_trace_id()
    assert len(tid) == 32
    assert all(c in "0123456789abcdef" for c in tid)


def test_generate_is_unique():
    assert generate_trace_id() != generate_trace_id()


def test_default_trace_id_is_empty():
    # 新线程中 ContextVar 默认值为空
    import threading
    results = []
    threading.Thread(target=lambda: results.append(get_trace_id())).start()
    # 等线程结束
    import time; time.sleep(0.05)
    assert results[0] == ""


def test_set_and_get():
    set_trace_id("abc123")
    assert get_trace_id() == "abc123"


def test_set_overrides_previous():
    set_trace_id("first")
    set_trace_id("second")
    assert get_trace_id() == "second"


def test_contextvars_isolated_across_async_tasks():
    async def task(trace_id: str) -> str:
        set_trace_id(trace_id)
        await asyncio.sleep(0)
        return get_trace_id()

    async def main():
        results = await asyncio.gather(task("trace-aaa"), task("trace-bbb"))
        assert set(results) == {"trace-aaa", "trace-bbb"}

    asyncio.run(main())
