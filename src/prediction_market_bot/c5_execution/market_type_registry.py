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
import re
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

    # T-474 (NFL skeleton spike, ADR-0056 §2/D1, GG-198): the four standard
    # game-level mechanisms. Series tickers confirmed live against Kalshi's
    # /series and /events endpoints 2026-08-21 -- NOT guessed from the MLB
    # pattern (explicit task instruction). All four are scope="Game"/full-game
    # markets (KXNFL*GAME/SPREAD/TOTAL/TEAMTOTAL), distinct from the ~100
    # quarter/half-scoped NFL series (KXNFL1QSPREAD etc.) which are out of
    # scope for this spike.
    NFL_MONEYLINE = "nfl_moneyline"
    NFL_SPREAD = "nfl_spread"
    NFL_GAME_TOTAL = "nfl_game_total"
    NFL_TEAM_TOTAL = "nfl_team_total"

    # T-495 (NHL skeleton spike, ADR-0056 §2/D1, EXP-024): mirrors T-474's NFL
    # pattern exactly. Series tickers confirmed live against Kalshi's /series
    # and /events endpoints 2026-08-25 -- measured, not guessed from NFL/MLB's
    # shape (same discipline the task instructed). Only THREE families are
    # seeded here, not the full four-family target list: no live NHL
    # team-total series was found on Kalshi as of the confirmation date (full
    # 3512-series Sports-category listing checked; KXNHLTOTAL is game-scoped
    # "Point Total", KXNHLPTS is player-scoped "Player Points" -- neither is a
    # team-total market, and no other NHL+team-total series exists). Adding an
    # NHL_TEAM_TOTAL member without a real backing ticker would fabricate a
    # value in _SERIES_TICKER_BY_MARKET_TYPE and break
    # test_round_trips_for_every_market_type. Registered as GG-217 (OPEN)
    # rather than silently omitted or guessed.
    NHL_MONEYLINE = "nhl_moneyline"
    NHL_PUCK_LINE = "nhl_puck_line"
    NHL_GAME_TOTAL = "nhl_game_total"


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
    # T-474: confirmed live 2026-08-21 via curl against
    # https://external-api.kalshi.com/trade-api/v2/series?category=Sports and
    # per-series /events lookups -- each returned open/scheduled NFL preseason
    # events (e.g. KXNFLGAME-26AUG21NYJPIT) at the time of confirmation.
    MarketType.NFL_MONEYLINE: "KXNFLGAME",
    MarketType.NFL_SPREAD: "KXNFLSPREAD",
    MarketType.NFL_GAME_TOTAL: "KXNFLTOTAL",
    MarketType.NFL_TEAM_TOTAL: "KXNFLTEAMTOTAL",
    # T-495: confirmed live 2026-08-25 via curl against
    # https://api.elections.kalshi.com/trade-api/v2/series?category=Sports and
    # per-series /events lookups -- each returned real 2026 Stanley Cup Finals
    # events (e.g. KXNHLGAME-26JUN14CARVGK). No KXNHLTEAMTOTAL entry -- see
    # GG-217; NHL_TEAM_TOTAL is intentionally not a MarketType member.
    MarketType.NHL_MONEYLINE: "KXNHLGAME",
    MarketType.NHL_PUCK_LINE: "KXNHLSPREAD",
    MarketType.NHL_GAME_TOTAL: "KXNHLTOTAL",
}


def series_ticker_for(market_type: MarketType) -> str:
    """Return the Kalshi series ticker for a market family."""
    return _SERIES_TICKER_BY_MARKET_TYPE[market_type]


# ---------------------------------------------------------------------------
# Sport attribute (ADR-0056 §2/D1, GG-198) — map form, per the operator's
# signed decision (either an enum property or this map satisfies D1; APR-0032
# frames the map as the direct mechanical parallel to
# _SERIES_TICKER_BY_MARKET_TYPE above, so an implementing session defaults to
# it absent a concrete reason otherwise).
# ---------------------------------------------------------------------------

