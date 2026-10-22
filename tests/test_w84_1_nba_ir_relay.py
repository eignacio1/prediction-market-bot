"""W84.1 / GG-1030: relay of the official NBA injury PDFs when the box's IP is 403'd."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nba_ir_relay as relay  # noqa: E402
import nba_lineup_window_capture as cap  # noqa: E402

NOW = datetime(2026, 10, 21, 21, 10, tzinfo=timezone.utc)  # 17:10 ET


def test_relay_stores_bytes_untouched_and_skips_known(tmp_path):
    body = b"%PDF-fake"
    seen = []

    def get(url, timeout, headers):
        seen.append(url)
        return SimpleNamespace(status_code=200, content=body, headers={"Last-Modified": "Wed, 21 Oct 2026 21:02:01 GMT"})

    first = cap.slot_url(cap.slot_candidates(NOW)[0]).rsplit("/", 1)[1]
    rows = relay.relay(tmp_path, NOW, {first}, get=get)
    assert first not in [r["file"] for r in rows] and len(rows) == 2
    assert all(r["sha256"] == hashlib.sha256(body).hexdigest() for r in rows)
    assert (tmp_path / rows[0]["file"]).read_bytes() == body


def test_relay_ignores_non_200(tmp_path):
    get = lambda url, timeout, headers: SimpleNamespace(status_code=403, content=b"", headers={})  # noqa: E731
    assert relay.relay(tmp_path, NOW, set(), get=get) == []


def test_capture_falls_back_to_relay_branch_with_verified_bytes():
    body = b"%PDF-official"
    name = cap.slot_url(cap.slot_candidates(NOW)[0]).rsplit("/", 1)[1]
    manifest = json.dumps({"file": name, "sha256": hashlib.sha256(body).hexdigest(),
                           "last_modified": "Wed, 21 Oct 2026 21:02:01 GMT"}) + "\n"

    def git(*a):
        if a[0] == "fetch":
            return SimpleNamespace(returncode=0, stdout=b"")
        if a[-1].endswith("manifest.jsonl"):
            return SimpleNamespace(returncode=0, stdout=manifest.encode())
        return SimpleNamespace(returncode=0, stdout=body)

    rep = cap.relay_fetch_report(NOW, git=git)
    assert rep["content"] == body and rep["published_utc"] == "2026-10-21T21:02:01Z" and rep["via"] == "relay"


def test_capture_rejects_relay_blob_whose_hash_does_not_match():
    name = cap.slot_url(cap.slot_candidates(NOW)[0]).rsplit("/", 1)[1]
    manifest = (json.dumps({"file": name, "sha256": "0" * 64, "last_modified": None}) + "\n").encode()
    git = lambda *a: SimpleNamespace(returncode=0, stdout=manifest if a[-1].endswith("manifest.jsonl") else b"tampered")  # noqa: E731
    assert cap.relay_fetch_report(NOW, git=git) is None
