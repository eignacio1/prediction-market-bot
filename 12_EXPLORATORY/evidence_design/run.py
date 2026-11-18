"""W115.1 (B-094) runner. usage: run.py <scratch_dir> [--write-map]
scratch_dir = the W110.5 settled corpus snapshot (settled/, nhl/, nhl_settled/), pulled read-only from the box.
Writes results.json beside this file; with --write-map also decision_trees/leaf_maps/leaf_map_v2.json.
Three routers on the W110.5 split (earliest 70% of games fit, latest 30% held out): per-leaf (today's v1 map rule),
pooled + sequential (v2), ride every favourite. Then the v2 map on the full corpus and the power calendar."""
import collections, glob, json, math, os, sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _fence import safe_out
from prediction_market_bot.quant import retro_route as rr
from prediction_market_bot.decision_trees.evidence import calendar as cal, model as M, pipeline as P

S = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
TRANSFER_SD = 0.03  # stated allowance for the gap between a sportsbook close and the Kalshi mid; widens the prior


def jl(p):
    with open(p) as fh:
        for l in fh:
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
                r["y"] = float(y)
                rows.append(r)
    rows = rr.dedupe(rows)
    rr.add_moves(rows)
    return rows


def obs_of(rows):
    return [P.Obs(rr.leaf_key(r), rr.game_id(r), P.look_index(r["start_time_utc"]), rr.arm_nets(r)) for r in rows]


def prior_obs(rows):
    """Sportsbook prior -> Kalshi nodes (sport, family, band, bin). RIDE mean = gap - what RIDE pays to trade there
    (ask + fee - mid, from our rows; no outcome enters: y cancels); FADE mean = -gap - FADE's cost. Variance =
    (se^2 + TRANSFER_SD^2) x number of bands sharing the same prior, so one prior is not counted once per band."""
    pri = json.load(open(f"{HERE}/prior_nflverse.json"))["bins"]
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


def score(test, arm_of):
    """arm_of(row) -> arm name. -> {sport|ALL: stats}; a row with no position counts 0 in net per row."""
    by = collections.defaultdict(lambda: collections.defaultdict(list)); bets = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in test:
        a = arm_of(r)
        x = rr.arm_nets(r).get(a) if a != "NO_BET" else None
        for s in (r["sport"], "ALL"):
            by[s][rr.game_id(r)].append(x or 0.0)
            if x is not None:
                bets[s][rr.game_id(r)].append(x)
    out = {}
    for s in sorted(by):
        m, lo, hi, _ = rr.boot_ci(by[s])
        d = {"rows": sum(len(v) for v in by[s].values()), "games": len(by[s]), "bets": sum(len(v) for v in bets[s].values()),
             "net_per_row": [round(m, 5), round(lo, 5), round(hi, 5)]}
        if len(bets[s]) >= 2:
            m, lo, hi, _ = rr.boot_ci(bets[s])
            d["net_per_bet"] = [round(m, 5), round(lo, 5), round(hi, 5)]
        out[s] = d
    return out


def paired(test, a_of, b_of):
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in test:
        n = rr.arm_nets(r)
        d = ((n.get(a_of(r)) or 0.0) if a_of(r) != "NO_BET" else 0.0) - ((n.get(b_of(r)) or 0.0) if b_of(r) != "NO_BET" else 0.0)
        for s in (r["sport"], "ALL"):
            by[s][rr.game_id(r)].append(d)
    return {s: [round(x, 5) for x in rr.boot_ci(by[s])[:3]] for s in sorted(by)}


def leaf_heldout(test, arm_by_leaf):
    """Armed leaves: how many have >= 10 held-out games, and how many of those have held-out net > 0."""
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in test:
        k = rr.leaf_key(r); a = arm_by_leaf.get(k, "NO_BET")
        if a != "NO_BET":
            x = rr.arm_nets(r).get(a)
            if x is not None:
                by[k][rr.game_id(r)].append(x)
    rep = {k: v for k, v in by.items() if len(v) >= rr.MIN_TEST_GAMES}
    pos = sum(sum(sum(x) for x in v.values()) > 0 for v in rep.values())
    lo_pos = sum(rr.boot_ci(v)[1] > 0 for v in rep.values())
    return {"armed_with_10_heldout_games": len(rep), "heldout_net_positive": pos, "heldout_interval_above_0": lo_pos}


