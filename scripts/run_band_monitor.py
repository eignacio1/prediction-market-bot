#!/usr/bin/env python3
"""
T-255 — Per-Band Anti-Predictive + Calibration Monitor
GG-099 | GG-100 | GG-098 | Companion to run_exp017_mlb.py / 017b / 017c / ab_harness.py

WHY THIS EXISTS
---------------
GG-099 found the standing edge-monotonicity guard (run_t177_edge_monitor.py) has
zero per-band resolution — it evaluates whatever book it's pointed at as one pool,
so a band with real anti-predictive behavior can hide inside a healthy aggregate
and vice versa. GG-100 then showed what happens when a monitor is built without
care: it read the STORED (YES-frame, wrong-signed for NO bets) fee_net_edge and
raised a false ANTI-PREDICTIVE alarm on the whole T1 book (p=0.0236) when the
direction-aware recompute shows p=0.247 (NOT anti-predictive). That bug is not
repeated here: this monitor NEVER reads a stored edge field. Every edge value is
recomputed via the audited run_exp017_mlb.compute_fee_net_edge() helper, exactly
once, per record — for both the T1/T2/T3 book (via run_exp017b_decomp_mlb's
loader) and the T4M-PROJ ledger (T-254), even though the T4 ledger's own "edge"
column was already computed direction-aware by build_t4_resolved_ledger.py.
Recomputing again here is deliberate defense-in-depth, not redundancy: this
monitor must never depend on any upstream file having gotten the sign right.

WHAT THIS DOES NOT DO
----------------------
This monitor never halts a band. GG-098 (the ab_harness MIN_REMOVED_N lesson)
established that acting on a small-n signal is itself the failure mode — a band
under MIN_N returns UNDERPOWERED, not a verdict, and even ANTI-PREDICTIVE on a
sufficiently large band is a WARNING requiring DS review (T-257), never an
automatic kill. Band-level halts remain a human decision.

COMPOSITION (no reimplementation of fee/edge math)
---------------------------------------------------
  run_exp017_mlb.py          MLBPosition, compute_fee_net_edge, edge_monotonicity
  run_exp017b_decomp_mlb.py  load_records() — T1/T2/T3 book loader (band-tagged)
  run_exp017c_calibration_mlb.py  calib_fit_ci(), ece()
  ab_harness.py              metrics() — EV/bet, $/staked, brier, calib_slope

Bands covered:
  T1, T2, T3    from the band-tagged live MLB book (T-253; band field on every
                closed position since PaperTrader.open_position() threads it).
  T4M-PROJ      from the resolved ledger (T-254; scripts/build_t4_resolved_ledger.py).
  UNTAGGED      catch-all for any resolved position missing a band tag — visibility
                only, never silently dropped.

Run:
  python3 scripts/run_band_monitor.py
  python3 scripts/run_band_monitor.py --portfolio logs/.vps_portfolio_cache_mlb.json \\
      --t4-ledger logs/t4_mlb_resolved_ledger.jsonl
  python3 scripts/run_band_monitor.py --ci    # exit 1 iff any band alarms; warn-only,
                                               # never a kill signal (T-257)

T-322 EXTENSION (2026-07-10, Workstream B) — clean_n only
-----------------------------------------------------------
T-320/T-321 added `logic_epoch`/`approval_commit` write-path provenance so a
resolved position can be identified as opened under clean write-path logic
versus an earlier, contaminated epoch. This monitor's verdict runs on
clean_n only — contaminated records (including records with no `logic_epoch`
at all, i.e. pre-T-320 history) are excluded from every statistic, never
silently blended in. `raw_n` is still reported alongside `clean_n` per band
for transparency, but raw_n never drives a verdict. Also adds `brier_murphy`
(full Brier + Murphy REL/RES/UNC decomposition) and the underlying
`reliability` curve rows to the per-band result, since T-322's exit criterion
explicitly asks for "reliability curve + Brier score", which the pre-T-322
version only partially covered via `ece`/`calib_fit_ci`.

GG-124 REMEDIATION (2026-07-23, Window C, C2) — per-band clean-epoch floors
-----------------------------------------------------------------------------
`filter_clean()` previously compared every band's records against a single
global `CURRENT_LOGIC_EPOCH`, so any write-path fix zeroed every band's
clean_n simultaneously regardless of which band it actually touched — five
such resets landed in ~5 days (2026-07-05 through 2026-07-19), producing a
monitoring-coverage blackout (GG-124). `filter_clean()` now takes `band` and
delegates to `logic_epoch.is_clean_for_band()`, which checks a record's
stamped `logic_epoch` against that specific band's own clean-epoch floor —
derived from which tracked boundaries' resolving commits were verified (via
direct `git show` diff inspection) to actually change that band's write
path. UNTAGGED records keep the conservative global-floor comparison, since
there is no reliable band identity to check them against. See
GOVERNANCE_GAP_LOG.md GG-124, src/prediction_market_bot/logic_epoch.py.

T-341 EXTENSION (2026-07-11, Window 3) — dated artifacts + C7 wiring
-----------------------------------------------------------------------
The T-255/T-257 cron job (Mondays 14:20 UTC — already live, confirmed via
`crontab -l`) was writing only the two fixed-filename outputs below, so each
run silently overwrote the prior week's verdict with no history retained.
Every run now additionally writes a timestamped snapshot to
`exp_output/T255-BAND-MONITOR/verdicts/band_monitor_<UTC-run-id>.json`
(full `results`, not just the summary) so verdict history survives across
runs. The two fixed-filename files remain as the "latest" pointer — nothing
that reads them today needs to change.

Each run also now wires ANTI_PREDICTIVE / calibration-slope-CI-excludes-1
breaches into C7 (`SystemMonitor.report_band_monitor_verdicts()`) as WARNING-
severity, warn-only audit events — mirroring the ADR-0009 shadow_promotion_flag
pattern. This never halts a band; GG-098 established that automated action on
a band-level signal is itself the failure mode. Disable with --no-c7 (e.g. for
ad hoc local runs where a real audit log isn't wanted).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017_mlb as e17                 # noqa: E402  MLBPosition, compute_fee_net_edge, edge_monotonicity
import run_exp017b_decomp_mlb as d17b        # noqa: E402  band-tagged T1/T2/T3 loader
import run_exp017c_calibration_mlb as c17c   # noqa: E402  calib_fit_ci, ece, brier_murphy, reliability
import ab_harness as abh                     # noqa: E402  metrics (EV/bet, $/staked)

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
from prediction_market_bot.logic_epoch import (  # noqa: E402
    CURRENT_LOGIC_EPOCH,
    is_clean_for_band,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402
from prediction_market_bot.c7_monitoring.monitor import SystemMonitor       # noqa: E402

MIN_N = 30  # ab_harness.py band-level floor (GG-098: no acting on ~11 bets)
BOOK_BANDS = ("T1", "T2", "T3")

DEFAULT_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
DEFAULT_T4_LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
OUT_DIR = Path("exp_output/T255-BAND-MONITOR")
DEFAULT_SNAPSHOT_ID = "SNAP-T255-BAND-MONITOR"


# ── record loading ──────────────────────────────────────────────────────────────

def _attach_event(recs: list[dict]) -> None:
    """Reconstruct the binary hit/miss event from direction+outcome (ab_harness's
    exact one-liner) — in place, so callers can pass either loader's output."""
    for r in recs:
        r["_event"] = 1 if ((r["_dir"] == "YES") == (r["_win"] == 1)) else 0


