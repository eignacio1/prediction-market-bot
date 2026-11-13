"""W112.1 Part B -- build the tested filter-split table the router reads (decision_trees/filter_splits.json) and the
point-in-time NBA team-percentile table the NBA adapter reads (decision_trees/filter_data/nba_team_percentiles.json).

Inputs are RESULTS already produced by earlier waves: 111.4 `granularity_index_nba/leaf_scores.json` (+ team_percentiles.json)
and 110.1 `20261111_w110_1_nfl_weather_matchup/results_leaves.json`. Nothing is refitted here.
KEPT rule (fixed a priori, written before the table was built): a split may change the logged arm only if its leaf is not thin,
the arm is not NO_BET, the held-out window has >= MIN_HELD_GAMES games AND a positive held-out mean net after the exact fee.
Every other tested leaf stays in the table as logged-only (it is logged on the row, never split on).
Applies when: refreshing the table after the index is re-scored. Doesn't: it does not choose arms, it copies the scored ones.
Run: python3 scripts/build_filter_splits_w112.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP = ROOT / "12_EXPLORATORY"
OUT = ROOT / "src" / "prediction_market_bot" / "decision_trees"
MIN_HELD_GAMES = 10
NBA_SERIES = {"GAME_TOTAL": "KXNBATOTAL", "TEAM_TOTAL": "KXNBATEAMTOTAL", "SPREAD": "KXNBASPREAD", "MONEYLINE": "KXNBAGAME"}
NBA_DATA_THROUGH = "2026-06-30T00:00:00+00:00"  # end of the 2025-26 season: the percentiles use nothing later


def nba_splits() -> list:
    doc = json.loads((EXP / "granularity_index_nba" / "leaf_scores.json").read_text())
    out = []
    for x in doc["leaves"]:
        kind = "total" if x["family"] in ("GAME_TOTAL", "TEAM_TOTAL") else "side"
        tg, tm = x.get("test_games") or 0, x.get("test_mean")
        kept = (not x["thin"] and x["arm"] != "NO_BET" and tg >= MIN_HELD_GAMES and tm is not None and tm > 0)
        why = ("kept" if kept else "thin" if x["thin"] else "no_arm_positive_in_fit" if x["arm"] == "NO_BET"
               else "held_out_games_below_min" if tg < MIN_HELD_GAMES else "held_out_net_not_positive")
        out.append({"sport": "NBA", "series": NBA_SERIES[x["family"]], "filter": f"{x['entry']}@{kind}", "leaf": x["leaf"],
                    "arm": x["arm"], "kept": bool(kept), "why": why, "fit_games": x["fit_games"], "test_games": tg,
                    "test_mean": tm, "bh": x["bh"], "source": "111.4 leaf_scores.json"})
    return out


NHL_SERIES = {"NHL_GAME_TOTAL": "KXNHLTOTAL", "NHL_PUCK_LINE": "KXNHLSPREAD", "NHL_MONEYLINE": "KXNHLGAME"}


def nhl_splits() -> list:
    """W113.1 Part B: the 112.x NHL per-leaf scores (nhl_factors_w112/leaf_scores.json), same KEPT rule as the NBA table."""
    doc = json.loads((EXP / "nhl_factors_w112" / "leaf_scores.json").read_text())
    out = []
    for x in doc["leaves"]:
        tg, tm = x.get("test_games") or 0, x.get("test_mean")
        kept = (not x["thin"] and x["arm"] != "NO_BET" and tg >= MIN_HELD_GAMES and tm is not None and tm > 0)
        why = ("kept" if kept else "thin" if x["thin"] else "no_arm_positive_in_fit" if x["arm"] == "NO_BET"
               else "held_out_games_below_min" if tg < MIN_HELD_GAMES else "held_out_net_not_positive")
        out.append({"sport": "NHL", "series": NHL_SERIES[x["family"]], "filter": x["filter"], "leaf": x["leaf"],
                    "arm": x["arm"], "kept": bool(kept), "why": why, "fit_games": x["fit_games"], "test_games": tg,
                    "test_mean": tm, "bh": x["bh"], "source": "112 nhl_factors_w112 leaf_scores.json"})
    return out


def nfl_splits() -> list:
    doc = json.loads((EXP / "20261111_w110_1_nfl_weather_matchup" / "results_leaves.json").read_text())
    out = []
    for x in doc["leaves"]:
        if x["market_state"] is not None:
            continue  # the market-state crossed leaves duplicate the router's own market-state split
        kind = "total" if x["arm"] in ("OVER", "UNDER") else "side"
        out.append({"sport": "NFL", "series": None, "filter": f"{x['filter']}@{kind}", "leaf": x["leaf"], "arm": x["arm"],
                    "kept": x["earns"] == "yes", "why": "kept" if x["earns"] == "yes" else f"tested_{x['earns']}",
                    "fit_games": None, "test_games": x["n"], "test_mean": x["net"], "bh": False,
                    "source": "110.1 results_leaves.json"})
    return out


def main() -> int:
    splits = nba_splits() + nfl_splits() + nhl_splits()
    doc = {"min_held_games": MIN_HELD_GAMES, "rule": "kept = not thin, arm != NO_BET, held-out games >= min, held-out mean net > 0",
           "n": len(splits), "n_kept": sum(s["kept"] for s in splits), "splits": splits}
    (OUT / "filter_splits.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    (OUT / "filter_data").mkdir(exist_ok=True)
    pct = json.loads((EXP / "granularity_index_nba" / "team_percentiles.json").read_text())
    (OUT / "filter_data" / "nba_team_percentiles.json").write_text(json.dumps(
        {"data_through_utc": NBA_DATA_THROUGH, "season_label": 2026, "teams": pct}, indent=1, sort_keys=True) + "\n")
    print(f"splits={doc['n']} kept={doc['n_kept']} teams={len(pct)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