rows = load()
pri_all = prior_obs(rows)
fit_g, test_g = rr.split_games(rows)
fit = [r for r in rows if rr.game_id(r) in fit_g]; test = [r for r in rows if rr.game_id(r) in test_g]
print("rows", len(rows), "fit", len(fit), "test", len(test), flush=True)

# router 1: per leaf, judged alone (today's map rule: fit-window arm, thin leaves out)
v1 = {tuple(l["leaf"]): l["arm"] for l in rr.route(rows)["leaves"]}
v1_bh = {tuple(l["leaf"]): l["arm"] for l in rr.route(rows)["leaves"] if l.get("bh")}
# router 2: pooled + sequential, fit window only
routers, cache, results = {}, {}, {}
for name, cfg in (("pooled_v2", P.Config(prior_obs=prior_obs(fit))), ("pooled_v2_no_long_prior", P.Config())):
    res = P.run(obs_of(fit), cfg)
    results[name] = res
    cache[name] = {}
    def arm(r, _n=name, _res=res):
        k = rr.leaf_key(r)
        if k not in cache[_n]:
            cache[_n][k] = _res.route(k)["arm"]
        return cache[_n][k]
    routers[name] = arm
    print(name, "fit leaves armed", sum(res.route(k)["arm"] != "NO_BET" for k in res.leaf_keys()), "of", len(res.leaf_keys()), flush=True)
routers["per_leaf_v1"] = lambda r: v1.get(rr.leaf_key(r), "NO_BET")
routers["per_leaf_bh_survivors_only"] = lambda r: v1_bh.get(rr.leaf_key(r), "NO_BET")
routers["ride_every_favourite"] = lambda r: "RIDE"

out = {"corpus": {"rows": len(rows), "fit_rows": len(fit), "test_rows": len(test), "fit_games": len(fit_g), "test_games": len(test_g)},
       "config": {"bar": 0.90, "alpha": 0.10, "root_sd": 0.10, "tau_floor": 0.005, "min_inc_games": 5, "transfer_sd": TRANSFER_SD,
                  "null_var": "binary", "e_process": "mean over path nodes (depth >= 2) of per-node mixture-LR e-processes"},
       "heldout": {n: score(test, f) for n, f in routers.items()},
       "paired_heldout_net_per_row": {"pooled_v2 - per_leaf_v1": paired(test, routers["pooled_v2"], routers["per_leaf_v1"]),
                                      "pooled_v2 - ride_every_favourite": paired(test, routers["pooled_v2"], routers["ride_every_favourite"]),
                                      "pooled_v2 - pooled_v2_no_long_prior": paired(test, routers["pooled_v2"], routers["pooled_v2_no_long_prior"])}}
res = results["pooled_v2"]
v2_fit = {k: res.route(k)["arm"] for k in res.leaf_keys()}
out["leaves_with_arm"] = {
    "per_leaf_v1": {"leaves": len(v1), "armed_fit": sum(a != "NO_BET" for a in v1.values()), **leaf_heldout(test, v1)},
    "pooled_v2": {"leaves": len(v2_fit), "armed_fit": sum(a != "NO_BET" for a in v2_fit.values()), **leaf_heldout(test, v2_fit)},
    "pooled_v2_arms": dict(collections.Counter(v2_fit.values())), "per_leaf_v1_arms": dict(collections.Counter(v1.values()))}
out["tau_sd_by_depth_fit"] = {a: {d: round(math.sqrt(t), 4) for d, t in sorted(res.fits[a].tau2.items())} for a in res.cfg.arms}
out["family_posteriors_fit"] = {a: {"|".join(k): [round(p.mean, 4), round(p.sd, 4), round(p.p_pos, 3), round(res.path_log_e(k, a)[0], 2)]
                                     for k, p in sorted(res.fits[a].nodes.items()) if len(k) == 2} for a in res.cfg.arms}

