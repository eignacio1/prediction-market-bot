"""
NFL/game-market settlement derivation (T-527, GG-254 follow-on).

Adapter into the existing, already sport-agnostic settlement primitive
`paper_trader.py::settle_position()` (line ~915: `yes_won = actual_stat >=
threshold`). That primitive is unmodified by this module (GG-034 file-lock
invariant) — it already accepts any `(actual_stat, stat_label)` pair for any
market. What's missing, and what this module supplies, is the pure
computation of `actual_stat`/`stat_label` for the four NFL game-market types
(moneyline, spread, game total, team total) from a completed game's final
score plus the position's own ticker.

Design constraints (deliberate, see 04_EXECUTION/SESSION_CLAIMS.md T-527):

- Pure function, no I/O. Threshold is NOT an input here — `settle_position()`
  reads `threshold = pos["kalshi_threshold"]` from the position record at
  settlement time (populated when the position was opened, a different,
  out-of-scope code path), so this module never needs to parse or encode the
  numeric line. It only needs the *team identity* embedded in the ticker's
  strike suffix (the segment after the event ticker's second hyphen), never
  the numeric line encoded elsewhere on that same suffix.

- Team identity is accepted from the caller as Kalshi's own team-code
  alphabet (e.g. "BAL", "TEN") rather than full team names, to avoid a
  32-team name<->code mapping table that would be error-prone for
  multi-team-city cases (NYJ/NYG, LAR/LAC) and is not needed for this path.

- A moneyline is a spread at zero: NFL_MONEYLINE and NFL_SPREAD share the
  same actual_stat computation (point margin from the perspective of the
  ticker's named team). The only difference is the threshold the *caller*
  later compares it to (0 for moneyline; the stored line for spread) --
  irrelevant to this module.

Tie/push handling is intentionally NOT part of `derive_actual_stat()` itself
-- see `check_settlement_ambiguity()` below, which takes `threshold`
explicitly (only the resolver script has both values together) and raises
`SettlementAmbiguityError` rather than silently letting `>=` mis-settle:

- Moneyline exact tie (margin == 0): Kalshi's KXNFLGAME rules
  (NFLGAME.pdf, "Tie" provision) settle a tied game as a $0.50/$0.50 split
  payout on each side of the moneyline market, not a boolean Yes/No.
  `settle_position()`'s boolean win/loss model has no way to express a
  split payout -- this is the one genuine settlement-primitive gap found in
  this build, and it is upstream of any NFL-specific code: it would apply
  identically to a hypothetical MLB extra-innings-suspended tie. Register
  and stop (Hard Rule 11) rather than silently resolving it either way.

- Spread/total/team-total "push" (actual_stat == threshold exactly): real
  currently-listed Kalshi NFL spread/total/team-total strikes are always
  half-point lines (verified against live KXNFLSPREAD/KXNFLTOTAL/
  KXNFLTEAMTOTAL market data -- every observed strike suffix is X.5), so an
  exact-integer push is not currently reachable in practice. It is tested
  and refused anyway (defensive, per explicit instruction) because
  `FOOTBALLTOTALS`/spread contract text does not define an equal-to
  outcome, and a future non-half-point strike is not something this module
  should silently guess `>=` vs `>` on.
"""

from __future__ import annotations

import re

from prediction_market_bot.c5_execution.market_type_registry import MarketType

__all__ = [
    "SettlementAmbiguityError",
    "derive_actual_stat",
    "check_settlement_ambiguity",
]

# The four game-market types this module handles. Anything else is a
# programmer error at the call site (e.g. a player-prop MarketType), not a
# data problem -- raised as ValueError, not a silent no-op.
_SUPPORTED_MARKET_TYPES = frozenset(
    {
        MarketType.NFL_MONEYLINE,
        MarketType.NFL_SPREAD,
        MarketType.NFL_GAME_TOTAL,
        MarketType.NFL_TEAM_TOTAL,
    }
)

# Kalshi's real strike-suffix shapes, confirmed live against
# KXNFLGAME/KXNFLSPREAD/KXNFLTOTAL/KXNFLTEAMTOTAL market tickers (T-527):
#   moneyline      <TICKER>-...-<TEAMCODE>        e.g. ...-CHI
#   spread/team-tl <TICKER>-...-<TEAMCODE><DIGITS> e.g. ...-BAL42
#   game total     <TICKER>-...-<DIGITS>           e.g. ...-76
# One generic pattern captures all three shapes from the ticker's final
# hyphen-segment.
_STRIKE_SUFFIX_RE = re.compile(r"^([A-Z]*)(\d*)$")


class SettlementAmbiguityError(RuntimeError):
    """Raised when actual_stat/threshold would settle a real-money position
    ambiguously under settle_position()'s boolean >= model: a moneyline
    exact tie, or a spread/total/team-total exact push. The caller (resolver
    script) must not call settle_position() for a position that raises
    this -- refuse and surface it, do not guess a side."""


