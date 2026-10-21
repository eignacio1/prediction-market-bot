"""W81.3: KXNFLPASSYDS pre-kickoff snapshot job (depth math, slots, caps, idempotence) + its silent-arm rule."""
from pathlib import Path as _P
ROOT_FOR_INSTALL = _P(__file__).resolve().parents[1]
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("passyds_snap", ROOT / "scripts" / "passyds_prekickoff_snapshot.py")
snap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(snap)

from prediction_market_bot.pregame_shadow.silent_arms import SPECS, ArmInput, evaluate_arm  # noqa: E402

NOW = datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc)


def book(yes, no):
    return {"orderbook_fp": {"yes_dollars": [[f"{p:.4f}", f"{q:.2f}"] for p, q in yes],
                             "no_dollars": [[f"{p:.4f}", f"{q:.2f}"] for p, q in no]}}


def test_depth_floor_met_on_cheaper_side():
    # yes bid .20, no bid .76 -> yes ask .24, mid .22, spread 4c; cheaper side = yes; yes asks within 2c of mid (<= .24)
    d = snap.depth_fields(book(yes=[(0.20, 50), (0.15, 400)], no=[(0.76, 12), (0.70, 900)]))
    assert d["two_sided"] and abs(d["mid"] - 0.22) < 1e-9 and abs(d["spread"] - 0.04) < 1e-9
    assert d["cheaper_side"] == "yes" and d["yes_ask_within_2c"] == 12.0 and d["yes_ask_within_5c"] == 12.0
    assert d["no_ask_within_2c"] == 50.0 and d["no_ask_within_5c"] == 50.0
    assert d["floor_met"] is True


def test_depth_floor_fails_on_wide_spread_or_thin_side():
    wide = snap.depth_fields(book(yes=[(0.20, 500)], no=[(0.70, 500)]))      # ask .30, spread 10c
    assert wide["floor_met"] is False
    thin = snap.depth_fields(book(yes=[(0.20, 500)], no=[(0.76, 9)]))        # 9 < 10 contracts within 2c
    assert thin["floor_met"] is False


def test_one_sided_book_is_not_two_sided_and_never_floor():
    d = snap.depth_fields(book(yes=[(0.20, 500)], no=[]))
    assert d["two_sided"] is False and d["floor_met"] is False and d["mid"] is None
    assert snap.depth_fields({})["two_sided"] is False


def test_slot_windows():
    assert snap.slot_for(29 * 60) == "pre30" and snap.slot_for(30 * 60) == "pre30"
    assert snap.slot_for(0) is None and snap.slot_for(-60) is None and snap.slot_for(31 * 60) is None
    assert snap.slot_for(110 * 60) == "pre2h" and snap.slot_for(104 * 60) is None and snap.slot_for(136 * 60) is None


class FakeClient:
    def __init__(self, markets, books):
        self.markets, self.books, self.gets = markets, books, []

    def get(self, path, **params):
        self.gets.append(path)
        if path.startswith("/markets/") and path.endswith("/orderbook"):
            return self.books[path.split("/")[2]], "http://x" + path
        raise AssertionError(path)


