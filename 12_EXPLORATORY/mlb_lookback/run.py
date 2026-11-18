"""W118.1 runner. usage: run.py <scratch_dir>   (scratch_dir/settled/MLB_*.jsonl pulled read-only from the box)
Spec: SPEC.md (frozen before results). Writes results.json beside this file and
src/.../decision_trees/leaf_maps/mlb_2026_lookback.json (not wired: PM_LEAF_MAP_VERSION unchanged)."""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _fence import safe_out
from prediction_market_bot.quant import retro_route as rr
from prediction_market_bot.decision_trees.evidence import model as M, pipeline as P

S = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
FRAC = 2 / 3
ARMS = ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM")

rows = []
for p in sorted(glob.glob(f"{S}/settled/MLB_*.jsonl")):
    rows += [json.loads(l) for l in open(p) if l.strip()]
raw = len(rows)
rows = rr.dedupe(rows); rr.add_moves(rows)
fit_g, test_g = rr.split_games(rows, FRAC)
fit = [r for r in rows if rr.game_id(r) in fit_g]; test = [r for r in rows if rr.game_id(r) in test_g]
cell = lambda r: f'{r["market_type"]}|{r["band"]}'
obs = lambda rs: [P.Obs(rr.leaf_key(r), rr.game_id(r), P.look_index(r["start_time_utc"]), rr.arm_nets(r)) for r in rs]

# routers fit on the fit window only
v1 = {tuple(l["leaf"]): l["arm"] for l in rr.route_fit(fit)} if hasattr(rr, "route_fit") else None
if v1 is None:  # route() splits internally at 70%; rebuild its fit rule on our fit window
    byk = collections.defaultdict(list)
    for r in fit: byk[rr.leaf_key(r)].append(r)
    v1 = {}
    for k, f in byk.items():
        arm = "NO_BET"
        if len(f) >= rr.MIN_FIT_ROWS and len({rr.game_id(r) for r in f}) >= rr.MIN_FIT_GAMES:
            m = {a: [x for x in (rr.arm_nets(r)[a] for r in f) if x is not None] for a in rr.ARMS}
            b = max(((sum(v) / len(v), a) for a, v in m.items() if len(v) >= rr.MIN_FIT_ROWS), default=None)
            if b and b[0] > 0: arm = b[1]
        v1[k] = arm
res = P.run(obs(fit), P.Config())
v2 = {k: res.route(k)["arm"] for k in res.leaf_keys()}
routers = {"v2_pooled": lambda r: res.route(rr.leaf_key(r))["arm"] if rr.leaf_key(r) in set(res.leaf_keys()) else "NO_BET",
           "v1_per_leaf": lambda r: v1.get(rr.leaf_key(r), "NO_BET"),
           "ride_every_favourite": lambda r: "RIDE"}
for a in ("FADE", "MOMENTUM"):
    routers[f"always_{a}"] = (lambda a: lambda r: a)(a)


def stats(by):
    if not by: return None
    m, lo, hi, _ = rr.boot_ci(by)
    return {"net": round(m, 5), "lo90": round(lo, 5), "hi90": round(hi, 5), "rows": sum(len(v) for v in by.values()), "games": len(by)}


def per_row(rs, arm_of):
    """net per row (no position = 0) and per bet, game-clustered."""
    row, bet = collections.defaultdict(list), collections.defaultdict(list)
    for r in rs:
        a = arm_of(r); x = rr.arm_nets(r).get(a) if a != "NO_BET" else None
        row[rr.game_id(r)].append(x or 0.0)
        if x is not None: bet[rr.game_id(r)].append(x)
    return {"per_row": stats(row), "per_bet": stats(bet)}

heldout = {n: {"ALL": per_row(test, f), **{c: per_row([r for r in test if cell(r) == c], f) for c in sorted({cell(r) for r in rows})}}
           for n, f in routers.items()}
# unrouted held-out net per arm per cell (every row the arm has a position on)
arm_cells = {}
for c in sorted({cell(r) for r in rows}):
    arm_cells[c] = {}
    for a in ARMS:
        by = collections.defaultdict(list)
        for r in test:
            if cell(r) == c:
                x = rr.arm_nets(r)[a]
                if x is not None: by[rr.game_id(r)].append(x)
        arm_cells[c][a] = stats(by)
# the same on the whole season (fit + test), descriptive only
arm_cells_all = {}
for c in sorted({cell(r) for r in rows}):
    arm_cells_all[c] = {}
    for a in ARMS:
        by = collections.defaultdict(list)
        for r in rows:
            if cell(r) == c:
                x = rr.arm_nets(r)[a]
                if x is not None: by[rr.game_id(r)].append(x)
        arm_cells_all[c][a] = stats(by)

# full-corpus v2 map (the frozen look-back map) and per-cell routing
full = P.run(obs(rows), P.Config())
fam = collections.defaultdict(lambda: collections.Counter())
leaves = {}
for k in sorted(full.leaf_keys(), key=str):
    rt = full.route(k); leaves["|".join(str(x) for x in k)] = rt
    fam[f"{k[1]}|{k[2]}"][rt["arm"]] += 1
