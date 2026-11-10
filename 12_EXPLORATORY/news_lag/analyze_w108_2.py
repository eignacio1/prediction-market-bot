"""W108.2: summarize study_results_w108_2.json -> table text.  usage: PYTHONPATH=12_EXPLORATORY analyze_w108_2.py IN_JSON OUT_JSON"""
import collections, json, random, statistics as st, sys
from _fence import safe_out
d = json.load(open(safe_out(sys.argv[1])))
random.seed(7)
GROUPS = {"ALL": lambda k: True, "to_out": lambda k: k == "to_out", "q_to_active": lambda k: k == "q_to_active",
          "worse(out/Q)": lambda k: k in ("to_out", "to_questionable"), "better(active)": lambda k: k in ("q_to_active", "out_to_active")}

def boot(vals_by_game, B=2000):
    """mean with game-clustered bootstrap 95% CI; vals_by_game: {game: [v..]}"""
    gs = list(vals_by_game)
    if not gs: return None
    flat = [v for g in gs for v in vals_by_game[g]]
    m = sum(flat) / len(flat)
    bs = []
    for _ in range(B):
        s = [v for g in random.choices(gs, k=len(gs)) for v in vals_by_game[g]]
        bs.append(sum(s) / len(s))
    bs.sort()
    return {"n_events": len(flat), "n_games": len(gs), "mean": m, "lo": bs[int(.025 * B)], "hi": bs[int(.975 * B) - 1]}

def collect(rows, fn):
    out = collections.defaultdict(list)
    for r in rows:
        v = fn(r)
        if v is not None: out[r["game"]].append(v)
    return out

res = {}
for fam, rows in d["families"].items():
    for tag in ("news", "placebo"):
        for gname, gf in GROUPS.items():
            R = [r for r in rows if r["tag"] == tag and gf(r["kind"])]
            if not R: continue
            cell = {"events": len(R)}
            ab = (lambda x: abs(x)) if fam == "KXNBATOTAL" else (lambda x: x)
            for m in ("1", "2", "5", "10", "30"):
                cell["move_m" + m] = boot(collect(R, lambda r: None if r["path"].get(m) is None else ab(r["path"][m])))
            cell["final"] = boot(collect(R, lambda r: ab(r["final"])))
            big = [r for r in R if abs(r["final"]) >= 0.02]
            cell["n_final_ge_2c"] = len(big)
            for k in ("lag50", "lag100"):
                v = [r[k] for r in big if r.get(k) is not None]
                cell[k + "_median_min"] = st.median(v) if v else None; cell[k + "_n"] = len(v)
            cell["pre_m30_m5"] = boot(collect(R, lambda r: None if not r["pre"] else ab(r["pre"]["m30_m5"])))
            cell["pre_m5_0"] = boot(collect(R, lambda r: None if not r["pre"] else ab(r["pre"]["m5_0"])))
            if fam != "KXNBATOTAL":
                for k in ("1", "2", "5"):
                    cell["net_entry_m" + k] = boot(collect(R, lambda r: None if not r["entry"] or not r["entry"].get(k) else r["entry"][k]["net"]))
                    cell["fill_rate_m" + k] = sum(1 for r in R if r["entry"] and r["entry"].get(k)) / len(R)
                    cell["gross_entry_m" + k] = boot(collect(R, lambda r: None if not r["entry"] or not r["entry"].get(k) else r["entry"][k]["gross"]))
            res[f"{fam}|{tag}|{gname}"] = cell
json.dump(res, open(safe_out(sys.argv[2]), "w"), indent=1)
def f(b): return "n/a" if not b else f"{b['mean']*100:+.2f}c [{b['lo']*100:+.2f},{b['hi']*100:+.2f}] n={b['n_events']}/{b['n_games']}g"
for key, c in res.items():
    if "|ALL" in key or "worse" in key or "better" in key:
        print(key, "events", c["events"]); 
        for m in ("1", "2", "5", "30"): print("   move m" + m, f(c["move_m" + m]))
        print("   final", f(c["final"]), "| lag50", c["lag50_median_min"], c["lag50_n"], "lag100", c["lag100_median_min"], c["lag100_n"], "| pre -30..-5", f(c["pre_m30_m5"]), "pre -5..0", f(c["pre_m5_0"]))
        if "net_entry_m1" in c:
            for k in ("1", "2", "5"): print("   entry m" + k, "net", f(c["net_entry_m" + k]), "gross", f(c["gross_entry_m" + k]), "fill", round(c["fill_rate_m" + k], 2))