_SPORT_BY_MARKET_TYPE: dict[MarketType, str] = {
    MarketType.MLB_PLAYER_PROP_HITS: "mlb",
    MarketType.MLB_MONEYLINE: "mlb",
    MarketType.MLB_RUN_LINE: "mlb",
    MarketType.MLB_GAME_TOTAL: "mlb",
    MarketType.MLB_TEAM_TOTAL: "mlb",
    MarketType.MLB_PARTIAL_GAME: "mlb",
    MarketType.NBA_PLAYER_POINTS: "nba",
    MarketType.NFL_MONEYLINE: "nfl",
    MarketType.NFL_SPREAD: "nfl",
    MarketType.NFL_GAME_TOTAL: "nfl",
    MarketType.NFL_TEAM_TOTAL: "nfl",
    MarketType.NHL_MONEYLINE: "nhl",
    MarketType.NHL_PUCK_LINE: "nhl",
    MarketType.NHL_GAME_TOTAL: "nhl",
}

# Fail-closed enforcement (ADR-0056 §2's enforcement clause): a MarketType
# member missing from this map is a construction-time failure, not a silent
# gap, mirroring MarketTypeCell.__post_init__'s existing RULED_OUT-requires-
# reason precedent. Runs once at import time -- catches a future member added
# to the enum without a matching sport entry before any cell can be seeded
# against it.
_missing_sport_mappings = [mt for mt in MarketType if mt not in _SPORT_BY_MARKET_TYPE]
if _missing_sport_mappings:
    raise RuntimeError(
        f"MarketType member(s) missing from _SPORT_BY_MARKET_TYPE (ADR-0056 §2, D1): "
        f"{_missing_sport_mappings!r} -- every MarketType member requires a sport entry, "
        f"fail-closed by design."
    )
del _missing_sport_mappings


def sport_for(market_type: MarketType) -> str:
    """Return the sport code for a market family (ADR-0056 §2/D1)."""
    return _SPORT_BY_MARKET_TYPE[market_type]


# ADR-0053 §6.3 item 1: reverse ticker->market_type lookup. Named as a
# sub-dependency of item 2 (market_type on the resolved-bet ledger, out of
# scope for T-453 -- see Block J), needed there to backfill/derive
# market_type for ledger rows written before that field existed. Buildable
# independently of item 2, so it ships now.
#
# T-472/GG-191 (2026-08-20): MLB_PARTIAL_GAME's forward entry above points at
# KXMLBF3 as "the representative partial-game ticker" -- fine as a forward
# label (series_ticker_for() must return one value), but KXMLBF5 and KXMLBF7
# are real, separately-registered tickers for the same MarketType
# (COVERAGE_TARGET_MATRIX.md line 41 lists the row as KXMLBF3/F5/F7) that a
# pure inversion of the forward map can never produce -- market_type_for_ticker
# raised KeyError on both, verified against the live registry. _ALIASES below
# adds the missing reverse-only entries without touching series_ticker_for()'s
# single-value forward contract. The map is no longer a pure bijection of
# _SERIES_TICKER_BY_MARKET_TYPE once these are merged in -- it is deliberately
# many-to-one for MLB_PARTIAL_GAME.
_MARKET_TYPE_BY_SERIES_TICKER_ALIASES: dict[str, MarketType] = {
    "KXMLBF5": MarketType.MLB_PARTIAL_GAME,
    "KXMLBF7": MarketType.MLB_PARTIAL_GAME,
}

