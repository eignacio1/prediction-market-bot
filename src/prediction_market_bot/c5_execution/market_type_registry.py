"""
C5: Market-Type Registry
=========================
Module:   c5_execution.market_type_registry
Phase:    Phase 7 (Market Expansion Phase 1, box 1.1 — abstraction repair)
Purpose:  Single source of truth mapping (market family, execution band) pairs
          to their coverage status and Kalshi series ticker.

Why this exists (04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md, box 1.1):
  Before this module, `market_mapper.py` had no concept of a market type at
  all — it only normalizes player names within the one family the bot
  currently trades. `kalshi_client.py` hardcoded two bare series-ticker
  constants. Neither file could answer "what markets exist, on what bands,
  and which have we already measured and rejected."

Design constraint (02_ARCHITECTURE_DESIGN/COVERAGE_TARGET_MATRIX.md):
  Cells are keyed on the PAIR (MarketType, ExecutionBand), not on market type
  alone. The coverage target is ~25 cells: {player prop, moneyline, run line,
  game total, team total} x {T1, T2, T3, T4, T5}. A market type alone cannot
  express "player props are ACTIVE at T4M-PROJ but NOT_IMPLEMENTED at T1" —
  the band is not a detail, it is half the key.

RULED_OUT is a first-class status, not an absence: a cell ruled out on
measured depth (Phase 0-I) is a COMPLETED cell, distinct from
NOT_IMPLEMENTED (never measured). RULED_OUT cells must carry a reason and a
measurement date so Phase 4 does not re-litigate settled cells.

As of this module's construction (2026-08-12), Phase 0-I's 360-obs/family
depth verdict flagged PLAYER_PROP and PARTIAL_GAME_WINNER as FAIL against an
earlier 3-obs pre-slate sample giving the opposite read on GAME_TOTAL/
RUN_LINE. The operator's standing instruction is that neither read has been
promoted to a kill decision ("neither declared dead") — so no MLB cell below
is seeded RULED_OUT. The status exists and is exercised by tests; it is
simply unused by live data pending an explicit operator verdict.

This module does not change ExecutionBand, BAND_CONFIGS, or any kelly_fraction
— it imports ExecutionBand read-only from execution_bands.py as the band half
of the registry key. Extending BAND_CONFIGS itself is Phase 3 (segmented pool
infrastructure), not this box.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

from prediction_market_bot.execution_bands import ExecutionBand


# ---------------------------------------------------------------------------
# Market type enum
# ---------------------------------------------------------------------------


class MarketType(Enum):
    """
    A tradeable market family, scoped by sport where the family is
    sport-specific (player prop families do not share a series across sports).

    MLB families match the rows of COVERAGE_TARGET_MATRIX.md exactly, using
    the same Phase-0 ticker-confirmed series. NBA_PLAYER_POINTS is the one
    pre-existing family outside that matrix — the legacy NBA points market
    the bot traded before MLB became the active pool. It is carried here only
    so kalshi_client.py's existing NBA constant can resolve through the
    registry like everything else; it is not part of the MLB coverage target
    and this module does not expand its own cell coverage.
    """
    MLB_PLAYER_PROP_HITS = "mlb_player_prop_hits"
    MLB_MONEYLINE = "mlb_moneyline"
    MLB_RUN_LINE = "mlb_run_line"
    MLB_GAME_TOTAL = "mlb_game_total"
    MLB_TEAM_TOTAL = "mlb_team_total"
    MLB_PARTIAL_GAME = "mlb_partial_game"  # F3/F5/F7 derivatives (Phase 0 ticker-confirmed)
    NBA_PLAYER_POINTS = "nba_player_points"  # legacy; dark/frozen, not an MLB coverage-target row


# Series ticker is a property of the market family, not of (family, band) — the
# same series is evaluated by whichever band's decision tree fires on it.
_SERIES_TICKER_BY_MARKET_TYPE: dict[MarketType, str] = {
    MarketType.MLB_PLAYER_PROP_HITS: "KXMLBHIT",
    MarketType.MLB_MONEYLINE: "KXMLBGAME",
    MarketType.MLB_RUN_LINE: "KXMLBSPREAD",
    MarketType.MLB_GAME_TOTAL: "KXMLBTOTAL",
    MarketType.MLB_TEAM_TOTAL: "KXMLBTEAMTOTAL",
    MarketType.MLB_PARTIAL_GAME: "KXMLBF3",  # F3 as the representative partial-game ticker
    MarketType.NBA_PLAYER_POINTS: "KXNBAPTS",
}


def series_ticker_for(market_type: MarketType) -> str:
    """Return the Kalshi series ticker for a market family."""
    return _SERIES_TICKER_BY_MARKET_TYPE[market_type]


# ADR-0053 §6.3 item 1: reverse ticker->market_type lookup. Named as a
# sub-dependency of item 2 (market_type on the resolved-bet ledger, out of
# scope for T-453 -- see Block J), needed there to backfill/derive
# market_type for ledger rows written before that field existed. Buildable
# independently of item 2, so it ships now. Every series ticker above is
# distinct, so this reverse map is bijective and needs no collision handling.
_MARKET_TYPE_BY_SERIES_TICKER: dict[str, MarketType] = {
    ticker: market_type for market_type, ticker in _SERIES_TICKER_BY_MARKET_TYPE.items()
}


def market_type_for_series_ticker(ticker: str) -> MarketType:
    """Reverse of series_ticker_for(). Raises KeyError on an unknown ticker,
    matching get_cell()'s loud-failure convention for an unseeded key."""
    return _MARKET_TYPE_BY_SERIES_TICKER[ticker]


