"""D6 layer 6: a sizing rule per arm (W112.2, B-082; DOCTRINE section 1 layers 6-7; OPERATOR_DIRECTIVES D-03).

``size_for(arm, cell, context)`` answers "how much, and why" for one routed bet. It is PURE: no I/O, no order path, no
registry write. The live rule today is deliberately small:

  * Kelly is 0 on every band (ADR-0048; no real capital until G6, ADR-0076), so the PLACED stake is the flat demo
    stake (ADR-0050 / ADR-0059 measurement stake, ``context.flat_stake_usd``), never a Kelly size;
  * that stake is cut by the caps that exist per arm: per event, per day, per arm budget, and a SAME-GAME cluster cap;
  * the SAME-GAME cap uses the 110.4 joint (``quant/sgp.py``): open legs whose draws move together with the new leg
    (phi >= ``merge_phi``) are ONE exposure - together they may not exceed one leg's cluster cap, so two perfectly
    correlated legs are sized as one;
  * a Kelly-SHAPED stake is computed and LOGGED beside the flat one (``kelly_shaped_usd``: what it would be at the
    hypothetical fraction on the hypothetical bankroll, never placed). It changes nothing.

NO_BET sizes to zero. A cell whose hypothesis is closed (``cell.closed_hypotheses``) is sized exactly like any other:
a losing look closes a test, never an arm (operator 2026-11-11 16:51 PT). Wiring into 112.3's order hook is the
window's next-wave step; this module does not import the order path and the order path does not import it yet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

import numpy as np

from prediction_market_bot.quant import sgp

ARMS = ("RIDE", "FADE", "MOMENTUM_FOLLOW", "MOMENTUM_FADE", "POT_OF_GOLD", "NO_BET")

FLAT_DEMO_STAKE_USD = 1.00             # ADR-0059 T1_MEASUREMENT_STAKE_USD; the context may override it
DEFAULT_EVENT_CAP_USD = 5.00           # per event (demo scale; real hard limit in risk._HARD_LIMITS is a different, larger fence)
DEFAULT_DAY_CAP_USD = 50.00            # per UTC day across all arms
DEFAULT_ARM_BUDGET_USD = 25.00         # per arm per day
DEFAULT_CLUSTER_CAP_USD = None         # None -> one leg's flat stake: correlated legs are sized as one
MERGE_PHI = 0.90                       # legs with phi >= this move together and merge into one exposure
HYPOTHETICAL_KELLY_FRACTION = 0.25     # logged only; the live fraction is 0.0 (execution_bands.py)
HYPOTHETICAL_BANKROLL_USD = 1000.0     # same denominator exposure_gate uses for the ledger-less shadow book


@dataclass(frozen=True)
class OpenLeg:
    """An already-sized leg of the same game. ``draws`` is its boolean 'this leg wins' array over the shared draws."""
    stake_usd: float
    draws: Any = None                  # numpy bool array over the game's shared simulation draws; None -> treated as independent
    leg_id: str = ""


@dataclass(frozen=True)
class SizingContext:
    price: Optional[float] = None              # cost per contract of the side being bought, in (0, 1)
    p_win: Optional[float] = None              # the engine's probability that THIS side wins (one input; never the bet)
    flat_stake_usd: float = FLAT_DEMO_STAKE_USD
    event_cap_usd: float = DEFAULT_EVENT_CAP_USD
    day_cap_usd: float = DEFAULT_DAY_CAP_USD
    arm_budget_usd: Mapping[str, float] = field(default_factory=dict)   # arm -> budget; missing -> DEFAULT_ARM_BUDGET_USD
    open_event_usd: float = 0.0                # already staked on this event (all arms)
    open_day_usd: float = 0.0                  # already staked today (all arms)
    open_arm_usd: float = 0.0                  # already staked today on THIS arm
    new_leg_draws: Any = None                  # this leg's boolean draws (same game); None -> no same-game merge
    same_game_open: Sequence[OpenLeg] = ()
    cluster_cap_usd: Optional[float] = DEFAULT_CLUSTER_CAP_USD
    merge_phi: float = MERGE_PHI


@dataclass(frozen=True)
class SizeDecision:
    arm: str
    cell: str
    stake_usd: float                           # the PLACED stake basis: flat demo, cut by caps
    reason: str
    basis: str = "flat_demo"
    binding_caps: tuple[str, ...] = ()         # every cap that cut the stake (the tightest is the last applied minimum)
    kelly_fraction_live: float = 0.0
    kelly_shaped_usd: Optional[float] = None   # LOGGED, never placed
    kelly_placed: bool = False                 # always False in this module
    correlated_exposure_usd: float = 0.0       # stake already open that merged into this leg's cluster
    merged_legs: int = 0                       # open same-game legs merged into this leg's exposure

    def as_row_fields(self) -> dict:
        """Fields a shadow / order row carries to count as 'has a size_for decision' (layer-6 evidence rule)."""
        return {"size_for": {
            "arm": self.arm, "stake_usd": round(self.stake_usd, 4), "reason": self.reason, "basis": self.basis,
            "binding_caps": list(self.binding_caps), "kelly_fraction_live": self.kelly_fraction_live,
            "kelly_shaped_usd": None if self.kelly_shaped_usd is None else round(self.kelly_shaped_usd, 4),
            "kelly_placed": False, "correlated_exposure_usd": round(self.correlated_exposure_usd, 4),
            "merged_legs": self.merged_legs}}


def kelly_shaped_stake(p_win: Optional[float], price: Optional[float], *, fraction: float = HYPOTHETICAL_KELLY_FRACTION,
                       bankroll_usd: float = HYPOTHETICAL_BANKROLL_USD) -> Optional[float]:
    """What a fractional-Kelly stake WOULD be for a binary contract bought at ``price`` with win probability ``p_win``:
    f* = (p - c) / (1 - c), stake = fraction * f* * bankroll, floored at 0. Logged next to the flat stake; never placed."""
    if p_win is None or price is None or not (0.0 < price < 1.0) or not (0.0 <= p_win <= 1.0):
        return None
    return max(0.0, (p_win - price) / (1.0 - price)) * fraction * bankroll_usd


def _live_kelly(cell: Any) -> float:
    try:
        from prediction_market_bot.execution_bands import get_band_config
        return float(get_band_config(cell.band).kelly_fraction)
    except Exception:  # noqa: BLE001 - a lookup failure must not size anything up; 0.0 is the safe report
        return 0.0


def _cell_name(cell: Any) -> str:
    mt = getattr(getattr(cell, "market_type", None), "value", getattr(cell, "market_type", None))
    bd = getattr(getattr(cell, "band", None), "value", getattr(cell, "band", None))
    return f"{mt}/{bd}" if mt is not None or bd is not None else str(cell)


def _cluster(ctx: SizingContext) -> tuple[float, int]:
    """(stake already open in this leg's cluster, legs merged). A cluster is the open same-game legs with
    phi(new, open) >= merge_phi over the shared draws; a leg with no draws is independent, a constant leg merges only
    with an identical constant leg."""
    if ctx.new_leg_draws is None:
        return 0.0, 0
    stake, n = 0.0, 0
    for o in ctx.same_game_open:
        if o.draws is None:
            continue
        ph = sgp.phi(ctx.new_leg_draws, o.draws)
        same = ph != ph and bool((np.asarray(ctx.new_leg_draws, bool) == np.asarray(o.draws, bool)).all())
        if same or (ph == ph and ph >= ctx.merge_phi):      # a constant leg merges only with an identical one
            stake += max(0.0, float(o.stake_usd))
            n += 1
    return stake, n


def size_for(arm: str, cell: Any, context: Optional[SizingContext] = None) -> SizeDecision:
    """The stake and the reason for one routed bet. Never raises on a cap; an unknown arm sizes to 0 with that reason."""
    ctx = context or SizingContext()
    name = _cell_name(cell)
    kelly_live = _live_kelly(cell)
    shaped = kelly_shaped_stake(ctx.p_win, ctx.price)
    if arm not in ARMS:
        return SizeDecision(arm, name, 0.0, f"unknown arm {arm!r}: sized 0", "none", (), kelly_live, shaped)
    if arm == "NO_BET":
        return SizeDecision(arm, name, 0.0, "NO_BET arm: no stake", "none", (), kelly_live, 0.0 if shaped is not None else None)
    stake = max(0.0, float(ctx.flat_stake_usd))
    binding: list[str] = []

    def cut(label: str, headroom: float) -> None:
        nonlocal stake
        h = max(0.0, headroom)
        if h < stake - 1e-12:
            stake = h
            binding.append(label)

    cut("event", ctx.event_cap_usd - ctx.open_event_usd)
    cut("day", ctx.day_cap_usd - ctx.open_day_usd)
    cut("arm_budget", float(ctx.arm_budget_usd.get(arm, DEFAULT_ARM_BUDGET_USD)) - ctx.open_arm_usd)
    merged_usd, merged_n = _cluster(ctx)
    ccap = ctx.cluster_cap_usd if ctx.cluster_cap_usd is not None else float(ctx.flat_stake_usd)
    if merged_n:
        cut("same_game_cluster", ccap - merged_usd)
    if stake <= 0.0:
        reason = "cap binds, stake 0: " + ",".join(binding)
    elif binding:
        reason = f"flat demo stake cut to {stake:.2f} by cap: " + ",".join(binding)
    else:
        reason = "flat demo stake (Kelly 0, no real capital); no cap binds"
    return SizeDecision(arm, name, stake, reason, "flat_demo", tuple(binding), kelly_live, shaped, False, merged_usd, merged_n)
