"""W97.4 Part C (this season vs Kalshi): the NHL engine's board vs the PRICE_ARCHIVE quotes, paired, game-clustered.

Exploratory. Engine fit on seasons <= 2025, regular season; 2026 games priced with the point-in-time level_adjust.
Market price = mid of the last archive snapshot at least GAP_MIN minutes before puck drop. Outcomes = final scores
(shootout winner credited one goal, as the Kalshi rules read). No orders, no registry cells.
Usage: python3 run_w97_4_kalshi.py <frame.parquet> <price_archive_dir> <out_json> [since_utc]
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nhl_engine import model  # noqa: E402
from prediction_market_bot.quant import bayes_skill  # noqa: E402

ALIAS = {"NJD": "NJ", "SJS": "SJ", "TBL": "TB", "LAK": "LA"}
GAP_MIN = 15
MAX_SPREAD = 0.10   # quote-quality filter on the market side; the unfiltered result is reported too
SER = {"KXNHLGAME": "ML", "KXNHLSPREAD": "SPREAD", "KXNHLTOTAL": "TOTAL", "KXNHLTEAMTOTAL": "TEAMTOTAL"}


def engine_probs(frame: str) -> pd.DataFrame:
    fr = pd.read_parquet(frame)
    fr = fr[fr["game_type"] == 2].reset_index(drop=True)
    tr = fr[(fr["season"] < 2026) & fr["reg_h"].notna() & fr["home_score"].notna()].reset_index(drop=True)
    te = fr[fr["season"] == 2026].reset_index(drop=True)
    m = model.fit(tr, tr["reg_h"].to_numpy(), tr["reg_a"].to_numpy(), (tr["home_score"] > tr["away_score"]).to_numpy())
    lh, la = model.level_adjust(te, *m.rates(te), te["reg_h"].to_numpy(), te["reg_a"].to_numpy())
    b = model.price_games(m, te, n_sim=40000, seed=7, rates=(lh, la))
    te["board"] = b
    return te


def load_archive(d: Path, since: str) -> pd.DataFrame:
    rows = []
    for f in sorted(d.glob("prices_2026-*.jsonl")):
        if f.stem[-10:] < since[:10]:
            continue
        with open(f) as fh:
            for line in fh:
                if '"KXNHL' not in line:
                    continue
                r = json.loads(line)
                if r["series_ticker"] in SER and r["run_ts"] >= since:
                    rows.append((r["run_ts"], r["series_ticker"], r["ticker"], r["event_ticker"], float(r["yes_bid"]), float(r["yes_ask"])))
    return pd.DataFrame(rows, columns=["run_ts", "series", "ticker", "event", "bid", "ask"])


def main(frame: str, arch: str, out: str, since: str = "2026-10-28T05:03:00Z") -> None:
    te = engine_probs(frame)
    key = {}
    for i, r in te.iterrows():
        et = r["start"].tz_convert("America/New_York")
        key[(et.strftime("%y%b%d").upper(), ALIAS.get(r["away"], r["away"]) + ALIAS.get(r["home"], r["home"]))] = i
    a = load_archive(Path(arch), since)
    a["run_ts"] = pd.to_datetime(a["run_ts"], utc=True)
    a["gi"] = a["event"].map(lambda e: key.get((e.split("-")[1][:7], e.split("-")[1][7:])))
    a = a[a["gi"].notna()].copy(); a["gi"] = a["gi"].astype(int)
    a["start"] = a["gi"].map(te["start"])
    a = a[a["run_ts"] <= a["start"] - pd.Timedelta(minutes=GAP_MIN)]
    a = a.sort_values("run_ts").groupby("ticker").tail(1)       # last pre-drop snapshot per market
    a["spread"] = a["ask"] - a["bid"]; a["mid"] = (a["bid"] + a["ask"]) / 2
    res = []
    for _, r in a.iterrows():
        g = te.loc[r["gi"]]; b = g["board"]; fam = SER[r["series"]]
        suf = r["ticker"].split("-")[-1]; hs, aw = g["home_score"], g["away_score"]; ah, aa = ALIAS.get(g["home"], g["home"]), ALIAS.get(g["away"], g["away"])
        if pd.isna(hs):
            continue
        mm = re.match(r"([A-Z]+?)(\d+)$", suf)
        if fam == "ML":
            p, y = (b["moneyline_home"], float(hs > aw)) if suf == ah else (1 - b["moneyline_home"], float(aw > hs))
        elif fam == "TOTAL":
            x = int(suf) - 0.5
            if x not in b["total_over"]: continue
            p, y = b["total_over"][x], float(hs + aw > x)
        elif mm:
            x = int(mm.group(2)) - 0.5; side = mm.group(1)
            if fam == "SPREAD":
                if side == ah and x in b["home_wins_by_over"]: p, y = b["home_wins_by_over"][x], float(hs - aw > x)
                elif side == aa and x in b["away_wins_by_over"]: p, y = b["away_wins_by_over"][x], float(aw - hs > x)
                else: continue
            else:
                if side == ah and x in b["home_goals_over"]: p, y = b["home_goals_over"][x], float(hs > x)
                elif side == aa and x in b["away_goals_over"]: p, y = b["away_goals_over"][x], float(aw > x)
                else: continue
        else:
            continue
        res.append(dict(game=int(g["game_id"]), fam=fam, ticker=r["ticker"], p_eng=float(p), p_mkt=float(r["mid"]), y=y, spread=float(r["spread"])))
    d = pd.DataFrame(res)
    d.to_csv(safe_out(Path(out).with_suffix(".csv")), index=False)

    def stat(x: pd.DataFrame) -> dict:
        if not len(x): return {"n_rows": 0}
        adv = (x["p_mkt"] - x["y"]) ** 2 - (x["p_eng"] - x["y"]) ** 2          # positive = engine beats market
        byg = {str(k): list(v) for k, v in adv.groupby(x["game"])}
        bm = float(((x["p_mkt"] - x["y"]) ** 2).mean()); be = float(((x["p_eng"] - x["y"]) ** 2).mean())
        post = bayes_skill.posterior(byg, bm)
        gm = np.array([np.mean(v) for v in byg.values()]); se = float(gm.std(ddof=1) / np.sqrt(len(gm))) if len(gm) > 1 else float("nan")
        return {"n_rows": len(x), "n_games": len(byg), "brier_engine": be, "brier_market": bm, "adv_mean": float(adv.mean()), "adv_game_mean": float(gm.mean()),
                "adv_se": se, "ci95": [float(gm.mean() - 1.96 * se), float(gm.mean() + 1.96 * se)], "post_mean": post.mean, "post_lo": post.lo, "post_hi": post.hi,
                "p_positive": post.p_positive, "skill_weight": post.weight, "sd_game": float(gm.std(ddof=1)) if len(gm) > 1 else None}
    out_d = {"since": since, "gap_min": GAP_MIN, "max_spread": MAX_SPREAD, "games_priced": int(te["home_score"].notna().sum())}
    for lab, sub in (("all", d), ("tight", d[d["spread"] <= MAX_SPREAD])):
        out_d[lab] = {"ALL": stat(sub)}
        for f in SER.values():
            out_d[lab][f] = stat(sub[sub["fam"] == f])
    safe_out(out).write_text(json.dumps(out_d, indent=1))
    for lab in ("all", "tight"):
        for f, s in out_d[lab].items():
            print(lab, f, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k in ("n_rows", "n_games", "brier_engine", "brier_market", "adv_game_mean", "adv_se", "skill_weight", "p_positive")})


if __name__ == "__main__":
    main(*sys.argv[1:])
