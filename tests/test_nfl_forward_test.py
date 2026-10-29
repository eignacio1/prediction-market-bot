"""EXP-045 forward-test machinery on a frozen synthetic archive with a known answer."""
import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.nfl_engine import forward_test as ft
from prediction_market_bot.nfl_engine.board_v2 import build_library
from prediction_market_bot.quant.money import fee

KO = "2026-11-01T18:00:00Z"
GAME = {"26NOV01AWYHOM": dict(home="HOM", away="AWY", ko=KO)}


def _lib():
    rng = np.random.default_rng(7)
    n = 400
    line = rng.choice([-7, -3, 0, 3, 7], n).astype(float)
    tl = rng.choice([40.0, 44.0, 48.0], n)
    m = np.round(line + rng.normal(0, 13, n)).astype(int)
    t = np.round(tl + rng.normal(0, 9, n)).astype(int)
    hp = np.maximum((t + m) // 2, 0)
    ap = np.maximum(t - hp, 0)
    return build_library(pd.DataFrame(dict(season=2020, home_score=hp, away_score=ap, spread_line=line, total_line=tl)))


def _row(ser, tick, bid, ask, ts):
    return dict(run_ts=ts, series_ticker=ser, ticker=f"{ser}-26NOV01AWYHOM-{tick}", event_ticker=f"{ser}-26NOV01AWYHOM",
                yes_bid=f"{bid:.4f}", yes_ask=f"{ask:.4f}")


def _archive(cache, ts, mispriced=True):
    """A fair ladder (quotes = engine +/- 0.05) with two planted mispricings; returns the rows for one snapshot."""
    b = cache.get(0.0, 44.0)
    rows = []
    for n in range(1, 21):
        for team, p in (("HOM", float(b.p[b.m > n].sum())), ("AWY", float(b.p[b.m < -n].sum()))):
            rows.append(_row("KXNFLSPREAD", f"{team}{n}", max(p - .05, .01), min(p + .05, .99), ts))
    for n in range(30, 61):
        p = b.p_total_ge(n + 1)
        rows.append(_row("KXNFLTOTAL", f"{n}", max(p - .05, .01), min(p + .05, .99), ts))
    if mispriced:
        for r in rows:
            if r["ticker"].endswith("-HOM14"):
                r["yes_bid"], r["yes_ask"] = "0.0100", "0.0300"     # engine ~0.1+: buy YES at 0.03
            if r["ticker"].endswith("-60") and r["series_ticker"] == "KXNFLTOTAL":
                r["yes_bid"], r["yes_ask"] = "0.3000", "0.3200"     # engine ~0.03: buy NO at 0.70
    return rows


def test_known_answer_trigger_and_settlement():
    cache = ft.BoardCache(_lib())
    snaps = [("2026-10-31T10:00:00Z", _archive(cache, "2026-10-31T10:00:00Z")),
             ("2026-10-31T10:20:00Z", _archive(cache, "2026-10-31T10:20:00Z")),   # same mispricing: no second position
             ("2026-10-30T10:00:00Z", _archive(cache, "2026-10-30T10:00:00Z")),   # before freeze (placed out of order on purpose)
             ("2026-11-01T18:05:00Z", _archive(cache, "2026-11-01T18:05:00Z"))]   # after kickoff
    snaps.sort(key=lambda s: s[0])
    grouped = ((ts, ev) for ts, ev in ft.iter_snapshots(r for _, rows in snaps for r in rows))
    pos = ft.find_triggers(grouped, GAME, cache, freeze_ts="2026-10-31T00:00:00Z")
    by = {p["ticker"].rsplit("-", 1)[1] + p["series"]: p for p in pos}
    yes, no = by["HOM14KXNFLSPREAD"], by["60KXNFLTOTAL"]
    assert (yes["side"], yes["entry"]) == ("YES", 0.03) and yes["run_ts"] == "2026-10-31T10:00:00Z"
    assert yes["fee"] == fee("KXNFLSPREAD", 0.03, 1) == pytest.approx(0.0021)
    assert no["side"] == "NO" and no["entry"] == pytest.approx(0.70)
    assert len(pos) == len({p["ticker"] for p in pos})                     # one position per market
    assert all(p["run_ts"] < KO and p["run_ts"] >= "2026-10-31T00:00:00Z" for p in pos)
    st = ft.settle(pos, GAME, {"26NOV01AWYHOM": (27, 10)})                  # home by 17, total 37
    sb = {p["ticker"].rsplit("-", 1)[1] + p["series"]: p for p in st}
    assert sb["HOM14KXNFLSPREAD"]["pnl"] == pytest.approx(1 - 0.03 - 0.0021)
    assert sb["60KXNFLTOTAL"]["pnl"] == pytest.approx(1 - 0.70 - fee("KXNFLTOTAL", 0.70, 1))
    assert ft.settle(pos, GAME, {}) == []                                   # unsettled games are not scored


def test_fair_ladder_triggers_nothing():
    cache = ft.BoardCache(_lib())
    rows = _archive(cache, "2026-10-31T10:00:00Z", mispriced=False)
    assert ft.find_triggers(ft.iter_snapshots(rows), GAME, cache, "2026-10-31T00:00:00Z") == []


def test_game_after_freeze_only():
    cache = ft.BoardCache(_lib())
    rows = _archive(cache, "2026-10-31T10:00:00Z")
    past = {"26NOV01AWYHOM": dict(GAME["26NOV01AWYHOM"], ko="2026-10-30T18:00:00Z")}
    assert ft.find_triggers(ft.iter_snapshots(rows), past, cache, "2026-10-31T00:00:00Z") == []


def test_power_and_bh():
    assert ft.power_n(0.165, 0.02) == 421
    s = [dict(event=f"e{i}", fam="spread", pnl=0.1 + (i % 3) * 0.01) for i in range(40)]
    r = ft.score(s)
    assert r["spread"]["pass"] and r["spread"]["lo"] > 0 and not r["total"]["pass"] and r["total"]["games"] == 0
    z = [dict(event=f"e{i}", fam="total", pnl=(-1) ** i * 0.1) for i in range(40)]
    assert not ft.score(z)["total"]["pass"]
