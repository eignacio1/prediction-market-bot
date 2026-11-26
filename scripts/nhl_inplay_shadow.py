#!/usr/bin/env python3
"""W129.7 -- NHL in-play SHADOW logger for the T4NHL-ARITH cells. Evaluate-and-log only: imports no order code.

One pass per invocation (cron runs it every 2 minutes in the game window; it exits at once when none are):
  live games (NHL /score/now) -> play-by-play state with measured latency -> staleness gate -> pre-game goal rates
  -> in-play price per open Kalshi market of that game -> one JSONL row per market in
  data/shadow/nhl_inplay/<MARKET_TYPE>_T4NHL-ARITH.jsonl.

OFF unless PM_NHL_INPLAY is 1/on/true. No orders, kelly 0, no kelly import. DATA RULE: NHL data is fetched, never used to
train a model (Content-Signal ai-train=no).

  --health   one line OK|IDLE|FAIL for logs/health.log: FAIL = a pass in the last 24h saw a live game with a priceable
             market and wrote no row for longer than the write-recency limit.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nhl_live as nl  # noqa: E402
from prediction_market_bot.c3_forecasting import nhl_inplay as ip  # noqa: E402
from prediction_market_bot.c3_forecasting.nhl_pregame import MARKET_TYPE, parse_ticker  # noqa: E402

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = {"KXNHLGAME": "NHL_MONEYLINE", "KXNHLSPREAD": "NHL_PUCK_LINE", "KXNHLTOTAL": "NHL_GAME_TOTAL"}
BAND = "T4NHL-ARITH"
SHADOW_DIR = Path("data/shadow/nhl_inplay")
PASS_LOG = "pass_log.jsonl"
STATE_FILE = "_last_state.json"
ENV_FLAG = "PM_NHL_INPLAY"


def enabled(env=os.environ) -> bool:
    return str(env.get(ENV_FLAG, "")).strip().lower() in ("1", "on", "true", "yes")


def quote(m: dict) -> Optional[tuple[float, float]]:
    try:
        b, a = float(m["yes_bid_dollars"]), float(m["yes_ask_dollars"])
    except (KeyError, TypeError, ValueError):
        return None
    return (b, a) if 0.0 < b < a < 1.0 else None


def fetch_open_markets(series: str, th: ni.Throttle, opener=None) -> list[dict]:
    out, cur = [], ""
    while True:
        d = ni.http_get_json(f"{KALSHI}/markets?series_ticker={series}&status=open&limit=200" + (f"&cursor={cur}" if cur else ""),
                             th, opener=opener)
        out.extend(d.get("markets", []))
        cur = d.get("cursor") or ""
        if not cur:
            return out


def make_row(market: dict, info: dict, p_yes: float, state: dict, lam: tuple[float, float], run_id: str,
             quote_ts: datetime, now: datetime, code_sha: str) -> Optional[dict]:
    q = quote(market)
    if q is None:
        return None
    bid, ask = q
    return {
        "run_id": run_id, "ts_utc": now.isoformat(), "sport": "NHL", "market_type": MARKET_TYPE[info["series"]],
        "band": BAND, "event_ticker": market["event_ticker"], "market_ticker": market["ticker"],
        "p_yes": p_yes, "yes_bid": bid, "yes_ask": ask, "mid": (bid + ask) / 2.0, "half_spread": (ask - bid) / 2.0,
        "lam_h": lam[0], "lam_a": lam[1], "game_id": state["game_id"],
        "score_h": state["score_h"], "score_a": state["score_a"], "period": state["period"],
        "minutes_left_reg": state["minutes_left_reg"], "strength": state["strength"], "empty_net": state["empty_net"],
        "pp_secs_left": state.get("pp_secs_left"), "sog_h": state.get("sog_h"), "sog_a": state.get("sog_a"),
        "last_event_id": state.get("last_event_id"), "state_fetched_at_utc": state["fetched_at_utc"],
        "feed_latency_ms": state["latency_ms"], "quote_fetched_at_utc": quote_ts.isoformat(),
        "state_to_quote_s": round((quote_ts - datetime.fromisoformat(state["fetched_at_utc"])).total_seconds(), 3),
        "code_sha": code_sha,
    }


def append_rows(rows: list[dict], root: Path) -> int:
    n = 0
    root.mkdir(parents=True, exist_ok=True)
    for r in rows:
        with (root / f"{r['market_type']}_{BAND}.jsonl").open("a") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
        n += 1
    return n


def _git_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def load_prev(root: Path) -> dict:
    p = root / STATE_FILE
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}


def run_pass(root: Path, now: datetime, fcst: Any, th_nhl: ni.Throttle, th_k: ni.Throttle, opener_nhl=None,
             opener_k=None, run_id: Optional[str] = None) -> dict:
    run_id = run_id or f"INPLAY-{now:%Y%m%dT%H%M}-{uuid.uuid4().hex[:4]}"
    live = nl.list_live_game_ids(th_nhl, opener=opener_nhl)
    summary: dict = {"run_id": run_id, "ts_utc": now.isoformat(), "live_games": len(live), "rows": 0, "skips": {}}

    def skip(k: str) -> None:
        summary["skips"][k] = summary["skips"].get(k, 0) + 1

    prev_all = load_prev(root)
    last_row = prev_all.get("_last_row_utc")
    last_row_dt = datetime.fromisoformat(last_row) if last_row else None
    priceable = 0
    sha = _git_sha()
    if live:
        markets: dict[str, list[dict]] = {}
        for s in SERIES:
            for m in fetch_open_markets(s, th_k, opener_k):
                markets.setdefault(m["event_ticker"], []).append(m)
        quote_ts = nl.utcnow() if opener_k is None else now
        new_state: dict = {}
        by_gid: dict[int, list[tuple[dict, dict]]] = {}
        for ev, ms in markets.items():
            for m in ms:
                info = parse_ticker(m["ticker"])
                g = fcst._game(info) if info else None
                if g is not None and int(g["game_id"]) in live:
                    by_gid.setdefault(int(g["game_id"]), []).append((m, info))
        rows: list[dict] = []
        for gid in live:
            try:
                st = nl.fetch_state(gid, th_nhl, opener=opener_nhl, clock=(lambda: now) if opener_nhl else nl.utcnow)
            except Exception:
                skip("feed_error")
                continue
            why = nl.staleness(st, prev_all.get(str(gid)), now if opener_nhl else nl.utcnow())
            if why:
                skip(why)
                continue
            new_state[str(gid)] = st
            mk = by_gid.get(gid)
            if not mk:
                skip("no_open_market_for_game")
                continue
            try:
                game = fcst._game(dict(mk[0][1]))
                start = datetime.fromisoformat(game["start_time_utc"].replace("Z", "+00:00"))
                _l, lh, la = fcst.model.raw_ladder(fcst.feature_row(game, start))
            except Exception:
                skip("no_pregame_rates")
                continue
            for m, info in mk:
                priced = ip.price_ticker(m["ticker"], lh, la, st)
                if priced is None:
                    skip("not_priced")
                    continue
                priceable += 1
                row = make_row(m, info, priced[0], st, (lh, la), run_id, quote_ts, now, sha)
                if row is None:
                    skip("one_sided_book")
                    continue
                rows.append(row)
        summary["rows"] = append_rows(rows, root)
        if summary["rows"]:
            last_row_dt = now
        new_state["_last_row_utc"] = last_row_dt.isoformat() if last_row_dt else None
        root.mkdir(parents=True, exist_ok=True)
        (root / STATE_FILE).write_text(json.dumps({**prev_all, **new_state}, sort_keys=True))
    status, detail = nl.write_recency(live if priceable else [], last_row_dt, now)
    summary["recency"], summary["recency_detail"], summary["priceable_markets"] = status, detail, priceable
    root.mkdir(parents=True, exist_ok=True)
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


def build_forecaster(now: datetime):
    from prediction_market_bot.c2_feature_store.nhl_features import NhlFeatureStore
    from prediction_market_bot.c3_forecasting.nhl_pregame import NhlPregameForecaster, load_model
    model, sha = load_model()
    cur = now.year - (1 if now.month < 8 else 0)
    sched = ni.load_schedule(cur) + ni.load_schedule(cur - 1)
    return NhlPregameForecaster(model, sha, NhlFeatureStore(ni.load_games()), sched)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(SHADOW_DIR))
    ap.add_argument("--health", action="store_true")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    root = Path(a.root)
    if a.health:
        st, detail = health(root, now)
        print(f"{st}: nhl_inplay {detail}")
        return 0
    if not enabled():
        print(f"{ENV_FLAG} is off: nothing fetched, nothing written")
        return 0
    s = run_pass(root, now, build_forecaster(now), ni.Throttle(1.0), ni.Throttle(1.0))
    print(json.dumps(s, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