_MARKET_TYPE_BY_SERIES_TICKER: dict[str, MarketType] = {
    **{ticker: market_type for market_type, ticker in _SERIES_TICKER_BY_MARKET_TYPE.items()},
    **_MARKET_TYPE_BY_SERIES_TICKER_ALIASES,
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
# Ticker date/team-code grammar (T-472/GG-191, 2026-08-20)
# ---------------------------------------------------------------------------
#
# GG-166/GG-170/GG-185 were all instances of the same defect: a MLB-only,
# KXMLBHIT-only regex (duplicated verbatim in run_t4_mlb_live.py and
# run_resolve_mlb.py) that silently fell back to the session wall-clock date
# whenever it failed to match -- which is every non-KXMLBHIT ticker, since
# the pattern is hardcoded to that one series' literal prefix. That defect's
# blast radius was 0% while only KXMLBHIT traded (confirmed empirically:
# 2948/2948 rows in logs/t4_mlb_resolved_ledger.jsonl are KXMLBHIT) but
# becomes 100% of any newly-activated cell the moment Phase 2 turns on
# KXMLBTOTAL or another series -- this is a precondition on Phase 2, not on
# any new sport.
#
# The fix is two-part: (1) register a grammar per series here, alongside the
# series registry itself, instead of a parallel ad hoc regex per call site;
# (2) refuse (raise) rather than fall back on a non-match -- see
# TickerDateParseError. Callers must not catch this exception and substitute
# a fallback value; they must skip/refuse the write.
#
# Two known shapes, empirically validated against every ticker in production
# logs (2948/2948 MLB tickers across logs/t4_mlb_resolved_ledger.jsonl +
# other logs/*.jsonl; 158/158 NBA tickers across
# logs/.vps_portfolio_cache_nba.json) -- do not assume a third series
# introduces a third shape without re-validating against real data first:
#
#   MLB:  <YY><MON><DD><HHMM><TEAMS...>   e.g. 26AUG011610MIANYM   (has HHMM)
#   NBA:  <YY><MON><DD><TEAMS...>          e.g. 26JUN05NYKSAS       (no HHMM)
#
# TEAMS is left as a raw, unsplit blob (`teams_raw`) -- splitting it into
# (away, home) requires a team-abbreviation table, which is Block H's job
# (ADR-0054 §5.2 correlation key), not this module's. The team-code
# character class is `[A-Z0-9]+`, not `[A-Z]+`: doubleheader tickers append
# a digit-bearing G1/G2 suffix to the team blob (e.g. ...TBBOSG1-...), which
# an letters-only class silently fails to match -- found empirically as
# 21/2948 real-ticker failures during grammar validation, fixed by widening
# the class, re-validated at 0/2948 failures.


class TickerDateParseError(ValueError):
    """Raised when a ticker's embedded date/team-code tail does not match its
    series' registered grammar. Callers MUST refuse the write on this error
    -- never substitute a fallback/wall-clock date (GG-166/GG-191)."""


@dataclass(frozen=True)
class ParsedTicker:
    """Result of parsing a ticker's embedded date and raw team-code blob."""

    game_date: str
    teams_raw: str


_TICKER_DATE_MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}


@dataclass(frozen=True)
class TickerGrammar:
    """A series family's ticker tail grammar -- everything after the first
    '-' separator. Prefix-agnostic by design: MLB_PARTIAL_GAME's three
    series (KXMLBF3/F5/F7) share one date shape, so the grammar must not be
    keyed to a single literal prefix."""

    tail_pattern: "re.Pattern[str]"
    has_hhmm: bool

    def parse(self, ticker: str) -> ParsedTicker:
        _prefix, sep, tail = ticker.partition("-")
        if not sep:
            raise TickerDateParseError(f"ticker {ticker!r} has no series separator")
        m = self.tail_pattern.match(tail)
        if not m:
            raise TickerDateParseError(
                f"ticker {ticker!r} does not match its series' date grammar"
            )
        if self.has_hhmm:
            yy, mon, dd, _hhmm, teams = m.groups()
        else:
            yy, mon, dd, teams = m.groups()
        month = _TICKER_DATE_MONTHS.get(mon)
        if month is None:
            raise TickerDateParseError(
                f"ticker {ticker!r} has unrecognized month token {mon!r}"
            )
        return ParsedTicker(game_date=f"20{yy}-{month}-{dd}", teams_raw=teams)


_MLB_TAIL = re.compile(r"^(\d{2})([A-Z]{3})(\d{2})(\d{4})([A-Z0-9]+)(?:-|$)")
_NBA_TAIL = re.compile(r"^(\d{2})([A-Z]{3})(\d{2})([A-Z0-9]+)(?:-|$)")

