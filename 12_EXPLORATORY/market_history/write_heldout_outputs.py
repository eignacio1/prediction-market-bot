"""W88.3 Part B: from score_vs_market.py outputs, write NEW models/<model>_heldout_vs_market_w88.json and replay the
position gate (descriptive only; the gate stays unwired). Replay: each scored game is one Candidate (home-side YES
market, bid/ask = mid -/+ spread/2, fee = 0.07*p*(1-p), the Kalshi taker schedule, un-rounded); error bar = sd of
(p_model - p_market) over the scored rows. Run at (a) the skill weight the gate rule implies, (b) weight 1.0 as a
labelled counterfactual (the model fully trusted), with realised flat-1-contract P&L on kept positions.
usage: write_heldout_outputs.py <repo_root> <model_id> <scored.json> > models/<model_id>_heldout_vs_market_w88.json
(JSON to stdout, replay summary to stderr; this script writes no files itself)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
sys.path.insert(0, str(repo / "src"))
from prediction_market_bot.c5_execution.position_gate import Candidate, error_bar, select  # noqa: E402


def replay(rows: list[dict], weight: float, bar: float) -> dict:
    cands = []
    for r in rows:
        mid, h = r["p_market"], r["spread"] / 2
        cands.append(Candidate(ts=str(r.get("game_date", r["game_id"])), market_ticker=str(r["game_id"]), band="T1",
                               game=str(r["game_id"]), family="MONEYLINE", p_model=r["p_model"], mid=mid,
                               yes_bid=mid - h, yes_ask=mid + h, fee=0.07 * mid * (1 - mid)))
    kept = select(cands, weight, bar)
    by_id = {str(r["game_id"]): r for r in rows}
    pnl = []
    for c, side in kept:
        y = by_id[c.market_ticker]["y"]
        pnl.append((y - c.yes_ask - c.fee) if side == "yes" else ((1 - y) - (1 - c.yes_bid) - c.fee))
    return {"weight": weight, "error_bar": bar, "n_kept": len(kept),
            "realised_pnl_per_contract": (sum(pnl) / len(pnl)) if pnl else None}


model_id, path = sys.argv[2], sys.argv[3]
s = json.loads(Path(path).read_text())
rows = s["rows"]
bar = error_bar([r["p_model"] - r["p_market"] for r in rows])
body = {k: v for k, v in s.items() if k != "rows"}
out = {"model_id": model_id,
       "market_referenced_heldout_brier": {**body, "price": "Kalshi game-winner home-side mid of the last hourly candle ending <= start-1h (band decision time), flipped to home if the listed market is the away side",
                                           "interval": "game-clustered percentile bootstrap, 2000 resamples, seed 20261002, via quant.inference.cluster_bootstrap"},
       "skill_weight": body["skill_weight"],
       "gate_rule": "position_gate.skill_weight = clip(1 - Bm/Bk, 0, 1)",
       "gate_replay_descriptive": {"at_implied_weight": replay(rows, body["skill_weight"], bar),
                                   "counterfactual_model_fully_trusted": replay(rows, 1.0, bar)},
       "generated_utc": "2026-10-27",
       "note": "new W88.3 file; existing models/ files untouched; descriptive only, gate stays unwired"}
sys.stdout.write(json.dumps(out, indent=1) + "\n")
print(model_id, out["gate_replay_descriptive"], file=sys.stderr)
