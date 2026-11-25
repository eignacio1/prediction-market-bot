"""W124.4 dense capture: filters, writers, state, budget gate, installer (no network, no crontab)."""
import gzip
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import archive_dense_capture as adc  # noqa: E402
import archive_dense_install as adi  # noqa: E402
from prediction_market_bot import io_jsonl  # noqa: E402

NOW = datetime(2026, 11, 28, 23, 0, tzinfo=timezone.utc)   # 18:00 ET on 28 NOV


def mk(ticker, occ="2026-11-29T03:00:00Z"):
    return {"ticker": ticker, "event_ticker": ticker.rsplit("-", 1)[0], "status": "open", "yes_bid_dollars": "0.40",
            "yes_ask_dollars": "0.44", "occurrence_datetime": occ, "close_time": occ}


def fake(markets_by_series=None, trades=None):
    calls = []

    def f(path, params):
        calls.append((path, dict(params)))
        if path == "/markets":
            return {"markets": (markets_by_series or {}).get(params["series_ticker"], []), "cursor": ""}
        return {"trades": trades or [], "cursor": ""}
    f.calls = calls
    return f


def test_ticker_date_and_sport():
    assert str(adc.ticker_date("KXNBAPTS-26NOV28LALDEN-X-20")) == "2026-11-28"
    assert adc.ticker_date("KXBTC-nonsense") is None
    assert adc.sport_of("KXNHLGOAL-26NOV28") == "NHL" and adc.sport_of("KXMVE-1") is None


def test_props_keep_only_today_et_and_write_gz_readable_by_io_jsonl(tmp_path):
    f = fake({"KXNBAPTS": [mk("KXNBAPTS-26NOV28A-1"), mk("KXNBAPTS-26NOV29B-1")]})
    res = adc.run_props(f, NOW, tmp_path, False)
    assert res["rows"] == 1
    p = tmp_path / "PRICE_ARCHIVE_DENSE" / "props" / "2026-11-28.jsonl.gz"
    rows = [json.loads(l) for l in io_jsonl.open_jsonl(p) if l.strip()]
    assert len(rows) == 1 and rows[0]["ticker"] == "KXNBAPTS-26NOV28A-1"
    assert rows[0]["run_ts"] == "2026-11-28T23:00:00Z" and rows[0]["occurrence_datetime"]   # event timestamps present
    adc.run_props(f, NOW, tmp_path, False)                                                  # second run appends a member
    assert len([l for l in io_jsonl.open_jsonl(p) if l.strip()]) == 2


def test_games_window_uses_estimated_start(tmp_path):
    # NBA occurrence 03:00Z => est start 00:30Z; window opens 21:30Z. NOW 23:00Z is inside; 20:00Z is not.
    f = fake({"KXNBAGAME": [mk("KXNBAGAME-26NOV28X-A")]})
    assert adc.run_games(f, NOW, tmp_path, True)["rows"] == 1
    early = datetime(2026, 11, 28, 20, 0, tzinfo=timezone.utc)
    assert adc.run_games(f, early, tmp_path, True)["rows"] == 0
    late = datetime(2026, 11, 29, 1, 0, tzinfo=timezone.utc)                                # past start + 15 min
    assert adc.run_games(f, late, tmp_path, True)["rows"] == 0


def test_dry_run_writes_nothing_but_counts_bytes(tmp_path):
    f = fake({"KXNBAGAME": [mk("KXNBAGAME-26NOV28X-A")]})
    res = adc.run_games(f, NOW, tmp_path, True)
    assert res["gz_bytes"] > 0 and not list(tmp_path.rglob("*"))


def _fake_prints(trades):
    # NBAPTS market starting 00:30Z on the 29th (window opens 21:30Z on the 28th); NHLGOAL / KXNBASPREAD are not kept families
    m = {"KXNBAPTS": [mk("KXNBAPTS-26NOV28A-1", "2026-11-29T03:00:00Z")], "KXNBAGAME": [mk("KXNBAGAME-26NOV28X-A", "2026-11-29T03:00:00Z")]}
    return fake(m, trades)