_MLB_GRAMMAR = TickerGrammar(_MLB_TAIL, has_hhmm=True)
_NBA_GRAMMAR = TickerGrammar(_NBA_TAIL, has_hhmm=False)

# T-474 (NFL skeleton spike): measured, not assumed, per the task's explicit
# instruction ("This is unknown and must be MEASURED"). Confirmed live
# 2026-08-21 against real Kalshi event tickers under KXNFLGAME/KXNFLSPREAD/
# KXNFLTOTAL (e.g. KXNFLGAME-26AUG21NYJPIT, KXNFLTEAMTOTAL-26JAN25LASEA):
# NFL's shape is <YY><MON><DD><TEAMS...> -- NO HHMM segment. This matches
# NBA's grammar shape, not MLB's. A separate _NFL_TAIL/_NFL_GRAMMAR pair is
# registered rather than reusing _NBA_GRAMMAR directly, even though the
# pattern is textually identical today, so NFL's grammar can diverge later
# (e.g. a doubleheader-style suffix) without silently changing NBA's.
_NFL_TAIL = re.compile(r"^(\d{2})([A-Z]{3})(\d{2})([A-Z0-9]+)(?:-|$)")
_NFL_GRAMMAR = TickerGrammar(_NFL_TAIL, has_hhmm=False)

# T-495 (NHL skeleton spike): measured, not assumed. Confirmed live
# 2026-08-25 against real Kalshi event tickers under KXNHLGAME/KXNHLSPREAD/
# KXNHLTOTAL (e.g. KXNHLGAME-26JUN14CARVGK, KXNHLSPREAD-26JUN11VGKCAR):
# NHL's shape is <YY><MON><DD><TEAMS...> -- NO HHMM segment, matching NBA/
# NFL's grammar shape, not MLB's. A separate _NHL_TAIL/_NHL_GRAMMAR pair is
# registered rather than reusing _NFL_GRAMMAR directly, for the same reason
# _NFL_GRAMMAR wasn't folded into _NBA_GRAMMAR: identical shape today does
# not imply coupled evolution later.
_NHL_TAIL = re.compile(r"^(\d{2})([A-Z]{3})(\d{2})([A-Z0-9]+)(?:-|$)")
_NHL_GRAMMAR = TickerGrammar(_NHL_TAIL, has_hhmm=False)

_TICKER_GRAMMAR_BY_MARKET_TYPE: dict[MarketType, TickerGrammar] = {
    MarketType.MLB_PLAYER_PROP_HITS: _MLB_GRAMMAR,
    MarketType.MLB_MONEYLINE: _MLB_GRAMMAR,
    MarketType.MLB_RUN_LINE: _MLB_GRAMMAR,
    MarketType.MLB_GAME_TOTAL: _MLB_GRAMMAR,
    MarketType.MLB_TEAM_TOTAL: _MLB_GRAMMAR,
    MarketType.MLB_PARTIAL_GAME: _MLB_GRAMMAR,
    MarketType.NBA_PLAYER_POINTS: _NBA_GRAMMAR,
    MarketType.NFL_MONEYLINE: _NFL_GRAMMAR,
    MarketType.NFL_SPREAD: _NFL_GRAMMAR,
    MarketType.NFL_GAME_TOTAL: _NFL_GRAMMAR,
    MarketType.NFL_TEAM_TOTAL: _NFL_GRAMMAR,
    MarketType.NHL_MONEYLINE: _NHL_GRAMMAR,
    MarketType.NHL_PUCK_LINE: _NHL_GRAMMAR,
    MarketType.NHL_GAME_TOTAL: _NHL_GRAMMAR,
}


def parse_ticker_date(kalshi_ticker: str) -> ParsedTicker:
    """Series-agnostic date/team-blob parse. Raises KeyError if the ticker's
    series isn't registered (via market_type_for_ticker), or
    TickerDateParseError if it's registered but its tail doesn't match that
    series' grammar. Never returns a fallback value -- refusal-only by
    design (T-472/GG-191, superseding the fallback-to-wall-clock pattern
    that caused GG-166/GG-170/GG-185)."""
    market_type = market_type_for_ticker(kalshi_ticker)
    grammar = _TICKER_GRAMMAR_BY_MARKET_TYPE[market_type]
    return grammar.parse(kalshi_ticker)


