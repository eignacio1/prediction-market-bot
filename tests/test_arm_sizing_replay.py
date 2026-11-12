import json
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("asr", Path(__file__).resolve().parents[1] / "scripts" / "arm_sizing_replay.py")
asr = importlib.util.module_from_spec(spec); spec.loader.exec_module(asr)


def _row(ts, ev, arm, side="yes"):
    return {"ts_utc": ts, "event_ticker": ev, "market_type": "NFL_GAME_TOTAL", "band": "T1_MULTI_DAY", "yes_bid": 0.48,
            "yes_ask": 0.52, "p_yes": 0.6, "router": {"arm": arm, "side": side}}


def test_replay_caps_split_epochs_and_unrouted_rows_dropped(tmp_path):
    rows = [_row("2026-11-10T12:00:00Z", "E1", "RIDE") for _ in range(7)]          # event cap 5.00 binds after 5 flat stakes
    rows += [_row("2026-11-05T12:00:00Z", "E2", "RIDE")]                            # pre-epoch, separate
    rows += [{"ts_utc": "2026-11-10T12:00:00Z", "router": {}}, _row("2026-10-01T00:00:00Z", "E3", "RIDE")]  # no arm / too old
    (tmp_path / "x.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    now = asr._ts("2026-11-12T00:00:00Z")
    out, caps, n = asr.replay(asr.load(tmp_path, now, 14))
    assert n["post"]["RIDE"] == 7 and n["pre"]["RIDE"] == 1
    assert out["post"]["RIDE"]["stake"] == 5.0 and caps["post"][("RIDE", "event")] == 2
    assert out["pre"]["RIDE"]["stake"] == 1.0
    assert "never mixed" in asr.report(out, caps, n, 14, now)
