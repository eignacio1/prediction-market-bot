"""The granularity-index machine (W80.3; GRANULARITY_INDEX.md, ADR-0075 components 2 and 4).

Generic over metric, bucket column and unit. An index *entry* is one (metric, split) pair; this module supplies the four
operations every entry needs and nothing sport- or metric-specific:

* ``split``       metric cut by a situation, per unit, season-to-date, point in time.
* ``rank``        where an entry sits league-wide and against every comparable unit-season at the same games-played
                  point, plus ``stability`` (split-half reliability with a CI: trait or noise at this sample).
* ``cross``       offense split x defense split x how often the defense shows each bucket vs this offense.
* ``market_map``  the Kalshi families the entry should move, joined to the thin-market inventory.
* ``filter_entries``  the filtering mechanism: extremes and mismatches pass, the median does not.

Input frame (one row per play, already restricted to the plays the metric is defined on) needs: ``season``, ``week``,
``game_id``, the unit column, the bucket column and the metric column. Point in time: ``before_week=N`` reads weeks < N
of that season only; ``games=g`` reads each unit's first g games (the "same games-played point" for history ranks).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SplitSpec:
    unit: str                      # unit column, e.g. "posteam" or "defteam"
    by: str                        # bucket column (NaN = play not classifiable, dropped)
    metric: str                    # numeric metric column (0/1 for rates)
    higher_is_better: bool = True  # for ranks: is a higher value "better" for this unit?
    min_n: int = 30                # plays below which an entry is not ranked


def game_table(plays: pd.DataFrame, spec: SplitSpec) -> pd.DataFrame:
    """Per (season, unit, game, bucket): n, s (sum), ss (sum of squares), plus game_no = the unit's k-th game in season."""
    d = plays.dropna(subset=[spec.unit, spec.by, spec.metric])
    x = d[spec.metric].astype(float)
    g = (d.assign(_x=x, _x2=x * x)
           .groupby(["season", spec.unit, "week", "game_id", spec.by], observed=True)
           .agg(n=("_x", "size"), s=("_x", "sum"), ss=("_x2", "sum")).reset_index())
    order = g.drop_duplicates(["season", spec.unit, "week", "game_id"])[["season", spec.unit, "week", "game_id"]]
    order = order.sort_values(["season", spec.unit, "week", "game_id"])
    order["game_no"] = order.groupby(["season", spec.unit]).cumcount() + 1
    return g.merge(order, on=["season", spec.unit, "week", "game_id"])


