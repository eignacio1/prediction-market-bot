"""W113.2 Part C -- score each NFL granularity-index entry per leaf on the 2026 NFL Kalshi shadow rows.

Run: python3 -E score_leaves.py <settled_dir>   (PYTHONPATH=src; cwd neutral)
Leaf labels come from each team's PRIOR-season (2025, 17 games) league percentile (team_percentiles.json), known before any
2026 kickoff. Per (entry, family, leaf): the earliest 70% of games pick the arm (RIDE / FADE / MODEL_FADE / MOMENTUM, best mean
net per contract after the exact taker fee, else NO_BET); the latest 30% score it (game-clustered bootstrap, 90% interval, n rows
and games). POT_OF_GOLD / MOMENTUM_OPEN are scored on every applicable held-out row of the leaf, reported not routed (as 111.3).
Reference = the same arm over the whole family held-out. Shadow rows are paper rows, not fills (GG-527). A leaf routed to NO_BET
is APPLIED and reported as routed. Writes stay inside 12_EXPLORATORY (safe_out).
"""
from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nfl_engine import filters as nf  # noqa: E402
from prediction_market_bot.quant import retro_route as rr  # noqa: E402

FAMILY_OF = {"KXNFLTOTAL": ("GAME_TOTAL",), "KXNFLTEAMTOTAL": ("TEAM_TOTAL",), "KXNFLSPREAD": ("SPREAD", "MONEYLINE")}
TOTAL_FAMILIES = ("GAME_TOTAL", "TEAM_TOTAL")
ARMS = ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM")


def profiles() -> dict:
    t = json.loads((HERE / "team_percentiles.json").read_text())["entries"]
    out: dict = defaultdict(dict)
    for name, teams in t.items():
        for team, v in teams.items():
            out[team][name] = v["pct"]
    return dict(out)


def load_rows(settled: str) -> list:
    rows = []
    for p in sorted(glob.glob(f"{settled}/NFL_*.jsonl")):
        with open(p) as fh:
            rows += [json.loads(l) for l in fh if l.strip()]
    for r in rows:
        r.setdefault("sport", "NFL")
    rows = rr.dedupe(rows)
    rr.add_moves(rows)
    return rows


def fam(r) -> str:
    return r["market_type"].removeprefix("NFL_")


def leaf_of(row: dict, prof: dict, entry: str) -> str:
    away, home = row["game_key"].split(":")[1].split("@")
    h, a = prof.get(home, {}).get(entry), prof.get(away, {}).get(entry)
    return nf.split_total_leaf(h, a) if fam(row) in TOTAL_FAMILIES else nf.split_side_leaf(entry, h, a)


def ci(rows, arm):
    g = defaultdict(list)
    for r in rows:
        x = (rr.arm_nets(r) | rr.extra_nets(r))[arm]
        if x is not None:
            g[rr.game_id(r)].append(x)
    if len(g) < rr.MIN_TEST_GAMES:
        return None
    m, lo, hi, p = rr.boot_ci(g)
    return {"mean": m, "lo": lo, "hi": hi, "p": p, "n": sum(map(len, g.values())), "games": len(g)}


