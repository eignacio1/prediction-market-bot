"""Kalshi NBA same-game combo (MVE) pricing from the engine's joint draws (W126.4 Part B, B-024).

A Kalshi combo market carries ``mve_selected_legs = [{market_ticker, side}]``; YES pays only if every leg resolves as selected.
Each leg ticker is mapped to a boolean array over the SAME simulation draws (``sgp_price.GameDraws``: engine_v2 team scores +
``joint.py`` player stats, one draw index), a NO-side leg is the negation, and P(all legs) is the share of draws where every leg
holds. The engine therefore carries whatever dependence its draws carry; independence is the product (known-answer tests).

Legs the engine cannot price are listed with a reason and make ``p_all`` None; ``p_priced_subset`` (the joint of the legs it can
price) is an upper bound on the full combo (dropping a leg can only raise the probability). Legs it cannot price today: steals,
blocks, stocks, PRA, double / triple double, first-half / first-quarter markets, precise total, the ``...PROT`` variants (series
semantics not yet identified), and any leg whose player is not in the draws. Two legs on the same player with different stats
are priced from the joint's shared latent but flagged ``same_player_cross_stat`` (W110.4 measured the older props layer wrong
there; the flag keeps those rows out of scoring until the dependence is re-measured).

Strike convention (spread checked against the live market 2026-11-25: KXNBASPREAD-26NOV24BOSWAS-BOS19 = "Boston wins by over 18.5"): a ticker number N means "N or more" for player stats and totals
(``KXNBATOTAL-...-219`` = total >= 219, i.e. "Over 218.5"); a spread ticker ``TEAM N`` means that team wins by >= N.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from prediction_market_bot.nba_engine.sgp_price import GameDraws
from prediction_market_bot.quant import sgp as S

_EVENT = re.compile(r"^(?P<series>KXNBA[A-Z0-9]*)-(?P<date>\d{2}[A-Z]{3}\d{2})(?P<away>[A-Z]{3})(?P<home>[A-Z]{3})$")
_PLAYER = re.compile(r"^([A-Z]{2,3})([A-Z])([A-Z]+?)(\d{0,2})$")
_TEAM_N = re.compile(r"^([A-Z]{3})(\d+)$")

PLAYER_STATS = {"KXNBAPTS": "points", "KXNBAREB": "rebounds", "KXNBAAST": "assists", "KXNBA3PT": "threes"}
UNPRICED_REASONS = {
    "KXNBASTL": "steals_not_modelled", "KXNBABLK": "blocks_not_modelled", "KXNBASTOCK": "stocks_not_modelled",
    "KXNBAPRA": "pra_not_modelled", "KXNBA2D": "double_double_not_modelled", "KXNBA3D": "triple_double_not_modelled",
    "KXNBA1H": "half_market_not_modelled", "KXNBA1HSPREAD": "half_market_not_modelled", "KXNBA1HTOTAL": "half_market_not_modelled",
    "KXNBA1Q": "quarter_market_not_modelled", "KXNBA1QSPREAD": "quarter_market_not_modelled", "KXNBA1QTOTAL": "quarter_market_not_modelled",
    "KXNBATOTALPRECISE": "precise_total_not_modelled",
}


@dataclass(frozen=True)
class ComboLeg:
    """A parsed Kalshi leg. ``kind`` is None when unpriceable (``reason`` says why)."""
    ticker: str
    yes: bool                      # False = NO side selected (the leg is negated)
    kind: str | None = None        # ml | spread | total | team_total | player
    side: str = "home"             # home | away
    line: float = 0.0
    stat: str | None = None
    player: str | None = None      # "<INITIAL><SURNAME>" as Kalshi writes it, e.g. "JTATUM"
    reason: str | None = None


def parse_leg(ticker: str, side: str) -> ComboLeg:
    yes = side.lower() != "no"
    parts = ticker.split("-")
    if len(parts) < 3:
        return ComboLeg(ticker, yes, reason="unparseable_ticker")
    ev = _EVENT.match("-".join(parts[:2]))
    if not ev:
        return ComboLeg(ticker, yes, reason="unparseable_event")
    series, away, home, tail = ev["series"], ev["away"], ev["home"], parts[2:]

    def which(team: str) -> str | None:
        return "home" if team == home else "away" if team == away else None

    if series in UNPRICED_REASONS:
        return ComboLeg(ticker, yes, reason=UNPRICED_REASONS[series])
    if series.endswith("PROT"):
        return ComboLeg(ticker, yes, reason="prot_variant_undefined")
    if series == "KXNBAGAME" and len(tail) == 1:
        w = which(tail[0])
        return ComboLeg(ticker, yes, "ml", w) if w else ComboLeg(ticker, yes, reason="unknown_team")
    if series == "KXNBATOTAL" and len(tail) == 1 and tail[0].isdigit():
        return ComboLeg(ticker, yes, "total", line=float(tail[0]))
    if series in ("KXNBASPREAD", "KXNBATEAMTOTAL") and len(tail) == 1:
        m = _TEAM_N.match(tail[0])
        w = which(m.group(1)) if m else None
        if not w:
            return ComboLeg(ticker, yes, reason="unknown_team")
        return ComboLeg(ticker, yes, "spread" if series == "KXNBASPREAD" else "team_total", w, float(m.group(2)))
    if series in PLAYER_STATS and len(tail) == 2 and tail[1].isdigit():
        m = _PLAYER.match(tail[0])
        w = which(m.group(1)) if m else None
        if not w:
            return ComboLeg(ticker, yes, reason="unparseable_player")
        return ComboLeg(ticker, yes, "player", w, float(tail[1]), PLAYER_STATS[series], m.group(2) + m.group(3))
    return ComboLeg(ticker, yes, reason="unknown_series")


def _array(g: GameDraws, leg: ComboLeg) -> np.ndarray | None:
    """Boolean draws for one parsed leg, NO side negated; None when the draws do not carry it."""
    if leg.kind is None:
        return None
    if leg.kind == "ml":
        m = (g.home - g.away) if leg.side == "home" else (g.away - g.home)
        a = m >= 1
    elif leg.kind == "spread":
        m = (g.home - g.away) if leg.side == "home" else (g.away - g.home)
        a = m >= leg.line
    elif leg.kind == "total":
        a = (g.home + g.away) >= leg.line
    elif leg.kind == "team_total":
        a = (g.home if leg.side == "home" else g.away) >= leg.line
    else:
        d = g.players.get((leg.side, leg.player, leg.stat))
        if d is None:
            return None
        a = np.asarray(d) >= leg.line
    return a if leg.yes else ~a


def price_kalshi_combo(g: GameDraws, legs: Sequence[tuple[str, str]]) -> dict:
    """legs = [(market_ticker, 'yes'|'no'), ...] of one combo. Returns the joint and bookkeeping (see module docstring)."""
    parsed = [parse_leg(t, s) for t, s in legs]
    arrays, priced, unpriced = [], [], []
    for p in parsed:
        a = _array(g, p)
        if a is None:
            unpriced.append({"ticker": p.ticker, "side": "yes" if p.yes else "no", "reason": p.reason or "player_not_in_draws"})
        else:
            arrays.append(a)
            priced.append(p.ticker)
    flags = []
    seen: dict = {}
    for p in parsed:
        if p.kind == "player" and p.ticker in priced:
            seen.setdefault((p.side, p.player), set()).add(p.stat)
    if any(len(v) > 1 for v in seen.values()):
        flags.append("same_player_cross_stat")
    out = dict(n_legs=len(parsed), legs_priced=priced, legs_unpriced=unpriced, flags=flags, n_draws=g.n,
               p_all=None, p_priced_subset=None, p_naive=None, lift=None, mc_se=None, resolved=False)
    if not arrays:
        return out
    pj, pn = S.joint(*arrays), S.independent(*arrays)
    out.update(p_priced_subset=pj, p_naive=pn, lift=(pj / pn if pn > 0 else None), mc_se=S.mc_se(pj, g.n),
               resolved=bool(S.resolved(pj, g.n)), p_marginals=[S.marginal(a) for a in arrays])
    if not unpriced:
        out["p_all"] = pj
    return out