def derive_game_date(kalshi_ticker: str) -> str:
    """Convenience wrapper for the common case -- most callers only need the
    embedded game date, not the raw team-code blob. Same refusal-only
    contract as parse_ticker_date(): raises, never falls back."""
    return parse_ticker_date(kalshi_ticker).game_date


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


# T-466: bands whose formula assertions (`assert_ledger_invariants.py`
# assertions [G] gross_edge_matches_band_formula, [I] adr0050_flat_stake_formula,
# [J] adr0050_contracts_cap) are actually evaluated rather than NO_FORMULA.
# NO_FORMULA is a silent pass — the assertion reports nothing, not "clean,"
# because it never ran — so a cell whose band is NOT in this set has zero
# formula-level protection against GG-166-style silent ledger corruption
# even if every other assertion in the suite reports clean.
#
# `ExecutionBand.value` is byte-identical to the band-label strings that
# script keys `GROSS_EDGE_VIG_MULTIPLIER` / `ADR_0050_BAND` against (verified
# T-466: T1_MULTI_DAY.value == "T1", T4M_PROJ.value == "T4M-PROJ", etc.), so
# this set can be expressed directly in ExecutionBand terms without importing
# the script into the package. There is no automated derivation — this set
# and the script's constants must be kept in lockstep BY HAND. If you add a
# band to either side, add it to the other in the same change.
#
# Current coverage (confirmed live 2026-08-18, T-466):
#   T1 (T1_MULTI_DAY):    [G] evaluated; [I]/[J] correctly N/A (ADR-0050 flat
#                          stake / contracts cap is T4M-PROJ-specific, not a
#                          T1 gap) -- included here on the strength of [G] alone.
#   T4M-PROJ (T4M_PROJ):  [G], [I], [J] all evaluated -- full coverage.
#   T2 (T2_SAME_DAY):     NO_FORMULA on all three -- NOT included. See GG-187.
#   All other bands:      no formula assertions written -- NOT included.
BANDS_WITH_FORMULA_ASSERTIONS: frozenset[ExecutionBand] = frozenset({
    ExecutionBand.T1_MULTI_DAY,
    ExecutionBand.T4M_PROJ,
})


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
        if self.status is CellStatus.ACTIVE:
            # T-466: a cell may not hold live-trading (ACTIVE) status unless
            # its band has formula-assertion coverage in
            # scripts/assert_ledger_invariants.py. Without this, GG-166-style
            # silent ledger corruption on a newly-activated band would have
            # zero formula-level detection, and the ledger script's own
            # NO_FORMULA output is easy to misread as "clean" (that misread
            # is the whole reason this gate exists).
            #
            # SHADOW is deliberately NOT gated here: it is the pre-formula,
            # no-capital-at-risk measurement-building phase (see CellStatus
            # docstring), and two existing regression tests
            # (test_promotion_without_guard_condition_succeeds,
            # test_ruled_out_to_shadow_with_superseding_reference_succeeds)
            # already promote uncovered bands to SHADOW and are expected to
            # keep succeeding. ACTIVE is where real capital risk is realized;
            # that is the line this gate draws.
            if self.band not in BANDS_WITH_FORMULA_ASSERTIONS:
                raise ValueError(
                    f"ACTIVE cell ({self.market_type}, {self.band}) requires formula-assertion "
                    f"coverage in scripts/assert_ledger_invariants.py before it may hold a "
                    f"live-trading status (T-466) — band {self.band} is NO_FORMULA. See "
                    f"BANDS_WITH_FORMULA_ASSERTIONS in this module."
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
    # T-597 D3: RECORDS REALITY, NOT PROMOTION. These three were NOT_IMPLEMENTED
    # while cron runs them daily (measured 2026-09-30). SHADOW = "paper-evaluate
    # without betting", which is what they do: kelly_fraction=0.0 for T1/T2/T3
    # (ADR-0048), so 0 bets. No band reassignment; no move toward ACTIVE.
    MarketTypeCell(
        MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW,
        notes="T-597 D3 records reality, not promotion. run_mlb_paper_trade.py cron 0 11 UTC; "
              "18-feature LR+Platt evaluates daily; kelly 0.0 (ADR-0048) so 0 bets; "
              "paper_portfolio_mlb.json last written 2026-08-06.",
        citing_decision="ADR-0048",
    ),
    MarketTypeCell(
        MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T2_SAME_DAY, CellStatus.SHADOW,
        notes="T-597 D3 records reality, not promotion. run_t2_mlb_sameday.py cron 30 19 UTC; "
              "evaluates lineup/scratch overlay daily; kelly 0.0 (ADR-0048); bets_placed=0.",
        citing_decision="ADR-0048",
    ),
    MarketTypeCell(
        MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T3_PRE_TIP, CellStatus.SHADOW,
        notes="T-597 D3 records reality, not promotion. run_t3_mlb_pretip.py every 15 min "
              "20-03 UTC; read-only drift scan, no order path; kelly 0.0 (ADR-0048). "
              "T-597 D2 verdict: MISFILED (shallow, not fast); reassignment is drafted only.",
        citing_decision="ADR-0048",
    ),
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

# --- T4 sub-bucket integration across the twelve game-market families
# (T-504/GG-226, 2026-08-29) ---
#
# Gap (verified live at session start): ExecutionBand carries 13 T4 sub-band
# members beyond the five coarse bands -- ten bare NBA-flavored ones
# (T4_STAGED, T4_EVENT, T4_LINEUP, T4_FLOW, T4_SENTIMENT, T4_PROJ, T4_ARITH,
# T4_BOUNDARY, T4_CORR, T4_EXIT) and three MLB-flavored ones (T4M_PROJ,
# T4M_ARITH, T4M_FLOW). Before this change, only MLB_PLAYER_PROP_HITS
# decomposed T4 at all; every other family (the five non-prop MLB families
# plus all NFL/NHL families) carried only the coarse T4_IN_PLAY aggregate.
#
# Decision rule applied per (family, sub-band) candidate pair -- structural,
# not strategic (per the operator directive governing this task: a family or
# sub-band is never declined on the strength of a finding about whether it
# would calibrate edge; declines here are about naming-namespace validity,
# not about hopelessness):
#
#   1. A sub-band cell may only be created against an ExecutionBand member
#      whose namespace matches the family's sport. ADR-0056 D2 grandfathers
#      MLB's T4M- prefix and NBA's bare T4_ prefix to their own sports
#      EXACTLY AS-IS and reserves the T4MLB-/T4NBA-/T4NFL-/T4NHL- prefixed
#      convention for every sub-band built from here forward -- for ANY
#      sport, not NFL/NHL alone. Reusing NBA's bare T4_* names (or MLB's
#      T4M_* names) for a different sport's family would misrepresent the
#      registry's own already-established one-roster-per-sport discipline,
#      the exact drift D2 exists to prevent.
#   2. Of the 13 sub-band members, only T4M_PROJ/T4M_ARITH/T4M_FLOW are
#      namespace-valid for MLB families; none of the 13 are namespace-valid
#      for NFL or NHL families (no T4NFL-/T4NHL- member exists -- T-474 and
#      T-495 explicitly left this unbuilt: "does not require building the
#      registry now"). Building the needed T4NFL-/T4NHL- members (and MLB's
#      own still-conceptual T4M-BOUNDARY/EVENT/LINEUP/PITCHER/STAGED/CORR/
#      EXIT Tier B roster) is an ExecutionBand edit in execution_bands.py --
#      outside this session's SCOPE FENCE (market_type_registry.py and its
#      tests only). This is the session's HARD STOP finding; see GG-226 in
#      GOVERNANCE_GAP_LOG.md rather than re-deriving it here.
#   3. Within the namespace-valid MLB set, each of the three sub-bands is
#      judged individually against the five non-prop MLB families:
#        - T4M_PROJ ("flat Binomial model" projecting a player's remaining
#          at-bats toward a hit threshold): player-scoped by construction --
#          no game-level analogue for who-wins/spread/total/team-total/
#          partial-game. DECLINED for all five.
#        - T4M_ARITH ("near-certain band between p_t4's 0.0/1.0 hard
#          boundaries"): the underlying concept -- late-state arithmetic
#          near-certainty -- is generic to any live score-state market (a
#          large, late run differential drives a moneyline or run line
#          toward 0/1 the same way an at-bat count drives a hit prop).
#          CREATED for all five, including MLB_PARTIAL_GAME (a partial-game
#          market resolves on the same live score state, just truncated to
#          fewer innings -- the near-certainty window arrives sooner, not
#          never).
#        - T4M_FLOW ("accumulated game-state/context pattern, incl.
#          FLOW-BLOWOUT tree"): blowout/momentum detection is directly a
#          function of score margin and pace -- the same signal a moneyline,
#          run line, or team-total decision tree would consume. CREATED for
#          all five, MLB_PARTIAL_GAME included for the same reasoning as
#          T4M_ARITH above.
#
# No new Kalshi series lookup was required for these cells: series_ticker_for
# is keyed on MarketType alone (see the module comment above --
# "the same series is evaluated by whichever band's decision tree fires on
# it"), and each family's ticker was already live-verified at T-439/T-474/
# T-495. A T4 sub-band cell routes a different decision tree against the
# SAME already-verified series, exactly like T4M_ARITH/T4M_FLOW already do
# for MLB_PLAYER_PROP_HITS/KXMLBHIT.
#
# All ten new cells below are NOT_IMPLEMENTED, no kelly_fraction touched
# (cells carry no kelly_fraction field -- that axis lives in
# execution_bands.py's BandConfig, untouched by this session), nothing wired.
_MLB_GAME_MARKET_T4_SUBBANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T4M_ARITH,
    ExecutionBand.T4M_FLOW,
)