def load_pool_by_band(portfolio_path: Path) -> dict[str, list[dict]]:
    """T1/T2/T3 (+ UNTAGGED) from the band-tagged live MLB book (T-253)."""
    recs = d17b.load_records(portfolio_path)
    _attach_event(recs)
    by_band: dict[str, list[dict]] = {b: [] for b in BOOK_BANDS}
    untagged: list[dict] = []
    for r in recs:
        b = r.get("band")
        if b in by_band:
            by_band[b].append(r)
        else:
            untagged.append(r)
    if untagged:
        by_band["UNTAGGED"] = untagged
    return by_band


def load_t4_ledger(path: Path) -> list[dict]:
    """T4M-PROJ resolved ledger (T-254). JSONL, one row per resolved position.

    GG-077 defense-in-depth: recompute _fne via compute_fee_net_edge() even
    though build_t4_resolved_ledger.py already wrote a direction-aware "edge"
    column — this monitor must never trust an upstream field's sign, full stop.
    """
    recs: list[dict] = []
    if not path.exists():
        return recs
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        p = json.loads(line)
        if p.get("outcome") not in ("WIN", "LOSS") or p.get("model_p") is None:
            continue
        try:
            model_p = float(p["model_p"])
            mip = float(p["mip"])
        except (KeyError, TypeError, ValueError):
            continue
        direction = str(p.get("direction", "YES"))
        r = dict(p)
        r["_model_p"] = model_p
        r["_mip"] = mip
        r["_dir"] = direction
        r["_win"] = 1 if p.get("outcome") == "WIN" else 0
        r["_pnl"] = float(p.get("pnl", 0.0) or 0.0)
        r["_size"] = float(p.get("size_usd", 0.0) or 0.0)
        r["_fne"] = e17.compute_fee_net_edge(direction, model_p, mip)  # never trust p["edge"]
        try:
            r["_thr"] = int(p.get("threshold", 0) or 0)
        except (TypeError, ValueError):
            r["_thr"] = 0
        recs.append(r)
    _attach_event(recs)
    return recs