def test_prints_filter_dedupe_and_state(tmp_path):
    t = [{"trade_id": "1", "ticker": "KXNBAPTS-26NOV28A-1", "created_time": "2026-11-28T22:59:00Z", "count": 3},
         {"trade_id": "2", "ticker": "KXBTC-26NOV28-X", "created_time": "2026-11-28T22:59:01Z"},
         {"trade_id": "3", "ticker": "KXNHLGOAL-26NOV29A", "created_time": "2026-11-28T22:59:02Z"}]
    f = _fake_prints(t)
    assert adc.run_prints(f, NOW, tmp_path, False)["rows"] == 1
    assert adc.run_prints(f, NOW, tmp_path, False)["rows"] == 0                              # overlap re-read is deduped
    rows = [json.loads(l) for l in io_jsonl.open_jsonl(tmp_path / "TRADE_PRINTS" / "2026-11-28.jsonl.gz") if l.strip()]
    assert [r["trade_id"] for r in rows] == ["1"] and rows[0]["created_time"] and rows[0]["captured_ts"]
    state = json.loads((tmp_path / "TRADE_PRINTS" / "_state.json").read_text())
    assert state["last_ts"] == int(datetime(2026, 11, 28, 22, 59, 2, tzinfo=timezone.utc).timestamp())
    assert f.calls[-1][1]["min_ts"] == state["last_ts"] - adc.PRINT_OVERLAP_S


def test_prints_keep_only_named_families_inside_the_3h_window(tmp_path):
    # start = 03:00Z - 2.5 h = 00:30Z; window = 21:30Z .. 00:45Z
    t = [{"trade_id": "in", "ticker": "KXNBAPTS-26NOV28A-1", "created_time": "2026-11-28T22:00:00Z"},
         {"trade_id": "in2", "ticker": "KXNBAGAME-26NOV28X-A", "created_time": "2026-11-28T22:30:00Z"},
         {"trade_id": "early", "ticker": "KXNBAPTS-26NOV28A-1", "created_time": "2026-11-28T21:00:00Z"},   # > 3 h before start
         {"trade_id": "unlisted", "ticker": "KXNBAPTS-26NOV28B-9", "created_time": "2026-11-28T22:00:00Z"},  # not in the start map
         {"trade_id": "spread", "ticker": "KXNBASPREAD-26NOV28X-A", "created_time": "2026-11-28T22:00:00Z"},
         {"trade_id": "nfl_prop", "ticker": "KXNFLPASSYDS-26NOV28X-A", "created_time": "2026-11-28T22:00:00Z"}]
    f = _fake_prints(t)
    res = adc.run_prints(f, NOW, tmp_path, True)
    assert res["rows"] == 2 and res["start_map"] == 2


def test_print_window_edges():
    s = 1_000_000
    assert adc.print_in_window(s, s - 3 * 3600) and not adc.print_in_window(s, s - 3 * 3600 - 1)
    assert adc.print_in_window(s, s + 900) and not adc.print_in_window(s, s + 901) and not adc.print_in_window(None, s)


def test_start_map_is_cached_in_state_and_relisted_when_stale(tmp_path):
    f = _fake_prints([])
    adc.run_prints(f, NOW, tmp_path, False)
    n = len([c for c in f.calls if c[0] == "/markets"])
    assert n >= len(adc.PRINT_SERIES)
    adc.run_prints(f, NOW + timedelta(minutes=5), tmp_path, False)                           # fresh: no relist
    assert len([c for c in f.calls if c[0] == "/markets"]) == n
    adc.run_prints(f, NOW + timedelta(minutes=25), tmp_path, False)                          # stale: relist
    assert len([c for c in f.calls if c[0] == "/markets"]) == 2 * n


