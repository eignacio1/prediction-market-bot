"""Scoring for EXP-044 / EXP-044b: paired Brier, engine minus market, per family (W94.1).

A logged row is (p_engine, p_market, family, subject, strike_n). It settles YES when the final score satisfies
X >= strike_n (X = home margin, away margin, game total or one team's points). Rows within a game are dependent
(one game's strikes), so intervals resample whole games. Nothing here touches an order, stake or ledger row.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Optional

from prediction_market_bot.c5_execution.position_gate import skill_weight
from prediction_market_bot.quant.inference import cluster_bootstrap

FAMILIES = ("NBA_MONEYLINE", "NBA_SPREAD", "NBA_GAME_TOTAL", "NBA_TEAM_TOTAL")


def outcome(row: Mapping, final: tuple) -> Optional[int]:
    """1/0 for a settled row given (home_pts, away_pts); None if the family is unknown."""
    hp, ap = final
    fam, subj, n = row["family"], row["subject"], row["strike_n"]
    if fam == "NBA_MONEYLINE":
        won_home = hp > ap
        return int(won_home if subj == row["home"] else not won_home)
    if fam == "NBA_GAME_TOTAL":
        return int(hp + ap >= n)
    mine, theirs = (hp, ap) if subj == row["home"] else (ap, hp)
    if fam == "NBA_SPREAD":
        return int(mine - theirs >= n)
    if fam == "NBA_TEAM_TOTAL":
        return int(mine >= n)
    return None


def paired_rows(rows: Iterable[Mapping], results: Mapping) -> list:
    """Settled rows with both prices: [(family, game_cluster, d, be, bm)] where d = Brier_engine - Brier_market.

    ``results``: (game_date, home, away) -> (home_pts, away_pts). Unsettled or market-less rows are skipped."""
    out = []
    for r in rows:
        pm, pe = r.get("p_market"), r.get("p_engine")
        final = results.get((r["game_date"], r["home"], r["away"]))
        if pm is None or pe is None or final is None:
            continue
        y = outcome(r, final)
        if y is None:
            continue
        be, bm = (pe - y) ** 2, (pm - y) ** 2
        out.append((r["family"], r["event_ticker"], be - bm, be, bm))
    return out


def score(rows: Iterable[Mapping], results: Mapping, b: int = 2000, seed: int = 20261029) -> dict:
    """Per family and pooled: n rows, n games, mean paired difference with game-clustered interval, both Briers
    and the skill weight w = clip(1 - Brier_engine / Brier_market, 0, 1) the accepted gate would give the engine."""
    pr = paired_rows(rows, results)
    out = {}
    for fam in FAMILIES + ("ALL",):
        sub = [x for x in pr if fam == "ALL" or x[0] == fam]
        if not sub:
            out[fam] = {"n_rows": 0, "n_games": 0}
            continue
        by = defaultdict(list)
        for _, g, d, _, _ in sub:
            by[g].append(d)
        mean, lo, hi = cluster_bootstrap(by, b=b, seed=seed)
        be = sum(x[3] for x in sub) / len(sub)
        bm = sum(x[4] for x in sub) / len(sub)
        out[fam] = {"n_rows": len(sub), "n_games": len(by), "mean_diff": mean, "lo": lo, "hi": hi,
                    "brier_engine": be, "brier_market": bm, "w": skill_weight(be, bm)}
    return out
