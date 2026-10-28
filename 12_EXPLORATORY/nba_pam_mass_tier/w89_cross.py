"""W89.5 Part B - EXPLORATORY. Does a player's PAM role explain where the KXNBAPTS price is wrong?

Market-anchored: the unit is a settled strike. y = 1[points > strike]; p = the market's own mid. A role is tested by (1) the mean
residual y - p for players with the role (a calibration gap *of the price*, not whether the role predicts points), and (2) out-of-sample
by date: anchor-only vs anchor + role logistic adjustment, Brier difference, game-clustered interval. BH across roles.

Roles are the 2025-26 season-end flags (taxonomy v4, unedited), strictly before every 2026-27 game. No threshold chosen from outcomes:
the roles tested are PRF-1 and PRF-4 (W84.2's stable subset, fixed in advance) plus any other PRF/M row whose joined count clears the
counts-only floor below (N_PLAYERS_MIN players, N_MARKETS_MIN strikes).

    PYTHONPATH=<repo>/src:<repo>/12_EXPLORATORY python3 w89_cross.py --join results/w89/join_rows.json --pam <season_end.jsonl> --out nba_pam_mass_tier/results/w89
"""
import argparse
import json
import math
import re
from collections import defaultdict

from _fence import safe_out
from prediction_market_bot.quant.inference import benjamini_hochberg, cluster_bootstrap, mde_paired
from prediction_market_bot.quant.scoring import brier_diff

PRIMARY = ("PRF-1", "PRF-4")
N_PLAYERS_MIN, N_MARKETS_MIN = 8, 60
MAX_SPREAD = 0.10   # a quote is usable when two-sided and at most this wide
MET = ("MET", "MET_PARTIAL")


def norm(s):
    from w89_join import norm as n
    return n(s)


ANCHOR_MODE = "first"   # "first": first usable quote after open (fixed before the run); "last_pretip": last usable quote at/before tip (sensitivity)


def _tip(r):
    import datetime as dt
    return int(dt.datetime.fromisoformat(re.sub(r"Z$", "+00:00", r["tip_utc"])).timestamp())


def anchor(r):
    """Usable = two-sided and at most MAX_SPREAD wide. first: earliest usable quote; last_pretip: latest usable quote with ts <= tip."""
    ok = [(ts, (bid + ask) / 2) for ts, bid, ask, _px, _v in r["candles"]
          if bid is not None and ask is not None and 0.0 < bid and ask < 1.0 and ask - bid <= MAX_SPREAD]
    if ANCHOR_MODE == "last_pretip":
        ok = [x for x in ok if x[0] <= _tip(r)]
        return ok[-1] if ok else None
    return ok[0] if ok else None


def logit(p):
    p = min(max(p, 1e-3), 1 - 1e-3)
    return math.log(p / (1 - p))


def fit_logit(X, y, l2=1.0, iters=60):
    """Ridge logistic by Newton; X rows include the intercept column. Applies for small n with few columns."""
    k = len(X[0])
    w = [0.0] * k
    for _ in range(iters):
        g = [-l2 * w[j] if j else 0.0 for j in range(k)]
        H = [[(l2 if (i == j and i) else 0.0) for j in range(k)] for i in range(k)]
        for xi, yi in zip(X, y):
            z = sum(a * b for a, b in zip(w, xi))
            p = 1 / (1 + math.exp(-z))
            for j in range(k):
                g[j] += (yi - p) * xi[j]
                for l in range(k):
                    H[j][l] += p * (1 - p) * xi[j] * xi[l]
        # solve H d = g (Gauss)
        A = [H[i][:] + [g[i]] for i in range(k)]
        for i in range(k):
            piv = max(range(i, k), key=lambda r: abs(A[r][i]))
            A[i], A[piv] = A[piv], A[i]
            for r in range(k):
                if r != i and A[i][i]:
                    f = A[r][i] / A[i][i]
                    A[r] = [a - f * b for a, b in zip(A[r], A[i])]
        d = [A[i][k] / A[i][i] if A[i][i] else 0.0 for i in range(k)]
        w = [a + b for a, b in zip(w, d)]
        if max(abs(x) for x in d) < 1e-8:
            break
    return w


