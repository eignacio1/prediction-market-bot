"""W119.4 / B-103: one place to read append-only JSONL evidence that may be stored plain (``X.jsonl``) or compressed
(``X.jsonl.gz``) by ``disk_retention``. Zero dependencies beyond the stdlib so a script can import it with only ``src/`` on the path.

  open_jsonl(path)          -> text handle (default) or bytes handle (mode 'rb') on ``path`` or ``path + '.gz'``; read-only.
  iter_jsonl(path)          -> yields each non-blank line parsed as JSON (blank lines skipped).
  jsonl_files(dir, pattern) -> sorted PLAIN names matching ``pattern`` (pattern WITHOUT '.gz'), each once, whether stored plain or .gz.
  glob_files(pattern)       -> same as jsonl_files for a full glob string.
  resolve(path)             -> the path that exists on disk (plain wins; else .gz); FileNotFoundError when neither.

Compression never deletes data and ``disk_retention`` verifies the decompressed bytes' sha256 before replacing a file, so a reader
that goes through this module sees byte-identical content before and after.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
from pathlib import Path
from typing import Iterator

GZ = ".gz"


def jsonl_files(directory, pattern: str) -> list:
    """Sorted plain-name paths matching ``pattern`` in ``directory``; a day stored only as ``.gz`` is listed under its plain name."""
    base = str(Path(directory) / pattern)
    names = set(glob.glob(base)) | {p[:-len(GZ)] for p in glob.glob(base + GZ)}
    return sorted(names)


def jsonl_paths(directory, pattern: str) -> list:
    """``jsonl_files`` returning ``pathlib.Path`` objects (for readers that iterate ``Path.glob`` results)."""
    return [Path(p) for p in jsonl_files(directory, pattern)]


def glob_files(pattern) -> list:
    """Like ``sorted(glob.glob(pattern))`` but a match stored only as ``.gz`` is listed under its plain name (pattern WITHOUT '.gz')."""
    base = str(pattern)
    names = set(glob.glob(base)) | {p[:-len(GZ)] for p in glob.glob(base + GZ)}
    return sorted(names)


def resolve(path) -> str:
    p = str(path)
    if os.path.exists(p):
        return p
    if os.path.exists(p + GZ):
        return p + GZ
    raise FileNotFoundError(p)


def open_jsonl(path, mode: str = "r", encoding: str = "utf-8"):
    """Open ``path`` or ``path.gz`` for reading. ``mode`` is 'r' (text) or 'rb'. Passing a '.gz' path directly also works."""
    if mode not in ("r", "rt", "rb"):
        raise ValueError("open_jsonl is read-only; got mode %r" % mode)
    real = resolve(path)
    if real.endswith(GZ):
        return gzip.open(real, "rb") if "b" in mode else gzip.open(real, "rt", encoding=encoding)
    return open(real, "rb") if "b" in mode else open(real, "r", encoding=encoding)


def iter_jsonl(path) -> Iterator[dict]:
    with open_jsonl(path) as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)