def score(rows, prof, entries):
    fit_g, test_g = rr.split_games(rows)
    res, pv = [], {}
    for entry, fams in entries.items():
        for f in fams:
            sub = [r for r in rows if fam(r) == f]
            by = defaultdict(lambda: ([], []))
            for r in sub:
                by[leaf_of(r, prof, entry)][0 if rr.game_id(r) in fit_g else 1].append(r)
            fam_test = [r for r in sub if rr.game_id(r) in test_g]
            for leaf, (fit, test) in sorted(by.items()):
                fg = len({rr.game_id(r) for r in fit})
                rec = {"entry": entry, "family": f, "leaf": leaf, "fit_rows": len(fit), "fit_games": fg, "arm": "NO_BET",
                       "thin": False, "test_rows": len(test), "test_games": len({rr.game_id(r) for r in test})}
                if leaf == "unknown" or len(fit) < rr.MIN_FIT_ROWS or fg < rr.MIN_FIT_GAMES:
                    rec["thin"] = True
                else:
                    tab = {}
                    for a in ARMS:
                        v = [x for x in (rr.arm_nets(r)[a] for r in fit) if x is not None]
                        if len(v) >= rr.MIN_FIT_ROWS:
                            tab[a] = sum(v) / len(v)
                    rec["fit"] = tab
                    best = max(tab.items(), key=lambda kv: kv[1], default=None)
                    if best and best[1] > 0:
                        rec["arm"] = best[0]
                if rec["arm"] != "NO_BET":
                    c = ci(test, rec["arm"])
                    if c:
                        rec.update(test_mean=c["mean"], test_lo=c["lo"], test_hi=c["hi"], test_p=c["p"], test_n=c["n"],
                                   test_n_games=c["games"])
                        pv[(entry, f, leaf)] = c["p"]
                        ref = ci(fam_test, rec["arm"])
                        if ref:
                            rec["family_same_arm_mean"], rec["family_same_arm_lo"], rec["family_same_arm_hi"] = ref["mean"], ref["lo"], ref["hi"]
                extras = {}
                for a in rr.EXTRA_ARMS + ("RIDE",):
                    c = ci(test, a)
                    if c:
                        extras[a] = {k: c[k] for k in ("mean", "lo", "hi", "n", "games")}
                if extras:
                    rec["held_out_all_applicable"] = extras
                res.append(rec)
    keep = rr.bh_reject(pv) if pv else set()
    for rec in res:
        rec["bh"] = (rec["entry"], rec["family"], rec["leaf"]) in keep
        rec["draft"] = bool(rec["bh"] and rec.get("test_lo", -1) > 0 and rec.get("test_n_games", 0) >= rr.DRAFT_TEST_GAMES)
    return res


def entries_by_family():
    out = {}
    for p in sorted((HERE / "entries").glob("*.json")):
        e = json.loads(p.read_text())
        if e["name"] not in nf.HIGHER_IS_BETTER:
            continue
        out[e["name"]] = sorted({x for m in e["markets"] for x in FAMILY_OF.get(m["family"], ())})
    return out


def main():
    prof, rows, entries = profiles(), load_rows(sys.argv[1]), entries_by_family()
    res = score(rows, prof, entries)
    fit_g, test_g = rr.split_games(rows)
    # moneyline RIDE family lead (W110.5): is it inside any split leaf?
    ml = [r for r in rows if fam(r) == "MONEYLINE" and rr.game_id(r) in test_g]
    ml_ride = ci(ml, "RIDE")
    per_entry = defaultdict(lambda: {"scored_leaves": 0, "routed": 0, "bh": 0, "draft": 0})
    for r in res:
        e = per_entry[r["entry"]]
        e["scored_leaves"] += "test_mean" in r
        e["routed"] += r["arm"] != "NO_BET"
        e["bh"] += r["bh"]
        e["draft"] += r["draft"]
    summ = {"rows": len(rows), "fit_games": len(fit_g), "test_games": len(test_g), "entries": len(entries),
            "leaves": len(res), "thin": sum(r["thin"] for r in res), "routed": sum(r["arm"] != "NO_BET" for r in res),
            "reportable": sum("test_mean" in r for r in res), "bh": sum(r["bh"] for r in res), "drafts": sum(r["draft"] for r in res),
            "moneyline_ride_heldout_family": ml_ride, "per_entry": dict(per_entry)}
    safe_out(HERE / "leaf_scores.json").write_text(json.dumps({"summary": summ, "leaves": res}, indent=1))
    print(json.dumps({k: v for k, v in summ.items() if k != "per_entry"}, indent=1))
    for k, v in sorted(per_entry.items()):
        print(f"{k:42s} {v}")


if __name__ == "__main__":
    main()