def two_sided_p(vals_by_game, b=4000, seed=20261027):
    """Bootstrap p for mean == 0 by centred game resampling. Applies to game-clustered residuals."""
    import random
    games = list(vals_by_game)
    allv = [v for g in games for v in vals_by_game[g]]
    mean = sum(allv) / len(allv)
    cen = {g: [x - mean for x in vals_by_game[g]] for g in games}
    rng = random.Random(seed)
    hits = 0
    for _ in range(b):
        s = n = 0
        for _ in games:
            c = cen[games[rng.randrange(len(games))]]
            s += sum(c)
            n += len(c)
        if abs(s / n) >= abs(mean):
            hits += 1
    return (hits + 1) / (b + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--join", required=True)
    ap.add_argument("--pam", required=True)
    ap.add_argument("--out", default="nba_pam_mass_tier/results/w89")
    ap.add_argument("--anchor", default="first", choices=["first", "last_pretip"])
    a = ap.parse_args()
    global ANCHOR_MODE
    ANCHOR_MODE = a.anchor
    rows = json.load(open(a.join))
    pam = {}
    for l in open(a.pam):
        r = json.loads(l)
        if r["season"] == 2026:
            pam[norm(r["name"])] = r
    use, drop = [], defaultdict(int)
    for r in rows:
        if r["pts"] is None:
            drop["no_stat_line"] += 1
            continue
        an = anchor(r)
        if an is None:
            drop["no_usable_quote"] += 1
            continue
        r["anchor_ts"], r["p"] = an
        r["y"] = r["result_yes"]
        pr = pam.get(r["key"])
        r["pam"] = pr
        use.append(r)
    no_pam = sorted({r["player"] for r in use if not r["pam"]})
    roles = set(PRIMARY)
    cnt = defaultdict(lambda: [set(), 0])
    for r in use:
        if not r["pam"]:
            continue
        for k, v in list(r["pam"]["factors"].items()) + list(r["pam"]["modifiers"].items()):
            if v["status"] in MET:
                cnt[k][0].add(r["key"]); cnt[k][1] += 1
    for k, (pl, nm) in cnt.items():
        if len(pl) >= N_PLAYERS_MIN and nm >= N_MARKETS_MIN:
            roles.add(k)
    flag = lambda r, k: bool(r["pam"]) and (r["pam"]["factors"].get(k) or r["pam"]["modifiers"].get(k) or {}).get("status") in MET
    dates = sorted({r["date"] for r in use})
    out = {"n_markets_joined": len(rows), "n_usable": len(use), "dropped": dict(drop), "n_games": len({r["espn_id"] for r in use}),
           "dates": dates, "players_without_pam_2026": no_pam, "share_with_pam": round(sum(1 for r in use if r["pam"]) / max(len(use), 1), 4),
           "anchor_overall": {"mean_p": sum(r["p"] for r in use) / len(use), "mean_y": sum(r["y"] for r in use) / len(use)}}
    res, pvals = [], []
    for k in sorted(roles):
        grp = [r for r in use if flag(r, k)]
        byg = defaultdict(list)
        for r in grp:
            byg[r["espn_id"]].append(r["y"] - r["p"])
        if not grp:
            res.append({"role": k, "n_markets": 0, "n_players": 0, "primary": k in PRIMARY, "note": "no joined strikes"})
            pvals.append(1.0)
            continue
        m, lo, hi = cluster_bootstrap(byg)
        p2 = two_sided_p(byg)
        # out of sample by date: expanding window, anchor-only vs anchor + role
        d_by_game = defaultdict(list)
        for i, d in enumerate(dates[1:], 1):
            tr = [r for r in use if r["date"] < d]
            te = [r for r in use if r["date"] == d]
            if len(tr) < 100 or not te:
                continue
            w0 = fit_logit([[1, logit(r["p"])] for r in tr], [r["y"] for r in tr])
            w1 = fit_logit([[1, logit(r["p"]), float(flag(r, k))] for r in tr], [r["y"] for r in tr])
            for r in te:
                z0 = w0[0] + w0[1] * logit(r["p"]); z1 = w1[0] + w1[1] * logit(r["p"]) + w1[2] * flag(r, k)
                p0, p1 = 1 / (1 + math.exp(-z0)), 1 / (1 + math.exp(-z1))
                d_by_game[r["espn_id"]].append(brier_diff([p0], [p1], [r["y"]])[0])
        oos = None
        if d_by_game:
            om, olo, ohi = cluster_bootstrap(d_by_game)
            allv = [v for g in d_by_game.values() for v in g]
            sd = (sum((x - om) ** 2 for x in allv) / max(len(allv) - 1, 1)) ** 0.5
            oos = {"n": len(allv), "n_games": len(d_by_game), "brier_diff_anchor_minus_adj": om, "ci95": [olo, ohi],
                   "sd": sd, "mde_at_n": mde_paired(sd, len(allv)) if len(allv) > 1 else None}
        res.append({"role": k, "primary": k in PRIMARY, "n_markets": len(grp), "n_players": len({r["key"] for r in grp}),
                    "n_games": len(byg), "mean_resid_y_minus_p": m, "ci95": [lo, hi], "p_two_sided": p2, "oos": oos})
        pvals.append(p2)
    keep = benjamini_hochberg(pvals, q=0.10)
    for r, kp in zip(res, keep):
        r["bh_q10_survives"] = bool(kp)
    out["roles"] = res
    # pooled reference group: players with no role MET among roles tested
    out["n_roles_tested"] = len(res)
    json.dump(out, open(safe_out(f"{a.out}/cross_{a.anchor}.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "roles"}, indent=1)[:2500])
    for r in res:
        print(r["role"], r["n_markets"], r.get("n_players"), None if "mean_resid_y_minus_p" not in r else round(r["mean_resid_y_minus_p"], 4),
              r.get("ci95") and [round(x, 3) for x in r["ci95"]], r.get("p_two_sided") and round(r["p_two_sided"], 3), r["bh_q10_survives"])


if __name__ == "__main__":
    main()
