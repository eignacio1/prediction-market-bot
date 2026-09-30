"""T-595 D1: the snapshot verifier must pass on the real snapshot and FAIL on tampering."""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_provenance_snapshot as v  # noqa: E402


@pytest.fixture()
def snap(tmp_path):
    dst = tmp_path / "snap"
    shutil.copytree(v.DEFAULT_SNAPSHOT, dst)
    return dst


def _fails(snap):
    windows, res = v.run(snap)
    return {k: e for k, e in res.items() if e}, v.verify_manifest(snap)


def test_real_snapshot_validates_13_of_13():
    windows, res = v.run(v.DEFAULT_SNAPSHOT)
    assert len(windows) == 13
    assert all(not e for e in res.values())
    assert v.verify_manifest(v.DEFAULT_SNAPSHOT) == []


def test_missing_journal_start_is_caught(snap):
    p = snap / "vps_journal_t4-mlb_full.txt"
    lines = p.read_text().splitlines()
    w1 = v.pa.load_allowlist(v.ALLOWLIST)[0]
    ps = v._sec(w1["process_started_utc"])
    cited = [l for l in lines if (m := v.STARTED_RE.match(l)) and v._sec(m.group(1) + "+00:00") == ps]
    assert cited
    p.write_text("\n".join(l for l in lines if l not in cited) + "\n")
    bad, merr = _fails(snap)
    assert w1["window_id"] in bad and merr  # window fails AND manifest hash no longer matches


def test_missing_reflog_line_is_caught(snap):
    p = snap / "vps_git_reflog_HEAD_full.txt"
    lines = p.read_text().splitlines()
    p.write_text("\n".join(lines[1:]) + "\n")
    bad, merr = _fails(snap)
    assert merr  # hash mismatch is always caught even if no window cited that line


def test_tampered_blob_is_caught(snap):
    b = sorted((snap / "blobs").iterdir())[0]
    b.write_text(b.read_text() + "\n# tampered\n")
    bad, merr = _fails(snap)
    assert any("blob object id" in x for e in bad.values() for x in e)
    assert merr


def test_extent_mismatch_is_caught(snap):
    p = snap / "vps_cycle_log_session_extents.json"
    d = json.loads(p.read_text())
    sid = next(iter(d["sessions"]))
    for k in d["sessions"]:
        d["sessions"][k]["rows"] += 1
    p.write_text(json.dumps(d))
    bad, _ = _fails(snap)
    assert any("cycle rows" in x for e in bad.values() for x in e)


def test_unlisted_extra_file_is_caught(snap):
    (snap / "extra.txt").write_text("x")
    _, merr = _fails(snap)
    assert any("not in manifest" in x for x in merr)
