"""W112.4 Part C -- score each NHL factor filter per leaf on the 2026-27 Kalshi shadow rows (held out, net after costs per arm).

Run: PYTHONPATH=src python3 12_EXPLORATORY/nhl_factors_w112/score_leaves.py <scratch_dir> <event_store_dir>
scratch_dir holds nhl/ and nhl_settled/ pulled read-only from the box. Leaves come from nhl_engine.filters.nhl_filters over
point-in-time facts (schedule_context + as-of rolling shot quality / deployment, league percentiles at puck drop).
Per (filter, family, leaf): earliest 70% of games pick the arm (best mean net per contract after the exact fee, else NO_BET);
latest 30% score it (game-clustered bootstrap, 90% interval). Shadow rows are paper rows, not fills (GG-527).
Applies when: refreshing per-leaf evidence for the NHL filters as shadow rows accumulate.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import defaultdict

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nhl_engine import factors_w112 as fx  # noqa: E402
from prediction_market_bot.nhl_engine.filters import nhl_filters  # noqa: E402
from prediction_market_bot.quant import retro_route as rr  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM", "POT_OF_GOLD")
ALIAS = {"LA": "LAK", "NJ": "NJD", "TB": "TBL", "SJ": "SJS"}   # Kalshi two-letter codes -> store abbreviations
MONTHS = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


def jl(p):
    with open(p) as fh:
        for l in fh:
            if l.strip():
                yield json.loads(l)


def load_rows(scratch):
    rows = []
    for p in sorted(glob.glob(f"{scratch}/nhl/NHL_*.jsonl")):
        out = {(r["market_ticker"], r["run_id"]): r.get("outcome") for r in jl(f"{scratch}/nhl_settled/{os.path.basename(p)}")}
        for r in jl(p):
            y = out.get((r["market_ticker"], r["run_id"]))
            if y is not None:
                r["y"] = float(y)
                rows.append(r)
    rows = rr.dedupe(rows)
    rr.add_moves(rows)
    return rows


def load_store(store):
    g = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{store}/games_202[56].parquet"))], ignore_index=True)
    ev = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{store}/events_202[56].parquet"))], ignore_index=True)
    sh = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{store}/shifts_202[56].parquet"))], ignore_index=True)
    return g.drop_duplicates("game_id", keep="last"), ev, sh


def game_lookup(g):
    """(date_et, away, home) -> game_id from the store schedule."""
    return {(r.game_date_et, r.away, r.home): int(r.game_id) for r in g.itertuples()}


def row_game(row, look):
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)([A-Z]+)$", row["event_ticker"])
    if not m:
        return None
    d = f"20{m.group(1)}-{MONTHS[m.group(2)]:02d}-{m.group(3)}"
    t = m.group(4)
    for k in range(2, len(t) - 1):
        gid = look.get((d, ALIAS.get(t[:k], t[:k]), ALIAS.get(t[k:], t[k:])))
        if gid:
            return gid
    return None


def percentiles(state, start, col):
    teams = state["team_id"].unique()
    vals = {t: fx.asof(state, int(t), start, (col,)).get(col) for t in teams}
    s = pd.Series({t: v for t, v in vals.items() if v is not None})
    return s.rank(pct=True, method="average").to_dict() if len(s) >= 8 else {}


def build_leaves(g, ev, sh, gids):
    sched = fx.schedule_context(g).set_index(["game_id", "team_id"])
    q = fx.shot_quality_rolling(ev, g)
    d = fx.deployment_rolling(sh, g)
    g = g.set_index("game_id")
    out = {}
    for gid in sorted(gids):
        r = g.loc[gid]
        start = pd.Timestamp(r["start_time_utc"])
        pct = {"hd_for": percentiles(q, start, "hd_for"), "hd_against": percentiles(q, start, "hd_against"),
               "top_share": percentiles(d, start, "top_share")}
        sides = {}
        for side, tid in (("home", r["home_team_id"]), ("away", r["away_team_id"])):
            s = sched.loc[(gid, tid)].to_dict()
            for k in ("hd_for", "hd_against", "top_share"):
                s[k] = pct[k].get(tid)
            sides[side] = s
        out[gid] = nhl_filters(sides["home"], sides["away"])
    return out


def score(rows, leaves_of):
    fit_g, test_g = rr.split_games(rows)
    res, pv = [], {}
    fams = sorted({r["market_type"] for r in rows})
    names = sorted({k for v in leaves_of.values() for k in v})
    for fam in fams:
        sub = [r for r in rows if r["market_type"] == fam and r["_lv"]]
        fam_test = [r for r in sub if rr.game_id(r) in test_g]
        for name in names:
            by = defaultdict(lambda: ([], []))
            for r in sub:
                by[r["_lv"][name]][0 if rr.game_id(r) in fit_g else 1].append(r)
            for leaf, (f, t) in sorted(by.items()):
                fg = len({rr.game_id(r) for r in f})
                rec = {"filter": name, "family": fam, "leaf": leaf, "fit_rows": len(f), "fit_games": fg, "arm": "NO_BET", "thin": False,
                       "test_rows": len(t), "test_games": len({rr.game_id(r) for r in t})}
                nets = lambda r: {**rr.arm_nets(r), **rr.extra_nets(r)}
                if leaf == "unknown" or len(f) < rr.MIN_FIT_ROWS or fg < rr.MIN_FIT_GAMES:
                    rec["thin"] = True
                else:
                    tab = {}
                    for a in ARMS:
                        v = [x for x in (nets(r)[a] for r in f) if x is not None]
                        if len(v) >= rr.MIN_FIT_ROWS:
                            tab[a] = sum(v) / len(v)
                    rec["fit"] = tab
                    best = max(tab.items(), key=lambda kv: kv[1], default=None)
                    if best and best[1] > 0:
                        rec["arm"] = best[0]
                if rec["arm"] != "NO_BET":
                    gm = defaultdict(list)
                    for r in t:
                        x = nets(r)[rec["arm"]]
                        if x is not None:
                            gm[rr.game_id(r)].append(x)
                    if len(gm) >= rr.MIN_TEST_GAMES:
                        m, lo, hi, p = rr.boot_ci(gm)
                        rec.update(test_mean=m, test_lo=lo, test_hi=hi, test_p=p, test_n=sum(map(len, gm.values())), test_n_games=len(gm))
                        pv[(name, fam, leaf)] = p
                        ref = defaultdict(list)
                        for r in fam_test:
                            x = nets(r)[rec["arm"]]
                            if x is not None:
                                ref[rr.game_id(r)].append(x)
                        if len(ref) >= rr.MIN_TEST_GAMES:
                            rm = rr.boot_ci(ref)
                            rec["family_same_arm_mean"], rec["family_same_arm_lo"], rec["family_same_arm_hi"] = rm[0], rm[1], rm[2]
                res.append(rec)
    keep = rr.bh_reject(pv) if pv else set()
    for rec in res:
        rec["bh"] = (rec["filter"], rec["family"], rec["leaf"]) in keep
        rec["draft"] = bool(rec["bh"] and rec.get("test_lo", -1) > 0 and rec.get("test_n_games", 0) >= rr.DRAFT_TEST_GAMES)
    return res, len(fit_g), len(test_g)


def main():
    scratch, store = sys.argv[1], sys.argv[2]
    rows = load_rows(scratch)
    g, ev, sh = load_store(store)
    look = game_lookup(g)
    for r in rows:
        r["_gid"] = row_game(r, look)
    matched = [r for r in rows if r["_gid"]]
    leaves_of = build_leaves(g, ev, sh, {r["_gid"] for r in matched})
    for r in rows:
        r["_lv"] = leaves_of.get(r["_gid"])
    res, nfit, ntest = score(rows, leaves_of)
    cover = {n: sum(1 for v in leaves_of.values() if v[n] != "unknown") for n in next(iter(leaves_of.values()))}
    summ = {"rows": len(rows), "rows_matched_to_store": len(matched), "games_matched": len(leaves_of), "games_with_known_leaf": cover,
            "fit_games": nfit, "test_games": ntest, "leaves": len(res), "thin": sum(r["thin"] for r in res),
            "routed": sum(r["arm"] != "NO_BET" for r in res), "reportable": sum("test_mean" in r for r in res),
            "bh": sum(r["bh"] for r in res), "drafts": sum(r["draft"] for r in res)}
    with open(safe_out(f"{HERE}/leaf_scores.json"), "w") as fh:
        json.dump({"summary": summ, "leaves": res}, fh, indent=1, default=str)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
