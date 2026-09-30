#!/usr/bin/env python3
"""T-595 / Wave 41 D1: re-validate the T4M-PROJ provenance allowlist against the
in-repo evidence snapshot ALONE. No VPS access, no network, no git repo access.

Beyond `load_allowlist` (which only checks that citation text is non-empty), each
of the 13 windows is checked against the captured record:
  journal   a 'Started t4-mlb.service' event at process_started_utc, and none
            strictly inside (window_start, window_end]
  reflog    a HEAD line carrying commit_sha at commit_sha_became_head_utc; HEAD
            at process start == commit_sha (no later move before start); no
            reset/checkout inside the window; every head_moves_after_start entry
            exists and post-dates process start
  extents   cycle-log session first/last ts == window bounds (to the second)
  code      blob git-object-id == VPS-reported id; sha256 of the
            p_hits_gte_threshold source segment == allowlist value; call site
            passes ba_l10=ba_l10_shrunk
Also verifies every snapshot file against MANIFEST.json sha256.

Compute/verify only: writes nothing unless --write-manifest is passed.
Usage: python3 scripts/verify_provenance_snapshot.py [--snapshot DIR] [--write-manifest]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import provenance_allowlist_recompute as pa  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "05_RESEARCH_EXPERIMENTS/provenance/snapshot_2026-09-30"
ALLOWLIST = ROOT / "05_RESEARCH_EXPERIMENTS/provenance/t4m_proj_provenance_allowlist.json"
REFLOG_RE = re.compile(r"^([0-9a-f]{40}) HEAD@\{(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \+0000\} \| (.*)$")
STARTED_RE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\.\d+\+00:00 \S+ systemd\[1\]: Started t4-mlb\.service")


def _sec(ts: str) -> datetime:
    """Parse any ISO-8601 (with Z / offset / micros / space) to UTC, truncated to the second."""
    ts = ts.replace("Z", "+00:00")
    d = datetime.fromisoformat(ts)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).replace(microsecond=0)


def parse_reflog(path: Path) -> list[tuple[str, datetime, str]]:
    out = []
    for line in path.read_text().splitlines():
        m = REFLOG_RE.match(line)
        if m:
            out.append((m.group(1), _sec(m.group(2) + "+00:00"), m.group(3)))
    return out  # file order = newest first


def parse_starts(path: Path) -> list[datetime]:
    return [_sec(m.group(1) + "+00:00") for l in path.read_text().splitlines() if (m := STARTED_RE.match(l))]


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def func_segment_sha(src: str, name: str = "p_hits_gte_threshold") -> str:
    fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == name)
    return hashlib.sha256(ast.get_source_segment(src, fn).encode()).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot_files(snap: Path) -> list[Path]:
    return sorted(p for p in snap.rglob("*") if p.is_file() and p.name != "MANIFEST.json")


def verify_manifest(snap: Path) -> list[str]:
    errs = []
    man = json.loads((snap / "MANIFEST.json").read_text())
    listed = {f["path"]: f["sha256"] for f in man["files"]}
    actual = {str(p.relative_to(snap)): sha256_file(p) for p in snapshot_files(snap)}
    for k, v in listed.items():
        if k not in actual:
            errs.append(f"manifest lists missing file {k}")
        elif actual[k] != v:
            errs.append(f"sha256 mismatch {k}")
    for k in actual:
        if k not in listed:
            errs.append(f"file not in manifest {k}")
    return errs


def verify_window(w: dict, snap: Path, reflog, starts, extents, blob_ids) -> list[str]:
    e: list[str] = []
    wid = w["window_id"]
    a, b = _sec(w["window_start_utc"]), _sec(w["window_end_utc"])
    ps = _sec(w["process_started_utc"])
    # journal
    if ps not in starts:
        e.append(f"{wid} journal: no 'Started t4-mlb.service' at {w['process_started_utc']}")
    inside = [s for s in starts if a < s <= b]
    if inside:
        e.append(f"{wid} journal: Started event(s) inside window: {inside}")
    # reflog
    became = _sec(w["commit_sha_became_head_utc"])
    if not any(sha == w["commit_sha"] and t == became for sha, t, _ in reflog):
        e.append(f"{wid} reflog: no HEAD line {w['commit_sha'][:8]} at {w['commit_sha_became_head_utc']}")
    head_at_start = next((sha for sha, t, _ in reflog if t <= ps), None)
    if head_at_start != w["commit_sha"]:
        e.append(f"{wid} reflog: HEAD at process start is {str(head_at_start)[:8]}, not {w['commit_sha'][:8]}")
    bad = [(t, s) for _, t, s in reflog if a <= t <= b and s.startswith(("reset", "checkout"))]
    if bad:
        e.append(f"{wid} reflog: reset/checkout inside window: {bad}")
    for mv in w.get("head_moves_after_start_not_loaded", []):
        sha, when = mv["sha7"], _sec(mv["utc"])
        hits = [t for s_, t, _ in reflog if s_.startswith(sha)]
        if when not in hits:
            e.append(f"{wid} reflog: head_moves_after_start entry {sha} @ {mv['utc']} not in reflog")
        elif not when > ps:
            e.append(f"{wid} reflog: head_moves_after_start entry {sha} does not post-date process start")
    # cycle-log extent
    ex = extents.get(w["session_id"])
    if not ex:
        e.append(f"{wid} extents: session {w['session_id']} absent")
    else:
        if _sec(ex["first_ts"]) != a or _sec(ex["last_ts"]) != b:
            e.append(f"{wid} extents: {ex['first_ts']}..{ex['last_ts']} != window {w['window_start_utc']}..{w['window_end_utc']}")
        m = re.search(r"(\d+) cycle rows", w["citation"]["session_to_process"])
        if m and int(m.group(1)) != ex["rows"]:
            e.append(f"{wid} extents: cited {m.group(1)} cycle rows, snapshot has {ex['rows']}")
    # code
    bp = snap / "blobs" / f"run_t4_mlb_live.py.{w['commit_sha']}"
    if not bp.exists():
        e.append(f"{wid} code: blob file absent")
    else:
        data = bp.read_bytes()
        if git_blob_id(data) != blob_ids.get(w["commit_sha"]):
            e.append(f"{wid} code: blob object id != VPS-reported id")
        src = data.decode()
        if func_segment_sha(src) != w["p_hits_gte_threshold_sha256"]:
            e.append(f"{wid} code: p_hits_gte_threshold sha256 differs from allowlist")
        if w["call_uses_ba_l10_shrunk"] and not re.search(r"ba_l10\s*=\s*ba_l10_shrunk", src):
            e.append(f"{wid} code: call site does not pass ba_l10=ba_l10_shrunk")
    return e


def run(snap: Path, allowlist: Path = ALLOWLIST) -> tuple[list[dict], dict[str, list[str]]]:
    windows = pa.load_allowlist(allowlist)  # raises on malformed
    reflog = parse_reflog(snap / "vps_git_reflog_HEAD_full.txt")
    starts = parse_starts(snap / "vps_journal_t4-mlb_full.txt")
    extents = json.loads((snap / "vps_cycle_log_session_extents.json").read_text())["sessions"]
    blob_ids = dict(l.split() for l in (snap / "vps_git_blob_ids.txt").read_text().splitlines() if l.strip())
    return windows, {w["window_id"]: verify_window(w, snap, reflog, starts, extents, blob_ids) for w in windows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    ap.add_argument("--write-manifest", action="store_true", help="(re)compute sha256 for every file into MANIFEST.json")
    args = ap.parse_args()
    snap = args.snapshot
    if args.write_manifest:
        man = json.loads((snap / "MANIFEST.json").read_text())
        man["files"] = [{"path": str(p.relative_to(snap)), "bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in snapshot_files(snap)]
        (snap / "MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n")
        print(f"manifest written: {len(man['files'])} files")
        return 0
    merr = verify_manifest(snap)
    windows, res = run(snap)
    print(f"manifest: {'OK' if not merr else 'FAIL'} ({len(merr)} problems)")
    for m in merr:
        print("  ", m)
    ok = 0
    for w in windows:
        errs = res[w["window_id"]]
        ok += not errs
        print(f"{w['window_id']}: {'VALID' if not errs else 'INVALID'}")
        for x in errs:
            print("   ", x)
    print(f"{ok}/{len(windows)} windows validate from the snapshot alone")
    return 0 if (ok == len(windows) and not merr) else 1


if __name__ == "__main__":
    sys.exit(main())