for _market_type in _OTHER_MLB_FAMILIES:
    for _band in _MLB_GAME_MARKET_T4_SUBBANDS:
        _cells.append(MarketTypeCell(_market_type, _band, CellStatus.NOT_IMPLEMENTED))

# --- NFL (T-474 skeleton spike, ADR-0056 §5): seeded NOT_IMPLEMENTED only ---
# No NFL cell may be promoted above NOT_IMPLEMENTED by this session (explicit
# DO NOT list item) -- SHADOW is not authorized here (ADR-0056 §6 explicitly
# leaves CellStatus/kelly_fraction/activation untouched). No T4 sub-band
# decomposition is built for NFL in this spike (ADR-0056 D2 names the future
# T4NFL- prefix but does not require building the registry now), so every
# NFL family's T4 column is the coarse ExecutionBand.T4_IN_PLAY aggregate --
# same pattern as every non-decomposed MLB family above. Reusing
# _MLB_COARSE_BANDS here despite its MLB-scoped name: it is actually just
# "the five coarse ExecutionBand values," sport-agnostic in content though
# not in name. Renaming it is a naming-only change outside this session's
# single-deliverable scope -- see the breakage-list artifact.
_NFL_FAMILIES: tuple[MarketType, ...] = (
    MarketType.NFL_MONEYLINE,
    MarketType.NFL_SPREAD,
    MarketType.NFL_GAME_TOTAL,
    MarketType.NFL_TEAM_TOTAL,
)

