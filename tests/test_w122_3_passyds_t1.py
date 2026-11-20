"""W122.3: NFL_PLAYER_PASS_YDS x T1 layer 1 is credited only from pre24h snapshot rows that carry a model p."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import d6_read  # noqa: E402

SINCE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _write(tmp_path, rows):
    d = tmp_path / "exp_output" / "PREGAME_SHADOW_PASSYDS"
    d.mkdir(parents=True)
    (d / "snap_2026-11-22.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_only_pre24h_with_model_p_counts(tmp_path):
    ts = "2026-11-21T18:00:00Z"
    _write(tmp_path, [
        {"ts_utc": ts, "slot": "pre24h", "model_p": 0.41},
        {"ts_utc": ts, "slot": "pre24h", "model_p": None},      # cold start / QB out: no p, no credit
        {"ts_utc": ts, "slot": "pre30", "model_p": 0.50},       # wrong horizon
        {"ts_utc": ts, "slot": "pre2h", "model_p": 0.50},
    ])
    got = list(d6_read.passyds_t1_rows(SINCE, repo=tmp_path))
    assert got == [{"market_type": "NFL_PLAYER_PASS_YDS", "band": "T1", "p_yes": 0.41, "router": {}}]


def test_missing_store_is_empty(tmp_path):
    assert list(d6_read.passyds_t1_rows(SINCE, repo=tmp_path)) == []
