"""T1 game-market flat measurement-stake wrapper (ADR-0059, T-497/GG-218).

Extends ADR-0050's flat-measurement-stake pattern (built for T4M-PROJ in
`run_t4_mlb_live.py::measurement_stake_and_stratum`) to T1's nine
`(MarketType, T1_MULTI_DAY)` game-market cells (ADR-0058), all of which remain
`NOT_IMPLEMENTED` and are not promoted by this module. This module is not
imported by any live pipeline (`run_mlb_paper_trade.py` is outside this
session's scope fence) — it exists as the wrapper design + implementation
this session was scoped to produce, ready to be wired in by a future,
cell-promotion session.

What generalizes from ADR-0050 unchanged (per ADR-0058 §3 and this session's
verification of `risk.py::evaluate_forecast` and `paper_trader.py::open_position`):
the `fixed_stake_usd` bypass at the risk-engine layer, and the opt-in
`entry_price_paid`/`price_stratum`/`contracts` stamping at the paper-trader
layer. Neither requires any change for T1 to use them — this module only
supplies the T1-shaped decision logic that used to live solely in T4's
live-loop script.

What does NOT generalize, and is added here specifically because T4's wrapper
never needed it: a fill-cost (haircut) bound. T-488/GG-157 (2026-08-26,
synthetic/uncorrected-ledger measurement, family-level nearest-in-time join —
see that task's SUMMARY.md for the join-method caveat) found game-market
haircuts running 3-5x props' measured median haircut ($0.0100/contract),
concentrated in a few families:

    GAME_WINNER (moneyline):  mean $0.0340  median $0.0350
    GAME_TOTAL:               mean $0.0307  p90 $0.0800   max $0.4200
    RUN_LINE (spread):        mean $0.0515  p90 $0.1500   max $0.4050

T4's wrapper had no such bound because T4 trades one deep, well-attended
family (KXMLBHIT props); a $1.00 flat stake against a thin game-market book
can fill at a materially worse effective price than the quoted mid without
the sizing formula itself ever seeing it. Per CLAUDE.md's standing rule that
depth/spread figures must be measured live at decision time and never taken
from a remembered constant, this module does not hardcode an assumed
haircut — it requires the caller to supply one, freshly measured, and
refuses the trade (returns None) if none is supplied or if it exceeds the
bound below. The bound itself (not the live measurement) is the one
citable constant this module owns, set conservatively near GAME_TOTAL's p90
and comfortably under RUN_LINE's p90/either family's tail max, so that a
RUN_LINE fill deep in its own tail is exactly the case this gate is meant to
catch, not wave through.
"""

from __future__ import annotations

# ADR-0050 §8(B)'s formula, unchanged: stake = min(flat_stake, max_contracts *
# entry_price), never a floor()-based integer-contract formula (rejected
# there for under-staking non-round prices). Same $1.00 / 10-contract values
# as T4M-PROJ — T-497 found no game-market-specific reason to diverge from
# them, and ADR-0058 §3 asks that T1's wrapper follow ADR-0050's invariant,
# not invent a new one.
T1_MEASUREMENT_STAKE_USD = 1.00
T1_MEASUREMENT_MAX_CONTRACTS = 10

# Same LOW/MID/HIGH price-stratum boundaries as T4M-PROJ (ADR-0050 addendum
# §C) — these are generic price buckets, not a T4-specific concept.
T1_PRICE_STRATUM_LOW_MAX = 0.10
T1_PRICE_STRATUM_MID_MAX = 0.70

# New in this module (T-497/ADR-0059) — grounded in T-488/GG-157's synthetic
# per-family haircut figures above. Set at GAME_TOTAL's p90 ($0.0800),
# rounded up: covers GAME_WINNER's median ($0.0350) and most of GAME_TOTAL's
# distribution, while gating out RUN_LINE's p90 ($0.1500) and both families'
# tails ($0.42/$0.4050) — i.e. it is a real, binding gate for the family
# T-488 found worst, not a rubber stamp. Re-derive if T-488's synthetic
# measurement is superseded by the ticker-targeted decision-time capture
# GG-157 Phase 3/4 already calls for.
T1_MAX_HAIRCUT_PER_CONTRACT_USD = 0.10

