import logging
import tempfile
from pathlib import Path

import pytest

from skarner.core.logging import get_logger, setup_logging
from skarner.core.tracing import set_trace_id


@pytest.fixture(autouse=True)
def reset_logging():
    yield
    # 每个用例后关闭所有 handler，避免文件句柄残留
    root = logging.getLogger()
    for h in root.handlers[:]:
        h.close()
        root.removeHandler(h)


def test_console_output_contains_trace_id(capsys):
    set_trace_id("test-trace-001")
    setup_logging(level=logging.INFO)
    get_logger("t").info("hello")
    out = capsys.readouterr().out
    assert "trace_id=test-trace-001" in out
    assert "hello" in out


def test_no_trace_id_shows_dash(capsys):
    set_trace_id("")
    setup_logging(level=logging.INFO)
    get_logger("t").info("msg")
    assert "trace_id=-" in capsys.readouterr().out


def test_file_output_created(tmp_path):
    setup_logging(log_dir=tmp_path)
    get_logger("t").info("to file")
    assert (tmp_path / "app.log").exists()


def test_file_contains_log_message(tmp_path):
    set_trace_id("file-trace-xyz")
    setup_logging(log_dir=tmp_path)
    get_logger("t").info("written to file")
    content = (tmp_path / "app.log").read_text()
    assert "written to file" in content
    assert "trace_id=file-trace-xyz" in content


def test_file_and_console_both_receive_output(tmp_path, capsys):
    set_trace_id("dual-trace")
    setup_logging(log_dir=tmp_path)
    get_logger("t").info("dual output")
    assert "dual output" in capsys.readouterr().out
    assert "dual output" in (tmp_path / "app.log").read_text()


def test_debug_filtered_when_level_info(capsys):
    setup_logging(level=logging.INFO)
    get_logger("t").debug("should not appear")
    assert "should not appear" not in capsys.readouterr().out


def test_log_dir_created_if_not_exists():
    with tempfile.TemporaryDirectory() as base:
        log_dir = Path(base) / "nested" / "logs"
        setup_logging(log_dir=log_dir)
        assert log_dir.is_dir()