def split(plays: pd.DataFrame, spec: SplitSpec, season: Optional[int] = None, before_week: Optional[int] = None,
          games: Optional[int] = None, table: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Season-to-date metric per (season, unit, bucket): columns n, s, ss, value, games. Point in time via
    ``before_week`` (week N reads weeks < N) and/or ``games`` (each unit's first g games)."""
    t = game_table(plays, spec) if table is None else table
    if season is not None:
        t = t[t.season == season]
    if before_week is not None:
        t = t[t.week < before_week]
    if games is not None:
        t = t[t.game_no <= games]
    out = (t.groupby(["season", spec.unit, spec.by], observed=True)
             .agg(n=("n", "sum"), s=("s", "sum"), ss=("ss", "sum"), games=("game_no", "max")).reset_index())
    out["value"] = out.s / out.n
    return out


def rank(plays: pd.DataFrame, spec: SplitSpec, unit_value, bucket, season: int, games: int,
         table: Optional[pd.DataFrame] = None) -> dict:
    """Where (unit, bucket) sits through ``games`` games of ``season``: league-wide that season, and against every
    unit-season in ``plays`` at the same games-played point. Rank 1 = best given ``higher_is_better``."""
    t = game_table(plays, spec) if table is None else table
    h = split(plays, spec, games=games, table=t)
    h = h[(h[spec.by] == bucket) & (h.n >= spec.min_n)]
    me = h[(h.season == season) & (h[spec.unit] == unit_value)]
    if me.empty:
        return {"ok": False, "reason": f"n<{spec.min_n} or unit absent", "games": games}
    v = float(me.value.iloc[0])

    def _rank(frame):
        better = (frame.value > v) if spec.higher_is_better else (frame.value < v)
        return int(better.sum()) + 1, len(frame)

    r_lg, n_lg = _rank(h[h.season == season])
    r_hi, n_hi = _rank(h)
    return {"ok": True, "unit": unit_value, "bucket": bucket, "value": v, "n_plays": int(me.n.iloc[0]), "games": games,
            "rank_league": r_lg, "of_league": n_lg, "rank_history": r_hi, "of_history": n_hi,
            "percentile_history": 1.0 - (r_hi - 1) / max(n_hi - 1, 1)}


def stability(plays: pd.DataFrame, spec: SplitSpec, bucket, games: int, min_half_n: int = 10, boot: int = 2000,
              seed: int = 20261019, table: Optional[pd.DataFrame] = None) -> dict:
    """Split-half reliability of the bucket's metric across unit-seasons at ``games`` games (odd vs even games),
    Spearman-Brown corrected, with a unit-season bootstrap CI. CI lower bound > 0 = trait at this sample."""
    t = game_table(plays, spec) if table is None else table
    t = t[(t.game_no <= games) & (t[spec.by] == bucket)].copy()
    t["half"] = np.where(t.game_no % 2 == 1, "a", "b")
    p = t.pivot_table(index=["season", spec.unit], columns="half", values=["n", "s"], aggfunc="sum")
    p = p.dropna()
    if p.empty:
        return {"ok": False, "reason": "no unit-season has both halves"}
    keep = (p[("n", "a")] >= min_half_n) & (p[("n", "b")] >= min_half_n)
    va = (p[("s", "a")] / p[("n", "a")])[keep].to_numpy()
    vb = (p[("s", "b")] / p[("n", "b")])[keep].to_numpy()
    if len(va) < 8:
        return {"ok": False, "reason": f"only {len(va)} unit-seasons with both halves >= {min_half_n} plays"}
    sb = lambda r: 2 * r / (1 + r) if r > -1 else float("nan")
    r = float(np.corrcoef(va, vb)[0, 1])
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(boot):
        i = rng.integers(0, len(va), len(va))
        if va[i].std() > 0 and vb[i].std() > 0:
            bs.append(sb(float(np.corrcoef(va[i], vb[i])[0, 1])))
    lo, hi = (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))) if bs else (float("nan"),) * 2
    return {"ok": True, "bucket": bucket, "games": games, "n_unit_seasons": int(len(va)), "r_half": r,
            "r_spearman_brown": sb(r), "ci95": [lo, hi], "trait": bool(lo > 0)}


def estimate_k(table_split: pd.DataFrame) -> float:
    """Pseudo-play prior strength k = within-variance / between-variance (method of moments) for one bucket's
    unit-season values; shrunk value = (s + k*league) / (n + k)."""
    d = table_split[table_split.n > 1]
    if len(d) < 8:
        return float("inf")
    within = float(((d.ss - d.s ** 2 / d.n).sum()) / (d.n - 1).sum())
    tau2 = float(np.average((d.value - np.average(d.value, weights=d.n)) ** 2, weights=d.n) - np.mean(within / d.n))
    return float("inf") if tau2 <= 1e-9 else within / tau2


def shrink(n: float, s: float, league: float, k: float) -> float:
    if not np.isfinite(k):
        return league
    return (s + k * league) / (n + k)


@dataclass
class CrossResult:
    expected: float                      # frequency-weighted expected metric per play, using the splits
    baseline: float                      # same, using only unsplit (overall) rates: what a season-long rating gives
    delta: float                         # expected - baseline: what only the split sees
    by_bucket: dict = field(default_factory=dict)  # bucket -> {freq, off, dfn, league, expected}


def show_frequency(dfn_share: Mapping, off_faced_share: Mapping, league_share: Mapping) -> dict:
    """How often the defense will show each bucket vs this offense: odds-product of the defense's own tendency and what
    this offense draws, over the league rate, renormalised. (A conditioning ``context`` such as personnel would be
    applied by the caller restricting the plays that feed the two shares.)"""
    raw = {b: dfn_share[b] * off_faced_share[b] / max(league_share[b], 1e-9) for b in league_share}
    z = sum(raw.values())
    return {b: v / z for b, v in raw.items()}