# The nine ADR-0058 game-market cells this wrapper is scoped to. Any other
# market_type (i.e. KXMLBHIT props) is out of scope for this module — T1
# props already trade Kelly-sized (kelly_fraction is band-level, unaffected
# by this module) and have no measured haircut problem per T-488's own
# baseline. Values are MarketType.value strings (market_type_registry.py) —
# lowercase, e.g. "mlb_moneyline" — matching what paper_trader.py::open_position
# actually stamps onto a ledger record's "market_type" field
# (`_resolved_market_type.value`), not the enum member names.
T1_GAME_MARKET_TYPES = frozenset({
    "mlb_moneyline", "mlb_run_line", "mlb_game_total",
    "mlb_team_total", "mlb_partial_game",
    "nfl_moneyline", "nfl_spread", "nfl_game_total", "nfl_team_total",
})


class MeasurementStakeRefused(Exception):
    """Raised (not silently swallowed) when the fill-cost bound can't be cleared.

    A caller that wants a soft refusal should catch this rather than the
    module returning None — a raised, named exception makes "refused, and
    why" impossible to lose in a truthiness check on a tuple/None return,
    which is exactly the failure mode a safety wrapper must not have.
    """


def t1_measurement_stake_and_stratum(
    entry_price: float,
    measured_haircut_usd_per_contract: float | None,
) -> tuple[float, float, str]:
    """T1 game-market equivalent of run_t4_mlb_live.py::measurement_stake_and_stratum.

    Args:
        entry_price: YES-frame entry price in [0, 1] (mid if direction=="YES",
            1-mid if direction=="NO" — same convention as T4's call site).
        measured_haircut_usd_per_contract: a freshly measured (this decision,
            this ticker) estimate of the per-contract fill-cost haircut —
            e.g. quoted-mid minus expected fill price, or half the current
            live-measured bid-ask spread from a depth read
            (`scripts/phase0_market_survey.py depth` / the archiver's
            `--depth-sample-per-family` output — see CLAUDE.md's market-depth
            section). Must not be a remembered/hardcoded constant. None means
            "no live measurement available," which this function treats as
            worst-case, not best-case: it refuses rather than assumes zero
            haircut.

    Returns:
        (stake_usd, contracts, price_stratum) — the same three-field shape
        T4's function returns and paper_trader.py::open_position already
        knows how to stamp verbatim onto the approval dict.

    Raises:
        MeasurementStakeRefused: entry_price is out of (0, 1], no haircut
            measurement was supplied, or the supplied measurement exceeds
            T1_MAX_HAIRCUT_PER_CONTRACT_USD.
    """
    if not (0.0 < entry_price <= 1.0):
        raise MeasurementStakeRefused(f"entry_price={entry_price} out of (0, 1]")

    if measured_haircut_usd_per_contract is None:
        raise MeasurementStakeRefused(
            "no live haircut measurement supplied — refusing rather than "
            "assuming zero haircut (CLAUDE.md market-depth rule: never size "
            "against a remembered/assumed figure)"
        )
    if measured_haircut_usd_per_contract > T1_MAX_HAIRCUT_PER_CONTRACT_USD:
        raise MeasurementStakeRefused(
            f"measured_haircut_usd_per_contract={measured_haircut_usd_per_contract} "
            f"exceeds bound={T1_MAX_HAIRCUT_PER_CONTRACT_USD} "
            "(T-488/GG-157-informed gate — see module docstring)"
        )

    stake = round(
        min(T1_MEASUREMENT_STAKE_USD, T1_MEASUREMENT_MAX_CONTRACTS * entry_price), 4
    )
    contracts = round(stake / entry_price, 4)

    if entry_price < T1_PRICE_STRATUM_LOW_MAX:
        stratum = "LOW"
    elif entry_price <= T1_PRICE_STRATUM_MID_MAX:
        stratum = "MID"
    else:
        stratum = "HIGH"

    return stake, contracts, stratum


def is_t1_game_market(market_type: str) -> bool:
    """True for the nine ADR-0058 cells this module governs; False for props."""
    return market_type in T1_GAME_MARKET_TYPES
