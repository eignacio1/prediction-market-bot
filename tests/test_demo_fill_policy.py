"""W64.2 / ADR-0072: demo fill placement policy + shadow flat stake. Everything here is mocked;
no network, no order. The switch is ON only inside tests that set it."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution import demo_fill_policy as pol
from prediction_market_bot.c5_execution import shadow_flat_stake as sfs
from prediction_market_bot.c5_execution.kalshi_client import KalshiOrder
from prediction_market_bot.c5_execution.paper_trader import PaperTrader


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch, tmp_path):
    for k in (pol.SWITCH_ENV, pol.CANCEL_AFTER_ENV, pol.MAX_GAP_ENV, pol.SHARE_ENV, pol.SEED_ENV,
              sfs.SWITCH_ENV):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv(pol.LOG_ENV, str(tmp_path / "pol.jsonl"))
    pol._LISTING_CACHE.clear()


def _events(tmp_path):
    p = tmp_path / "pol.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def _client(bid=0.40, ask=0.44, ok=True):
    c = MagicMock()
    c.has_signing_key.return_value = True
    c.get_market_book.return_value = (True, {"yes_bid": bid, "yes_ask": ask})
    c.submit_order.return_value = KalshiOrder(ok=ok, order_id="OID1" if ok else "", client_order_id="x",
                                              ticker="T", side="yes", contracts=2, yes_price_cents=40,
                                              actual_cost_usd=0.8, status="resting",
                                              error="" if ok else "boom")
    c.cancel_order.return_value = (True, {})
    c.is_listed_on_demo.return_value = True
    return c


def _approval(size=1.0, direction="YES"):
    return {"approval_status": "APPROVED", "approved_size": size, "approved_direction": direction,
            "risk_eval_id": "R", "forecast_id": "F"}


def _open(tmp_path, client, mid=0.42, direction="YES"):
    lg = MagicMock()
    t = PaperTrader(tmp_path / "p.json", lg, kalshi_client=client)
    return t.open_position(approval=_approval(direction=direction), player_name="P", player_id=1,
                           kalshi_ticker="KXMLBHIT-TEST", kalshi_threshold=1, mid_price=mid, vig=0.04,
                           game_date="2026-10-01")


# ---- switch semantics ------------------------------------------------------------------
@pytest.mark.parametrize("val", ["", "1", "true", "on", "BOOK_ANCHOR_CANCEL", "book_anchor"])
def test_only_exact_value_enables(monkeypatch, val):
    monkeypatch.setenv(pol.SWITCH_ENV, val)
    assert not pol.is_enabled()
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    assert pol.is_enabled()


def test_off_is_byte_identical_and_touches_nothing(tmp_path, monkeypatch):
    c = _client()
    ok, pos = _open(tmp_path, c, mid=0.42)
    assert ok and pos
    c.get_market_book.assert_not_called()
    c.cancel_order.assert_not_called()
    kw = c.submit_order.call_args.kwargs
    assert kw["mid_price"] == 0.42                      # the caller's model mid, unchanged
    assert "fill_policy" not in pos
    assert not (tmp_path / "pol.jsonl").exists()


# ---- ON: R2 ----------------------------------------------------------------------------
def test_on_yes_anchors_to_best_bid_and_schedules_cancel(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")  # timer never fires in test
    c = _client(bid=0.40, ask=0.44)
    ok, pos = _open(tmp_path, c, mid=0.42, direction="YES")
    assert c.submit_order.call_args.kwargs["mid_price"] == 0.40
    assert pos["fill_policy"]["submit_mid"] == 0.40 and pos["fill_policy"]["model_mid"] == 0.42
    assert any(e["event"] == "cancel_scheduled" and e["order_id"] == "OID1" for e in _events(tmp_path))


def test_on_no_rests_at_own_side_best_bid(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")
    c = _client(bid=0.40, ask=0.44)
    _open(tmp_path, c, mid=0.42, direction="NO")
    # YES-frame 0.44 -> NO price 0.56 == 1 - yes_ask: NO best bid
    assert c.submit_order.call_args.kwargs["mid_price"] == 0.44


@pytest.mark.parametrize("bid,ask,reason", [(0.0, 0.44, "one_sided_or_crossed_book"),
                                            (0.40, 0.0, "one_sided_or_crossed_book"),
                                            (0.30, 0.34, "mid_gap_above_threshold")])
def test_on_skips_logged_and_places_nothing(tmp_path, monkeypatch, bid, ask, reason):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client(bid=bid, ask=ask)
    ok, pos = _open(tmp_path, c, mid=0.42)
    assert ok and pos == {}
    c.submit_order.assert_not_called()
    assert any(e["event"] == "skip" and e["reason"] == reason for e in _events(tmp_path))


def test_book_read_failure_is_a_skip_not_a_fallback_order(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client()
    c.get_market_book.return_value = (False, {})
    ok, pos = _open(tmp_path, c)
    assert pos == {}
    c.submit_order.assert_not_called()


# ---- R1 --------------------------------------------------------------------------------
def test_cancel_after_n_fires(monkeypatch, tmp_path):
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "0.05")
    c = _client()
    t = pol.schedule_cancel(c, "OID9", "POS1", "TK")
    t.join(2)
    c.cancel_order.assert_called_once_with("OID9")
    assert [e["event"] for e in _events(tmp_path)] == ["cancel_scheduled", "cancel_ok"]


def test_cancel_failure_is_logged_not_raised(tmp_path):
    c = _client()
    c.cancel_order.side_effect = RuntimeError("net")
    assert pol.cancel_now(c, "O", "P", "T", "unfilled_after_N") is False
    assert _events(tmp_path)[-1]["event"] == "cancel_failed"


def test_sweep_overdue_finishes_orphaned_cancels(monkeypatch, tmp_path):
    c = _client()
    pol.append_log({"event": "cancel_scheduled", "order_id": "A", "position_id": "P", "ticker": "T",
                    "due_ts": 100.0})
    pol.append_log({"event": "cancel_scheduled", "order_id": "B", "position_id": "P", "ticker": "T",
                    "due_ts": 100.0})
    pol.append_log({"event": "cancel_ok", "order_id": "B"})
    assert pol.sweep_overdue(c, now_ts=200.0) == 1
    c.cancel_order.assert_called_once_with("A")


# ---- assignment ------------------------------------------------------------------------
def test_assignment_deterministic_and_share(monkeypatch):
    monkeypatch.setenv(pol.SHARE_ENV, "0.5")
    ids = [f"POS-{i}" for i in range(2000)]
    a1 = [pol.assigned(i) for i in ids]
    assert a1 == [pol.assigned(i) for i in ids]
    assert 0.45 < sum(a1) / len(a1) < 0.55
    monkeypatch.setenv(pol.SHARE_ENV, "0")
    assert not any(pol.assigned(i) for i in ids)


def test_control_arm_gets_todays_behaviour(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.SHARE_ENV, "0")
    c = _client()
    ok, pos = _open(tmp_path, c, mid=0.42)
    assert pos and c.submit_order.call_args.kwargs["mid_price"] == 0.42
    c.get_market_book.assert_not_called()


# ---- shadow flat stake -----------------------------------------------------------------
def _row(ey=0.05, en=-0.07, mid=0.42):
    return {"run_id": "RUN1", "market_ticker": "KXNBAGAME-X", "mid": mid,
            "e_net_yes_k007": ey, "e_net_no_k007": en, "p_yes": 0.5}


def test_shadow_off_places_nothing(monkeypatch):
    c = _client()
    assert sfs.maybe_place(_row(), c, lambda e: 1.0) is None
    c.submit_order.assert_not_called()


def test_shadow_requires_both_switches(monkeypatch):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")           # placement rule still OFF
    c = _client()
    assert sfs.maybe_place(_row(), c, lambda e: 1.0) is None
    c.submit_order.assert_not_called()


def test_shadow_on_places_flat_stake_under_policy_row_untouched(monkeypatch, tmp_path):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")
    c = _client(bid=0.40, ask=0.44)
    row = _row()
    before = json.dumps(row, sort_keys=True)
    res = sfs.maybe_place(row, c, lambda e: 1.0)
    assert res and res["ok"]
    assert json.dumps(row, sort_keys=True) == before            # shadow row never altered
    kw = c.submit_order.call_args.kwargs
    assert kw["size_usd"] == 1.0 and kw["side"] == "yes" and kw["mid_price"] == 0.40
    assert any(e["event"] == "cancel_scheduled" for e in _events(tmp_path))
    import uuid                                                 # W67.2: Kalshi rejects non-UUID ids (HTTP 400)
    assert str(uuid.UUID(kw["client_order_id"])) == kw["client_order_id"]


def test_shadow_below_gate_or_skip_places_nothing(monkeypatch):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client()
    assert sfs.maybe_place(_row(ey=-0.01, en=-0.02), c, lambda e: 1.0) is None
    c2 = _client(bid=0.0, ask=0.44)
    assert sfs.maybe_place(_row(), c2, lambda e: 1.0) is None
    c.submit_order.assert_not_called(); c2.submit_order.assert_not_called()


def test_make_on_row_none_when_off():
    assert sfs.make_on_row(MagicMock()) is None


def test_default_stake_is_adr0050_flat(monkeypatch):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")
    c = _client(bid=0.40, ask=0.44)
    sfs.maybe_place(_row(), c)
    from prediction_market_bot.run_t4_mlb_live import measurement_stake_and_stratum
    assert c.submit_order.call_args.kwargs["size_usd"] == measurement_stake_and_stratum(0.40)[0]


# ---- W66.2: persisted cancel sweeper + repo-mirrored switch config --------------------------------
def test_sweeper_finishes_cancel_after_process_exit(tmp_path):
    """The cron T1 process writes cancel_scheduled then exits (daemon Timer never fires); the sweeper,
    in another process, cancels it once due and logs the outcome."""
    import time
    pol.append_log({"event": "cancel_scheduled", "order_id": "O9", "position_id": "p9", "ticker": "T",
                    "cancel_after_s": 60, "due_ts": time.time() - 1})
    c = MagicMock()
    c.cancel_order.return_value = (True, {"status": "canceled"})
    assert pol.sweep_overdue(c) == 1
    c.cancel_order.assert_called_once_with("O9")
    assert [e["event"] for e in _events(tmp_path)][-1] == "cancel_ok"
    assert pol.sweep_overdue(c) == 0  # already finished; never cancelled twice


def test_sweeper_waits_until_due_and_records_failure(tmp_path):
    import time
    pol.append_log({"event": "cancel_scheduled", "order_id": "O8", "position_id": "p8", "ticker": "T",
                    "cancel_after_s": 60, "due_ts": time.time() + 600})
    c = MagicMock()
    c.cancel_order.return_value = (False, {"error": "filled"})
    assert pol.sweep_overdue(c) == 0
    assert pol.sweep_overdue(c, now_ts=time.time() + 700) == 1
    assert _events(tmp_path)[-1]["event"] == "cancel_failed"


def test_sweeper_overdue_pending_detects_work(tmp_path):
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    import demo_cancel_sweeper as sw
    assert sw.overdue_pending() is False
    pol.append_log({"event": "cancel_scheduled", "order_id": "O7", "position_id": "p", "ticker": "T", "due_ts": 1})
    assert sw.overdue_pending() is True
    pol.append_log({"event": "cancel_ok", "order_id": "O7"})
    assert sw.overdue_pending() is False


def test_repo_mirrored_config_carries_registered_parameters():
    cfg = {}
    for line in (Path(__file__).parent.parent / "deploy" / "demo_fill.env").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            k, v = line.split("=", 1)
            cfg[k] = v
    assert cfg == {"DEMO_FILL_PLACEMENT_RULE": "book_anchor_cancel", "SHADOW_FLAT_STAKE": "on",
                   "DEMO_FILL_CANCEL_AFTER_S": "60", "DEMO_FILL_MAX_MID_GAP": "0.05",
                   "DEMO_FILL_ASSIGN_SHARE": "0.5", "DEMO_FILL_SEED": "w64-2"}


# ---- W67.2 / GG-564: skip tickers the demo venue does not list --------------------------
def test_unlisted_ticker_is_logged_skip_no_order_even_for_control_arm(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    for share in ("1", "0"):                       # treatment arm AND control arm: identical
        monkeypatch.setenv(pol.SHARE_ENV, share)
        pol._LISTING_CACHE.clear()
        c = _client(); c.is_listed_on_demo.return_value = False
        ok, pos = _open(tmp_path, c)
        assert ok and pos == {}
        c.submit_order.assert_not_called()
        c.get_market_book.assert_not_called()
    skips = [e for e in _events(tmp_path) if e.get("reason") == "not_listed_on_demo"]
    assert len(skips) == 2 and all(e["ticker"] == "KXMLBHIT-TEST" for e in skips)


def test_unknown_listing_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client(); c.is_listed_on_demo.return_value = None
    ok, pos = _open(tmp_path, c)
    assert pos == {}
    c.submit_order.assert_not_called()
    assert any(e.get("reason") == "demo_listing_unknown" for e in _events(tmp_path))
    assert "KXMLBHIT-TEST" not in pol._LISTING_CACHE        # unknown is never cached
    c.is_listed_on_demo.side_effect = RuntimeError("x")
    assert pol.listing_skip_reason(c, "T2") == "demo_listing_unknown"


def test_listing_cached_within_ttl_and_refreshed_after(monkeypatch):
    c = _client()
    assert pol.listing_skip_reason(c, "T1") is None
    assert pol.listing_skip_reason(c, "T1") is None
    assert c.is_listed_on_demo.call_count == 1
    monkeypatch.setenv(pol.LISTING_TTL_ENV, "0")
    assert pol.listing_skip_reason(c, "T1") is None
    assert c.is_listed_on_demo.call_count == 2


def test_listing_check_inert_when_switch_off(tmp_path):
    c = _client(); c.is_listed_on_demo.return_value = False
    ok, pos = _open(tmp_path, c)                    # forward test OFF: today's behaviour, byte-identical
    assert pos and c.submit_order.called
    c.is_listed_on_demo.assert_not_called()


def test_shadow_unlisted_ticker_skips_before_assignment(monkeypatch, tmp_path):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client(); c.is_listed_on_demo.return_value = False
    assert sfs.maybe_place(_row(), c, lambda e: 1.0) is None
    c.submit_order.assert_not_called(); c.get_market_book.assert_not_called()
    ev = _events(tmp_path)
    assert [e["reason"] for e in ev] == ["not_listed_on_demo"]      # no control_arm record: pre-assignment


def test_client_is_listed_on_demo_maps_status(monkeypatch):
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    k = KalshiMarketClient.__new__(KalshiMarketClient)
    for resp, want in [((True, {}), True), ((False, {"error": "HTTP 404"}), False),
                       ((False, {"error": "HTTP 500"}), None), ((False, {"error": "Connection failed"}), None)]:
        monkeypatch.setattr(k, "_get", lambda *a, _r=resp, **kw: _r, raising=False)
        assert k.is_listed_on_demo("X") is want


def test_shadow_runner_cron_lines_load_demo_config_except_preseason_and_settle():
    """W67.2: every T1/T2/T3 shadow runner line loads deploy/demo_fill.env (so SHADOW_FLAT_STAKE is
    in effect, W68.2: NBA game + NBA player points included, demo-only guard in code); the preseason and
    settle jobs never do."""
    import re
    run = re.compile(r"scripts/run_(pregame|mlb_pregame|nba_pregame|nba_player_points)_shadow\.py (--refresh )?--bands T[123]\b")
    n = 0
    for f in ("cron.conf", "cron_exp037_pregame_shadow.conf", "cron.nba_shadow", "cron.nba_player_points_shadow"):
        for line in (Path(__file__).parent.parent / "deploy" / f).read_text().splitlines():
            if line.lstrip().startswith("#"):
                continue
            if run.search(line):
                n += 1
                assert "deploy/demo_fill.env" in line and ".env | xargs" in line, line
            elif "--preseason" in line or "_settle.py" in line:
                assert "demo_fill.env" not in line, line
    assert n == 12 + 6 + 6      # NFL+MLB + NBA game + NBA player points, counted in conf + fragment (W68.2)


def test_nhl_shadow_eval_lines_use_staked_wrapper_with_demo_config():
    """W68.2: NHL eval cron lines run the staked wrapper, load demo_fill.env and pin BOT_ENV=paper."""
    for f in ("cron.conf", "cron.nhl_shadow"):
        lines = [l for l in (Path(__file__).parent.parent / "deploy" / f).read_text().splitlines()
                 if "nhl_shadow_eval" in l or "run_nhl_shadow_staked" in l]
        assert len([l for l in lines if "run_nhl_shadow_staked.py --band" in l]) == 5, f
        for l in lines:
            assert "nhl_shadow_eval.py" not in l
            assert "deploy/demo_fill.env" in l and "BOT_ENV=paper" in l, l


def test_demo_host_guard_refuses_production_and_unknown(monkeypatch):
    """W68.2: demo-only guard -- production host and unrecognised BOT_ENV are refused, and no order is placed."""
    from prediction_market_bot.c5_execution import shadow_flat_stake as sfs
    for env, want in (("paper", True), ("", True), ("live", False), ("garbage", False)):
        if env:
            monkeypatch.setenv("BOT_ENV", env)
        else:
            monkeypatch.delenv("BOT_ENV", raising=False)
        assert sfs.demo_host_ok() is want, env
    monkeypatch.setenv("BOT_ENV", "live")
    monkeypatch.setenv("SHADOW_FLAT_STAKE", "on")
    monkeypatch.setenv("DEMO_FILL_PLACEMENT_RULE", "book_anchor_cancel")

    class Boom:
        def __getattr__(self, n):
            raise AssertionError("client touched on production host")
    row = {"run_id": "r", "market_ticker": "T", "mid": 0.5, "e_net_yes_k007": 0.1, "e_net_no_k007": -0.1}
    assert sfs.maybe_place(row, Boom()) is None


# ---- W69.1 / GG-586: SHADOW control arm places a plain model-mid order ------------------
def test_shadow_control_arm_places_model_mid_no_cancel_no_book_read(monkeypatch, tmp_path):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.SHARE_ENV, "0")                      # everything is control
    c = _client()
    row = _row()
    res = sfs.maybe_place(row, c, lambda e: 1.0)
    assert res and res["ok"]
    c.get_market_book.assert_not_called()                       # no book anchoring
    assert c.submit_order.call_args.kwargs["mid_price"] == float(row["mid"])
    ev = _events(tmp_path)
    assert [e["event"] for e in ev] == ["shadow_order"] and ev[0]["arm"] == "control"
    assert not any(e["event"] == "cancel_scheduled" for e in ev)   # no cancel


def test_shadow_arm_split_follows_same_hash_and_share(monkeypatch, tmp_path):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.SHARE_ENV, "0.5")
    rid = f"{_row().get('run_id')}|{_row().get('market_ticker')}"
    want = "treatment" if pol.assigned(rid) else "control"
    c = _client()
    sfs.maybe_place(_row(), c, lambda e: 1.0)
    orders = [e for e in _events(tmp_path) if e["event"] == "shadow_order"]
    assert orders and orders[0]["arm"] == want
