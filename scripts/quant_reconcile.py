"""W87.1 Part A: old scoring path vs the quant core on one frozen, seeded snapshot.

Each row: path, case, old value, core value, |difference|, verdict, reason. MATCH = |diff| < TOL (1e-6).
Only MATCH rows may be re-pointed (Part B). DEFINITION rows are two different, both-defensible definitions;
BUG rows are registered, and fixed only if the bug is in the core. Pure; no I/O, no network, no ledger read.
Run: PYTHONPATH=src:scripts python3 scripts/quant_reconcile.py
"""
from __future__ import annotations

import random
import sys
from types import SimpleNamespace as NS

TOL = 1e-6
SEED = 7


def snapshot() -> dict:
    """Frozen input: 500 seeded probabilities plus the float-edge values (0, 1, decile edges, 0.5 push)."""
    rng = random.Random(SEED)
    ps = [rng.random() for _ in range(500)] + [0.0, 1.0, 0.3, 0.7, 0.1, 0.2, 0.5, 0.9, 0.57, 0.58, 0.29]
    ys = [1.0 if rng.random() < p * 0.8 + 0.1 else 0.0 for p in ps]
    byg = {f"g{i}": [rng.gauss(0, 1) for _ in range(rng.randint(1, 6))] for i in range(40)}
    quotes = []
    for _ in range(2000):
        bid = rng.random() * 0.9
        quotes.append((rng.random(), bid, min(0.99, bid + rng.random() * 0.1)))
    return {"ps": ps, "ys": ys, "byg": byg, "quotes": quotes}


def _row(path, case, old, core, verdict, reason):
    return {"path": path, "case": case, "old": old, "core": core, "diff": abs(old - core), "verdict": verdict, "reason": reason}


def _classify(diff, if_diff, reason_match, reason_diff):
    return ("MATCH", reason_match) if diff < TOL else (if_diff, reason_diff)