def market_type_for_ticker(kalshi_ticker: str) -> MarketType:
    """ADR-0053 §6.3 item 2: derive market_type from a full Kalshi ticker
    (e.g. 'KXMLBHIT-26JUN241607BALLAA-...') by extracting its series prefix.
    Read-time derivation only -- never mutates stored ledger data (GG-077
    defense-in-depth pattern). Raises KeyError on an unknown series prefix."""
    return market_type_for_series_ticker(kalshi_ticker.split("-")[0])


# ---------------------------------------------------------------------------
# Cell status enum
# ---------------------------------------------------------------------------


class CellStatus(Enum):
    """
    Coverage status of a single (MarketType, ExecutionBand) cell.

    ACTIVE:
        Currently placing live (paper) bets.
    BLOCKED:
        Built, but gated behind an unmet activation condition (an unrun EXP,
        an unactivated Phase 8 gate, a live-wiring gap) — not a measurement
        verdict, a build/governance gate.
    NOT_IMPLEMENTED:
        No build exists for this cell. The default state for an unseeded
        cell in a family/band's coverage.
    RULED_OUT:
        Measured (depth, liquidity, or model-fit) and rejected. A completed
        cell, not a gap — see `reason` and `measured_date`, both required.
    DARK:
        Built and previously or potentially active, currently paused for a
        reason unrelated to measurement (sport tabled, off-season, etc.).
    SHADOW:
        Paper-evaluate this cell without betting (Phase 4 box 4.1, "shadow
        mode per family"). Distinct from NOT_IMPLEMENTED (never evaluated),
        ACTIVE (live betting), and BLOCKED (implemented but gated) — added
        per ADR-0053 §6.2, which also considered and rejected adding a
        SCOPING member as redundant with the already-shipped NOT_IMPLEMENTED.
    """
    ACTIVE = "active"
    BLOCKED = "blocked"
    NOT_IMPLEMENTED = "not_implemented"
    RULED_OUT = "ruled_out"
    DARK = "dark"
    SHADOW = "shadow"