def to_mlb_positions(recs: list[dict]) -> list[e17.MLBPosition]:
    """Adapter into e17.MLBPosition so edge_monotonicity() runs bit-for-bit
    identical logic to EXP-017, regardless of which loader produced `recs`."""
    positions = []
    for r in recs:
        vig = float(r.get("vig_at_entry", r.get("vig", 0.0)) or 0.0)
        positions.append(e17.MLBPosition(
            kalshi_ticker=str(r.get("kalshi_ticker", "")),
            direction=r["_dir"],
            mip=r["_mip"],
            vig=vig,
            model_p=r["_model_p"],
            fee_net_edge=r["_fne"],
            outcome="WIN" if r["_win"] else "LOSS",
            pnl=r["_pnl"],
            game_date=str(r.get("game_date", "")),
            threshold=int(r.get("_thr", 0) or 0),
            player_name=str(r.get("player_name", "")),
            player_id=r.get("player_id"),
            position_id=r.get("position_id"),
            logic_epoch=r.get("logic_epoch"),
        ))
    return positions


# ── clean_n filtering (T-322) ────────────────────────────────────────────────────

def filter_clean(recs: list[dict], band: str) -> list[dict]:
    """Keep only records whose write-path is clean for `band` specifically
    (T-320/T-321, per-band remediation GG-124/Window C 2026-07-23).

    Previously this compared `logic_epoch` against the single global
    CURRENT_LOGIC_EPOCH, so any write-path fix — even one verified to touch
    only one band — zeroed every band's clean_n simultaneously (five such
    resets landed in ~5 days, a monitoring-coverage blackout; GG-124). Now
    each band is compared against its own clean-epoch floor
    (`logic_epoch.clean_epoch_floor_for_band()`), which only advances when a
    boundary's verified diff actually touched that band's write path — a fix
    scoped to one band no longer discards another band's already-clean
    cohort. UNTAGGED records (no reliable band identity) still use the
    conservative global floor via `CURRENT_LOGIC_EPOCH`, since there is no
    band-specific floor to check them against.

    Records with no `logic_epoch` at all (pre-T-320 history) are still
    excluded — `is_clean_for_band()` treats `None` as not clean."""
    if band == "UNTAGGED":
        return [r for r in recs if r.get("logic_epoch") == CURRENT_LOGIC_EPOCH]
    return [r for r in recs if is_clean_for_band(r.get("logic_epoch"), band)]


