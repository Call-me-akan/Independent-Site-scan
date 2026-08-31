"""Tee logging: mirror stdout/stderr to console AND a rotating log file.

Ensures packaged binaries (no visible console) still persist logs at a
predictable location so users can share them for troubleshooting.

Log file location:  <data_dir>/logs/monitor.log
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
BACKUP_COUNT = 2

_orig_stdout = sys.stdout
_orig_stderr = sys.stderr
_started = False
_lock = threading.Lock()
_log_file: Path | None = None


class _Tee:
    def __init__(self, stream, file_path: Path):
        self._stream = stream
        self._file_path = file_path

    def write(self, message: str):
        with _lock:
            self._stream.write(message)
            try:
                with self._file_path.open("a", encoding="utf-8", errors="replace") as f:
                    f.write(message)
            except OSError:
                pass  # 日志写入失败不影响主流程
        return len(message)

    def flush(self):
        with _lock:
            try:
                self._stream.flush()
            except Exception:
                pass

    def isatty(self) -> bool:
        try:
            return self._stream.isatty()
        except Exception:
            return False

    def fileno(self) -> int:
        return self._stream.fileno()


def _rotate(log_file: Path) -> None:
    """Simple size-based rotation: monitor.log -> monitor.log.1 -> monitor.log.2"""
    try:
        if log_file.exists() and log_file.stat().st_size > MAX_BYTES:
            for i in range(BACKUP_COUNT, 0, -1):
                src = log_file if i == 1 else log_file.with_suffix(f".log.{i-1}")
                dst = log_file.with_suffix(f".log.{i}")
                if src.exists():
                    dst.unlink(missing_ok=True)
                    src.rename(dst)
    except OSError:
        pass


def setup_file_logging(data_dir: str | Path) -> Path:
    """Redirect stdout/stderr to console + <data_dir>/logs/monitor.log. Idempotent."""
    global _started, _log_file
    if _started and _log_file is not None:
        return _log_file
    log_dir = Path(data_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "monitor.log"
    _rotate(log_file)
    sys.stdout = _Tee(_orig_stdout, log_file)
    sys.stderr = _Tee(_orig_stderr, log_file)
    _started = True
    _log_file = log_file
    return log_file


def _current_log_path() -> Path:
    return _log_file or Path("monitor.log")


def log_path_hint() -> str:
    """Human-readable hint about where logs live."""
    return "~/monitor-agent/logs/monitor.log"