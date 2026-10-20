#!/usr/bin/env python3
"""doc_registry.py — W80.4 / GG-074: foundation-doc registry check. ALARM-ONLY.

Reads 00_ADMIN/DOC_REGISTRY.toml and prints one line per problem:
  UNREGISTERED  a tracked file under a covered path is not in the registry
  MISSING       a registered path no longer exists
  STALE         a LIVING doc is older than its max_age_days
Prints nothing when clean. Always exits 0 unless --strict is passed.
Age of a LIVING doc = days since `last_verified`, else since its last git commit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys

try:  # python 3.11+; local dev machines may be older
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = "00_ADMIN/DOC_REGISTRY.toml"


def _mini_parse(text: str) -> dict:
    """Fallback for the registry's flat shape: `covered = [..]` and `[[doc]]` tables of scalars."""
    out: dict = {"doc": []}
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[doc]]":
            cur = {}
            out["doc"].append(cur)
        elif line.startswith("covered"):
            out["covered"] = re.findall(r'"([^"]*)"', line)
        elif "=" in line and cur is not None:
            k, v = (s.strip() for s in line.split("=", 1))
            cur[k] = int(v) if re.fullmatch(r"\d+", v) else v.strip('"')
    return out


def load(root: pathlib.Path) -> dict:
    text = (root / REGISTRY).read_text()
    return tomllib.loads(text) if tomllib else _mini_parse(text)


def _git(root: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True).stdout.strip()


def check(root: pathlib.Path, today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    reg = load(root)
    docs = {d["path"]: d for d in reg.get("doc", [])}
    covered = tuple(reg.get("covered", []))
    problems = []
    tracked = [p for p in _git(root, "ls-files").splitlines() if p.startswith(covered)]
    for p in sorted(tracked):
        if p not in docs:
            problems.append(f"UNREGISTERED {p}")
    for p, d in sorted(docs.items()):
        if not (root / p).exists():
            problems.append(f"MISSING {p}")
            continue
        if d.get("class") != "LIVING":
            continue
        stamp = d.get("last_verified") or _git(root, "log", "-1", "--format=%as", "--", p)
        try:
            age = (today - dt.date.fromisoformat(stamp)).days
        except ValueError:
            problems.append(f"STALE {p} (no verification date)")
            continue
        if age > int(d.get("max_age_days", 180)):
            problems.append(f"STALE {p} (age {age}d > {d.get('max_age_days', 180)}d, owner {d.get('owner')})")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["check"])
    ap.add_argument("--strict", action="store_true", help="exit 1 on any problem (off by default; alarm-only)")
    args = ap.parse_args(argv)
    problems = check(ROOT)
    for p in problems:
        print(p)
    return 1 if (args.strict and problems) else 0


if __name__ == "__main__":
    sys.exit(main())
