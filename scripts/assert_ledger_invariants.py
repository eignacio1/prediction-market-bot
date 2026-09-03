#!/usr/bin/env python3
"""Alarm-only ledger invariant suite (T-432/BLOCK B).

WHY THIS EXISTS: GG-166 corrupted ~44% of the epoch-12 clean cohort's
outcomes/P&L. It was baked into four analysis sessions before an
independent, decoupled data path (T-421's outcome store) happened to
disagree with the ledger. Nothing in the session-start protocol, the
governance gap log, or session-end checks a VALUE in the ledger is
correct — only that a step ran. This suite checks values.

MODE: ALARM-ONLY. Non-negotiable, per operator directive:
  - Exits 0 even when invariants are violated. Violations go to a report
    and stderr, never to the exit code, unless --strict is passed.
  - --strict is reserved and OFF by default. It is wired to nothing —
    no cron, no hook, no CI gate calls this script with --strict. It
    exists only so promoting this suite to a gate later is a one-line
    change (add the flag where it's invoked) rather than a rewrite.
  - Never halts, gates, or blocks the resolution cron, CI, or any
    pipeline.
  - Never modifies any ledger, portfolio file, or store. Read-only.

THREE DESIGN RULES (do not relax them):
  1. PRESENCE GUARD — "field absent" is a distinct outcome from "field
     violates". A missing field is never coerced into a value that
     fails a bound; it is counted separately and excluded from the
     violation rate's denominator.
  2. BAND SCOPE — assertions are per-band unless proven global. Two
     bands can have genuinely different correct formulas for the same
     field (ADR-0045/GG-119: T1 bakes half-vig into gross_edge,
     T4M-PROJ bakes full-vig) — evaluating both under one formula
     produces a false violation, not a real one.
  3. VIOLATION PROVENANCE — every violation carries its own
     logic_epoch and entered_at, so a reader can tell legacy residue
     (an old, already-superseded write-path era) from a live
     regression (violations concentrated in the current epoch) without
     re-deriving epoch boundaries by hand.

DATA SOURCES: the two live portfolio caches (T1/T2/T3 book,
T4 book) and T-421's decoupled outcome store, all pulled read-only
from the VPS into `logs/` (gitignored, not committed — see the
deliverable doc for the fetch commands). If a source file is absent,
the assertions that depend on it are reported as SOURCE_UNAVAILABLE,
never silently skipped and never treated as a violation.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from prediction_market_bot.logic_epoch import (  # noqa: E402
    clean_epoch_floor_for_band,
    is_clean_for_band,
)
from prediction_market_bot.c5_execution.measurement_stake import (  # noqa: E402
    T1_GAME_MARKET_TYPES,
    T1_MEASUREMENT_MAX_CONTRACTS,
    T1_MEASUREMENT_STAKE_USD,
)
from prediction_market_bot.c5_execution.market_type_registry import (  # noqa: E402
    MarketType,
)

DEFAULT_T1_PORTFOLIO = _REPO_ROOT / "logs" / ".vps_portfolio_cache_mlb.json"
DEFAULT_T4_PORTFOLIO = _REPO_ROOT / "logs" / ".vps_portfolio_cache_mlb_t4.json"
DEFAULT_OUTCOME_STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"
DEFAULT_REPORT_PATH = _REPO_ROOT / "logs" / "ledger_invariant_report.jsonl"

TICKER_RE = re.compile(
    r"^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})([A-Z]{4,6})(G[12])?-([A-Z]+?)(\d+)-(\d+)$"
)
MONTH_ABBR = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
NAME_SUFFIXES = {"JR", "SR", "II", "III", "IV", "V"}

# fee_net_edge write-path eras (T-432 empirical derivation, this session,
# n=2,150 rows T1+T4M-PROJ at logic_epoch>=6): the CURRENT (post-GG-113)
# cascade is clean only from this epoch forward. logic_epoch==3 used the
# pre-GG-113 plain-sign-flip formula; logic_epoch 1-2 used the even older
# pre-GG-077 no-direction-flip formula. Both are legacy residue, not live
# regressions — this assertion intentionally does not evaluate them.
FEE_NET_EDGE_CLEAN_FLOOR = 6

# ADR-0050 flat-measurement-stake fields only exist on T4M-PROJ rows at or
# above this epoch (verified empirically this session: entirely absent
# below it, present on all 627 epoch-12 T4M-PROJ rows sampled).
ADR_0050_FLOOR = 12
ADR_0050_BAND = "T4M-PROJ"

KNOWN_OUTCOMES = {"WIN", "LOSS"}
KNOWN_STATUSES = {"OPEN", "CLOSED", "REJECTED"}

# G is band-scoped per ADR-0045/GG-119: T1's gross_edge embeds half-vig
# (kalshi_client.py's DS02Snapshot.half_spread = vig / 2), T4M-PROJ's embeds
# full vig (run_t4_mlb_live.py:1148, always stored YES-frame per GG-087/
# GG-113). Bands not listed here have no verified formula and are not
# evaluated for G — reported as NO_FORMULA, never guessed.
GROSS_EDGE_VIG_MULTIPLIER = {"T1": 0.5, "T4M-PROJ": 1.0}

# T-509/ADR-0054(a) SS8 item 1: this suite predates the (MarketType, band)
# cell registry (78 cells today) and was band-scoped only — a record whose
# market_type is a game market (moneyline/run-line/totals, ADR-0058/ADR-0059)
# but whose band happens to have a verified G/K formula for PROP bets would
# have been silently evaluated under that props-only formula, producing a
# false violation (or worse, a false clean) rather than an honest NO_FORMULA.
# VIG_FORMULA_VERIFIED_MARKET_TYPE names the one market type G/K's formulas
# were actually derived against (GG-119/ADR-0045, T-432's fee_net_edge
# empirical derivation) — both stay gated to it until a game-market formula
# is independently verified and this constant grows into a set.
VIG_FORMULA_VERIFIED_MARKET_TYPE = MarketType.MLB_PLAYER_PROP_HITS.value

# A record whose market_type field is absent (pre-ADR-0058 write path) or
# holds a value outside the registered MarketType enum is grouped here —
# never silently folded into VIG_FORMULA_VERIFIED_MARKET_TYPE and never
# dropped. See positions_by_cell() and _UNKNOWN_MARKET_TYPE_COUNTS.
UNKNOWN_MARKET_TYPE = "UNKNOWN_MARKET_TYPE"

_KNOWN_MARKET_TYPE_VALUES = {m.value for m in MarketType}

# GG-191-pattern counter (mirrors run_band_monitor.py's
# _UNREGISTERED_SERIES_COUNTS, T-509 item 2): keyed by (raw_market_type_or_
# None, band), incremented every time positions_by_cell() cannot place a
# record's market_type in the registered enum. Reported loudly in run(),
# never silently absorbed.
_UNKNOWN_MARKET_TYPE_COUNTS: "Counter[tuple[Any, str]]" = Counter()


# ── loading ──────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def positions_by_band(portfolio: dict) -> dict[str, list[dict]]:
    all_recs = (
        portfolio.get("open_positions", [])
        + portfolio.get("closed_positions", [])
        + portfolio.get("rejected_positions", [])
    )
    by_band: dict[str, list[dict]] = {}
    for r in all_recs:
        b = r.get("band") or "UNTAGGED"
        by_band.setdefault(b, []).append(r)
    return by_band


def positions_by_cell(portfolio: dict) -> dict[tuple[str, str], list[dict]]:
    """T-509/ADR-0054(a) item 1: groups positions by (market_type, band) --
    the same key the live registry (MARKET_TYPE_REGISTRY, 78 cells) uses.

    A record whose market_type is absent (pre-ADR-0058 write path) or holds
    a value outside the registered MarketType enum is grouped under
    UNKNOWN_MARKET_TYPE rather than being dropped or folded into
    VIG_FORMULA_VERIFIED_MARKET_TYPE -- and is separately counted via
    _UNKNOWN_MARKET_TYPE_COUNTS (GG-191 pattern) so the run() summary can
    report it loudly instead of it silently vanishing into a bucket whose
    label implies something it isn't.
    """
    all_recs = (
        portfolio.get("open_positions", [])
        + portfolio.get("closed_positions", [])
        + portfolio.get("rejected_positions", [])
    )
    by_cell: dict[tuple[str, str], list[dict]] = {}
    for r in all_recs:
        b = r.get("band") or "UNTAGGED"
        raw_mt = r.get("market_type")
        if raw_mt in _KNOWN_MARKET_TYPE_VALUES:
            mt = raw_mt
        else:
            mt = UNKNOWN_MARKET_TYPE
            _UNKNOWN_MARKET_TYPE_COUNTS[(raw_mt, b)] += 1
        by_cell.setdefault((mt, b), []).append(r)
    return by_cell


# ── assertion result plumbing ───────────────────────────────────────────

class AssertionResult:
    def __init__(
        self,
        aid: str,
        name: str,
        band: str,
        fields_required: list[str],
        description: str,
        market_type: str = "ALL",
    ):
        self.aid = aid
        self.name = name
        self.band = band
        self.fields_required = fields_required
        self.description = description
        # "ALL" means this assertion is market-type-agnostic (band-scoped
        # only, unaffected by the T-509 cell-awareness change) -- a real
        # cell identity is only ever set by the CELL_ASSERTIONS (G, K, I2,
        # J2), the four whose correct formula actually depends on
        # market_type. Do not read "ALL" as "evaluated across every cell";
        # it means the market_type axis was never consulted at all.
        self.market_type = market_type
        self.n_applicable = 0
        self.n_absent = 0
        self.n_violations = 0
        self.examples: list[dict] = []
        self.epochs_seen_in_violations: list[int] = []
        self.no_formula = False

    def record(self, ok: bool, rec: dict, detail: str = "") -> None:
        self.n_applicable += 1
        if not ok:
            self.n_violations += 1
            epoch = rec.get("logic_epoch")
            if epoch is not None:
                self.epochs_seen_in_violations.append(epoch)
            if len(self.examples) < 10:
                self.examples.append({
                    "position_id": rec.get("position_id"),
                    "kalshi_ticker": rec.get("kalshi_ticker"),
                    "logic_epoch": epoch,
                    "entered_at": rec.get("entered_at"),
                    "detail": detail,
                })

    def to_jsonl_line(self) -> dict:
        rate = (self.n_violations / self.n_applicable * 100.0) if self.n_applicable else None
        epoch_dist = dict(Counter(self.epochs_seen_in_violations))
        return {
            "type": "assertion",
            "id": self.aid,
            "name": self.name,
            "band_scope": self.band,
            "market_type": self.market_type,
            "fields_required": self.fields_required,
            "description": self.description,
            "no_formula": self.no_formula,
            "n_applicable": self.n_applicable,
            "n_absent": self.n_absent,
            "n_violations": self.n_violations,
            "violation_rate_pct": round(rate, 2) if rate is not None else None,
            "violation_epoch_distribution": epoch_dist,
            "first_seen_epoch": min(self.epochs_seen_in_violations) if self.epochs_seen_in_violations else None,
            "last_seen_epoch": max(self.epochs_seen_in_violations) if self.epochs_seen_in_violations else None,
            "examples": self.examples,
        }


# ── core assertions (operator table A-H, corrected per T-432 brief) ────

def assert_A_ticker_date(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "A", "ticker_date_matches_game_date", band,
        ["kalshi_ticker", "game_date"],
        "Ticker-embedded date (YYMONDD) equals the stored game_date field.",
    )
    for rec in recs:
        tk, gd = rec.get("kalshi_ticker"), rec.get("game_date")
        m = TICKER_RE.match(tk) if tk else None
        if not m or gd is None:
            r.n_absent += 1
            continue
        yy, mon, dd = m.group(1), m.group(2), m.group(3)
        try:
            ticker_date = date(2000 + int(yy), MONTH_ABBR[mon], int(dd)).isoformat()
        except (KeyError, ValueError):
            r.n_absent += 1
            continue
        r.record(ticker_date == gd, rec, f"ticker_date={ticker_date} game_date={gd}")
    return r


def assert_B_ticker_threshold(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "B", "ticker_threshold_matches_kalshi_threshold", band,
        ["kalshi_ticker", "kalshi_threshold"],
        "Ticker-embedded threshold equals the stored kalshi_threshold field.",
    )
    for rec in recs:
        tk, kt = rec.get("kalshi_ticker"), rec.get("kalshi_threshold")
        m = TICKER_RE.match(tk) if tk else None
        if not m or kt is None:
            r.n_absent += 1
            continue
        r.record(int(m.group(9)) == int(kt), rec, f"ticker_thr={m.group(9)} kalshi_threshold={kt}")
    return r


def assert_C_entry_price_bounds(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "C", "entry_price_paid_bounds", band, ["entry_price_paid"],
        "0 < entry_price_paid <= 1 (presence-guarded — field only exists on "
        f"{ADR_0050_BAND} rows at logic_epoch>={ADR_0050_FLOOR}, ADR-0050).",
    )
    for rec in recs:
        epp = rec.get("entry_price_paid")
        if epp is None:
            r.n_absent += 1
            continue
        r.record(0 < epp <= 1, rec, f"entry_price_paid={epp}")
    return r


def assert_C2_mid_price_bounds(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "C2", "mid_price_at_entry_bounds", band, ["mid_price_at_entry"],
        "0 <= mid_price_at_entry <= 1.",
    )
    for rec in recs:
        mpe = rec.get("mid_price_at_entry")
        if mpe is None:
            r.n_absent += 1
            continue
        r.record(0 <= mpe <= 1, rec, f"mid_price_at_entry={mpe}")
    return r


def assert_D_contracts_consistency(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "D", "contracts_equals_stake_over_price", band,
        ["contracts", "size_usd", "entry_price_paid"],
        "contracts == size_usd / entry_price_paid (presence-guarded).",
    )
    for rec in recs:
        cts, su, epp = rec.get("contracts"), rec.get("size_usd"), rec.get("entry_price_paid")
        if cts is None or su is None or epp is None or epp == 0:
            r.n_absent += 1
            continue
        r.record(abs(cts - su / epp) <= 1e-3, rec, f"contracts={cts} size_usd/price={su/epp:.4f}")
    return r


def assert_E_pnl_sign(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "E", "pnl_sign_matches_outcome", band, ["outcome", "pnl"],
        "WIN implies pnl >= 0; LOSS implies pnl <= 0. Resolved positions only.",
    )
    for rec in recs:
        oc, pnl = rec.get("outcome"), rec.get("pnl")
        if oc not in ("WIN", "LOSS") or pnl is None:
            r.n_absent += 1
            continue
        ok = not ((oc == "WIN" and pnl < 0) or (oc == "LOSS" and pnl > 0))
        r.record(ok, rec, f"outcome={oc} pnl={pnl}")
    return r


def assert_F_resolved_after_entered(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "F", "resolved_after_entered", band, ["entered_at", "resolved_at"],
        "resolved_at > entered_at. Resolved positions only.",
    )
    for rec in recs:
        if rec.get("outcome") not in ("WIN", "LOSS"):
            continue
        ea, ra = rec.get("entered_at"), rec.get("resolved_at")
        if ea is None or ra is None:
            r.n_absent += 1
            continue
        r.record(ra > ea, rec, f"entered_at={ea} resolved_at={ra}")
    return r


def assert_G_gross_edge_formula(
    recs: list[dict], band: str, market_type: str = VIG_FORMULA_VERIFIED_MARKET_TYPE
) -> AssertionResult:
    r = AssertionResult(
        "G", "gross_edge_matches_band_formula", band,
        ["gross_edge", "model_p", "mid_price_at_entry", "vig_at_entry"],
        "gross_edge == model_p - mid - (vig * band_multiplier); band-scoped "
        "per ADR-0045/GG-119 — T1 bakes half-vig, T4M-PROJ bakes full-vig. "
        "Bands with no verified formula are not evaluated (NO_FORMULA). "
        "Cell-scoped as of T-509/ADR-0054(a): only cells whose market_type "
        f"is {VIG_FORMULA_VERIFIED_MARKET_TYPE} have a verified formula -- "
        "game-market cells (moneyline/run-line/totals, ADR-0058/ADR-0059) "
        "are also NOT EVALUATED until their own formula is verified.",
        market_type=market_type,
    )
    mult = GROSS_EDGE_VIG_MULTIPLIER.get(band)
    if mult is None or market_type != VIG_FORMULA_VERIFIED_MARKET_TYPE:
        r.no_formula = True
        return r
    for rec in recs:
        ge, mp, mid, vig = (
            rec.get("gross_edge"), rec.get("model_p"),
            rec.get("mid_price_at_entry"), rec.get("vig_at_entry"),
        )
        if None in (ge, mp, mid, vig):
            r.n_absent += 1
            continue
        expected = mp - mid - vig * mult
        r.record(abs(ge - expected) <= 1e-4, rec, f"gross_edge={ge} expected={expected:.6f}")
    return r


def assert_H_no_dual_direction_open(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "H", "no_dual_direction_open_same_ticker", band,
        ["status", "kalshi_ticker", "direction"],
        "No ticker has both a YES and a NO position simultaneously OPEN.",
    )
    open_recs = [rec for rec in recs if rec.get("status") == "OPEN"]
    by_ticker: dict[str, list[dict]] = {}
    for rec in open_recs:
        by_ticker.setdefault(rec.get("kalshi_ticker"), []).append(rec)
    for tk, group in by_ticker.items():
        dirs = {g.get("direction") for g in group}
        r.n_applicable += 1
        if len(dirs) > 1:
            r.n_violations += 1
            epochs = [g.get("logic_epoch") for g in group if g.get("logic_epoch") is not None]
            r.epochs_seen_in_violations.extend(epochs)
            if len(r.examples) < 10:
                r.examples.append({
                    "kalshi_ticker": tk,
                    "position_ids": [g.get("position_id") for g in group],
                    "directions": sorted(dirs),
                    "logic_epochs": epochs,
                })
    return r


# ── EXTEND assertions ────────────────────────────────────────────────────

def assert_I_adr0050_stake(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "I", "adr0050_flat_stake_formula", band, ["entry_price_paid", "size_usd"],
        f"size_usd == round(min(1.00, 10*entry_price_paid), 4) — {ADR_0050_BAND} "
        f"epoch>={ADR_0050_FLOOR} only (ADR-0050).",
    )
    if band != ADR_0050_BAND:
        r.no_formula = True
        return r
    for rec in recs:
        if (rec.get("logic_epoch") or 0) < ADR_0050_FLOOR:
            continue
        epp, su = rec.get("entry_price_paid"), rec.get("size_usd")
        if epp is None or su is None:
            r.n_absent += 1
            continue
        expected = round(min(1.00, 10 * epp), 4)
        r.record(abs(su - expected) <= 1e-3, rec, f"size_usd={su} expected={expected}")
    return r


def assert_J_contracts_cap(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "J", "adr0050_contracts_cap", band, ["contracts"],
        f"contracts <= 10.0 — {ADR_0050_BAND} epoch>={ADR_0050_FLOOR} only (ADR-0050).",
    )
    if band != ADR_0050_BAND:
        r.no_formula = True
        return r
    for rec in recs:
        if (rec.get("logic_epoch") or 0) < ADR_0050_FLOOR:
            continue
        cts = rec.get("contracts")
        if cts is None:
            r.n_absent += 1
            continue
        r.record(cts <= 10.0 + 1e-9, rec, f"contracts={cts}")
    return r


def assert_I2_t1_measurement_stake(
    recs: list[dict], band: str, market_type: str = UNKNOWN_MARKET_TYPE
) -> AssertionResult:
    """T-497/ADR-0059 T1 equivalent of assert_I_adr0050_stake.

    T1's flat measurement-stake mechanism (c5_execution/measurement_stake.py)
    has no floor epoch the way T4M-PROJ's ADR_0050_FLOOR does — it has not
    yet been wired into any live pipeline, so there is no historical epoch
    boundary to anchor to. Scope is instead by cell membership: only the T1
    cells whose market_type is one of the nine ADR-0058 game-market types
    are evaluated. A prop bet (KXMLBHIT) never carries this formula
    regardless of epoch — T1 props are Kelly-sized (kelly_fraction=0.0
    today, ADR-0048) and untouched by this mechanism.

    T-509/ADR-0054(a) item 1: this used to gate on band alone and then
    silently `continue` past any non-game-market record inside the loop --
    neither counted as applicable, absent, nor NO_FORMULA. Called
    cell-aware (recs pre-partitioned to a single market_type by
    positions_by_cell()), the gate now returns a proper cell-level
    NO_FORMULA for every T1 cell whose market_type isn't a game market,
    instead of a silent no-op that looked identical to "0 applicable,
    clean".
    """
    r = AssertionResult(
        "I2", "adr0059_t1_measurement_stake_formula", band,
        ["entry_price_paid", "size_usd", "market_type"],
        f"size_usd == round(min({T1_MEASUREMENT_STAKE_USD}, "
        f"{T1_MEASUREMENT_MAX_CONTRACTS}*entry_price_paid), 4) — T1 game-market "
        "cells only (ADR-0058/ADR-0059), scoped by market_type membership, not epoch.",
        market_type=market_type,
    )
    if band != "T1" or market_type not in T1_GAME_MARKET_TYPES:
        r.no_formula = True
        return r
    for rec in recs:
        epp, su = rec.get("entry_price_paid"), rec.get("size_usd")
        if epp is None or su is None:
            r.n_absent += 1
            continue
        expected = round(min(T1_MEASUREMENT_STAKE_USD, T1_MEASUREMENT_MAX_CONTRACTS * epp), 4)
        r.record(abs(su - expected) <= 1e-3, rec, f"size_usd={su} expected={expected}")
    return r


def assert_J2_t1_contracts_cap(
    recs: list[dict], band: str, market_type: str = UNKNOWN_MARKET_TYPE
) -> AssertionResult:
    """T-497/ADR-0059 T1 equivalent of assert_J_contracts_cap. See assert_I2's
    docstring for the cell-scoping rationale and the T-509 gating change."""
    r = AssertionResult(
        "J2", "adr0059_t1_contracts_cap", band, ["contracts", "market_type"],
        f"contracts <= {float(T1_MEASUREMENT_MAX_CONTRACTS)} — T1 game-market "
        "cells only (ADR-0058/ADR-0059), scoped by market_type membership, not epoch.",
        market_type=market_type,
    )
    if band != "T1" or market_type not in T1_GAME_MARKET_TYPES:
        r.no_formula = True
        return r
    for rec in recs:
        cts = rec.get("contracts")
        if cts is None:
            r.n_absent += 1
            continue
        r.record(cts <= float(T1_MEASUREMENT_MAX_CONTRACTS) + 1e-9, rec, f"contracts={cts}")
    return r


def _fee_net_edge_current(direction: str, band: str, gross_edge: float, vig: float, fee_per_contract: float) -> float:
    if direction == "YES":
        dg = gross_edge
    elif band == "T4M-PROJ":
        dg = -gross_edge - 2.0 * vig
    elif band == "T1":
        dg = -gross_edge - 1.0 * vig
    else:
        dg = -gross_edge
    return round(dg - fee_per_contract, 6)


def assert_K_fee_net_edge(
    recs: list[dict], band: str, market_type: str = VIG_FORMULA_VERIFIED_MARKET_TYPE
) -> AssertionResult:
    r = AssertionResult(
        "K", "fee_net_edge_matches_vig_cascade", band,
        ["fee_net_edge", "gross_edge", "vig_at_entry", "fee_per_contract", "direction"],
        f"fee_net_edge matches paper_trader.py's post-GG-113 direction-conditional "
        f"vig cascade — logic_epoch>={FEE_NET_EDGE_CLEAN_FLOOR} only. Epoch 3 used the "
        "pre-GG-113 plain-sign-flip formula; epoch 1-2 used the pre-GG-077 "
        "no-direction-flip formula. Both are legacy residue, not evaluated here. "
        "Cell-scoped as of T-509/ADR-0054(a): the vig cascade in "
        "_fee_net_edge_current() was derived (T-432) only against "
        f"{VIG_FORMULA_VERIFIED_MARKET_TYPE} data — game-market cells are "
        "NOT EVALUATED (NO_FORMULA) until independently verified.",
        market_type=market_type,
    )
    if market_type != VIG_FORMULA_VERIFIED_MARKET_TYPE:
        r.no_formula = True
        return r
    for rec in recs:
        if (rec.get("logic_epoch") or 0) < FEE_NET_EDGE_CLEAN_FLOOR:
            continue
        fne, ge, vig, fpc, d = (
            rec.get("fee_net_edge"), rec.get("gross_edge"), rec.get("vig_at_entry"),
            rec.get("fee_per_contract"), rec.get("direction"),
        )
        if None in (fne, ge, vig, fpc, d):
            r.n_absent += 1
            continue
        expected = _fee_net_edge_current(d, band, ge, vig, fpc)
        r.record(abs(fne - expected) <= 1e-4, rec, f"fee_net_edge={fne} expected={expected}")
    return r


def assert_L_enums(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "L", "actual_hits_outcome_status_enums", band,
        ["actual_hits", "outcome", "status"],
        "actual_hits is a non-negative integer (when present); outcome in "
        f"{sorted(KNOWN_OUTCOMES)}; status in {sorted(KNOWN_STATUSES)}.",
    )
    for rec in recs:
        problems = []
        ah = rec.get("actual_hits")
        if ah is not None:
            try:
                ahf = float(ah)
                if ahf < 0 or ahf != int(ahf):
                    problems.append(f"actual_hits={ah}")
            except (TypeError, ValueError):
                problems.append(f"actual_hits={ah} (unparseable)")
        oc = rec.get("outcome")
        if oc is not None and oc not in KNOWN_OUTCOMES:
            problems.append(f"outcome={oc}")
        st = rec.get("status")
        if st is not None and st not in KNOWN_STATUSES:
            problems.append(f"status={st}")
        r.record(not problems, rec, "; ".join(problems))
    return r


def assert_M_logic_epoch_present(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "M", "logic_epoch_never_null", band, ["logic_epoch"],
        "logic_epoch is never null on any position record.",
    )
    for rec in recs:
        r.record(rec.get("logic_epoch") is not None, rec, "logic_epoch=None")
    return r


def _name_tokens(name: str) -> tuple[str, str] | tuple[None, None]:
    parts = [w.upper() for w in re.sub(r"[^A-Za-z ]", "", name).split()]
    while parts and parts[-1] in NAME_SUFFIXES:
        parts = parts[:-1]
    if not parts:
        return None, None
    first = parts[0]
    lastword_tok = first[:1] + parts[-1]
    fullconcat_tok = first[:1] + ("".join(parts[1:]) if len(parts) > 1 else parts[0])
    return lastword_tok, fullconcat_tok


# GG-175: Kalshi's own ticker generation truncates some player tokens to fit
# the field (e.g. "N"+"LOPEZ" -> "NLOPE" for Nicky Lopez) — the token
# embedded in the ticker can be a shortened PREFIX of the full computed
# token, not just possibly preceded by extra characters (a team code) as the
# pre-existing endswith check already handled. MIN_TRUNCATED_TOKEN_LEN is the
# floor for how short that prefix is allowed to get before a match is no
# longer considered meaningful (first initial + at least 4 surname letters).
MIN_TRUNCATED_TOKEN_LEN = 5


def _token_matches(player_block: str, tok: str) -> bool:
    """True if player_block ends with tok, or with a truncated prefix of tok
    (down to MIN_TRUNCATED_TOKEN_LEN chars) — see GG-175."""
    floor = min(MIN_TRUNCATED_TOKEN_LEN, len(tok))
    for k in range(len(tok), floor - 1, -1):
        if player_block.endswith(tok[:k]):
            return True
    return False


def assert_N_player_token_consistency(recs: list[dict], band: str) -> AssertionResult:
    r = AssertionResult(
        "N", "ticker_player_token_consistent", band, ["kalshi_ticker", "player_name"],
        "Ticker-embedded player token matches player_name by either the "
        "last-name-only or first-initial+full-concat-surname convention "
        "(both real conventions in the data — e.g. 'Witt Jr.' needs "
        "last-word, 'De La Cruz' needs full-concat, 'Jung Hoo Lee' needs "
        "last-word again — no single deterministic rule captures all three), "
        "allowing for Kalshi-side truncation of the computed token down to "
        f"{MIN_TRUNCATED_TOKEN_LEN} chars (GG-175, e.g. 'NLOPE' for Nicky Lopez).",
    )
    for rec in recs:
        tk, name = rec.get("kalshi_ticker"), rec.get("player_name")
        m = TICKER_RE.match(tk) if tk else None
        if not m or not name:
            r.n_absent += 1
            continue
        player_block = m.group(7)
        tok1, tok2 = _name_tokens(name)
        if tok1 is None:
            r.n_absent += 1
            continue
        ok = _token_matches(player_block, tok1) or _token_matches(player_block, tok2)
        r.record(ok, rec, f"player_block={player_block} tok1={tok1} tok2={tok2} name={name}")
    return r


# T-509/ADR-0054(a) item 1: G, K, I2, J2 are the only four assertions whose
# CORRECT formula depends on market_type, not just band (ADR-0045/GG-119's
# vig cascade and T-432's fee_net_edge derivation were both verified only
# against MLB_PLAYER_PROP_HITS data; I2/J2 are the inverse case, verified
# only against the ADR-0058 game-market types). They are run per (market_type,
# band) CELL in run() below, via positions_by_cell(), not per band — pulling
# them out of CORE/EXTEND keeps the other 13 assertions band-scoped exactly
# as before (they are market-type-agnostic; cell-partitioning them would
# only fragment their denominators with no behavioral difference — a pure
# "denominator-unit-change" with zero real-finding content, worth avoiding).
CORE_ASSERTIONS = [
    assert_A_ticker_date, assert_B_ticker_threshold, assert_C_entry_price_bounds,
    assert_C2_mid_price_bounds, assert_D_contracts_consistency, assert_E_pnl_sign,
    assert_F_resolved_after_entered, assert_H_no_dual_direction_open,
]
EXTEND_ASSERTIONS = [
    assert_I_adr0050_stake, assert_J_contracts_cap,
    assert_L_enums, assert_M_logic_epoch_present, assert_N_player_token_consistency,
]
CELL_ASSERTIONS = [
    assert_G_gross_edge_formula, assert_K_fee_net_edge,
    assert_I2_t1_measurement_stake, assert_J2_t1_contracts_cap,
]


# ── Task 2 — cross-path agreement (standing, generalized from T-426) ──────

def cross_path_agreement(recs: list[dict], band: str, store: dict[str, dict]) -> list[dict]:
    """Per band, per epoch: ledger actual_hits/outcome vs the decoupled
    outcome store's independently-fetched actual_hits for the same ticker.
    Reports what is measured — does NOT assume the rate should be zero
    (GG-170 is OPEN and this disagreement is expected until T-437 lands).
    """
    by_epoch: dict[Any, list[dict]] = {}
    for rec in recs:
        if rec.get("outcome") not in ("WIN", "LOSS") or rec.get("model_p") is None:
            continue
        by_epoch.setdefault(rec.get("logic_epoch"), []).append(rec)

    out = []
    for epoch, epoch_recs in sorted(by_epoch.items(), key=lambda kv: (kv[0] is None, kv[0])):
        matched = unmatched = unresolved_in_store = 0
        hits_agree = hits_disagree = 0
        outcome_agree = outcome_disagree = 0
        for rec in epoch_recs:
            srec = store.get(rec.get("kalshi_ticker", ""))
            if srec is None:
                unmatched += 1
                continue
            if not srec.get("resolved"):
                unresolved_in_store += 1
                continue
            matched += 1
            lh, sh = rec.get("actual_hits"), srec.get("actual_hits")
            if lh is not None and sh is not None and float(lh) == float(sh):
                hits_agree += 1
            else:
                hits_disagree += 1
            try:
                thr = int(rec.get("threshold", rec.get("kalshi_threshold", 0)) or 0)
                direction = str(rec.get("direction", "YES"))
                store_meets = float(sh) >= thr
                derived = "WIN" if (store_meets if direction == "YES" else not store_meets) else "LOSS"
            except (TypeError, ValueError):
                derived = None
            if derived is not None and derived == rec.get("outcome"):
                outcome_agree += 1
            else:
                outcome_disagree += 1
        n_resolved = len(epoch_recs)
        out.append({
            "type": "cross_path_agreement",
            "band": band,
            "logic_epoch": epoch,
            "n_resolved_ledger_positions": n_resolved,
            "n_matched_in_store": matched,
            "n_unmatched_in_store": unmatched,
            "n_matched_but_unresolved_in_store": unresolved_in_store,
            "hits_agree": hits_agree,
            "hits_disagree": hits_disagree,
            "hits_agreement_rate_pct": round(hits_agree / matched * 100.0, 1) if matched else None,
            "outcome_agree": outcome_agree,
            "outcome_disagree": outcome_disagree,
            "outcome_agreement_rate_pct": round(outcome_agree / matched * 100.0, 1) if matched else None,
        })
    return out


# ── run ──────────────────────────────────────────────────────────────────

def run(
    t1_portfolio_path: Path,
    t4_portfolio_path: Path,
    outcome_store_path: Path,
    report_path: Path,
    strict: bool,
) -> int:
    lines: list[dict] = []
    total_violations = 0
    total_assertions_run = 0
    total_no_formula = 0
    bands_with_incomplete_formula_coverage: list[str] = []

    t1_pf = load_json(t1_portfolio_path)
    t4_pf = load_json(t4_portfolio_path)
    store_recs = load_jsonl(outcome_store_path)
    store = {r["ticker"]: r for r in store_recs} if store_recs is not None else None

    print("=" * 78, file=sys.stderr)
    print("LEDGER INVARIANT SUITE — ALARM-ONLY (T-432)", file=sys.stderr)
    print("Exit code is always 0 unless --strict was passed explicitly.", file=sys.stderr)
    print("=" * 78, file=sys.stderr)

    for label, path, pf in (("T1/T2/T3 book", t1_portfolio_path, t1_pf), ("T4 book", t4_portfolio_path, t4_pf)):
        if pf is None:
            print(f"[SOURCE_UNAVAILABLE] {label}: {path} not found — skipping its bands.", file=sys.stderr)
            lines.append({"type": "source_unavailable", "source": str(path), "label": label})

    if store is None:
        print(f"[SOURCE_UNAVAILABLE] outcome store: {outcome_store_path} not found — Task 2 cross-path check skipped.", file=sys.stderr)
        lines.append({"type": "source_unavailable", "source": str(outcome_store_path), "label": "outcome_store"})

    by_band: dict[str, list[dict]] = {}
    if t1_pf is not None:
        by_band.update(positions_by_band(t1_pf))
    if t4_pf is not None:
        for b, recs in positions_by_band(t4_pf).items():
            by_band.setdefault(b, []).extend(recs)

    # T-509/ADR-0054(a) item 1: cell-level (market_type, band) grouping,
    # used only by CELL_ASSERTIONS below (see the comment above that list
    # for why the other 13 assertions stay band-scoped via by_band).
    by_cell: dict[tuple[str, str], list[dict]] = {}
    if t1_pf is not None:
        by_cell.update(positions_by_cell(t1_pf))
    if t4_pf is not None:
        for c, recs in positions_by_cell(t4_pf).items():
            by_cell.setdefault(c, []).extend(recs)

    for band, recs in sorted(by_band.items()):
        print(f"\n--- band={band} (n={len(recs)}) ---", file=sys.stderr)
        current_epoch = max(
            (rec.get("logic_epoch") for rec in recs if rec.get("logic_epoch") is not None),
            default=None,
        )
        band_no_formula_ids: list[str] = []
        for fn in CORE_ASSERTIONS + EXTEND_ASSERTIONS:
            result = fn(recs, band)
            if result.no_formula:
                print(f"  [{result.aid}] {result.name}: NO_FORMULA for this band — not evaluated", file=sys.stderr)
                lines.append(result.to_jsonl_line())
                band_no_formula_ids.append(result.aid)
                total_no_formula += 1
                continue
            total_assertions_run += 1
            total_violations += result.n_violations
            flag = "ALARM" if result.n_violations else "clean"
            print(
                f"  [{result.aid}] {result.name}: n={result.n_applicable} "
                f"absent={result.n_absent} violations={result.n_violations} ({flag})",
                file=sys.stderr,
            )
            line = result.to_jsonl_line()
            lines.append(line)

            # GG-170/T-458: assertion A (ticker_date_matches_game_date) is the
            # date-binding check GG-170 exists to catch. A violation count
            # concentrated in old epochs is legacy residue; a violation AT the
            # current epoch means it is still happening on resolutions written
            # under today's logic, not just old data. ALARM-ONLY mode already
            # prints every violation, but that print is identical in weight to
            # every other assertion's routine ALARM line and is easy to miss
            # in a long run — this makes new-epoch recurrence structurally
            # louder and separately flagged in the report, without promoting
            # the script to --strict (exit code is untouched).
            if result.aid == "A" and current_epoch is not None:
                epoch_dist = line["violation_epoch_distribution"]
                # NOTE: keys here are still ints (this dict is the in-memory
                # Python object from to_jsonl_line(), not yet json.dumps'd —
                # serialization to string keys happens only when written to
                # the report file below). Do not str()-coerce current_epoch.
                n_current_epoch_violations = epoch_dist.get(current_epoch, 0)
                if n_current_epoch_violations > 0:
                    print(
                        "  " + "!" * 74,
                        file=sys.stderr,
                    )
                    print(
                        f"  [GG-170 RECURRENCE] band={band} epoch={current_epoch}: "
                        f"{n_current_epoch_violations} NEW ticker/game_date mismatches "
                        f"at the CURRENT epoch — this is not legacy residue, it is "
                        f"still happening. See GOVERNANCE_GAP_LOG.md GG-170.",
                        file=sys.stderr,
                    )
                    print(
                        "  " + "!" * 74,
                        file=sys.stderr,
                    )
                    lines.append({
                        "type": "recurrence_alarm",
                        "gg": "GG-170",
                        "assertion_id": "A",
                        "band": band,
                        "current_epoch": current_epoch,
                        "n_current_epoch_violations": n_current_epoch_violations,
                    })

        # T-466: NO_FORMULA is a silent pass (the assertion reports nothing
        # rather than "clean" or "violation" because it never ran) — a reader
        # scanning per-assertion ALARM/clean lines above can mistake a run of
        # NO_FORMULA lines for a healthy band. This makes coverage itself a
        # first-class, loud line per band, and a machine-readable record in
        # the report, so "not evaluated" and "evaluated and clean" can never
        # be confused for one another.
        n_formula_assertions_total = len(CORE_ASSERTIONS) + len(EXTEND_ASSERTIONS)
        n_no_formula = len(band_no_formula_ids)
        n_evaluated = n_formula_assertions_total - n_no_formula
        lines.append({
            "type": "band_formula_coverage",
            "band": band,
            "n_assertions_total": n_formula_assertions_total,
            "n_evaluated": n_evaluated,
            "n_no_formula": n_no_formula,
            "no_formula_ids": band_no_formula_ids,
        })
        if n_no_formula:
            bands_with_incomplete_formula_coverage.append(band)
            print(
                f"  COVERAGE band={band}: {n_evaluated}/{n_formula_assertions_total} "
                f"assertions evaluated — {n_no_formula} NOT EVALUATED (NO_FORMULA: "
                f"{','.join(band_no_formula_ids)}). Do not read these as clean — "
                f"they were never checked. (T-466)",
                file=sys.stderr,
            )
        else:
            print(
                f"  COVERAGE band={band}: {n_evaluated}/{n_formula_assertions_total} "
                f"assertions evaluated — full formula coverage.",
                file=sys.stderr,
            )

        if store is not None and band in ("T1", "T4M-PROJ"):
            agreement = cross_path_agreement(recs, band, store)
            for row in agreement:
                lines.append(row)
                print(
                    f"  [cross-path] band={band} epoch={row['logic_epoch']}: "
                    f"matched={row['n_matched_in_store']}/{row['n_resolved_ledger_positions']} "
                    f"hits_agree={row['hits_agreement_rate_pct']}% outcome_agree={row['outcome_agreement_rate_pct']}%",
                    file=sys.stderr,
                )

    # ── T-509/ADR-0054(a) item 1: cell-scoped assertions (G, K, I2, J2) ────
    # Run once per (market_type, band) cell rather than once per band. This
    # is the actual cell-awareness fix: before it, a game-market record
    # sharing a band with props (e.g. a future T1 moneyline cell) would have
    # been silently evaluated under the props-verified G/K formula inside
    # the band loop above, or (for I2/J2) silently `continue`d past without
    # being counted at all. Now every cell gets its own honest NO_FORMULA
    # determination, reported separately and never folded into a clean count.
    cells_with_incomplete_formula_coverage: list[str] = []
    for (market_type, band), recs in sorted(by_cell.items()):
        cell_label = f"{market_type}|{band}"
        print(f"\n--- cell=({market_type}, {band}) (n={len(recs)}) ---", file=sys.stderr)
        cell_no_formula_ids: list[str] = []
        for fn in CELL_ASSERTIONS:
            result = fn(recs, band, market_type)
            if result.no_formula:
                print(f"  [{result.aid}] {result.name}: NO_FORMULA for this cell — not evaluated", file=sys.stderr)
                lines.append(result.to_jsonl_line())
                cell_no_formula_ids.append(result.aid)
                total_no_formula += 1
                continue
            total_assertions_run += 1
            total_violations += result.n_violations
            flag = "ALARM" if result.n_violations else "clean"
            print(
                f"  [{result.aid}] {result.name}: n={result.n_applicable} "
                f"absent={result.n_absent} violations={result.n_violations} ({flag})",
                file=sys.stderr,
            )
            lines.append(result.to_jsonl_line())

        n_cell_assertions_total = len(CELL_ASSERTIONS)
        n_no_formula = len(cell_no_formula_ids)
        n_evaluated = n_cell_assertions_total - n_no_formula
        lines.append({
            "type": "cell_formula_coverage",
            "market_type": market_type,
            "band": band,
            "n_assertions_total": n_cell_assertions_total,
            "n_evaluated": n_evaluated,
            "n_no_formula": n_no_formula,
            "no_formula_ids": cell_no_formula_ids,
        })
        if n_no_formula:
            cells_with_incomplete_formula_coverage.append(cell_label)
            print(
                f"  COVERAGE cell=({market_type}, {band}): {n_evaluated}/{n_cell_assertions_total} "
                f"assertions evaluated — {n_no_formula} NOT EVALUATED (NO_FORMULA: "
                f"{','.join(cell_no_formula_ids)}). Do not read these as clean — "
                f"they were never checked. (T-509)",
                file=sys.stderr,
            )
        else:
            print(
                f"  COVERAGE cell=({market_type}, {band}): {n_evaluated}/{n_cell_assertions_total} "
                f"assertions evaluated — full formula coverage.",
                file=sys.stderr,
            )

    # GG-191-pattern loud reporting: a record whose market_type could not be
    # placed in the registered enum is never silently dropped or folded into
    # a known cell (see positions_by_cell()). Surface it here, once, with
    # full (raw_value, band) provenance.
    if _UNKNOWN_MARKET_TYPE_COUNTS:
        total_unknown = sum(_UNKNOWN_MARKET_TYPE_COUNTS.values())
        print(
            f"\n[UNKNOWN_MARKET_TYPE] {total_unknown} record(s) across "
            f"{len(_UNKNOWN_MARKET_TYPE_COUNTS)} (raw_market_type, band) group(s) had a "
            "missing or unregistered market_type field and were grouped under "
            "UNKNOWN_MARKET_TYPE rather than a real cell — CELL_ASSERTIONS report "
            "NO_FORMULA for these, not clean:",
            file=sys.stderr,
        )
        for (raw_mt, b), n in sorted(_UNKNOWN_MARKET_TYPE_COUNTS.items(), key=lambda kv: -kv[1]):
            print(f"    raw_market_type={raw_mt!r} band={b}: {n} record(s)", file=sys.stderr)
        lines.append({
            "type": "unknown_market_type_summary",
            "total_records": total_unknown,
            "groups": [
                {"raw_market_type": raw_mt, "band": b, "n": n}
                for (raw_mt, b), n in sorted(_UNKNOWN_MARKET_TYPE_COUNTS.items(), key=lambda kv: -kv[1])
            ],
        })

    summary = {
        "type": "run_summary",
        "mode": "alarm-only",
        "strict": strict,
        "total_bands": len(by_band),
        "total_cells": len(by_cell),
        "total_assertions_run": total_assertions_run,
        "total_violations": total_violations,
        "total_no_formula": total_no_formula,
        "bands_with_incomplete_formula_coverage": bands_with_incomplete_formula_coverage,
        "cells_with_incomplete_formula_coverage": cells_with_incomplete_formula_coverage,
        "total_unknown_market_type_records": sum(_UNKNOWN_MARKET_TYPE_COUNTS.values()),
    }
    lines.append(summary)

    print("\n" + "=" * 78, file=sys.stderr)
    print(
        f"SUMMARY: {total_violations} total violations across {total_assertions_run} "
        f"band-scoped + cell-scoped assertion runs. ALARM-ONLY: this does not fail the build.",
        file=sys.stderr,
    )
    if total_no_formula:
        print(
            f"COVERAGE: {total_no_formula} (band, assertion) + (cell, assertion) pairs were "
            f"NOT EVALUATED (NO_FORMULA) — these are NOT counted as clean above. Incomplete "
            f"bands: {', '.join(bands_with_incomplete_formula_coverage) or 'none'}. Incomplete "
            f"cells: {', '.join(cells_with_incomplete_formula_coverage) or 'none'}. See "
            f"per-band/per-cell COVERAGE lines above. (T-466/T-509)",
            file=sys.stderr,
        )
    print("=" * 78, file=sys.stderr)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        for line in lines:
            f.write(json.dumps(line, default=str) + "\n")
    print(f"\nMachine-readable report written to {report_path}", file=sys.stderr)

    if strict and total_violations > 0:
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--t1-portfolio", type=Path, default=DEFAULT_T1_PORTFOLIO)
    p.add_argument("--t4-portfolio", type=Path, default=DEFAULT_T4_PORTFOLIO)
    p.add_argument("--outcome-store", type=Path, default=DEFAULT_OUTCOME_STORE)
    p.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    p.add_argument(
        "--strict", action="store_true", default=False,
        help="Reserved for future promotion. OFF by default, wired to nothing. "
        "When passed, exits 1 if any violation was found; otherwise exit is always 0.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return run(args.t1_portfolio, args.t4_portfolio, args.outcome_store, args.report_path, args.strict)
    except Exception as e:  # noqa: BLE001 — alarm-only: a crash in this suite must never propagate as a gate failure
        print(f"[ASSERT_LEDGER_INVARIANTS ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        return 0 if not args.strict else 1


if __name__ == "__main__":
    sys.exit(main())
