"""Stored-file hash sidecar for the NBA event store (W79.3).

The W78.4 manifest's ``source_sha256`` is the hash of the bytes downloaded from the release, not of the parquet
we store (columns ``_source``/``_as_of`` are added on write), so it cannot verify a copy of the store. This
module writes ``store_file_hashes.json`` (sha256 + size of every stored file, keyed by manifest ``store_file``)
and verifies any store root against it - used to prove the VPS copy is byte-identical to the build machine's.

    python3 -m prediction_market_bot.c1_signal_ingestion.nba_store_verify write  [ROOT]
    python3 -m prediction_market_bot.c1_signal_ingestion.nba_store_verify verify [ROOT]
Exit 0 only if every manifest file is present with matching size and sha256.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = REPO / "exp_output" / "NBA_EVENTS"
MANIFEST = REPO / "02_ARCHITECTURE_DESIGN" / "NBA_ENGINE" / "event_store_manifest.json"
SIDECAR = REPO / "02_ARCHITECTURE_DESIGN" / "NBA_ENGINE" / "store_file_hashes.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def store_files(manifest_path: Path = MANIFEST) -> list:
    return [f["store_file"] for f in json.loads(manifest_path.read_text())["files"]]


def write_sidecar(root: Path = DEFAULT_ROOT, manifest_path: Path = MANIFEST, out: Path = SIDECAR) -> dict:
    files = {}
    for rel in store_files(manifest_path):
        p = root / rel
        files[rel] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    doc = {"manifest_build_as_of": json.loads(manifest_path.read_text())["build_as_of"], "files": files}
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return doc


def verify(root: Path = DEFAULT_ROOT, sidecar: Path = SIDECAR) -> list:
    """Return a list of problems (empty = byte-identical to the sidecar)."""
    doc = json.loads(sidecar.read_text())
    problems = []
    for rel, want in doc["files"].items():
        p = root / rel
        if not p.exists():
            problems.append(f"MISSING {rel}")
        elif p.stat().st_size != want["bytes"]:
            problems.append(f"SIZE {rel}: {p.stat().st_size} != {want['bytes']}")
        elif sha256_file(p) != want["sha256"]:
            problems.append(f"SHA {rel}")
    return problems


def main(argv: Optional[list] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "verify"
    root = Path(argv[1]) if len(argv) > 1 else DEFAULT_ROOT
    if cmd == "write":
        doc = write_sidecar(root)
        print(f"wrote {SIDECAR.name}: {len(doc['files'])} files")
        return 0
    problems = verify(root)
    for p in problems:
        print(p, file=sys.stderr)
    print(f"verify {root}: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