# ── per-band analysis ────────────────────────────────────────────────────────────

def analyze_band(
    band: str,
    recs: list[dict],
    bins: int = 5,
    boot: int = 10000,
    seed: int = 17,
    alpha: float = 0.10,
) -> dict:
    raw_n = len(recs)
    clean_recs = filter_clean(recs, band)
    clean_n = len(clean_recs)
    if clean_n < MIN_N:
        return {
            "band": band,
            "verdict": "UNDERPOWERED",
            "raw_n": raw_n,
            "clean_n": clean_n,
            "n": clean_n,
            "min_n": MIN_N,
            "reason": f"clean_n={clean_n} < MIN_N={MIN_N} (raw_n={raw_n}) — GG-098 "
                      f"discipline: too few bets resolved under this band's own "
                      f"clean-epoch floor to return a verdict, not just a "
                      f"low-confidence one (GG-124 per-band floors). Pre-fix-epoch "
                      f"bets are excluded, never blended in to reach the floor.",
            "anti_predictive_alarm": False,
        }

    positions = to_mlb_positions(clean_recs)
    mono = e17.edge_monotonicity(positions, alpha=alpha)
    rng = random.Random(seed)
    fit = c17c.calib_fit_ci(clean_recs, boot, rng)
    ece_val = c17c.ece(clean_recs, bins)
    bm = c17c.brier_murphy(clean_recs, bins)
    rel_curve = c17c.reliability(clean_recs, bins)
    m = abh.metrics(clean_recs)
    anti_predictive_alarm = mono["verdict"] == e17.E_ANTI

    return {
        "band": band,
        "verdict": "ANALYZED",
        "raw_n": raw_n,
        "clean_n": clean_n,
        "n": clean_n,
        "edge_monotonicity": mono,
        "calibration": fit,
        "ece": ece_val,
        "brier_murphy": bm,
        "reliability_curve": rel_curve,
        "ev_per_bet_usd": m["ev_per_bet_usd"],
        "pnl_per_dollar": m["pnl_per_dollar"],
        "win_rate": m["win_rate"],
        "total_pnl": m["total_pnl"],
        "anti_predictive_alarm": anti_predictive_alarm,
    }


def run_all_bands(
    portfolio_path: Path,
    t4_ledger_path: Path,
    bins: int = 5,
    boot: int = 10000,
    seed: int = 17,
    alpha: float = 0.10,
) -> dict[str, dict]:
    results: dict[str, dict] = {}

    by_band = load_pool_by_band(portfolio_path)
    for band in BOOK_BANDS:
        results[band] = analyze_band(band, by_band.get(band, []), bins, boot, seed, alpha)
    if "UNTAGGED" in by_band:
        results["UNTAGGED"] = analyze_band("UNTAGGED", by_band["UNTAGGED"], bins, boot, seed, alpha)

    t4_recs = load_t4_ledger(t4_ledger_path)
    if t4_recs or t4_ledger_path.exists():
        results["T4M-PROJ"] = analyze_band("T4M-PROJ", t4_recs, bins, boot, seed, alpha)
    else:
        results["T4M-PROJ"] = {
            "band": "T4M-PROJ", "verdict": "NO_DATA", "n": 0,
            "reason": f"ledger not found: {t4_ledger_path} — run "
                      f"scripts/build_t4_resolved_ledger.py first",
            "anti_predictive_alarm": False,
        }

    return results


# ── reporting ────────────────────────────────────────────────────────────────────