for _market_type in _NFL_FAMILIES:
    for _band in _MLB_COARSE_BANDS:
        _cells.append(MarketTypeCell(_market_type, _band, CellStatus.NOT_IMPLEMENTED))

# --- NFL T4 sub-band cells (ADR-0062, T-524/GG-251, registry+scaffolding only) ---
# T4NFL-ARITH/T4NFL-FLOW now exist in execution_bands.py (conservative reading of
# ADR-0062 §4/§6's BOUNDARY conflict — see DECISION_LOG.md T-524 entry; BOUNDARY and
# EVENT are NOT built). Every NFL family gets both sub-bands, mirroring the MLB
# game-market pattern above (_MLB_GAME_MARKET_T4_SUBBANDS): all NOT_IMPLEMENTED, no
# kelly_fraction touched here (that axis lives in execution_bands.py's BandConfig,
# already 0.0 for both new members), nothing wired, nothing promoted.
_NFL_GAME_MARKET_T4_SUBBANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T4NFL_ARITH,
    ExecutionBand.T4NFL_FLOW,
)

for _market_type in _NFL_FAMILIES:
    for _band in _NFL_GAME_MARKET_T4_SUBBANDS:
        _cells.append(MarketTypeCell(_market_type, _band, CellStatus.NOT_IMPLEMENTED))

