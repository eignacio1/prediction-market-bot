#!/usr/bin/env python3
"""
Phase 0 — Kalshi market universe survey: depth sampler + classifier.

Spec:   02_ARCHITECTURE_DESIGN/MARKET_UNIVERSE_SURVEY_SPEC.md section 2
Status: read-only. Places no orders. Never writes to any portfolio, ledger,
        logic_epoch register, or live config.

Two subcommands, deliberately split by execution context:

  depth     Samples orderbooks per market family (section 2.3). Requires an
            authenticated Kalshi session from the datacenter IP, so this runs
            on the VPS. Consumes Phase 0-A's markets_sample.json.

  classify  Consumes Phase 0-A's raw dumps plus (optionally) the depth output
            and emits the four spec tables. Pure data transformation, no
            network, runs anywhere.

Usage
-----
    # on the VPS, after Phase 0-A raw capture:
    python3 scripts/phase0_market_survey.py depth \\
        --in exp_output/PHASE0_SURVEY/markets_sample.json \\
        --out exp_output/PHASE0_SURVEY/depth_sample.json \\
        --per-family 20

    # anywhere:
    python3 scripts/phase0_market_survey.py classify \\
        --series exp_output/PHASE0_SURVEY/series_all.json \\
        --markets exp_output/PHASE0_SURVEY/markets_sample.json \\
        --depth exp_output/PHASE0_SURVEY/depth_sample.json \\
        --out exp_output/PHASE0_SURVEY/SURVEY_TABLES.md

Depth gate (spec section 2.7)
-----------------------------
A family fails the gate when measured depth is below DEPTH_GATE_MULTIPLE x the
intended per-bet stake. Intended stake is taken from the live measurement
regime (ADR-0050: T4_MEASUREMENT_STAKE_USD = $1.00, capped at
T4_MEASUREMENT_MAX_CONTRACTS = 10 contracts), overridable via --stake so the
gate can be re-evaluated against a future sizing decision without editing code.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

DEPTH_GATE_MULTIPLE = 10.0
DEFAULT_INTENDED_STAKE_USD = 1.00
REQUEST_PAUSE_S = 0.12          # ~8 req/s: inside Basic tier (~20 req/s) with margin
MAX_RETRIES = 5

# Family classification is applied to the series ticker. Ordered: first match
# wins, so specific patterns precede general ones. Anything unmatched lands in
# UNCLASSIFIED and is reported rather than silently dropped -- an unmatched
# series is a finding, not noise.
FAMILY_PATTERNS: list[tuple[str, str]] = [
    # MLBKS (strikeouts prop) and MLBF3/F5/F7 (partial-game winners) were found
    # missing entirely from this classifier (both landed UNCLASSIFIED) during
    # the 2026-07-31 Phase 0-B session's hand review of the "220 MLB-looking
    # series" search space -- matched on the MLB-prefixed ticker token rather
    # than a bare "KS"/"F3" pattern, since those short tokens collide with
    # unrelated tickers (e.g. NHL "KNICKS"-style substrings, generic "F3"
    # noise) that have nothing to do with strikeouts or partial-game winners.
    ("PLAYER_PROP", r"(HIT|PTS|STRIKEOUT|MLBKS|HR|TOTALBASE|RBI|ASSIST|REBOUND|PASSYD|RUSHYD)"),
    ("SEASON_WIN_TOTAL", r"(SEASONWIN|WINTOTAL|WINS)"),
    ("TEAM_TOTAL", r"(TEAMTOTAL|TEAMRUN|TEAMSCORE)"),
    ("GAME_TOTAL", r"(TOTAL|OVERUNDER|RUNS|POINTS)"),
    ("RUN_LINE", r"(RUNLINE|SPREAD|HANDICAP|LINE)"),
    # Must sit after GAME_TOTAL/RUN_LINE: KXMLBF5TOTAL and KXMLBF5SPREAD are
    # partial-game TOTAL/RUN_LINE variants, not partial-game winner markets,
    # and need to be caught by those patterns first. Only a bare KXMLBF3/F5/F7
    # (no TOTAL/SPREAD suffix) is a genuine partial-game winner market.
    ("PARTIAL_GAME_WINNER", r"MLBF[357]"),
    ("GAME_WINNER", r"(GAME|WINNER|WIN|MATCH)"),
]

SPORT_PATTERNS: list[tuple[str, str]] = [
    ("MLB", r"MLB|BASEBALL"),
    ("NBA", r"NBA|BASKETBALL"),
    ("NFL", r"NFL|FOOTBALL"),
    ("NHL", r"NHL|HOCKEY"),
    ("WNBA", r"WNBA"),
]


def _classify(ticker: str, patterns: list[tuple[str, str]], default: str) -> str:
    upper = (ticker or "").upper()
    for label, pattern in patterns:
        if re.search(pattern, upper):
            return label
    return default


def _load(path: Path) -> Any:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    with path.open() as handle:
        return json.load(handle)


def _records(blob: Any, *keys: str) -> list[dict[str, Any]]:
    """Pull a record list out of a raw API dump without assuming its shape."""
    if isinstance(blob, list):
        return [r for r in blob if isinstance(r, dict)]
    if isinstance(blob, dict):
        for key in keys:
            if isinstance(blob.get(key), list):
                return [r for r in blob[key] if isinstance(r, dict)]
        for value in blob.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
    return []


def _flatten_markets_by_series(blob: Any) -> list[dict[str, Any]] | None:
    """Unwrap Phase 0-A's markets_sample.json shape, confirmed 2026-07-31:
    {"markets_by_series": {series_ticker: {"ok":.., "count":.., "markets": [...]}}}
    -- a dict of dicts, not the flat list or single-nested list _records()
    handles. Individual market dicts carry no series_ticker field of their
    own (confirmed by direct inspection), so it is injected here from the
    outer key. Returns None (not []) when the shape doesn't match, so
    callers can fall back to _records() instead of treating "wrong shape"
    the same as "right shape, zero markets".
    """
    if not isinstance(blob, dict):
        return None
    mbs = blob.get("markets_by_series")
    if not isinstance(mbs, dict):
        return None
    flat: list[dict[str, Any]] = []
    for series_ticker, entry in mbs.items():
        if not isinstance(entry, dict):
            continue
        for m in entry.get("markets") or []:
            if isinstance(m, dict):
                m = dict(m)
                m.setdefault("series_ticker", series_ticker)
                flat.append(m)
    return flat


def _load_markets(path: Path) -> list[dict[str, Any]]:
    blob = _load(path)
    flat = _flatten_markets_by_series(blob)
    if flat is not None:
        return flat
    return _records(blob, "markets", "data")


# ---------------------------------------------------------------------------
# depth
# ---------------------------------------------------------------------------

def _normalize_book(raw: dict[str, Any]) -> dict[str, Any]:
    """Unwrap the live /markets/{ticker}/orderbook response.

    Confirmed by direct API probe 2026-07-31 (this session): the live
    response is keyed "orderbook_fp" with "yes_dollars"/"no_dollars" sides,
    prices as decimal-dollar strings (e.g. "0.0100" == 1 cent) and sizes as
    decimal-string contract counts -- not the legacy integer-cents
    {"orderbook": {"yes": [[price_cents, size]]}} shape this script
    originally assumed (which silently produced usable=False for every
    single sample, since book.get("yes")/book.get("no") were always empty).
    """
    ob = raw.get("orderbook_fp") or raw.get("orderbook") or raw
    if not isinstance(ob, dict):
        return {"yes": [], "no": []}
    if "yes_dollars" in ob or "no_dollars" in ob:
        def conv(side: str) -> list[list[Any]]:
            return [[round(float(p) * 100), int(float(s))]
                    for p, s in (ob.get(side) or []) if s]
        return {"yes": conv("yes_dollars"), "no": conv("no_dollars")}
    return {"yes": ob.get("yes") or [], "no": ob.get("no") or []}


def _book_metrics(book: dict[str, Any]) -> dict[str, Any]:
    """Top-of-book size, cumulative size within 5c of mid, observed half-spread.

    Kalshi orderbooks are quoted in cents as [price, size] pairs per side.
    Bid sides are returned best-first; this does not assume that and sorts.
    """
    yes = [(int(p), int(s)) for p, s in (book.get("yes") or []) if s]
    no = [(int(p), int(s)) for p, s in (book.get("no") or []) if s]
    if not yes or not no:
        return {"usable": False}

    best_yes = max(p for p, _ in yes)          # best bid for YES
    best_no = max(p for p, _ in no)            # best bid for NO
    yes_ask = 100 - best_no                    # YES ask implied by NO bid
    if yes_ask <= best_yes:
        return {"usable": False}

    mid = (best_yes + yes_ask) / 2.0
    half_spread = (yes_ask - best_yes) / 2.0

    top_yes = sum(s for p, s in yes if p == best_yes)
    top_no = sum(s for p, s in no if p == best_no)
    within_yes = sum(s for p, s in yes if abs(p - mid) <= 5)
    within_no = sum(s for p, s in no if abs((100 - p) - mid) <= 5)

    return {
        "usable": True,
        "mid_cents": round(mid, 2),
        "half_spread_cents": round(half_spread, 2),
        "top_of_book_contracts": {"yes": top_yes, "no": top_no},
        "within_5c_contracts": {"yes": within_yes, "no": within_no},
        # Notional a taker could absorb within 5c, in dollars, worst side.
        "within_5c_usd_min_side": round(
            min(within_yes * mid / 100.0, within_no * (100 - mid) / 100.0), 2
        ),
    }


def cmd_depth(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from prediction_market_bot.c5_execution.kalshi_client import (  # noqa: E402
        KalshiMarketClient,
    )

    markets = _load_markets(Path(args.inp))
    if not markets:
        raise SystemExit("no markets found in input dump")

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in markets:
        series = m.get("series_ticker") or m.get("event_ticker") or m.get("ticker", "")
        by_family[_classify(series, FAMILY_PATTERNS, "UNCLASSIFIED")].append(m)

    client = KalshiMarketClient.from_env()
    out: dict[str, Any] = {"sampled_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                           "per_family_target": args.per_family, "families": {}}

    for family, group in sorted(by_family.items()):
        sampled: list[dict[str, Any]] = []
        for m in group[: args.per_family]:
            ticker = m.get("ticker")
            if not ticker:
                continue
            book = None
            for attempt in range(MAX_RETRIES):
                ok, data = client._get(f"/markets/{ticker}/orderbook")
                if ok:
                    book = _normalize_book(data or {})
                    break
                time.sleep(REQUEST_PAUSE_S * (2 ** attempt))
            time.sleep(REQUEST_PAUSE_S)
            if book is None:
                sampled.append({"ticker": ticker, "usable": False, "reason": "fetch_failed"})
                continue
            metrics = _book_metrics(book)
            metrics["ticker"] = ticker
            sampled.append(metrics)

        usable = [s for s in sampled if s.get("usable")]
        out["families"][family] = {
            "n_available": len(group),
            "n_sampled": len(sampled),
            "n_usable": len(usable),
            "median_half_spread_cents": round(
                statistics.median([s["half_spread_cents"] for s in usable]), 2
            ) if usable else None,
            "median_within_5c_usd": round(
                statistics.median([s["within_5c_usd_min_side"] for s in usable]), 2
            ) if usable else None,
            "min_within_5c_usd": min(
                (s["within_5c_usd_min_side"] for s in usable), default=None
            ),
            "samples": sampled,
        }
        print(f"{family:>18}: sampled {len(sampled)}, usable {len(usable)}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"wrote {args.out}")
    return 0


# ---------------------------------------------------------------------------
# classify
# ---------------------------------------------------------------------------

def cmd_classify(args: argparse.Namespace) -> int:
    series = _records(_load(Path(args.series)), "series", "data")
    markets = _load_markets(Path(args.markets)) if args.markets else []
    depth = _load(Path(args.depth)) if args.depth and Path(args.depth).exists() else None
    gate_floor = args.stake * DEPTH_GATE_MULTIPLE

    rows: list[dict[str, str]] = []
    for s in series:
        ticker = s.get("ticker") or s.get("series_ticker") or ""
        rows.append({
            "ticker": ticker,
            "title": (s.get("title") or "")[:70],
            "sport": _classify(ticker + " " + (s.get("title") or ""), SPORT_PATTERNS, "OTHER"),
            "family": _classify(ticker, FAMILY_PATTERNS, "UNCLASSIFIED"),
        })

    mkt_by_series: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in markets:
        mkt_by_series[m.get("series_ticker") or ""].append(m)

    lines: list[str] = [
        "# Phase 0 — Kalshi Market Universe Survey (generated)",
        "",
        f"Series enumerated: **{len(rows)}**  |  markets sampled: **{len(markets)}**",
        f"Depth gate: family must clear **${gate_floor:,.2f}** "
        f"(= {DEPTH_GATE_MULTIPLE:g} x ${args.stake:,.2f} intended stake, spec section 2.7)",
        "",
        "## Table 1 — Series by sport and family",
        "",
        "| Sport | Family | Series count | Example tickers |",
        "|---|---|---:|---|",
    ]
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for r in rows:
        grouped[(r["sport"], r["family"])].append(r["ticker"])
    for (sport, family), tickers in sorted(grouped.items()):
        lines.append(f"| {sport} | {family} | {len(tickers)} | {', '.join(sorted(tickers)[:3])} |")

    lines += ["", "## Table 2 — MLB series detail", "",
              "| Series | Family | Title | Markets sampled |", "|---|---|---|---:|"]
    for r in sorted([r for r in rows if r["sport"] == "MLB"], key=lambda x: x["ticker"]):
        lines.append(f"| `{r['ticker']}` | {r['family']} | {r['title']} "
                     f"| {len(mkt_by_series.get(r['ticker'], []))} |")

    lines += ["", "## Table 3 — Depth and gate verdict", ""]
    if depth is None:
        lines += ["_Depth sample not supplied. Run the `depth` subcommand on the VPS "
                  "and re-run `classify` with `--depth`. **The section 2.7 gate cannot be "
                  "evaluated without it, and no family may proceed past Phase 2 on an "
                  "unevaluated gate.**_"]
    else:
        lines += ["| Family | Sampled | Usable | Median half-spread (c) | "
                  "Median depth within 5c (USD) | Min depth (USD) | Gate |",
                  "|---|---:|---:|---:|---:|---:|---|"]
        for family, d in sorted(depth.get("families", {}).items()):
            med = d.get("median_within_5c_usd")
            verdict = "NO DATA" if med is None else ("PASS" if med >= gate_floor else "**FAIL**")
            lines.append(
                f"| {family} | {d.get('n_sampled', 0)} | {d.get('n_usable', 0)} "
                f"| {d.get('median_half_spread_cents')} | {med} "
                f"| {d.get('min_within_5c_usd')} | {verdict} |"
            )

    unclassified = [r["ticker"] for r in rows if r["family"] == "UNCLASSIFIED"]
    lines += ["", "## Table 4 — Unclassified series (review individually)", ""]
    lines += ([f"- `{t}`" for t in sorted(unclassified)[:60]] or ["_none_"])
    if len(unclassified) > 60:
        lines.append(f"- _...and {len(unclassified) - 60} more_")
    lines += ["", "_An unclassified series is a finding, not noise — FAMILY_PATTERNS is a "
              "heuristic over ticker strings and every miss should be resolved by hand "
              "before this survey is treated as complete._", ""]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines))
    print(f"wrote {args.out}  ({len(rows)} series, {len(unclassified)} unclassified)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("depth", help="sample orderbook depth per family (needs API)")
    d.add_argument("--in", dest="inp", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--per-family", type=int, default=20)
    d.set_defaults(func=cmd_depth)

    c = sub.add_parser("classify", help="build survey tables from raw dumps (offline)")
    c.add_argument("--series", required=True)
    c.add_argument("--markets", default="")
    c.add_argument("--depth", default="")
    c.add_argument("--out", required=True)
    c.add_argument("--stake", type=float, default=DEFAULT_INTENDED_STAKE_USD)
    c.set_defaults(func=cmd_classify)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