# ---------------------------------------------------------------------------
# Registry cell
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarketTypeCell:
    """
    A single (MarketType, ExecutionBand) coverage cell.

    `reason` and `measured_date` are required when `status is RULED_OUT`
    (enforced in `__post_init__`) — a RULED_OUT cell without a reason and a
    date is indistinguishable from an unmeasured NOT_IMPLEMENTED cell, which
    defeats the entire point of the status.

    `citing_decision` (ADR-0053 §6.3 item 5) is a pointer to the DECISION_LOG
    / GG / ADR entry that ruled the cell out — distinct from the free-text
    `reason` above. It is NOT enforced at construction time (unlike `reason`/
    `measured_date`): the registry today seeds zero RULED_OUT cells (no
    family has been promoted to a kill decision yet — "neither declared
    dead"), so there is no seeded case to validate against, and requiring it
    here would break the existing `test_ruled_out_with_both_fields_succeeds`
    regression test for no corresponding safety gain. The real teeth live in
    `promote_cell_status()` below: a RULED_OUT cell cannot be promoted to
    SHADOW/ACTIVE without supplying a superseding reference at promotion
    time, which is where ADR-0053 §2.4 actually places the guard ("refuse to
    move a RULED_OUT cell... without an explicit superseding decision
    reference").
    """
    market_type: MarketType
    band: ExecutionBand
    status: CellStatus
    reason: Optional[str] = None
    measured_date: Optional[date] = None
    notes: Optional[str] = None
    citing_decision: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status is CellStatus.RULED_OUT:
            if not self.reason:
                raise ValueError(
                    f"RULED_OUT cell ({self.market_type}, {self.band}) requires a reason"
                )
            if self.measured_date is None:
                raise ValueError(
                    f"RULED_OUT cell ({self.market_type}, {self.band}) requires a measured_date"
                )

    @property
    def series_ticker(self) -> str:
        return series_ticker_for(self.market_type)


CellKey = tuple[MarketType, ExecutionBand]


# ---------------------------------------------------------------------------
# Registry — single source of truth
# ---------------------------------------------------------------------------
#
# Seed data sources (per T-439 instructions):
#   - COVERAGE_TARGET_MATRIX.md (2026-08-12, verified against origin/main 44e845b):
#     target matrix rows/columns, "1 cell of ~25" starting state, per-band
#     kelly_fraction/raw_n/clean_n status.
#   - 02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md § Live Registry (2026-07-19):
#     MLB T4M-PROJ ACTIVE; T4M-ARITH/T4M-FLOW built-but-BLOCKED pending their
#     own EXP; T4M-BOUNDARY/EVENT/LINEUP/PITCHER/STAGED/CORR/EXIT scoping-only
#     (NOT_IMPLEMENTED here, not modeled as separate cells — Tier B roster is
#     not authorized for implementation and adding cells for unauthorized
#     sub-bands would misrepresent scope as coverage).
#
# Only MLB_PLAYER_PROP_HITS decomposes T4 into MLB-native sub-bands — every
# other MLB family has no sub-band build at all, so its T4 column is the
# coarse ExecutionBand.T4_IN_PLAY aggregate, correctly NOT_IMPLEMENTED.

_MLB_COARSE_BANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T1_MULTI_DAY,
    ExecutionBand.T2_SAME_DAY,
    ExecutionBand.T3_PRE_TIP,
    ExecutionBand.T4_IN_PLAY,
    ExecutionBand.T5_LATE_GAME,
)

_OTHER_MLB_FAMILIES: tuple[MarketType, ...] = (
    MarketType.MLB_MONEYLINE,
    MarketType.MLB_RUN_LINE,
    MarketType.MLB_GAME_TOTAL,
    MarketType.MLB_TEAM_TOTAL,
    MarketType.MLB_PARTIAL_GAME,
)

_cells: list[MarketTypeCell] = [
    # --- MLB_PLAYER_PROP_HITS: the one family with MLB-native T4 sub-bands ---
    MarketTypeCell(MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T1_MULTI_DAY, CellStatus.NOT_IMPLEMENTED),
    MarketTypeCell(MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T2_SAME_DAY, CellStatus.NOT_IMPLEMENTED),
    MarketTypeCell(MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T3_PRE_TIP, CellStatus.NOT_IMPLEMENTED),
    MarketTypeCell(
        MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T4M_PROJ, CellStatus.ACTIVE,
        notes="ADR-0023; run_t4_mlb_live.py; the only cell placing live bets today.",
    ),
    MarketTypeCell(
        MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T4M_ARITH, CellStatus.BLOCKED,
        notes="ADR-0039; built+unit-tested (t4_mlb_execution_engine.py); gated on EXP-ARITH-MLB-01.",
    ),
    MarketTypeCell(
        MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T4M_FLOW, CellStatus.BLOCKED,
        notes="ADR-0039; gated on EXP-FLOW-MLB-01; score_diff live-wiring gap must also close.",
    ),
    MarketTypeCell(MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T5_LATE_GAME, CellStatus.NOT_IMPLEMENTED),

    # --- NBA legacy family: single cell, carried only for alias continuity ---
    MarketTypeCell(
        MarketType.NBA_PLAYER_POINTS, ExecutionBand.T4_IN_PLAY, CellStatus.DARK,
        notes="run_t4_live.py; built+deployed; dark — NBA tabled per operator directive "
              "(2026-07-01) independent of season; not part of the MLB coverage target.",
    ),
]

