"""W56.3: /project operational sections -- data present / missing / stale, honest "no data", no zeros."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import generate_project_state as gps  # noqa: E402
import project_ops as po  # noqa: E402

NOW = datetime(2026, 10, 6, 0, 0, tzinfo=timezone.utc)


def _touch(p: Path, text: str = "ok\n", age_h: float = 1.0) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    t = (NOW - timedelta(hours=age_h)).timestamp()
    os.utime(p, (t, t))
    return p


def _no_run(argv):  # systemctl/journalctl/git unavailable (e.g. a Mac)
    return None


def _fake_run(argv):
    if argv[0] == "systemctl":
        unit = argv[2]
        n = "2" if unit.startswith("t4") else "0"
        return f"ActiveState=active\nNRestarts={n}\nActiveEnterTimestamp=Mon 2026-10-05 07:57:14 UTC\n"
    if argv[0] == "journalctl":
        return "2026-10-05T22:30:00+00:00 h kernel: Out of memory: Killed process 1 (python3)\n2026-10-05T22:30:00+00:00 h kernel: oom-kill:constraint=x\n"
    if argv[0] == "git":
        return "a" * 40 + "\n"
    return None


# ── operations ──────────────────────────────────────────────────────────────

def test_operations_present_stale_and_missing(tmp_path):
    _touch(tmp_path / "logs/paper_mlb_cron.log", age_h=3)                       # fresh
    _touch(tmp_path / "logs/resolve_mlb_cron.log", age_h=30)                    # amber
    _touch(tmp_path / "logs/pregame_shadow_settle.log", age_h=60)               # red
    _touch(tmp_path / "logs/nhl_shadow_cron.log", "x\nTraceback (most recent call last):\n", age_h=1)  # error tail
    s = po.sec_operations(tmp_path, NOW)
    r = {x["source"]: x for x in s["rows"]}
    assert r["logs/paper_mlb_cron.log"]["state"] == "ok" and r["logs/paper_mlb_cron.log"]["last_success"]
    assert r["logs/resolve_mlb_cron.log"]["state"] == "warn"
    assert r["logs/pregame_shadow_settle.log"]["state"] == "bad"
    nhl = r["logs/nhl_shadow_cron.log"]
    assert nhl["last_success"] is None and nhl["state"] == "warn"               # never claims success after an error
    assert r["logs/t4_mlb_live_cron.log"]["state"] == "nodata" and r["logs/t4_mlb_live_cron.log"]["last_run"] is None
    assert s["status"] == "bad"


def test_operations_no_logs_dir_is_nodata(tmp_path):
    s = po.sec_operations(tmp_path, NOW)
    assert s["status"] == "nodata" and s["rows"] == [] and s["nodata"]


# ── feeds ───────────────────────────────────────────────────────────────────

def _meta(tmp_path, hours_ago):
    ts = (NOW - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    p = tmp_path / "exp_output/MLB_GAME/cache_w47/games_current.meta.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"refreshed_at": ts, "rows": 1}))


def test_games_cache_stamp_vs_26h_limit(tmp_path):
    _meta(tmp_path, 10)
    assert po.sec_feeds(tmp_path, NOW)["rows"][0]["state"] == "ok"
    _meta(tmp_path, 24)
    assert po.sec_feeds(tmp_path, NOW)["rows"][0]["state"] == "warn"      # inside limit, nearly out
    _meta(tmp_path, 27)
    row = po.sec_feeds(tmp_path, NOW)["rows"][0]
    assert row["state"] == "bad" and row["age_h"] > po.MAX_CACHE_AGE_H


def test_games_cache_missing_or_corrupt_is_nodata(tmp_path):
    assert po.sec_feeds(tmp_path, NOW)["rows"][0]["state"] == "nodata"
    p = tmp_path / "exp_output/MLB_GAME/cache_w47/games_current.meta.json"
    p.parent.mkdir(parents=True)
    p.write_text("{not json")
    row = po.sec_feeds(tmp_path, NOW)["rows"][0]
    assert row["state"] == "nodata" and row["stamp"] is None


# ── services ────────────────────────────────────────────────────────────────

def test_services_present(tmp_path):
    s = po.sec_services(tmp_path, NOW, _fake_run)
    r = {x["label"]: x for x in s["rows"]}
    assert r["t4-mlb service"]["state"] == "warn" and "2 restarts" in r["t4-mlb service"]["value"]
    assert r["pmbot-web-dashboard service"]["state"] == "ok"
    assert r["Kernel OOM kills, 7d (GG-477)"]["state"] == "bad" and r["Kernel OOM kills, 7d (GG-477)"]["value"].startswith("1 killed")
    assert r["VPS HEAD vs origin/main"]["state"] == "ok"
    dec = r["Last deploy's t4-mlb restart decision"]
    assert dec["state"] == "nodata" and dec["value"] is None               # never guessed


def test_services_unavailable_is_nodata_not_zero(tmp_path):
    s = po.sec_services(tmp_path, NOW, _no_run)
    assert all(x["state"] == "nodata" and x["value"] is None for x in s["rows"])
    assert s["status"] == "nodata"


# ── books ───────────────────────────────────────────────────────────────────

def _book(tmp_path, name, rpnl, age_h, init=1000.0):
    ts = (NOW - timedelta(hours=age_h)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    p = tmp_path / "logs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"bankroll_usd": init + rpnl, "initial_bankroll_usd": init, "total_realized_pnl": rpnl,
                             "open_positions": [{}, {}], "last_updated": ts}))


def test_books_drawdown_states(tmp_path):
    _book(tmp_path, "paper_portfolio_mlb.json", -124.44, 1)    # 12.4% -> ok
    _book(tmp_path, "paper_portfolio_mlb_t4.json", -170.0, 50)  # 17% -> warn (>=16%)
    _book(tmp_path, "paper_portfolio_t1_nfl_game_market.json", -210.0, 2)  # 21% -> bad
    s = po.sec_books(tmp_path, NOW)
    st = [r["state"] for r in s["rows"]]
    assert st == ["ok", "warn", "bad"] and s["status"] == "bad"
    r0 = s["rows"][0]
    assert abs(r0["drawdown"] - 0.12444) < 1e-4 and r0["open_positions"] == 2 and r0["limit"] == 0.20
    assert s["rows"][1]["age_h"] == 50                           # stale age is carried for dimming


def test_books_profit_is_zero_drawdown_and_missing_is_nodata(tmp_path):
    _book(tmp_path, "paper_portfolio_mlb.json", +40.0, 1)
    s = po.sec_books(tmp_path, NOW)
    assert s["rows"][0]["drawdown"] == 0.0 and s["rows"][0]["state"] == "ok"
    assert s["rows"][1]["state"] == "nodata" and "bankroll" not in s["rows"][1]


# ── evidence ────────────────────────────────────────────────────────────────

def test_evidence_counts_rows_and_settled_games(tmp_path):
    d = tmp_path / "data/shadow/nhl"
    _touch(d / "NHL_MONEYLINE_T1.jsonl", '{"a":1}\n{"a":2}\n{"a":3}\n', age_h=2)
    _touch(d / "settled/NHL_MONEYLINE_T1.jsonl",
           '{"event_ticker":"E1","outcome":1}\n{"event_ticker":"E1","outcome":1}\n{"event_ticker":"E2","outcome":0}\n')
    nfl = tmp_path / "exp_output/PREGAME_SHADOW"
    _touch(nfl / "NFL_NFL_SPREAD_T1.jsonl", '{"a":1}\n', age_h=100)
    s = po.sec_evidence(tmp_path, NOW)
    r = {x["cell"]: x for x in s["rows"] if x.get("rows") is not None}
    nhl = r["NHL_MONEYLINE_T1"]
    assert nhl["rows"] == 3 and nhl["settled_games"] == 2 and nhl["judged"] == 2500    # games, not rows
    nf = r["NFL_NFL_SPREAD_T1"]
    assert nf["first"] == 60 and nf["judged"] == 150 and nf["settled_games"] == 0 and nf["age_h"] == 100
    assert "brier" not in json.dumps(s).lower().replace("no brier", "")                # counts only
    mlb = [x for x in s["rows"] if x["sport"] == "MLB"]
    assert mlb and mlb[0]["state"] == "nodata"


def test_evidence_empty_host_is_nodata(tmp_path):
    s = po.sec_evidence(tmp_path, NOW)
    assert s["status"] == "nodata" and all(r["state"] == "nodata" for r in s["rows"])


# ── one broken section never blanks the rest; render ────────────────────────

def test_build_ops_isolates_failures(tmp_path, monkeypatch):
    monkeypatch.setitem(po.SECTIONS, "books", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    out = po.build_ops(tmp_path, NOW, _no_run)
    assert out["books"]["status"] == "nodata" and "boom" in out["books"]["nodata"]
    assert set(out) == set(po.SECTIONS)


def test_render_strip_sections_and_honest_nodata(tmp_path):
    _book(tmp_path, "paper_portfolio_mlb.json", -124.44, 1)
    _touch(tmp_path / "logs/paper_mlb_cron.log", age_h=3)
    ops = po.build_ops(tmp_path, NOW, _no_run)
    st = {"generated": "2026-10-06T00:00:00Z", "repo": "x", "ops": ops, "sections": {
        "git": gps._awaiting("git", "n/a"), "experiments": gps._awaiting("e", "n/a"),
        "governance": gps._awaiting("g", "n/a"), "queue": gps._awaiting("q", "n/a")}}
    html = gps.render_html(st, link_prefix=None)
    for id_ in ("operations", "feeds", "services", "books", "evidence"):
        assert f"href='#{id_}'" in html and f"<section id='{id_}'>" in html     # strip links to every section
    assert "SHADOW · not trading" not in html or "no data" in html             # shadow labelled, evidence absent here
    assert "12.4% / 20%" in html and "no data" in html
    assert "<span class='ok'>●" in html or "class='ok'" in html
    assert "$0.00" not in html and ">0<" not in html                            # no placeholder zeros


def test_render_labels_shadow_and_dims_stale(tmp_path):
    d = tmp_path / "exp_output/PREGAME_SHADOW"
    _touch(d / "MLB_MLB_MONEYLINE_T1.jsonl", '{"a":1}\n', age_h=200)
    ops = po.build_ops(tmp_path, NOW, _no_run)
    st = {"generated": "g", "repo": "x", "ops": ops, "sections": {}}
    html = gps.render_html(st, link_prefix=None)
    assert "SHADOW · not trading" in html and "class='stale'" in html
    assert "of 150 → 150" in html or "150" in html


def test_page_degrades_when_ops_missing_from_state():
    st = {"generated": "g", "repo": "x", "sections": {}}                       # old-shape state, no "ops" key
    html = gps.render_html(st, link_prefix=None)
    assert "no data" in html and "<section id='operations'>" in html


def test_oom_older_than_24h_is_warn_and_none_is_ok(tmp_path):
    old = lambda a: ("2026-10-02T01:00:00+00:00 h kernel: Out of memory: Killed process 1\n" if a[0] == "journalctl" else None)
    row = [r for r in po.sec_services(tmp_path, NOW, old)["rows"] if "OOM" in r["label"]][0]
    assert row["state"] == "warn"
    none = lambda a: ("quiet\n" if a[0] == "journalctl" else None)
    row = [r for r in po.sec_services(tmp_path, NOW, none)["rows"] if "OOM" in r["label"]][0]
    assert row["state"] == "ok" and row["value"] == "0 killed"


def test_old_error_in_log_does_not_mask_a_clean_latest_run(tmp_path):
    body = "ERROR: yesterday\n" + "\n".join(f"line {i}" for i in range(10)) + "\n"
    _touch(tmp_path / "logs/paper_mlb_cron.log", body, age_h=3)
    r = [x for x in po.sec_operations(tmp_path, NOW)["rows"] if x["source"].endswith("paper_mlb_cron.log")][0]
    assert r["state"] == "ok" and r["last_success"]
