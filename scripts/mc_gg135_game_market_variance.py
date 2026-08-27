#!/usr/bin/env python3
"""
T-494 / GG-135 amendment -- does the MAIN-book ruin geometry transfer to
game markets?  (2026-08-27)
=============================================================================

WHY THIS EXISTS
---------------
GG-135 (RESOLVED via ADR-0048, 2026-07-29) found that MAIN's real per-bet
variance x real cadence trips the permanent 20%-drawdown kill switch at
~100%/yr *independent of edge sign*, on a dataset that was 100% KXMLBHIT
player-prop trades (confirmed live in ADR-0058 Section 1). ADR-0058 proposes
reopening T1 on game markets (MLB_MONEYLINE / MLB_RUN_LINE / MLB_GAME_TOTAL)
and explicitly declines to answer whether GG-135's ruin geometry transfers --
"That question is T-494's, not this session's." This script answers it.

METHOD -- reused, not reimplemented
------------------------------------
`day_params`, `simulate_1yr_pkill`, `bisect_min_edge`, `sweep_lever`,
`frontier_from_sweep` are imported unmodified from `mc_survivable_edge_sweep.py`
(the Window B2 script that produced GG-135's own Kelly/cadence/DD frontier).
`START_BANKROLL`, `KILL_DD`, `DAILY_BREAKER`, `SEED` are imported unmodified
from `mc_empirical_bootstrap.py`. Same day-by-day compounding + kill
mechanics, same TARGET_PKILL=0.10 threshold, same 1yr horizon -- so this
script's numbers are comparable to GG-135's by construction.

WHAT COULD NOT BE REUSED, AND WHY
----------------------------------
`load_book_fracs`/`cohort_fracs` (the other two functions GG-135 used) pull a
real *bet* ledger cache (`.vps_portfolio_cache_*.json`, closed positions with
realized pnl/size_usd). There are zero real T1 game-market positions -- T1 is
zeroed and has never traded these cells (ADR-0058 Sec.1: all nine game-market
T1 cells are `NOT_IMPLEMENTED`). This script therefore builds a *synthetic*
per-bet frac pool from first principles: archived quote data
(`exp_output/PRICE_ARCHIVE/prices_*.jsonl`) joined against real resolved game
outcomes (`logs/t4_mlb_totals_outcome_store.jsonl`, 329 rows / 307 resolved).

JOIN LOGIC
----------
`t4_mlb_totals_outcome_store.jsonl` only carries KXMLBTOTAL-family rows, but
its `home_runs`/`away_runs`/`total_runs` fields are the FINAL SCORE of the
underlying MLB game -- the same final score that resolves KXMLBGAME (moneyline)
and KXMLBSPREAD (run line) contracts for that identical game, since all three
families settle on one shared box score. This script strips the family
prefix from each event_ticker to get a family-agnostic game key
(date+time+teams), and uses that key to resolve GAME/SPREAD contracts too --
so all three families share one ground-truth source, not three.

RESOLUTION CONVENTION (explicit assumption, stated because it is not
independently verified against a Kalshi settlement spec in this session):
threshold ladder contracts resolve YES iff the realized value is
>= the ticker-embedded strike. KXMLBGAME's suffix is a team abbreviation, not
a threshold -- that one resolves YES iff that team's runs > opponent's runs
(assume no ties; extra innings already resolve MLB games unambiguously).

FILL COST (Task 2, T-488/GG-157)
---------------------------------
The T-488 measured per-contract haircuts (2026-08-26 GG-157 update; see
`exp_output/T488_GG157_FILL_HAIRCUT/results.json`, `game_markets_synthetic`
key) are applied as a first-class effective-entry-price adjustment:
  GAME_WINNER (moneyline): mean $0.0340/contract
  GAME_TOTAL  (totals):    mean $0.0307/contract
  RUN_LINE    (spread):    mean $0.0515/contract
Effective entry price P' = P + haircut; frac_net computed at P', frac_gross
at P, both reported. No measured team-total haircut exists (T-488 did not
cover MLB_TEAM_TOTAL) -- team totals are therefore NOT reported as a fourth
family; this is stated as a limitation, not silently dropped.

Usage:
  PYTHONPATH=src python3 scripts/mc_gg135_game_market_variance.py \
      --out exp_output/T494_GG135_GAME_MARKET_RUIN/results.json
"""
from __future__ import annotations

