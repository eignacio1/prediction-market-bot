#!/usr/bin/env python3
"""Run the NFL WR mass-tier classifier for 2023-2025, write the PAM store, print the Part B report (W75.1).

Needs the local nflverse build (exp_output/NFL_EVENTS/raw). Offline analysis, no running component.
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.pam import PamStore, nfl_wr_mass as m  # noqa: E402

SEASONS = (2023, 2024, 2025)
TAX = {
    "version": m.VERSION, "sport": "nfl", "position_group": "WR", "min_targets": m.MIN_TARGETS, "prune_weight": m.PRUNE,
    "archetypes": {
        "WR-VERT": {"name": "Vertical Stretcher", "score": "mean(clip((aDOT-9)/6), clip((deep_rate-.10)/.20), clip((route_deep-.20)/.25))",
                    "sources": "pbp air_yards; participation route (GO/POST/CORNER/WHEEL)"},
        "WR-YAC": {"name": "YAC / Short-Game Weapon", "score": "mean(clip((YAC_per_rec-3.5)/3), clip((short_rate-.25)/.30))",
                   "sources": "pbp yards_after_catch, air_yards<=3"},
        "WR-VOL": {"name": "Volume Target Earner", "score": "clip((target_share-.14)/.12)", "sources": "pbp targets by team"},
        "WR-MID": {"name": "Intermediate Chain-Mover", "score": "clip(1-|aDOT-10|/5)", "sources": "pbp air_yards"},
    },
    "note": "Weights = scores normalised; weights < prune dropped and renormalised. Thresholds fixed a priori, not fitted.",
}


def split_half(t, ids):
    wk = t.week
    a, b = m.features(t[wk % 2 == 1], ids, 25), m.features(t[wk % 2 == 0], ids, 25)
    j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
    out = {}
    for k in ("adot", "deep_rate", "yac_per_rec", "tgt_share", "short_rate"):
        r = j[f"{k}_a"].corr(j[f"{k}_b"])
        out[k] = round(2 * r / (1 + r), 2)  # Spearman-Brown to full-season reliability
    return out, len(j)


def main(write=True):
    labels = {k: v["name"] for k, v in TAX["archetypes"].items()}
    tdir = Path("qualitative_data/pam/nfl")
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "taxonomy.json").write_text(json.dumps(TAX, indent=1, sort_keys=True) + "\n")
    feats, cls, recs, prior, rel = {}, {}, [], {}, {}
    today = dt.date.today()
    for s in SEASONS:
        t = m.load_targets(s)
        ids = m.wr_ids(s)
        feats[s] = m.features(t, ids)
        cls[s] = m.classify(feats[s])
        rel[s] = split_half(t, ids)
        recs += m.to_records(s, feats[s], cls[s], labels, today, prior)
        prior = {g: f"nfl:wr:{s}:{g}" for g in feats[s].index}
    if write:
        st = PamStore()
        old = {r.record_id for r in st.load("nfl")}
        st.append([r for r in recs if r.record_id not in old])
    print("== counts (primary archetype) ==")
    for s in SEASONS:
        print(s, len(feats[s]), cls[s].primary.value_counts().to_dict())
        print("   hybrids (>=2 archetypes):", int((cls[s].w.apply(len) > 1).sum()))
    print("== split-half reliability (Spearman-Brown, odd/even weeks), n ==")
    for s in SEASONS:
        print(s, rel[s])
    print("== year-over-year ==")
    for a, b in zip(SEASONS, SEASONS[1:]):
        j = feats[a].join(feats[b], lsuffix="_a", rsuffix="_b", how="inner")
        ca, cb = cls[a].loc[j.index, "primary"], cls[b].loc[j.index, "primary"]
        same = float((ca == cb).mean())
        chance = float(sum((ca.value_counts(normalize=True).get(k, 0)) * (cb.value_counts(normalize=True).get(k, 0)) for k in TAX["archetypes"]))
        corr = {k: round(j[f"{k}_a"].corr(j[f"{k}_b"]), 2) for k in ("adot", "deep_rate", "yac_per_rec", "tgt_share", "short_rate")}
        print(f"{a}->{b}: n={len(j)} primary retained {same:.2f} vs chance {chance:.2f}; feature YoY r={corr}")
    print("== examples (2025) ==")
    f, c = feats[2025], cls[2025]
    for gid in f.sort_values("targets", ascending=False).index[:40]:
        r = f.loc[gid]
        print(f"{r['name']:<14} {r.team:<4} tgt={int(r.targets):>3} aDOT={r.adot:5.1f} YAC/rec={r.yac_per_rec:4.1f} share={r.tgt_share:.2f} -> "
              + " / ".join(f"{k} {v:.2f}" for k, v in c.loc[gid, 'w'].items()))


if __name__ == "__main__":
    main(write="--dry" not in sys.argv)
