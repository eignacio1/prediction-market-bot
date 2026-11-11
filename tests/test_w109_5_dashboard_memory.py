"""W108.5 / W109.5: a failed dashboard rebuild is logged and keeps the last good page, and /api/data is encoded without a
str+bytes double copy. (HEAD-following lives in #459, _expire_on_new_head.)"""
import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import web_dashboard as wd  # noqa: E402




def test_failed_rebuild_is_logged_keeps_last_good_and_retries_soon(capsys):
    cache = {"t": time.time() - 1000, "html": "good"}

    def boom():
        raise RuntimeError("disk full")
    wd._serve_cached("h3", cache, "html", 300.0, boom)
    for _ in range(100):
        if cache.get("err"):
            break
        time.sleep(0.05)
    assert cache["html"] == "good" and "RuntimeError: disk full" in cache["err"]
    assert "rebuild of h3 FAILED" in capsys.readouterr().err
    assert time.time() - cache["t"] >= 300.0 - wd._RETRY_AFTER_FAIL_S - 1   # due again within ~15 s, not a full TTL


def test_first_build_failure_uses_fallback():
    cache = {"t": 0.0, "html": ""}

    def boom():
        raise ValueError("x")
    out = wd._serve_cached("h4", cache, "html", 300.0, boom, fallback=lambda e: "fallback:" + type(e).__name__)
    assert out == "fallback:ValueError"





def test_data_body_is_identical_compact_json(monkeypatch):
    monkeypatch.setattr(wd, "_load_all_data", lambda: {"a": [1, 2.5, "é"], "t": Path("/x")})
    assert wd._build_data_body() == json.dumps({"a": [1, 2.5, "é"], "t": "/x"}, separators=(",", ":")).encode("utf-8")
