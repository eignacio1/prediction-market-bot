"""W121.1: the weekly look. Router v2's always-valid guarantee needs looks taken on schedule and CARRIED FORWARD.

One run = one cut (the latest Tuesday 10:00 UTC at or before `now`). Rows are box shadow rows settled through the cut,
grouped into whole-week looks (pipeline.look_index). Per sport and per map (v1, each candidate in `router_candidates`, plus
`board`: every arm on every row = what a refit router would earn) the saved State is advanced over the looks it has not
yet scored, in order, and saved again. Nothing is recomputed from scratch: the running e-process, the pending increment and
its frozen prior, and the posterior's leaf clusters all come from the previous look's state file.

A look already scored is never re-scored: a row that settles after its look was taken is COUNTED as late and left out of
that look (it would otherwise be chosen after seeing the outcome of the weekly cut). A week with no look taken is
reported (`missed_looks`, `catch_up`), never silently filled.

Wording: a leaf with no arm is "routed to no bet in this leaf yet"; nothing here closes a cell or a market.
"""
from __future__ import annotations

import collections
import glob
import json
import math
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from prediction_market_bot.decision_trees.evidence import calendar as cal
from prediction_market_bot.decision_trees.evidence import pipeline as P
from prediction_market_bot.quant import retro_route as rr

SCHEMA = 1
BOARD = "board"
V1 = "v1"


