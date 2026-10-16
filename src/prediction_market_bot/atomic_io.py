"""Crash-safe file writes and corrupt-file quarantine for ledger state (W72.2, GG-663/664/672).

atomic_write_json / atomic_write_text: tmp file in the same directory + fsync + os.replace, so a crash
mid-write leaves the previous file intact (never a truncated one). quarantine() renames an unreadable
ledger aside and alarms; callers then halt instead of starting a fresh state over the evidence.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - non-POSIX
    _HAS_FCNTL = False

_log = logging.getLogger(__name__)


class LedgerCorruptError(RuntimeError):
    """A ledger file could not be read; it was quarantined and the writer must halt."""


class LedgerWriteError(RuntimeError):
    """A ledger write failed; the previous file is intact but the mutation was NOT persisted."""


def alarm(msg: str) -> None:
    _log.critical(msg)
    print(f"LEDGER ALARM: {msg}", file=sys.stderr, flush=True)


def _fsync_dir(directory: Path) -> None:
    try:
        fd = os.open(str(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_text(path: Path | str, text: str) -> None:
    path = Path(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    _fsync_dir(path.parent)


@contextmanager
def file_lock(path: Path | str) -> Iterator[None]:
    """Exclusive cross-process flock on <path>.lock (W76.3, GG-748).

    Same lock file PaperTrader._file_lock uses for a portfolio JSON, so a script rewriting a live
    ledger and the runner appending to it serialise against each other. Blocks until acquired.
    """
    if not _HAS_FCNTL:  # pragma: no cover - non-POSIX fallback
        yield
        return
    path = Path(path)
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = open(lock_path, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def atomic_write_json(path: Path | str, obj: Any, *, indent: int | None = 2) -> None:
    atomic_write_text(path, json.dumps(obj, indent=indent))


def quarantine(path: Path | str, reason: str) -> Path:
    """Rename an unreadable ledger to <name>.corrupt.<epoch-ns> (never overwrites) and alarm."""
    import time

    path = Path(path)
    dest = path.with_name(f"{path.name}.corrupt.{time.time_ns()}")
    try:
        os.replace(path, dest)
    except OSError as e:
        alarm(f"{path}: unreadable ({reason}) AND quarantine rename failed: {e}")
        return path
    alarm(f"{path}: unreadable ({reason}); quarantined to {dest.name}; writer halted")
    return dest
