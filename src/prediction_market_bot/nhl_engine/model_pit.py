"""NHL engine, W100.1 Part A: the matchup cross divided by a SAME-VINTAGE point-in-time league rate.

Why this exists (measured, 12_EXPLORATORY/nhl_engine/results_W100_1.md): in ``inputs.expected_xg`` the cross is
``sec5/3600 * f5_own * a5_opp / lg_f5``. The two team rates are decayed/shrunk from the CURRENT xG vintage (the xG model is
refit every season), but ``lg_f5`` is the league rate over EARLIER seasons only, i.e. an OLDER vintage. When the xG scale
drifts between seasons the denominator is stale and every cross is scaled by (current scale / old scale). On the frame
the mean ``lg_f5`` ran above the mean team rate in 2023-2025 (2.757 vs 2.676, 2.661 vs 2.555, 2.621 vs 2.605), so the
cross under-counts. Here the denominator is the mean of the sides' own rates over the previous ``window`` games with a
STRICTLY EARLIER puck drop, so numerator and denominator share a scale and nothing from the game's own start or later enters.

Applies to a ``game_features`` frame (regular season, with ``start``). Does not apply to the first rows of a frame (no earlier
game): there the original ``lg_*`` column is used, by design. It does not touch the merged ``model.py`` / ``inputs.py``; the
fit and the pricing reuse them unchanged. Size of the effect: small (about 0.03-0.05 goals per game on held-out seasons);
it is a correctness fix, not the whole of the held-out bias (see the results file).
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd

from . import model as _m

WINDOW = 1000


def pit_league_rate(start, own: np.ndarray, opp: np.ndarray, fallback: np.ndarray, window: int = WINDOW) -> np.ndarray:
    """For each row, the mean of ``(own+opp)/2`` over the ``window`` rows immediately before the first row sharing its
    ``start`` (strictly earlier puck drop, in time order). ``fallback`` fills rows with no earlier game."""
    st = pd.to_datetime(pd.Series(np.asarray(start))).to_numpy()
    order = np.argsort(st, kind="stable")
    s_sorted = st[order]
    v = ((np.asarray(own, float) + np.asarray(opp, float)) / 2.0)[order]
    cs = np.concatenate([[0.0], np.cumsum(v)])
    first = np.searchsorted(s_sorted, s_sorted, side="left")      # first row of each start-time group
    lo = np.maximum(first - window, 0)
    n = first - lo
    with np.errstate(invalid="ignore", divide="ignore"):
        r_sorted = np.where(n > 0, (cs[first] - cs[lo]) / np.maximum(n, 1), np.nan)
    out = np.empty(len(st)); out[order] = r_sorted
    return np.where(np.isnan(out), np.asarray(fallback, float), out)


def with_pit_denominators(fr: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    """Copy of ``fr`` with ``pit_f5`` / ``pit_pp`` columns (same-vintage league rates, per 60)."""
    out = fr.copy()
    out["pit_f5"] = pit_league_rate(fr["start"], fr["f5_h"], fr["f5_a"], fr["lg_f5_h"], window)
    out["pit_pp"] = pit_league_rate(fr["start"], fr["pp_h"], fr["pp_a"], fr["lg_pp_h"], window)
    return out


def expected_xg_pit(row, side: str) -> float:
    """``inputs.expected_xg`` with the league denominators swapped for the same-vintage ones in ``row``."""
    o = "a" if side == "h" else "h"
    e5 = row["sec5_h"] / 3600.0 * row[f"f5_{side}"] * row[f"a5_{o}"] / max(row["pit_f5"], 1e-9)
    ppt = 0.5 * (row[f"ppt_{side}"] + row[f"sht_{o}"])
    epp = ppt / 3600.0 * row[f"pp_{side}"] * row[f"pk_{o}"] / max(row["pit_pp"], 1e-9)
    return float(e5 + epp)


def side_rows_pit(fr: pd.DataFrame) -> pd.DataFrame:
    """``model.side_rows`` with the same-vintage cross. ``fr`` must carry ``pit_f5`` / ``pit_pp`` (``with_pit_denominators``)."""
    out = []
    recs = fr.to_dict("records")
    for side in ("h", "a"):
        o = "a" if side == "h" else "h"
        out.append(pd.DataFrame({
            "game_id": [r["game_id"] for r in recs],
            "lx": [np.log(max(expected_xg_pit(r, side), 1e-3)) for r in recs],
            "home": 1.0 if side == "h" else 0.0,
            "b2b_own": [float(r[f"rest_{side}"] < 1.5) for r in recs],
            "b2b_opp": [float(r[f"rest_{o}"] < 1.5) for r in recs],
            "gs_own": [r[f"gs_{side}"] for r in recs],
            "gs_opp": [r[f"gs_{o}"] for r in recs],
        }))
    return pd.concat(out, ignore_index=True)


class PitFitted(_m.Fitted):
    """A ``Fitted`` whose rates use the same-vintage cross. Pricing (``model.price_games``) works on it unchanged."""

    def rates(self, fr: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        x = side_rows_pit(fr)
        lam = np.exp(np.column_stack([np.ones(len(x)), x[_m.FEATS].to_numpy()]) @ self.coef)
        n = len(fr)
        return lam[:n], lam[n:]


def fit_pit(fr: pd.DataFrame, reg_h: np.ndarray, reg_a: np.ndarray, home_won: np.ndarray, force_poisson: bool = False,
            alpha: float = 1e-3) -> PitFitted:
    """``model.fit`` on the same-vintage cross. ``fr`` must carry the ``pit_*`` columns, computed on the frame passed in
    (training rows see only earlier training rows; apply ``with_pit_denominators`` to train+test together, or to each
    side with the test frame's window anchored in the train tail, see the results script)."""
    base = _m.side_rows
    _m.side_rows = side_rows_pit
    try:
        f = _m.fit(fr, reg_h, reg_a, home_won, force_poisson=force_poisson, alpha=alpha)
    finally:
        _m.side_rows = base
    return PitFitted(coef=f.coef, k=f.k, p_home_ot=f.p_home_ot, tie_odds=f.tie_odds)