def reconcile() -> list[dict]:
    from prediction_market_bot import quant as Q
    from prediction_market_bot import t4_fill_status as tfs
    from prediction_market_bot.analytics import calibration_diagnostics as cd
    from prediction_market_bot.c7_monitoring import monitor as mon
    from prediction_market_bot.pregame_shadow import fees, scoring
    import nhl_shadow_eval as nse
    import demo_fill_forward_report as dfr

    s = snapshot()
    ps, ys, byg, quotes = s["ps"], s["ys"], s["byg"], s["quotes"]
    recs = [{"_model_p": p, "_event": int(y)} for p, y in zip(ps, ys)]
    out: list[dict] = []

    # fees / edge: pregame_shadow.fees.e_net and nhl_shadow_eval.edge_net vs quant.money.net_edge
    for path, fn in (("pregame_shadow/fees.py e_net", lambda p, b, a: fees.e_net(p, b, a, fees.fee_k007)),
                     ("scripts/nhl_shadow_eval.py edge_net", lambda p, b, a: nse.edge_net(p, b, a, 0.07))):
        mx = 0.0
        for p, b, a in quotes:
            o, c = fn(p, b, a), Q.net_edge(p, b, a)
            mx = max(mx, abs(o[0] - c["yes"]), abs(o[1] - c["no"]))
        out.append(_row(path, f"{len(quotes)} random quotes, max over YES and NO", mx, 0.0, "MATCH" if mx < TOL else "BUG",
                        "same formula p - ask - fee(ask) / (1-p) - (1-bid) - fee(1-bid)"))

    # bootstrap CIs: t4_fill_status (E2/E3), scoring (pre-registered looks)
    for path, old, kw in (("t4_fill_status.py cluster_bootstrap_ci", tfs.cluster_bootstrap_ci(byg), dict(b=4000, seed=20261009)),
                          ("pregame_shadow/scoring.py cluster_bootstrap_ci", scoring.cluster_bootstrap_ci(byg), dict(b=scoring.BOOT_B, seed=scoring.BOOT_SEED))):
        _, lo, hi = Q.cluster_bootstrap(byg, **kw)
        for nm, o, c in (("lo", old[-2], lo), ("hi", old[-1], hi)):
            d = abs(o - c)
            v, r = _classify(d, "ROUNDING" if d < 1e-4 else "BUG", "same percentile algorithm, same B and seed",
                             "old path rounds to 4 dp (output formatting); algorithm identical")
            out.append(_row(path, f"40 clusters, {nm}", o, c, v, r))
    out.append({"path": "t4_fill_status.py cluster_bootstrap_ci", "case": "edge cases", "old": "None for <2 clusters, empty clusters dropped",
                "core": "single cluster returns a point interval", "diff": float("nan"), "verdict": "DEFINITION",
                "reason": "re-point must keep the wrapper's guard (<2 non-empty clusters -> None); E2/E3 print None today"})

    # calibration_diagnostics vs core, per bin count
    for bins in (5, 10, 20, 25):
        e1, e2 = cd.ece(recs, bins), Q.ece(ps, ys, bins)
        m1, m2 = cd.brier_murphy(recs, bins), Q.murphy(ps, ys, bins)
        nbad = sum(1 for a, b in zip(cd.reliability(recs, bins), Q.reliability_bins(ps, ys, bins)) if a["n"] != b["n"])
        d = max(abs(e1 - e2), abs(m1["reliability"] - m2["reliability"]), abs(m1["resolution"] - m2["resolution"]), float(nbad))
        out.append(_row("analytics/calibration_diagnostics.py ece/reliability/murphy", f"{bins} bins; ECE, reliability, resolution, bin counts",
                        d, 0.0, "MATCH" if d < TOL else "BUG", "same int(p*bins) binning with p=1 folded into the top bin"))

    # irls_logistic vs slope_intercept
    a1, b1 = cd.irls_logistic([cd.logit(p) for p in ps], [int(y) for y in ys])
    a2, b2 = Q.slope_intercept(ps, ys)
    for nm, o, c in (("slope", a1, a2), ("intercept", b1, b2)):
        d = abs(o - c)
        v, r = _classify(d, "DEFINITION", "identical fit", "logit clamp EPS=1e-9 on p=0 and p=1 rows differs from the core's clamp, and "
                         "the stopping tolerance differs; both fit the same model. The pre-registrations use the core's (slope, intercept)")
        out.append(_row("analytics/calibration_diagnostics.py irls_logistic", f"{nm}, snapshot incl. p=0 and p=1", o, c, v, r))

    # monitor ECE (live ADR-0004 drift ladder)
    rr = [NS(p_estimate=p, outcome=y) for p, y in zip(ps, ys)]
    o, c = mon._compute_ece(rr), Q.ece(ps, ys, mon._ECE_N_BINS)
    out.append(_row("c7_monitoring/monitor.py _compute_ece", f"{mon._ECE_N_BINS} bins, snapshot incl. 0.3/0.7/0.57/0.58",
                    o, c, *_classify(abs(o - c), "DEFINITION",
                                     "same", "np.linspace edges are inexact floats (linspace(0,1,11)[3] = 0.30000000000000004), so p=0.3 lands in bin 2 here and bin 3 in the core's int(p*n). "
                                             "Matters for probabilities rounded to 0.1/0.01. Not re-pointed: live drift ladder, c7 not owned by 87.1")))

    # demo_fill_forward_report analytic clustered mean/CI vs bootstrap (means must agree; intervals are a different estimator)
    cl = dfr._clustered(byg)
    mean_core = Q.cluster_bootstrap(byg, b=200, seed=1)[0]
    out.append(_row("scripts/demo_fill_forward_report.py _clustered", "cluster ratio-estimator mean", cl["mean"], mean_core,
                    *_classify(abs(cl["mean"] - mean_core), "BUG", "same pooled mean", "point estimates differ")))
    lo_b, hi_b = Q.cluster_bootstrap(byg, b=2000, seed=1)[1:]
    half_an = dfr.Z95 * cl["var"] ** 0.5
    out.append(_row("scripts/demo_fill_forward_report.py _clustered", "one-sided 95% half-width: analytic vs bootstrap",
                    half_an, (hi_b - lo_b) / 2 * (1.645 / 1.96), "DEFINITION",
                    "analytic ratio-estimator (Z=1.645, one-sided) vs percentile bootstrap (two-sided 95%). Both cluster by game. "
                    "The forward-test rule in its own pre-registration uses the analytic one; keep it"))

    # scoring side choice
    diffs = 0
    for p, b, a in quotes:
        r = {"p_yes": p, "yes_bid": b, "yes_ask": a}
        for y in (0.0, 1.0):
            old = scoring._best_side_e_net(r, y, fees.fee_k007)
            n = Q.net_edge(p, b, a)
            core_y = y - a - fees.fee_k007(a)
            core_n = (1 - y) - (1 - b) - fees.fee_k007(1 - b)
            core = core_y if n["yes"] >= n["no"] else core_n
            diffs += abs(old - core) > TOL
    out.append(_row("pregame_shadow/scoring.py _best_side_e_net", f"{len(quotes)*2} quote/outcome pairs; rows where the side differs",
                    float(diffs), 0.0, "DEFINITION" if diffs else "MATCH",
                    "scoring picks the side by GROSS edge (p-ask vs (1-p)-(1-bid)); core net_edge picks by NET edge. The pre-registered EXP-036/037 realised E_net uses the gross choice; keep it"))
    return out


def markdown(rows: list[dict]) -> str:
    h = "| path | case | old | core | diff | verdict | reason |\n|---|---|---|---|---|---|---|\n"
    f = lambda v: f"{v:.3g}" if isinstance(v, float) else str(v)
    return h + "\n".join(f"| {r['path']} | {r['case']} | {f(r['old'])} | {f(r['core'])} | {f(r['diff'])} | {r['verdict']} | {r['reason']} |" for r in rows)


if __name__ == "__main__":
    print(markdown(reconcile()))
    sys.exit(0)
