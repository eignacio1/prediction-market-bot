"""W91.2 leave-one-out ladder price: what the REST of a strike ladder says one strike should cost.

Pure, no I/O, measure-only. Applies when a ladder has >= 4 strikes (3 left after dropping one) with mids in the
fit window and a roughly bell-shaped implied distribution (fit_normal returns None otherwise -> None here).
Does not apply to 1-3 strike ladders, or to a strike whose own price drove the fit (hence leave-one-out).
"""
from __future__ import annotations

from prediction_market_bot.quant.ladder import fit_normal, parse_ticker, surv_normal, survival_points


def loo_ladder_prices(rows, kind: str):
    """rows: dicts ticker/bid/ask (floats), ONE ladder at ONE snapshot. kind 'total' | 'margin'.
    Returns {ticker: ladder_yes_price} for every strike whose leave-one-out fit succeeds.
    For kind 'margin' the reference team is the alphabetically first code present (as in survival_points); a
    non-reference team's contract is priced 1 - S(-k)."""
    out = {}
    if len(rows) < 4:
        return out
    teams = sorted({parse_ticker(r["ticker"])[1] for r in rows})
    ref = teams[0] if kind == "margin" else ""
    for i, r in enumerate(rows):
        rest = rows[:i] + rows[i + 1:]
        pts = survival_points(rest, kind)
        fit = fit_normal(pts)
        if fit is None:
            continue
        _, team, k = parse_ticker(r["ticker"])
        if kind == "margin" and team != ref:
            p = 1.0 - float(surv_normal(-k, fit["mu"], fit["sigma"]))
        else:
            p = float(surv_normal(k, fit["mu"], fit["sigma"]))
        out[r["ticker"]] = p
    return out