def build_summary(results: dict[str, dict]) -> dict[str, dict]:
    """T-322 exit criterion: one compact {band -> {verdict, p, brier, n}} emission
    for the current epoch (clean_n only). UNDERPOWERED/NO_DATA bands still get an
    entry — p/brier are null rather than the band being silently omitted, so a
    thin band is visible, not invisible."""
    summary: dict[str, dict] = {}
    for band, r in results.items():
        verdict = r.get("verdict")
        if verdict == "ANALYZED":
            summary[band] = {
                "verdict": r["edge_monotonicity"]["verdict"],
                "p": r["edge_monotonicity"].get("fisher_pvalue"),
                "brier": r["brier_murphy"]["brier_full"],
                "n": r["clean_n"],
            }
        else:
            summary[band] = {
                "verdict": verdict,
                "p": None,
                "brier": None,
                "n": r.get("clean_n", r.get("n", 0)),
            }
    return summary


def _print_report(results: dict[str, dict]) -> None:
    print("=" * 96)
    print("T-255/T-322 PER-BAND ANTI-PREDICTIVE + CALIBRATION MONITOR  (GG-099, clean_n only)")
    print("=" * 96)
    for band, r in results.items():
        verdict = r["verdict"]
        if verdict == "UNDERPOWERED":
            print(f"\n[{band}] UNDERPOWERED  clean_n={r['clean_n']} raw_n={r['raw_n']} "
                  f"(clean_n < MIN_N={r['min_n']}) — {r['reason']}")
            continue
        if verdict == "NO_DATA":
            print(f"\n[{band}] NO_DATA — {r['reason']}")
            continue
        mono = r["edge_monotonicity"]
        fit = r["calibration"]
        bm = r["brier_murphy"]
        alarm = " *** ANTI_PREDICTIVE WARNING ***" if r["anti_predictive_alarm"] else ""
        print(f"\n[{band}] clean_n={r['clean_n']}  (raw_n={r['raw_n']}){alarm}")
        print(f"  edge_monotonicity: {mono['verdict']}  "
              f"(fisher_p={mono.get('fisher_pvalue', float('nan')):.4f}, "
              f"n_pos_edge={mono.get('n_pos_edge')}, n_neg_edge={mono.get('n_neg_edge')}, "
              f"winrate_pos={mono.get('winrate_edge_pos', float('nan')):.3f}, "
              f"winrate_neg={mono.get('winrate_edge_neg', float('nan')):.3f})")
        print(f"  calibration: slope_b={fit['slope_b']:.3f} b_ci={[round(x, 3) for x in fit['b_ci']]} "
              f"({fit['interpretation']}, excludes_1={fit['b_excludes_1']})  ECE={r['ece']:.4f}")
        print(f"  brier: full={bm['brier_full']:.4f} binned={bm['brier_binned']:.4f} "
              f"REL={bm['reliability']:.4f} RES={bm['resolution']:.4f} UNC={bm['uncertainty']:.4f} "
              f"base_rate={bm['base_rate']:.3f}")
        print(f"  EV/bet=${r['ev_per_bet_usd']:+.4f}  $/staked={r['pnl_per_dollar']*100:+.2f}%  "
              f"win_rate={r['win_rate']:.3f}  total_pnl=${r['total_pnl']:+.2f}")
    print("\n" + "=" * 96)
    alarmed = [b for b, r in results.items() if r.get("anti_predictive_alarm")]
    if alarmed:
        print(f"WARNING (warn-only, no auto-kill): ANTI-PREDICTIVE flagged for band(s): "
              f"{', '.join(alarmed)} — requires DS review before any capital/allocation "
              f"decision touches this band (GG-098 lesson).")
    else:
        print("No band flagged ANTI-PREDICTIVE this run.")
    print("=" * 96)
    summary = build_summary(results)
    print("\nSUMMARY {band -> verdict, p, brier, n} (current epoch, clean_n only):")
    print(json.dumps(summary, indent=2))


# ── dated artifact + C7 wiring (T-341) ──────────────────────────────────────────