def test_print_families_are_the_ones_h3_named():
    assert {"KXNBAPTS", "KXNBATEAMTOTAL", "KXNBAGAME", "KXNFLGAME"} <= adc.PRINT_SERIES
    assert not any(s.startswith("KXNHL") or s.startswith("KXNFLPASS") for s in adc.PRINT_SERIES)


def test_cut_capture_passes_its_own_gate_at_todays_disk():
    # the 11-25 02:19Z gate read: disk 68%, existing growth -3.1 pct/day (clamped to 0), 24.9 GB total
    ok, why, n = adi.gate({"pct": 68.0, "total_bytes": 24.9e9}, -3.1)
    assert ok and not why and n["new_mb_per_day"] < 99.5 and n["projected_pct_30d"] < 80


def test_runs_per_day_matches_cron_mirror():
    lines = [l for l in (ROOT / "deploy" / "cron.archive_dense").read_text().splitlines() if l and l[0].isdigit()]
    assert len(lines) == 3 and set(adi.OWN_KEYS) == {adi.aci._rr()._cron_key(l)[0] for l in lines}
    assert adc.RUNS_PER_DAY == {"props": 3 * 11, "games": 288, "prints": 288}                # 3/h x hours 6-16; 12/h x 24


def _usage(pct, total=24e9):
    return {"pct": pct, "total_bytes": total, "used_bytes": total * pct / 100, "avail_bytes": total * (1 - pct / 100)}


def test_gate_passes_when_roomy_and_refuses_when_not():
    ok, why, n = adi.gate(_usage(40), 0.05)
    assert ok and not why and n["projected_pct_30d"] < 80
    ok, why, _ = adi.gate(_usage(74), 0.4)                                                  # 74 + 30*(0.4+new) > 80
    assert not ok and any("projected disk" in w for w in why)
    ok, why, _ = adi.gate(_usage(40), None)                                                 # unknown growth never passes
    assert not ok and any("unknown" in w for w in why)
    ok, why, _ = adi.gate(_usage(40), 0.05, doc_limit_rps=2.0)                              # half-limit 1 req/s < burst
    assert not ok and any("request rate" in w for w in why)


def test_measured_burst_rate_is_under_half_the_derived_limit():
    cap = adi.capture_budget()
    assert cap["burst_rps"] < adi.DOC_LIMIT_RPS * adi.RATE_FRACTION


def _inst(**kw):
    state = {"cron": "MAILTO=x\n"}
    ev = {"budget": "GREEN", "head": "abc", "as_of": "now", "red": []}
    reg = [{"key": k, "kind": "cron", "status": "paused"} for k in adi.OWN_KEYS]
    out = adi.install(live_fn=lambda: ev, read=lambda: state["cron"], write=lambda t: state.update(cron=t),
                      backup=lambda c: "bk", reg=reg, **kw)
    return out, state


def test_install_refused_by_gate_leaves_crontab_untouched(capsys):
    out, st = _inst(disk_fn=lambda: (_usage(74), 0.4))
    assert out == 0 and st["cron"] == "MAILTO=x\n" and "REFUSED: BUDGET GATE" in capsys.readouterr().out


def test_install_and_uninstall_roundtrip_when_gate_passes(capsys):
    out, st = _inst(disk_fn=lambda: (_usage(30), 0.02))
    assert out == 0 and st["cron"].startswith("MAILTO=x\n") and st["cron"].count("archive_dense_capture.py") == 3
    assert adi.BEGIN in st["cron"] and adi.END in st["cron"]
    assert adi.uninstall(read=lambda: st["cron"], write=lambda t: st.update(cron=t), backup=lambda c: "bk") == 0
    assert st["cron"] == "MAILTO=x\n"


def test_install_refused_when_disk_unreadable(capsys):
    def boom():
        raise OSError("no disk")
    out, st = _inst(disk_fn=boom)
    assert out == 0 and st["cron"] == "MAILTO=x\n" and "could not read the disk" in capsys.readouterr().out
