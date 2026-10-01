#!/usr/bin/env python3
"""EXP-033 — multi-leg coherence of Kalshi sports books (arithmetic only).

No model, no order, no pool, no sizing. Reads exp_output/PRICE_ARCHIVE (read-only) and
public, unauthenticated Kalshi GET endpoints (market/event metadata; same endpoint family
EXP-031 used for settlements). Subcommands:

    fetch-meta   cache Kalshi market + event metadata per series (GET only, no credentials)
    group        reconstruct and verify leg sets; write d1_grouping.json
    measure      run the pre-registered coherence tests (requires the frozen pre-registration)

Pre-registration: 05_RESEARCH_EXPERIMENTS/EXP033_MULTILEG_COHERENCE_PREREGISTRATION_2026-10-01.md
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict

ARCHIVE = "exp_output/PRICE_ARCHIVE"
OUT = "exp_output/EXP-033-MULTILEG-COHERENCE"
API = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = [
    "KXMLBGAME", "KXMLBSPREAD", "KXMLBTOTAL", "KXMLBTEAMTOTAL",
    "KXMLBF3", "KXMLBF5", "KXMLBF7", "KXMLBF5SPREAD", "KXMLBF5TOTAL", "KXMLBHIT",
    "KXNFLGAME", "KXNFLSPREAD", "KXNFLTEAMTOTAL", "KXNFLTOTAL",
]
MARKET_KEEP = ["ticker", "event_ticker", "market_type", "strike_type", "floor_strike", "cap_strike",
               "yes_sub_title", "custom_strike", "status", "result", "close_time"]
EVENT_KEEP = ["event_ticker", "series_ticker", "mutually_exclusive", "sub_title", "title"]


def _get(url: str) -> dict:
    """Public read-only GET with retry. No credentials, no order endpoint."""
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"GET failed: {url}")


def fetch_series_meta(series: str, out_dir: str, sleep_s: float = 0.15) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    markets, events = {}, {}
    for status in ("open", "closed", "settled"):
        cursor = ""
        while True:
            u = f"{API}/markets?series_ticker={series}&status={status}&limit=1000" + (f"&cursor={cursor}" if cursor else "")
            j = _get(u)
            for m in j["markets"]:
                markets[m["ticker"]] = {k: m.get(k) for k in MARKET_KEEP}
            cursor = j.get("cursor") or ""
            if not cursor or not j["markets"]:
                break
            time.sleep(sleep_s)
        cursor = ""
        while True:
            u = f"{API}/events?series_ticker={series}&status={status}&limit=200" + (f"&cursor={cursor}" if cursor else "")
            j = _get(u)
            for e in j["events"]:
                events[e["event_ticker"]] = {k: e.get(k) for k in EVENT_KEEP}
            cursor = j.get("cursor") or ""
            if not cursor or not j["events"]:
                break
            time.sleep(sleep_s)
    with open(os.path.join(out_dir, f"{series}.json"), "w") as fh:
        json.dump({"markets": markets, "events": events}, fh)
    return {"series": series, "markets": len(markets), "events": len(events)}


def cmd_fetch_meta(args):
    for s in SERIES:
        print(json.dumps(fetch_series_meta(s, os.path.join(args.out, "meta"))), flush=True)


# ----------------------------------------------------------------------------------------------
# D1 -- leg-set reconstruction. Every grouping decision below is read from Kalshi's own
# metadata (event.mutually_exclusive, market.strike_type/floor_strike, custom_strike team/player
# uuid). The game key (event_ticker suffix) is used ONLY as a join key, and is verified against
# event.sub_title and the team uuids before any cross-family set is accepted.
# ----------------------------------------------------------------------------------------------
EXPECTED_ME_LEGS = {"KXMLBGAME": 2, "KXMLBF3": 3, "KXMLBF5": 3, "KXMLBF7": 3, "KXNFLGAME": 2}
# (sub family, super family, how the two legs are matched). P(sub) <= P(super) is a logical
# implication of the contract wording: sub true => super true.
CROSS = [
    ("KXMLBSPREAD", "KXMLBGAME", "team"),
    ("KXNFLSPREAD", "KXNFLGAME", "team"),
    ("KXMLBF5SPREAD", "KXMLBF5", "team"),
    ("KXMLBTEAMTOTAL", "KXMLBTOTAL", "floor"),
    ("KXNFLTEAMTOTAL", "KXNFLTOTAL", "floor"),
    ("KXMLBF5TOTAL", "KXMLBTOTAL", "floor"),
]


def game_key(event_ticker: str) -> str:
    return event_ticker.split("-", 1)[1]


def load_meta(out_dir: str):
    markets, events = {}, {}
    for s in SERIES:
        d = json.load(open(os.path.join(out_dir, "meta", f"{s}.json")))
        for t, m in d["markets"].items():
            m["series"] = s
            markets[t] = m
        for e, v in d["events"].items():
            events[e] = v
    return markets, events


def _quote_ok(r) -> bool:
    try:
        return float(r["yes_ask"]) > 0 and float(r["no_ask"]) > 0 and r["yes_bid"] is not None
    except (TypeError, ValueError, KeyError):
        return False


def scan_archive(archive_dir: str):
    """presence[ticker] = set(run_ts) with a parseable executable quote; plus archive ticker set."""
    presence, seen = defaultdict(set), set()
    for _, r in iter_price_rows(archive_dir):
        seen.add(r["ticker"])
        if _quote_ok(r):
            presence[r["ticker"]].add(r["run_ts"])
    return presence, seen


def iter_price_rows(archive_dir: str):
    for path in sorted(glob.glob(os.path.join(archive_dir, "prices_*.jsonl"))):
        with open(path) as fh:
            for line in fh:
                yield os.path.basename(path), json.loads(line)


def build_sets(markets, events, presence, seen):
    by_event = defaultdict(list)
    for t, m in markets.items():
        by_event[m["event_ticker"]].append(t)
    excl = Counter()
    sets = []
    # --- complementary (event.mutually_exclusive == True)
    for ev, ts in by_event.items():
        e = events.get(ev)
        series = markets[ts[0]]["series"]
        if not e or not any(t in seen for t in ts):
            continue
        if e["mutually_exclusive"] is True:
            exp = EXPECTED_ME_LEGS.get(series)
            if exp is None or len(ts) != exp:
                excl[(series, "me_leg_count_unexpected")] += 1
                continue
            res = [markets[t]["result"] for t in ts]
            sets.append({"relation": "complementary", "family": series, "event": ev, "legs": sorted(ts),
                         "settled": all(r in ("yes", "no") for r in res),
                         "n_yes": sum(r == "yes" for r in res) if all(r in ("yes", "no") for r in res) else None})
    # --- nested ladders within an event (strike_type == greater, event not ME)
    for ev, ts in by_event.items():
        e = events.get(ev)
        series = markets[ts[0]]["series"]
        if not e or e["mutually_exclusive"] is not False or not any(t in seen for t in ts):
            continue
        groups = defaultdict(list)
        for t in ts:
            m = markets[t]
            if m["strike_type"] != "greater" or m["floor_strike"] is None:
                excl[(series, "ladder_leg_not_greater_or_no_floor")] += 1
                continue
            cs = m["custom_strike"] or {}
            groups[(cs.get("baseball_team") or cs.get("football_team"), cs.get("baseball_player"))].append(t)
        for k, g in groups.items():
            if len(g) < 2:
                excl[(series, "ladder_single_rung")] += 1
                continue
            g.sort(key=lambda t: markets[t]["floor_strike"])
            if len({markets[t]["floor_strike"] for t in g}) != len(g):
                excl[(series, "ladder_duplicate_floor")] += 1
                continue
            sets.append({"relation": "nested", "kind": "ladder", "family": series, "event": ev, "legs": g})
    # --- nested, cross-family, verified by game key + sub_title + team uuid
    gk = defaultdict(dict)  # game key -> series -> event
    for ev, ts in by_event.items():
        if events.get(ev):
            gk[game_key(ev)][markets[ts[0]]["series"]] = ev
    sub_bad = 0
    for g, fam in gk.items():
        subs = {events[e]["sub_title"] for e in fam.values()}
        if len(subs) > 1:
            sub_bad += 1
            excl[("game", "sub_title_mismatch_across_families")] += 1
            continue
        for sub_s, sup_s, how in CROSS:
            if sub_s not in fam or sup_s not in fam:
                continue
            sub_ts = [t for t in by_event[fam[sub_s]] if markets[t]["strike_type"] == "greater"]
            sup_ts = by_event[fam[sup_s]]
            if not any(t in seen for t in sub_ts + sup_ts):
                continue
            if how == "team":
                sup_team = {(markets[t]["custom_strike"] or {}).get("baseball_team") or
                            (markets[t]["custom_strike"] or {}).get("football_team"): t
                            for t in sup_ts if (markets[t]["yes_sub_title"] or "").lower() != "tie"}
                for t in sub_ts:
                    cs = markets[t]["custom_strike"] or {}
                    team = cs.get("baseball_team") or cs.get("football_team")
                    if team not in sup_team:
                        excl[(sub_s, "cross_team_uuid_unmatched")] += 1
                        continue
                    sets.append({"relation": "nested", "kind": "cross", "family": f"{sub_s}<={sup_s}",
                                 "event": fam[sub_s], "legs": [t, sup_team[t] if False else sup_team[team]]})
            else:
                sup_by_floor = {markets[t]["floor_strike"]: t for t in sup_ts if markets[t]["strike_type"] == "greater"}
                for t in sub_ts:
                    f = markets[t]["floor_strike"]
                    if f not in sup_by_floor:
                        excl[(sub_s, "cross_floor_unmatched")] += 1
                        continue
                    sets.append({"relation": "nested", "kind": "cross", "family": f"{sub_s}<={sup_s}",
                                 "event": fam[sub_s], "legs": [t, sup_by_floor[f]]})
    return sets, excl, gk


def testable_runs(s, presence):
    if s["relation"] == "complementary" or s.get("kind") == "cross":
        runs = None
        for t in s["legs"]:
            runs = presence[t] if runs is None else runs & presence[t]
        return len(runs or ())
    cnt = Counter()
    for t in s["legs"]:
        for r in presence[t]:
            cnt[r] += 1
    return sum(1 for v in cnt.values() if v >= 2)


def cmd_group(args):
    markets, events = load_meta(args.out)
    presence, seen = scan_archive(args.archive)
    unmapped = sorted(t for t in seen if t not in markets)
    sets, excl, gk = build_sets(markets, events, presence, seen)
    for s in sets:
        s["n_legs"] = len(s["legs"])
        s["testable_runs"] = testable_runs(s, presence)
    # exhaustiveness check against actual settlements (complementary sets only)
    exh = defaultdict(Counter)
    for s in sets:
        if s["relation"] == "complementary" and s["settled"]:
            exh[s["family"]][s["n_yes"]] += 1
    dist = defaultdict(lambda: {"sets": 0, "testable_sets": 0, "legs": Counter(), "runs": 0})
    for s in sets:
        d = dist[(s["relation"], s["family"])]
        d["sets"] += 1
        d["legs"][s["n_legs"]] += 1
        if s["testable_runs"] > 0:
            d["testable_sets"] += 1
            d["runs"] += s["testable_runs"]
    fam_per_game = Counter(len(f) for f in gk.values())
    summary = {
        "archive_tickers": len(seen), "archive_tickers_not_in_meta": len(unmapped),
        "unmapped_sample": unmapped[:10],
        "distribution": {f"{k[0]}|{k[1]}": {"sets": v["sets"], "testable_sets": v["testable_sets"],
                                            "legs_per_set": dict(v["legs"]), "testable_set_runs": v["runs"]}
                         for k, v in sorted(dist.items())},
        "exclusions": {f"{k[0]}|{k[1]}": v for k, v in sorted(excl.items())},
        "exhaustiveness_n_yes_by_family": {k: dict(v) for k, v in exh.items()},
        "families_per_game_key": dict(sorted(fam_per_game.items())),
    }
    os.makedirs(args.out, exist_ok=True)
    json.dump({"summary": summary, "sets": sets}, open(os.path.join(args.out, "d1_grouping.json"), "w"))
    print(json.dumps(summary, indent=1, default=str))


# ----------------------------------------------------------------------------------------------
# D3 -- measurement, exactly as pre-registered (EXP033_MULTILEG_COHERENCE_PREREGISTRATION_2026-10-01.md)
# ----------------------------------------------------------------------------------------------
SEED = 20261001
FLIPS = 10000
BOOT = 2000
MIN_GAMES = 30
ALPHA = 0.05


def fee(p: float) -> float:
    """ADR-0016 in-repo fee model (paper_trader.py:505): 0.07*p*(1-p) per contract at price paid."""
    return round(0.07 * p * (1.0 - p), 6)


def comp_margin(legs, direction):
    """legs = [(yes_ask, no_ask)]. Returns (gross, net) margin per $1 guaranteed payoff."""
    n = len(legs)
    if direction == "buy_all_yes":
        cost = sum(y for y, _ in legs)
        gross = 1.0 - cost
        return round(gross, 4), round(gross - sum(fee(y) for y, _ in legs), 4)
    cost = sum(nn for _, nn in legs)
    gross = (n - 1) - cost
    return round(gross, 4), round(gross - sum(fee(nn) for _, nn in legs), 4)


def edge_margin(sup_yes_ask, sub_no_ask):
    gross = 1.0 - sup_yes_ask - sub_no_ask
    return round(gross, 4), round(gross - fee(sup_yes_ask) - fee(sub_no_ask), 4)


def mono_margin(quotes):
    """quotes = [(yes_ask, no_ask)] ordered sub->super for a ladder (rising floor = sub-most last).
    Ladder legs arrive ascending by floor, so a HIGHER floor is the SUB. All pairs i<j:
    super = legs[i] (lower floor), sub = legs[j]. Returns max (gross, net) over pairs."""
    best_g, best_n = None, None
    for i in range(len(quotes)):
        for j in range(i + 1, len(quotes)):
            g, nn = edge_margin(quotes[i][0], quotes[j][1])
            if best_g is None or nn > best_n:
                best_g, best_n = g, nn
    return best_g, best_n


def holm(pvals, alpha=ALPHA):
    """Holm-Bonferroni; returns adjusted p-values (monotone, capped at 1) in input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [1.0] * m
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvals[i]))
        adj[i] = run
    return adj


