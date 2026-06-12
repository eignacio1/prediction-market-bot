#!/usr/bin/env python3
"""
EXP-018 — Opponent-Adjusted λ: EV Test Against Kalshi Prices
ADR-0015 | GG-004 | OQ-023

Hypothesis: adj_λ = pts_l10_mean × clip(opp_def_l10/113.0, 0.70, 1.30) produces
positive net-of-fee EV vs actual Kalshi market prices, correcting the
DIRECTIONAL_NEGATIVE result from EXP-017 Part B Finals G1 (raw λ, n=32, EV=-$0.162/bet).

Attribution framing:
  - EXP-017 original (G1 only, raw λ): DIRECTIONAL_NEGATIVE, EV=-$0.162/bet, n=32
  - EXP-018 (G2+ only, adj_λ):        this experiment
  - The T1 paper portfolio contains only adj_λ era bets (G2 onwards);
    G1 is excluded because PIPE-03 was not fully operational on Jun 3.

Data requirements:
  - logs/pregame_YYYYMMDD.json (game_date >= 2026-06-05, adj_λ active post-ADR-0015)
  - logs/paper_portfolio.json  (closed_positions from G2+ game nights)

Additional metric vs EXP-017 Part B:
  - opp_adj_factor = opp_adj_lambda / pts_l10_mean per bet
    Expected < 1.0 in Finals (Knicks/Spurs defenses stronger than league average 113.0)
    Validates that adj_λ is actually suppressing λ in the right direction

Run:
  PYTHONPATH=src python3 scripts/run_exp018.py
  Or: python3 scripts/run_exp018.py  (no PYTHONPATH needed — standalone)
"""
import json
import sys
from pathlib import Path

APR_FLOOR       = 66       # APR-0017 statistical floor (unique resolved markets)
ADJ_LAMBDA_FROM = "2026-06-05"   # ADR-0015 deployment date (Finals G2)
EXP_017_G1_EV   = -0.162  # EXP-017 original Part B baseline (raw λ, to attribute improvement)

PROJ        = Path(__file__).parent.parent
LOGS        = PROJ / "logs"
PORTFOLIO   = LOGS / "paper_portfolio.json"
OUT_PATH    = PROJ / "exp_output" / "EXP-018" / "EXP-018_results.json"


# ── Data loaders ───────────────────────────────────────────────────────────────
def load_pregame_lambda_map() -> dict:
    """
    Load {kalshi_ticker: {opp_adj_lambda, pts_l10_mean}} from adj_λ era pregame files.
    Takes earliest file per ticker to stay consistent with T1 window.
    """
    records: dict[str, dict] = {}
    for f in sorted(LOGS.glob("pregame_*.json")):
        date_str = f.stem.replace("pregame_", "")
        game_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        if game_date < ADJ_LAMBDA_FROM:
            continue
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        for fc in data.get("forecasts", []):
            ticker = fc.get("kalshi_ticker")
            if ticker and ticker not in records:
                records[ticker] = {
                    "opp_adj_lambda": fc.get("opp_adj_lambda"),
                    "pts_l10_mean":   fc.get("pts_l10_mean"),
                    "opp_team":       fc.get("opp_team"),
                    "game_date":      game_date,
                }
    return records


def load_adj_lambda_positions() -> list[dict]:
    """Load closed positions from adj_λ era (game_date >= ADJ_LAMBDA_FROM).

    Positions carrying `duplicate_of` are excluded from experiment n per
    T-169/GG-031 DS ruling (Option A): late-cron re-bets of failed orders
    are committed exposure but not independent market observations.
    """
    data = json.loads(PORTFOLIO.read_text())
    positions = [
        p for p in data.get("closed_positions", [])
        if p.get("game_date", "") >= ADJ_LAMBDA_FROM
        and (p.get("status") in ("RESOLVED", "resolved")
             or p.get("actual_pts") is not None)
    ]
    n_dups = sum(1 for p in positions if p.get("duplicate_of"))
    if n_dups:
        print(f"  T-169 dedupe: excluding {n_dups} duplicate_of positions from experiment n")
    return [p for p in positions if not p.get("duplicate_of")]