for _market_type in _OTHER_MLB_FAMILIES:
    for _band in _MLB_COARSE_BANDS:
        _cells.append(MarketTypeCell(_market_type, _band, CellStatus.NOT_IMPLEMENTED))

del _market_type, _band

MARKET_TYPE_REGISTRY: dict[CellKey, MarketTypeCell] = {
    (cell.market_type, cell.band): cell for cell in _cells
}


def get_cell(market_type: MarketType, band: ExecutionBand) -> MarketTypeCell:
    """
    Return the registry cell for (market_type, band).

    Raises KeyError if the pair has never been seeded — an unseeded pair is
    an error, not an implicit NOT_IMPLEMENTED, so a typo in a caller's band
    argument fails loudly instead of silently reporting no coverage.
    """
    return MARKET_TYPE_REGISTRY[(market_type, band)]


def cells_by_status(status: CellStatus) -> list[MarketTypeCell]:
    """Return every registered cell with the given status."""
    return [cell for cell in MARKET_TYPE_REGISTRY.values() if cell.status is status]


def cells_for_market_type(market_type: MarketType) -> list[MarketTypeCell]:
    """Return every registered cell for a market family, across all seeded bands."""
    return [cell for cell in MARKET_TYPE_REGISTRY.values() if cell.market_type is market_type]


def promote_cell_status(
    market_type: MarketType,
    band: ExecutionBand,
    new_status: CellStatus,
    *,
    superseding_reference: Optional[str] = None,
) -> MarketTypeCell:
    """
    Mutate MARKET_TYPE_REGISTRY in place, replacing the cell at (market_type,
    band) with a copy carrying new_status (ADR-0053 §6.3 item 5b — the first
    write path this registry has ever had; it was a static literal dict
    before this).

    Guard (ADR-0053 §2.4): a RULED_OUT cell may not be silently promoted to
    SHADOW or ACTIVE. That transition requires an explicit
    superseding_reference (a DECISION_LOG/GG/ADR pointer) — the same
    immutability discipline Hard Rule 3 gives ADRs, applied here at the
    cell-status level so a future session cannot silently re-open a cell
    someone already investigated and closed. Raises KeyError for an
    unseeded (market_type, band) pair, matching get_cell()'s convention.
    """
    key = (market_type, band)
    current = MARKET_TYPE_REGISTRY[key]

    if current.status is CellStatus.RULED_OUT and new_status in (
        CellStatus.SHADOW,
        CellStatus.ACTIVE,
    ):
        if not superseding_reference:
            raise ValueError(
                f"cannot promote RULED_OUT cell {key} to {new_status} without an "
                f"explicit superseding_reference (ADR-0053 §2.4 guard)"
            )

    new_cell = dataclasses.replace(
        current,
        status=new_status,
        citing_decision=superseding_reference or current.citing_decision,
    )
    MARKET_TYPE_REGISTRY[key] = new_cell
    return new_cell


# ---------------------------------------------------------------------------
# Per-cell measurement state (ADR-0053 §2.2 / §6.3 item 3)
# ---------------------------------------------------------------------------
#
# Deliberately NOT fields on MarketTypeCell. MarketTypeCell is a frozen,
# hand-reviewed literal describing what a cell IS (family, band, coverage
# status) — the 33 seeded cells above are edited by a human and reviewed in
# a diff. clean_n/n_star are runtime-computed numbers that change every time
# scripts/run_power_calc.py re-derives them against the resolved-bet ledger
# (see the SAMPLE ADEQUACY section of .claude/hooks/governance_scan.sh,
# which already computes these live rather than reading a stored constant —
# this project's own remediation-pass history is full of doc-embedded
# numbers going stale between edits; baking a live number into a frozen
# literal reintroduces exactly that failure mode). A separate CellKey-keyed
# mutable store keeps the registry a stable, reviewable artifact while
# giving measurement state the same lookup key.
#
# Not populated by this session. §6.3 item 2 (market_type on the
# resolved-bet ledger) is the load-bearing dependency this needs to group
# real ledger rows by cell instead of by band alone — item 2 is explicitly
# out of scope here (Block J). This is the container Phase 3.3/3.4 tooling
# writes into once item 2 lands; get_measurement() returns an honest
# unmeasured default for every cell today.