def signflip_p(game_diffs, flips=FLIPS, seed=SEED):
    """One-sided sign-flip test over games of sum(real - placebo); p = (#T*>=T + 1)/(flips+1)."""
    import numpy as np
    d = np.asarray(game_diffs, dtype=float)
    if d.size == 0:
        return 1.0
    rng = np.random.default_rng(seed)
    T = d.sum()
    ge = 0
    for _ in range(0, flips, 1000):
        sg = rng.choice([-1.0, 1.0], size=(1000, d.size))
        ge += int(((sg * d).sum(axis=1) >= T - 1e-12).sum())
    return (ge + 1) / (flips + 1)


def persistent(flags_by_runidx):
    """flags_by_runidx: sorted [(run_index, net>0)]. Count observations in streaks of >=2
    consecutive run indices."""
    n, streak = 0, []
    prev = None
    for idx, f in flags_by_runidx:
        if f and prev is not None and idx == prev + 1 and streak:
            streak.append(idx)
        elif f:
            if len(streak) >= 2:
                n += len(streak)
            streak = [idx]
        else:
            if len(streak) >= 2:
                n += len(streak)
            streak = []
        prev = idx
    if len(streak) >= 2:
        n += len(streak)
    return n


def load_quotes(archive_dir, tickers):
    """quotes[ticker] = sorted [(run_ts, yes_ask, no_ask, yes_mid) or None-quote]; first row per (ticker, run_ts)."""
    q = defaultdict(dict)
    dup = 0
    for _, r in iter_price_rows(archive_dir):
        t = r["ticker"]
        if t not in tickers:
            continue
        if r["run_ts"] in q[t]:
            dup += 1
            continue
        ok = r.get("status") == "active" and _quote_ok(r)
        ya = na = None
        if ok:
            ya, na = round(float(r["yes_ask"]), 4), round(float(r["no_ask"]), 4)
            ok = 0 < ya < 1 and 0 < na < 1
        q[t][r["run_ts"]] = (ya, na, r.get("yes_mid")) if ok else None
    return q, dup


