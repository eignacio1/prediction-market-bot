"""W110.5 runner. usage: run.py <scratch_dir> -> writes results.json + inventory.json beside this file.
scratch_dir holds shadow/ (+settled/ via ../settled), nhl/ and nhl_settled/ pulled read-only from the box."""
import json, sys, glob, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _fence import safe_out
from prediction_market_bot.quant import retro_route as rr

S = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))


def jl(p):
    with open(p) as fh:
        for l in fh:
            if l.strip():
                yield json.loads(l)


rows = []
for p in sorted(glob.glob(f"{S}/settled/*.jsonl")):
    rows += list(jl(p))
for p in sorted(glob.glob(f"{S}/nhl/NHL_*.jsonl")):
    out = {}
    for q in glob.glob(f"{S}/nhl_settled/{os.path.basename(p)}"):
        for r in jl(q):
            out[(r["market_ticker"], r["run_id"])] = r.get("outcome")
    for r in jl(p):
        y = out.get((r["market_ticker"], r["run_id"]))
        if y is not None:
            r["y"] = float(y)
            rows.append(r)
n_raw = len(rows)
rows = rr.dedupe(rows)
rr.add_moves(rows)
inv = collections.defaultdict(lambda: {"rows": 0, "games": set(), "first": "9", "last": ""})
for r in rows:
    k = f'{r["sport"]}|{r["market_type"]}'
    d = inv[k]; d["rows"] += 1; d["games"].add(rr.game_id(r))
    d["first"] = min(d["first"], r["start_time_utc"][:10]); d["last"] = max(d["last"], r["start_time_utc"][:10])
inventory = {k: {"rows": v["rows"], "games": len(v["games"]), "first": v["first"], "last": v["last"]} for k, v in sorted(inv.items())}
json.dump({"raw_scored_rows": n_raw, "deduped_rows": len(rows), "inventory": inventory}, open(safe_out(f"{HERE}/inventory.json"), "w"), indent=1)

res = rr.route(rows)
fit_g, test_g = rr.split_games(rows)
ref = rr.whole_arm_table(rows, test_g)
refout = {}
for fam, arms in ref.items():
    refout["|".join(fam)] = {a: dict(zip(("mean", "lo", "hi", "p"), rr.boot_ci(by))) | {"n": sum(len(v) for v in by.values()), "games": len(by)}
                             for a, by in arms.items() if len(by) >= rr.MIN_TEST_GAMES}
xf = rr.extra_family_table(rows, test_g)
extra_fam = {"|".join(f): {a: dict(zip(("mean", "lo", "hi", "p"), rr.boot_ci(by))) | {"n": sum(len(v) for v in by.values()), "games": len(by)}
                          for a, by in arms.items() if len(by) >= rr.MIN_TEST_GAMES} for f, arms in xf.items()}
xl = rr.extra_leaf_table(rows, test_g)
extra_leaves = [{"leaf": list(k), **{"arms": v}} for k, v in sorted(xl.items())]
json.dump({"extra_arms": {"family": extra_fam, "leaves": extra_leaves}}, open(safe_out(f"{HERE}/results_extra.json"), "w"), indent=1)
json.dump({"route": res, "reference_heldout_all_rows": refout}, open(safe_out(f"{HERE}/results.json"), "w"), indent=1, default=list)
L = res["leaves"]
print("rows", len(rows), "fit_games", res["fit_games"], "test_games", res["test_games"])
print("leaves", len(L), "thin", sum(l["thin"] for l in L), "routed", sum(l["arm"] != "NO_BET" for l in L),
      "reportable", sum("test_mean" in l for l in L), "BH", sum(l["bh"] for l in L), "drafts", sum(l["draft"] for l in L))
