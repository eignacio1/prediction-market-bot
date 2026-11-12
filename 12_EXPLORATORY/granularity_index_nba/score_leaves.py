"""W111.4 Part C -- score each NBA granularity-index entry per leaf on the 2026-27 Kalshi shadow rows.

Run: PYTHONPATH=src python3 12_EXPLORATORY/granularity_index_nba/score_leaves.py <settled_dir> [--rebuild]
Leaf labels come from each team's PRIOR-season (2025-26, season label 2026, 82 games) league percentile, so they are known
before any 2026-27 tip (2026-27 event data is not in the store, GG-1420). Per (entry, family, leaf): the earliest 70% of games
pick the arm (RIDE / FADE / MODEL_FADE / MOMENTUM, best mean net per contract after the exact fee, else NO_BET); the latest 30%
score it (game-clustered bootstrap, 90% interval, n rows and games). Reference = the same arm over the whole family held-out.
Shadow rows are paper rows, not fills (GG-527). A leaf routed to NO_BET is APPLIED and reported as routed.
Applies when: refreshing per-leaf evidence for the index entries as shadow rows accumulate.
"""
from __future__ import annotations

import glob
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import filters as nf
from prediction_market_bot.nfl_engine import granularity_index as gi
from prediction_market_bot.nba_engine import situation_splits as ss
from prediction_market_bot.quant import retro_route as rr

HERE = Path(__file__).parent
FAMILY_OF = {"KXNBATOTAL": "GAME_TOTAL", "KXNBATEAMTOTAL": "TEAM_TOTAL", "KXNBASPREAD": "SPREAD", "KXNBAGAME": "MONEYLINE"}
ARMS = ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM")


