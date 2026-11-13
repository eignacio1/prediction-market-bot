"""W114.2 / B-090: scripts/arm_orders_read.py and scripts/d6_read.py -- epoch split, E1-E3 per arm, tolerant timestamps,
allowlist entries are read-only. No network."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import arm_orders_read as aor  # noqa: E402
import d6_read  # noqa: E402

PRE_TS, POST_TS = "2026-11-05T12:00:00Z", "2026-11-12T12:00:00Z"


def _o(ts, arm="RIDE", side="yes", oid="o1", ok=True, sport="NBA", **kw):
    return {"ts": ts, "event": "arm_order", "ok": ok, "order_id": oid, "arm": arm, "side": side, "sport": sport,
            "ticker": "T-" + oid, "entry_price": 0.4, **kw}


def test_parse_ts_tolerant():
    assert aor.parse_ts("2026-11-12T12:00:00Z").year == 2026
    assert aor.parse_ts("2026-11-12T12:00:00.12345Z") is not None  # 5-digit fraction
    assert aor.parse_ts("2026-11-12T12:00:00").tzinfo is not None
    assert aor.parse_ts("garbage") is None and aor.parse_ts(None) is None


def test_counts_split_by_epoch_and_reasons():
    rows = [_o(PRE_TS, oid="a"), _o(POST_TS, oid="b"), _o(POST_TS, oid="c", ok=False),
            {"ts": POST_TS, "event": "arm_skip", "arm": "FADE", "sport": "NHL", "reason": "no_bet"},
            {"ts": POST_TS, "event": "arm_skip", "arm": "FADE", "sport": "NHL", "reason": "no_bet"},
            {"ts": POST_TS, "event": "arm_would_order", "arm": "RIDE", "sport": "NFL"},
            {"ts": "bad", "event": "arm_skip", "arm": "FADE", "sport": "NHL", "reason": "x"}]
    c = aor.counts(rows)
    assert c["per_epoch_arm_sport"][f"{aor.PRE}|RIDE|NBA"] == {"orders": 1}
    assert c["per_epoch_arm_sport"][f"{aor.POST}|RIDE|NBA"] == {"orders": 1, "refused": 1}
    assert c["per_epoch_arm_sport"][f"{aor.POST}|FADE|NHL"] == {"skips": 2}
    assert c["per_epoch_arm_sport"][f"{aor.POST}|RIDE|NFL"] == {"would": 1}
    assert c["skip_reasons_per_epoch_arm"][f"{aor.POST}|FADE"] == {"no_bet": 2}
    assert c["rows_with_unparseable_ts"] == 1


def test_fills_e1_e2_e3_and_pre_epoch_no_side_dropped():
    rows = [_o(POST_TS, oid="w", side="no"), _o(POST_TS, oid="l"), _o(POST_TS, oid="n"), _o(POST_TS, oid="x"),
            _o(PRE_TS, oid="pn", side="no"), _o(PRE_TS, oid="py", side="yes")]
    table = {"w": {"fills": 1, "settled": True, "won": True, "price": 0.4},
             "l": {"fills": 1, "settled": True, "won": False, "price": 0.6},
             "n": {"fills": 0, "nf_won": True},
             "x": {"status": "unretrievable"},
             "py": {"fills": 1, "settled": True, "won": True, "price": 0.5}}
    res = aor.fills_report(rows, lambda oid, tk: table.get(oid, {"fills": 0}))
    post = res[f"RIDE|{aor.POST}"]
    assert post["E1_orders"] == 4 and post["E1_fills"] == 2 and post["fill_rate"] == 0.5
    assert abs(post["E2_pnl_per_filled_contract_before_fees"] - ((0.6 - 0.6) / 2)) < 1e-9  # +0.6 and -0.6
    assert post["E3_win_rate_fills"] == 0.5 and post["E3_win_rate_nonfills_counterfactual"] == 1.0
    assert post["lookups_failed"] == 1
    pre = res[f"RIDE|{aor.PRE}"]
    assert pre["E1_orders"] == 1 and pre["E1_fills"] == 1 and abs(pre["E2_pnl_per_filled_contract_before_fees"] - 0.5) < 1e-9


def test_no_fills_lookup_reports_none_not_zero():
    res = aor.fills_report([_o(POST_TS)], None)
    r = res[f"RIDE|{aor.POST}"]
    assert r["E1_orders"] == 1 and r["E1_fills"] is None and r["fill_rate"] is None


def test_build_is_json_serialisable_and_last_row():
    out = aor.build([_o(POST_TS)], None, "fills skipped: x", "src")
    json.dumps(out)
    assert out["last_row_ts"] == POST_TS and out["fills_note"] == "fills skipped: x"


def test_load_rows_skips_garbage(tmp_path):
    p = tmp_path / "o.jsonl"
    p.write_text(json.dumps({"a": 1}) + "\nnot json\n[1]\n")
    assert aor.load_rows(p) == [{"a": 1}]
    assert aor.load_rows(tmp_path / "missing.jsonl") == []


def test_d6_build_counts_layers_6_7_from_orders():
    from prediction_market_bot.decision_trees import coverage
    base = coverage.d6_layers(orders=[], fills_for=None)
    pick = next(c for c in base if c["n_layers"] >= 1)
    orders = [{"ts": POST_TS, "event": "arm_order", "ok": True, "order_id": "z", "market_type": pick["market_type"],
               "band": pick["band"], "size_for": {"stake": 1}, "ticker": "T"}]
    out = d6_read.build(orders, lambda oid, tk: {"fills": 0}, "ok", "src")
    cell = next(c for c in coverage.d6_layers(orders=orders, fills_for=lambda o, t: {"fills": 0})
                if (c["market_type"], c["band"]) == (pick["market_type"], pick["band"]))
    assert cell["layers"][5] and cell["layers"][6]
    assert out["d6"]["registered"] == len(base) and out["arm_order_rows"] == 1
    assert sum(out["cells_by_n_layers"].values()) == len(base)
    assert "nhl_store_dir_exists" in out["layer3_inputs"]
    json.dumps(out, default=str)


def _bt():
    spec = importlib.util.spec_from_file_location("box_tasks", REPO / "scripts" / "box_tasks.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_allowlist_entries_are_read_only_and_exact():
    bt = _bt()
    for name, script in (("arm_orders_read", "arm_orders_read.py"), ("d6_read", "d6_read.py")):
        cmd = bt.TASKS[name]
        assert cmd.endswith(f"scripts/{script}") and bt.NAME_RE.match(name)
        assert not re.search(r">", cmd)
        assert not any(w in cmd for w in ("crontab", "install", "rm ", "git pull", "systemctl"))


def test_scripts_write_no_files():
    for f in ("arm_orders_read.py", "d6_read.py"):
        src = (REPO / "scripts" / f).read_text()
        assert not re.search(r"open\([^)]*['\"][wa]b?['\"]|write_text|atomic_write|\.mkdir\(", src), f