import glob
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from mc_survivable_edge_sweep import (
    day_params, simulate_1yr_pkill, bisect_min_edge, sweep_lever,
    frontier_from_sweep, TARGET_PKILL, GRID_KELLY,
)
from mc_empirical_bootstrap import START_BANKROLL, KILL_DD, DAILY_BREAKER, SEED

ROOT = Path(__file__).resolve().parent.parent
OUTCOME_STORE = ROOT / "logs" / "t4_mlb_totals_outcome_store.jsonl"
PRICE_GLOB = str(ROOT / "exp_output" / "PRICE_ARCHIVE" / "prices_*.jsonl")

# T-488/GG-157, 2026-08-26 update, game_markets_synthetic block --
# mean $/contract haircut, hardcoded from exp_output/T488_GG157_FILL_HAIRCUT/results.json
HAIRCUT_USD = {
    "MONEYLINE": 0.03403409309198988,   # GAME_WINNER
    "RUN_LINE": 0.051486058527668695,   # RUN_LINE
    "TOTALS": 0.030691459059448825,     # GAME_TOTAL
}

FAMILY_SERIES = {
    "MONEYLINE": "KXMLBGAME",
    "RUN_LINE": "KXMLBSPREAD",
    "TOTALS": "KXMLBTOTAL",
}

# GG-135's frac_i is pnl_i / bankroll_before_i -- fraction of BANKROLL, not
# fraction of stake (see mc_empirical_bootstrap.py:98, "p['_frac'] = p['pnl'] / B").
# A synthetic per-contract payoff (which ranges up to -1.0/+huge as a fraction
# of STAKE) must be converted to a fraction of bankroll before it is
# comparable to GG-135's MAIN/T4 sig_g_base figures. ADR-0058/ADR-0059
# propose T1 reopen game markets via the SAME flat measurement-stake
# mechanism T4M-PROJ already uses live ($1 flat stake; ADR-0050), not
# Kelly-proportional sizing -- so this uses that same $1-on-$1000 baseline
# (0.001 of bankroll/bet) as the kelly_mult=1.0 reference point, exactly
# mirroring how GG-135's own T4M-PROJ sig_g_base was itself measured from a
# real flat-$1-stake history. This is a first-class modeling assumption,
# not a footnote -- see Task 4 discussion in the close-out write-up.
STAKE_FRAC_OF_BANKROLL = 1.0 / START_BANKROLL

EDGE_SCENARIOS = [0.0, 0.0002, 0.0005, 0.0010, 0.0020]


