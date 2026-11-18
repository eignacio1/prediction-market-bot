"""W117.2 Parts A3 and C. usage: python3 run_calendar.py <w110.5 scratch_dir> <prior: none|nfl|nhl|both>
The router-v2 power calendar (as 12_EXPLORATORY/evidence_design/run.py) with a long-history prior switch, and at four tree levels:
family (sport, family), band, price bin, leaf. Each level asks: at a true net of +0.02 / +0.05 per contract, when does ONE node at that
level first cross the arm bar (P(net>0) >= 0.90 and the e-process >= 1/alpha, alpha split over the path nodes at that depth)?
Per sport: the earliest such node, and the median over nodes that can earn within 104 weeks. Writes calendar_<prior>.json beside this file."""
import collections, glob, json, os, sys
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__)); ED = os.path.join(os.path.dirname(HERE), "evidence_design")
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from _fence import safe_out
from prediction_market_bot.quant import retro_route as rr
from prediction_market_bot.decision_trees.evidence import calendar as cal, pipeline as P

S, MODE = sys.argv[1], sys.argv[2]
TRANSFER_SD = 0.03


def jl(p):
    for l in open(p):
        if l.strip():
            yield json.loads(l)


def load():
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
                r["y"] = float(y); rows.append(r)
    rows = rr.dedupe(rows); rr.add_moves(rows)
    return rows


def priors():
    pri = {}
    if MODE in ("nfl", "both"):
        pri.update(json.load(open(f"{ED}/prior_nflverse.json"))["bins"])
    if MODE in ("nhl", "both"):
        pri.update(json.load(open(f"{HERE}/prior_nhl_consensus.json"))["bins"])
    return pri


def prior_obs(rows, pri):
    """identical to evidence_design/run.py prior_obs, over the merged prior bins"""
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


rows = load()
obs = [P.Obs(rr.leaf_key(r), rr.game_id(r), P.look_index(r["start_time_utc"]), rr.arm_nets(r)) for r in rows]
cfg = P.Config(prior_obs=prior_obs(rows, priors()))
full = P.run(obs, cfg)
last = max(P.parse_ts(r["start_time_utc"]) for r in rows)
recent = collections.defaultdict(set)
for r in rows:
    k = rr.leaf_key(r)
    if P.parse_ts(r["start_time_utc"]) >= last - timedelta(days=14):
        for d in range(2, len(k) + 1):
            recent[k[:d]].add(rr.game_id(r))
NODE = {a: P.node_clusters(obs, a, 2) for a in cfg.arms}
NULL = {a: P.node_null_sd(obs, a, 2) for a in cfg.arms}


def vgame(cl, node, arm):
    g = NULL[arm].get(node, {})
    return max(cl.var_cr() or 0.0, sum(v * v for v in g.values()) / cl.rows ** 2) * cl.games


def weeks(node, mu):
    """earliest week (None = not within 104) that this node alone clears the bar at a true net of mu"""
    d = len(node)  # depth: sport=1, family=2, band=3, bin=4, leaf=5; path nodes = d-1
    best = max(cfg.arms, key=lambda a: full.fits[a].predict(node).mean)
    cl = NODE[best].get(node)
    if cl is None or cl.games < 2 or not cl.var_cr():
        return None
    post = full.fits[best].predict(node); gpw = len(recent.get(node, ())) / 2.0; vg = vgame(cl, node, best)
    hist = full.log_e[best].get(node, [])
    cw = cal.weeks_to_cross(hist[-1][1] if hist else 0.0, (post.mean, post.var), mu, vg, gpw, alpha=cfg.alpha / (d - 1))
    bw = cal.weeks_to_bar((post.mean, post.var), mu, vg, gpw, cfg.bar)
    return None if cw is None or bw is None else max(cw, bw)


nodes_by_level = {2: set(), 3: set(), 4: set(), 5: set()}
for k in full.leaf_keys():
    for d in nodes_by_level:
        nodes_by_level[d].add(k[:d])
LV = {2: "family", 3: "band", 4: "price_bin", 5: "leaf"}
dt = lambda w: (last + timedelta(weeks=w)).date().isoformat()
out = {"prior": MODE, "as_of": last.date().isoformat(), "rows": len(rows), "nodes": {LV[d]: len(v) for d, v in nodes_by_level.items()}, "by_mu": {}}
for mu in (0.02, 0.05):
    res = {}
    for d, nodes in nodes_by_level.items():
        for sp in ("MLB", "NBA", "NFL", "NHL", "ALL"):
            ws = sorted(w for n in nodes if sp == "ALL" or n[0] == sp for w in [weeks(n, mu)] if w is not None)
            tot = sum(1 for n in nodes if sp == "ALL" or n[0] == sp)
            res.setdefault(sp, {})[LV[d]] = {"nodes": tot, "earn_within_104w": len(ws), "first": dt(ws[0]) if ws else None,
                                             "first_weeks": round(ws[0], 1) if ws else None, "median_of_earners": dt(ws[len(ws) // 2]) if ws else None}
    out["by_mu"][str(mu)] = res
safe_out(os.path.join(HERE, f"calendar_{MODE}.json")).write_text(json.dumps(out, indent=1))
print(MODE, out["rows"], out["nodes"], flush=True)
for mu, res in out["by_mu"].items():
    for sp in ("NFL", "NHL", "NBA", "ALL"):
        print(mu, sp, {l: (v["first"], v["earn_within_104w"]) for l, v in res[sp].items()})
