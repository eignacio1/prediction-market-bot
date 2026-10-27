"""W88.1 Part A: tail fits on per-game P&L, clustered by game. Read-only on every ledger.
Usage: python3 12_EXPLORATORY/tails_evt/run_tails.py <dir with box copies> [out.json]
Inputs (copies of the box files): paper_portfolio_mlb_t4.json, paper_portfolio_mlb.json, *_fill_status.jsonl.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "12_EXPLORATORY"))
import gpd  # noqa: E402
from _fence import safe_out  # noqa: E402

CONFIRMED_FILLED = "CONFIRMED_FILLED"   # mirrors t4_fill_status (the exploratory fence forbids importing it)


def game_key(pos):
    """Cluster id = the Kalshi event segment of the ticker (one game), else game_date. Mirrors t4_fill_status."""
    parts = str(pos.get("kalshi_ticker") or pos.get("ticker") or "").split("-")
    return parts[1] if len(parts) >= 2 and parts[1] else f"date:{pos.get('game_date')}"


def load_fill_status(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("position_id") and row["position_id"] not in out:
            out[row["position_id"]] = row
    return out


def is_confirmed_filled(rec, status):
    row = status.get(rec.get("position_id"))
    return bool(row) and row.get("fill_class") == CONFIRMED_FILLED

BOOKS = {"t4_mlb": ("paper_portfolio_mlb_t4.json", "t4_mlb_fill_status.jsonl"),
         "t1_mlb": ("paper_portfolio_mlb.json", "t1_mlb_fill_status.jsonl")}


def by_game(rows):
    g = defaultdict(lambda: [0.0, 0.0, 0])
    for p in rows:
        k = game_key(p)
        g[k][0] += float(p["pnl"]); g[k][1] += float(p.get("size_usd") or 0); g[k][2] += 1
    keys = sorted(g)
    return (np.array([g[k][0] for k in keys]), np.array([g[k][1] for k in keys]), np.array([g[k][2] for k in keys]))


def analyse(name, pnl, stake, nbets, horizon=(30, 90)):
    r = {"games": len(pnl), "bets": int(nbets.sum()), "pnl_total": float(pnl.sum()), "stake_total": float(stake.sum()),
         "loss_games": int((pnl < 0).sum()), "worst_game_pnl": float(pnl.min()), "worst_game_per_$staked": float((pnl / stake).min())}
    for unit, v in (("usd", -pnl), ("per_usd_staked", -pnl / np.maximum(stake, 1e-9))):
        f = gpd.fit_pot(v)
        ci, fail = gpd.cluster_bootstrap_levels(v, n_boot=600) if f["status"] == "OK" else ({}, None)
        u = {"fit": f, "normal_1in100": gpd.normal_level(v, 100), "normal_1in1000": gpd.normal_level(v, 1000),
             "empirical_max_loss": float(v.max()), "ci_fail_rate": fail}
        for m in (100, 1000):
            lv = gpd.return_level(f, m)
            u[f"gpd_1in{m}"] = lv
            u[f"gpd_1in{m}_ci95"] = ci.get(m) if ci else None
            u[f"gpd_1in{m}_extrapolated"] = len(v) < m
        r[unit] = u
        if unit == "usd":
            r["drawdown_usd"] = {str(h): {"empirical_bootstrap": gpd.drawdown_levels(pnl, h),
                                           "gpd_smoothed": gpd.drawdown_levels(pnl, h, fit=gpd.fit_pot(-pnl)),
                                           "zero_edge_gpd": gpd.drawdown_levels(pnl - pnl.mean(), h, fit=gpd.fit_pot(-(pnl - pnl.mean())))} for h in horizon}
    return r


def main(d, out="tails_evt/tails_W88.json"):
    d = Path(d); res = {}
    for key, (pf, sf) in BOOKS.items():
        closed = [p for p in json.loads((d / pf).read_text())["closed_positions"]
                  if p.get("position_id") and p.get("pnl") is not None and p.get("outcome") in ("WIN", "LOSS")]
        status = load_fill_status(d / sf)
        filled = [p for p in closed if is_confirmed_filled(p, status)]
        res[key] = {"filled": analyse(key, *by_game(filled)), "paper_all": analyse(key, *by_game(closed))}
    safe_out(out).write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    r = main(*sys.argv[1:3])
    for k, v in r.items():
        for c, a in v.items():
            u, p = a["usd"], a["per_usd_staked"]
            print(k, c, f"games={a['games']} bets={a['bets']} pnl={a['pnl_total']:.1f} worst_game={a['worst_game_pnl']:.1f}",
                  f"| fit={u['fit']['status']} n_exc={u['fit'].get('n_exc')} xi={u['fit'].get('xi')}",
                  f"| usd 1/100 gpd={u['gpd_1in100']} ci={u['gpd_1in100_ci95']} normal={u['normal_1in100']:.1f}",
                  f"| 1/1000 gpd={u['gpd_1in1000']} ci={u['gpd_1in1000_ci95']} normal={u['normal_1in1000']:.1f}")
            print("   per$staked: 1/100", p["gpd_1in100"], "1/1000", p["gpd_1in1000"], "empmax", p["empirical_max_loss"])
            print("   DD(as-is)", {h: x["gpd_smoothed"] for h, x in a["drawdown_usd"].items()}); print("   DD(zero-edge)", {h: x["zero_edge_gpd"] for h, x in a["drawdown_usd"].items()})