def load_resolved_games():
    """game_key (event_ticker w/ 'KXMLBTOTAL-' stripped) -> resolution dict."""
    games = {}
    n_total = 0
    with open(OUTCOME_STORE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            n_total += 1
            if not d.get("resolved"):
                continue
            et = d["event_ticker"]
            assert et.startswith("KXMLBTOTAL-"), et
            key = et[len("KXMLBTOTAL-"):]
            games[key] = {
                "home_abbr": d["home_abbr"], "away_abbr": d["away_abbr"],
                "home_runs": d["home_runs"], "away_runs": d["away_runs"],
                "total_runs": d["total_runs"], "game_date": d["game_date"],
            }
    return games, n_total


def parse_price(v):
    try:
        p = float(v)
    except (TypeError, ValueError):
        return None
    return p


def resolve_contract(family, suffix, game):
    """Return True (YES) / False (NO) per the stated threshold convention."""
    if family == "MONEYLINE":
        team = suffix
        if team == game["home_abbr"]:
            return game["home_runs"] > game["away_runs"]
        elif team == game["away_abbr"]:
            return game["away_runs"] > game["home_runs"]
        return None
    if family == "TOTALS":
        try:
            strike = float(suffix)
        except ValueError:
            return None
        return game["total_runs"] >= strike
    if family == "RUN_LINE":
        # suffix = team abbr + integer margin threshold, e.g. "TEX4"
        i = len(suffix)
        while i > 0 and suffix[i - 1].isdigit():
            i -= 1
        team, num = suffix[:i], suffix[i:]
        if not num:
            return None
        strike = float(num)
        if team == game["home_abbr"]:
            margin = game["home_runs"] - game["away_runs"]
        elif team == game["away_abbr"]:
            margin = game["away_runs"] - game["home_runs"]
        else:
            return None
        return margin >= strike
    raise ValueError(family)


def build_family_fracs(family, series_ticker, games):
    """Scan PRICE_ARCHIVE, take first valid quote per ticker as entry price,
    join to resolved games, return (fracs_gross, fracs_net, dates_used)."""
    first_quote = {}  # ticker -> (mid_price, game_key, suffix)
    files = sorted(glob.glob(PRICE_GLOB))
    for fn in files:
        with open(fn) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("series_ticker") != series_ticker:
                    continue
                ticker = d["ticker"]
                if ticker in first_quote:
                    continue
                bid = parse_price(d.get("yes_bid"))
                ask = parse_price(d.get("yes_ask"))
                if bid is None or ask is None or bid <= 0 or ask <= 0 or ask <= bid:
                    continue
                et = d["event_ticker"]
                prefix = series_ticker + "-"
                if not et.startswith(prefix):
                    continue
                game_key = et[len(prefix):]
                suffix = ticker[len(et) + 1:]
                mid = (bid + ask) / 2.0
                first_quote[ticker] = (mid, game_key, suffix)

    fracs_gross, fracs_net, dates_used, games_touched = [], [], set(), set()
    haircut = HAIRCUT_USD[family]
    n_no_game, n_bad_resolve, n_bad_price = 0, 0, 0
    for ticker, (mid, game_key, suffix) in first_quote.items():
        game = games.get(game_key)
        if game is None:
            n_no_game += 1
            continue
        yes = resolve_contract(family, suffix, game)
        if yes is None:
            n_bad_resolve += 1
            continue
        p = mid
        if not (0.0 < p < 1.0):
            n_bad_price += 1
            continue
        p_net = min(p + haircut, 0.999)
        payoff_gross = (1.0 - p) / p if yes else -1.0
        payoff_net = (1.0 - p_net) / p_net if yes else -1.0
        fracs_gross.append(payoff_gross * STAKE_FRAC_OF_BANKROLL)
        fracs_net.append(payoff_net * STAKE_FRAC_OF_BANKROLL)
        dates_used.add(game["game_date"])
        games_touched.add(game_key)

    diag = {"n_tickers_seen": len(first_quote), "n_no_game_match": n_no_game,
            "n_bad_resolve": n_bad_resolve, "n_bad_price": n_bad_price,
            "n_used": len(fracs_gross), "n_files_scanned": len(files),
            "n_distinct_dates": len(dates_used),
            "n_distinct_games": len(games_touched)}
    return np.array(fracs_gross), np.array(fracs_net), dates_used, diag


def cadence_per_day(dates_used, n_bets):
    """Bets/calendar-day (GG-135's own cadence definition -- see
    mc_empirical_bootstrap.py's lambda_cal, real bets per calendar day, not
    'days with >=1 bet'), spanning the date range actually observed."""
    if not dates_used:
        return 0.0
    dmin, dmax = min(dates_used), max(dates_used)
    from datetime import date
    y1, m1, d1 = (int(x) for x in dmin.split("-"))
    y2, m2, d2 = (int(x) for x in dmax.split("-"))
    span_days = max(1, (date(y2, m2, d2) - date(y1, m1, d1)).days + 1)
    return n_bets / span_days


def main():
    t0 = time.time()
    games, n_total_outcome_rows = load_resolved_games()
    print(f"Resolved games available for join: {len(games)} / {n_total_outcome_rows} outcome-store rows")

    rng = np.random.default_rng(SEED)
    results = {"meta": {
        "seed": SEED, "target_pkill_1yr": TARGET_PKILL,
        "start_bankroll": START_BANKROLL, "real_kill_dd": KILL_DD,
        "real_daily_breaker": DAILY_BREAKER,
        "n_outcome_store_rows": n_total_outcome_rows,
        "n_resolved_games_joinable": len(games),
        "haircut_usd_per_contract": HAIRCUT_USD,
        "stake_frac_of_bankroll_kelly_mult_1x": STAKE_FRAC_OF_BANKROLL,
        "resolution_convention": ">= strike for threshold ladders (TOTALS, RUN_LINE); "
                                  "moneyline resolves on raw run comparison, no ties possible",
        "edge_scenarios": EDGE_SCENARIOS, "grid_kelly_mult": GRID_KELLY,
    }, "families": {}}

    for family, series in FAMILY_SERIES.items():
        fg, fn, dates_used, diag = build_family_fracs(family, series, games)
        if len(fg) < 30:
            results["families"][family] = {"error": "insufficient joined n", "diag": diag}
            print(f"{family}: insufficient n ({len(fg)}) -- skipping sim")
            continue

        g_gross = np.log1p(fg)
        g_net = np.log1p(fn)
        sig_gross = float(np.std(g_gross))
        sig_net = float(np.std(g_net))
        mean_gross = float(np.mean(fg))
        mean_net = float(np.mean(fn))
        lam = cadence_per_day(dates_used, len(fg))
        # ALT cadence: 1 bet per game (T1's real operating assumption -- pick
        # the single best strike/side per game per family), vs. lam above
        # which counts every distinct priced threshold-ladder contract as a
        # bet. lam over-counts for RUN_LINE/TOTALS (many strikes/game); this
        # alt figure bounds how much of the reported cadence is ladder-width
        # artifact rather than real bet frequency -- see Task 4 discussion.
        lam_one_per_game = cadence_per_day(dates_used, diag["n_distinct_games"])

        print(f"\n{family}: n={len(fg)} cadence_all_contracts={lam:.3f}/day "
              f"cadence_one_bet_per_game={lam_one_per_game:.3f}/day "
              f"mean_gross={mean_gross*100:+.3f}%/bet mean_net={mean_net*100:+.3f}%/bet "
              f"sig_g_gross={sig_gross*100:.3f}% sig_g_net={sig_net*100:.3f}%")

        # Task 3: bisection at REAL current-config shape (kelly=1x,cadence=1x,
        # real DD/breaker), using the NET-of-haircut variance shape.
        min_edge, p_at_min = bisect_min_edge(
            sig_net, lam, rng, n_sims=30000, kill_dd=KILL_DD, daily_breaker=DAILY_BREAKER)
        min_edge_alt, p_at_min_alt = bisect_min_edge(
            sig_net, lam_one_per_game, rng, n_sims=30000, kill_dd=KILL_DD, daily_breaker=DAILY_BREAKER)
        print(f"  [alt cadence min-edge check] one_bet_per_game min_edge="
              f"{'NONE up to +2.0%/bet' if min_edge_alt is None else f'{min_edge_alt*100:+.4f}%/bet'}")

        # Task 3/4: Kelly frontier per edge scenario (incl. 0.0, to test
        # whether GG-135's edge-independence property transfers) plus the
        # family's own observed net edge.
        edge_grid = sorted(set(EDGE_SCENARIOS + [round(mean_net, 6)]))
        kelly_frontier = {}
        for edge in edge_grid:
            pts = sweep_lever(sig_net, lam, rng, 8000, edge, "kelly", GRID_KELLY)
            max_kelly = frontier_from_sweep(pts, higher_is_riskier=True)
            kelly_frontier[f"{edge:.4f}"] = {
                "target_edge_pct_per_bet": edge * 100,
                "kelly_mult_sweep": pts,
                "max_kelly_mult_surviving_pkill10": max_kelly,
            }
            print(f"  edge={edge*100:+.4f}%/bet -> max_kelly_mult_surviving={max_kelly}")

        results["families"][family] = {
            "diag": diag,
            "n_used": len(fg),
            "cadence_per_day_all_contracts": lam,
            "cadence_per_day_one_bet_per_game": lam_one_per_game,
            "mean_frac_gross_pct": mean_gross * 100,
            "mean_frac_net_pct": mean_net * 100,
            "sig_g_gross_pct": sig_gross * 100,
            "sig_g_net_pct": sig_net * 100,
            "part_a_min_edge_pct_per_bet_net": None if min_edge is None else min_edge * 100,
            "part_a_pkill_at_min_edge": p_at_min,
            "part_a_min_edge_pct_per_bet_net_one_bet_per_game_cadence":
                None if min_edge_alt is None else min_edge_alt * 100,
            "kelly_frontier_by_edge_scenario": kelly_frontier,
        }

    outp = ROOT / "exp_output" / "T494_GG135_GAME_MARKET_RUIN" / "results.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(outp, "w"), indent=2)
    print(f"\nWrote {outp}  ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