def _bi():
    spec = importlib.util.spec_from_file_location("build_index", HERE / "build_index.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def team_percentiles(season: int = 2026) -> dict:
    """{team_abbr: {entry: raw-value league percentile}} at the end of ``season`` (prior season for the next one)."""
    bi = _bi()
    bi.YEARS = [season - 1, season]
    games = bi.load_games()
    sched = bi.rd("schedule", season)
    abbr = {}
    for side in ("home", "away"):
        abbr.update(dict(zip(sched[f"{side}_team_id"], sched[f"{side}_team_abbreviation"])))
    frames = {"poss": bi.load_possession_frame(games), "shot": bi.load_shot_frame(games)}
    out: dict = defaultdict(dict)
    for sit, kind in [(s, "poss") for s in bi.SITUATIONS] + [(s, "shot") for s in bi.ZONE]:
        if sit.name not in nf.HIGHER_IS_BETTER:
            continue
        fr, spec = frames[kind], ss.spec_for(sit)
        plays = ss.plays_for(fr, sit)
        t = gi.split(plays, spec, season=season, games=82)
        t = t[t.n >= sit.min_n]
        pct = t.value.rank(pct=True, method="average")
        for u, p in zip(t.unit, pct):
            out[abbr.get(u, str(u))][sit.name] = float(p)
    return dict(out)


def load_rows(settled: str) -> list:
    rows = []
    for p in sorted(glob.glob(f"{settled}/NBA_*.jsonl")):
        with open(p) as fh:
            rows += [json.loads(l) for l in fh if l.strip()]
    rows = rr.dedupe(rows)
    rr.add_moves(rows)
    return rows


def leaves_for(row: dict, prof: dict, entry: str) -> str:
    away, home = row["game_key"].split(":")[1].split("@")
    fam = row["market_type"].removeprefix("NBA_")
    h, a = prof.get(home, {}).get(entry), prof.get(away, {}).get(entry)
    return nf.total_leaf(h, a) if fam in nf.TOTAL_FAMILIES else nf.side_leaf(entry, h, a)


def score(rows: list, prof: dict, entries: dict) -> list:
    fit_g, test_g = rr.split_games(rows)
    res = []
    pv = {}
    for entry, fams in entries.items():
        for fam in fams:
            sub = [r for r in rows if r["market_type"].endswith(fam)]
            by = defaultdict(lambda: ([], []))
            for r in sub:
                by[leaves_for(r, prof, entry)][0 if rr.game_id(r) in fit_g else 1].append(r)
            fam_test = [r for r in sub if rr.game_id(r) in test_g]
            for leaf, (f, t) in sorted(by.items()):
                fg = len({rr.game_id(r) for r in f})
                rec = {"entry": entry, "family": fam, "leaf": leaf, "fit_rows": len(f), "fit_games": fg, "arm": "NO_BET",
                       "thin": False, "test_rows": len(t), "test_games": len({rr.game_id(r) for r in t})}
                if leaf == "unknown" or len(f) < rr.MIN_FIT_ROWS or fg < rr.MIN_FIT_GAMES:
                    rec["thin"] = True
                else:
                    tab = {}
                    for a in ARMS:
                        v = [x for x in (rr.arm_nets(r)[a] for r in f) if x is not None]
                        if len(v) >= rr.MIN_FIT_ROWS:
                            tab[a] = sum(v) / len(v)
                    rec["fit"] = tab
                    best = max(tab.items(), key=lambda kv: kv[1], default=None)
                    if best and best[1] > 0:
                        rec["arm"] = best[0]
                if rec["arm"] != "NO_BET":
                    g = defaultdict(list)
                    for r in t:
                        x = rr.arm_nets(r)[rec["arm"]]
                        if x is not None:
                            g[rr.game_id(r)].append(x)
                    if len(g) >= rr.MIN_TEST_GAMES:
                        m, lo, hi, p = rr.boot_ci(g)
                        rec.update(test_mean=m, test_lo=lo, test_hi=hi, test_p=p, test_n=sum(map(len, g.values())), test_n_games=len(g))
                        pv[(entry, fam, leaf)] = p
                        ref = defaultdict(list)
                        for r in fam_test:
                            x = rr.arm_nets(r)[rec["arm"]]
                            if x is not None:
                                ref[rr.game_id(r)].append(x)
                        if len(ref) >= rr.MIN_TEST_GAMES:
                            rm = rr.boot_ci(ref)
                            rec["family_same_arm_mean"], rec["family_same_arm_lo"], rec["family_same_arm_hi"] = rm[0], rm[1], rm[2]
                res.append(rec)
    keep = rr.bh_reject(pv) if pv else set()
    for rec in res:
        rec["bh"] = (rec["entry"], rec["family"], rec["leaf"]) in keep
        rec["draft"] = bool(rec["bh"] and rec.get("test_lo", -1) > 0 and rec.get("test_n_games", 0) >= rr.DRAFT_TEST_GAMES)
    return res


def entries_by_family() -> dict:
    out = {}
    for p in sorted((HERE / "entries").glob("*.json")):
        e = json.loads(p.read_text())
        if e["name"] not in nf.HIGHER_IS_BETTER:
            continue
        fams = sorted({FAMILY_OF[m["family"]] for m in e["markets"] if m["family"] in FAMILY_OF})
        out[e["name"]] = fams
    return out


def main():
    settled = sys.argv[1]
    cache = HERE / "team_percentiles.json"
    if "--rebuild" in sys.argv or not cache.exists():
        safe_out(cache).write_text(json.dumps(team_percentiles(), indent=1))
    prof = json.loads(cache.read_text())
    rows = load_rows(settled)
    entries = entries_by_family()
    res = score(rows, prof, entries)
    fit_g, test_g = rr.split_games(rows)
    summ = {"rows": len(rows), "fit_games": len(fit_g), "test_games": len(test_g), "entries_scored": sum(1 for v in entries.values() if v),
            "entries_props_only": [k for k, v in entries.items() if not v], "leaves": len(res), "thin": sum(r["thin"] for r in res),
            "routed": sum(r["arm"] != "NO_BET" for r in res), "reportable": sum("test_mean" in r for r in res),
            "bh": sum(r["bh"] for r in res), "drafts": sum(r["draft"] for r in res)}
    safe_out(HERE / "leaf_scores.json").write_text(json.dumps({"summary": summ, "leaves": res}, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