# ── EV calculation (same methodology as EXP-017 Part B live) ──────────────────
def compute_pnl_unit(direction: str, mip: float, vig: float, won: bool) -> float:
    half_vig = vig / 2.0
    if direction == "YES":
        price_paid = mip + half_vig
        return (1.0 - price_paid) if won else -price_paid
    else:
        price_paid = (1.0 - mip) + half_vig
        return (1.0 - price_paid) if won else -price_paid


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 65)
    print("EXP-018 — Opponent-Adjusted λ: EV Test Against Kalshi Prices")
    print("ADR-0015 | GG-004 | OQ-023")
    print("=" * 65)

    if not PORTFOLIO.exists():
        print(f"ERROR: {PORTFOLIO} not found.", file=sys.stderr)
        sys.exit(1)

    lambda_map = load_pregame_lambda_map()
    all_positions = load_adj_lambda_positions()

    if not all_positions:
        print("ERROR: No adj_λ era positions found in portfolio.", file=sys.stderr)
        sys.exit(1)

    game_dates = sorted(set(p["game_date"] for p in all_positions))
    print(f"\n  adj_λ era positions:   {len(all_positions)}")
    print(f"  Game dates covered:    {game_dates}")
    print(f"  APR-0017 floor:        >= {APR_FLOOR} unique resolved markets")

    # Deduplicate to unique markets (earliest entry per ticker — matches EXP-017 method)
    seen_tickers: set[str] = set()
    unique_positions: list[dict] = []
    for p in sorted(all_positions, key=lambda x: x.get("entered_at", "")):
        ticker = p.get("kalshi_ticker")
        if ticker and ticker not in seen_tickers:
            seen_tickers.add(ticker)
            unique_positions.append(p)

    n_unique = len(unique_positions)
    print(f"  Unique resolved markets: {n_unique}")

    at_floor = n_unique >= APR_FLOOR
    print(f"  At APR-0017 floor:     {'YES — conclusive' if at_floor else 'NO — directional only'}")

    # EV computation
    pnl_units: list[float] = []
    adj_factors: list[float] = []
    by_direction: dict[str, list] = {"YES": [], "NO": []}
    injury_rows: list[dict] = []

    for p in unique_positions:
        ticker    = p["kalshi_ticker"]
        direction = p["direction"]
        mip       = float(p["mid_price_at_entry"])
        vig       = float(p.get("vig_at_entry", 0.01))
        outcome   = p.get("outcome", "")
        won       = (outcome == "WIN")
        inj       = bool(p.get("probable_injury_signal"))

        pnl = compute_pnl_unit(direction, mip, vig, won)
        pnl_units.append(pnl)
        by_direction[direction].append(pnl)
        if inj:
            injury_rows.append(p)

        lm = lambda_map.get(ticker)
        if lm and lm["opp_adj_lambda"] and lm["pts_l10_mean"] and lm["pts_l10_mean"] > 0:
            adj_factors.append(lm["opp_adj_lambda"] / lm["pts_l10_mean"])

    n_bets = len(pnl_units)
    total_pnl = sum(pnl_units)
    ev_per_bet = total_pnl / n_bets if n_bets else 0.0
    wins_all = sum(1 for p in unique_positions if p.get("outcome") == "WIN")
    win_rate = wins_all / n_bets if n_bets else 0.0

    n_yes = len(by_direction["YES"])
    n_no  = len(by_direction["NO"])
    ev_yes = sum(by_direction["YES"]) / n_yes if n_yes else 0.0
    ev_no  = sum(by_direction["NO"])  / n_no  if n_no  else 0.0

    mean_adj_factor = sum(adj_factors) / len(adj_factors) if adj_factors else None
    n_inj = len(injury_rows)

    # Injury-filtered subset
    clean = [p for p in unique_positions if not p.get("probable_injury_signal")]
    pnl_clean = [compute_pnl_unit(p["direction"], float(p["mid_price_at_entry"]),
                                   float(p.get("vig_at_entry", 0.01)),
                                   p.get("outcome") == "WIN") for p in clean]
    ev_clean = sum(pnl_clean) / len(pnl_clean) if pnl_clean else 0.0

    # Verdict
    def verdict_str(ev: float, n: int) -> str:
        if ev > 0:
            return "DIRECTIONAL_POSITIVE" if n < APR_FLOOR else "CONFIRMED_POSITIVE"
        else:
            return "DIRECTIONAL_NEGATIVE" if n < APR_FLOOR else "CONFIRMED_NEGATIVE"

    verdict_all   = verdict_str(ev_per_bet, n_unique)
    verdict_clean = verdict_str(ev_clean, len(clean))

    print()
    print("── EV Results (adj_λ era, unique markets) ──────────────────")
    print(f"  All bets:         EV={ev_per_bet:+.4f}/bet  ({n_bets} unique markets,  win_rate={win_rate:.3f})")
    print(f"  YES bets only:    EV={ev_yes:+.4f}/bet  ({n_yes} bets)")
    print(f"  NO bets only:     EV={ev_no:+.4f}/bet  ({n_no} bets)")
    print(f"  Injury-filtered:  EV={ev_clean:+.4f}/bet  ({len(clean)} bets, {n_inj} excluded)")
    print()
    print("── opp_adj_factor ──────────────────────────────────────────")
    if mean_adj_factor is not None:
        print(f"  mean opp_adj_factor = {mean_adj_factor:.4f}  (n={len(adj_factors)} bets with lambda data)")
        direction_ok = mean_adj_factor < 1.0
        print(f"  < 1.0 (Finals defense > league avg):  {'YES ✓' if direction_ok else 'NO — unexpected'}")
    else:
        print("  No opp_adj_lambda data available (pregame join failed)")
    print()
    print("── Attribution: adj_λ vs raw λ ─────────────────────────────")
    print(f"  EXP-017 G1 (raw λ):  EV={EXP_017_G1_EV:+.3f}/bet  DIRECTIONAL_NEGATIVE  (n=32)")
    print(f"  EXP-018 G2+ (adj_λ): EV={ev_per_bet:+.4f}/bet  {verdict_all}  (n={n_unique})")
    improvement = ev_per_bet - EXP_017_G1_EV
    print(f"  Improvement:         {improvement:+.4f}/bet  attributed to adj_λ (opponent context)")
    print()
    print("── Verdict ─────────────────────────────────────────────────")
    print(f"  All bets:          {verdict_all}")
    print(f"  Injury-filtered:   {verdict_clean}")

    if verdict_all in ("CONFIRMED_POSITIVE", "DIRECTIONAL_POSITIVE"):
        print(f"  GG-004: adj_λ shows positive EV vs Kalshi prices.")
        if not at_floor:
            print(f"  Power: INSUFFICIENT ({n_unique} < {APR_FLOOR}). Add more game nights.")
    else:
        print(f"  GG-004: adj_λ does NOT show positive EV — model class review required.")
        print(f"  If EV ≤ 0 after >= 30 unique markets, Hypothesis C applies (EXP-018 spec).")

    print("=" * 65)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "exp_id": "EXP-018",
        "adj_lambda_from": ADJ_LAMBDA_FROM,
        "game_dates": game_dates,
        "n_unique_markets": n_unique,
        "at_apr_floor": at_floor,
        "n_yes": n_yes,
        "n_no": n_no,
        "n_injury_excluded": n_inj,
        "win_rate": round(win_rate, 4),
        "ev_per_bet_all": round(ev_per_bet, 6),
        "ev_per_bet_yes": round(ev_yes, 6),
        "ev_per_bet_no": round(ev_no, 6),
        "ev_per_bet_injury_filtered": round(ev_clean, 6),
        "mean_opp_adj_factor": round(mean_adj_factor, 4) if mean_adj_factor is not None else None,
        "verdict_all": verdict_all,
        "verdict_injury_filtered": verdict_clean,
        "attribution": {
            "exp_017_g1_raw_lambda_ev": EXP_017_G1_EV,
            "exp_018_adj_lambda_ev": round(ev_per_bet, 6),
            "improvement": round(improvement, 6),
        },
    }
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved: {OUT_PATH.relative_to(PROJ)}")


if __name__ == "__main__":
    main()
