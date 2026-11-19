"""W119.1 Part C. usage: run.py <scratch_dir>   (scratch_dir/nhl/ and nhl_settled/ pulled read-only from the box)
NHL leaves through router v2 (pooled posterior + sequential e-process) with the W117.2 NHL consensus prior (transfer sd 0.03, as for
nflverse). Writes results.json and nhl_v2.json beside this file (EXPLORATORY fence); the map is then copied to src/.../decision_trees/leaf_maps/nhl_v2.json by hand = leaf_map_v2.json with its NHL leaves
replaced by these (every other sport unchanged). Selected only by PM_LEAF_MAP_VERSION=nhl_v2; the default stays v1."""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
ROOT = os.path.dirname(EXP)
sys.path.insert(0, EXP); sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.join(EXP, "nhl_consensus"))
from _fence import safe_out
from prediction_market_bot.quant import retro_route as rr
from prediction_market_bot.decision_trees.evidence import pipeline as P

S = sys.argv[1]
TRANSFER_SD = 0.03
LEAF_MAPS = os.path.join(ROOT, "src", "prediction_market_bot", "decision_trees", "leaf_maps")


def load():
    sys.argv = [sys.argv[0], S, "nhl"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("sl", os.path.join(EXP, "nhl_factors_w112", "score_leaves.py"))
    sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)
    return sl.load_rows(S)


def prior_obs(rows, pri):
    cost = collections.defaultdict(lambda: {"RIDE": [], "FADE": []})
    for r in rows:
        k = rr.leaf_key(r)[:4]
        if f"{k[1]}|{k[3]}" not in pri:
            continue
        fs = rr.fav_side(r); fp = rr.fav_price(r); y = float(r["y"]); yf = y if fs == "YES" else 1 - y
        cost[k]["RIDE"].append((yf - fp) - rr.side_net(r, fs))
        cost[k]["FADE"].append(((1 - yf) - (1 - fp)) - rr.side_net(r, "NO" if fs == "YES" else "YES"))
    nb = collections.Counter((k[1], k[3]) for k in cost)
    out = {"RIDE": {}, "FADE": {}}
    for k, c in cost.items():
        b = pri[f"{k[1]}|{k[3]}"]
        v = (b["se"] ** 2 + TRANSFER_SD ** 2) * nb[(k[1], k[3])]
        out["RIDE"][k] = (b["gap"] - sum(c["RIDE"]) / len(c["RIDE"]), v)
        out["FADE"][k] = (-b["gap"] - sum(c["FADE"]) / len(c["FADE"]), v)
    return out


rows = [r for r in load() if str(r["sport"]).upper() == "NHL"]
pri = json.load(open(os.path.join(EXP, "nhl_consensus", "prior_nhl_consensus.json")))["bins"]
obs = lambda rs: [P.Obs(rr.leaf_key(r), rr.game_id(r), P.look_index(r["start_time_utc"]), rr.arm_nets(r)) for r in rs]
cell = lambda r: f'{r["market_type"]}|{r["band"]}'

# held-out check: router fit on the earliest 70% of games, scored on the latest 30% (game-clustered, 90% interval)
fit_g, test_g = rr.split_games(rows)
fit = [r for r in rows if rr.game_id(r) in fit_g]; test = [r for r in rows if rr.game_id(r) in test_g]
def heldout(cfg):
    res = P.run(obs(fit), cfg); keys = set(res.leaf_keys())
    arm_of = lambda r: res.route(rr.leaf_key(r))["arm"] if rr.leaf_key(r) in keys else "NO_BET"
    by, bet = collections.defaultdict(list), collections.defaultdict(list)
    for r in test:
        a = arm_of(r); x = rr.arm_nets(r).get(a) if a != "NO_BET" else None
        by[rr.game_id(r)].append(x or 0.0)
        if x is not None: bet[rr.game_id(r)].append(x)
    st = lambda d: dict(zip(("net", "lo90", "hi90"), [round(v, 5) for v in rr.boot_ci(d)[:3]]), games=len(d)) if d else None
    return {"armed_leaves": sum(res.route(k)["arm"] != "NO_BET" for k in keys), "leaves": len(keys), "per_row": st(by), "per_bet": st(bet)}
held = {"no_prior": heldout(P.Config()), "consensus_prior": heldout(P.Config(prior_obs=prior_obs(fit, pri)))}

# full corpus with the consensus prior = the map
full = P.run(obs(rows), P.Config(prior_obs=prior_obs(rows, pri)))
newleaves, per_cell = {}, collections.defaultdict(collections.Counter)
cell_games = {c: len({rr.game_id(r) for r in rows if cell(r) == c}) for c in {cell(r) for r in rows}}
for k in sorted(full.leaf_keys(), key=str):
    rt = dict(full.route(k)); rt["seen"] = True
    newleaves["|".join(str(x) for x in k)] = rt
    per_cell[f"{k[1]}|{k[2]}"][rt["arm"]] += 1
cells = {}
for c, arms in sorted(per_cell.items()):
    earned = {a: n for a, n in arms.items() if a != "NO_BET"}
    cells[c] = {"leaves": sum(arms.values()), "arms": dict(arms), "games": cell_games.get(c, 0),
                "routing": "arms:" + ",".join(f"{a}={n}" for a, n in sorted(earned.items())) if earned else "NO_BET in every leaf",
                "note": None if earned else f"routed to no bet in these leaves (EXP-W119.1-NHL-V2-{c.replace('|','-')}); logs continue"}
out = {"corpus": {"rows": len(rows), "games": len({rr.game_id(r) for r in rows}), "fit_games": len(fit_g), "test_games": len(test_g),
                  "range": [min(r["start_time_utc"] for r in rows), max(r["start_time_utc"] for r in rows)]},
       "heldout": held, "full": {"leaves": len(newleaves), "armed": sum(v["arm"] != "NO_BET" for v in newleaves.values()), "cells": cells}}
json.dump(out, open(safe_out(f"{HERE}/results.json"), "w"), indent=1, default=str)

base = json.load(open(os.path.join(LEAF_MAPS, "leaf_map_v2.json")))
base["version"] = "nhl_v2"
base["arm_source"] = "router_v2_pooled_sequential_nhl_consensus_prior_w119_1"
base["source"] = "12_EXPLORATORY/nhl_router_v2/run.py on the NHL 2026-27 shadow rows, W117.2 consensus prior; other sports = leaf_map_v2.json"
base["leaves"] = {**{k: v for k, v in base["leaves"].items() if not k.startswith("NHL|")}, **newleaves,
                  **{k: v for k, v in base["leaves"].items() if k.startswith("NHL|") and k not in newleaves}}
base["nhl_cells"] = cells
safe_out(f"{HERE}/nhl_v2.json").write_text(json.dumps(base, indent=1, sort_keys=True, default=str))
print(json.dumps(out, indent=1, default=str))