# full-corpus v2 map + power calendar
cfg = P.Config(prior_obs=pri_all)
full = P.run(obs_of(rows), cfg)
last = max(P.parse_ts(r["start_time_utc"]) for r in rows)
recent = collections.defaultdict(set); allg = collections.defaultdict(set)
for r in rows:
    k = rr.leaf_key(r)
    for d in range(2, len(k) + 1):
        allg[k[:d]].add(rr.game_id(r))
        if P.parse_ts(r["start_time_utc"]) >= last - timedelta(days=14):
            recent[k[:d]].add(rr.game_id(r))
m_tests = sum(1 for l in rr.route(rows)["leaves"] if not l["thin"])
_all_obs = obs_of(rows)
NODE = {a: P.node_clusters(_all_obs, a, 2) for a in cfg.arms}
NULL = {a: P.node_null_sd(_all_obs, a, 2) for a in cfg.arms}


def vgame(cl, node, arm):
    """per-game variance for the calendar: the plug-in, floored at the binary net=0 variance (as the e-process does)."""
    g = NULL[arm].get(node, {})
    return max(cl.var_cr() or 0.0, sum(v * v for v in g.values()) / cl.rows ** 2) * cl.games
calrows = []
for k in full.leaf_keys():
    rt = full.route(k)
    best = max(cfg.arms, key=lambda a: full.fits[a].predict(k).mean)
    post = full.fits[best].predict(k)
    c = full.clusters[best].get(k)
    gpw = len(recent.get(k, ())) / 2.0
    rec = {"leaf": "|".join(str(x) for x in k), "sport": k[0], "arm_now": rt["arm"], "best_arm": best, "assumed_net": round(post.mean, 5),
           "games": c.games if c else 0, "games_per_week": gpw, "v2_weeks": None, "v1_weeks": None}
    if rt["arm"] != "NO_BET":
        rec["v2_weeks"] = 0
    elif post.mean > 0 and c and c.games >= 2 and c.var_cr():
        nodes = [k[:d] for d in range(2, len(k) + 1)]
        cross = []
        for n in nodes:
            np_ = full.fits[best].predict(n)
            ncl = NODE[best].get(n)
            if ncl is None or ncl.games < 2 or not ncl.var_cr() or np_.mean <= 0:
                continue
            hist = full.log_e[best].get(n, [])
            w = cal.weeks_to_cross(hist[-1][1] if hist else 0.0, (np_.mean, np_.var), np_.mean, vgame(ncl, n, best),
                                   len(recent.get(n, ())) / 2.0, alpha=cfg.alpha / len(nodes))
            if w is not None:
                cross.append(w)
        bar = cal.weeks_to_bar((post.mean, post.var), post.mean, vgame(c, k, best), gpw, cfg.bar)
        if cross and bar is not None:
            rec["v2_weeks"] = max(min(cross), bar)
    if post.mean > 0 and c and c.games >= 2 and c.var_cr():
        rec["v1_weeks"] = cal.weeks_to_bh(c.games, c.rows / c.games, post.mean, vgame(c, k, best), gpw, m_tests)
    calrows.append(rec)

# sensitivity: the same leaves at a FIXED true net per contract (design power, not a forecast). v2 here uses the leaf
# node alone (its e-process from today's value at alpha / path length, and its own posterior bar): sibling pooling would
# only shorten it, so this is an upper bound on v2's wait. v1 = the W110.5 BH rule over the same m tests.
SENS = (0.02, 0.05)
for rec, k in zip(calrows, full.leaf_keys()):
    best = rec["best_arm"]; c = full.clusters[best].get(k); post = full.fits[best].predict(k)
    gpw = rec["games_per_week"]; L = len(k) - 1
    for mu in SENS:
        v1w = v2w = None
        if c and c.games >= 2 and c.var_cr():
            vg = vgame(c, k, best)
            v1w = cal.weeks_to_bh(c.games, c.rows / c.games, mu, vg, gpw, m_tests)
            hist = full.log_e[best].get(k, [])
            cw = cal.weeks_to_cross(hist[-1][1] if hist else 0.0, (post.mean, post.var), mu, vg, gpw, alpha=cfg.alpha / L)
            bw = cal.weeks_to_bar((post.mean, post.var), mu, vg, gpw, cfg.bar)
            if cw is not None and bw is not None:
                v2w = max(cw, bw)
        rec[f"v1_weeks_at_{mu}"] = v1w; rec[f"v2_weeks_at_{mu}"] = v2w