fullcells = {}
for c in sorted({cell(r) for r in rows}):
    arms = dict(fam.get(c, {}))
    earned = {a: n for a, n in arms.items() if a != "NO_BET"}
    fullcells[c] = {"leaves": sum(arms.values()), "arms": arms, "games": len({rr.game_id(r) for r in rows if cell(r) == c}),
                    "routing": max(earned, key=earned.get) if earned else "NO_BET",
                    "note": None if earned else f"hypothesis closed (EXP-W118.1-MLB-{'-'.join(c.split('|'))}, parked for R&D); logs continue in 2027"}
rows_per_cell = collections.Counter(cell(r) for r in rows); games_per_cell = {c: len({rr.game_id(r) for r in rows if cell(r) == c}) for c in rows_per_cell}
out = {"corpus": {"raw_rows": raw, "deduped_rows": len(rows), "games": len({rr.game_id(r) for r in rows}),
                  "range": [min(r["start_time_utc"] for r in rows), max(r["start_time_utc"] for r in rows)],
                  "split": f"earliest {FRAC:.3f} of games fit / rest held out", "fit_games": len(fit_g), "test_games": len(test_g),
                  "fit_rows": len(fit), "test_rows": len(test), "rows_per_cell": dict(sorted(rows_per_cell.items())), "games_per_cell": dict(sorted(games_per_cell.items()))},
       "fit_window_leaves": {"v2_leaves": len(v2), "v2_armed": sum(a != "NO_BET" for a in v2.values()), "v1_leaves": len(v1), "v1_armed": sum(a != "NO_BET" for a in v1.values()),
                             "v1_arms": dict(collections.Counter(v1.values()))},
       "heldout_routers": heldout, "heldout_unrouted_arm_by_cell": arm_cells, "all_games_unrouted_arm_by_cell_descriptive": arm_cells_all,
       "full_corpus_v2": {"leaves": len(leaves), "armed": sum(v["arm"] != "NO_BET" for v in leaves.values()), "cells": fullcells}}
json.dump(out, open(safe_out(f"{HERE}/results.json"), "w"), indent=1)
doc = {"version": "mlb_2026_lookback", "arm_source": "router_v2_pooled_sequential_w118_1", "key": "sport|market_type|band|favprice_bin|move_bin",
       "source": "12_EXPLORATORY/mlb_lookback/run.py on MLB 2026 postseason shadow rows (22 settled games, 2026-10-05..10-29)",
       "status": "FROZEN for 2027; not wired (PM_LEAF_MAP_VERSION default and v2 unchanged); sees 22 games only",
       "rule": "arm iff pooled P(net>0) >= bar AND path-averaged e-process >= 1/alpha; else NO_BET", "cells": fullcells, "leaves": leaves}
safe_out(f"{HERE}/mlb_2026_lookback.json").write_text(json.dumps(doc, indent=1, sort_keys=True, default=str))
print(json.dumps(out, indent=1, default=str))

# ---- Part C: MLB layers 1-5 in the d6_read shape (coverage.d6_layers), and the 2027 power calendar ----
from prediction_market_bot.decision_trees import coverage as cov
from prediction_market_bot.decision_trees.evidence import calendar as cal
import statistics
held_games = {c: out["heldout_unrouted_arm_by_cell"][c]["RIDE"]["games"] for c in out["heldout_unrouted_arm_by_cell"]}
lm_doc = {"leaves": {f"mlb|{c.split('|')[0]}|{c.split('|')[1]}|x": {"fit": {"MODEL_FADE": 1}, "thin": True, "arm": "NO_BET",
                                                                           "test": {"test_n_games": held_games[c]}} for c in held_games}}
cells = [r for r in cov.cell_rows() if str(r["sport"]).lower() == "mlb"
         and (r["market_type"].upper(), r["band"]) in {tuple(c.split("|")) for c in held_games}]
d6 = cov.d6_layers(leaf_map_doc=lm_doc, rows=cells, splits_doc={"splits": []}, filter_sports=set())
GPW = 90.0  # assumption, stated in PREREG: ~15 MLB games/day logged x 6 days
cal_out = {}
for c in sorted(held_games):
    byg = collections.defaultdict(list)
    for r in rows:
        if cell(r) == c:
            x = rr.arm_nets(r)["RIDE"]
            if x is not None: byg[rr.game_id(r)].append(x)
    gm = [sum(v) / len(v) for v in byg.values()]
    var = statistics.pvariance(gm)
    cal_out[c] = {"var_game": round(var, 5), "games_per_week_assumed": GPW,
                  "weeks_to_first_arm_if_mu": {str(mu): cal.weeks_to_bh(0, 1, mu, var, GPW, m_tests=len(held_games)) for mu in (0.02, 0.04, 0.06)}}
out["d6_mlb_lookback"] = {"layer_names": list(cov.LAYER_NAMES), "cells": d6, "summary": cov.d6_summary(d6), "layers_1_to_5_present_per_cell": {
    f'{x["market_type"]}|{x["band"]}': x["layers"][:5] for x in d6}, "note": "cells not in this ledger (player hits, T4M, NBA-style props) are out of scope: 18 registered MLB game cells vs 12 pulled"}
out["power_calendar_2027"] = cal_out
json.dump(out, open(safe_out(f"{HERE}/results.json"), "w"), indent=1, default=str)
print("D6", json.dumps(out["d6_mlb_lookback"]["summary"], default=str)); print(json.dumps(out["d6_mlb_lookback"]["layers_1_to_5_present_per_cell"]))
print(json.dumps(cal_out))
