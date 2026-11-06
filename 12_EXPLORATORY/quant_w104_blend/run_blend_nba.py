"""W104.2 Part B (NBA engines): descriptive market-anchored blend weight per engine x family.

READ-ONLY inputs: box rows copied to a scratch dir (NBA_ENGINE_LIVE{,_V2,_V3}/rows.jsonl) and ESPN finals JSON.
usage: run_blend_nba.py <rows_dir> <finals.json> <out.json relative to 12_EXPLORATORY/>
Descriptive only - not a verdict on any sealed cell."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

from _fence import safe_out
from prediction_market_bot.nba_engine.live_scoring import outcome
from prediction_market_bot.quant import blend
from prediction_market_bot.quant.multiplicity import benjamini_hochberg, holm

ABBR = {"GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}
ENGINES = {"v1": "NBA_ENGINE_LIVE", "v2": "NBA_ENGINE_LIVE_V2", "v3": "NBA_ENGINE_LIVE_V3"}
FAMS = ("NBA_MONEYLINE", "NBA_SPREAD", "NBA_GAME_TOTAL", "NBA_TEAM_TOTAL")


def load_finals(path):
    out = {}
    for h, a, hp, ap, d in json.load(open(path)).values():
        out.setdefault((ABBR.get(h, h), ABBR.get(a, a)), []).append((dt.date.fromisoformat(d[:10]), (hp, ap)))
    return out


def final_for(r, finals):
    gd = dt.date.fromisoformat(r["game_date"])
    best = None
    for d, f in finals.get((r["home"], r["away"]), []):
        k = abs((d - gd).days)
        if k <= 1 and (best is None or k < best[0]):
            best = (k, f)
    return best[1] if best else None


def main(rows_dir, finals_path, out_path):
    finals = load_finals(finals_path)
    cells, unmatched = [], {}
    for eng, d in ENGINES.items():
        rows = [json.loads(l) for l in open(Path(rows_dir) / f"{d}.jsonl")]
        for fam in FAMS:
            data, lost = [], 0
            for r in rows:
                if r["family"] != fam or r.get("p_market") is None or r.get("p_engine") is None:
                    continue
                f = final_for(r, finals)
                if f is None:
                    lost += 1
                    continue
                y = outcome(r, f)
                if y is None:
                    continue
                data.append(((r["game_date"], r["home"], r["away"]), r["p_market"], r["p_engine"], float(y)))
            unmatched[f"{eng}/{fam}"] = lost
            for form in ("linear", "logit"):
                rep = blend.blend_report(data, form, b=1000)
                rep.update(engine=eng, family=fam)
                cells.append(rep)
    for form in ("linear", "logit"):
        idx = [i for i, c in enumerate(cells) if c["form"] == form and c.get("w_hat") is not None and c["n_games"] >= 15]
        ps = [max(1 / 1001, 1 - cells[i]["p_w_gt0"]) for i in idx]
        if ps:
            h, bh = holm(ps), benjamini_hochberg(ps, 0.10)
            for i, hh, bb, p in zip(idx, h, bh, ps):
                cells[i].update(p_one_sided=p, p_holm=hh["p_adj"], holm_reject=hh["reject"], bh_reject=bb["reject"])
    json.dump({"cells": cells, "unmatched_rows": unmatched, "note": "descriptive; NBA engine arms only"},
              open(safe_out(out_path), "w"), indent=1, default=list)
    for c in cells:
        if c["form"] == "linear":
            print(c["engine"], c["family"], c["n_games"], c["n_rows"], c.get("w_hat"), c.get("w_boot_ci"),
                  None if c.get("oos_gain") is None else round(c["oos_gain"], 5), c.get("holm_reject"))


if __name__ == "__main__":
    main(*sys.argv[1:4])
