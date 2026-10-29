"""W94.Q Part C: apply quant.bayes_skill to the frozen models' held-out scores. DESCRIPTIVE; stdout only.

Reads models/*_heldout_vs_market_w88.json (and the NFL file) and prints a markdown table. Writes nothing.
position_gate.py stays unwired: this only compares its implied weight with the posterior weight.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from prediction_market_bot.c5_execution.position_gate import skill_weight as gate_skill_weight  # read-only; gate stays unwired
from prediction_market_bot.quant.bayes_skill import DEFAULT_TAU, n_for_weight, posterior_from_summary

ROOT = Path(__file__).resolve().parents[2]
HYPO = 0.01  # counterfactual advantage, for models whose point estimate never reaches the threshold
THRESHOLD = 0.02  # a weight worth acting on: 2% of the market's Brier


def _scored(block: dict) -> tuple[int, float, float, float, float]:
    lo, hi = block["ci95"]
    return (block["n_scored"], block["market_minus_model"], lo, hi, block["brier_market"])


def load() -> list[tuple[str, str, tuple | None]]:
    out = []
    for m in ("nba_pregame_v1", "mlb_game_pregame_v1", "nhl_pregame_v1"):
        d = json.loads((ROOT / f"models/{m}_heldout_vs_market_w88.json").read_text())
        out.append((m, "W88.3 held-out vs Kalshi mid", _scored(d["market_referenced_heldout_brier"])))
    d = json.loads((ROOT / "models/nfl_pregame_v1_heldout_vs_market.json").read_text())
    dm, lo, hi = d["paired_brier_diff_market_minus_model"]
    out.append(("nfl_pregame_v1", "2025 vs nflverse close (GG-1090 timing caveat)", (d["n_games"], dm, lo, hi, d["brier_market"])))
    out.append(("nfl_qb_challenger_v1", "no held-out season exists", None))
    out.append(("nba_player_points_v1", "NOT_REBUILT (no scored rows)", None))
    return out


def main() -> int:
    print(f"tau={DEFAULT_TAU} (prior N(0, tau^2) on the Brier advantage), weight threshold={THRESHOLD}\n")
    print("| model | source | n | point adv | posterior mean [95% CI] | P(adv>0) | posterior weight | gate-implied w | n for w>=thr if point held ; if adv were +0.01 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, src, s in load():
        if s is None:
            pp = posterior_from_summary(0.0, 1.0, 0, 0.25, DEFAULT_TAU)
            print(f"| {name} | {src} | 0 | - | prior only 0.0000 [{pp.lo:+.4f}, {pp.hi:+.4f}] | - | 0.0000 | - | - |")
            continue
        n, d, lo, hi, bm = s
        se = (hi - lo) / (2 * 1.96)
        p = posterior_from_summary(d, se, n, bm, DEFAULT_TAU)
        bk = bm - d
        implied = gate_skill_weight(bk, bm)
        sd_game = se * math.sqrt(n)
        nw = n_for_weight(d, sd_game, bm, THRESHOLD, DEFAULT_TAU)
        nws = f"{nw:,.0f}" if nw else f"never (point adv < {THRESHOLD * bm:.4f})"
        nh = n_for_weight(HYPO, sd_game, bm, THRESHOLD, DEFAULT_TAU)
        nws += f" ; if adv were +{HYPO}: {nh:,.0f}"
        print(f"| {name} | {src} | {n} | {d:+.5f} | {p.mean:+.5f} [{p.lo:+.5f}, {p.hi:+.5f}] | {p.p_positive:.3f} | {p.weight:.4f} | {implied:.4f} | {nws} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
