import pytest

from skarner.core.response import CODE_SUCCESS, ResponseModel, fail, success
from skarner.core.tracing import set_trace_id


@pytest.fixture(autouse=True)
def _reset_trace():
    """Reset the trace contextvar so tests don't leak trace_id into each other."""
    set_trace_id("")
    yield
    set_trace_id("")


# --- success ---

def test_success_defaults():
    resp = success()
    assert resp.code == CODE_SUCCESS == 0
    assert resp.message == "ok"
    assert resp.data is None
    assert resp.trace_id == ""


def test_success_with_data():
    resp = success({"id": 1, "name": "alice"})
    assert resp.code == 0
    assert resp.data == {"id": 1, "name": "alice"}


def test_success_generic_parametrization():
    resp: ResponseModel[list[int]] = success([1, 2, 3])
    assert resp.data == [1, 2, 3]


def test_success_auto_injects_trace_id():
    set_trace_id("t-123")
    resp = success(message="done")
    assert resp.trace_id == "t-123"
    assert resp.message == "done"


def test_success_explicit_trace_id_overrides():
    set_trace_id("ctx-trace")
    resp = success(trace_id="explicit")
    assert resp.trace_id == "explicit"


# --- fail ---

def test_fail_basic():
    resp = fail(1001, "invalid param")
    assert resp.code == 1001
    assert resp.message == "invalid param"
    assert resp.data is None


def test_fail_with_data():
    resp = fail(1002, "validation error", data={"field": "email"})
    assert resp.code == 1002
    assert resp.data == {"field": "email"}


def test_fail_zero_code_raises():
    with pytest.raises(ValueError):
        fail(0, "should not allow success code")


def test_fail_auto_injects_trace_id():
    set_trace_id("t-err")
    resp = fail(500, "boom")
    assert resp.trace_id == "t-err"


def test_fail_explicit_trace_id_overrides():
    set_trace_id("ctx")
    resp = fail(500, "boom", trace_id="forced")
    assert resp.trace_id == "forced"


# --- serialization ---

def test_model_dump_has_all_fields():
    set_trace_id("t-dump")
    dumped = success({"k": "v"}).model_dump()
    assert dumped == {
        "code": 0,
        "message": "ok",
        "data": {"k": "v"},
        "trace_id": "t-dump",
    }