# --- NHL (T-495 skeleton spike, ADR-0056 §5, EXP-024): seeded NOT_IMPLEMENTED
# only, mirroring T-474's NFL pattern exactly. No NHL cell may be promoted
# above NOT_IMPLEMENTED by this session -- kelly_fraction=0.0 throughout,
# unchanged. Only three families seeded (moneyline/puck-line/game-total) --
# NHL_TEAM_TOTAL is not a MarketType member at all (no live Kalshi series;
# GG-217). No T4 sub-band decomposition is built (ADR-0056 D2 names the
# future T4NHL- prefix but does not require building the registry now); every
# NHL family's T4 column is the coarse ExecutionBand.T4_IN_PLAY aggregate.
_NHL_FAMILIES: tuple[MarketType, ...] = (
    MarketType.NHL_MONEYLINE,
    MarketType.NHL_PUCK_LINE,
    MarketType.NHL_GAME_TOTAL,
)

for _market_type in _NHL_FAMILIES:
    for _band in _MLB_COARSE_BANDS:
        _cells.append(MarketTypeCell(_market_type, _band, CellStatus.NOT_IMPLEMENTED))

# --- NHL T4 sub-band cells (ADR-0062, T-524/GG-251, registry+scaffolding only) ---
# Same rationale as the NFL block above: T4NHL-ARITH/T4NHL-FLOW only, both
# NOT_IMPLEMENTED, no kelly_fraction touched here, nothing wired, nothing promoted.
_NHL_GAME_MARKET_T4_SUBBANDS: tuple[ExecutionBand, ...] = (
    ExecutionBand.T4NHL_ARITH,
    ExecutionBand.T4NHL_FLOW,
)

for _market_type in _NHL_FAMILIES:
    for _band in _NHL_GAME_MARKET_T4_SUBBANDS:
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


# --- EXP-037 / T-608 (Wave 47.2): NFL pre-game SHADOW cells, flipped via promote_cell_status ---
# A cell flips to SHADOW only after at least one valid row for it exists in the
# pregame-shadow ledger (exp_output/PREGAME_SHADOW). SHADOW is evaluate-and-log: no order,
# position, paper fill or sizing path exists in the pregame_shadow package (enforced by
# tests/test_pregame_shadow_safety.py); kelly_fraction is untouched (ADR-0048).
# T1 flipped 2026-10-02 (live Week 5 rows banked: ML 50 / spread 637 / total 475 / team total 646
# ledger rows). T2 (4-8h) and T3 (15-60min) stay NOT_IMPLEMENTED until their first valid row.
# Pre-registration: 05_RESEARCH_EXPERIMENTS/EXP037_NFL_PREGAME_SHADOW_PREREGISTRATION_2026-10-02.md.
_EXP037_NFL_SHADOW_CELLS: tuple[tuple[MarketType, ExecutionBand], ...] = (
    (MarketType.NFL_MONEYLINE, ExecutionBand.T1_MULTI_DAY),
    (MarketType.NFL_SPREAD, ExecutionBand.T1_MULTI_DAY),
    (MarketType.NFL_GAME_TOTAL, ExecutionBand.T1_MULTI_DAY),
    (MarketType.NFL_TEAM_TOTAL, ExecutionBand.T1_MULTI_DAY),
)
for _mt, _bd in _EXP037_NFL_SHADOW_CELLS:
    promote_cell_status(_mt, _bd, CellStatus.SHADOW, superseding_reference="EXP-037")


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