def _parse_strike_suffix(ticker: str) -> tuple[str, str]:
    """Extract (team_code, digits) from a ticker's final hyphen-segment.

    Raises ValueError if the ticker has no strike suffix (no '-') or the
    suffix doesn't match the known letters-then-digits shape.
    """
    if "-" not in ticker:
        raise ValueError(f"ticker {ticker!r} has no strike suffix (no '-')")
    suffix = ticker.rsplit("-", 1)[1]
    m = _STRIKE_SUFFIX_RE.match(suffix)
    if not m:
        raise ValueError(
            f"ticker {ticker!r} strike suffix {suffix!r} does not match the "
            f"known <TEAMCODE><DIGITS> shape"
        )
    team_code, digits = m.groups()
    return team_code, digits


def _team_score(
    yes_team: str,
    home_team_code: str,
    away_team_code: str,
    home_score: float,
    away_score: float,
) -> tuple[float, float]:
    """Return (yes_team_score, other_team_score), raising ValueError if
    yes_team matches neither the supplied home nor away code."""
    if yes_team == home_team_code:
        return home_score, away_score
    if yes_team == away_team_code:
        return away_score, home_score
    raise ValueError(
        f"ticker's strike team {yes_team!r} matches neither "
        f"home_team_code={home_team_code!r} nor away_team_code={away_team_code!r}"
    )


def derive_actual_stat(
    market_type: MarketType,
    ticker: str,
    home_team_code: str,
    away_team_code: str,
    home_score: float,
    away_score: float,
) -> tuple[float, str]:
    """Pure function: given a completed game's final scores and a cell's
    (MarketType, ticker), return the (actual_stat, stat_label) pair that
    `paper_trader.py::settle_position()` needs. No I/O, no threshold input
    -- see module docstring.

    Raises ValueError for an unsupported market_type, a ticker whose strike
    suffix doesn't parse, or a strike team that matches neither supplied
    team code. Never guesses -- refuses instead.
    """
    if market_type not in _SUPPORTED_MARKET_TYPES:
        raise ValueError(
            f"derive_actual_stat: unsupported market_type {market_type!r} "
            f"(supported: {sorted(t.value for t in _SUPPORTED_MARKET_TYPES)})"
        )

    home_team_code = home_team_code.upper()
    away_team_code = away_team_code.upper()
    home_score = float(home_score)
    away_score = float(away_score)

    if market_type in (MarketType.NFL_MONEYLINE, MarketType.NFL_SPREAD):
        yes_team, _digits = _parse_strike_suffix(ticker)
        yes_score, other_score = _team_score(
            yes_team, home_team_code, away_team_code, home_score, away_score
        )
        actual_stat = yes_score - other_score
        stat_label = f"point_margin_for_{yes_team}"
        return actual_stat, stat_label

    if market_type is MarketType.NFL_GAME_TOTAL:
        return home_score + away_score, "combined_final_score"

    # NFL_TEAM_TOTAL
    yes_team, _digits = _parse_strike_suffix(ticker)
    yes_score, _other_score = _team_score(
        yes_team, home_team_code, away_team_code, home_score, away_score
    )
    return yes_score, f"team_final_score_{yes_team}"


def check_settlement_ambiguity(
    market_type: MarketType,
    actual_stat: float,
    threshold: float,
) -> None:
    """Raise SettlementAmbiguityError if (actual_stat, threshold) would
    settle ambiguously under settle_position()'s boolean `actual_stat >=
    threshold` model for this market_type. No-op (returns None) otherwise.

    Takes threshold explicitly, unlike derive_actual_stat() -- only the
    resolver script has both actual_stat and threshold together at
    settlement time. See module docstring for the tie/push rules this
    enforces and where they were sourced.
    """
    if market_type not in _SUPPORTED_MARKET_TYPES:
        raise ValueError(
            f"check_settlement_ambiguity: unsupported market_type {market_type!r}"
        )

    if market_type is MarketType.NFL_MONEYLINE:
        if actual_stat == 0:
            raise SettlementAmbiguityError(
                "NFL moneyline exact tie (point margin == 0): Kalshi's "
                "KXNFLGAME rules (NFLGAME.pdf, Tie provision) settle a tied "
                "game as a $0.50/$0.50 split payout, which "
                "settle_position()'s boolean win/loss model cannot "
                "represent. Do not settle this position via settle_position()."
            )
        return

    # NFL_SPREAD / NFL_GAME_TOTAL / NFL_TEAM_TOTAL: an exact push.
    if actual_stat == threshold:
        raise SettlementAmbiguityError(
            f"push: actual_stat ({actual_stat}) equals threshold "
            f"({threshold}) exactly for {market_type.value}. Kalshi's "
            f"contract terms (NFLSPREAD.pdf / FOOTBALLTOTALS) define only "
            f"over/under (or cover/no-cover), not an equal-to outcome -- "
            f"refusing rather than guessing >= vs >. (Note: real currently-"
            f"listed Kalshi strikes are always half-point lines, so this "
            f"should not occur against live data; it is reachable only if "
            f"a future strike lands on an integer.)"
        )