def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_dated_verdict(results: dict[str, dict], out_dir: Path, run_id: str) -> Path:
    """Write a timestamped, never-overwritten snapshot of the full per-band
    results alongside the fixed-filename 'latest' outputs (T-341)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dated_path = out_dir / f"band_monitor_{run_id}.json"
    dated_path.write_text(json.dumps(
        {"run_id": run_id, "results": results, "summary": build_summary(results)},
        indent=2,
    ))
    return dated_path


def wire_c7(
    results: dict[str, dict],
    audit_log_path: Path,
    session_id: str,
    snapshot_id: str = DEFAULT_SNAPSHOT_ID,
) -> list[str]:
    """Emit warn-only C7 alarms for any ANALYZED band that alarms
    ANTI_PREDICTIVE or has a calibration slope CI excluding 1.0 (T-341,
    GG-099/GG-100/GG-098). Never halts a band — see
    SystemMonitor.report_band_monitor_verdicts() docstring."""
    logger = AuditLogger(audit_log_path, min_severity="INFO")
    monitor = SystemMonitor(logger=logger, snapshot_id=snapshot_id, session_id=session_id)
    return monitor.report_band_monitor_verdicts(results, session_id=session_id)


# ── CLI ──────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="T-255/T-322 per-band anti-predictive + calibration monitor (GG-099, clean_n only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO,
                    help=f"Band-tagged T1/T2/T3 MLB portfolio JSON (default: {DEFAULT_PORTFOLIO})")
    p.add_argument("--t4-ledger", type=Path, default=DEFAULT_T4_LEDGER,
                    help=f"T4M-PROJ resolved ledger JSONL (default: {DEFAULT_T4_LEDGER})")
    p.add_argument("--bins", type=int, default=5)
    p.add_argument("--boot", type=int, default=10000)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--alpha", type=float, default=0.10)
    p.add_argument("--out", type=Path, default=OUT_DIR)
    p.add_argument("--ci", action="store_true",
                   help="CI mode: exit 1 iff any band alarms ANTI-PREDICTIVE. "
                        "Warn-only signal — never a kill trigger (T-257).")
    p.add_argument("--no-c7", action="store_true",
                   help="Skip C7 audit wiring (T-341) — e.g. ad hoc local runs "
                        "where writing to the real audit log isn't wanted.")
    p.add_argument("--audit-log", type=Path,
                   default=Path("logs/audit_mlb.jsonl"),
                   help="C6 audit log path for C7 wiring (default: logs/audit_mlb.jsonl)")
    p.add_argument("--session-id", type=str, default=None,
                   help="Session ID to attach to C7 events (default: auto-generated "
                        "SES-BAND-MONITOR-<run_id>)")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    results = run_all_bands(args.portfolio, args.t4_ledger, args.bins, args.boot,
                             args.seed, args.alpha)

    run_id = _run_id()

    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "band_monitor_results.json"
    out_json.write_text(json.dumps(results, indent=2))
    summary_json = args.out / "band_monitor_summary.json"
    summary_json.write_text(json.dumps(build_summary(results), indent=2))
    dated_path = write_dated_verdict(results, args.out / "verdicts", run_id)

    _print_report(results)
    print(f"\nWrote {out_json}")
    print(f"Wrote {summary_json}")
    print(f"Wrote {dated_path}  (dated verdict artifact, T-341)")

    if not args.no_c7:
        session_id = args.session_id or f"SES-BAND-MONITOR-{run_id}"
        alarmed = wire_c7(results, args.audit_log, session_id)
        if alarmed:
            print(f"\n[C7] WARNING events emitted (warn-only, no auto-kill) for band(s): "
                  f"{', '.join(alarmed)} — see {args.audit_log}")
        else:
            print(f"\n[C7] No band alarmed this run — no events emitted to {args.audit_log}")

    if args.ci:
        any_alarm = any(r.get("anti_predictive_alarm") for r in results.values())
        return 1 if any_alarm else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