@dataclass
class CellMeasurement:
    """Mutable per-cell sample-adequacy measurement. See module-level comment above."""
    clean_n: int = 0
    n_star: Optional[int] = None
    computed_at: Optional[date] = None


_CELL_MEASUREMENTS: dict[CellKey, CellMeasurement] = {}


def get_measurement(market_type: MarketType, band: ExecutionBand) -> CellMeasurement:
    """Return the cell's measurement state, or an unmeasured default. Never
    raises — an un-populated cell is honestly "not yet measured," not an error."""
    return _CELL_MEASUREMENTS.get((market_type, band), CellMeasurement())


def set_measurement(
    market_type: MarketType, band: ExecutionBand, measurement: CellMeasurement
) -> None:
    """Write path for future Phase 3.3/3.4 tooling (scripts/run_power_calc.py
    scoped per-cell). Unused by any shipped caller today — named seam, not wired."""
    _CELL_MEASUREMENTS[(market_type, band)] = measurement


# ---------------------------------------------------------------------------
# Per-cell kill-switch state (ADR-0053 §2.3 / §6.3 item 4, Phase 3 box 3.5)
# ---------------------------------------------------------------------------
#
# Same mutable-store-keyed-by-CellKey shape as CellMeasurement above, for the
# same reason, plus one specific to kill-switch state: C4's live kill-switch
# check (risk.py) is today implicitly band-scoped because only one cell
# exists system-wide. Making C4/C7 resolve which cell an incoming bet
# belongs to *before* checking halt state — so halting (run_line, T4M-PROJ)
# does not touch (hits, T4M-PROJ) — is a real change to a live risk-control
# path and is explicitly OUT of scope for this session (T-453). This section
# ships the state and a resolution helper only; nothing here is called from
# risk.py, paper_trader.py, or execution_bands.py. The live wiring is
# registered as its own follow-on task — see the session report.


class CellKillSwitchStatus(Enum):
    ACTIVE = "active"
    HALTED = "halted"


@dataclass
class CellKillSwitchState:
    """Per-cell kill-switch state. See module-level comment above."""
    status: CellKillSwitchStatus = CellKillSwitchStatus.ACTIVE
    reason: Optional[str] = None
    halted_at: Optional[datetime] = None


_CELL_KILL_SWITCH_STATE: dict[CellKey, CellKillSwitchState] = {}


def resolve_kill_switch_state(
    market_type: MarketType, band: ExecutionBand
) -> CellKillSwitchState:
    """Cell-resolution helper (ADR-0053 §2.3). Returns an ACTIVE default for
    any cell with no recorded halt — never raises. NOT called by C4/C7
    today; wiring the live kill-switch path to resolve per-cell state before
    checking halt status is future work (see the session report)."""
    return _CELL_KILL_SWITCH_STATE.get((market_type, band), CellKillSwitchState())


def halt_cell(market_type: MarketType, band: ExecutionBand, reason: str) -> CellKillSwitchState:
    """Write path for a future C4/C7 wiring session. Unused by any shipped
    caller today — named seam, not wired."""
    state = CellKillSwitchState(
        status=CellKillSwitchStatus.HALTED, reason=reason, halted_at=datetime.utcnow()
    )
    _CELL_KILL_SWITCH_STATE[(market_type, band)] = state
    return state


# ---------------------------------------------------------------------------
# Legacy alias constants (box 1.3) — resolve through the registry so nothing
# downstream (venue_adapter.py, run_t2/t3/t4_mlb_*.py, tests) has to change.
# ---------------------------------------------------------------------------

SERIES_PLAYER_POINTS: str = series_ticker_for(MarketType.NBA_PLAYER_POINTS)
SERIES_MLB_PLAYER_HITS: str = series_ticker_for(MarketType.MLB_PLAYER_PROP_HITS)