def cut_of(now: datetime) -> datetime:
    """Latest Tuesday 10:00 UTC at or before now (the looks are whole weeks from LOOK_ANCHOR, itself such a Tuesday)."""
    now = now.astimezone(timezone.utc)
    wk = int((now - P.LOOK_ANCHOR).total_seconds() // (7 * 86400))
    return P.LOOK_ANCHOR + timedelta(weeks=wk)


def cut_look(cut: datetime) -> int:
    """First look index NOT yet complete at the cut: looks < this are scored."""
    return int(round((cut - P.LOOK_ANCHOR).total_seconds() / (7 * 86400)))


# ---------------------------------------------------------------- rows -> per-map observations

def _jl(path: str) -> Iterable[dict]:
    try:
        fh = open(path, "r", encoding="utf-8", errors="ignore")
    except OSError:
        return
    with fh:
        for line in fh:
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def load_rows(shadow_dir: str, nhl_dir: str) -> List[dict]:
    """Settled rows. NFL / NBA / MLB: <shadow_dir>/settled/*.jsonl (already carry `y`). NHL: raw <nhl_dir>/NHL_*.jsonl joined to
    <nhl_dir>/settled/ on (market_ticker, run_id) via `outcome`."""
    rows: List[dict] = []
    for p in sorted(glob.glob(os.path.join(shadow_dir, "settled", "*.jsonl"))):
        rows += list(_jl(p))
    for p in sorted(glob.glob(os.path.join(nhl_dir, "NHL_*.jsonl"))):
        out = {}
        for q in glob.glob(os.path.join(nhl_dir, "settled", os.path.basename(p))):
            for r in _jl(q):
                out[(r.get("market_ticker"), r.get("run_id"))] = r.get("outcome")
        for r in _jl(p):
            y = out.get((r.get("market_ticker"), r.get("run_id")))
            if y is not None:
                r["y"] = float(y)
                rows.append(r)
    rows = rr.dedupe(rows)
    rr.add_moves(rows)
    return rows


def _only(nets: dict, arm: Optional[str]) -> dict:
    return {a: (x if a == arm else None) for a, x in nets.items()}


def series_of(rows: Iterable[dict]) -> Dict[str, List[P.Obs]]:
    """-> {"<SPORT>|<map>": [Obs]}. A map's series holds, per row, only the arm THAT MAP chose (its nets for other arms are None),
    so its e-process scores the map's own routing; `board` keeps every arm on every row. Rows without a map's block are not
    in that map's series (the candidates exist only on rows logged since W120.2)."""
    out: Dict[str, List[P.Obs]] = collections.defaultdict(list)
    for r in rows:
        try:
            k, g, lk, nets = rr.leaf_key(r), rr.game_id(r), P.look_index(r["start_time_utc"]), rr.arm_nets(r)
        except (KeyError, ValueError, TypeError):
            continue
        sp = str(r["sport"]).upper()
        out[f"{sp}|{BOARD}"].append(P.Obs(k, g, lk, nets))
        v1 = (r.get("router") or {}).get("arm")
        if v1 is not None:
            out[f"{sp}|{V1}"].append(P.Obs(k, g, lk, _only(nets, v1)))
        cands = r.get("router_candidates")
        if isinstance(cands, dict):
            for name, rec in cands.items():
                if isinstance(rec, dict) and rec.get("arm") is not None:
                    out[f"{sp}|{name}"].append(P.Obs(k, g, lk, _only(nets, rec["arm"])))
    return out


# ---------------------------------------------------------------- state files

def load_state(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            j = json.load(fh)
    except (OSError, ValueError):
        return {"schema": SCHEMA, "last_look": None, "series": {}, "routes": {}}
    if j.get("schema") != SCHEMA:
        raise ValueError(f"state schema {j.get('schema')} != {SCHEMA}: refusing to carry forward a state of another shape")
    return j


def save_state(path: str, j: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(j, fh, sort_keys=True)
    os.replace(tmp, path)


# ---------------------------------------------------------------- one look

def _leaf_id(k: tuple) -> str:
    return "|".join(str(x) for x in k)


def _calendar(res: P.Result, cfg: P.Config, obs_all: List[P.Obs], now_look: int) -> dict:
    """Weeks to the first earned arm for unarmed leaves whose best pooled mean is positive, at the last 4 weeks' game rate.
    Assumes the true net equals that leaf's current posterior mean (a design number, not a forecast)."""
    recent: Dict[tuple, set] = collections.defaultdict(set)
    for o in obs_all:
        if o.look >= now_look - 4:
            for d in range(2, len(o.key) + 1):
                recent[o.key[:d]].add(o.game)
    rows = []
    for k in res.leaf_keys():
        if res.route(k)["arm"] != "NO_BET":
            continue
        best = max(cfg.arms, key=lambda a: res.fits[a].predict(k).mean)
        post = res.fits[best].predict(k)
        c = res.clusters[best].get(k)
        if post.mean <= 0 or not c or c.games < 2 or not c.var_cr():
            continue
        nodes = [k[:d] for d in range(2, len(k) + 1)]
        nulls = P.node_null_sd(obs_all, best, 2)
        cross = []
        for n in nodes:
            ncl = P.node_clusters(obs_all, best, 2).get(n)
            np_ = res.fits[best].predict(n)
            if ncl is None or ncl.games < 2 or not ncl.var_cr() or np_.mean <= 0:
                continue
            vg = max(ncl.var_cr() or 0.0, sum(v * v for v in nulls.get(n, {}).values()) / ncl.rows ** 2) * ncl.games
            hist = res.log_e[best].get(n, [])
            w = cal.weeks_to_cross(hist[-1][1] if hist else 0.0, (np_.mean, np_.var), np_.mean, vg,
                                   len(recent.get(n, ())) / 4.0, alpha=cfg.alpha / len(nodes))
            if w is not None:
                cross.append(w)
        vg = c.var_cr() * c.games
        bar = cal.weeks_to_bar((post.mean, post.var), post.mean, vg, len(recent.get(k, ())) / 4.0, cfg.bar)
        if cross and bar is not None:
            rows.append({"leaf": _leaf_id(k), "best_arm": best, "assumed_net": round(post.mean, 5),
                         "weeks_to_arm": max(min(cross), bar)})
    ws = sorted(r["weeks_to_arm"] for r in rows)
    return {"leaves_that_can_earn": len(ws), "soonest_weeks": ws[0] if ws else None,
            "median_weeks": ws[len(ws) // 2] if ws else None, "assumption": "true net = the leaf's current posterior mean",
            "soonest": sorted(rows, key=lambda r: r["weeks_to_arm"])[:5]}


def look_series(name: str, state_json: Optional[dict], obs: List[P.Obs], upto: int, cfg: P.Config,
                prev_last: Optional[int] = None, taken: Optional[Dict[str, int]] = None) -> Tuple[dict, dict, dict, Dict[str, int]]:
    """-> (new state json, report, routes, rows taken per look). Scores the looks after `prev_last` (the last week any series took)
    and before `upto`; rows for a week at or before prev_last that were not in it when it was taken are late and score nowhere."""
    st = P.State.from_json(state_json) if state_json else P.State.new(cfg.arms)
    new = [o for o in obs if o.look < upto and (prev_last is None or o.look > prev_last)]
    taken = dict(taken or {})
    now_by_look = collections.Counter(o.look for o in obs if prev_last is not None and o.look <= prev_last)
    late = sum(max(0, n - taken.get(str(lk), 0)) for lk, n in now_by_look.items())
    for lk, n in collections.Counter(o.look for o in new).items():
        taken[str(lk)] = n
    P.advance(st, new, cfg)
    res = P.result_of(st, cfg)
    routes, armed = {}, collections.Counter()
    for k in res.leaf_keys():
        r = res.route(k)
        routes[_leaf_id(k)] = r["arm"]
        armed[r["arm"]] += 1
    leaders = []
    for k in res.leaf_keys():
        for a in cfg.arms:
            le, who = res.path_log_e(k, a)
            if who is not None and le > 0:
                leaders.append({"leaf": _leaf_id(k), "arm": a, "log_e": round(le, 3), "e": round(math.exp(min(le, 50)), 2),
                                "p_pos": round(res.fits[a].predict(k).p_pos, 4), "mean": round(res.fits[a].predict(k).mean, 5)})
    leaders.sort(key=lambda x: -x["log_e"])
    games = len({o.game for o in obs if o.look < upto})
    rep = {"series": name, "looks_in_state": len(st.looks), "last_look": st.looks[-1] if st.looks else None,
           "looks_scored_now": sorted({o.look for o in new}), "rows_scored_now": len(new), "games_total": games,
           "late_rows_not_scored": late, "leaves": len(routes), "leaves_with_arm": sum(v != "NO_BET" for v in routes.values()),
           "arms": dict(armed), "e_leaders": leaders[:5], "calendar": _calendar(res, cfg, [o for o in obs if o.look < upto], upto)}
    return st.to_json(), rep, routes, taken


# ---------------------------------------------------------------- the whole run

def run(shadow_dir: str, nhl_dir: str, out_dir: str, now: Optional[datetime] = None, cfg: Optional[P.Config] = None) -> dict:
    now = now or datetime.now(timezone.utc)
    cfg = cfg or P.Config()
    cut = cut_of(now)
    upto = cut_look(cut)
    state_path = os.path.join(out_dir, "state.json")
    top = load_state(state_path)
    prev_last = top["last_look"]
    if prev_last is not None and prev_last >= upto - 1:
        return {"schema": SCHEMA, "cut_utc": cut.strftime("%Y-%m-%dT%H:%M:%SZ"), "skipped": "look already taken for this cut",
                "last_look": prev_last}
    rows = load_rows(shadow_dir, nhl_dir)
    all_series = series_of(rows)
    looks_present = sorted({o.look for s in all_series.values() for o in s if o.look < upto and (prev_last is None or o.look > prev_last)})
    expected = list(range((prev_last + 1) if prev_last is not None else (looks_present[0] if looks_present else upto), upto))
    missed = [k for k in expected if k not in looks_present]  # a week with no settled rows at all: reported, never filled
    report = {"schema": SCHEMA, "cut_utc": cut.strftime("%Y-%m-%dT%H:%M:%SZ"), "cut_look": upto, "previous_last_look": prev_last,
              "looks_scored": looks_present, "missed_looks": missed,
              "catch_up": prev_last is not None and (upto - prev_last) > 1,
              "prior": f"root N(0, {cfg.root_sd}^2); no sportsbook prior; bar {cfg.bar}; alpha {cfg.alpha}; min_inc_games {cfg.min_inc_games}",
              "rows_loaded": len(rows), "series": {}, "earned": [], "lost": []}
    prev_routes = top.get("routes", {})
    for name in sorted(all_series):
        meta = top.setdefault("rows_taken", {})
        sj, rep, routes, meta[name] = look_series(name, top["series"].get(name), all_series[name], upto, cfg, prev_last, meta.get(name))
        top["series"][name] = sj
        report["series"][name] = rep
        for leaf, arm in routes.items():
            before = prev_routes.get(f"{name}#{leaf}", "NO_BET")
            if before == "NO_BET" and arm != "NO_BET":
                report["earned"].append({"series": name, "leaf": leaf, "arm": arm})
            elif before != "NO_BET" and arm == "NO_BET":
                report["lost"].append({"series": name, "leaf": leaf, "was": before})
            prev_routes[f"{name}#{leaf}"] = arm
    top["routes"] = prev_routes
    top["last_look"] = upto - 1  # every complete week up to the cut was taken (a week with no rows is reported in missed_looks)
    report["leaders"] = sorted((dict(e, series=n) for n, r in report["series"].items() for e in r["e_leaders"]),
                               key=lambda x: -x["log_e"])[:10]
    stamp = cut.strftime("%Y-%m-%d")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{stamp}.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
    with open(os.path.join(out_dir, f"{stamp}.md"), "w", encoding="utf-8") as fh:
        fh.write(summary(report))
    save_state(state_path, top)  # last: a crash before this leaves the previous state, so the look reruns, never half-applies
    return report


def summary(rep: dict) -> str:
    L = [f"# Weekly look, cut {rep['cut_utc']}", ""]
    if rep.get("skipped"):
        return "\n".join(L + [f"Skipped: {rep['skipped']} (last look {rep['last_look']})."]) + "\n"
    L.append(f"Looks scored: {rep['looks_scored'] or 'none (no new settled rows)'}"
             + (f" · missed (no settled rows): {rep['missed_looks']}" if rep["missed_looks"] else "")
             + (" · CATCH-UP: more than one week since the last look" if rep["catch_up"] else ""))
    L += [f"Rows loaded: {rep['rows_loaded']}. Prior: {rep['prior']}.", "",
          "| series | games | leaves | with an arm | late rows | soonest to arm (weeks) |", "|---|---|---|---|---|---|"]
    for n, r in rep["series"].items():
        L.append(f"| {n} | {r['games_total']} | {r['leaves']} | {r['leaves_with_arm']} | {r['late_rows_not_scored']} "
                 f"| {r['calendar']['soonest_weeks']} |")
    L += ["", f"Earned an arm this look: {len(rep['earned'])}. Routed back to no bet: {len(rep['lost'])}.", ""]
    for e in rep["earned"][:10]:
        L.append(f"- earned: {e['series']} {e['leaf']} -> {e['arm']}")
    for e in rep["lost"][:10]:
        L.append(f"- no bet again: {e['series']} {e['leaf']} (was {e['was']})")
    L += ["", "E-value leaders (path-averaged e-process; arm needs e >= 1/alpha AND P(net>0) >= bar):"]
    for e in rep["leaders"]:
        L.append(f"- {e['series']} {e['leaf']} {e['arm']}: e={e['e']} P(net>0)={e['p_pos']} mean={e['mean']}")
    return "\n".join(L) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shadow-dir", default=os.environ.get("PM_SHADOW_DIR", "exp_output/PREGAME_SHADOW"))
    ap.add_argument("--nhl-dir", default="data/shadow/nhl")
    ap.add_argument("--out-dir", default="exp_output/EVIDENCE_WEEKLY")
    ap.add_argument("--now", help="override the clock (UTC ISO), for tests and replays")
    a = ap.parse_args(argv)
    now = P.parse_ts(a.now) if a.now else None
    rep = run(a.shadow_dir, a.nhl_dir, a.out_dir, now)
    print(summary(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
