"""NBA factor class: officials (crew) tendencies, point-in-time (W93.2 Part B, ADR-0073/0075).

For each game, each official's rate on three game-level quantities (total personal fouls, total free-throw attempts,
pace) is a shrunk mean over that official's EARLIER games only; a crew's value is the mean of its officials' values.
The deviation from the league mean is what the factor carries. A game's own box line is never used for its own row.

Definitions (fixed before any result):
  quantity q    game total of fouls_personal (both teams), free_throws_attempted (both teams), pace (team_box mean)
  official rate (sum_prior_q + K * league_mean_prior) / (n_prior + K), K = SHRINK_K = 30 games, league_mean_prior = mean of q
                over all games strictly before this game's date. n_prior counts only games on an EARLIER date.
  crew value    mean of the officials' rates for the game; crew_dev = crew value - league_mean_prior
Assumption stated plainly: the archive's crew for a game is the crew that worked it; the NBA posts assignments about nine
hours before tip, so using the game's own crew is a game-day-known upper bound, not a timestamped pre-game fact (GG-1390).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SHRINK_K = 30.0
QUANTITIES = ("fouls", "fta", "pace")


def game_quantities(team_box: pd.DataFrame) -> pd.DataFrame:
    """game_id -> date-free game totals from team_box (two rows per game)."""
    b = team_box.copy()
    b["game_id"] = b["game_id"].astype(str)
    g = b.groupby("game_id").agg(fouls=("fouls_personal", "sum"), fta=("free_throws_attempted", "sum"),
                                 fga=("field_goals_attempted", "sum"), n=("team_id", "size"))
    g = g[g["n"] == 2].drop(columns="n")
    return g


def official_rates(crews: pd.DataFrame, games: pd.DataFrame, k: float = SHRINK_K) -> pd.DataFrame:
    """Point-in-time crew deviation per game.

    ``crews``: game_id, official_id. ``games``: index game_id, columns date (datetime) + fouls, fta, pace (game totals).
    Returns index game_id with crew_dev_<q> (shrunk crew mean minus league mean before that date) and crew_n (min prior
    games across the crew's officials). Only games on strictly earlier dates feed a row.
    """
    crews = crews.assign(game_id=crews["game_id"].astype(str))
    crews = crews[crews["game_id"].isin(games.index)].drop_duplicates(["game_id", "official_id"])
    crews = crews.join(games[["date", *QUANTITIES]], on="game_id").sort_values("date")
    gdays = games.sort_values("date")
    days = gdays["date"].to_numpy(dtype="datetime64[D]")
    league_cum = {q: np.concatenate([[0.0], np.cumsum(gdays[q].to_numpy(float))]) for q in QUANTITIES}
    out = {}
    hist = {}  # official_id -> (n, {q: sum}) over dates strictly before the current date
    rows = crews.to_dict("records")
    by_day = {}
    for r in rows:
        by_day.setdefault(r["date"], []).append(r)
    for day in sorted(by_day):
        d64 = np.datetime64(day, "D")
        lo = int(np.searchsorted(days, d64, side="left"))  # games strictly before this date
        lg = {q: (league_cum[q][lo] / lo if lo else np.nan) for q in QUANTITIES}
        gm = {}
        for r in by_day[day]:
            n, s = hist.get(r["official_id"], (0, dict.fromkeys(QUANTITIES, 0.0)))
            gm.setdefault(r["game_id"], []).append((n, s))
        for gid, offs in gm.items():
            rec = {"crew_n": min(n for n, _ in offs)}
            for q in QUANTITIES:
                if np.isnan(lg[q]):
                    rec[f"crew_dev_{q}"] = np.nan
                    continue
                rates = [(s[q] + k * lg[q]) / (n + k) for n, s in offs]
                rec[f"crew_dev_{q}"] = float(np.mean(rates) - lg[q])
            out[gid] = rec
        for r in by_day[day]:  # update AFTER the day is scored: a game never feeds an official's rate on its own date
            n, s = hist.get(r["official_id"], (0, dict.fromkeys(QUANTITIES, 0.0)))
            s = dict(s)
            for q in QUANTITIES:
                s[q] += float(r[q])
            hist[r["official_id"]] = (n + 1, s)
    return pd.DataFrame.from_dict(out, orient="index")