def cross(off: Mapping, dfn: Mapping, league: Mapping, freq: Mapping, k: Mapping, overall: Optional[Mapping] = None
          ) -> CrossResult:
    """Join both sides of the same split. ``off``/``dfn``: bucket -> (n, s) for the offense's own metric and the metric
    the defense allows; ``league``: bucket -> league mean; ``k``: bucket -> prior strength. Expected per-play outcome in
    a bucket = league + (offense deviation) + (defense deviation), each shrunk by its own sample - additive in the two
    deviations, hence symmetric in the roles. ``overall`` = {"off": (n,s), "dfn": (n,s), "league": v, "k": k} gives the
    unsplit baseline; without it the baseline uses the freq-weighted sums of the same buckets (delta is then 0)."""
    rows, exp = {}, 0.0
    for b, f in freq.items():
        lv = league[b]
        o = shrink(*off[b], lv, k[b]) if b in off else lv
        d = shrink(*dfn[b], lv, k[b]) if b in dfn else lv
        e = lv + (o - lv) + (d - lv)
        rows[b] = {"freq": f, "off": o, "dfn": d, "league": lv, "expected": e}
        exp += f * e
    if overall is None:
        return CrossResult(exp, exp, 0.0, rows)
    L = overall["league"]
    base = L + (shrink(*overall["off"], L, overall["k"]) - L) + (shrink(*overall["dfn"], L, overall["k"]) - L)
    return CrossResult(exp, base, exp - base, rows)


# Which Kalshi families an entry's metric should move. Direction is for "metric up for the offense". Kept as data so a
# new entry adds a row, not code. Families verified against 12_EXPLORATORY/thin_markets/inventory.json.
MARKET_TAGS: dict = {
    "rush_success": [("KXNFLRSHYDS", "player rushing yards over", "up"), ("KXNFLTEAMTOTAL", "offense team total", "up"),
                     ("KXNFLSPREAD", "offense side", "up"), ("KXNFLTOTAL", "game total", "up"),
                     ("KXNFLRSHATT", "rush attempts (game-script)", "up"), ("KXNFLTEAMYDS", "team yards", "up")],
    "rush_stuffed": [("KXNFLRSHYDS", "player rushing yards over", "down"), ("KXNFLTEAMTOTAL", "offense team total", "down"),
                     ("KXNFLSPREAD", "offense side", "down"), ("KXNFLTOTAL", "game total", "down"),
                     ("KXNFLTEAMYDS", "team yards", "down")],
    "rush_yards_per_carry": [("KXNFLRSHYDS", "player rushing yards over", "up"), ("KXNFLMOSTRSHYDS", "most rushing yards", "up"),
                             ("KXNFLLONGRSH", "longest rush", "up"), ("KXNFLTEAMYDS", "team yards", "up")],
}


def market_map(tag: str, inventory: Optional[Mapping] = None) -> list:
    """Families an entry should move, with direction and the inventory's live/settled counts (None if not listed)."""
    out = []
    for fam, line, direction in MARKET_TAGS.get(tag, []):
        inv = (inventory or {}).get(fam)
        out.append({"family": fam, "line": line, "direction": direction,
                    "events": inv["events"] if inv else None, "open_now": inv["open_now"] if inv else None,
                    "settled_since_floor": inv["settled_since_floor"] if inv else None})
    return out


def filter_entries(entries: Iterable[Mapping], tail: float = 0.10, min_n: int = 30,
                   require_trait: bool = True, mismatch_min: Optional[float] = None) -> list:
    """The filtering mechanism. An entry passes when it is (a) ranked (n >= min_n), (b) in the history tail (top or bottom
    ``tail`` of unit-seasons at the same games-played point), (c) a trait at this sample if ``require_trait``, and, when
    ``mismatch_min`` is set, (d) the matchup cross moves the expectation by at least that much. Returns every entry
    with ``pass`` and the failed ``reasons`` - the median fails, loudly."""
    res = []
    for e in entries:
        why = []
        if not e.get("ok", True) or e.get("n_plays", 0) < min_n:
            why.append("n<min")
        else:
            p = e["percentile_history"]
            if not (p <= tail or p >= 1 - tail):
                why.append("not in tail")
            if require_trait and not (e.get("stability") or {}).get("trait", False):
                why.append("not a trait at this sample")
        if mismatch_min is not None and abs(e.get("cross_delta", 0.0)) < mismatch_min:
            why.append("cross too small")
        res.append({**e, "pass": not why, "reasons": why})
    return res