def set_series(s):
    return s["family"].split("<=")[0]


def obs_margins(s, q_by_leg, direction, h=None, mids=None):
    """q_by_leg: [(ya, na)] in s['legs'] order. Returns (gross, net)."""
    if s["relation"] == "complementary":
        return comp_margin(q_by_leg, direction)
    if s.get("kind") == "cross":
        # legs = [sub, super]
        return edge_margin(q_by_leg[1][0], q_by_leg[0][1])
    return mono_margin(q_by_leg)


def cmd_measure(args):
    import numpy as np
    g = json.load(open(os.path.join(args.out, "d1_grouping.json")))
    sets = [s for s in g["sets"] if s["testable_runs"] > 0]
    markets, _ = load_meta(args.out)
    tickers = {t for s in sets for t in s["legs"]}
    q, dup = load_quotes(args.archive, tickers)
    H = {k: v["H"] for k, v in json.load(open(args.h_file))["families"].items()}
    rng = np.random.default_rng(SEED)
    sport_runs = {}
    for sp in ("KXMLB", "KXNFL"):
        ru = sorted({r for t, d in q.items() if t.startswith(sp) for r in d})
        sport_runs[sp] = {r: i for i, r in enumerate(ru)}
    seqs = {t: sorted(d) for t, d in q.items()}
    pos = {t: {r: i for i, r in enumerate(sq)} for t, sq in seqs.items()}
    sport_of = lambda s: "KXNFL" if set_series(s).startswith("KXNFL") else "KXMLB"
    # --- validity gates from settled results
    bad_edges = Counter()
    for s in sets:
        if s["relation"] == "nested":
            res = [markets[t]["result"] for t in s["legs"]]
            if s.get("kind") == "cross":
                if res[0] == "yes" and res[1] == "no":
                    bad_edges[s["family"]] += 1
            else:
                for i in range(len(res)):
                    for j in range(i + 1, len(res)):  # j has the higher floor => sub
                        if res[j] == "yes" and res[i] == "no":
                            bad_edges[s["family"]] += 1
    cells = {}
    def cell(key):
        return cells.setdefault(key, {"obs": 0, "untestable": 0, "gross_pos": 0, "net_pos": 0, "net_pos_H": 0,
                                      "margins_pos": [], "games": defaultdict(lambda: [0, 0, 0]),  # n, real_viol, plac_viol
                                      "paired": 0, "plac_viol": 0, "persist_obs": 0, "runs_all": 0, "overround": []})
    for s in sets:
        ser = set_series(s)
        dirs = ["mono"] if s["relation"] == "nested" else (["buy_all_no"] if ser.startswith("KXNFL") else ["buy_all_yes", "buy_all_no"])
        game = game_key(s["event"])
        ladder = s["relation"] == "nested" and s.get("kind") == "ladder"
        if ladder:
            cnt = Counter(r for t in s["legs"] for r, v in q[t].items() if v is not None)
            runs = sorted(r for r, n in cnt.items() if n >= 2)
        else:
            runs = sorted(set.intersection(*[set(q[t]) for t in s["legs"]]))
        for d in dirs:
            c = cell((s["relation"], s["family"], d))
            flags = []
            for r in runs:
                c["runs_all"] += 1
                if ladder:
                    use = [t for t in s["legs"] if q[t].get(r) is not None]
                else:
                    use = s["legs"]
                legq = [q[t][r] for t in use]
                if any(x is None for x in legq):
                    c["untestable"] += 1
                    continue
                gross, net = obs_margins(s, [(x[0], x[1]) for x in legq], d)
                c["obs"] += 1
                c["gross_pos"] += gross > 0
                c["net_pos"] += net > 0
                if net > 0:
                    c["margins_pos"].append(net)
                flags.append((sport_runs[sport_of(s)][r], net > 0))
                # H sensitivity: replace ask by mid +/- family H
                if all(x[2] is not None for x in legq):
                    mids = [float(x[2]) for x in legq]
                    hq = [(min(0.999, m + H[markets[t]["series"]]), min(0.999, (1 - m) + H[markets[t]["series"]]))
                          for m, t in zip(mids, use)]
                    c["net_pos_H"] += obs_margins(s, hq, d)[1] > 0
                    if s["relation"] == "complementary":
                        c["overround"].append(sum(mids) - 1)
                # placebo: each used leg from the ticker's previous or next archived run
                real_v = net > 0
                shifted, ok = [], True
                for t in use:
                    seq = seqs[t]
                    i = pos[t][r] + (1 if rng.random() < 0.5 else -1)
                    if i < 0 or i >= len(seq) or q[t][seq[i]] is None:
                        ok = False
                        break
                    shifted.append((q[t][seq[i]][0], q[t][seq[i]][1]))
                gg = c["games"][game]
                gg[0] += 1
                if ok:
                    pv = obs_margins(s, shifted, d)[1] > 0
                    c["paired"] += 1
                    c["plac_viol"] += pv
                    gg[1] += real_v
                    gg[2] += pv
            c["persist_obs"] += persistent(sorted(flags))
    # --- labels
    keys = sorted(cells)
    pv = []
    for k in keys:
        c = cells[k]
        diffs = [gg[1] - gg[2] for gg in c["games"].values()]
        pv.append(signflip_p(diffs) if c["paired"] else 1.0)
    adj = holm(pv)
    out = []
    for k, p, a in zip(keys, pv, adj):
        c = cells[k]
        games = sum(1 for gg in c["games"].values() if gg[0] > 0)
        if games < MIN_GAMES:
            label = "INCONCLUSIVE"
        elif k[1] in bad_edges:
            label = "DROPPED (invalid relation)"
        elif c["net_pos"] == 0:
            label = "NO NET VIOLATION"
        elif c["persist_obs"] > 0 and a < ALPHA:
            label = "SURVIVES"
        else:
            label = "NOT DISTINGUISHABLE FROM TIMING/COST"
        mp = sorted(c["margins_pos"])
        out.append({"relation": k[0], "family": k[1], "direction": k[2], "games": games, "obs": c["obs"],
                    "untestable_obs": c["untestable"], "gross_pos": c["gross_pos"], "net_pos": c["net_pos"],
                    "net_pos_H_sens": c["net_pos_H"], "paired": c["paired"], "placebo_net_pos": c["plac_viol"],
                    "persist_obs": c["persist_obs"], "p_signflip": round(p, 5), "p_holm": round(a, 5),
                    "margin_pos_median": (mp[len(mp) // 2] if mp else None), "margin_pos_max": (mp[-1] if mp else None),
                    "overround_median": (float(np.median(c["overround"])) if c["overround"] else None),
                    "implication_violations_settled": bad_edges.get(k[1], 0), "label": label})
    json.dump({"cells": out, "holm_m": len(keys), "duplicate_rows": dup, "seed": SEED, "flips": FLIPS},
              open(os.path.join(args.out, "d3_results.json"), "w"), indent=1)
    for o in out:
        print(json.dumps(o))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch-meta")
    f.add_argument("--out", default=OUT)
    f.set_defaults(fn=cmd_fetch_meta)
    g = sub.add_parser("group")
    g.add_argument("--out", default=OUT)
    g.add_argument("--archive", default=ARCHIVE)
    g.set_defaults(fn=cmd_group)
    m = sub.add_parser("measure")
    m.add_argument("--out", default=OUT)
    m.add_argument("--archive", default=ARCHIVE)
    m.add_argument("--h-file", default="exp_output/EXP-031-MKT-EFF-SURVEY/d3_d4_results.json")
    m.set_defaults(fn=cmd_measure)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