def _mk(ticker, strike, ev="KXNFLPASSYDS-26OCT22NECHI"):
    return {"ticker": ticker, "event_ticker": ev, "floor_strike": strike, "no_sub_title": "Drake Maye: 250+",
            "occurrence_datetime": (NOW + timedelta(minutes=20) + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")}


class Sched:
    def __init__(self, ko):
        self.ko = ko

    def kickoff_for_event(self, ev):
        return (self.ko, "nflverse_gameday_gametime_ET")


def _run(tmp_path, monkeypatch, markets, ko_min=20, **kw):
    # hermetic: the live model hook downloads nflverse data; its own behaviour is covered in test_passyds_model.py
    monkeypatch.setattr(snap, "model_fields", lambda m, now: {"model_p": None, "model_id": None, "model_sha256": None, "factor_inputs": None, "factor_as_of": None})
    monkeypatch.setattr(snap.tc, "_list_open", lambda client, series, **f: markets)
    cl = FakeClient(markets, {m["ticker"]: book([(0.20, 50)], [(0.76, 50)]) for m in markets})
    out = snap.run(cl, tmp_path, now=NOW.timestamp(), sha="abc", sched=Sched(NOW + timedelta(minutes=ko_min)), **kw)
    return out, cl


def test_writes_one_row_per_strike_with_real_kickoff_and_is_idempotent(tmp_path, monkeypatch):
    ms = [_mk("T-1", 224.5), _mk("T-2", 249.5)]
    out, _ = _run(tmp_path, monkeypatch, ms)
    assert out["written"] == 2 and out["est_kickoff"] == 0
    rows = [json.loads(x) for x in (tmp_path / "snap_2026-10-23.jsonl").read_text().splitlines()]
    assert {r["ticker"] for r in rows} == {"T-1", "T-2"}
    r = rows[0]
    assert r["slot"] == "pre30" and r["secs_to_kickoff_est"] == 20 * 60 and r["kickoff_source"] == "nflverse_schedule"
    assert r["model_p"] is None and r["qb"] == "Drake Maye" and r["floor_met"] is True
    for k in ("event_time", "yes_ask_within_1c", "no_ask_within_5c", "spread", "content_sha256", "runtime_commit_sha"):
        assert k in r
    out2, _ = _run(tmp_path, monkeypatch, ms)             # same run time again -> dedup
    assert out2["written"] == 0 and out2["dup"] == 2


def test_out_of_slot_game_writes_nothing_and_fetches_no_book(tmp_path, monkeypatch):
    out, cl = _run(tmp_path, monkeypatch, [_mk("T-1", 224.5)], ko_min=300)
    assert out["written"] == 0 and cl.gets == []


def test_missing_schedule_falls_back_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(snap.tc, "_list_open", lambda client, series, **f: [_mk("T-1", 224.5)])
    cl = FakeClient([], {"T-1": book([(0.2, 50)], [(0.76, 50)])})
    out = snap.run(cl, tmp_path, now=NOW.timestamp(), sha="abc", sched=None)
    assert out["written"] == 1 and out["est_kickoff"] == 1
    row = json.loads((tmp_path / "snap_2026-10-23.jsonl").read_text().splitlines()[0])
    assert row["kickoff_source"] == "occurrence_minus_3h_est"


def test_byte_cap_stops_writes_and_deletes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(snap, "MAX_DAILY_BYTES", 10)
    out, _ = _run(tmp_path, monkeypatch, [_mk("T-1", 224.5)])
    assert out["written"] == 0 and "byte cap" in out["cap"]


def test_dry_run_writes_no_file(tmp_path, monkeypatch):
    out, _ = _run(tmp_path, monkeypatch, [_mk("T-1", 224.5)], dry_run=True)
    assert out["written"] == 1 and not list(tmp_path.glob("snap_*.jsonl"))


# --- silent-arm rule: a game that kicked off with zero snapshots in its 30-min window is SILENT -----------------------
def _arm(starts, rows):
    return ArmInput(SPECS["nfl_passyds_snap"], starts, max(rows) if rows else None, "", list(rows))


def test_silent_arm_fires_when_game_kicked_off_with_no_snapshot():
    now = NOW + timedelta(hours=2)
    r = evaluate_arm(_arm([NOW], []), now)
    assert r["status"] == "silent"


def test_silent_arm_ok_with_snapshot_in_window_and_silent_with_only_early_row():
    now = NOW + timedelta(hours=2)
    assert evaluate_arm(_arm([NOW], [NOW - timedelta(minutes=12)]), now)["status"] == "ok"
    assert evaluate_arm(_arm([NOW], [NOW - timedelta(minutes=90)]), now)["status"] == "silent"   # pre2h row only


def test_silent_arm_idle_when_no_game_started():
    assert evaluate_arm(_arm([NOW + timedelta(hours=5)], []), NOW)["status"] == "idle"


def test_install_merges_block_once_and_preserves_lines():
    import sys
    sys.path.insert(0, str(ROOT_FOR_INSTALL / "scripts"))
    import passyds_install as pi
    frag = (ROOT_FOR_INSTALL / "deploy" / "cron.passyds_prekickoff").read_text()
    cur = "MAILTO=x\n51 * * * * foo\n"
    store = {"t": cur}
    live = lambda: {"budget": "GREEN", "head": "h", "as_of": "now"}  # noqa: E731
    rd, wr = (lambda: store["t"]), (lambda t: store.__setitem__("t", t))
    assert pi.install(live, rd, wr) == 0
    assert pi.BEGIN in store["t"] and "51 * * * * foo" in store["t"]
    once = store["t"]
    assert pi.install(live, rd, wr) == 0 and store["t"] == once
    assert frag.count("passyds_prekickoff_snapshot.py") >= 1


def test_install_refused_when_red():
    import sys
    sys.path.insert(0, str(ROOT_FOR_INSTALL / "scripts"))
    import passyds_install as pi
    store = {"t": "x\n"}
    live = lambda: {"budget": "RED", "reasons": ["r"]}  # noqa: E731
    pi.install(live, lambda: store["t"], lambda t: store.__setitem__("t", t))
    assert store["t"] == "x\n"


def test_install_ignores_red_about_itself_only():
    import sys
    sys.path.insert(0, str(ROOT_FOR_INSTALL / "scripts"))
    import passyds_install as pi
    st = {"t": "x\n"}
    rd, wr = (lambda: st["t"]), (lambda t: st.__setitem__("t", t))
    own = lambda: {"budget": "RED", "reasons": ["STALE cron|2,22,42 * * * *|scripts/passyds_prekickoff_snapshot.py: no write found"]}  # noqa: E731
    assert pi.install(own, rd, wr) == 0 and pi.BEGIN in st["t"]
    st["t"] = "x\n"
    mixed = lambda: {"budget": "RED", "reasons": ["STALE cron|passyds", "SILENT ARM NHL"]}  # noqa: E731
    pi.install(mixed, rd, wr)
    assert st["t"] == "x\n"
