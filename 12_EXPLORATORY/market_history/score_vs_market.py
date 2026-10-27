"""W88.3 Part B: paired Brier of a frozen model vs the Kalshi pre-game price, game-clustered interval, skill weight.
Joins <model_side.json> rows (game_id, start_time_utc, home, away, p_model, y) to <SERIES>_pregame.jsonl (one market per
event, hourly candles). Market price = mid of (yes_bid.close, yes_ask.close) of the last hourly candle ending at or
before start - 1h (the band's decision time), flipped to the home side when the listed market is the away team; rows
whose market outcome disagrees with the game outcome are dropped and counted.
usage: score_vs_market.py <nhl|nba|mlb> <model_side.json> <pregame.jsonl> <out.json>"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from prediction_market_bot.c3_forecasting import nhl_pregame as nhl  # noqa: E402
from prediction_market_bot.c5_execution.position_gate import skill_weight  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import canon as mlb_canon  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker as nba_parse  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402
from prediction_market_bot.quant.scoring import brier, brier_diff  # noqa: E402

DECISION_LEAD_S = 3600
MATCH_WINDOW_S = 12 * 3600


def listed_team(ticker: str) -> str:
    code = ticker.rsplit("-", 1)[1]
    return mlb_canon(nhl.TEAM_ALIASES.get(code, code))


def mlb_parse(ticker: str):
    """KXMLBGAME-25APR16ATHCWS-ATH (2025 tickers carry no HHMM; the live parser requires one) -> away first, home second."""
    m = re.match(r"^KXMLBGAME-\d{2}[A-Z]{3}\d{2}(?:\d{4})?([A-Z]+)-([A-Z]+)$", ticker)
    if not m:
        return None
    teams, sub = m.groups()
    if teams.startswith(sub):
        away, home = sub, teams[len(sub):]
    elif teams.endswith(sub):
        away, home = teams[:-len(sub)], sub
    else:
        return None
    return {"away": mlb_canon(away), "home": mlb_canon(home)}


def parse_game(kind: str, ticker: str):
    """(home, away) of a game-winner market ticker, or None."""
    pt = {"nhl": nhl.parse_ticker, "nba": nba_parse, "mlb": mlb_parse}[kind](ticker)
    return (pt["home"], pt["away"]) if pt else None


def pre_game_mid(candles: list[dict], cutoff_ts: int):
    best = None
    for c in candles:
        if c["end_period_ts"] <= cutoff_ts and c.get("yes_bid", {}).get("close") and c.get("yes_ask", {}).get("close"):
            best = c
    if best is None:
        return None
    b, a = float(best["yes_bid"]["close"]), float(best["yes_ask"]["close"])
    return (b + a) / 2, a - b, best["end_period_ts"]


def summarize(joined: list[dict]) -> dict:
    ys = [j["y"] for j in joined]
    pm, pk = [j["p_model"] for j in joined], [j["p_market"] for j in joined]
    diff = brier_diff(pk, pm, ys)  # market - model; positive = model beats the market
    mean, lo, hi = cluster_bootstrap({str(j["game_id"]): [d] for j, d in zip(joined, diff)})
    bm, bk = sum(brier(p, y) for p, y in zip(pm, ys)) / len(ys), sum(brier(p, y) for p, y in zip(pk, ys)) / len(ys)
    return {"n_scored": len(joined), "brier_model": bm, "brier_market": bk, "market_minus_model": mean, "ci95": [lo, hi],
            "cluster": "game", "skill_weight": skill_weight(bm, bk),
            "median_spread": sorted(j["spread"] for j in joined)[len(joined) // 2]}


def main():
    kind = sys.argv[1]
    model_side = json.loads(Path(sys.argv[2]).read_text())
    mk = [json.loads(l) for l in Path(sys.argv[3]).open()]
    by_teams = defaultdict(list)
    for r in mk:
        ha = parse_game(kind, r["ticker"])
        if ha:
            by_teams[ha].append(r)
    joined, drop = [], defaultdict(int)
    for g in model_side["rows"]:
        start = datetime.fromisoformat(g["start_time_utc"].replace("Z", "+00:00")).timestamp()
        cands = [r for r in by_teams.get((g["home"], g["away"]), []) if abs(r["occurrence_ts"] - start) < MATCH_WINDOW_S]
        if len(cands) != 1:
            drop["no_market" if not cands else "ambiguous"] += 1
            continue
        r = cands[0]
        px = pre_game_mid(r["candles"], int(start - DECISION_LEAD_S))
        if px is None:
            drop["no_pre_game_quote"] += 1
            continue
        mid, spread, ts = px
        home_listed = listed_team(r["ticker"]) == g["home"]
        y_mkt_home = int(r["result"] == "yes") if home_listed else int(r["result"] == "no")
        if y_mkt_home != g["y"]:
            drop["outcome_disagrees"] += 1
            continue
        joined.append({"game_id": g["game_id"], "p_model": min(max(g["p_model"], 1e-4), 1 - 1e-4),
                       "p_market": mid if home_listed else 1 - mid, "spread": spread, "y": g["y"],
                       "quote_age_s": int(start - DECISION_LEAD_S - ts),
                       **({"inseason_prior_min": g["inseason_prior_min"]} if "inseason_prior_min" in g else {})})
    res = {"model_sha256": model_side["model_sha256"], "season": model_side["season"], "n_model_rows": len(model_side["rows"]),
           "dropped": dict(drop), **summarize(joined)}
    if joined and "inseason_prior_min" in joined[0]:
        res["full_inseason_history_ge30"] = summarize([j for j in joined if j["inseason_prior_min"] >= 30])
    res["rows"] = joined
    Path(sys.argv[4]).write_text(json.dumps(res))
    print({k: v for k, v in res.items() if k != "rows"})


if __name__ == "__main__":
    main()
