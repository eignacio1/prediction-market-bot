#!/usr/bin/env python3
"""W130.1 -- NFL in-play SHADOW logger for the T4NFL-ARITH / T4NFL-FLOW cells. Evaluate-and-log only: imports no order code.

One pass per invocation (cron runs it every 2 minutes in the game window; it exits after one request when no game is live):
  ESPN scoreboard -> live games -> ESPN plays (measured feed lag = fetch - play wallclock) -> staleness gate
  -> pre-game line (ESPN pickcenter, cached before kickoff) -> in-play price per open Kalshi market of that game
  -> one JSONL row per market and band in data/shadow/nfl_inplay/<MARKET_TYPE>_<BAND>.jsonl.

Pricer: ``quant/inplay_nfl`` exactly as pre-registered in EXP-NFLINPLAY-001 (s2 FROZEN below, fitted on 2026 weeks 1-6 only,
v2 estimator). T4NFL-FLOW logs the same price with mode="flow_identity" (flow_adjustment is the identity). The team-total price is a
NEW extension with no replay (see the W130.1 addendum): mode="team_total_ext_unvalidated".

OFF unless PM_NFL_INPLAY is 1/on/true. No orders, kelly 0, no kelly import. No User-Agent is sent (GG-163, handled in the feed).

  --health   one line OK|IDLE|FAIL for logs/health.log: FAIL = a live game with a priceable market and no row for 10 minutes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion import nfl_live_feed as feed  # noqa: E402
from prediction_market_bot.quant import inplay_nfl as q  # noqa: E402

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
SERIES = {"KXNFLGAME": "nfl_moneyline", "KXNFLSPREAD": "nfl_spread", "KXNFLTOTAL": "nfl_game_total",
          "KXNFLTEAMTOTAL": "nfl_team_total"}
BANDS = ("T4NFL-ARITH", "T4NFL-FLOW")
# FROZEN: pooled variance per minute, EXP-NFLINPLAY-001 v2 estimator (sum r^2 / sum tau), 93 FINAL games, ESPN weeks 1-6 of 2026.
S2_MARGIN_PM = 3.2717
S2_TOTAL_PM = 3.2161
# ESPN abbreviation -> Kalshi event code (the replay's alias map)
KALSHI_CODE = {"ARI": "ARI", "WSH": "WAS", "LAR": "LA", "JAC": "JAX", "ARZ": "ARI"}
SHADOW_DIR = Path("data/shadow/nfl_inplay")
PASS_LOG = "pass_log.jsonl"
STATE_FILE = "_last_state.json"
ENV_FLAG = "PM_NFL_INPLAY"
WRITE_RECENCY_S = 600.0
PREGAME_AHEAD_H = 4          # cache pre-game lines for games starting within this many hours
_MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
_SUF = re.compile(r"^([A-Z]*)(\d*)$")


def enabled(env=os.environ) -> bool:
    return str(env.get(ENV_FLAG, "")).strip().lower() in ("1", "on", "true", "yes")


def kcode(abbr: str) -> str:
    return KALSHI_CODE.get(abbr, abbr)


def quote(m: dict) -> Optional[tuple[float, float]]:
    try:
        b, a = float(m["yes_bid_dollars"]), float(m["yes_ask_dollars"])
    except (KeyError, TypeError, ValueError):
        return None
    return (b, a) if 0.0 < b < a < 1.0 else None


# ---------------------------------------------------------------- I/O (every network call goes through here; tests swap it)
class Io:
    def scoreboard(self) -> tuple[list[dict], Optional[str]]:
        js, err = feed._get(feed._SCOREBOARD, None)
        if js is None:
            return [], err
        out = []
        for e in js.get("events", []):
            try:
                c = e["competitions"][0]
                h = [x for x in c["competitors"] if x["homeAway"] == "home"][0]
                a = [x for x in c["competitors"] if x["homeAway"] == "away"][0]
                out.append({"id": e["id"], "status": e["status"]["type"]["name"], "date": e["date"],
                            "home_id": h["team"]["id"], "home": h["team"]["abbreviation"], "away": a["team"]["abbreviation"]})
            except (KeyError, IndexError):
                continue
        return out, None

    def plays(self, eid: str) -> tuple[list[dict], Optional[str], str]:
        return feed.fetch_plays(eid)

    def pickcenter(self, eid: str) -> tuple[Optional[float], Optional[float]]:
        js, _ = feed._get(SUMMARY, {"event": eid}, delays=(2,))
        pc = ((js or {}).get("pickcenter") or [{}])[0]
        return pc.get("spread"), pc.get("overUnder")

    def markets(self, event_ticker: str) -> list[dict]:
        js, _ = feed._get(f"{KALSHI}/markets", {"event_ticker": event_ticker, "status": "open", "limit": 200}, delays=(2,))
        time.sleep(0.25)
        return (js or {}).get("markets", [])

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


# ---------------------------------------------------------------- tickers and pricing
def event_ticker(series: str, ev: dict) -> str:
    from zoneinfo import ZoneInfo
    d = datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
    return f"{series}-{d:%y}{_MON[d.month - 1]}{d:%d}{kcode(ev['away'])}{kcode(ev['home'])}"


def parse_market(m: dict) -> Optional[dict]:
    """{'team': code or '', 'strike': float or None} from the market ticker suffix and floor_strike."""
    suf = m["ticker"].rpartition("-")[2]
    mm = _SUF.match(suf)
    if not mm:
        return None
    strike = m.get("floor_strike")
    if strike is None and mm.group(2):
        strike = int(mm.group(2)) - 0.5
    return {"team": mm.group(1), "strike": None if strike is None else float(strike)}


def price_market(series: str, info: dict, st: Any, ev: dict, M: float, T: float) -> Optional[tuple[float, str]]:
    """(p_yes, mode) for one market from the pricer, or None if not priceable."""
    mg = st.home_score - st.away_score
    tot = st.home_score + st.away_score
    sl, yg, dn = st.secs_left_reg, st.yards_to_endzone, st.down
    home = kcode(ev["home"])
    away = kcode(ev["away"])
    if series == "KXNFLGAME":
        if info["team"] not in (home, away):
            return None
        p = q.p_home_win(mg, sl, M, S2_MARGIN_PM, st.possession, yg, dn)
        return (p if info["team"] == home else 1.0 - p), "arith"
    if info["strike"] is None:
        return None
    k = info["strike"]
    if series == "KXNFLSPREAD":
        if info["team"] == home:
            return q.p_margin_gt(mg, sl, M, S2_MARGIN_PM, k, st.possession, yg, dn), "arith"
        if info["team"] == away:
            return 1.0 - q.p_margin_gt(mg, sl, M, S2_MARGIN_PM, -k, st.possession, yg, dn), "arith"
        return None
    if series == "KXNFLTOTAL":
        return q.p_total_gt(tot, sl, T, S2_TOTAL_PM, k, yg, dn), "arith"
    if series == "KXNFLTEAMTOTAL":
        if info["team"] not in (home, away):
            return None
        return _p_team_total(info["team"] == home, st, M, T, k), "team_total_ext_unvalidated"
    return None


def _p_team_total(is_home: bool, st: Any, M: float, T: float, k: float) -> float:
    """NEW, unvalidated: team points ~ Normal(points so far + team drift*tau + own-drive EP, (s2m + s2t)/4 * tau).
    Team expected total = (T +/- M)/2 (home +); margin and total residuals taken as uncorrelated. See the W130.1 addendum."""
    import math
    tau = st.secs_left_reg / 60.0
    mine = st.home_score if is_home else st.away_score
    side = 1 if is_home else -1
    drift = ((T + side * M) / 2.0) * (tau / q.REG_MINUTES)
    has_ball = (st.possession == "home") == is_home and st.possession in ("home", "away")
    mu = mine + drift + (q.drive_ep(st.yards_to_endzone, st.down) if has_ball and tau > 0 else 0.0)
    var = (S2_MARGIN_PM + S2_TOTAL_PM) / 4.0 * tau
    if var <= 1e-12:
        return 1.0 if mine > k else 0.0
    return 1.0 - q._phi((k - mu) / math.sqrt(var))


def make_rows(market: dict, series: str, p_yes: float, mode: str, st: Any, ev: dict, M: float, T: float, line_info: dict,
              run_id: str, quote_ts: datetime, now: datetime, code_sha: str) -> list[dict]:
    qt = quote(market)
    if qt is None:
        return []
    bid, ask = qt
    fetched = datetime.strptime(st.fetch_time_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    rows = []
    for band in BANDS:
        rows.append({
            "run_id": run_id, "ts_utc": now.isoformat(), "sport": "NFL", "market_type": SERIES[series], "band": band,
            "mode": "flow_identity" if (band == "T4NFL-FLOW" and mode == "arith") else mode,
            "event_ticker": market["event_ticker"], "market_ticker": market["ticker"], "p_yes": q.flow_adjustment(p_yes),
            "yes_bid": bid, "yes_ask": ask, "mid": (bid + ask) / 2.0, "half_spread": (ask - bid) / 2.0,
            "espn_event_id": ev["id"], "home": ev["home"], "away": ev["away"], "score_h": st.home_score, "score_a": st.away_score,
            "period": st.period, "secs_left_reg": st.secs_left_reg, "down": st.down, "distance": st.distance,
            "yards_to_endzone": st.yards_to_endzone, "possession": st.possession, "last_play_id": st.play_id,
            "pregame_margin": M, "pregame_total": T, **line_info, "s2_margin_pm": S2_MARGIN_PM, "s2_total_pm": S2_TOTAL_PM,
            "play_wallclock_utc": st.wallclock_utc, "state_fetched_at_utc": st.fetch_time_utc, "feed_lag_s": st.feed_lag_s,
            "quote_fetched_at_utc": quote_ts.isoformat(), "state_to_quote_s": round((quote_ts - fetched).total_seconds(), 3),
            "code_sha": code_sha,
        })
    return rows


def append_rows(rows: list[dict], root: Path) -> int:
    root.mkdir(parents=True, exist_ok=True)
    for r in rows:
        with (root / f"{r['market_type']}_{r['band']}.jsonl").open("a") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return len(rows)


def _git_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def load_prev(root: Path) -> dict:
    p = root / STATE_FILE
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}


def write_recency(live_ids: list, last_row_utc: Optional[datetime], now: datetime,
                  max_age_s: float = WRITE_RECENCY_S) -> tuple[str, str]:
    if not live_ids:
        return "IDLE", "no live games"
    if last_row_utc is None:
        return "FAIL", f"{len(live_ids)} live game(s), no row ever written"
    age = (now - last_row_utc).total_seconds()
    if age > max_age_s:
        return "FAIL", f"{len(live_ids)} live game(s), last row {age:.0f}s ago (> {max_age_s:.0f}s)"
    return "OK", f"{len(live_ids)} live game(s), last row {age:.0f}s ago"


# ---------------------------------------------------------------- one pass
def run_pass(root: Path, io: Io, run_id: Optional[str] = None) -> dict:
    now = io.now()
    run_id = run_id or f"NFLIP-{now:%Y%m%dT%H%M}-{uuid.uuid4().hex[:4]}"
    events, err = io.scoreboard()
    live = [e for e in events if e["status"] == "STATUS_IN_PROGRESS"]
    summary: dict = {"run_id": run_id, "ts_utc": now.isoformat(), "live_games": len(live), "rows": 0, "skips": {},
                     "scoreboard_error": err}

    def skip(k: str) -> None:
        summary["skips"][k] = summary["skips"].get(k, 0) + 1

    prev = load_prev(root)
    lines: dict = dict(prev.get("_lines", {}))
    # cache the pre-game line BEFORE kickoff (in-game the pickcenter may move to a live line)
    for e in events:
        if e["id"] in lines or e["status"] != "STATUS_SCHEDULED":
            continue
        start = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        if timedelta(0) <= start - now <= timedelta(hours=PREGAME_AHEAD_H):
            sp, ou = io.pickcenter(e["id"])
            if sp is not None and ou is not None:
                lines[e["id"]] = {"spread": float(sp), "total": float(ou), "first_seen_utc": now.isoformat(), "pre_kickoff": True}
    last_row = prev.get("_last_row_utc")
    last_row_dt = datetime.fromisoformat(last_row) if last_row else None
    priceable = 0
    sha = _git_sha()
    rows: list[dict] = []
    for ev in live:
        raw, perr, ft = io.plays(ev["id"])
        if perr or not raw:
            skip("feed_error" if perr else "no_plays")
            continue
        states = feed.states_from_plays([feed.normalise(p) for p in raw], ev["id"], ev["home_id"], ev["home"], ev["away"], ft)
        why = feed.is_stale(states, now, True)
        if why:
            skip(why)
            continue
        st = states[-1]
        if st.period > 4:
            skip("overtime_abstain")
            continue
        if st.secs_left_reg <= 0:
            skip("regulation_over")
            continue
        ln = lines.get(ev["id"])
        if ln is None:
            sp, ou = io.pickcenter(ev["id"])
            if sp is None or ou is None:
                skip("no_pregame_line")
                continue
            ln = lines[ev["id"]] = {"spread": float(sp), "total": float(ou), "first_seen_utc": now.isoformat(),
                                    "pre_kickoff": False}
        M, T = -float(ln["spread"]), float(ln["total"])
        line_info = {"line_first_seen_utc": ln["first_seen_utc"], "line_pre_kickoff": ln["pre_kickoff"]}
        n_mk = 0
        for series in SERIES:
            mks = io.markets(event_ticker(series, ev))
            quote_ts = io.now()
            for m in mks:
                info = parse_market(m)
                priced = price_market(series, info, st, ev, M, T) if info else None
                if priced is None:
                    skip("not_priced")
                    continue
                n_mk += 1
                priceable += 1
                made = make_rows(m, series, priced[0], priced[1], st, ev, M, T, line_info, run_id, quote_ts, now, sha)
                if not made:
                    skip("one_sided_book")
                    continue
                rows.extend(made)
        if n_mk == 0:
            skip("no_open_market_for_game")
    summary["rows"] = append_rows(rows, root)
    if summary["rows"]:
        last_row_dt = now
    root.mkdir(parents=True, exist_ok=True)
    keep = {k: v for k, v in prev.items() if not k.startswith("_")}
    (root / STATE_FILE).write_text(json.dumps({**keep, "_lines": lines,
                                               "_last_row_utc": last_row_dt.isoformat() if last_row_dt else None}, sort_keys=True))
    status, detail = write_recency([e["id"] for e in live] if priceable else [], last_row_dt, now)
    summary["recency"], summary["recency_detail"], summary["priceable_markets"] = status, detail, priceable
    with (root / PASS_LOG).open("a") as f:
        f.write(json.dumps(summary, sort_keys=True) + "\n")
    return summary


def health(root: Path, now: datetime) -> tuple[str, str]:
    p = root / PASS_LOG
    if not p.exists():
        return "IDLE", "no in-play pass logged yet"
    cut = now - timedelta(hours=24)
    passes = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    recent = [x for x in passes if datetime.fromisoformat(x["ts_utc"]) >= cut]
    bad = [x for x in recent if x.get("recency") == "FAIL"]
    if bad:
        return "FAIL", f"{len(bad)} pass(es) in 24h with a live game and no row: last {bad[-1]['ts_utc']} ({bad[-1]['recency_detail']})"
    live = [x for x in recent if x.get("live_games")]
    rows = sum(x.get("rows", 0) for x in recent)
    return ("OK", f"{len(recent)} passes, {len(live)} with live games, {rows} rows in 24h") if live else \
           ("IDLE", f"{len(recent)} passes in 24h, no live games")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(SHADOW_DIR))
    ap.add_argument("--health", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.health:
        st, detail = health(root, datetime.now(timezone.utc))
        print(f"{st}: nfl_inplay {detail}")
        return 0
    if not enabled():
        print(f"{ENV_FLAG} is off: nothing fetched, nothing written")
        return 0
    print(json.dumps(run_pass(root, Io()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
