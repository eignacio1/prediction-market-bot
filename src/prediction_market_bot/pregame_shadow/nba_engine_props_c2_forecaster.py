"""EXP-047-C2 (W126.2): EXP-047 with a STAT-SPECIFIC absorption of the players listed Out at the pre-tip cutoff.
Points: C1's full absorption (the team total is the simulated score, so a fraction cannot change the shares). Rebounds and assists:
own-stat means, an absorption fraction fitted on the fit season. Threes: the vacated three-point ATTEMPTS are absorbed at a fitted fraction
and each active player converts them at his own make rate. The fractions are frozen in ``LAMBDA`` (12_EXPLORATORY/nba_props_role/FIT_C2.json)
and hashed into ``model_sha256``. Same inputs, same seeds, same draws as EXP-047; nobody Out -> prices exactly as EXP-047 (test).
EVALUATE-AND-LOG only; see PREREG_C2.md."""
from __future__ import annotations

import collections
import dataclasses
import hashlib
import json
from datetime import datetime
from typing import Any, Callable, Collection, Mapping, Optional

import numpy as np

from prediction_market_bot.c1_signal_ingestion.nba_ingest import kalshi_code
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name
from prediction_market_bot.nba_engine.usage_redistribution import absorb, absorb_threes, redistribute
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from prediction_market_bot.pregame_shadow.contract import PregameForecast

MODEL_ID = "nba_engine_v2_props_c2_w126_2"
LAMBDA = {"rebounds": 1.0, "assists": 1.0, "threes": 1.0}      # replaced by the frozen fit (FIT_C2.json) before the judged season is scored
_C2 = dict(base=F._CONSTANTS, points_rest=F.POINTS_REST, rule="stat_specific_absorption", lam=LAMBDA, points="full", out_p=0.0, other_p=1.0)
MODEL_SHA256 = hashlib.sha256(json.dumps(_C2, sort_keys=True).encode()).hexdigest()


def parse_attempts(raw: Mapping[str, Any]) -> dict:
    """ESPN raw store -> {(team code, name): [(date, three-point attempts)]}, the same players and dates ``F.parse_box`` keeps."""
    att: dict = collections.defaultdict(list)
    for g in raw.values():
        for t in g["box"]["players"]:
            code = kalshi_code(t["team"]["abbreviation"])
            ix = {k: i for i, k in enumerate(t["statistics"][0]["keys"])}
            for a in t["statistics"][0]["athletes"]:
                st = a.get("stats") or []
                if not st or a.get("didNotPlay"):
                    continue
                try:
                    if float(st[ix["minutes"]]) <= 0:
                        continue
                    att[(code, a["athlete"]["displayName"])].append(
                        (g["date"], float(st[ix["threePointFieldGoalsMade-threePointFieldGoalsAttempted"]].split("-")[1])))
                except (ValueError, IndexError, KeyError):
                    continue
    return att


class NBAEnginePropsC2(F.NBAEngineProps):
    """``out_lookup(parsed_ticker, as_of_utc) -> names listed Out`` (injected); ``att_rows`` from ``parse_attempts``."""

    def __init__(self, games: dict, player_rows: dict, tips, out_lookup: Callable[[dict, datetime], Collection[str]],
                 att_rows: Optional[dict] = None, lam: Optional[Mapping[str, float]] = None) -> None:
        super().__init__(games, player_rows, tips)
        self.out_lookup, self.att_rows = out_lookup, att_rows or {}
        self.lam = dict(LAMBDA if lam is None else lam)
        self._out: frozenset = frozenset()

    def _prior_att(self, team: str, name: str, before: str) -> Optional[float]:
        v = [a for d, a in self.att_rows.get((team, name), ()) if d < before]
        return float(np.mean(v)) if v else None

    def _mu(self, ros: list, p: dict) -> dict:
        base = super()._mu(ros, p)
        pp = [0.0 if norm_name(n) in self._out else 1.0 for _, n, _ in ros]
        if all(x == 1.0 for x in pp):
            return base
        out = {"points": redistribute(base["points"], pp),
               "rebounds": absorb(base["rebounds"], pp, self.lam["rebounds"]),
               "assists": absorb(base["assists"], pp, self.lam["assists"])}
        att = [self._prior_att(p.get("team"), n, p.get("game_date", "9999")) for _, n, _ in ros]
        if all(a is not None for a in att):
            out["threes"] = absorb_threes(att, base["threes"], pp, self.lam["threes"])
        else:                                   # attempts missing for someone: absorb on makes (stated fallback)
            out["threes"] = absorb(base["threes"], pp, self.lam["threes"])
        return out

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = F.parse_market_ticker(market_ticker)
        if p is None:
            return None
        self._out = frozenset(norm_name(x) for x in (self.out_lookup(p, as_of_utc) or ()))
        key_out = tuple(sorted(self._out))
        self._tag = key_out            # the split cache is per (game, team, stat, Out set)
        fc = super().forecast(market_ticker, as_of_utc)
        if fc is None:
            return None
        row = hashlib.sha256((fc.feature_row_sha256 + "|" + ",".join(key_out)).encode()).hexdigest()
        return dataclasses.replace(fc, model_id=MODEL_ID, model_sha256=MODEL_SHA256, feature_row_sha256=row)
