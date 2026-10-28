"""W93.3 Part B: engine vs this season's Kalshi NBA prices (descriptive; no settled games exist yet).

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_board/study_b.py <NBA_EVENTS raw dir> <archive nba_rows.jsonl> <out json>
Ratings are prior-only (previous-season means): no 2026-27 schedule/team_box is published in the event store.
Market side: last archive snapshot per event; mid = (bid+ask)/2; ladders via quant.ladder.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import study_a as A  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import engine as E, ratings as R  # noqa: E402
from prediction_market_bot.quant import ladder as L  # noqa: E402


def main(raw, rows_path, out):
    tg = A.load(raw)
    tg = tg[tg["season_type"] == "regular-season"]
    full, league = R.prior_table(tg[tg.season == 2026], ("pace", "ortg", "drtg"))
    # calibration on season 2026 (rolling origin: shape from the latest complete season)
    g26 = R.game_inputs(R.add_ratings(tg[tg.season <= 2026], k=10.0))
    g26 = g26[g26.season == 2026]
    cal = A.calibrate(g26)
    print({k: round(v, 3) for k, v in cal.items()})
    code2id = {}
    import glob
    import pandas as pd
    sch = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{raw}/schedule/*.parquet"))], ignore_index=True)
    sch = sch[sch.season == 2026]
    for side in ("home", "away"):
        for tid, c in zip(sch[f"{side}_team_id"], sch[f"{side}_team_abbreviation"]):
            code2id[str(c)] = tid
    alias = {"GS": "GSW", "NY": "NYK", "NO": "NOP", "SA": "SAS", "PHX": "PHX", "WSH": "WAS", "UTAH": "UTA"}
    snap = defaultdict(dict)
    for line in open(rows_path):
        r = json.loads(line)
        snap[r["event_ticker"]][r["ticker"] + "|" + r["run_ts"]] = r
    events = defaultdict(lambda: defaultdict(list))
    for ev, d in snap.items():
        lastts = max(x["run_ts"] for x in d.values())
        for r in d.values():
            if r["run_ts"] != lastts:
                continue
            bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
            events[ev.split("-")[0]][ev.split("-")[1]].append(dict(ticker=r["ticker"], bid=bid, ask=ask, hs=(ask - bid) / 2))
    games = sorted(events["KXNBAGAME"])
    res, skipped = [], []
    for g in games:
        codes = sorted({r["ticker"].rsplit("-", 1)[1] for r in events["KXNBAGAME"][g]})
        if len(codes) != 2:
            skipped.append((g, "codes"))
            continue
        # Kalshi event ticker is AWAYHOME; derive from the two team codes' order in the ticker string
        s = g[7:]
        a_code = next((c for c in codes if s.startswith(c)), None)
        h_code = next((c for c in codes if c != a_code), None)
        ids = [code2id.get(alias.get(c, c)) for c in (h_code, a_code)]
        if None in ids or a_code is None:
            skipped.append((g, "unmapped " + str(codes)))
            continue
        h, a = ids
        ph, pa = full.loc[h], full.loc[a]
        row = {k: float(np.asarray(v).ravel()[0]) for k, v in dict(mu_poss=(ph["pace"] + pa["pace"]) / 2, ppp_h=(ph["ortg"] + pa["drtg"]) / 2, ppp_a=(pa["ortg"] + ph["drtg"]) / 2).items()}
        s_ = A.sim_game(row, cal, 5)
        e_mu_m, e_sd_m, e_mu_t, e_sd_t = float(s_.margin.mean()), float(s_.margin.std()), float(s_.total.mean()), float(s_.total.std())
        ml = {r["ticker"].rsplit("-", 1)[1]: 0.5 * (r["bid"] + r["ask"]) for r in events["KXNBAGAME"][g]}
        mk_ml_home = ml[h_code] / (ml[h_code] + ml[a_code])
        out_g = dict(game=g, home=h_code, away=a_code, e_p_home=E.p_moneyline_home(s_), mk_p_home=mk_ml_home,
                     mk_overround=ml[h_code] + ml[a_code], ml_halfspread=float(np.mean([r["hs"] for r in events["KXNBAGAME"][g]])),
                     e_mu_margin=e_mu_m, e_sd_margin=e_sd_m, e_mu_total=e_mu_t, e_sd_total=e_sd_t)
        sp = events["KXNBASPREAD"].get(g)
        if sp:
            rows = [dict(ticker=r["ticker"], bid=r["bid"], ask=r["ask"]) for r in sp]
            ref = sorted({L.parse_ticker(r["ticker"])[1] for r in rows})[0]
            f = L.fit_normal(L.survival_points(rows, "margin"))
            if f:
                sgn = 1.0 if ref == h_code else -1.0
                out_g.update(mk_mu_margin=sgn * f["mu"], mk_sd_margin=f["sigma"], mk_spread_n=f["n"], mk_spread_rmse=f["rmse"])
                out_g["mk_p_home_from_spread"] = float(L.surv_normal(0.0, sgn * f["mu"], f["sigma"]))
        tt = events["KXNBATOTAL"].get(g)
        if tt:
            f = L.fit_normal(L.survival_points([dict(ticker=r["ticker"], bid=r["bid"], ask=r["ask"]) for r in tt], "total"))
            if f:
                out_g.update(mk_mu_total=f["mu"], mk_sd_total=f["sigma"], mk_total_n=f["n"], mk_total_rmse=f["rmse"])
        res.append(out_g)
    res_all = res
    res = [r for r in res if not r["game"].startswith("26OCT27")]  # live/finished at snapshot time: excluded

    def col(k, rs=None):
        return np.array([r[k] for r in (rs or res) if k in r], float)

    sp = [r for r in res if "mk_mu_margin" in r]
    tl = [r for r in res if "mk_mu_total" in r]
    d_ml = col("e_p_home") - col("mk_p_home")
    summ = dict(
        n_games=len(res), n_with_spread_ladder=len(sp), n_with_total_ladder=len(tl),
        ml_engine_minus_market_mean=float(d_ml.mean()), ml_abs_diff_mean=float(np.abs(d_ml).mean()),
        ml_corr=float(np.corrcoef(col("e_p_home"), col("mk_p_home"))[0, 1]),
        margin_mu_diff_mean=float((col("e_mu_margin", sp) - col("mk_mu_margin", sp)).mean()),
        margin_mu_diff_sd=float((col("e_mu_margin", sp) - col("mk_mu_margin", sp)).std()),
        margin_mu_corr=float(np.corrcoef(col("e_mu_margin", sp), col("mk_mu_margin", sp))[0, 1]),
        margin_sd_engine_mean=float(col("e_sd_margin", sp).mean()), margin_sd_market_mean=float(col("mk_sd_margin", sp).mean()),
        total_mu_diff_mean=float((col("e_mu_total", tl) - col("mk_mu_total", tl)).mean()),
        total_mu_diff_sd=float((col("e_mu_total", tl) - col("mk_mu_total", tl)).std()),
        total_mu_corr=float(np.corrcoef(col("e_mu_total", tl), col("mk_mu_total", tl))[0, 1]),
        total_sd_engine_mean=float(col("e_sd_total", tl).mean()), total_sd_market_mean=float(col("mk_sd_total", tl).mean()),
        market_ml_vs_spread_p_absdiff_mean=float(np.abs(col("mk_p_home", sp) - col("mk_p_home_from_spread", sp)).mean()),
        settled_games=0)
    print(json.dumps(summ, indent=1))
    safe_out(out).write_text(json.dumps(dict(summary=summ, games=res_all, skipped=skipped, cal={k: v for k, v in cal.items()}), indent=1, default=float))
    for r in res:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    print("skipped", skipped)


if __name__ == "__main__":
    main(*sys.argv[1:4])
