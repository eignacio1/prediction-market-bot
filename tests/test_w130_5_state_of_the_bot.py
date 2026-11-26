"""W130.5 Part C: state_of_the_bot is read-only, streams counters, never fills a section from memory, and ingests a box result."""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import box_tasks  # noqa: E402
import state_of_the_bot as sob  # noqa: E402

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc)


def test_task_is_allowlisted_and_read_only():
    cmd = box_tasks.TASKS["state_of_the_bot_read"]
    assert cmd.endswith("scripts/state_of_the_bot.py") and "--ingest" not in cmd and "install" not in cmd


def test_count_rows_windows_and_skips_old_files(tmp_path):
    f = tmp_path / "a.jsonl"
    f.write_text("\n".join([
        f'{{"ts_utc": "{(NOW - timedelta(hours=1)).isoformat()}"}}',
        f'{{"ts_utc": "{(NOW - timedelta(days=3)).isoformat()}"}}',
        f'{{"ts_utc": "{(NOW - timedelta(days=9)).isoformat()}"}}', "not json", '{"x": 1}']))
    os.utime(f, (NOW.timestamp(), NOW.timestamp()))
    c = sob.count_rows([f], NOW)
    assert (c["rows_24h"], c["rows_7d"]) == (1, 2)
    old = tmp_path / "old.jsonl"
    old.write_text(f'{{"ts_utc": "{NOW.isoformat()}"}}')
    os.utime(old, (NOW.timestamp() - 9 * 86400,) * 2)
    assert sob.count_rows([old], NOW)["rows_7d"] == 0   # mtime older than 7 d: skipped unread


def test_order_counts_by_sport_and_epoch(tmp_path):
    log = tmp_path / "o.jsonl"
    t = lambda d: (NOW - timedelta(hours=d)).isoformat()  # noqa: E731
    log.write_text("\n".join([
        f'{{"event":"arm_order","ts":"{t(1)}","arm":"RIDE","sport":"nba","ok":true,"order_id":"o1","side":"yes","ticker":"T"}}',
        f'{{"event":"arm_order","ts":"{t(2)}","arm":"RIDE","sport":"nba","ok":false}}',
        f'{{"event":"arm_skip","ts":"{t(30)}","arm":"FADE","sport":"nhl","reason":"spread"}}',
        f'{{"event":"arm_order","ts":"2026-10-01T00:00:00+00:00","arm":"RIDE","sport":"nba","ok":true,"order_id":"old"}}']))
    r = sob.order_counts(log, NOW)
    nba = r["per"]["NBA|RIDE"]
    assert nba["orders_24h"] == 1 and nba["refused_24h"] == 1 and nba["orders_epoch"] == 1   # pre-epoch order not in epoch
    assert r["per"]["NHL|FADE"]["skips_7d"] == 1 and [p["order_id"] for p in r["placed"]] == ["o1"]


def test_fills_by_sport_pnl_and_unlooked_orders():
    placed = [{"sport": "nba", "order_id": "a", "ticker": "T", "side": "yes", "entry_price": 0.4},
              {"sport": "nba", "order_id": "b", "ticker": "T", "side": "yes", "entry_price": 0.4},
              {"sport": "nba", "order_id": "c", "ticker": "T", "side": "yes", "entry_price": 0.4}]
    ans = {"a": {"fills": 1, "settled": True, "won": True, "price": 0.4}, "b": {"fills": 0}}
    out = sob.fills_by_sport(placed, lambda o, t: ans.get(o))
    n = out["NBA"]
    assert (n["orders"], n["looked_up"], n["filled"], n["settled"]) == (3, 2, 1, 1)
    assert abs(n["pnl_per_filled_before_fees"] - 0.6) < 1e-9


def test_red_signals_surface_silent_arm_health_and_budget():
    arms = [{"status": "silent", "text": "EXP-047-S is SILENT"}, {"status": "ok", "text": "fine"}]
    reds = sob.red_signals(arms, "[FAIL] disk 95%\n[WARN] x\n=== ok", "SURFACE BUDGET: RED", "OK fine", "boom")
    assert any("SILENT" in r for r in reds) and any("[FAIL]" in r for r in reds) and any("RED" in r for r in reds)
    assert any("D6 not computed" in r for r in reds) and not any("fine" in r for r in reds)


def test_ingest_takes_newest_successful_result(tmp_path):
    res = tmp_path / sob.RES_DIR
    res.mkdir(parents=True)
    (tmp_path / "04_EXECUTION").mkdir(exist_ok=True)

    def mk(stem, ran, code, body):
        (res / f"{stem}_state_of_the_bot_read.md").write_text(
            f"# Box task\n\n- ran: {ran} on box\n- exit code: {code}\n\n```\n{body}\n\n[stderr]\nwarn\n```\n")
    mk("20261126T0100Z", "2026-11-26T01:00:00Z", 0, "# STATE OF THE BOT - read A\nold\n~~~\nx\n~~~")
    mk("20261126T0200Z", "2026-11-26T02:00:00Z", 0, "# STATE OF THE BOT - read B\nnew\n~~~\ny\n~~~")
    mk("20261126T0300Z", "2026-11-26T03:00:00Z", 124, "# STATE OF THE BOT - read C\ntimeout")
    assert sob.ingest(tmp_path) == 0
    out = (tmp_path / sob.OUT_REL).read_text()
    assert "read B" in out and "read A" not in out and "read C" not in out and "[stderr]" not in out and "~~~\ny\n~~~" in out


def test_ingest_without_result_fails_loudly(tmp_path):
    (tmp_path / sob.RES_DIR).mkdir(parents=True)
    assert sob.ingest(tmp_path) == 2


def test_d6_sport_key_is_lowercase_in_page():
    import inspect
    import scripts.state_of_the_bot as s
    assert "d6s.get(sp.lower())" in inspect.getsource(s.build)