def summ(key):
    o = {}
    for s in sorted({r["sport"] for r in calrows}) + ["ALL"]:
        ws = sorted(r[key] for r in calrows if (s == "ALL" or r["sport"] == s) and r[key] is not None)
        n = sum(1 for r in calrows if s == "ALL" or r["sport"] == s)
        d = lambda w: (last + timedelta(weeks=w)).date().isoformat()
        o[s] = {"leaves": n, "can_earn_within_104_weeks": len(ws), "first": d(ws[0]) if ws else None,
                "median_of_those": d(ws[len(ws) // 2]) if ws else None, "median_all_leaves": d(ws[n // 2]) if len(ws) > n // 2 else "beyond 104 weeks / never"}
    return o


out["power_calendar"] = {"as_of": last.date().isoformat(), "row_rate": "games per leaf in the corpus's last 14 days / 2",
                         "assumption": "true net = the leaf's current pooled posterior mean for its best arm; leaves whose best mean <= 0 never earn",
                         "bh_tests_m": m_tests, "pooled_v2": summ("v2_weeks"), "per_leaf_bh": summ("v1_weeks"),
                         "ride_every_favourite": "no evidence required: every leaf rides from day 0",
                         "sensitivity": {f"at_{mu}": {"pooled_v2_leaf_only_upper_bound": summ(f"v2_weeks_at_{mu}"),
                                                       "per_leaf_bh": summ(f"v1_weeks_at_{mu}")} for mu in SENS}}
out["full_corpus_v2"] = {"leaves": len(full.leaf_keys()), "armed": sum(r["arm_now"] != "NO_BET" for r in calrows),
                         "arms": dict(collections.Counter(r["arm_now"] for r in calrows)), "looks": len(full.looks)}
json.dump(out, open(safe_out(f"{HERE}/results.json"), "w"), indent=1)
json.dump(calrows, open(safe_out(f"{HERE}/power_calendar.json"), "w"), indent=1)

if "--write-map" in sys.argv:
    fams = sorted({k[:3] for k in full.leaf_keys()})
    seen = set(full.leaf_keys())
    leaves = {}
    for f3 in fams:
        for b in range(len(rr.FAV_BINS) + 1):
            for mv in ("na", "up", "down", "flat"):
                k = f3 + (b, mv)
                rt = full.route(k)
                rt["seen"] = k in seen
                leaves["|".join(str(x) for x in k)] = rt
    doc = {"version": "v2", "arm_source": "leaf_map_v2_pooled_sequential_w115_1", "key": "sport|market_type|band|favprice_bin|move_bin",
           "source": "12_EXPLORATORY/evidence_design/run.py (W115.1) on the W110.5 corpus, all rows through " + last.date().isoformat(),
           "rule": "arm iff pooled P(net>0) >= bar AND path-averaged e-process >= 1/alpha; else NO_BET",
           "posterior_fields": "[mean net per contract, sd, P(net>0)]", "source_fields": "[path node with the most evidence, log path e-value]",
           "config": out["config"], "tau_sd_by_depth": {a: {str(d): round(math.sqrt(t), 4) for d, t in sorted(full.fits[a].tau2.items())} for a in cfg.arms},
           "unseen_leaf": "seen=false leaves inherit their deepest known ancestor plus tau; a key outside the map is NO_BET",
           "leaves": leaves}
    # Written inside the fence; the copy under src/.../leaf_maps/ is a reviewed promotion pinned by sha256
    # in tests/test_leaf_map_version_w116.py and in ROUTER_V2_PREREGISTRATION_2026-11-17.md.
    safe_out("evidence_design/leaf_map_v2.json").write_text(json.dumps(doc, indent=1, sort_keys=True))
print(json.dumps({k: out[k] for k in ("heldout", "paired_heldout_net_per_row", "leaves_with_arm", "full_corpus_v2", "power_calendar")}, indent=1))
